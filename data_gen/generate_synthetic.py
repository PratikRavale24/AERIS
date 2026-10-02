"""AERIS — Synthetic Data Generator.

Generates realistic, correlated, seeded, reproducible synthetic data for:
- 25 demo aircraft with 4 components each
- Training corpus (250 run-to-failure sequences per supported component type)
- Live fleet telemetry (150 cycles per component)
- Maintenance events, inspections, spares, facilities
- Injected data defects for validation testing

All data is labelled SYNTHETIC_NON_OPERATIONAL.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

# Seed for reproducibility
MASTER_SEED = 42
np.random.seed(MASTER_SEED)

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data" / "synthetic"
FLEET_DIR = DATA_DIR / "fleet"
TRAINING_DIR = DATA_DIR / "training"
SCENARIOS_FILE = SCRIPT_DIR / "scenarios.yaml"

# ── Sensor definitions ──────────────────────────────────────────────

ENGINE_SENSORS: dict[str, dict[str, Any]] = {
    "egt_c": {"unit": "celsius", "baseline": 650, "std": 8, "min": 400, "max": 1100},
    "n1_rpm": {"unit": "rpm", "baseline": 9500, "std": 50, "min": 5000, "max": 12000},
    "n2_rpm": {"unit": "rpm", "baseline": 14000, "std": 60, "min": 8000, "max": 18000},
    "vibration_mm_s": {"unit": "mm/s", "baseline": 2.5, "std": 0.3, "min": 0, "max": 25},
    "oil_pressure_kpa": {"unit": "kPa", "baseline": 350, "std": 10, "min": 100, "max": 600},
    "oil_temp_c": {"unit": "celsius", "baseline": 85, "std": 3, "min": 30, "max": 180},
    "fuel_flow_kg_h": {"unit": "kg/h", "baseline": 1200, "std": 30, "min": 500, "max": 3000},
}

HYDRAULIC_SENSORS: dict[str, dict[str, Any]] = {
    "outlet_pressure_kpa": {"unit": "kPa", "baseline": 21000, "std": 200, "min": 5000, "max": 35000},
    "flow_l_min": {"unit": "L/min", "baseline": 45, "std": 1.5, "min": 5, "max": 80},
    "case_temp_c": {"unit": "celsius", "baseline": 55, "std": 2, "min": 20, "max": 120},
    "vibration_mm_s": {"unit": "mm/s", "baseline": 1.8, "std": 0.2, "min": 0, "max": 20},
}

GEARBOX_SENSORS: dict[str, dict[str, Any]] = {
    "vibration_mm_s": {"unit": "mm/s", "baseline": 3.0, "std": 0.4, "min": 0, "max": 30},
    "oil_temp_c": {"unit": "celsius", "baseline": 75, "std": 3, "min": 30, "max": 150},
    "metal_particle_count": {"unit": "count", "baseline": 15, "std": 5, "min": 0, "max": 500},
    "torque_nm": {"unit": "Nm", "baseline": 5000, "std": 100, "min": 1000, "max": 10000},
}

COMPONENT_SENSORS = {
    "ENGINE": ENGINE_SENSORS,
    "HYDRAULIC_PUMP": HYDRAULIC_SENSORS,
    "GEARBOX": GEARBOX_SENSORS,
}

# Part number mapping
PART_NUMBERS = {
    "ENGINE": ["PN-4007", "PN-4008"],
    "HYDRAULIC_PUMP": ["PN-5012"],
    "GEARBOX": ["PN-6003"],
}

ALTITUDE_BANDS = ["LOW", "MEDIUM", "HIGH", "CRUISE"]
CONTEXT_TEMPS = [-20, -5, 15, 25, 35, 45]


def load_scenarios() -> dict[str, Any]:
    """Load scenario definitions from YAML."""
    with open(SCENARIOS_FILE) as f:
        return yaml.safe_load(f)


def generate_operating_context(rng: np.random.Generator) -> dict[str, Any]:
    """Generate random operating context for a cycle."""
    return {
        "altitude_band": rng.choice(ALTITUDE_BANDS),
        "ambient_temp_c": float(rng.choice(CONTEXT_TEMPS) + rng.normal(0, 3)),
        "load_factor": float(rng.uniform(0.6, 1.2)),
    }


def generate_sensor_value(
    sensor_name: str,
    sensor_cfg: dict[str, Any],
    cycle: int,
    onset_cycle: int | None,
    degradation: dict[str, Any] | None,
    context: dict[str, Any],
    rng: np.random.Generator,
    sensor_fault: dict[str, Any] | None = None,
) -> float:
    """Generate a sensor value with optional degradation trend."""
    base = sensor_cfg["baseline"]
    noise = rng.normal(0, sensor_cfg["std"])

    # Context effects
    if context.get("load_factor", 1.0) > 1.0:
        base *= 1 + (context["load_factor"] - 1.0) * 0.05

    # Degradation
    if onset_cycle is not None and degradation and cycle >= onset_cycle:
        cycles_since = cycle - onset_cycle
        for affected in degradation.get("affected_sensors", []):
            if affected["sensor"] == sensor_name:
                mag = affected["magnitude"]
                if affected["direction"] == "increase":
                    base += mag * cycles_since
                else:
                    base -= mag * cycles_since

    # Sensor fault (drift / flatline)
    if sensor_fault and sensor_fault.get("sensor") == sensor_name:
        if cycle >= sensor_fault.get("flatline_after", 9999):
            return float(sensor_cfg["baseline"])  # Flatline
        drift_rate = sensor_fault.get("drift_rate", 0)
        if onset_cycle and cycle >= onset_cycle:
            base += drift_rate * (cycle - onset_cycle)

    value = base + noise
    return float(np.clip(value, sensor_cfg["min"], sensor_cfg["max"]))


def generate_aircraft_fleet() -> list[dict[str, Any]]:
    """Generate 25 demo aircraft."""
    scenarios = load_scenarios()
    hero_cfg = scenarios["hero"]
    fleet_targets = scenarios["fleet_targets"]

    aircraft_list = []
    statuses = (
        ["AVAILABLE"] * 16 +
        ["AVAILABLE_MONITOR"] * 3 +
        ["SCHEDULED_MAINTENANCE"] * 4 +
        ["AOG_AWAITING_PARTS"] * 1 +
        ["UNSERVICEABLE"] * 1
    )
    np.random.shuffle(statuses)

    for i in range(1, 26):
        aid = f"A-{i:03d}"
        rng = np.random.default_rng(MASTER_SEED + i)
        platform = "DEMO-TYPE-A" if i <= 15 else "DEMO-TYPE-B"

        # Hero aircraft special handling
        if aid == hero_cfg["aircraft_id"]:
            status = "AVAILABLE_MONITOR"
        else:
            status = statuses[i - 1] if i - 1 < len(statuses) else "AVAILABLE"

        aircraft_list.append({
            "aircraft_id": aid,
            "platform_type": platform,
            "status": status,
            "age_years": round(float(rng.uniform(3, 25)), 1),
            "total_cycles": int(rng.integers(500, 8000)),
            "criticality": int(rng.choice([1, 2, 3], p=[0.2, 0.5, 0.3])),
            "cycles_per_day": round(float(rng.uniform(0.8, 1.8)), 1),
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        })

    return aircraft_list


def generate_components(aircraft_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate 4 components per aircraft."""
    components = []
    for ac in aircraft_list:
        aid = ac["aircraft_id"]
        rng = np.random.default_rng(MASTER_SEED + hash(aid) % 10000)

        # 2 engines
        for eng_idx in range(1, 3):
            comp_id = f"{aid}-ENG-{eng_idx:02d}"
            components.append({
                "component_id": comp_id,
                "aircraft_id": aid,
                "component_type": "ENGINE",
                "subsystem": "PROPULSION",
                "part_no": rng.choice(PART_NUMBERS["ENGINE"]),
                "install_cycle": int(rng.integers(0, max(1, ac["total_cycles"] // 2))),
                "data_source": "SYNTHETIC_NON_OPERATIONAL",
            })

        # 1 hydraulic pump
        components.append({
            "component_id": f"{aid}-HYD-01",
            "aircraft_id": aid,
            "component_type": "HYDRAULIC_PUMP",
            "subsystem": "HYDRAULIC",
            "part_no": PART_NUMBERS["HYDRAULIC_PUMP"][0],
            "install_cycle": int(rng.integers(0, max(1, ac["total_cycles"] // 3))),
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        })

        # 1 gearbox
        components.append({
            "component_id": f"{aid}-GBX-01",
            "aircraft_id": aid,
            "component_type": "GEARBOX",
            "subsystem": "TRANSMISSION",
            "part_no": PART_NUMBERS["GEARBOX"][0],
            "install_cycle": int(rng.integers(0, max(1, ac["total_cycles"] // 4))),
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        })

    return components


def _assign_scenario(
    comp_id: str,
    comp_type: str,
    scenarios: dict[str, Any],
) -> dict[str, Any] | None:
    """Assign a degradation scenario to a component."""
    hero = scenarios["hero"]
    if comp_id == hero["component_id"]:
        # Hero: rapid bearing wear
        return {
            "name": "rapid_bearing_wear",
            "failure_mode": hero["failure_mode"],
            "onset_cycle": 120,
            "degradation": next(
                s for s in scenarios["scenarios"]
                if s["name"] == "rapid_bearing_wear"
            ),
        }

    # Assign scenarios to some components for variety
    rng = np.random.default_rng(MASTER_SEED + hash(comp_id) % 100000)
    roll = rng.random()

    matching = [s for s in scenarios["scenarios"] if s["component_type"] == comp_type]
    if not matching:
        return None

    if roll < 0.25:  # 25% chance of degradation
        scenario = rng.choice(matching)
        onset = int(rng.integers(
            scenario["onset_cycle_range"][0],
            scenario["onset_cycle_range"][1],
        ))
        return {
            "name": scenario["name"],
            "failure_mode": scenario.get("failure_mode"),
            "onset_cycle": onset,
            "degradation": scenario,
            "sensor_fault": scenario.get("sensor_fault"),
        }

    return None


def generate_health_data(
    components: list[dict[str, Any]],
    aircraft_map: dict[str, dict[str, Any]],
    num_cycles: int = 150,
) -> list[dict[str, Any]]:
    """Generate health telemetry for all components."""
    scenarios = load_scenarios()
    health_rows = []
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    for comp in components:
        comp_id = comp["component_id"]
        comp_type = comp["component_type"]
        sensors = COMPONENT_SENSORS[comp_type]
        rng = np.random.default_rng(MASTER_SEED + hash(comp_id) % 100000)

        scenario = _assign_scenario(comp_id, comp_type, scenarios)

        for cycle in range(1, num_cycles + 1):
            ts = base_time + timedelta(hours=cycle * 8, minutes=int(rng.integers(0, 60)))
            context = generate_operating_context(rng)

            for sensor_name, sensor_cfg in sensors.items():
                value = generate_sensor_value(
                    sensor_name=sensor_name,
                    sensor_cfg=sensor_cfg,
                    cycle=cycle,
                    onset_cycle=scenario["onset_cycle"] if scenario else None,
                    degradation=scenario.get("degradation") if scenario else None,
                    context=context,
                    rng=rng,
                    sensor_fault=scenario.get("sensor_fault") if scenario else None,
                )

                health_rows.append({
                    "timestamp": ts.isoformat(),
                    "aircraft_id": comp["aircraft_id"],
                    "component_id": comp_id,
                    "sensor": sensor_name,
                    "value": round(value, 4),
                    "unit": sensor_cfg["unit"],
                    "cycle": cycle,
                    "operating_context": json.dumps(context),
                    "data_source": "SYNTHETIC_NON_OPERATIONAL",
                })

    return health_rows


def generate_training_corpus(num_runs: int = 250) -> None:
    """Generate training data: run-to-failure sequences as Parquet."""
    scenarios = load_scenarios()

    for comp_type in ["ENGINE", "HYDRAULIC_PUMP"]:
        sensors = COMPONENT_SENSORS[comp_type]
        matching_scenarios = [
            s for s in scenarios["scenarios"]
            if s["component_type"] == comp_type and s.get("failure_mode")
        ]

        if not matching_scenarios:
            continue

        all_records = []
        for run_idx in range(num_runs):
            rng = np.random.default_rng(MASTER_SEED + run_idx * 1000 + hash(comp_type))
            scenario = rng.choice(matching_scenarios)
            run_length = int(rng.integers(150, 301))
            onset = int(rng.integers(
                scenario["onset_cycle_range"][0],
                scenario["onset_cycle_range"][1],
            ))

            # Censored run (no failure)?
            is_censored = rng.random() < 0.2  # 20% censored
            failure_cycle = run_length if not is_censored else None

            for cycle in range(1, run_length + 1):
                context = generate_operating_context(rng)
                rul = max(0, run_length - cycle) if not is_censored else None

                record: dict[str, Any] = {
                    "run_id": f"run-{comp_type}-{run_idx:04d}",
                    "component_type": comp_type,
                    "cycle": cycle,
                    "failure_mode": scenario.get("failure_mode") if not is_censored else None,
                    "is_censored": is_censored,
                    "RUL_cycles_at_t": rul,
                }

                for sensor_name, sensor_cfg in sensors.items():
                    value = generate_sensor_value(
                        sensor_name=sensor_name,
                        sensor_cfg=sensor_cfg,
                        cycle=cycle,
                        onset_cycle=onset,
                        degradation=scenario,
                        context=context,
                        rng=rng,
                    )
                    record[sensor_name] = round(value, 4)

                # Context features
                record["altitude_band"] = context["altitude_band"]
                record["ambient_temp_c"] = round(context["ambient_temp_c"], 1)
                record["load_factor"] = round(context["load_factor"], 3)

                all_records.append(record)

        df = pd.DataFrame(all_records)
        output_path = TRAINING_DIR / f"{comp_type.lower()}_training.parquet"
        df.to_parquet(output_path, index=False, engine="pyarrow")
        print(f"  [+] {comp_type}: {num_runs} runs, {len(df)} records -> {output_path}")


def generate_maintenance_events(
    components: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate historical maintenance events."""
    events = []
    base_time = datetime(2023, 6, 1, tzinfo=timezone.utc)
    rng = np.random.default_rng(MASTER_SEED + 5000)

    event_types = ["SCHEDULED", "UNSCHEDULED", "INSPECTION", "REPAIR"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    actions = ["REPLACED", "REPAIRED", "INSPECTED", "ADJUSTED", "CLEANED"]

    for comp in components:
        num_events = int(rng.integers(1, 5))
        for j in range(num_events):
            opened = base_time + timedelta(days=int(rng.integers(0, 365)))
            closed = opened + timedelta(days=int(rng.integers(1, 14)))
            events.append({
                "event_id": str(uuid.uuid4()),
                "aircraft_id": comp["aircraft_id"],
                "component_id": comp["component_id"],
                "fault_code": f"FC-{rng.integers(100, 999)}",
                "event_type": rng.choice(event_types),
                "severity": rng.choice(severities),
                "opened_at": opened.isoformat(),
                "closed_at": closed.isoformat(),
                "action": rng.choice(actions),
                "technician_notes": f"Routine check on {comp['component_type']}. No anomalies found during cycle {rng.integers(100, 500)}.",
                "data_source": "SYNTHETIC_NON_OPERATIONAL",
            })

    return events


def generate_inspections(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate inspection findings."""
    findings = []
    rng = np.random.default_rng(MASTER_SEED + 6000)
    base_time = datetime(2023, 9, 1, tzinfo=timezone.utc)

    finding_types = ["VISUAL", "NDT", "BORESCOPE", "OIL_ANALYSIS"]
    severities = ["INFO", "LOW", "MEDIUM", "HIGH"]

    for comp in components:
        if rng.random() < 0.4:  # 40% have findings
            findings.append({
                "finding_id": str(uuid.uuid4()),
                "component_id": comp["component_id"],
                "finding_type": rng.choice(finding_types),
                "severity": rng.choice(severities),
                "observation": f"Minor surface wear observed on {comp['component_type']} during routine inspection.",
                "date": (base_time + timedelta(days=int(rng.integers(0, 180)))).isoformat(),
                "data_source": "SYNTHETIC_NON_OPERATIONAL",
            })

    return findings


def generate_spares() -> list[dict[str, Any]]:
    """Generate spare parts inventory."""
    scenarios = load_scenarios()
    hero = scenarios["hero"]

    spares = [
        {
            "part_no": "PN-4007",
            "description": "Engine bearing assembly",
            "stock": hero["part_stock"],
            "min_stock": 2,
            "lead_time_days": hero["part_lead_time_days"],
            "criticality": "HIGH",
            "facility_id": "FAC-01",
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        {
            "part_no": "PN-4008",
            "description": "Engine turbine blade set",
            "stock": 4,
            "min_stock": 2,
            "lead_time_days": 10,
            "criticality": "HIGH",
            "facility_id": "FAC-01",
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        {
            "part_no": "PN-5012",
            "description": "Hydraulic pump seal kit",
            "stock": 8,
            "min_stock": 3,
            "lead_time_days": 3,
            "criticality": "MEDIUM",
            "facility_id": "FAC-02",
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        {
            "part_no": "PN-6003",
            "description": "Gearbox oil filter assembly",
            "stock": 12,
            "min_stock": 4,
            "lead_time_days": 2,
            "criticality": "LOW",
            "facility_id": "FAC-02",
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        # Low-stock critical part for dashboard scenario
        {
            "part_no": "PN-4009",
            "description": "Engine compressor rotor disk",
            "stock": 0,
            "min_stock": 1,
            "lead_time_days": 21,
            "criticality": "CRITICAL",
            "facility_id": "FAC-01",
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        {
            "part_no": "PN-5013",
            "description": "Hydraulic actuator cylinder",
            "stock": 1,
            "min_stock": 2,
            "lead_time_days": 14,
            "criticality": "HIGH",
            "facility_id": "FAC-02",
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
    ]
    return spares


def generate_facilities() -> list[dict[str, Any]]:
    """Generate maintenance facilities."""
    scenarios = load_scenarios()
    hero = scenarios["hero"]

    return [
        {
            "facility_id": "FAC-01",
            "name": "Primary Engine Workshop",
            "capability": "ENGINE",
            "slots_available": hero["facility_bays"],
            "avg_turnaround_days": hero["facility_turnaround_days"],
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        {
            "facility_id": "FAC-02",
            "name": "Hydraulic & Accessories Bay",
            "capability": "HYDRAULIC_PUMP,GEARBOX",
            "slots_available": 4,
            "avg_turnaround_days": 3.0,
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
        {
            "facility_id": "FAC-03",
            "name": "General Maintenance Hangar",
            "capability": "ENGINE,HYDRAULIC_PUMP,GEARBOX",
            "slots_available": 2,
            "avg_turnaround_days": 6.0,
            "data_source": "SYNTHETIC_NON_OPERATIONAL",
        },
    ]


def inject_data_defects(health_rows: list[dict[str, Any]], rng: np.random.Generator) -> list[dict[str, Any]]:
    """Inject data defects for validation testing."""
    defect_rows = list(health_rows)  # Copy

    # 1. Missing values (~1% of rows)
    for i in rng.choice(len(defect_rows), size=max(1, len(defect_rows) // 100), replace=False):
        defect_rows[i]["value"] = None  # type: ignore[assignment]

    # 2. Out-of-order timestamps (swap a few)
    swap_indices = rng.choice(range(10, len(defect_rows) - 10), size=5, replace=False)
    for idx in swap_indices:
        defect_rows[idx]["timestamp"], defect_rows[idx + 1]["timestamp"] = (
            defect_rows[idx + 1]["timestamp"],
            defect_rows[idx]["timestamp"],
        )

    # 3. Duplicate rows (add 3 exact duplicates)
    for _ in range(3):
        idx = int(rng.integers(0, len(defect_rows)))
        defect_rows.append(dict(defect_rows[idx]))

    # 4. Unit mismatch: some temperatures in Fahrenheit
    for i in rng.choice(len(defect_rows), size=3, replace=False):
        if defect_rows[i]["unit"] == "celsius":
            defect_rows[i]["unit"] = "fahrenheit"
            defect_rows[i]["value"] = round(defect_rows[i]["value"] * 9 / 5 + 32, 4) if defect_rows[i]["value"] else None

    # 5. Out-of-range spike
    spike_idx = int(rng.integers(0, len(defect_rows)))
    defect_rows[spike_idx]["value"] = 99999.0

    # 6. Unknown component_id
    defect_rows.append({
        "timestamp": "2024-03-15T10:00:00+00:00",
        "aircraft_id": "A-999",
        "component_id": "UNKNOWN-COMP-001",
        "sensor": "vibration_mm_s",
        "value": 5.0,
        "unit": "mm/s",
        "cycle": 100,
        "operating_context": "{}",
        "data_source": "SYNTHETIC_NON_OPERATIONAL",
    })

    return defect_rows


def write_csv(data: list[dict[str, Any]], filepath: Path) -> None:
    """Write data to CSV file."""
    if not data:
        return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  [+] {filepath.name}: {len(data)} rows")


def generate_failures_csv(components: list[dict[str, Any]], scenarios_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate failures.csv with RUL labels for the live fleet."""
    failures = []
    rng = np.random.default_rng(MASTER_SEED + 9000)

    for comp in components:
        comp_type = comp["component_type"]
        if comp_type == "GEARBOX":
            continue  # No RUL for gearbox

        scenario = _assign_scenario(comp["component_id"], comp_type, scenarios_cfg)
        if scenario and scenario.get("failure_mode"):
            # Estimate when failure would occur
            onset = scenario["onset_cycle"]
            # Failure at onset + some progression
            failure_cycle = onset + int(rng.integers(30, 80))
            failures.append({
                "asset_id": comp["aircraft_id"],
                "component_id": comp["component_id"],
                "event_time": f"2024-06-{rng.integers(1, 29):02d}T12:00:00+00:00",
                "failure_type": scenario["failure_mode"],
                "RUL_cycles_at_t": max(0, failure_cycle - 150),  # RUL at current cycle
            })

    return failures


def main() -> None:
    """Main generation entrypoint."""
    print("=" * 60)
    print("AERIS — Synthetic Data Generator")
    print("All data is SYNTHETIC and NON-OPERATIONAL")
    print("=" * 60)

    # Create directories
    FLEET_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    scenarios_cfg = load_scenarios()

    # 1. Aircraft fleet
    print("\n[1/8] Generating aircraft fleet...")
    aircraft = generate_aircraft_fleet()
    write_csv(aircraft, FLEET_DIR / "aircraft.csv")
    aircraft_map = {a["aircraft_id"]: a for a in aircraft}

    # 2. Components
    print("[2/8] Generating components...")
    components = generate_components(aircraft)
    write_csv(components, FLEET_DIR / "components.csv")

    # 3. Health telemetry
    print("[3/8] Generating health telemetry (this may take a moment)...")
    health = generate_health_data(components, aircraft_map)
    # Inject defects
    rng = np.random.default_rng(MASTER_SEED + 7777)
    health_with_defects = inject_data_defects(health, rng)
    write_csv(health_with_defects, FLEET_DIR / "health.csv")

    # 4. Maintenance events
    print("[4/8] Generating maintenance events...")
    maintenance = generate_maintenance_events(components)
    write_csv(maintenance, FLEET_DIR / "maintenance.csv")

    # 5. Inspections
    print("[5/8] Generating inspection findings...")
    inspections = generate_inspections(components)
    write_csv(inspections, FLEET_DIR / "inspections.csv")

    # 6. Spares
    print("[6/8] Generating spare parts inventory...")
    spares = generate_spares()
    write_csv(spares, FLEET_DIR / "spares.csv")

    # 7. Facilities
    print("[7/8] Generating facilities...")
    facilities = generate_facilities()
    write_csv(facilities, FLEET_DIR / "facilities.csv")

    # 8. Training corpus
    print("[8/8] Generating training corpus (Parquet)...")
    generate_training_corpus(num_runs=250)

    # Failures CSV
    failures = generate_failures_csv(components, scenarios_cfg)
    write_csv(failures, FLEET_DIR / "failures.csv")

    print("\n" + "=" * 60)
    print("Data generation complete!")
    print(f"Fleet data: {FLEET_DIR}")
    print(f"Training data: {TRAINING_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
