"""
GreenGrid AI — Phase 2 offline tests (no server required)
Run: python3 tests/test_phase2.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

passed, failed = 0, 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}")
        failed += 1


from services import demand_forecaster, battery_service, optimizer, sustainability_service, alert_service, wind_power_curve, irradiance_estimator  # noqa: E402

print("Demand forecaster — deterministic, no randomness")
d1 = demand_forecaster.demand_at_hour(8, 30, "weekday")
d2 = demand_forecaster.demand_at_hour(8, 30, "weekday")
check("same inputs -> identical output", d1 == d2)
check("weekend demand is lower than weekday at same hour/temp", demand_forecaster.demand_at_hour(19, 30, "weekend") < demand_forecaster.demand_at_hour(19, 30, "weekday"))

print("\nBattery — normal, low, full cases")
cfg = battery_service.BatteryConfig()
check("charging increases SOC", battery_service.apply_charge(50, 2, 1, cfg) > 50)
check("discharging decreases SOC", battery_service.apply_discharge(50, 2, 1, cfg) < 50)
check("SOC never exceeds max", battery_service.apply_charge(99, 5, 1, cfg) <= cfg.max_soc_pct)
check("SOC never drops below min", battery_service.apply_discharge(cfg.min_soc_pct + 1, 5, 1, cfg) >= cfg.min_soc_pct)

print("\nOptimizer — normal, surplus, deficit, low-battery cases")
r_surplus = optimizer.optimize(renewable_generation_kw=8, demand_kw=4, battery_soc_pct=60)
check("surplus case charges battery", r_surplus.battery_charging_kw > 0)
check("surplus case draws nothing from grid", r_surplus.grid_import_kw == 0)

r_deficit = optimizer.optimize(renewable_generation_kw=1, demand_kw=6, battery_soc_pct=60)
check("deficit case discharges battery", r_deficit.battery_discharging_kw > 0)

r_low_batt = optimizer.optimize(renewable_generation_kw=1, demand_kw=6, battery_soc_pct=cfg.min_soc_pct)
check("deficit + battery at floor -> no discharge, full grid import", r_low_batt.battery_discharging_kw == 0 and r_low_batt.grid_import_kw > 0)

r_full_batt = optimizer.optimize(renewable_generation_kw=10, demand_kw=2, battery_soc_pct=100, allow_export=True)
check("surplus + full battery -> exports rather than charges", r_full_batt.battery_charging_kw == 0 and r_full_batt.grid_export_kw > 0)

r_no_export = optimizer.optimize(renewable_generation_kw=10, demand_kw=2, battery_soc_pct=100, allow_export=False)
check("surplus + full battery + export disabled -> curtails", r_no_export.curtailed_kw > 0)

print("\nSustainability — deterministic")
s1 = sustainability_service.green_score(80, 10, 30, 0)
s2 = sustainability_service.green_score(80, 10, 30, 0)
check("same inputs -> identical score", s1["greengrid_operational_score"] == s2["greengrid_operational_score"])
check("higher renewable utilization -> higher score, all else equal", sustainability_service.green_score(95, 10, 30, 0)["greengrid_operational_score"] > s1["greengrid_operational_score"])
check("CO2 avoided scales with renewable energy used", sustainability_service.co2_avoided_kg(10)["co2_avoided_kg"] > sustainability_service.co2_avoided_kg(1)["co2_avoided_kg"])

print("\nAlerts — threshold-based, no randomness")
a_low_batt = alert_service.evaluate_alerts(battery_soc_pct=10, renewable_generation_kw=5, demand_kw=5)
check("low battery triggers a battery alert", any(a["category"] == "battery" for a in a_low_batt))
a_fine = alert_service.evaluate_alerts(battery_soc_pct=70, renewable_generation_kw=5, demand_kw=4)
check("healthy state produces no false battery/grid alerts", not any(a["category"] in ("battery",) for a in a_fine))

print("\nWind power curve — sane physical behavior")
check("below cut-in -> zero", wind_power_curve.estimate_theoretical_power(1.0) == 0.0)
check("above cut-out -> zero", wind_power_curve.estimate_theoretical_power(30.0) == 0.0)
check("at/above rated -> full rated power", wind_power_curve.estimate_theoretical_power(15.0) == wind_power_curve.estimate_theoretical_power(20.0))
check("mid-range power increases with wind speed", wind_power_curve.estimate_theoretical_power(6) < wind_power_curve.estimate_theoretical_power(10))

print("\nIrradiance estimator — sane physical behavior")
check("midnight has zero clear-sky irradiance", irradiance_estimator.clear_sky_irradiation(0) == 0.0)
check("midday has positive clear-sky irradiance", irradiance_estimator.clear_sky_irradiation(13) > 0.0)
check("more cloud cover reduces irradiance", irradiance_estimator.cloud_adjusted_irradiation(13, 90) < irradiance_estimator.cloud_adjusted_irradiation(13, 10))

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
