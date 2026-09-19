"""
GreenGrid AI — Alert service (Phase 2)

Every alert here is triggered by an actual threshold check against the
values passed in. Nothing is randomly generated. Severity levels:
"info", "warning", "high", "critical".
"""
from datetime import datetime, timezone
import config


def evaluate_alerts(battery_soc_pct: float, renewable_generation_kw: float, demand_kw: float,
                     cloud_cover_pct: float = None, precipitation_probability_pct: float = None,
                     grid_import_kw: float = 0.0, curtailed_kw: float = 0.0,
                     solar_expected_kw: float = None, solar_actual_kw: float = None) -> list:
    now = datetime.now(timezone.utc).isoformat()
    alerts = []

    if battery_soc_pct < config.BATTERY_MIN_SOC_PCT + 5:
        alerts.append({
            "timestamp": now, "severity": "high", "category": "battery",
            "message": f"Battery SOC is low ({battery_soc_pct:.0f}%).",
            "explanation": f"SOC is within 5 points of the configured minimum reserve ({config.BATTERY_MIN_SOC_PCT:.0f}%).",
            "recommended_action": "Defer non-essential loads until renewable generation or battery charge recovers.",
        })

    if cloud_cover_pct is not None and cloud_cover_pct >= 70:
        alerts.append({
            "timestamp": now, "severity": "warning", "category": "weather",
            "message": f"Heavy cloud cover forecast ({cloud_cover_pct:.0f}%).",
            "explanation": "High cloud cover reduces expected solar generation for the affected period.",
            "recommended_action": "Expect increased battery/grid reliance; consider shifting flexible loads earlier.",
        })

    if precipitation_probability_pct is not None and precipitation_probability_pct >= 60:
        alerts.append({
            "timestamp": now, "severity": "warning", "category": "weather",
            "message": f"High chance of rain ({precipitation_probability_pct:.0f}%).",
            "explanation": "Rain typically accompanies heavy cloud cover, further reducing solar output.",
            "recommended_action": "Monitor renewable surplus/deficit closely during this window.",
        })

    if demand_kw > 0 and renewable_generation_kw < demand_kw * 0.3:
        alerts.append({
            "timestamp": now, "severity": "warning", "category": "demand",
            "message": "Renewable generation is well below current demand.",
            "explanation": f"Renewable generation ({renewable_generation_kw:.2f} kW) covers less than 30% of demand ({demand_kw:.2f} kW).",
            "recommended_action": "Battery and/or grid import will cover most of the current load.",
        })

    if grid_import_kw > 0.05:
        alerts.append({
            "timestamp": now, "severity": "info", "category": "grid",
            "message": f"Drawing {grid_import_kw:.2f} kW from the grid.",
            "explanation": "Renewable generation plus available battery reserve is insufficient for current demand.",
            "recommended_action": "No action required; this is expected behavior when renewables and battery fall short.",
        })

    if curtailed_kw > 0.05:
        alerts.append({
            "timestamp": now, "severity": "info", "category": "renewable",
            "message": f"{curtailed_kw:.2f} kW of renewable surplus is being curtailed.",
            "explanation": "The battery is full and export is disabled, so excess generation cannot be used.",
            "recommended_action": "Consider enabling grid export or scheduling a flexible load to absorb the surplus.",
        })

    if renewable_generation_kw - demand_kw > 1.0 and battery_soc_pct < 95:
        alerts.append({
            "timestamp": now, "severity": "info", "category": "renewable",
            "message": "Renewable surplus available.",
            "explanation": f"Generation exceeds demand by {(renewable_generation_kw - demand_kw):.2f} kW and the battery has room to charge.",
            "recommended_action": "Good window to run flexible loads (EV charging, laundry) or charge the battery.",
        })

    if solar_expected_kw is not None and solar_actual_kw is not None and solar_expected_kw > 1.0:
        deviation = solar_expected_kw - solar_actual_kw
        if deviation > solar_expected_kw * 0.35:
            alerts.append({
                "timestamp": now, "severity": "high", "category": "maintenance",
                "message": "Potential performance anomaly detected in solar generation.",
                "explanation": (f"Actual output ({solar_actual_kw:.2f} kW) is {deviation:.2f} kW below the "
                                f"model's expectation ({solar_expected_kw:.2f} kW) for current conditions."),
                "recommended_action": "Inspect panels for shading, dust, or a possible inverter issue. This is a statistical flag, not confirmed hardware evidence.",
            })

    if not alerts:
        alerts.append({
            "timestamp": now, "severity": "info", "category": "system",
            "message": "No active alerts.",
            "explanation": "All monitored values are within expected thresholds.",
            "recommended_action": "None.",
        })

    return alerts
