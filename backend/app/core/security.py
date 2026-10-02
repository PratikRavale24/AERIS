"""AERIS Backend — Security Module.

Argon2id password hashing, JWT management via HttpOnly cookies, CSRF tokens,
constant-time comparison, and session management.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings, read_secret
from app.core.logging import get_logger

logger = get_logger("security")

# Argon2id hasher with secure defaults
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its Argon2id hash. Constant-time."""
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def check_password_policy(password: str) -> list[str]:
    """Check password meets policy requirements. Returns list of violations."""
    settings = get_settings()
    violations: list[str] = []
    if len(password) < settings.min_password_length:
        violations.append(f"Password must be at least {settings.min_password_length} characters")
    if not any(c.isupper() for c in password):
        violations.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        violations.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        violations.append("Password must contain at least one digit")
    return violations


# ── JWT Token Management ───────────────────────────────────────────

def create_access_token(user_id: str, role: str, username: str) -> str:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "username": username,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_signing_key, algorithm="HS256")


def create_refresh_token(user_id: str, family_id: str | None = None) -> tuple[str, str, datetime]:
    """Create a refresh token. Returns (raw_token, token_hash, expires_at)."""
    settings = get_settings()
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.jwt_refresh_token_expire_hours
    )
    if family_id is None:
        family_id = str(uuid.uuid4())
    return raw_token, token_hash, expires_at


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_signing_key,
            algorithms=["HS256"],
            options={"require": ["sub", "role", "exp", "type"]},
        )
        if payload.get("type") != "access":
            return None
        return payload  # type: ignore[no-any-return]
    except jwt.ExpiredSignatureError:
        logger.debug("Access token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid access token: {e}")
        return None


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── CSRF ───────────────────────────────────────────────────────────

def generate_csrf_token() -> str:
    """Generate a cryptographically random CSRF token."""
    return secrets.token_urlsafe(32)


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


# ── Step-up Auth ───────────────────────────────────────────────────

def create_stepup_token() -> tuple[str, str, datetime]:
    """Create a step-up re-authentication token (5-min validity)."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    return raw_token, token_hash, expires_at
