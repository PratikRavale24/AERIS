"""AERIS Backend — Core Configuration.

All configuration is loaded from environment variables and Docker secrets.
The APP_NAME constant is the single place to rename the application.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings


# ── Single rename constant ──────────────────────────────────────────
APP_NAME: str = os.environ.get("APP_NAME", "AERIS")

# ── Docker secrets reader ───────────────────────────────────────────
SECRETS_DIR = Path("/run/secrets")


def read_secret(name: str, default: str = "") -> str:
    """Read a Docker secret file. Falls back to env var or default."""
    secret_path = SECRETS_DIR / name
    if secret_path.exists():
        return secret_path.read_text().strip()
    return os.environ.get(name.upper(), default)


def read_json_secret(name: str) -> dict[str, Any]:
    """Read a Docker secret that contains JSON."""
    raw = read_secret(name)
    if raw:
        return json.loads(raw)  # type: ignore[no-any-return]
    return {}


class Settings(BaseSettings):
    """Application settings loaded from env vars and secrets."""

    # Application
    app_name: str = Field(default=APP_NAME)
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    data_source_label: str = Field(default="SYNTHETIC_NON_OPERATIONAL")

    # Database
    postgres_db: str = Field(default="aeris")
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)

    # Server
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    backend_workers: int = Field(default=2)

    # JWT & Sessions
    jwt_access_token_expire_minutes: int = Field(default=10)
    jwt_refresh_token_expire_hours: int = Field(default=8)
    session_idle_timeout_minutes: int = Field(default=15)
    session_absolute_timeout_hours: int = Field(default=8)

    # Rate limits
    rate_limit_login: str = Field(default="5/minute")
    rate_limit_api: str = Field(default="120/minute")
    rate_limit_upload: str = Field(default="10/hour")

    # ML
    rul_ref_cycles: int = Field(default=100)
    failure_horizon_cycles: int = Field(default=30)
    availability_target_percent: int = Field(default=70)

    # Lockout
    max_login_attempts: int = Field(default=5)
    lockout_duration_minutes: int = Field(default=15)

    # Password policy
    min_password_length: int = Field(default=12)

    @property
    def database_url(self) -> str:
        """Build the database URL using the app role (DML only) or full env URL."""
        if os.environ.get("DATABASE_URL"):
            url = os.environ.get("DATABASE_URL")
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            return url
        password = read_secret("db_password")
        return (
            f"postgresql+psycopg2://vayu_app:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_async(self) -> str:
        """Build the async database URL."""
        if os.environ.get("DATABASE_URL"):
            url = os.environ.get("DATABASE_URL")
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
            return url
        password = read_secret("db_password")
        return (
            f"postgresql+asyncpg://vayu_app:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def migrator_database_url(self) -> str:
        """Build the database URL using the migrator role (DDL)."""
        if os.environ.get("DATABASE_URL"):
            url = os.environ.get("DATABASE_URL")
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            return url
        password = read_secret("db_migrator_password")
        return (
            f"postgresql+psycopg2://vayu_migrator:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def jwt_signing_key(self) -> str:
        return read_secret("jwt_signing_key")

    @property
    def aes_encryption_config(self) -> dict[str, Any]:
        return read_json_secret("aes_encryption_key")

    @property
    def model_hmac_key(self) -> str:
        return read_secret("model_hmac_key")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
