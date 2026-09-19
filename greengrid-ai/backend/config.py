"""
GreenGrid AI — Phase 2 configuration

All values are overridable via environment variables (see .env.example).
Nothing here is a secret; these are just tunable defaults so the same
code works for any location/battery size without editing source files.
"""
import os


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# Demo location default: New Delhi. Override with real coordinates via env vars.
LATITUDE = _float_env("LATITUDE", 28.6139)
LONGITUDE = _float_env("LONGITUDE", 77.2090)

WEATHER_API_BASE_URL = os.environ.get("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1/forecast")
WEATHER_TIMEOUT_SECONDS = _float_env("WEATHER_TIMEOUT_SECONDS", 5.0)

# CO2 estimate assumption — configurable, and always shown alongside any
# CO2 number in the API/UI so the assumption isn't hidden.
GRID_EMISSION_FACTOR_KG_PER_KWH = _float_env("GRID_EMISSION_FACTOR", 0.71)

# Battery defaults (a small building-scale battery, not the Kaggle plant scale)
BATTERY_CAPACITY_KWH = _float_env("BATTERY_CAPACITY_KWH", 13.5)
BATTERY_MIN_SOC_PCT = _float_env("BATTERY_MIN_SOC_PCT", 15.0)
BATTERY_MAX_SOC_PCT = _float_env("BATTERY_MAX_SOC_PCT", 100.0)
BATTERY_CHARGE_EFFICIENCY = _float_env("BATTERY_CHARGE_EFFICIENCY", 0.92)
BATTERY_DISCHARGE_EFFICIENCY = _float_env("BATTERY_DISCHARGE_EFFICIENCY", 0.92)
BATTERY_MAX_CHARGE_KW = _float_env("BATTERY_MAX_CHARGE_KW", 5.0)
BATTERY_MAX_DISCHARGE_KW = _float_env("BATTERY_MAX_DISCHARGE_KW", 5.0)

# Reference turbine used only to convert a forecast wind speed into an
# estimated "theoretical power" input for the trained wind model (the model
# itself was trained on the Kaggle turbine's actual theoretical-power
# column; at forecast time we don't have that column, so we approximate it
# from wind speed with a generic cubic curve, documented in
# services/wind_power_curve.py).
WIND_TURBINE_RATED_KW = _float_env("WIND_TURBINE_RATED_KW", 3600.0)
WIND_CUT_IN_MS = _float_env("WIND_CUT_IN_MS", 3.0)
WIND_RATED_MS = _float_env("WIND_RATED_MS", 12.0)
WIND_CUT_OUT_MS = _float_env("WIND_CUT_OUT_MS", 25.0)

# The solar and wind ML models were trained on utility/plant-scale Kaggle
# data (tens of thousands of kW). To combine their output with a small
# building's demand (a few kW) in the Simulation Lab / optimizer, we scale
# both down by the same order of magnitude. This is a demo-scale
# assumption, not a claim about any real site's capacity — always shown
# alongside the scaled figures in API responses.
SOLAR_SCALE_FACTOR = _float_env("SOLAR_SCALE_FACTOR", 0.001)
WIND_SCALE_FACTOR = _float_env("WIND_SCALE_FACTOR", 0.001)
