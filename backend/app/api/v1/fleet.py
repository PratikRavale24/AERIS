"""AERIS Backend — Fleet & Aircraft API Routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_field
from app.core.rbac import CurrentUser, Permission, get_current_user, require_permission
from app.db.models import (
    Aircraft,
    Alert,
    Component,
    DataQualityReport,
    HealthObservation,
    InspectionFinding,
    MaintenanceEvent,
    Prediction,
    Recommendation,
    SparePart,
)
from app.db.session import get_db
from app.services.planner import compute_fleet_availability

router = APIRouter(tags=["fleet"])


@router.get("/fleet/summary", dependencies=[require_permission(Permission.VIEW_FLEET)])
async def fleet_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Fleet overview with KPI strip data."""
    availability = compute_fleet_availability(db)

    # High-risk assets
    high_risk = db.query(func.count(Prediction.id)).filter(
        Prediction.risk_score >= 0.7,
        Prediction.is_superseded == False,  # noqa: E712
    ).scalar() or 0

    # Maintenance due
    maint_due = db.query(func.count(Recommendation.id)).filter(
        Recommendation.status == "OPEN",
        Recommendation.is_superseded == False,  # noqa: E712
    ).scalar() or 0

    # Critical spare shortages
    spare_shortages = db.query(func.count(SparePart.part_no)).filter(
        SparePart.stock == 0,
        SparePart.criticality.in_(["HIGH", "CRITICAL"]),
    ).scalar() or 0

    # Data completeness
    total_components = db.query(func.count(Component.component_id)).scalar() or 1
    components_with_data = db.query(func.count(func.distinct(HealthObservation.component_id))).scalar() or 0
    data_completeness = round(components_with_data / total_components * 100, 1)

    # Recent alerts
    alerts = (
        db.query(Alert)
        .filter(Alert.is_acknowledged == False)  # noqa: E712
        .order_by(desc(Alert.created_at))
        .limit(10)
        .all()
    )

    # Top-10 priority recommendations
    top_recs = (
        db.query(Recommendation)
        .filter(Recommendation.is_superseded == False, Recommendation.status == "OPEN")  # noqa: E712
        .order_by(desc(Recommendation.priority_score))
        .limit(10)
        .all()
    )

    top_priority_table = []
    for rec in top_recs:
        pred = db.query(Prediction).filter_by(id=rec.prediction_id).first()
        top_priority_table.append({
            "recommendation_id": rec.id,
            "aircraft_id": rec.aircraft_id,
            "component_id": rec.component_id,
            "risk_score": pred.risk_score if pred else None,
            "rul_q10": pred.rul_q10 if pred else None,
            "rul_q50": pred.rul_q50 if pred else None,
            "rul_q90": pred.rul_q90 if pred else None,
            "trust_score": pred.trust_score if pred else None,
            "part_status": rec.part_status,
            "facility_id": rec.facility_id,
            "priority_score": rec.priority_score,
            "priority_tier": rec.priority_tier,
            "recommended_action": rec.recommended_action,
            "reason_codes": rec.reason_codes,
        })

    return {
        "availability": availability,
        "high_risk_assets": high_risk,
        "maintenance_due": maint_due,
        "critical_spare_shortages": spare_shortages,
        "data_completeness": data_completeness,
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "tier": a.tier,
                "title": a.title,
                "message": a.message,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "top_priority": top_priority_table,
        "data_source": "SYNTHETIC_NON_OPERATIONAL",
    }


