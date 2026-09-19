"""
GreenGrid AI — Phase 1 offline tests (no server required)

Run with:
    cd greengrid-ai
    python3 tests/test_pipeline.py

Covers: dataset loading, preprocessing, model loading, and sane
(not "accurate" — just physically sensible) prediction behavior.
"""
import sys
import importlib.util
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


def load_module(name, path):
    """Load a same-named preprocess.py from solar/ and wind/ without them
    colliding in sys.modules (both files are literally called preprocess.py)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


print("1-2. Solar: dataset loading + preprocessing")
solar_pre = load_module("solar_preprocess", ROOT / "ml" / "solar" / "preprocess.py")
solar_df = solar_pre.build_dataset()
check("solar dataset has rows", len(solar_df) > 1000)
check("solar dataset has both plants", solar_df["plant_id"].nunique() == 2)
check("solar target has no NaN", solar_df[solar_pre.TARGET_COLUMN].isna().sum() == 0)
check("solar target is never negative", (solar_df[solar_pre.TARGET_COLUMN] >= 0).all())

print("\n1-2. Wind: dataset loading + preprocessing")
wind_pre = load_module("wind_preprocess", ROOT / "ml" / "wind" / "preprocess.py")
wind_df = wind_pre.build_dataset()
check("wind dataset has rows", len(wind_df) > 10000)
check("wind target has no NaN", wind_df[wind_pre.TARGET_COLUMN].isna().sum() == 0)
check("wind target is never negative", (wind_df[wind_pre.TARGET_COLUMN] >= 0).all())

print("\n3-4. Model artifacts exist and load")
import joblib  # noqa: E402
solar_model_path = ROOT / "backend" / "models" / "solar_model" / "model.joblib"
wind_model_path = ROOT / "backend" / "models" / "wind_model" / "model.joblib"
check("solar model file exists", solar_model_path.exists())
check("wind model file exists", wind_model_path.exists())
if solar_model_path.exists():
    solar_model = joblib.load(solar_model_path)
    check("solar model loads", solar_model is not None)
if wind_model_path.exists():
    wind_model = joblib.load(wind_model_path)
    check("wind model loads", wind_model is not None)

print("\n5. Solar prediction is numerical and reasonable")
from services import solar_predictor  # noqa: E402
sunny_midday = solar_predictor.predict(irradiation=0.9, ambient_temperature=32, module_temperature=48, hour=13, plant_id=1)
night = solar_predictor.predict(irradiation=0.0, ambient_temperature=20, module_temperature=18, hour=2, plant_id=1)
check("midday prediction is a number", isinstance(sunny_midday, float))
check("midday prediction is positive", sunny_midday > 0)
check("night prediction is ~zero", night < 50)  # kW, small tolerance
check("midday generates more than night", sunny_midday > night)

print("\n6. Wind prediction is numerical and reasonable")
from services import wind_predictor  # noqa: E402
strong_wind = wind_predictor.predict(wind_speed=12, wind_direction=180, theoretical_power=3400)
light_wind = wind_predictor.predict(wind_speed=1, wind_direction=90, theoretical_power=10)
check("strong-wind prediction is a number", isinstance(strong_wind, float))
check("strong wind generates more than light wind", strong_wind > light_wind)
check("light-wind prediction is near zero", light_wind < 100)

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
