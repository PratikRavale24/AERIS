"""AERIS Backend — ML Pipeline Tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.features import (
    compute_feature_schema_hash,
    engineer_features_for_window,
    engineer_features_batch,
)


def test_feature_engineering_window() -> None:
    """Test feature engineering over synthetic sensor window data."""
    cycles = list(range(1, 35))
    df = pd.DataFrame({
        "cycle": cycles,
        "sensor": ["egt_c"] * 34,
        "value": 650.0 + np.random.randn(34) * 5.0,
    })

    feats = engineer_features_for_window(df, "ENGINE")
    assert isinstance(feats, dict)
    assert len(feats) > 0
    assert "mean_egt_c_w10" in feats


def test_feature_schema_hash() -> None:
    """Test deterministic feature schema hash computation per component type."""
    hash_eng1 = compute_feature_schema_hash("ENGINE")
    hash_eng2 = compute_feature_schema_hash("ENGINE")
    hash_hyd = compute_feature_schema_hash("HYDRAULIC_PUMP")

    assert hash_eng1 == hash_eng2
    assert hash_eng1 != hash_hyd
    assert len(hash_eng1) == 64