@router.get("/fleet/status-breakdown", dependencies=[require_permission(Permission.VIEW_FLEET)])
async def fleet_status_breakdown(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Fleet status breakdown for charts."""
    availability = compute_fleet_availability(db)
    return availability


@router.get("/aircraft", dependencies=[require_permission(Permission.VIEW_FLEET)])
async def list_aircraft(
    status: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List all aircraft with optional status filter."""
    query = db.query(Aircraft)
    if status:
        query = query.filter(Aircraft.status == status)

    aircraft_list = query.order_by(Aircraft.aircraft_id).all()
    return {
        "aircraft": [
            {
                "aircraft_id": a.aircraft_id,
                "platform_type": a.platform_type,
                "status": a.status,
                "age_years": a.age_years,
                "total_cycles": a.total_cycles,
                "criticality": a.criticality,
                "cycles_per_day": a.cycles_per_day,
                "data_source": a.data_source,
            }
            for a in aircraft_list
        ],
        "total": len(aircraft_list),
    }


@router.get("/aircraft/{aircraft_id}", dependencies=[require_permission(Permission.VIEW_AIRCRAFT_DETAIL)])
async def get_aircraft_detail(
    aircraft_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Get detailed aircraft information."""
    aircraft = db.query(Aircraft).filter_by(aircraft_id=aircraft_id).first()
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    # Components
    components = db.query(Component).filter_by(aircraft_id=aircraft_id).all()

    comp_details = []
    for comp in components:
        pred = (
            db.query(Prediction)
            .filter_by(component_id=comp.component_id, is_superseded=False)
            .order_by(desc(Prediction.created_at))
            .first()
        )
        rec = (
            db.query(Recommendation)
            .filter_by(component_id=comp.component_id, is_superseded=False)
            .order_by(desc(Recommendation.created_at))
            .first()
        )
        quality = (
            db.query(DataQualityReport)
            .filter_by(component_id=comp.component_id)
            .order_by(desc(DataQualityReport.created_at))
            .first()
        )

        comp_details.append({
            "component_id": comp.component_id,
            "component_type": comp.component_type,
            "subsystem": comp.subsystem,
            "part_no": comp.part_no,
            "prediction": {
                "risk_score": pred.risk_score if pred else None,
                "rul_q10": pred.rul_q10 if pred else None,
                "rul_q50": pred.rul_q50 if pred else None,
                "rul_q90": pred.rul_q90 if pred else None,
                "anomaly_score": pred.anomaly_score if pred else None,
                "suspected_failure_mode": pred.suspected_failure_mode if pred else None,
                "trust_score": pred.trust_score if pred else None,
                "trust_gate": pred.trust_gate if pred else None,
                "shap_values": pred.shap_values if pred else None,
                "data_quality_score": pred.data_quality_score if pred else None,
            } if pred else None,
            "recommendation": {
                "id": rec.id,
                "priority_score": rec.priority_score,
                "priority_tier": rec.priority_tier,
                "recommended_action": rec.recommended_action,
                "reason_codes": rec.reason_codes,
                "part_status": rec.part_status,
                "status": rec.status,
            } if rec else None,
            "data_quality": {
                "score": quality.quality_score,
                "flags": quality.flags,
            } if quality else None,
        })

    # Maintenance history
    maint_events = (
        db.query(MaintenanceEvent)
        .filter_by(aircraft_id=aircraft_id)
        .order_by(desc(MaintenanceEvent.opened_at))
        .limit(20)
        .all()
    )

    maint_history = []
    for m in maint_events:
        entry: dict[str, Any] = {
            "event_id": m.event_id,
            "component_id": m.component_id,
            "fault_code": m.fault_code,
            "event_type": m.event_type,
            "severity": m.severity,
            "opened_at": m.opened_at.isoformat() if m.opened_at else None,
            "closed_at": m.closed_at.isoformat() if m.closed_at else None,
            "action": m.action,
        }
        # Only show tech notes to authorized roles
        if current_user.has_permission(Permission.VIEW_TECH_NOTES) and m.technician_notes_encrypted:
            entry["technician_notes"] = decrypt_field(m.technician_notes_encrypted)
        maint_history.append(entry)

    return {
        "aircraft": {
            "aircraft_id": aircraft.aircraft_id,
            "platform_type": aircraft.platform_type,
            "status": aircraft.status,
            "age_years": aircraft.age_years,
            "total_cycles": aircraft.total_cycles,
            "criticality": aircraft.criticality,
            "cycles_per_day": aircraft.cycles_per_day,
        },
        "components": comp_details,
        "maintenance_history": maint_history,
        "data_source": "SYNTHETIC_NON_OPERATIONAL",
    }


@router.get("/aircraft/{aircraft_id}/telemetry", dependencies=[require_permission(Permission.VIEW_AIRCRAFT_DETAIL)])
async def get_aircraft_telemetry(
    aircraft_id: str,
    component_id: str | None = None,
    sensor: str | None = None,
    limit: int = 500,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get health telemetry for an aircraft."""
    query = db.query(HealthObservation).filter_by(aircraft_id=aircraft_id)
    if component_id:
        query = query.filter_by(component_id=component_id)
    if sensor:
        query = query.filter_by(sensor=sensor)

    observations = query.order_by(HealthObservation.cycle.desc()).limit(min(limit, 1000)).all()

    return {
        "observations": [
            {
                "timestamp": o.timestamp.isoformat() if o.timestamp else None,
                "component_id": o.component_id,
                "sensor": o.sensor,
                "value": o.value,
                "unit": o.unit,
                "cycle": o.cycle,
            }
            for o in observations
        ],
        "total": len(observations),
    }
