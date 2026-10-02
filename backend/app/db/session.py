"""AERIS Backend — Database Session Management."""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def get_engine():  # type: ignore[no-untyped-def]
    """Create SQLAlchemy engine with the app role (DML only)."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
    )


_session_factory: sessionmaker[Session] | None = None


def get_session_factory() -> sessionmaker[Session]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session and ensures cleanup."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
