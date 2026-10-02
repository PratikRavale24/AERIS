"""AERIS Backend — Planning Engine.

Priority scoring, spare matching, facility capacity, fleet availability,
recommendations, and alerts generation.

Run as: python -m app.services.planner --run
"""
from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.audit import write_audit_entry
from app.core.logging import get_logger, setup_logging
from app.db.models import (
    Aircraft,
    Alert,
    Component,
    Decision,
    Facility,
    PendingOverride,
    Prediction,
    Recommendation,
    SparePart,
)

logger = get_logger("planner")

# ── Priority Score Computation ──────────────────────────────────────

# Default weights (stored in config_params in production)
DEFAULT_WEIGHTS = {
    "w_risk": 0.35,
    "w_rul_urgency": 0.20,
    "w_severity": 0.15,
    "w_criticality": 0.10,
    "w_schedule_risk": 0.20,
}

DEFAULT_RUL_REF = 100  # cycles
TIER_THRESHOLDS = {"CRITICAL": 75, "HIGH": 55, "MEDIUM": 35}
HYSTERESIS = 5


def compute_priority(
    risk_score: float,
    rul_q10: float,
    severity: float,
    criticality: int,
    aircraft_cycles_per_day: float,
    part_stock: int,
    part_min_stock: int,
    part_lead_time_days: int,
    earliest_facility_start_days: float,
    weights: dict[str, float] | None = None,
    rul_ref: int = DEFAULT_RUL_REF,
) -> dict[str, Any]:
    """Compute priority score (0-100) and tier. Pure function."""
    w = weights or DEFAULT_WEIGHTS

    # RUL urgency
    rul_urgency = float(np.clip(1 - rul_q10 / rul_ref, 0, 1))

    # RUL in days
    rul_days_q10 = rul_q10 / max(aircraft_cycles_per_day, 0.1)

    # Part risk
    if part_stock == 0 and part_lead_time_days >= rul_days_q10:
        part_risk = 1.0
    elif part_stock == 0 and part_lead_time_days < rul_days_q10:
        part_risk = 0.6
    elif part_stock <= part_min_stock:
        part_risk = 0.3
    else:
        part_risk = 0.0

    # Slot risk
    slot_risk = 1.0 if earliest_facility_start_days > rul_days_q10 else 0.0

    # Schedule risk
    schedule_risk = max(part_risk, slot_risk)

    # Criticality normalized to 0-1 (1=most critical, 3=least)
    criticality_norm = (4 - criticality) / 3.0

    # Severity normalized (assuming 0-1 input, or use risk as proxy)
    severity_norm = min(severity, 1.0)

    # Priority score
    priority = 100 * (
        w["w_risk"] * risk_score +
        w["w_rul_urgency"] * rul_urgency +
        w["w_severity"] * severity_norm +
        w["w_criticality"] * criticality_norm +
        w["w_schedule_risk"] * schedule_risk
    )
    priority = float(np.clip(priority, 0, 100))

    # Tier with hysteresis
    if priority >= TIER_THRESHOLDS["CRITICAL"]:
        tier = "CRITICAL"
    elif priority >= TIER_THRESHOLDS["HIGH"]:
        tier = "HIGH"
    elif priority >= TIER_THRESHOLDS["MEDIUM"]:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    # Reason codes
    reason_codes = []
    if risk_score >= 0.7:
        reason_codes.append("RISK_HIGH")
    if rul_q10 <= 25:
        reason_codes.append("RUL_LOW")
    if part_risk >= 0.6:
        reason_codes.append("PART_SHORTAGE")
    if slot_risk > 0:
        reason_codes.append("NO_SLOT_BEFORE_FAILURE")
    if part_stock <= part_min_stock and part_stock > 0:
        reason_codes.append("LOW_STOCK")

    # Recommended action
    if priority >= 75:
        action = "REPLACE" if part_risk < 0.6 else "EXPEDITE_PART"
    elif priority >= 55:
        action = "REPAIR"
    elif priority >= 35:
        action = "INSPECT"
    else:
        action = "MONITOR"

    return {
        "priority_score": round(priority, 2),
        "priority_tier": tier,
        "reason_codes": reason_codes,
        "recommended_action": action,
        "rul_urgency": round(rul_urgency, 3),
        "part_risk": round(part_risk, 3),
        "slot_risk": round(slot_risk, 3),
        "schedule_risk": round(schedule_risk, 3),
    }


