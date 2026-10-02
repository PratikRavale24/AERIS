"""AERIS Backend — System API Routes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.core.config import APP_NAME

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint (unauthenticated, minimal)."""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_source": "SYNTHETIC_NON_OPERATIONAL",
    }
