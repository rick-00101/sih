"""
PLACEHOLDER — NOT IMPLEMENTED IN PHASE 1.

This file exists only to document the intended Phase 2 architecture for
hydro so the interface shape is already agreed on. Nothing in here is
connected to a live data source, and calling it will not return a real
number.

Planned Phase 2 flow:
    Open-Meteo Flood API (river discharge, Q, in m^3/s)
        -> physics calculation:  P = rho * g * Q * H * eta
        -> hydro power estimate (kW)

Where:
    rho = water density (~1000 kg/m^3)
    g   = gravitational acceleration (9.81 m/s^2)
    Q   = river discharge (m^3/s) -- from the live API
    H   = head height (m) -- site-specific, not from the API
    eta = turbine + generator efficiency (typically 0.7-0.9)

This is a CALCULATION, not a trained ML model — there is no historical
hydro dataset backing this in Phase 1, per the honest-data rule.
"""


def estimate_hydro_power_placeholder(discharge_m3s: float, head_m: float, efficiency: float = 0.8) -> float:
    """
    Physics-based estimate ONLY — head_m and discharge_m3s must be supplied
    by the caller (i.e. not yet wired to a live API in Phase 1).
    Returns an estimate in kW. This function is NOT called by any route
    yet; it's here so Phase 2 has a clear place to plug in the live feed.
    """
    RHO = 1000.0   # kg/m^3
    G = 9.81       # m/s^2
    power_watts = RHO * G * discharge_m3s * head_m * efficiency
    return power_watts / 1000.0  # -> kW