# ── Spare Matching ──────────────────────────────────────────────────

def get_spare_status(
    part_no: str,
    db: Session,
) -> dict[str, Any]:
    """Get spare part readiness status."""
    spare = db.query(SparePart).filter_by(part_no=part_no).first()
    if spare is None:
        return {
            "part_no": part_no,
            "stock": 0,
            "min_stock": 0,
            "lead_time_days": 99,
            "criticality": "UNKNOWN",
            "status": "UNKNOWN",
        }

    if spare.stock == 0:
        status = "SHORTAGE"
    elif spare.stock <= spare.min_stock:
        status = "LOW_STOCK"
    else:
        status = "READY"

    return {
        "part_no": spare.part_no,
        "stock": spare.stock,
        "min_stock": spare.min_stock,
        "lead_time_days": spare.lead_time_days,
        "criticality": spare.criticality,
        "facility_id": spare.facility_id,
        "status": status,
    }


# ── Facility Allocation ─────────────────────────────────────────────

def allocate_facility(
    component_type: str,
    db: Session,
) -> dict[str, Any] | None:
    """Allocate a facility slot (greedy: earliest completion for matching capability)."""
    facilities = db.query(Facility).all()

    best: dict[str, Any] | None = None
    for fac in facilities:
        caps = [c.strip() for c in fac.capability.split(",")]
        if component_type not in caps:
            continue
        if fac.slots_available <= 0:
            continue

        start_days = 0.0  # Simplified — would check existing bookings
        completion_days = start_days + fac.avg_turnaround_days

        if best is None or completion_days < best["completion_days"]:
            best = {
                "facility_id": fac.facility_id,
                "facility_name": fac.name,
                "slots_available": fac.slots_available,
                "avg_turnaround_days": fac.avg_turnaround_days,
                "start_days": start_days,
                "completion_days": completion_days,
            }

    return best


# ── Fleet Availability ──────────────────────────────────────────────

def compute_fleet_availability(db: Session) -> dict[str, Any]:
    """Compute fleet availability metrics."""
    aircraft_list = db.query(Aircraft).all()
    total = len(aircraft_list)
    if total == 0:
        return {"availability_percent": 0, "total": 0, "available": 0, "breakdown": {}}

    breakdown: dict[str, int] = {}
    for ac in aircraft_list:
        breakdown[ac.status] = breakdown.get(ac.status, 0) + 1

    available = breakdown.get("AVAILABLE", 0) + breakdown.get("AVAILABLE_MONITOR", 0)
    availability_pct = round(available / total * 100, 1)

    return {
        "availability_percent": availability_pct,
        "total": total,
        "available": available,
        "breakdown": breakdown,
    }


# ── Recommendation Generation ───────────────────────────────────────

