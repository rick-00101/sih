"""
GreenGrid AI — Battery model (Phase 2)

A physically understandable, deterministic battery simulation. SOC only
changes because of an actual computed energy allocation (from the
optimizer) — never randomly.
"""
from dataclasses import dataclass
import config


@dataclass
class BatteryConfig:
    capacity_kwh: float = config.BATTERY_CAPACITY_KWH
    min_soc_pct: float = config.BATTERY_MIN_SOC_PCT
    max_soc_pct: float = config.BATTERY_MAX_SOC_PCT
    charge_efficiency: float = config.BATTERY_CHARGE_EFFICIENCY
    discharge_efficiency: float = config.BATTERY_DISCHARGE_EFFICIENCY
    max_charge_kw: float = config.BATTERY_MAX_CHARGE_KW
    max_discharge_kw: float = config.BATTERY_MAX_DISCHARGE_KW


def available_charge_room_kwh(soc_pct: float, cfg: BatteryConfig = BatteryConfig()) -> float:
    """How much energy (kWh, before charge-efficiency loss) the battery can still accept."""
    room_pct = max(0.0, cfg.max_soc_pct - soc_pct)
    return room_pct / 100.0 * cfg.capacity_kwh


def available_discharge_kwh(soc_pct: float, cfg: BatteryConfig = BatteryConfig()) -> float:
    """How much energy (kWh, before discharge-efficiency loss) the battery can still give up
    while staying at or above the configured minimum reserve."""
    usable_pct = max(0.0, soc_pct - cfg.min_soc_pct)
    return usable_pct / 100.0 * cfg.capacity_kwh


def apply_charge(soc_pct: float, charge_kw: float, duration_hours: float, cfg: BatteryConfig = BatteryConfig()) -> float:
    """Charging the battery by charge_kw for duration_hours. Returns the new SOC%."""
    energy_in_kwh = charge_kw * duration_hours * cfg.charge_efficiency
    new_soc_pct = soc_pct + (energy_in_kwh / cfg.capacity_kwh) * 100.0
    return round(min(cfg.max_soc_pct, new_soc_pct), 2)


def apply_discharge(soc_pct: float, discharge_kw: float, duration_hours: float, cfg: BatteryConfig = BatteryConfig()) -> float:
    """Discharging the battery by discharge_kw for duration_hours. Returns the new SOC%."""
    energy_out_kwh = discharge_kw * duration_hours / cfg.discharge_efficiency
    new_soc_pct = soc_pct - (energy_out_kwh / cfg.capacity_kwh) * 100.0
    return round(max(cfg.min_soc_pct, new_soc_pct), 2)


def status(soc_pct: float, cfg: BatteryConfig = BatteryConfig()) -> dict:
    return {
        "capacity_kwh": cfg.capacity_kwh,
        "soc_pct": round(soc_pct, 1),
        "min_soc_pct": cfg.min_soc_pct,
        "max_soc_pct": cfg.max_soc_pct,
        "usable_energy_kwh": round(available_discharge_kwh(soc_pct, cfg), 2),
        "chargeable_room_kwh": round(available_charge_room_kwh(soc_pct, cfg), 2),
        "source": "calculated",
    }
