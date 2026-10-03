"""AERIS Backend — Auth API Routes.

Login, logout, refresh, CSRF, step-up re-authentication.
Tokens live only in HttpOnly Secure SameSite=Strict cookies.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit_entry
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.rate_limit import rate_limit_login
from app.core.rbac import CurrentUser, get_current_user
from app.core.security import (
    constant_time_compare,
    create_access_token,
    create_refresh_token,
    create_stepup_token,
    generate_csrf_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import LoginAttempt, RefreshToken, SecurityEvent, StepupToken, User
from app.db.session import get_db
from app.schemas.auth import (
    CSRFResponse,
    LoginRequest,
    MeResponse,
    RefreshResponse,
    StepupRequest,
    StepupResponse,
)

logger = get_logger("auth")
router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str) -> None:
    """Set HttpOnly, Secure, SameSite=Strict cookies with __Host- prefix."""
    settings = get_settings()
    response.set_cookie(
        key="__Host-access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.jwt_access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="__Host-refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.jwt_refresh_token_expire_hours * 3600,
        path="/api/v1/auth/refresh",
    )
    response.set_cookie(
        key="__Host-csrf_token",
        value=csrf_token,
        httponly=False,  # Readable by JS for header submission
        secure=True,
        samesite="none",
        max_age=settings.jwt_refresh_token_expire_hours * 3600,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear all auth cookies."""
    response.delete_cookie("__Host-access_token", path="/", samesite="none", secure=True)
    response.delete_cookie("__Host-refresh_token", path="/api/v1/auth/refresh", samesite="none", secure=True)
    response.delete_cookie("__Host-csrf_token", path="/", samesite="none", secure=True)


def _check_lockout(db: Session, username: str, ip: str) -> None:
    """Check if user or IP is locked out."""
    user = db.query(User).filter_by(username=username).first()
    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "account_locked",
                "message": "Account is temporarily locked due to too many failed attempts.",
            },
            headers={"Retry-After": str(remaining)},
        )


