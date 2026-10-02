"""AERIS Backend — Spares & Facilities API Routes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import write_audit_entry
from app.core.rbac import CurrentUser, Permission, get_current_user, require_permission
from app.db.models import Component, Facility, Prediction, SparePart
from app.db.session import get_db

router = APIRouter(tags=["spares"])


class SpareUpdateRequest(BaseModel):
    stock: int | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)


class FacilityUpdateRequest(BaseModel):
    slots_available: int | None = Field(default=None, ge=0)


@router.get("/spares", dependencies=[require_permission(Permission.VIEW_SPARES)])
async def list_spares(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List all spare parts with readiness status."""
    spares = db.query(SparePart).all()

    items = []
    for s in spares:
        if s.stock == 0:
            status = "SHORTAGE"
        elif s.stock <= s.min_stock:
            status = "LOW_STOCK"
        else:
            status = "READY"

        # Find affected components
        affected = (
            db.query(Component.component_id, Component.aircraft_id)
            .filter(Component.part_no == s.part_no)
            .all()
        )

        items.append({
            "part_no": s.part_no,
            "description": s.description,
            "stock": s.stock,
            "min_stock": s.min_stock,
            "lead_time_days": s.lead_time_days,
            "criticality": s.criticality,
            "facility_id": s.facility_id,
            "status": status,
            "affected_components": [
                {"component_id": c.component_id, "aircraft_id": c.aircraft_id}
                for c in affected
            ],
        })

    return {"spares": items, "total": len(items)}


@router.get("/spares/readiness", dependencies=[require_permission(Permission.VIEW_SPARES)])
async def spares_readiness(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Spare readiness overview with lead-time vs RUL analysis."""
    spares = db.query(SparePart).all()

    readiness = []
    for s in spares:
        # Find components using this part
        components = db.query(Component).filter_by(part_no=s.part_no).all()

        for comp in components:
            pred = (
                db.query(Prediction)
                .filter_by(component_id=comp.component_id, is_superseded=False)
                .first()
            )
            if pred and pred.rul_q10 is not None:
                readiness.append({
                    "part_no": s.part_no,
                    "component_id": comp.component_id,
                    "aircraft_id": comp.aircraft_id,
                    "stock": s.stock,
                    "lead_time_days": s.lead_time_days,
                    "rul_q10_cycles": pred.rul_q10,
                    "rul_q50_cycles": pred.rul_q50,
                    "lead_time_risk": s.stock == 0 and s.lead_time_days > (pred.rul_q10 or 999),
                })

    return {"readiness": readiness}


@router.patch("/spares/{part_no}", dependencies=[require_permission(Permission.EDIT_SPARES)])
async def update_spare(
    part_no: str,
    body: SpareUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Update spare stock or lead time (audited, triggers recompute)."""
    spare = db.query(SparePart).filter_by(part_no=part_no).first()
    if not spare:
        raise HTTPException(status_code=404, detail="Spare part not found")

    old_values = {"stock": spare.stock, "lead_time_days": spare.lead_time_days}

    if body.stock is not None:
        spare.stock = body.stock
    if body.lead_time_days is not None:
        spare.lead_time_days = body.lead_time_days

    spare.updated_at = datetime.now(timezone.utc)

    write_audit_entry(
        db,
        action="SPARE_UPDATED",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        entity_type="spare",
        entity_id=part_no,
        payload={
            "old": old_values,
            "new": {"stock": spare.stock, "lead_time_days": spare.lead_time_days},
        },
    )

    db.commit()

    return {"message": f"Spare {part_no} updated", "part_no": part_no}


@router.get("/facilities", dependencies=[require_permission(Permission.VIEW_SPARES)])
async def list_facilities(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List all maintenance facilities."""
    facilities = db.query(Facility).all()
    return {
        "facilities": [
            {
                "facility_id": f.facility_id,
                "name": f.name,
                "capability": f.capability,
                "slots_available": f.slots_available,
                "avg_turnaround_days": f.avg_turnaround_days,
            }
            for f in facilities
        ],
    }


@router.patch("/facilities/{facility_id}", dependencies=[require_permission(Permission.EDIT_FACILITIES)])
async def update_facility(
    facility_id: str,
    body: FacilityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Update facility slots (audited)."""
    facility = db.query(Facility).filter_by(facility_id=facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    old_slots = facility.slots_available

    if body.slots_available is not None:
        facility.slots_available = body.slots_available

    facility.updated_at = datetime.now(timezone.utc)

    write_audit_entry(
        db,
        action="FACILITY_UPDATED",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        entity_type="facility",
        entity_id=facility_id,
        payload={"old_slots": old_slots, "new_slots": facility.slots_available},
    )

    db.commit()

    return {"message": f"Facility {facility_id} updated"}
