"""
GreenGrid AI — Smart Optimizer (Phase 2)

A clean, explainable rule-based allocation engine (deliberately NOT
over-engineered with a solver library for this prototype — see README
"Phase 3 recommendations" for the OR-Tools upgrade path).

Given renewable generation, demand, and battery state, decides how much
goes to: building load, battery charge/discharge, grid import/export,
and curtailment — plus a plain-English reason, matching the project's
"Explainable AI" requirement.
"""
from dataclasses import dataclass, field

import services.battery_service as battery_service
from services.battery_service import BatteryConfig


@dataclass
class OptimizationResult:
    renewable_generation_kw: float
    demand_kw: float
    renewable_used_kw: float
    battery_charging_kw: float
    battery_discharging_kw: float
    grid_import_kw: float
    grid_export_kw: float
    curtailed_kw: float
    battery_soc_pct: float
    recommended_action: str
    reason: str
    source: str = "calculated"


def optimize(renewable_generation_kw: float, demand_kw: float, battery_soc_pct: float,
             allow_export: bool = True, cfg: BatteryConfig = BatteryConfig(),
             duration_hours: float = (1 / 6)) -> OptimizationResult:
    """
    duration_hours defaults to 10 minutes (1/6 hour) — a reasonable single
    control-step length for a dashboard tick; callers may pass a different
    step size (e.g. 1.0 for an hourly forecast slot).
    """
    renewable_used = min(renewable_generation_kw, demand_kw)
    remaining_demand = max(0.0, demand_kw - renewable_generation_kw)
    surplus = max(0.0, renewable_generation_kw - demand_kw)

    battery_charge_kw = 0.0
    battery_discharge_kw = 0.0
    grid_import_kw = 0.0
    grid_export_kw = 0.0
    curtailed_kw = 0.0
    new_soc = battery_soc_pct

    if surplus > 0:
        # Case 1: renewable generation exceeds demand.
        room_kwh = battery_service.available_charge_room_kwh(battery_soc_pct, cfg)
        max_charge_this_step_kw = min(cfg.max_charge_kw, room_kwh / duration_hours if duration_hours > 0 else cfg.max_charge_kw)
        battery_charge_kw = min(surplus, max_charge_this_step_kw)
        leftover = surplus - battery_charge_kw
        if allow_export:
            grid_export_kw = leftover
        else:
            curtailed_kw = leftover
        new_soc = battery_service.apply_charge(battery_soc_pct, battery_charge_kw, duration_hours, cfg)

        if battery_charge_kw > 0.05:
            reason = (f"Renewable generation ({renewable_generation_kw:.2f} kW) exceeds demand "
                      f"({demand_kw:.2f} kW). Charging the battery with the {surplus:.2f} kW surplus"
                      + (f"; {grid_export_kw:.2f} kW exported to the grid." if grid_export_kw > 0.05 else "."))
            action = "Charge battery"
        elif grid_export_kw > 0.05:
            reason = "Battery has no room to charge further, so the surplus is exported to the grid."
            action = "Export surplus to grid"
        else:
            reason = "Surplus renewable generation is available but cannot be stored or exported, so it is curtailed."
            action = "Curtail surplus"

    elif remaining_demand > 0:
        # Case 2: demand exceeds renewable generation.
        usable_kwh = battery_service.available_discharge_kwh(battery_soc_pct, cfg)
        max_discharge_this_step_kw = min(cfg.max_discharge_kw, usable_kwh / duration_hours if duration_hours > 0 else cfg.max_discharge_kw)
        battery_discharge_kw = min(remaining_demand, max_discharge_this_step_kw)
        grid_import_kw = remaining_demand - battery_discharge_kw
        new_soc = battery_service.apply_discharge(battery_soc_pct, battery_discharge_kw, duration_hours, cfg)

        if battery_discharge_kw > 0.05 and grid_import_kw <= 0.05:
            reason = (f"Demand ({demand_kw:.2f} kW) exceeds renewable generation "
                      f"({renewable_generation_kw:.2f} kW). The battery covers the gap without needing the grid.")
            action = "Discharge battery"
        elif battery_discharge_kw > 0.05:
            reason = (f"Demand exceeds renewable generation and available battery reserve. The battery "
                      f"covers {battery_discharge_kw:.2f} kW; the remaining {grid_import_kw:.2f} kW comes from the grid.")
            action = "Discharge battery + grid import"
        else:
            reason = (f"Demand exceeds renewable generation and the battery is at its minimum reserve "
                      f"({cfg.min_soc_pct:.0f}%), so the full {grid_import_kw:.2f} kW gap is drawn from the grid.")
            action = "Grid import"
    else:
        reason = "Renewable generation matches demand exactly. No battery or grid action needed."
        action = "Hold — balanced"

    return OptimizationResult(
        renewable_generation_kw=round(renewable_generation_kw, 2),
        demand_kw=round(demand_kw, 2),
        renewable_used_kw=round(renewable_used, 2),
        battery_charging_kw=round(battery_charge_kw, 2),
        battery_discharging_kw=round(battery_discharge_kw, 2),
        grid_import_kw=round(grid_import_kw, 2),
        grid_export_kw=round(grid_export_kw, 2),
        curtailed_kw=round(curtailed_kw, 2),
        battery_soc_pct=new_soc,
        recommended_action=action,
        reason=reason,
    )
