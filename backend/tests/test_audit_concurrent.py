import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.audit import write_audit_entry, verify_audit_chain
from app.db.models import AuditLog


def test_concurrent_audit_writes(db_session: Session):
    """Stress test: 50 parallel writers appending to the audit log concurrently."""
    # Ensure audit log is empty
    db_session.query(AuditLog).delete()
    db_session.commit()

    NUM_WRITERS = 50
    exceptions = []

    def write_entry(i):
        # We need a separate session per thread
        from app.db.session import SessionLocal
        local_db = SessionLocal()
        try:
            write_audit_entry(
                local_db,
                action=f"concurrent_test_{i}",
                actor_id="test_user",
            )
            local_db.commit()
        except Exception as e:
            exceptions.append(e)
            local_db.rollback()
        finally:
            local_db.close()

    with ThreadPoolExecutor(max_workers=NUM_WRITERS) as executor:
        futures = [executor.submit(write_entry, i) for i in range(NUM_WRITERS)]
        for f in futures:
            f.result()

    assert not exceptions, f"Exceptions occurred during concurrent writes: {exceptions}"

    # Verify the chain is intact
    is_valid, error = verify_audit_chain(db_session)
    assert is_valid, f"Audit chain broken: {error}"
