"""Initial schema - all AERIS tables

Revision ID: 001_initial
Revises: None
Create Date: 2024-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- User role enum
    user_role = sa.Enum(
        "FLEET_SUPERVISOR", "MAINT_PLANNER", "MAINT_ENGINEER",
        "SPARES_PLANNER", "SYS_ADMIN",
        name="user_role",
    )

    # -- Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("email_encrypted", sa.Text, nullable=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_count", sa.Integer, default=0, nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True),
        sa.Column("totp_secret_encrypted", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])

    # -- Refresh tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), unique=True, nullable=False),
        sa.Column("family_id", sa.String(36), nullable=False),
        sa.Column("is_revoked", sa.Boolean, default=False, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])

    # -- Login attempts
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_login_attempts_username", "login_attempts", ["username"])
    op.create_index("ix_login_attempts_ip", "login_attempts", ["ip_address"])
    op.create_index("ix_login_attempts_ts", "login_attempts", ["timestamp"])

    # -- Step-up tokens
    op.create_table(
        "stepup_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # -- Aircraft
    aircraft_status = sa.Enum(
        "AVAILABLE", "AVAILABLE_MONITOR", "SCHEDULED_MAINTENANCE",
        "AOG_AWAITING_PARTS", "UNSERVICEABLE",
        name="aircraft_status",
    )
    op.create_table(
        "aircraft",
        sa.Column("aircraft_id", sa.String(16), primary_key=True),
        sa.Column("platform_type", sa.String(32), nullable=False),
        sa.Column("status", aircraft_status, nullable=False, server_default="AVAILABLE"),
        sa.Column("age_years", sa.Float, nullable=False),
        sa.Column("total_cycles", sa.Integer, nullable=False),
        sa.Column("criticality", sa.Integer, nullable=False),
        sa.Column("cycles_per_day", sa.Float, nullable=False, server_default="1.2"),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aircraft_status", "aircraft", ["status"])

    # -- Components
    component_type = sa.Enum("ENGINE", "HYDRAULIC_PUMP", "GEARBOX", name="component_type")
    op.create_table(
        "components",
        sa.Column("component_id", sa.String(32), primary_key=True),
        sa.Column("aircraft_id", sa.String(16), sa.ForeignKey("aircraft.aircraft_id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_type", component_type, nullable=False),
        sa.Column("subsystem", sa.String(32), nullable=False),
        sa.Column("part_no", sa.String(16), nullable=False),
        sa.Column("install_cycle", sa.Integer, nullable=False, server_default="0"),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_components_aircraft_id", "components", ["aircraft_id"])
    op.create_index("ix_components_part_no", "components", ["part_no"])

    # -- Facilities (before spares, for FK)
    op.create_table(
        "facilities",
        sa.Column("facility_id", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("capability", sa.String(64), nullable=False),
        sa.Column("slots_available", sa.Integer, nullable=False, server_default="1"),
        sa.Column("avg_turnaround_days", sa.Float, nullable=False, server_default="5.0"),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # -- Ingest batches (before health_observations, for FK)
    batch_status = sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="batch_status")
    op.create_table(
        "ingest_batches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset", sa.String(32), nullable=False),
        sa.Column("filename", sa.String(128), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("row_count_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("row_count_accepted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("row_count_quarantined", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", batch_status, nullable=False, server_default="PENDING"),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # -- Health observations
    op.create_table(
        "health_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aircraft_id", sa.String(16), sa.ForeignKey("aircraft.aircraft_id"), nullable=False),
        sa.Column("component_id", sa.String(32), sa.ForeignKey("components.component_id"), nullable=False),
        sa.Column("sensor", sa.String(32), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("cycle", sa.Integer, nullable=False),
        sa.Column("operating_context", JSON, nullable=True),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("ingest_batches.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_health_component_cycle", "health_observations", ["component_id", "cycle"])
    op.create_index("ix_health_aircraft", "health_observations", ["aircraft_id"])
    op.create_index("ix_health_created", "health_observations", ["created_at"])

    # -- Maintenance events
    op.create_table(
        "maintenance_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("aircraft_id", sa.String(16), sa.ForeignKey("aircraft.aircraft_id"), nullable=False),
        sa.Column("component_id", sa.String(32), sa.ForeignKey("components.component_id"), nullable=True),
        sa.Column("fault_code", sa.String(16), nullable=True),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=True),
        sa.Column("technician_notes_encrypted", sa.Text, nullable=True),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_maint_aircraft", "maintenance_events", ["aircraft_id"])

    # -- Inspection findings
    op.create_table(
        "inspection_findings",
        sa.Column("finding_id", sa.String(36), primary_key=True),
        sa.Column("component_id", sa.String(32), sa.ForeignKey("components.component_id"), nullable=False),
        sa.Column("finding_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("observation_encrypted", sa.Text, nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_findings_component", "inspection_findings", ["component_id"])

    # -- Spare parts
    op.create_table(
        "spare_parts",
        sa.Column("part_no", sa.String(16), primary_key=True),
        sa.Column("description", sa.String(128), nullable=True),
        sa.Column("stock", sa.Integer, nullable=False, server_default="0"),
        sa.Column("min_stock", sa.Integer, nullable=False, server_default="1"),
        sa.Column("lead_time_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("criticality", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("facility_id", sa.String(16), sa.ForeignKey("facilities.facility_id"), nullable=True),
        sa.Column("data_source", sa.String(32), nullable=False, server_default="SYNTHETIC_NON_OPERATIONAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # -- Quarantined rows
    op.create_table(
        "quarantined_rows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("ingest_batches.id"), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("row_data", JSON, nullable=False),
        sa.Column("reason", sa.String(256), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="ERROR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quarantined_batch", "quarantined_rows", ["batch_id"])

    # -- Data quality reports
    op.create_table(
        "data_quality_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("component_id", sa.String(32), sa.ForeignKey("components.component_id"), nullable=True),
        sa.Column("window_start_cycle", sa.Integer, nullable=True),
        sa.Column("window_end_cycle", sa.Integer, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=False),
        sa.Column("flags", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # -- Model registry
    op.create_table(
        "model_registry",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("component_type", sa.String(32), nullable=False),
        sa.Column("file_path", sa.String(256), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("file_hmac", sa.String(64), nullable=False),
        sa.Column("training_dataset_hash", sa.String(64), nullable=False),
        sa.Column("feature_schema_hash", sa.String(64), nullable=False),
        sa.Column("metrics", JSON, nullable=True),
        sa.Column("hyperparameters", JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_model_version", "model_registry", ["model_name", "version"])

    # -- Predictions
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("component_id", sa.String(32), sa.ForeignKey("components.component_id"), nullable=False),
        sa.Column("aircraft_id", sa.String(16), sa.ForeignKey("aircraft.aircraft_id"), nullable=False),
        sa.Column("model_id", sa.String(36), sa.ForeignKey("model_registry.id"), nullable=False),
        sa.Column("prediction_type", sa.String(16), nullable=False),
        sa.Column("risk_score", sa.Float, nullable=True),
        sa.Column("rul_q10", sa.Float, nullable=True),
        sa.Column("rul_q50", sa.Float, nullable=True),
        sa.Column("rul_q90", sa.Float, nullable=True),
        sa.Column("anomaly_score", sa.Float, nullable=True),
        sa.Column("suspected_failure_mode", sa.String(32), nullable=True),
        sa.Column("confidence_interval_width", sa.Float, nullable=True),
        sa.Column("shap_values", JSON, nullable=True),
        sa.Column("data_quality_score", sa.Float, nullable=True),
        sa.Column("data_quality_flags", JSON, nullable=True),
        sa.Column("trust_score", sa.Float, nullable=True),
        sa.Column("trust_gate", sa.String(32), nullable=True),
        sa.Column("input_window_start", sa.Integer, nullable=True),
        sa.Column("input_window_end", sa.Integer, nullable=True),
        sa.Column("input_rows_hash", sa.String(64), nullable=True),
        sa.Column("is_superseded", sa.Boolean, default=False, nullable=False),
        sa.Column("superseded_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_predictions_component", "predictions", ["component_id"])
    op.create_index("ix_predictions_aircraft", "predictions", ["aircraft_id"])
    op.create_index("ix_predictions_created", "predictions", ["created_at"])

    # -- Recommendations
    priority_tier = sa.Enum("CRITICAL", "HIGH", "MEDIUM", "LOW", name="priority_tier")
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("component_id", sa.String(32), sa.ForeignKey("components.component_id"), nullable=False),
        sa.Column("aircraft_id", sa.String(16), sa.ForeignKey("aircraft.aircraft_id"), nullable=False),
        sa.Column("prediction_id", sa.String(36), sa.ForeignKey("predictions.id"), nullable=False),
        sa.Column("priority_score", sa.Float, nullable=False),
        sa.Column("priority_tier", priority_tier, nullable=False),
        sa.Column("reason_codes", JSON, nullable=False),
        sa.Column("recommended_action", sa.String(32), nullable=False),
        sa.Column("part_no", sa.String(16), nullable=True),
        sa.Column("part_status", sa.String(32), nullable=True),
        sa.Column("facility_id", sa.String(16), nullable=True),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_completion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_version", sa.String(36), nullable=True),
        sa.Column("is_superseded", sa.Boolean, default=False, nullable=False),
        sa.Column("supersedes_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendations_component", "recommendations", ["component_id"])
    op.create_index("ix_recommendations_aircraft", "recommendations", ["aircraft_id"])
    op.create_index("ix_recommendations_status", "recommendations", ["status"])

    # -- Decisions (immutable - no DELETE allowed)
    decision_action = sa.Enum("ACCEPT", "DEFER", "REJECT", "OVERRIDE", name="decision_action")
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("recommendation_version", sa.Integer, nullable=False),
        sa.Column("action", decision_action, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("model_version", sa.String(16), nullable=True),
        sa.Column("decided_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_decisions_recommendation", "decisions", ["recommendation_id"])

    # -- Pending overrides
    override_status = sa.Enum("PENDING", "APPROVED", "REJECTED", name="override_status")
    op.create_table(
        "pending_overrides",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("decision_id", sa.String(36), sa.ForeignKey("decisions.id"), nullable=False),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("requested_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", override_status, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_overrides_decision", "pending_overrides", ["decision_id"])

    # -- Evidence passports (fully immutable)
    op.create_table(
        "evidence_passports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("passport_data", JSON, nullable=False),
        sa.Column("passport_hash", sa.String(64), nullable=False),
        sa.Column("signature", sa.Text, nullable=False),
        sa.Column("model_checksum", sa.String(64), nullable=False),
        sa.Column("input_rows_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_passports_recommendation", "evidence_passports", ["recommendation_id"])

    # -- Forecast runs
    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("seed", sa.Integer, nullable=False),
        sa.Column("model_versions", JSON, nullable=False),
        sa.Column("inputs_hash", sa.String(64), nullable=False),
        sa.Column("horizon_days", sa.Integer, nullable=False, server_default="90"),
        sa.Column("num_simulations", sa.Integer, nullable=False, server_default="2000"),
        sa.Column("results", JSON, nullable=False),
        sa.Column("run_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("runtime_seconds", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forecast_config_hash", "forecast_runs", ["config_hash"])

    # -- Scenarios
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("scenario_type", sa.String(32), nullable=False),
        sa.Column("parameters", JSON, nullable=False),
        sa.Column("results", JSON, nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_simulation", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # -- Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("tier", sa.String(16), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean, default=False, nullable=False),
        sa.Column("acknowledged_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_created", "alerts", ["created_at"])

    # -- Config params
    op.create_table(
        "config_params",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", JSON, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("changed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_config_key", "config_params", ["key"])
    op.create_unique_constraint("uq_config_key_version", "config_params", ["key", "version"])

    # -- Security events
    op.create_table(
        "security_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_security_events_type", "security_events", ["event_type"])

    # -- Audit log (append-only, hash-chained)
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("actor_role", sa.String(32), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("model_version", sa.String(16), nullable=True),
        sa.Column("payload_json", JSON, nullable=True),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("entry_hash", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("ix_audit_ts", "audit_log", ["ts"])
    op.create_index("ix_audit_action", "audit_log", ["action"])
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id"])


def downgrade() -> None:
    # Drop in reverse order
    tables = [
        "audit_log", "security_events", "config_params", "alerts",
        "scenarios", "forecast_runs", "evidence_passports",
        "pending_overrides", "decisions", "recommendations",
        "predictions", "model_registry", "data_quality_reports",
        "quarantined_rows", "inspection_findings", "maintenance_events",
        "health_observations", "ingest_batches", "spare_parts",
        "facilities", "components", "aircraft",
        "stepup_tokens", "login_attempts", "refresh_tokens", "users",
    ]
    for table in tables:
        op.drop_table(table)

    # Drop enums
    for enum_name in [
        "override_status", "decision_action", "priority_tier",
        "batch_status", "component_type", "aircraft_status", "user_role",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
