"""AERIS Backend — Audit Module.

Hash-chained append-only audit log. Genesis hash = SHA256("VAYU-PdM-GENESIS").
entry_hash = SHA256(prev_hash || canonical_json(entry)).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from app.core.crypto import canonical_json, sha256_hash_str
from app.core.logging import get_logger
from app.db.models import AuditLog

logger = get_logger("audit")

GENESIS_HASH = hashlib.sha256(b"VAYU-PdM-GENESIS").hexdigest()


def _get_prev_hash(db: Session) -> str:
    """Get the hash of the last audit entry, or genesis hash, with lock."""
    # Acquire transaction-level advisory lock on PostgreSQL to serialize audit writers
    try:
        bind = db.get_bind()
        if bind and bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(1001)"))
    except Exception:
        pass

    try:
        last_entry = (
            db.query(AuditLog.entry_hash)
            .order_by(desc(AuditLog.ts))
            .first()
        )
        if last_entry is None:
            return GENESIS_HASH
        return last_entry.entry_hash  # type: ignore[return-value]
    except Exception:
        return GENESIS_HASH


def _compute_entry_hash(prev_hash: str, entry_data: dict[str, Any]) -> str:
    """Compute hash for audit chain: SHA256(prev_hash || canonical_json(entry))."""
    canon = canonical_json(entry_data)
    to_hash = prev_hash + canon
    return sha256_hash_str(to_hash)


def write_audit_entry(
    db: Session,
    *,
    action: str,
    actor_id: str | None = None,
    actor_role: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    model_version: str | None = None,
    payload: dict[str, Any] | None = None,
) -> str:
    """Write an audit entry to the hash-chained log.
    
    Returns the entry hash.
    """
    try:
        entry_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc)
        prev_hash = _get_prev_hash(db)

        entry_data = {
            "id": entry_id,
            "ts": ts.isoformat(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "model_version": model_version,
            "payload_json": payload,
        }

        entry_hash = _compute_entry_hash(prev_hash, entry_data)

        audit_entry = AuditLog(
            id=entry_id,
            ts=ts,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            model_version=model_version,
            payload_json=payload,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )

        db.add(audit_entry)
        db.flush()  # Ensure it's written immediately

        logger.info(
            f"Audit: {action}",
            extra={"extra_data": {
                "action": action,
                "actor_id": actor_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entry_hash": entry_hash[:16] + "...",
            }},
        )

        return entry_hash
    except Exception as e:
        logger.warning(f"Audit log write failed (non-blocking): {e}")
        return "audit_fallback_hash"


def verify_audit_chain(db: Session) -> dict[str, Any]:
    """Verify the integrity of the entire audit hash chain.
    
    Returns:
        {
            "status": "VERIFIED" | "TAMPERED" | "EMPTY",
            "total_entries": int,
            "verified_entries": int,
            "first_tampered_id": str | None,
            "head_hash": str | None,
        }
    """
    entries = (
        db.query(AuditLog)
        .order_by(AuditLog.ts.asc())
        .all()
    )

    if not entries:
        return {
            "status": "EMPTY",
            "total_entries": 0,
            "verified_entries": 0,
            "first_tampered_id": None,
            "head_hash": None,
        }

    expected_prev_hash = GENESIS_HASH
    verified_count = 0

    for entry in entries:
        # Reconstruct the entry data
        entry_data = {
            "id": entry.id,
            "ts": entry.ts.isoformat() if entry.ts else None,
            "actor_id": entry.actor_id,
            "actor_role": entry.actor_role,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "model_version": entry.model_version,
            "payload_json": entry.payload_json,
        }

        # Check prev_hash links correctly
        if entry.prev_hash != expected_prev_hash:
            logger.error(
                f"Audit chain broken at entry {entry.id}: "
                f"expected prev_hash={expected_prev_hash[:16]}..., "
                f"got {entry.prev_hash[:16]}..."
            )
            return {
                "status": "TAMPERED",
                "total_entries": len(entries),
                "verified_entries": verified_count,
                "first_tampered_id": entry.id,
                "head_hash": entries[-1].entry_hash,
            }

        # Recompute entry hash
        expected_hash = _compute_entry_hash(expected_prev_hash, entry_data)
        if entry.entry_hash != expected_hash:
            logger.error(
                f"Audit entry hash mismatch at {entry.id}: "
                f"expected={expected_hash[:16]}..., "
                f"got={entry.entry_hash[:16]}..."
            )
            return {
                "status": "TAMPERED",
                "total_entries": len(entries),
                "verified_entries": verified_count,
                "first_tampered_id": entry.id,
                "head_hash": entries[-1].entry_hash,
            }

        expected_prev_hash = entry.entry_hash
        verified_count += 1

    return {
        "status": "VERIFIED",
        "total_entries": len(entries),
        "verified_entries": verified_count,
        "first_tampered_id": None,
        "head_hash": entries[-1].entry_hash,
    }
