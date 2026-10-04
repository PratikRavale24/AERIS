"""AERIS — Database Seeding.

Seeds the database with synthetic data and demo users.
Run as: python -m app.db.seed [--ingest] [--users]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings, read_secret
from app.core.logging import get_logger, setup_logging

logger = get_logger("seed")


def create_demo_users(session) -> None:  # type: ignore[no-untyped-def]
    """Create demo users from secrets/demo_credentials.txt."""
    from argon2 import PasswordHasher
    from app.db.models import User

    ph = PasswordHasher()
    creds_path = Path("/run/secrets/../demo_credentials.txt")

    # Demo usernames mapped to database role enum
    demo_users = [
        ("commander1", "FLEET_SUPERVISOR"),
        ("supervisor1", "MAINT_PLANNER"),
        ("engineer1", "MAINT_ENGINEER"),
        ("logistics1", "SPARES_PLANNER"),
        ("auditor1", "SYS_ADMIN"),
        ("admin1", "SYS_ADMIN"),
        ("fleet_supervisor", "FLEET_SUPERVISOR"),
        ("maint_planner", "MAINT_PLANNER"),
        ("maint_engineer", "MAINT_ENGINEER"),
        ("spares_planner", "SPARES_PLANNER"),
        ("sys_admin", "SYS_ADMIN"),
    ]

    # Read passwords from demo_credentials.txt
    passwords: dict[str, str] = {}
    creds_file = Path("/app/secrets/demo_credentials.txt")
    if not creds_file.exists():
        # Try mounted secrets path
        creds_file = Path("/run/secrets/demo_credentials.txt")

    if creds_file.exists():
        for line in creds_file.read_text().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3 and parts[0] and not parts[0].startswith(("=", "-", "Username")):
                passwords[parts[0]] = parts[2]

    default_passwords = {
        "commander1": "DemoCommander1Pass123!",
        "supervisor1": "DemoSupervisor1Pass123!",
        "engineer1": "DemoEngineer1Pass123!",
        "logistics1": "DemoLogistics1Pass123!",
        "auditor1": "DemoAuditor1Pass123!",
        "admin1": "DemoAdmin1Pass123!",
        "fleet_supervisor": "DemoCommander1Pass123!",
        "maint_planner": "DemoSupervisor1Pass123!",
        "maint_engineer": "DemoEngineer1Pass123!",
        "spares_planner": "DemoLogistics1Pass123!",
        "sys_admin": "DemoAdmin1Pass123!",
    }

    for username, role in demo_users:
        password = passwords.get(username) or default_passwords.get(username, f"Demo{username.capitalize()}Pass123!")
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            existing.password_hash = ph.hash(password)
            existing.is_active = True
            existing.failed_login_count = 0
            existing.locked_until = None
            logger.info(f"User {username} refreshed with active credentials")
            continue

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=ph.hash(password),
            role=role,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(user)
        logger.info(f"Created demo user: {username} ({role})")

    session.commit()


def main() -> None:
    """Main seed entrypoint."""
    parser = argparse.ArgumentParser(description="AERIS Database Seeder")
    parser.add_argument("--ingest", action="store_true", help="Ingest synthetic data")
    parser.add_argument("--users", action="store_true", help="Create demo users")
    parser.add_argument("--all", action="store_true", help="Run all seed steps")
    args = parser.parse_args()

    setup_logging("INFO")

    from app.db.session import get_session_factory

    factory = get_session_factory()
    session = factory()

    try:
        if args.users or args.all:
            logger.info("Creating demo users...")
            create_demo_users(session)

        if args.ingest or args.all:
            logger.info("Ingesting synthetic data...")
            from app.services.ingestion import ingest_all_datasets
            ingest_all_datasets(session)

        logger.info("Seed complete.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
