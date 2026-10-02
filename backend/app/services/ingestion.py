"""AERIS Backend — Data Ingestion Service.

Validates, quarantines bad rows, and ingests CSV data into the database.
Handles: aircraft, components, health, maintenance, inspections, spares, facilities.
"""
from __future__ import annotations

import csv
import hashlib
import json
import uuid
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import write_audit_entry
from app.core.crypto import encrypt_field
from app.core.logging import get_logger
from app.db.models import (
    Aircraft,
    Component,
    DataQualityReport,
    Facility,
    HealthObservation,
    IngestBatch,
    InspectionFinding,
    MaintenanceEvent,
    QuarantinedRow,
    SparePart,
)

logger = get_logger("ingestion")

DATA_DIR = Path("/app/data/synthetic/fleet")

# Sensor ranges for validation
SENSOR_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "ENGINE": {
        "egt_c": (200, 1200),
        "n1_rpm": (3000, 15000),
        "n2_rpm": (5000, 20000),
        "vibration_mm_s": (0, 30),
        "oil_pressure_kpa": (50, 700),
        "oil_temp_c": (10, 200),
        "fuel_flow_kg_h": (200, 4000),
    },
    "HYDRAULIC_PUMP": {
        "outlet_pressure_kpa": (1000, 40000),
        "flow_l_min": (1, 100),
        "case_temp_c": (5, 150),
        "vibration_mm_s": (0, 25),
    },
    "GEARBOX": {
        "vibration_mm_s": (0, 40),
        "oil_temp_c": (10, 180),
        "metal_particle_count": (0, 600),
        "torque_nm": (500, 15000),
    },
}


class ValidationResult:
    """Track validation results for a batch."""

    def __init__(self) -> None:
        self.accepted: int = 0
        self.quarantined: int = 0
        self.quarantined_rows: list[dict[str, Any]] = []
        self.issues: list[str] = []

    def quarantine(self, row_num: int, row_data: dict[str, Any], reason: str, severity: str = "ERROR") -> None:
        self.quarantined += 1
        self.quarantined_rows.append({
            "row_number": row_num,
            "row_data": row_data,
            "reason": reason,
            "severity": severity,
        })
        self.issues.append(f"Row {row_num}: {reason}")

    def accept(self) -> None:
        self.accepted += 1


def _compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_health_row(
    row: dict[str, Any],
    row_num: int,
    result: ValidationResult,
    known_components: set[str],
    seen_keys: set[str],
) -> bool:
    """Validate a single health observation row."""
    comp_id = row.get("component_id", "")

    # Check for unknown component
    if comp_id not in known_components:
        result.quarantine(row_num, row, f"Unknown component_id: {comp_id}")
        return False

    # Check for missing value
    value_str = row.get("value")
    if value_str is None or value_str == "" or value_str == "None":
        result.quarantine(row_num, row, "Missing sensor value", "WARNING")
        return False

    # Parse value
    try:
        value = float(value_str)
    except (ValueError, TypeError):
        result.quarantine(row_num, row, f"Invalid sensor value: {value_str}")
        return False

    # Check for out-of-range spikes
    sensor = row.get("sensor", "")
    comp_type = comp_id.split("-")[-2] if "-" in comp_id else ""
    type_map = {"ENG": "ENGINE", "HYD": "HYDRAULIC_PUMP", "GBX": "GEARBOX"}
    comp_type_full = type_map.get(comp_type, "")

    if comp_type_full in SENSOR_RANGES:
        ranges = SENSOR_RANGES[comp_type_full]
        if sensor in ranges:
            low, high = ranges[sensor]
            if value < low or value > high:
                result.quarantine(row_num, row, f"Value {value} out of range [{low}, {high}] for {sensor}", "WARNING")
                return False

    # Check unit consistency (fahrenheit flagged as potential mismatch)
    unit = row.get("unit", "")
    if unit == "fahrenheit" and sensor in ("egt_c", "oil_temp_c", "case_temp_c"):
        result.quarantine(row_num, row, f"Unit mismatch: {sensor} reported in {unit}, expected celsius", "WARNING")
        return False

    # Check for duplicates
    dup_key = f"{comp_id}|{row.get('cycle')}|{sensor}"
    if dup_key in seen_keys:
        result.quarantine(row_num, row, "Duplicate row", "WARNING")
        return False
    seen_keys.add(dup_key)

    # Timestamp ordering check (basic)
    ts = row.get("timestamp", "")
    if not ts:
        result.quarantine(row_num, row, "Missing timestamp")
        return False

    result.accept()
    return True


