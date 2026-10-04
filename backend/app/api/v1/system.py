"""AERIS Backend — System API Routes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from sqlalchemy import text

from app.core.config import APP_NAME
from app.db.session import get_engine

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint (unauthenticated, includes DB diagnosis)."""
    db_status = "unknown"
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        dialect = engine.dialect.name
        db_status = f"connected ({dialect})"
    except Exception as e:
        db_status = f"error: {type(e).__name__} - {str(e)}"

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": "0.1.4",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_source": "SYNTHETIC_NON_OPERATIONAL",
    }


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """System metrics summary."""
    return {
        "status": "operational",
        "uptime": "normal",
        "data_source": "SYNTHETIC_NON_OPERATIONAL",
    }
