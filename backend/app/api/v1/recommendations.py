"""AERIS Backend — Recommendations & Decisions API Routes."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.audit import write_audit_entry
from app.core.rbac import CurrentUser, Permission, get_current_user, require_permission
from app.db.models import Decision, PendingOverride, Prediction, Recommendation
from app.db.session import get_db

router = APIRouter(tags=["recommendations"])


class DecisionRequest(BaseModel):
    action: str = Field(..., pattern=r"^(ACCEPT|DEFER|REJECT|OVERRIDE)$")
    reason: str = Field(..., min_length=15, max_length=500)


class OverrideApproval(BaseModel):
    approved: bool
    reason: str = Field(..., min_length=15, max_length=500)


@router.get("/recommendations", dependencies=[require_permission(Permission.VIEW_RECOMMENDATIONS)])
async def list_recommendations(
    status: str | None = None,
    tier: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List recommendations with filters."""
    page_size = min(page_size, 100)
    query = db.query(Recommendation).filter(Recommendation.is_superseded == False)  # noqa: E712

    if status:
        query = query.filter(Recommendation.status == status)
    if tier:
        query = query.filter(Recommendation.priority_tier == tier)

    total = query.count()
    recs = (
        query.order_by(desc(Recommendation.priority_score))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for rec in recs:
        pred = db.query(Prediction).filter_by(id=rec.prediction_id).first()
        items.append({
            "id": rec.id,
            "version": rec.version,
            "aircraft_id": rec.aircraft_id,
            "component_id": rec.component_id,
            "priority_score": rec.priority_score,
            "priority_tier": rec.priority_tier,
            "reason_codes": rec.reason_codes,
            "recommended_action": rec.recommended_action,
            "part_no": rec.part_no,
            "part_status": rec.part_status,
            "facility_id": rec.facility_id,
            "status": rec.status,
            "risk_score": pred.risk_score if pred else None,
            "rul_q10": pred.rul_q10 if pred else None,
            "rul_q50": pred.rul_q50 if pred else None,
            "rul_q90": pred.rul_q90 if pred else None,
            "trust_score": pred.trust_score if pred else None,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
        })

    return {"total": total, "page": page, "page_size": page_size, "recommendations": items}


@router.get("/recommendations/{rec_id}", dependencies=[require_permission(Permission.VIEW_RECOMMENDATIONS)])
async def get_recommendation(rec_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get a single recommendation with full details."""
    rec = db.query(Recommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    pred = db.query(Prediction).filter_by(id=rec.prediction_id).first()

    # Get decision history
    decisions = (
        db.query(Decision)
        .filter_by(recommendation_id=rec_id)
        .order_by(desc(Decision.decided_at))
        .all()
    )

    return {
        "id": rec.id,
        "version": rec.version,
        "aircraft_id": rec.aircraft_id,
        "component_id": rec.component_id,
        "priority_score": rec.priority_score,
        "priority_tier": rec.priority_tier,
        "reason_codes": rec.reason_codes,
        "recommended_action": rec.recommended_action,
        "part_no": rec.part_no,
        "part_status": rec.part_status,
        "facility_id": rec.facility_id,
        "scheduled_start": rec.scheduled_start.isoformat() if rec.scheduled_start else None,
        "estimated_completion": rec.estimated_completion.isoformat() if rec.estimated_completion else None,
        "status": rec.status,
        "prediction": {
            "id": pred.id,
            "risk_score": pred.risk_score,
            "rul_q10": pred.rul_q10,
            "rul_q50": pred.rul_q50,
            "rul_q90": pred.rul_q90,
            "anomaly_score": pred.anomaly_score,
            "suspected_failure_mode": pred.suspected_failure_mode,
            "shap_values": pred.shap_values,
            "trust_score": pred.trust_score,
            "trust_gate": pred.trust_gate,
            "data_quality_score": pred.data_quality_score,
            "data_quality_flags": pred.data_quality_flags,
            "input_window_start": pred.input_window_start,
            "input_window_end": pred.input_window_end,
        } if pred else None,
        "decisions": [
            {
                "id": d.id,
                "action": d.action,
                "reason": d.reason,
                "model_version": d.model_version,
                "decided_by": d.decided_by,
                "decided_at": d.decided_at.isoformat() if d.decided_at else None,
            }
            for d in decisions
        ],
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
    }


@router.post("/recommendations/{rec_id}/decision", dependencies=[require_permission(Permission.MAKE_DECISION)])
async def make_decision(
    rec_id: str,
    body: DecisionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Record a decision on a recommendation."""
    rec = db.query(Recommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    now = datetime.now(timezone.utc)

    decision = Decision(
        id=str(uuid.uuid4()),
        recommendation_id=rec_id,
        recommendation_version=rec.version,
        action=body.action,
        reason=body.reason,
        decided_by=current_user.user_id,
        decided_at=now,
        created_at=now,
    )
    db.add(decision)

    # Handle overrides — require second approval
    if body.action == "OVERRIDE":
        override = PendingOverride(
            id=str(uuid.uuid4()),
            decision_id=decision.id,
            recommendation_id=rec_id,
            requested_by=current_user.user_id,
            status="PENDING",
            created_at=now,
        )
        db.add(override)
        rec.status = "PENDING_SECOND_APPROVAL"
    elif body.action == "ACCEPT":
        rec.status = "ACCEPTED"
    elif body.action == "DEFER":
        rec.status = "DEFERRED"
    elif body.action == "REJECT":
        rec.status = "REJECTED"

    # Audit
    write_audit_entry(
        db,
        action=f"DECISION_{body.action}",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        entity_type="recommendation",
        entity_id=rec_id,
        payload={
            "reason": body.reason,
            "recommendation_version": rec.version,
        },
    )

    db.commit()

    return {
        "message": f"Decision recorded: {body.action}",
        "decision_id": decision.id,
        "recommendation_status": rec.status,
    }


@router.post("/overrides/{override_id}/approve", dependencies=[require_permission(Permission.APPROVE_OVERRIDE)])
async def approve_override(
    override_id: str,
    body: OverrideApproval,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Approve or reject an override (requires different user — two-person rule)."""
    override = db.query(PendingOverride).filter_by(id=override_id, status="PENDING").first()
    if not override:
        raise HTTPException(status_code=404, detail="Pending override not found")

    # Two-person rule: approver must be different from requester
    if override.requested_by == current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "two_person_rule",
                "message": "Cannot approve your own override. A different Fleet Supervisor must approve.",
            },
        )

    now = datetime.now(timezone.utc)
    override.approved_by = current_user.user_id
    override.resolved_at = now

    rec = db.query(Recommendation).filter_by(id=override.recommendation_id).first()

    if body.approved:
        override.status = "APPROVED"
        if rec:
            rec.status = "OVERRIDDEN"
    else:
        override.status = "REJECTED"
        if rec:
            rec.status = "OPEN"

    write_audit_entry(
        db,
        action=f"OVERRIDE_{'APPROVED' if body.approved else 'REJECTED'}",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        entity_type="override",
        entity_id=override_id,
        payload={"reason": body.reason, "recommendation_id": override.recommendation_id},
    )

    db.commit()

    return {
        "message": f"Override {'approved' if body.approved else 'rejected'}",
        "override_id": override_id,
    }
