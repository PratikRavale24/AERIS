"""AERIS Backend — Planning Engine Tests."""
from __future__ import annotations

import pytest
from app.services.planner import compute_priority


def test_compute_priority_pure_function() -> None:
    """Test priority score computation logic."""
    # High risk, low RUL, part shortage -> Critical priority
    res1 = compute_priority(
        risk_score=0.85,
        rul_q10=15.0,
        severity=0.85,
        criticality=1,
        aircraft_cycles_per_day=1.5,
        part_stock=0,
        part_min_stock=1,
        part_lead_time_days=20,
        earliest_facility_start_days=5.0,
    )

    # Low risk, high RUL, plenty of stock -> Low priority
    res2 = compute_priority(
        risk_score=0.10,
        rul_q10=180.0,
        severity=0.10,
        criticality=3,
        aircraft_cycles_per_day=1.2,
        part_stock=5,
        part_min_stock=1,
        part_lead_time_days=7,
        earliest_facility_start_days=0.0,
    )

    assert res1["priority_score"] > res2["priority_score"]
    assert res1["priority_tier"] in ("CRITICAL", "HIGH")
    assert res2["priority_tier"] in ("LOW", "MEDIUM")
