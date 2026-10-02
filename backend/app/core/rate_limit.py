"""AERIS Backend — Rate Limiting.

In-memory rate limiter for API endpoints. Uses sliding window counters.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any

from fastapi import HTTPException, Request, status

from app.core.logging import get_logger

logger = get_logger("rate_limit")


class RateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is within rate limit.
        
        Returns True if allowed, False if rate-limited.
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Clean old entries
            self._windows[key] = [
                ts for ts in self._windows[key] if ts > cutoff
            ]

            if len(self._windows[key]) >= limit:
                return False

            self._windows[key].append(now)
            return True

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        """Get seconds until the rate limit resets."""
        with self._lock:
            if not self._windows[key]:
                return 0
            oldest = min(self._windows[key])
            return max(1, int(oldest + window_seconds - time.time()))


# Global rate limiter instance
_limiter = RateLimiter()


def rate_limit_login(request: Request) -> None:
    """Rate limit for login attempts: 5/minute per IP."""
    ip = request.client.host if request.client else "unknown"
    key = f"login:{ip}"
    if not _limiter.check(key, limit=5, window_seconds=60):
        retry_after = _limiter.get_retry_after(key, 60)
        logger.warning(f"Rate limit exceeded for login from {ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many login attempts. Please try again later.",
            },
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit_api(request: Request, user_id: str) -> None:
    """Rate limit for API requests: 120/minute per user."""
    key = f"api:{user_id}"
    if not _limiter.check(key, limit=120, window_seconds=60):
        retry_after = _limiter.get_retry_after(key, 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
            },
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit_upload(request: Request, user_id: str) -> None:
    """Rate limit for uploads: 10/hour per user."""
    key = f"upload:{user_id}"
    if not _limiter.check(key, limit=10, window_seconds=3600):
        retry_after = _limiter.get_retry_after(key, 3600)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many uploads. Please try again later.",
            },
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit_scenario(request: Request, user_id: str) -> None:
    """Rate limit for scenario/forecast runs: 20/minute per user."""
    key = f"scenario:{user_id}"
    if not _limiter.check(key, limit=20, window_seconds=60):
        retry_after = _limiter.get_retry_after(key, 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many scenario runs. Please try again later.",
            },
            headers={"Retry-After": str(retry_after)},
        )
