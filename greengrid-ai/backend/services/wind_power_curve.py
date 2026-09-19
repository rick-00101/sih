"""
GreenGrid AI — generic wind power curve (Phase 2 helper, not a trained model)

The Phase 1 wind ML model was trained using the Kaggle turbine's actual
`Theoretical_Power_Curve` column, which we don't have for future/forecast
wind speeds (we only get raw wind speed from the weather API). This module
approximates that curve with a standard cubic wind-turbine power curve
(power ~ wind_speed^3 between cut-in and rated speed, flat at rated power
until cut-out, zero outside that range).

This is a textbook approximation, NOT the manufacturer's exact curve, and
is used only to produce a plausible input for the trained model at
forecast time — it is documented here so this distinction is never lost.
"""
import config


def estimate_theoretical_power(wind_speed_ms: float) -> float:
    if wind_speed_ms is None:
        return 0.0
    if wind_speed_ms < config.WIND_CUT_IN_MS or wind_speed_ms >= config.WIND_CUT_OUT_MS:
        return 0.0
    if wind_speed_ms >= config.WIND_RATED_MS:
        return config.WIND_TURBINE_RATED_KW
    # Cubic ramp between cut-in and rated speed
    span = config.WIND_RATED_MS - config.WIND_CUT_IN_MS
    fraction = ((wind_speed_ms - config.WIND_CUT_IN_MS) / span) ** 3
    return round(config.WIND_TURBINE_RATED_KW * fraction, 2)
