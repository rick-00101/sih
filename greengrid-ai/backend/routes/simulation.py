from fastapi import APIRouter

import config
from schemas.energy_schemas import SimulationRequest
from services import (
    solar_predictor, wind_predictor, wind_power_curve, irradiance_estimator,
    demand_forecaster, optimizer, sustainability_service, alert_service,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/run")
def run_simulation(payload: SimulationRequest):
    """
    The What-If Simulation engine. Deterministic: identical input always
    produces identical output (no randomness anywhere in this path).

    Pipeline: irradiance estimate -> real solar ML model -> real wind ML
    model -> demo demand profile -> rule-based optimizer -> calculated
    sustainability + alerts. Every section of the response says which of
    those categories it came from.
    """
    clear_sky = irradiance_estimator.clear_sky_irradiation(payload.hour)
    actual_irradiation = irradiance_estimator.cloud_adjusted_irradiation(payload.hour, payload.cloud_cover_pct)
    module_temp_actual = payload.ambient_temperature_c + 14 * actual_irradiation
    module_temp_clear = payload.ambient_temperature_c + 14 * clear_sky

    solar_expected_raw = solar_actual_raw = None
    if solar_predictor.is_loaded():
        solar_expected_raw = solar_predictor.predict(
            irradiation=clear_sky, ambient_temperature=payload.ambient_temperature_c,
            module_temperature=module_temp_clear, hour=payload.hour, plant_id=payload.plant_id)
        solar_actual_raw = solar_predictor.predict(
            irradiation=actual_irradiation, ambient_temperature=payload.ambient_temperature_c,
            module_temperature=module_temp_actual, hour=payload.hour, plant_id=payload.plant_id)

    theoretical_power = wind_power_curve.estimate_theoretical_power(payload.wind_speed_ms)
    wind_raw = None
    if wind_predictor.is_loaded():
        wind_raw = wind_predictor.predict(wind_speed=payload.wind_speed_ms, wind_direction=180.0,
                                           theoretical_power=theoretical_power)

    solar_kw = round((solar_actual_raw or 0.0) * config.SOLAR_SCALE_FACTOR, 3)
    solar_expected_kw = round((solar_expected_raw or 0.0) * config.SOLAR_SCALE_FACTOR, 3)
    wind_kw = round((wind_raw or 0.0) * config.WIND_SCALE_FACTOR, 3)
    renewable_kw = round(solar_kw + wind_kw, 3)

    demand_kw = demand_forecaster.demand_at_hour(payload.hour, payload.ambient_temperature_c, payload.day_type)

    opt = optimizer.optimize(
        renewable_generation_kw=renewable_kw, demand_kw=demand_kw,
        battery_soc_pct=payload.battery_soc_pct, allow_export=payload.allow_export,
        duration_hours=1.0,
    )

    renewable_utilization_pct = min(100.0, (opt.renewable_used_kw / renewable_kw * 100) if renewable_kw > 0 else 100.0)
    grid_dependency_pct = min(100.0, (opt.grid_import_kw / demand_kw * 100) if demand_kw > 0 else 0.0)
    activity = max(renewable_kw, demand_kw, 0.01)
    battery_utilization_pct = min(100.0, (opt.battery_charging_kw + opt.battery_discharging_kw) / activity * 100)
    curtailment_pct = min(100.0, (opt.curtailed_kw / renewable_kw * 100) if renewable_kw > 0 else 0.0)

    co2 = sustainability_service.co2_avoided_kg(opt.renewable_used_kw)  # 1-hour step -> kWh == kW
    score = sustainability_service.green_score(renewable_utilization_pct, grid_dependency_pct,
                                                battery_utilization_pct, curtailment_pct)

    alerts = alert_service.evaluate_alerts(
        battery_soc_pct=opt.battery_soc_pct, renewable_generation_kw=renewable_kw, demand_kw=demand_kw,
        cloud_cover_pct=payload.cloud_cover_pct, precipitation_probability_pct=payload.precipitation_probability_pct,
        grid_import_kw=opt.grid_import_kw, curtailed_kw=opt.curtailed_kw,
        # NOTE: we deliberately do NOT pass solar_expected_kw/solar_actual_kw here.
        # Both numbers come from the same model fed different weather inputs
        # (clear-sky vs. cloud-adjusted) — any gap between them is just the
        # cloud-cover effect, already surfaced by the weather alert above, and
        # is not an independent sensor reading. Flagging that gap as a
        # "performance anomaly" would misrepresent a weather effect as an
        # equipment issue. The anomaly check is only meaningful once a real,
        # independent sensor reading exists to compare against the model's
        # expectation — /alerts/evaluate still accepts those fields directly
        # for that future use.
    )

    return {
        "inputs": payload.dict(),
        "solar": {
            "expected_kw": solar_expected_kw, "actual_kw": solar_kw,
            "raw_model_output_kw": solar_actual_raw, "scale_factor": config.SOLAR_SCALE_FACTOR,
            "source": "ml_prediction" if solar_predictor.is_loaded() else "unavailable",
            "note": "Raw model output is at the training dataset's industrial-plant scale; scaled down for this small-building demo.",
        },
        "wind": {
            "estimated_kw": wind_kw, "raw_model_output_kw": wind_raw,
            "theoretical_power_estimate_kw": theoretical_power, "scale_factor": config.WIND_SCALE_FACTOR,
            "source": "ml_prediction" if wind_predictor.is_loaded() else "unavailable",
            "note": "theoretical_power is estimated from wind speed via a generic cubic curve, not the exact manufacturer curve.",
        },
        "demand": {"demand_kw": demand_kw, "source": "simulated_demo_profile"},
        "optimizer": {**opt.__dict__},
        "sustainability": {"co2": co2, "green_score": score},
        "alerts": alerts,
        "source_summary": (
            "solar & wind = real trained ML models (scaled for demo building size); "
            "demand = simulated demo profile; optimizer/battery/sustainability = calculated; "
            "cloud cover / temperature / wind speed here are the scenario inputs you provided, not live weather."
        ),
    }
