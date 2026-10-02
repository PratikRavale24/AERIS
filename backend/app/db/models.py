"""AERIS Backend — SQLAlchemy Database Models.

All tables with UUID/text PKs, created_at/updated_at, FKs, and proper indexes.
Audit log is hash-chained and append-only (enforced by Postgres triggers).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ── Users and Auth ──────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email_encrypted = Column(Text, nullable=True)  # AES-256-GCM encrypted
    password_hash = Column(String(256), nullable=False)
    role = Column(
        Enum(
            "FLEET_SUPERVISOR", "MAINT_PLANNER", "MAINT_ENGINEER",
            "SPARES_PLANNER", "SYS_ADMIN",
            name="user_role",
        ),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    failed_login_count = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    totp_secret_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False)
    family_id = Column(String(36), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(String(36), primary_key=True, default=_uuid)
    username = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)


class StepupToken(Base):
    __tablename__ = "stepup_tokens"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Fleet and Components ─────────────────────────────────────────────

class Aircraft(Base):
    __tablename__ = "aircraft"

    aircraft_id = Column(String(16), primary_key=True)
    platform_type = Column(String(32), nullable=False)
    status = Column(
        Enum(
            "AVAILABLE", "AVAILABLE_MONITOR", "SCHEDULED_MAINTENANCE",
            "AOG_AWAITING_PARTS", "UNSERVICEABLE",
            name="aircraft_status",
        ),
        nullable=False,
        default="AVAILABLE",
    )
    age_years = Column(Float, nullable=False)
    total_cycles = Column(Integer, nullable=False)
    criticality = Column(Integer, nullable=False)  # 1-3
    cycles_per_day = Column(Float, nullable=False, default=1.2)
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    components = relationship("Component", back_populates="aircraft", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_aircraft_status", "status"),
    )


class Component(Base):
    __tablename__ = "components"

    component_id = Column(String(32), primary_key=True)
    aircraft_id = Column(String(16), ForeignKey("aircraft.aircraft_id", ondelete="CASCADE"), nullable=False, index=True)
    component_type = Column(
        Enum("ENGINE", "HYDRAULIC_PUMP", "GEARBOX", name="component_type"),
        nullable=False,
    )
    subsystem = Column(String(32), nullable=False)
    part_no = Column(String(16), nullable=False, index=True)
    install_cycle = Column(Integer, nullable=False, default=0)
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    aircraft = relationship("Aircraft", back_populates="components")


# ── Health Telemetry ─────────────────────────────────────────────────

class HealthObservation(Base):
    __tablename__ = "health_observations"

    id = Column(String(36), primary_key=True, default=_uuid)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    aircraft_id = Column(String(16), ForeignKey("aircraft.aircraft_id"), nullable=False)
    component_id = Column(String(32), ForeignKey("components.component_id"), nullable=False)
    sensor = Column(String(32), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(16), nullable=False)
    cycle = Column(Integer, nullable=False)
    operating_context = Column(JSON, nullable=True)
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    batch_id = Column(String(36), ForeignKey("ingest_batches.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_health_component_cycle", "component_id", "cycle"),
        Index("ix_health_aircraft", "aircraft_id"),
        Index("ix_health_created", "created_at"),
    )


# ── Maintenance Records ─────────────────────────────────────────────

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    event_id = Column(String(36), primary_key=True, default=_uuid)
    aircraft_id = Column(String(16), ForeignKey("aircraft.aircraft_id"), nullable=False, index=True)
    component_id = Column(String(32), ForeignKey("components.component_id"), nullable=True)
    fault_code = Column(String(16), nullable=True)
    event_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    action = Column(String(64), nullable=True)
    technician_notes_encrypted = Column(Text, nullable=True)  # AES-256-GCM
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class InspectionFinding(Base):
    __tablename__ = "inspection_findings"

    finding_id = Column(String(36), primary_key=True, default=_uuid)
    component_id = Column(String(32), ForeignKey("components.component_id"), nullable=False, index=True)
    finding_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    observation_encrypted = Column(Text, nullable=True)  # AES-256-GCM
    date = Column(DateTime(timezone=True), nullable=False)
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Spares and Facilities ───────────────────────────────────────────

class SparePart(Base):
    __tablename__ = "spare_parts"

    part_no = Column(String(16), primary_key=True)
    description = Column(String(128), nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, nullable=False, default=1)
    lead_time_days = Column(Integer, nullable=False, default=7)
    criticality = Column(String(16), nullable=False, default="MEDIUM")
    facility_id = Column(String(16), ForeignKey("facilities.facility_id"), nullable=True)
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


class Facility(Base):
    __tablename__ = "facilities"

    facility_id = Column(String(16), primary_key=True)
    name = Column(String(64), nullable=False)
    capability = Column(String(64), nullable=False)
    slots_available = Column(Integer, nullable=False, default=1)
    avg_turnaround_days = Column(Float, nullable=False, default=5.0)
    data_source = Column(String(32), nullable=False, default="SYNTHETIC_NON_OPERATIONAL")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


# ── Ingestion ────────────────────────────────────────────────────────

class IngestBatch(Base):
    __tablename__ = "ingest_batches"

    id = Column(String(36), primary_key=True, default=_uuid)
    dataset = Column(String(32), nullable=False)
    filename = Column(String(128), nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    row_count_total = Column(Integer, nullable=False, default=0)
    row_count_accepted = Column(Integer, nullable=False, default=0)
    row_count_quarantined = Column(Integer, nullable=False, default=0)
    status = Column(
        Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="batch_status"),
        nullable=False,
        default="PENDING",
    )
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


class QuarantinedRow(Base):
    __tablename__ = "quarantined_rows"

    id = Column(String(36), primary_key=True, default=_uuid)
    batch_id = Column(String(36), ForeignKey("ingest_batches.id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    row_data = Column(JSON, nullable=False)
    reason = Column(String(256), nullable=False)
    severity = Column(String(16), nullable=False, default="ERROR")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    component_id = Column(String(32), ForeignKey("components.component_id"), nullable=True)
    window_start_cycle = Column(Integer, nullable=True)
    window_end_cycle = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=False)  # 0-1
    flags = Column(JSON, nullable=True)  # List of quality flag strings
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── ML Models and Predictions ───────────────────────────────────────

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_name = Column(String(64), nullable=False)
    model_type = Column(String(32), nullable=False)  # risk, rul, anomaly
    version = Column(String(16), nullable=False)
    component_type = Column(String(32), nullable=False)
    file_path = Column(String(256), nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    file_hmac = Column(String(64), nullable=False)
    training_dataset_hash = Column(String(64), nullable=False)
    feature_schema_hash = Column(String(64), nullable=False)
    metrics = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    trained_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=_uuid)
    component_id = Column(String(32), ForeignKey("components.component_id"), nullable=False, index=True)
    aircraft_id = Column(String(16), ForeignKey("aircraft.aircraft_id"), nullable=False, index=True)
    model_id = Column(String(36), ForeignKey("model_registry.id"), nullable=False)
    prediction_type = Column(String(16), nullable=False)  # risk, rul, anomaly
    risk_score = Column(Float, nullable=True)
    rul_q10 = Column(Float, nullable=True)
    rul_q50 = Column(Float, nullable=True)
    rul_q90 = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    suspected_failure_mode = Column(String(32), nullable=True)
    confidence_interval_width = Column(Float, nullable=True)
    shap_values = Column(JSON, nullable=True)  # top-k features
    data_quality_score = Column(Float, nullable=True)
    data_quality_flags = Column(JSON, nullable=True)
    trust_score = Column(Float, nullable=True)
    trust_gate = Column(String(32), nullable=True)
    input_window_start = Column(Integer, nullable=True)
    input_window_end = Column(Integer, nullable=True)
    input_rows_hash = Column(String(64), nullable=True)
    is_superseded = Column(Boolean, default=False, nullable=False)
    superseded_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_predictions_created", "created_at"),
    )


# ── Recommendations and Decisions ────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=_uuid)
    version = Column(Integer, nullable=False, default=1)
    component_id = Column(String(32), ForeignKey("components.component_id"), nullable=False, index=True)
    aircraft_id = Column(String(16), ForeignKey("aircraft.aircraft_id"), nullable=False, index=True)
    prediction_id = Column(String(36), ForeignKey("predictions.id"), nullable=False)
    priority_score = Column(Float, nullable=False)
    priority_tier = Column(
        Enum("CRITICAL", "HIGH", "MEDIUM", "LOW", name="priority_tier"),
        nullable=False,
    )
    reason_codes = Column(JSON, nullable=False)  # List of reason code strings
    recommended_action = Column(String(32), nullable=False)
    part_no = Column(String(16), nullable=True)
    part_status = Column(String(32), nullable=True)
    facility_id = Column(String(16), nullable=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    config_version = Column(String(36), nullable=True)
    is_superseded = Column(Boolean, default=False, nullable=False)
    supersedes_id = Column(String(36), nullable=True)
    status = Column(String(32), nullable=False, default="OPEN")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_recommendations_status", "status"),
    )


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=_uuid)
    recommendation_id = Column(String(36), ForeignKey("recommendations.id"), nullable=False, index=True)
    recommendation_version = Column(Integer, nullable=False)
    action = Column(
        Enum("ACCEPT", "DEFER", "REJECT", "OVERRIDE", name="decision_action"),
        nullable=False,
    )
    reason = Column(Text, nullable=False)  # min 15 chars, enforced in API
    model_version = Column(String(16), nullable=True)
    decided_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    decided_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class PendingOverride(Base):
    __tablename__ = "pending_overrides"

    id = Column(String(36), primary_key=True, default=_uuid)
    decision_id = Column(String(36), ForeignKey("decisions.id"), nullable=False, index=True)
    recommendation_id = Column(String(36), ForeignKey("recommendations.id"), nullable=False)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(
        Enum("PENDING", "APPROVED", "REJECTED", name="override_status"),
        nullable=False,
        default="PENDING",
    )
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


# ── Evidence Passports ───────────────────────────────────────────────

class EvidencePassport(Base):
    __tablename__ = "evidence_passports"

    id = Column(String(36), primary_key=True, default=_uuid)
    recommendation_id = Column(String(36), ForeignKey("recommendations.id"), nullable=False, index=True)
    passport_data = Column(JSON, nullable=False)
    passport_hash = Column(String(64), nullable=False)
    signature = Column(Text, nullable=False)
    model_checksum = Column(String(64), nullable=False)
    input_rows_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Forecast ─────────────────────────────────────────────────────────

class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    config_hash = Column(String(64), nullable=False, index=True)
    seed = Column(Integer, nullable=False)
    model_versions = Column(JSON, nullable=False)
    inputs_hash = Column(String(64), nullable=False)
    horizon_days = Column(Integer, nullable=False, default=90)
    num_simulations = Column(Integer, nullable=False, default=2000)
    results = Column(JSON, nullable=False)
    run_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    runtime_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Scenarios ────────────────────────────────────────────────────────

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(32), nullable=False)
    parameters = Column(JSON, nullable=False)
    results = Column(JSON, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_simulation = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Alerts ───────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    alert_type = Column(String(32), nullable=False)
    tier = Column(String(16), nullable=False)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    entity_type = Column(String(32), nullable=True)
    entity_id = Column(String(36), nullable=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_alerts_created", "created_at"),
    )


# ── Configuration ────────────────────────────────────────────────────

class ConfigParam(Base):
    __tablename__ = "config_params"

    id = Column(String(36), primary_key=True, default=_uuid)
    key = Column(String(64), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("key", "version", name="uq_config_key_version"),
    )


# ── Security Events ─────────────────────────────────────────────────

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    event_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False)
    description = Column(Text, nullable=False)
    actor_id = Column(String(36), nullable=True)
    ip_address = Column(String(45), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Audit Log (append-only, hash-chained) ────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=_uuid)
    ts = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
    actor_id = Column(String(36), nullable=True)
    actor_role = Column(String(32), nullable=True)
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(32), nullable=True)
    entity_id = Column(String(36), nullable=True)
    model_version = Column(String(16), nullable=True)
    payload_json = Column(JSON, nullable=True)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False, unique=True)

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )
