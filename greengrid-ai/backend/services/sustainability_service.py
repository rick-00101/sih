"""
GreenGrid AI — Sustainability calculations (Phase 2)

Deterministic, explainable, and NOT presented as a certified environmental
metric. "GreenGrid operational score" is this project's own composite
indicator, not an industry-standard rating.
"""
import config


def co2_avoided_kg(renewable_used_kwh: float, emission_factor: float = config.GRID_EMISSION_FACTOR_KG_PER_KWH) -> dict:
    return {
        "co2_avoided_kg": round(renewable_used_kwh * emission_factor, 2),
        "assumption": f"Calculated as renewable energy used (kWh) x grid emission factor ({emission_factor} kg CO2/kWh, configurable).",
        "source": "calculated",
    }


def green_score(renewable_utilization_pct: float, grid_dependency_pct: float,
                 battery_utilization_pct: float, curtailment_pct: float) -> dict:
    """
    All inputs are 0-100. Weights are our own explainable design choice,
    not a scientific standard — documented plainly here and in the API.
    """
    renewable_utilization_pct = max(0.0, min(100.0, renewable_utilization_pct))
    grid_dependency_pct = max(0.0, min(100.0, grid_dependency_pct))
    battery_utilization_pct = max(0.0, min(100.0, battery_utilization_pct))
    curtailment_pct = max(0.0, min(100.0, curtailment_pct))

    score = (
        renewable_utilization_pct * 0.45
        + (100 - grid_dependency_pct) * 0.30
        + battery_utilization_pct * 0.15
        + (100 - curtailment_pct) * 0.10
    )
    score = round(max(0.0, min(100.0, score)), 1)

    factors = {
        "renewable_utilization_pct": round(renewable_utilization_pct, 1),
        "grid_dependency_pct": round(grid_dependency_pct, 1),
        "battery_utilization_pct": round(battery_utilization_pct, 1),
        "curtailment_pct": round(curtailment_pct, 1),
    }
    return {
        "greengrid_operational_score": score,
        "label": "GreenGrid operational score (this project's own composite indicator — not a certified environmental rating)",
        "factors": factors,
        "weights": {"renewable_utilization": 0.45, "grid_independence": 0.30, "battery_utilization": 0.15, "low_curtailment": 0.10},
        "source": "calculated",
    }