def ingest_aircraft(db: Session, filepath: Path) -> ValidationResult:
    """Ingest aircraft.csv."""
    result = ValidationResult()
    file_hash = _compute_file_hash(filepath)

    batch = IngestBatch(
        id=str(uuid.uuid4()),
        dataset="aircraft",
        filename=filepath.name,
        file_sha256=file_hash,
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                ac = Aircraft(
                    aircraft_id=row["aircraft_id"],
                    platform_type=row["platform_type"],
                    status=row.get("status", "AVAILABLE"),
                    age_years=float(row["age_years"]),
                    total_cycles=int(row["total_cycles"]),
                    criticality=int(row["criticality"]),
                    cycles_per_day=float(row.get("cycles_per_day", "1.2")),
                    data_source=row.get("data_source", "SYNTHETIC_NON_OPERATIONAL"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.merge(ac)
                result.accept()
            except Exception as e:
                result.quarantine(i, row, str(e))

    batch.row_count_total = result.accepted + result.quarantined
    batch.row_count_accepted = result.accepted
    batch.row_count_quarantined = result.quarantined
    batch.status = "COMPLETED"
    batch.updated_at = datetime.now(timezone.utc)

    _save_quarantined(db, batch.id, result)
    db.flush()
    return result


def ingest_components(db: Session, filepath: Path) -> ValidationResult:
    """Ingest components.csv."""
    result = ValidationResult()
    file_hash = _compute_file_hash(filepath)

    batch = IngestBatch(
        id=str(uuid.uuid4()),
        dataset="components",
        filename=filepath.name,
        file_sha256=file_hash,
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                comp = Component(
                    component_id=row["component_id"],
                    aircraft_id=row["aircraft_id"],
                    component_type=row["component_type"],
                    subsystem=row["subsystem"],
                    part_no=row["part_no"],
                    install_cycle=int(row.get("install_cycle", "0")),
                    data_source=row.get("data_source", "SYNTHETIC_NON_OPERATIONAL"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.merge(comp)
                result.accept()
            except Exception as e:
                result.quarantine(i, row, str(e))

    batch.row_count_total = result.accepted + result.quarantined
    batch.row_count_accepted = result.accepted
    batch.row_count_quarantined = result.quarantined
    batch.status = "COMPLETED"
    batch.updated_at = datetime.now(timezone.utc)

    _save_quarantined(db, batch.id, result)
    db.flush()
    return result


def ingest_health(db: Session, filepath: Path) -> ValidationResult:
    """Ingest health.csv with full validation."""
    result = ValidationResult()
    file_hash = _compute_file_hash(filepath)

    batch = IngestBatch(
        id=str(uuid.uuid4()),
        dataset="health",
        filename=filepath.name,
        file_sha256=file_hash,
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    # Get known components
    known_components = set(
        row[0] for row in db.query(Component.component_id).all()
    )
    seen_keys: set[str] = set()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_buffer: list[HealthObservation] = []

        for i, row in enumerate(reader, 1):
            if _validate_health_row(row, i, result, known_components, seen_keys):
                obs = HealthObservation(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    aircraft_id=row["aircraft_id"],
                    component_id=row["component_id"],
                    sensor=row["sensor"],
                    value=float(row["value"]),
                    unit=row["unit"],
                    cycle=int(row["cycle"]),
                    operating_context=json.loads(row.get("operating_context", "{}")),
                    data_source=row.get("data_source", "SYNTHETIC_NON_OPERATIONAL"),
                    batch_id=batch.id,
                    created_at=datetime.now(timezone.utc),
                )
                rows_buffer.append(obs)

                # Batch insert every 1000 rows
                if len(rows_buffer) >= 1000:
                    db.bulk_save_objects(rows_buffer)
                    rows_buffer = []

        if rows_buffer:
            db.bulk_save_objects(rows_buffer)

    batch.row_count_total = result.accepted + result.quarantined
    batch.row_count_accepted = result.accepted
    batch.row_count_quarantined = result.quarantined
    batch.status = "COMPLETED"
    batch.updated_at = datetime.now(timezone.utc)

    _save_quarantined(db, batch.id, result)
    db.flush()

    # Generate data quality report
    _generate_quality_report(db, known_components)

    return result


def ingest_maintenance(db: Session, filepath: Path) -> ValidationResult:
    """Ingest maintenance.csv."""
    result = ValidationResult()
    file_hash = _compute_file_hash(filepath)

    batch = IngestBatch(
        id=str(uuid.uuid4()),
        dataset="maintenance",
        filename=filepath.name,
        file_sha256=file_hash,
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                notes = row.get("technician_notes", "")
                encrypted_notes = encrypt_field(notes) if notes else None

                event = MaintenanceEvent(
                    event_id=row.get("event_id", str(uuid.uuid4())),
                    aircraft_id=row["aircraft_id"],
                    component_id=row.get("component_id"),
                    fault_code=row.get("fault_code"),
                    event_type=row["event_type"],
                    severity=row["severity"],
                    opened_at=datetime.fromisoformat(row["opened_at"]),
                    closed_at=datetime.fromisoformat(row["closed_at"]) if row.get("closed_at") else None,
                    action=row.get("action"),
                    technician_notes_encrypted=encrypted_notes,
                    data_source=row.get("data_source", "SYNTHETIC_NON_OPERATIONAL"),
                    created_at=datetime.now(timezone.utc),
                )
                db.merge(event)
                result.accept()
            except Exception as e:
                result.quarantine(i, row, str(e))

    batch.row_count_total = result.accepted + result.quarantined
    batch.row_count_accepted = result.accepted
    batch.row_count_quarantined = result.quarantined
    batch.status = "COMPLETED"
    batch.updated_at = datetime.now(timezone.utc)

    _save_quarantined(db, batch.id, result)
    db.flush()
    return result


def ingest_spares(db: Session, filepath: Path) -> ValidationResult:
    """Ingest spares.csv."""
    result = ValidationResult()
    file_hash = _compute_file_hash(filepath)

    batch = IngestBatch(
        id=str(uuid.uuid4()),
        dataset="spares",
        filename=filepath.name,
        file_sha256=file_hash,
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                spare = SparePart(
                    part_no=row["part_no"],
                    description=row.get("description"),
                    stock=int(row["stock"]),
                    min_stock=int(row["min_stock"]),
                    lead_time_days=int(row["lead_time_days"]),
                    criticality=row.get("criticality", "MEDIUM"),
                    facility_id=row.get("facility_id"),
                    data_source=row.get("data_source", "SYNTHETIC_NON_OPERATIONAL"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.merge(spare)
                result.accept()
            except Exception as e:
                result.quarantine(i, row, str(e))

    batch.row_count_total = result.accepted + result.quarantined
    batch.row_count_accepted = result.accepted
    batch.row_count_quarantined = result.quarantined
    batch.status = "COMPLETED"
    _save_quarantined(db, batch.id, result)
    db.flush()
    return result


def ingest_facilities(db: Session, filepath: Path) -> ValidationResult:
    """Ingest facilities.csv."""
    result = ValidationResult()
    file_hash = _compute_file_hash(filepath)

    batch = IngestBatch(
        id=str(uuid.uuid4()),
        dataset="facilities",
        filename=filepath.name,
        file_sha256=file_hash,
        status="PROCESSING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.flush()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                fac = Facility(
                    facility_id=row["facility_id"],
                    name=row["name"],
                    capability=row["capability"],
                    slots_available=int(row["slots_available"]),
                    avg_turnaround_days=float(row["avg_turnaround_days"]),
                    data_source=row.get("data_source", "SYNTHETIC_NON_OPERATIONAL"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.merge(fac)
                result.accept()
            except Exception as e:
                result.quarantine(i, row, str(e))

    batch.row_count_total = result.accepted + result.quarantined
    batch.row_count_accepted = result.accepted
    batch.row_count_quarantined = result.quarantined
    batch.status = "COMPLETED"
    _save_quarantined(db, batch.id, result)
    db.flush()
    return result


def _save_quarantined(db: Session, batch_id: str, result: ValidationResult) -> None:
    """Save quarantined rows to database."""
    for qr in result.quarantined_rows:
        db.add(QuarantinedRow(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            row_number=qr["row_number"],
            row_data=qr["row_data"],
            reason=qr["reason"],
            severity=qr.get("severity", "ERROR"),
            created_at=datetime.now(timezone.utc),
        ))


def _generate_quality_report(db: Session, known_components: set[str]) -> None:
    """Generate data quality scores per component."""
    from sqlalchemy import func

    for comp_id in known_components:
        total = db.query(func.count(HealthObservation.id)).filter(
            HealthObservation.component_id == comp_id
        ).scalar() or 0

        if total == 0:
            quality_score = 0.0
            flags = ["NO_DATA"]
        else:
            # Simple quality score: 1 - (quarantined / total)
            quality_score = 1.0  # Will be refined with more checks
            flags = []

            # Check for flat-line sensors
            from sqlalchemy import distinct
            distinct_values = db.query(
                func.count(distinct(HealthObservation.value))
            ).filter(
                HealthObservation.component_id == comp_id
            ).scalar() or 0

            if distinct_values < 5 and total > 10:
                quality_score -= 0.3
                flags.append("POSSIBLE_FLATLINE")

            quality_score = max(0.0, min(1.0, quality_score))

        report = DataQualityReport(
            id=str(uuid.uuid4()),
            component_id=comp_id,
            quality_score=quality_score,
            flags=flags,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report)

    db.flush()


def ingest_all_datasets(db: Session) -> dict[str, Any]:
    """Ingest all synthetic datasets in dependency order."""
    results: dict[str, dict[str, int]] = {}

    datasets = [
        ("aircraft", ingest_aircraft, DATA_DIR / "aircraft.csv"),
        ("components", ingest_components, DATA_DIR / "components.csv"),
        ("facilities", ingest_facilities, DATA_DIR / "facilities.csv"),
        ("spares", ingest_spares, DATA_DIR / "spares.csv"),
        ("maintenance", ingest_maintenance, DATA_DIR / "maintenance.csv"),
        ("health", ingest_health, DATA_DIR / "health.csv"),
    ]

    for name, ingest_fn, filepath in datasets:
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}, skipping {name}")
            results[name] = {"accepted": 0, "quarantined": 0, "error": "file_not_found"}
            continue

        logger.info(f"Ingesting {name} from {filepath}...")
        try:
            result = ingest_fn(db, filepath)
            results[name] = {
                "accepted": result.accepted,
                "quarantined": result.quarantined,
            }
            logger.info(
                f"  {name}: {result.accepted} accepted, {result.quarantined} quarantined"
            )
        except Exception as e:
            logger.error(f"  {name}: ingestion failed: {e}")
            results[name] = {"accepted": 0, "quarantined": 0, "error": str(e)}

    # Audit the ingestion
    write_audit_entry(
        db,
        action="DATA_INGESTION_COMPLETE",
        entity_type="system",
        payload=results,
    )

    db.commit()
    return results
