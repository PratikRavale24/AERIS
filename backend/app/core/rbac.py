"""AERIS Backend — RBAC Module.

Role-Based Access Control enforced server-side via FastAPI dependencies.
Deny by default — every route must declare required permissions.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.core.logging import get_logger
from app.core.security import constant_time_compare, decode_access_token

logger = get_logger("rbac")


class Role(str, Enum):
    FLEET_SUPERVISOR = "FLEET_SUPERVISOR"
    MAINT_PLANNER = "MAINT_PLANNER"
    MAINT_ENGINEER = "MAINT_ENGINEER"
    SPARES_PLANNER = "SPARES_PLANNER"
    SYS_ADMIN = "SYS_ADMIN"


class Permission(str, Enum):
    # Fleet & Aircraft
    VIEW_FLEET = "view_fleet"
    VIEW_AIRCRAFT_DETAIL = "view_aircraft_detail"
    VIEW_TECH_NOTES = "view_tech_notes"

    # Predictions & Models
    RUN_INFERENCE = "run_inference"
    VIEW_MODEL_EVIDENCE = "view_model_evidence"

    # Recommendations & Decisions
    VIEW_RECOMMENDATIONS = "view_recommendations"
    MAKE_DECISION = "make_decision"  # accept/defer/reject
    APPROVE_OVERRIDE = "approve_override"

    # Scenarios & Twin
    RUN_SCENARIOS = "run_scenarios"
    RUN_SPARES_SCENARIOS = "run_spares_scenarios"
    SIMULATE_CYCLES = "simulate_cycles"

    # Spares & Facilities
    VIEW_SPARES = "view_spares"
    EDIT_SPARES = "edit_spares"
    EDIT_FACILITIES = "edit_facilities"

    # Ingestion & Admin
    INGEST_DATA = "ingest_data"
    RETRAIN_MODELS = "retrain_models"
    MANAGE_USERS = "manage_users"
    MANAGE_CONFIG = "manage_config"

    # Audit & Reports
    VIEW_FULL_AUDIT = "view_full_audit"
    VIEW_OWN_AUDIT = "view_own_audit"
    GENERATE_REPORTS = "generate_reports"
    VIEW_SECURITY = "view_security"

    # Forecast
    RUN_FORECAST = "run_forecast"

    # Passport
    VERIFY_PASSPORT = "verify_passport"


# ── Permission Matrix ───────────────────────────────────────────────
# Each role maps to a set of permissions. Deny by default.

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.FLEET_SUPERVISOR: {
        Permission.VIEW_FLEET,
        Permission.VIEW_AIRCRAFT_DETAIL,
        Permission.VIEW_TECH_NOTES,
        Permission.RUN_INFERENCE,
        Permission.VIEW_MODEL_EVIDENCE,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.MAKE_DECISION,
        Permission.APPROVE_OVERRIDE,
        Permission.RUN_SCENARIOS,
        Permission.VIEW_SPARES,
        Permission.VIEW_FULL_AUDIT,
        Permission.GENERATE_REPORTS,
        Permission.VIEW_SECURITY,
        Permission.RUN_FORECAST,
        Permission.VERIFY_PASSPORT,
        Permission.SIMULATE_CYCLES,
    },
    Role.MAINT_PLANNER: {
        Permission.VIEW_FLEET,
        Permission.VIEW_AIRCRAFT_DETAIL,
        Permission.VIEW_TECH_NOTES,
        Permission.RUN_INFERENCE,
        Permission.VIEW_MODEL_EVIDENCE,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.MAKE_DECISION,
        Permission.RUN_SCENARIOS,
        Permission.VIEW_SPARES,
        Permission.EDIT_FACILITIES,
        Permission.VIEW_OWN_AUDIT,
        Permission.GENERATE_REPORTS,
        Permission.RUN_FORECAST,
        Permission.VERIFY_PASSPORT,
        Permission.SIMULATE_CYCLES,
    },
    Role.MAINT_ENGINEER: {
        Permission.VIEW_FLEET,
        Permission.VIEW_AIRCRAFT_DETAIL,
        Permission.VIEW_TECH_NOTES,
        Permission.RUN_INFERENCE,
        Permission.VIEW_MODEL_EVIDENCE,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.MAKE_DECISION,
        Permission.RUN_SCENARIOS,
        Permission.VIEW_SPARES,
        Permission.VIEW_OWN_AUDIT,
        Permission.GENERATE_REPORTS,
        Permission.RUN_FORECAST,
        Permission.VERIFY_PASSPORT,
        Permission.SIMULATE_CYCLES,
    },
    Role.SPARES_PLANNER: {
        Permission.VIEW_FLEET,
        Permission.VIEW_AIRCRAFT_DETAIL,
        # No VIEW_TECH_NOTES
        Permission.VIEW_SPARES,
        Permission.EDIT_SPARES,
        Permission.RUN_SPARES_SCENARIOS,
        Permission.VIEW_OWN_AUDIT,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.VERIFY_PASSPORT,
    },
    Role.SYS_ADMIN: {
        Permission.VIEW_FLEET,
        Permission.VIEW_AIRCRAFT_DETAIL,
        # No VIEW_TECH_NOTES
        Permission.RUN_INFERENCE,
        Permission.VIEW_MODEL_EVIDENCE,
        Permission.INGEST_DATA,
        Permission.RETRAIN_MODELS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_CONFIG,
        Permission.VIEW_FULL_AUDIT,
        Permission.VIEW_SECURITY,
        Permission.VIEW_SPARES,
        Permission.VIEW_RECOMMENDATIONS,
        Permission.GENERATE_REPORTS,
        Permission.VERIFY_PASSPORT,
        Permission.SIMULATE_CYCLES,
        # SYS_ADMIN cannot make maintenance decisions (separation of duties)
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    try:
        role_enum = Role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(role_enum, set())


# ── FastAPI Dependencies ─────────────────────────────────────────────

class CurrentUser:
    """Represents the current authenticated user."""

    def __init__(self, user_id: str, role: str, username: str) -> None:
        self.user_id = user_id
        self.role = role
        self.username = username

    def has_permission(self, permission: Permission) -> bool:
        return has_permission(self.role, permission)


async def get_current_user(request: Request) -> CurrentUser:
    """Extract and validate the current user from the access token cookie.
    
    This is the core authentication dependency. All protected routes use this.
    """
    # Read token from HttpOnly cookie
    token = request.cookies.get("__Host-access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "authentication_required", "message": "Not authenticated"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "token_invalid", "message": "Invalid or expired token"},
        )

    return CurrentUser(
        user_id=payload["sub"],
        role=payload["role"],
        username=payload["username"],
    )


def require_permission(permission: Permission):  # type: ignore[no-untyped-def]
    """FastAPI dependency factory: require a specific permission.
    
    Usage:
        @router.get("/protected", dependencies=[Depends(require_permission(Permission.VIEW_FLEET))])
        async def protected_route():
            ...
    """
    async def _check(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not current_user.has_permission(permission):
            logger.warning(
                f"RBAC denied: user={current_user.username} role={current_user.role} "
                f"permission={permission.value}",
                extra={"extra_data": {
                    "user_id": current_user.user_id,
                    "role": current_user.role,
                    "permission": permission.value,
                    "path": str(request.url.path),
                }},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_permissions",
                    "message": "You do not have permission to perform this action",
                },
            )
        return current_user

    return Depends(_check)


def require_stepup(request: Request) -> None:
    """Verify step-up authentication token for sensitive operations."""
    stepup_token = request.headers.get("X-Stepup-Token")
    if not stepup_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "stepup_required",
                "message": "Re-authentication required for this operation",
            },
        )
    # Token validation happens in the auth service layer
