"""AERIS Backend — Feature Engineering.

Rolling statistics, trend detection, EWMA, context-normalized residuals.
Configurable windows (10/30 cycles). Produces a feature schema hash.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd

from app.core.logging import get_logger

logger = get_logger("features")

# Feature windows
WINDOWS = [10, 30]

# Sensors by component type
ENGINE_SENSORS = ["egt_c", "n1_rpm", "n2_rpm", "vibration_mm_s", "oil_pressure_kpa", "oil_temp_c", "fuel_flow_kg_h"]
HYDRAULIC_SENSORS = ["outlet_pressure_kpa", "flow_l_min", "case_temp_c", "vibration_mm_s"]

COMPONENT_SENSOR_MAP = {
    "ENGINE": ENGINE_SENSORS,
    "HYDRAULIC_PUMP": HYDRAULIC_SENSORS,
}


def compute_feature_schema_hash(component_type: str) -> str:
    """Compute a hash of the feature schema for versioning."""
    sensors = COMPONENT_SENSOR_MAP.get(component_type, [])
    schema = {
        "component_type": component_type,
        "sensors": sensors,
        "windows": WINDOWS,
        "features": ["mean", "std", "min", "max", "slope", "roc", "ewma"],
    }
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()


def _compute_slope(values: np.ndarray) -> float:
    """Linear regression slope via least squares."""
    n = len(values)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=np.float64)
    x_mean = x.mean()
    y_mean = values.mean()
    denom = np.sum((x - x_mean) ** 2)
    if denom == 0:
        return 0.0
    return float(np.sum((x - x_mean) * (values - y_mean)) / denom)


def engineer_features_for_window(
    df: pd.DataFrame,
    component_type: str,
    window_end: int | None = None,
) -> dict[str, float]:
    """Compute features for a single component at a point in time.
    
    Args:
        df: DataFrame with columns: cycle, sensor, value (pivoted or long format)
        component_type: ENGINE or HYDRAULIC_PUMP
        window_end: The cycle number to compute features up to (default: latest)
    
    Returns:
        Dict of feature_name -> value
    """
    sensors = COMPONENT_SENSOR_MAP.get(component_type, [])
    if not sensors:
        return {}

    features: dict[str, float] = {}

    # Pivot to wide format if in long format
    if "sensor" in df.columns:
        pivoted = df.pivot_table(index="cycle", columns="sensor", values="value", aggfunc="mean")
        pivoted = pivoted.sort_index()
    else:
        pivoted = df.sort_values("cycle").set_index("cycle") if "cycle" in df.columns else df

    if window_end is not None:
        pivoted = pivoted[pivoted.index <= window_end]

    if pivoted.empty:
        return {}

    for sensor in sensors:
        if sensor not in pivoted.columns:
            continue

        values = pivoted[sensor].dropna().values

        if len(values) == 0:
            continue

        for window in WINDOWS:
            suffix = f"_{sensor}_w{window}"
            window_vals = values[-window:] if len(values) >= window else values

            features[f"mean{suffix}"] = float(np.mean(window_vals))
            features[f"std{suffix}"] = float(np.std(window_vals)) if len(window_vals) > 1 else 0.0
            features[f"min{suffix}"] = float(np.min(window_vals))
            features[f"max{suffix}"] = float(np.max(window_vals))
            features[f"slope{suffix}"] = _compute_slope(window_vals)
            
            # Rate of change (last value - first value in window)
            if len(window_vals) > 1:
                features[f"roc{suffix}"] = float(window_vals[-1] - window_vals[0])
            else:
                features[f"roc{suffix}"] = 0.0

            # EWMA
            alpha = 2.0 / (min(window, len(window_vals)) + 1)
            ewma = window_vals[0]
            for v in window_vals[1:]:
                ewma = alpha * v + (1 - alpha) * ewma
            features[f"ewma{suffix}"] = float(ewma)

    # Global features
    features["total_cycles_observed"] = float(len(pivoted))
    features["latest_cycle"] = float(pivoted.index.max()) if len(pivoted) > 0 else 0.0

    return features


def engineer_features_batch(
    health_df: pd.DataFrame,
    component_type: str,
) -> pd.DataFrame:
    """Compute features for training data (all cycles for each run).
    
    Args:
        health_df: DataFrame with columns including cycle and sensor value columns.
        component_type: ENGINE or HYDRAULIC_PUMP
    
    Returns:
        DataFrame with one row per (run_id, cycle) with computed features.
    """
    sensors = COMPONENT_SENSOR_MAP.get(component_type, [])
    if not sensors:
        return pd.DataFrame()

    # For training data, we have all sensor columns directly
    has_run_id = "run_id" in health_df.columns

    if not has_run_id:
        # Single component: compute features at each cycle
        return _compute_rolling_features(health_df, sensors, group_col=None)
    else:
        # Training corpus: group by run_id
        return _compute_rolling_features(health_df, sensors, group_col="run_id")


def _compute_rolling_features(
    df: pd.DataFrame,
    sensors: list[str],
    group_col: str | None,
) -> pd.DataFrame:
    """Compute rolling features across cycles."""
    all_features = []

    groups = df.groupby(group_col) if group_col else [(None, df)]

    for group_key, group_df in groups:
        group_df = group_df.sort_values("cycle")

        for _, row in group_df.iterrows():
            cycle = int(row["cycle"])
            past_data = group_df[group_df["cycle"] <= cycle]

            feat_row: dict[str, Any] = {}
            if group_col:
                feat_row[group_col] = group_key
            feat_row["cycle"] = cycle

            # Copy target columns if they exist
            for col in ["RUL_cycles_at_t", "failure_mode", "is_censored"]:
                if col in row.index:
                    feat_row[col] = row[col]

            for sensor in sensors:
                if sensor not in past_data.columns:
                    continue
                values = past_data[sensor].dropna().values

                for window in WINDOWS:
                    suffix = f"_{sensor}_w{window}"
                    w_vals = values[-window:] if len(values) >= window else values

                    if len(w_vals) == 0:
                        for prefix in ["mean", "std", "min", "max", "slope", "roc", "ewma"]:
                            feat_row[f"{prefix}{suffix}"] = 0.0
                        continue

                    feat_row[f"mean{suffix}"] = float(np.mean(w_vals))
                    feat_row[f"std{suffix}"] = float(np.std(w_vals)) if len(w_vals) > 1 else 0.0
                    feat_row[f"min{suffix}"] = float(np.min(w_vals))
                    feat_row[f"max{suffix}"] = float(np.max(w_vals))
                    feat_row[f"slope{suffix}"] = _compute_slope(w_vals)
                    feat_row[f"roc{suffix}"] = float(w_vals[-1] - w_vals[0]) if len(w_vals) > 1 else 0.0

                    alpha = 2.0 / (min(window, len(w_vals)) + 1)
                    ewma = w_vals[0]
                    for v in w_vals[1:]:
                        ewma = alpha * v + (1 - alpha) * ewma
                    feat_row[f"ewma{suffix}"] = float(ewma)

            feat_row["total_cycles_observed"] = float(len(past_data))
            all_features.append(feat_row)

    return pd.DataFrame(all_features)