def generate_recommendations(db: Session) -> list[dict[str, Any]]:
    """Generate recommendations for all components with predictions."""
    # Get latest non-superseded predictions
    predictions = (
        db.query(Prediction)
        .filter(Prediction.is_superseded == False)  # noqa: E712
        .filter(Prediction.risk_score.isnot(None))
        .all()
    )

    results = []
    now = datetime.now(timezone.utc)

    for pred in predictions:
        component = db.query(Component).filter_by(component_id=pred.component_id).first()
        aircraft = db.query(Aircraft).filter_by(aircraft_id=pred.aircraft_id).first()

        if not component or not aircraft:
            continue

        # Spare matching
        spare_info = get_spare_status(component.part_no, db)

        # Facility allocation
        facility = allocate_facility(component.component_type, db)
        earliest_start = facility["start_days"] if facility else 999.0

        # Compute priority
        priority = compute_priority(
            risk_score=pred.risk_score or 0,
            rul_q10=pred.rul_q10 or 100,
            severity=pred.risk_score or 0,  # Use risk as severity proxy
            criticality=aircraft.criticality,
            aircraft_cycles_per_day=aircraft.cycles_per_day,
            part_stock=spare_info["stock"],
            part_min_stock=spare_info["min_stock"],
            part_lead_time_days=spare_info["lead_time_days"],
            earliest_facility_start_days=earliest_start,
        )

        # Supersede existing open recommendation for this component
        existing = (
            db.query(Recommendation)
            .filter_by(component_id=pred.component_id, is_superseded=False, status="OPEN")
            .first()
        )
        if existing:
            existing.is_superseded = True

        # Create new recommendation
        rec = Recommendation(
            id=str(uuid.uuid4()),
            version=(existing.version + 1) if existing else 1,
            component_id=pred.component_id,
            aircraft_id=pred.aircraft_id,
            prediction_id=pred.id,
            priority_score=priority["priority_score"],
            priority_tier=priority["priority_tier"],
            reason_codes=priority["reason_codes"],
            recommended_action=priority["recommended_action"],
            part_no=component.part_no,
            part_status=spare_info["status"],
            facility_id=facility["facility_id"] if facility else None,
            scheduled_start=now + timedelta(days=facility["start_days"]) if facility else None,
            estimated_completion=now + timedelta(days=facility["completion_days"]) if facility else None,
            supersedes_id=existing.id if existing else None,
            status="OPEN",
            created_at=now,
        )
        db.add(rec)

        # Generate alerts for high-priority items
        if priority["priority_tier"] in ("CRITICAL", "HIGH"):
            alert = Alert(
                id=str(uuid.uuid4()),
                alert_type="HIGH_RISK_ASSET",
                tier=priority["priority_tier"],
                title=f"{priority['priority_tier']} risk: {pred.component_id}",
                message=(
                    f"Component {pred.component_id} on {pred.aircraft_id} "
                    f"has risk score {pred.risk_score:.2f}, "
                    f"RUL ~{pred.rul_q50:.0f} cycles. "
                    f"Action: {priority['recommended_action']}"
                ),
                entity_type="component",
                entity_id=pred.component_id,
                created_at=now,
            )
            db.add(alert)

        # Spare shortage alerts
        if spare_info["status"] in ("SHORTAGE", "LOW_STOCK"):
            alert = Alert(
                id=str(uuid.uuid4()),
                alert_type="SPARE_SHORTAGE",
                tier="HIGH" if spare_info["status"] == "SHORTAGE" else "MEDIUM",
                title=f"Spare {spare_info['status']}: {component.part_no}",
                message=(
                    f"Part {component.part_no} stock={spare_info['stock']}, "
                    f"min={spare_info['min_stock']}, "
                    f"lead time={spare_info['lead_time_days']} days. "
                    f"Required for {pred.component_id}."
                ),
                entity_type="spare",
                entity_id=component.part_no,
                created_at=now,
            )
            db.add(alert)

        results.append({
            "recommendation_id": rec.id,
            "component_id": pred.component_id,
            "aircraft_id": pred.aircraft_id,
            **priority,
            "part_status": spare_info["status"],
            "facility_id": facility["facility_id"] if facility else None,
        })

    # Update aircraft statuses based on recommendations
    _update_aircraft_statuses(db, results)

    # Audit
    write_audit_entry(
        db,
        action="RECOMMENDATIONS_GENERATED",
        entity_type="system",
        payload={"count": len(results)},
    )

    db.commit()
    logger.info(f"Generated {len(results)} recommendations")
    return results


def _update_aircraft_statuses(db: Session, recommendations: list[dict[str, Any]]) -> None:
    """Update aircraft statuses based on recommendation tiers."""
    aircraft_max_tier: dict[str, str] = {}

    for rec in recommendations:
        aid = rec["aircraft_id"]
        tier = rec["priority_tier"]
        current = aircraft_max_tier.get(aid, "LOW")
        tier_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        if tier_order.get(tier, 0) > tier_order.get(current, 0):
            aircraft_max_tier[aid] = tier

    for aid, max_tier in aircraft_max_tier.items():
        aircraft = db.query(Aircraft).filter_by(aircraft_id=aid).first()
        if aircraft:
            if max_tier == "CRITICAL":
                aircraft.status = "UNSERVICEABLE"
            elif max_tier == "HIGH":
                aircraft.status = "SCHEDULED_MAINTENANCE"
            elif max_tier == "MEDIUM":
                aircraft.status = "AVAILABLE_MONITOR"
            # LOW stays as-is


def main() -> None:
    """Run recommendation generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if not args.run:
        print("Use --run to execute planner")
        return

    setup_logging("INFO")
    from app.db.session import get_session_factory
    factory = get_session_factory()
    session = factory()

    try:
        results = generate_recommendations(session)
        availability = compute_fleet_availability(session)
        logger.info(f"Fleet availability: {availability['availability_percent']}%")
    finally:
        session.close()


if __name__ == "__main__":
    main()
