"""
GreenGrid AI — clear-sky irradiance approximation (Phase 2 helper)

A simple bell curve peaking at solar noon, used only to turn "hour of
day" + "cloud cover %" into a plausible IRRADIATION input for the
trained solar model when we don't have an actual pyranometer reading
(e.g. inside the Simulation Lab, or before a real on-site sensor feed
exists). This is NOT a real solar-position / atmospheric radiative
transfer model — it's a documented approximation, matching the shape
used in the Phase 1 frontend simulation for consistency.
"""
import math


def clear_sky_irradiation(hour: float) -> float:
    """Returns an approximate clear-sky irradiation in kW/m^2 (roughly
    0 to ~1.05, matching typical IRRADIATION values in the training data)."""
    if hour < 6 or hour > 18.5:
        return 0.0
    peak_hour, spread = 13.0, 3.6
    return round(max(0.0, 1.05 * math.exp(-((hour - peak_hour) ** 2) / (2 * spread ** 2))), 4)


def cloud_adjusted_irradiation(hour: float, cloud_cover_pct: float) -> float:
    clear = clear_sky_irradiation(hour)
    factor = 1 - (max(0.0, min(100.0, cloud_cover_pct)) / 100.0) * 0.9
    return round(max(0.0, clear * factor), 4)
