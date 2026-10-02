"""AERIS Backend — Auth Pydantic Schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Login response."""
    message: str
    user: UserInfo


class UserInfo(BaseModel):
    """Public user information."""
    id: str
    username: str
    role: str


class StepupRequest(BaseModel):
    """Step-up re-authentication request."""
    password: str = Field(..., min_length=1, max_length=128)


class StepupResponse(BaseModel):
    """Step-up response with the step-up token."""
    message: str
    expires_in_seconds: int


class RefreshResponse(BaseModel):
    """Token refresh response."""
    message: str


class CSRFResponse(BaseModel):
    """CSRF token response."""
    csrf_token: str


class MeResponse(BaseModel):
    """Current user info response."""
    id: str
    username: str
    role: str
    session_idle_timeout_minutes: int
    session_absolute_timeout_hours: int


# Fix forward reference
LoginResponse.model_rebuild()