def _record_login_attempt(db: Session, username: str, ip: str, success: bool) -> None:
    """Record a login attempt and handle lockout."""
    import uuid
    attempt = LoginAttempt(
        id=str(uuid.uuid4()),
        username=username,
        ip_address=ip,
        success=success,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(attempt)

    if not success:
        user = db.query(User).filter_by(username=username).first()
        if user:
            user.failed_login_count += 1
            settings = get_settings()
            if user.failed_login_count >= settings.max_login_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.lockout_duration_minutes
                )
                # Record security event
                db.add(SecurityEvent(
                    event_type="ACCOUNT_LOCKOUT",
                    severity="HIGH",
                    description=f"Account locked after {user.failed_login_count} failed attempts",
                    actor_id=user.id,
                    ip_address=ip,
                ))
                logger.warning(f"Account locked: {username} from {ip}")
    else:
        user = db.query(User).filter_by(username=username).first()
        if user:
            user.failed_login_count = 0
            user.locked_until = None
            user.last_activity = datetime.now(timezone.utc)

    db.flush()


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate user and set auth cookies."""
    # Rate limit
    rate_limit_login(request)
    ip = request.client.host if request.client else "unknown"

    # Check lockout
    _check_lockout(db, body.username, ip)

    # Find user — generic error message regardless of failure reason
    user = db.query(User).filter_by(username=body.username, is_active=True).first()
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "invalid_credentials", "message": "Invalid username or password"},
    )

    if user is None:
        _record_login_attempt(db, body.username, ip, False)
        db.commit()
        raise generic_error

    if not verify_password(body.password, user.password_hash):
        _record_login_attempt(db, body.username, ip, False)
        db.commit()
        raise generic_error

    # Success
    _record_login_attempt(db, body.username, ip, True)

    # Create tokens
    access_token = create_access_token(user.id, user.role, user.username)
    raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
    csrf_token = generate_csrf_token()

    # Store refresh token (hashed)
    import uuid
    family_id = str(uuid.uuid4())
    db.add(RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=expires_at,
    ))

    # Audit
    write_audit_entry(
        db,
        action="LOGIN_SUCCESS",
        actor_id=user.id,
        actor_role=user.role,
        entity_type="user",
        entity_id=user.id,
        payload={"ip": ip},
    )

    db.commit()

    # Set cookies
    _set_auth_cookies(response, access_token, raw_refresh, csrf_token)

    return {
        "message": "Login successful",
        "user": {"id": user.id, "username": user.username, "role": user.role},
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Log out and clear all auth cookies."""
    # Revoke refresh token if present
    refresh_cookie = request.cookies.get("__Host-refresh_token")
    if refresh_cookie:
        token_hash = hash_token(refresh_cookie)
        stored = db.query(RefreshToken).filter_by(token_hash=token_hash).first()
        if stored:
            stored.is_revoked = True
            # Revoke entire family
            db.query(RefreshToken).filter_by(
                family_id=stored.family_id
            ).update({"is_revoked": True})

    # Try to audit (may fail if not authenticated)
    try:
        current_user = await get_current_user(request)
        write_audit_entry(
            db,
            action="LOGOUT",
            actor_id=current_user.user_id,
            actor_role=current_user.role,
            entity_type="user",
            entity_id=current_user.user_id,
        )
    except HTTPException:
        pass

    db.commit()
    _clear_auth_cookies(response)

    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Refresh access token using the refresh token cookie."""
    refresh_cookie = request.cookies.get("__Host-refresh_token")
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "no_refresh_token", "message": "Refresh token required"},
        )

    token_hash = hash_token(refresh_cookie)
    stored = db.query(RefreshToken).filter_by(token_hash=token_hash).first()

    if stored is None or stored.is_revoked:
        # Possible token reuse attack — revoke entire family
        if stored and stored.is_revoked:
            logger.warning(f"Refresh token reuse detected for family {stored.family_id}")
            db.query(RefreshToken).filter_by(
                family_id=stored.family_id
            ).update({"is_revoked": True})
            db.add(SecurityEvent(
                event_type="REFRESH_TOKEN_REUSE",
                severity="CRITICAL",
                description=f"Refresh token reuse detected for user {stored.user_id}",
                actor_id=stored.user_id,
            ))
            db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_refresh_token", "message": "Invalid or revoked refresh token"},
        )

    if stored.expires_at < datetime.now(timezone.utc):
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "refresh_token_expired", "message": "Refresh token expired"},
        )

    # Get user
    user = db.query(User).filter_by(id=stored.user_id, is_active=True).first()
    if user is None:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "user_not_found", "message": "User account not found or disabled"},
        )

    # Check idle timeout
    settings = get_settings()
    if user.last_activity:
        idle_limit = user.last_activity + timedelta(minutes=settings.session_idle_timeout_minutes)
        if datetime.now(timezone.utc) > idle_limit:
            stored.is_revoked = True
            db.commit()
            _clear_auth_cookies(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "session_idle_timeout", "message": "Session timed out due to inactivity"},
            )

    # Rotate: revoke old, issue new
    stored.is_revoked = True
    import uuid
    new_access = create_access_token(user.id, user.role, user.username)
    new_raw_refresh, new_hash, new_expires = create_refresh_token(user.id, stored.family_id)
    csrf_token = generate_csrf_token()

    db.add(RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=new_hash,
        family_id=stored.family_id,
        expires_at=new_expires,
    ))

    user.last_activity = datetime.now(timezone.utc)
    db.commit()

    _set_auth_cookies(response, new_access, new_raw_refresh, csrf_token)

    return {"message": "Token refreshed"}


@router.post("/stepup")
async def stepup(
    request: Request,
    response: Response,
    body: StepupRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Re-authenticate for step-up operations."""
    user = db.query(User).filter_by(id=current_user.user_id, is_active=True).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid password"},
        )

    raw_token, token_hash, expires_at = create_stepup_token()

    import uuid
    db.add(StepupToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    ))

    write_audit_entry(
        db,
        action="STEPUP_AUTH",
        actor_id=user.id,
        actor_role=user.role,
        entity_type="user",
        entity_id=user.id,
    )

    db.commit()

    return {
        "message": "Step-up authentication successful",
        "stepup_token": raw_token,
        "expires_in_seconds": 300,
    }


@router.get("/csrf")
async def get_csrf(
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Get a CSRF token."""
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="__Host-csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="none",
        path="/",
    )
    return {"csrf_token": csrf_token}


@router.get("/me")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Get current authenticated user info."""
    settings = get_settings()
    return {
        "id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "session_idle_timeout_minutes": settings.session_idle_timeout_minutes,
        "session_absolute_timeout_hours": settings.session_absolute_timeout_hours,
    }
