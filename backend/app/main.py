"""AERIS Backend — Main FastAPI Application."""
from __future__ import annotations

import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import APP_NAME, get_settings
from app.core.logging import get_logger, setup_logging

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info(f"{APP_NAME} starting up", extra={
        "extra_data": {"env": settings.app_env, "version": "0.1.0"}
    })

    # Verify egress is blocked (air-gap check)
    _verify_egress_blocked()

    yield

    logger.info(f"{APP_NAME} shutting down")


def _verify_egress_blocked() -> None:
    """Attempt outbound connection; expect failure in air-gapped deployment."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(("8.8.8.8", 443))
        sock.close()
        if result == 0:
            logger.warning(
                "SECURITY: Outbound egress is NOT blocked. "
                "In production, the internal Docker network should prevent this."
            )
        else:
            logger.info("SECURITY: Egress blocked (verified at startup)")
    except (OSError, socket.timeout):
        logger.info("SECURITY: Egress blocked (verified at startup)")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    application = FastAPI(
        title=APP_NAME,
        description=(
            "Predictive Maintenance Decision-Support Platform. "
            "This system is a maintenance decision-support prototype. "
            "Predictions are not airworthiness or release-to-service decisions "
            "and are not validated for operational aircraft."
        ),
        version="0.1.0",
        docs_url="/api/docs" if settings.app_env == "development" else None,
        redoc_url="/api/redoc" if settings.app_env == "development" else None,
        openapi_url="/api/openapi.json" if settings.app_env == "development" else None,
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "aeris-local", "127.0.0.1"],
    )

    @application.middleware("http")
    async def security_headers_middleware(request: Request, call_next: Any) -> Response:
        """Add security headers to all responses."""
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return response

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any) -> Response:
        """Propagate or generate request ID."""
        request_id = request.headers.get("X-Request-ID", f"req-{int(time.time() * 1000)}")
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Health endpoint (unauthenticated) ─────────────────────
    @application.get("/api/v1/health", tags=["system"])
    async def health_check() -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": APP_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        }

    # ── Global exception handler ──────────────────────────────
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            exc_info=exc,
            extra={"extra_data": {"request_id": request_id}},
        )
        # Never expose stack traces to clients
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            },
        )

    return application


app = create_app()
