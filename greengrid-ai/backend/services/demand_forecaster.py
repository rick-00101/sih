"""
GreenGrid AI — Demand forecaster (Phase 2)

No historical demand dataset exists for this prototype, so this module
produces a DETERMINISTIC demo demand profile: the same inputs (hour,
day type, temperature) always produce the same output. This is clearly
labeled "simulated/demo" wherever it's returned via the API — it is not
a trained model and must never be presented as one.

The shape (morning + evening peaks, a mild temperature sensitivity for
cooling load) mirrors typical small building consumption and matches the
profile already used by the existing frontend simulation, so Phase 2
numbers are consistent with what the dashboard showed in Phase 1.
"""
import math


def demand_at_hour(hour: float, temperature_c: float = 28.0, day_type: str = "weekday") -> float:
    """Returns an estimated demand in kW for a given hour (0-24, float ok)."""
    base = 3.4
    morning_peak = 2.1 * math.exp(-((hour - 8) ** 2) / (2 * 1.4 ** 2))
    evening_peak = 2.8 * math.exp(-((hour - 19.5) ** 2) / (2 * 1.8 ** 2))
    weekend_factor = 0.85 if day_type == "weekend" else 1.0
    # Mild cooling-load sensitivity: warmer than 28C nudges demand up.
    temp_adjustment = max(0.0, (temperature_c - 28.0)) * 0.06
    demand = (base + morning_peak + evening_peak) * weekend_factor + temp_adjustment
    return round(max(0.4, demand), 2)


def hourly_forecast(start_hour: float, hours: int, temperature_c: float = 28.0, day_type: str = "weekday") -> list:
    out = []
    for i in range(hours):
        h = (start_hour + i) % 24
        out.append({"hour_offset": i, "hour_of_day": round(h, 2), "demand_kw": demand_at_hour(h, temperature_c, day_type)})
    return out


def summary(current_hour: float, temperature_c: float = 28.0, day_type: str = "weekday") -> dict:
    forecast = hourly_forecast(current_hour, 24, temperature_c, day_type)
    peak = max(forecast, key=lambda r: r["demand_kw"])
    return {
        "current_demand_kw": demand_at_hour(current_hour, temperature_c, day_type),
        "next_hour_demand_kw": forecast[1]["demand_kw"] if len(forecast) > 1 else None,
        "hourly_forecast": forecast,
        "peak_demand_kw": peak["demand_kw"],
        "peak_hour_of_day": peak["hour_of_day"],
        "expected_daily_demand_kwh": round(sum(r["demand_kw"] for r in forecast), 1),
        "source": "simulated_demo_profile",
    }
