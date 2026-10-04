"""AERIS Backend — ML Scoring Service.

Scores all supported components: loads verified models, computes features,
generates predictions with SHAP explanations.

Run as: python -m app.services.scoring --run
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import read_secret
from app.core.crypto import sha256_hash
from app.core.logging import get_logger
from app.db.models import Component, HealthObservation, ModelRegistry, Prediction
from app.services.features import (
    COMPONENT_SENSOR_MAP,
    compute_feature_schema_hash,
    engineer_features_for_window,
)

logger = get_logger("scoring")

MODEL_DIR = Path("/app/ml_artifacts")
SUPPORTED_TYPES = {"ENGINE", "HYDRAULIC_PUMP"}


def _verify_model_file(filepath: str, expected_sha256: str, expected_hmac: str) -> bool:
    """Verify model file integrity before loading."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()

        actual_sha256 = hashlib.sha256(data).hexdigest()
        if actual_sha256 != expected_sha256:
            logger.error(f"Model SHA-256 mismatch: {filepath}")
            return False

        key = read_secret("model_hmac_key").encode()
        if key:
            actual_hmac = hmac.new(key, data, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(actual_hmac, expected_hmac):
                logger.error(f"Model HMAC mismatch: {filepath}")
                return False

        return True
    except Exception as e:
        logger.error(f"Model verification failed: {e}")
        return False


def _load_verified_model(filepath: str, sha256: str, hmac_val: str) -> Any:
    """Load a model only after verifying integrity."""
    if not _verify_model_file(filepath, sha256, hmac_val):
        raise ValueError(f"Model integrity check failed: {filepath}")
    return joblib.load(filepath)


def score_component(
    db: Session,
    component_id: str,
    component_type: str,
    aircraft_id: str,
) -> dict[str, Any] | None:
    """Score a single component: anomaly, risk, RUL with explanations."""
    if component_type not in SUPPORTED_TYPES:
        return None

    # Get health observations
    observations = (
        db.query(HealthObservation)
        .filter(HealthObservation.component_id == component_id)
        .order_by(HealthObservation.cycle.asc())
        .all()
    )

    if not observations:
        return None

    # Build DataFrame
    records = [
        {
            "cycle": obs.cycle,
            "sensor": obs.sensor,
            "value": obs.value,
        }
        for obs in observations
    ]
    df = pd.DataFrame(records)

    # Compute features
    features = engineer_features_for_window(df, component_type)
    if not features:
        return None

    # Load models from filesystem (simplified — in production, use model_registry DB)
    result: dict[str, Any] = {
        "component_id": component_id,
        "aircraft_id": aircraft_id,
        "component_type": component_type,
    }

    # Get feature vector
    feature_cols = list(features.keys())
    feature_values = np.array([features[c] for c in feature_cols]).reshape(1, -1)

    # Get active models from registry
    def _get_active_model(m_type: str) -> ModelRegistry | None:
        from sqlalchemy import desc
        return db.query(ModelRegistry).filter_by(
            model_type=m_type,
            component_type=component_type,
            is_active=True
        ).order_by(desc(ModelRegistry.version)).first()

    # Risk prediction
    risk_reg = _get_active_model("risk")
    if risk_reg and Path(risk_reg.file_path).exists():
        try:
            risk_model = _load_verified_model(risk_reg.file_path, risk_reg.file_sha256, risk_reg.file_hmac)
            risk_proba = risk_model.predict_proba(
                pd.DataFrame([features])[[c for c in features if c in (
                    risk_model.feature_names_in_ if hasattr(risk_model, 'feature_names_in_') else features.keys()
                )]]
            )[:, 1]
            result["risk_score"] = float(risk_proba[0])

            # SHAP explanation
            try:
                import shap
                # Get the base estimator for SHAP
                base_model = risk_model
                if hasattr(risk_model, 'estimators_'):
                    base_model = risk_model.estimators_[0]
                if hasattr(base_model, 'estimators_'):
                    base_model = base_model.estimators_[0]

                explainer = shap.TreeExplainer(base_model)
                feature_df = pd.DataFrame([features])
                shap_values = explainer.shap_values(feature_df)

                if isinstance(shap_values, list):
                    shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
                else:
                    shap_vals = shap_values

                # Top-5 features by absolute SHAP value
                shap_flat = shap_vals.flatten()
                top_indices = np.argsort(np.abs(shap_flat))[-5:][::-1]
                top_features = []
                for idx in top_indices:
                    if idx < len(feature_df.columns):
                        col = feature_df.columns[idx]
                        top_features.append({
                            "feature": col,
                            "shap_value": float(shap_flat[idx]),
                            "feature_value": float(features.get(col, 0)),
                        })
                result["shap_top_features"] = top_features
            except Exception as e:
                logger.warning(f"SHAP computation failed for {component_id}: {e}")
                result["shap_top_features"] = []
        except Exception as e:
            logger.warning(f"Risk scoring failed for {component_id}: {e}")

    # RUL prediction
    rul_reg = _get_active_model("rul")
    if rul_reg and Path(rul_reg.file_path).exists():
        try:
            rul_data = _load_verified_model(rul_reg.file_path, rul_reg.file_sha256, rul_reg.file_hmac)
            rul_model = rul_data["model"] if isinstance(rul_data, dict) else rul_data
            feature_df = pd.DataFrame([features])
            matching_cols = [c for c in feature_df.columns if c in (
                rul_model.feature_names_in_ if hasattr(rul_model, 'feature_names_in_') else feature_df.columns
            )]
            rul_pred = rul_model.predict(feature_df[matching_cols])
            q50 = float(max(0, rul_pred[0]))

            # Conformal intervals
            conformal_q10 = rul_data.get("conformal_q10", q50 * 0.3) if isinstance(rul_data, dict) else q50 * 0.3
            conformal_q90 = rul_data.get("conformal_q90", q50 * 0.5) if isinstance(rul_data, dict) else q50 * 0.5

            result["rul_q10"] = float(max(0, q50 - conformal_q90))
            result["rul_q50"] = q50
            result["rul_q90"] = float(q50 + conformal_q90)
            result["confidence_interval_width"] = float(conformal_q90 * 2)
        except Exception as e:
            logger.warning(f"RUL scoring failed for {component_id}: {e}")

    # Anomaly detection
    anomaly_reg = _get_active_model("anomaly")
    if anomaly_reg and Path(anomaly_reg.file_path).exists():
        try:
            anomaly_model = _load_verified_model(anomaly_reg.file_path, anomaly_reg.file_sha256, anomaly_reg.file_hmac)
            feature_df = pd.DataFrame([features])
            matching_cols = [c for c in feature_df.columns if c in (
                anomaly_model.feature_names_in_ if hasattr(anomaly_model, 'feature_names_in_') else feature_df.columns
            )]
            anomaly_score = float(anomaly_model.decision_function(feature_df[matching_cols])[0])
            result["anomaly_score"] = anomaly_score
        except Exception as e:
            logger.warning(f"Anomaly scoring failed for {component_id}: {e}")

    # Suspected failure mode (heuristic from dominant degraded channel)
    if result.get("risk_score", 0) > 0.5 and result.get("shap_top_features"):
        top_feature = result["shap_top_features"][0]["feature"]
        if "vibration" in top_feature and "oil_temp" in str([f["feature"] for f in result["shap_top_features"]]):
            result["suspected_failure_mode"] = "BEARING_WEAR"
        elif "egt" in top_feature or "fuel_flow" in top_feature:
            result["suspected_failure_mode"] = "HPT_EROSION"
        elif "pressure" in top_feature or "flow" in top_feature:
            result["suspected_failure_mode"] = "SEAL_LEAK"
        else:
            result["suspected_failure_mode"] = "UNKNOWN"

    # Data quality from observations
    max_cycle = max(obs.cycle for obs in observations)
    min_cycle = min(obs.cycle for obs in observations)
    result["input_window_start"] = min_cycle
    result["input_window_end"] = max_cycle

    # Compute input rows hash
    row_data = json.dumps([
        {"cycle": obs.cycle, "sensor": obs.sensor, "value": obs.value}
        for obs in observations
    ], sort_keys=True)
    result["input_rows_hash"] = hashlib.sha256(row_data.encode()).hexdigest()

    return result


def score_all_components(db: Session) -> list[dict[str, Any]]:
    """Score all supported components and save predictions."""
    components = (
        db.query(Component)
        .filter(Component.component_type.in_(SUPPORTED_TYPES))
        .all()
    )

    results = []
    for comp in components:
        result = score_component(
            db, comp.component_id, comp.component_type, comp.aircraft_id
        )
        if result:
            # Save prediction to DB
            active_risk = db.query(ModelRegistry).filter_by(model_type="risk", component_type=comp.component_type, is_active=True).first()
            prediction = Prediction(
                id=str(uuid.uuid4()),
                component_id=comp.component_id,
                aircraft_id=comp.aircraft_id,
                model_id=active_risk.id if active_risk else str(uuid.uuid4()),
                prediction_type="combined",
                risk_score=result.get("risk_score"),
                rul_q10=result.get("rul_q10"),
                rul_q50=result.get("rul_q50"),
                rul_q90=result.get("rul_q90"),
                anomaly_score=result.get("anomaly_score"),
                suspected_failure_mode=result.get("suspected_failure_mode"),
                confidence_interval_width=result.get("confidence_interval_width"),
                shap_values=result.get("shap_top_features"),
                input_window_start=result.get("input_window_start"),
                input_window_end=result.get("input_window_end"),
                input_rows_hash=result.get("input_rows_hash"),
                created_at=datetime.now(timezone.utc),
            )
            db.add(prediction)
            results.append(result)

    db.commit()
    logger.info(f"Scored {len(results)} components")
    return results


def main() -> None:
    """Run scoring on all components."""
    import argparse
    from app.core.logging import setup_logging
    from app.db.session import get_session_factory

    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if not args.run:
        print("Use --run to execute scoring")
        return

    setup_logging("INFO")
    factory = get_session_factory()
    session = factory()

    try:
        results = score_all_components(session)
        logger.info(f"Scoring complete: {len(results)} predictions generated")
    finally:
        session.close()


if __name__ == "__main__":
    main()
