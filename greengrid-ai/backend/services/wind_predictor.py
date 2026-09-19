"""
Loads the trained wind model ONCE at import time. No retraining at runtime.
"""
import json
import math
from pathlib import Path

import joblib
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "wind_model"

_model = None
_metadata = None
_load_error = None

try:
    _model = joblib.load(MODEL_DIR / "model.joblib")
    with open(MODEL_DIR / "metadata.json") as f:
        _metadata = json.load(f)
except Exception as exc:  # noqa: BLE001
    _load_error = str(exc)


def is_loaded() -> bool:
    return _model is not None


def load_error() -> str | None:
    return _load_error


def metadata() -> dict:
    return _metadata or {}


def predict(wind_speed: float, wind_direction: float, theoretical_power: float) -> float:
    if _model is None:
        raise RuntimeError(f"Wind model is not loaded: {_load_error}")

    dir_sin = math.sin(2 * math.pi * wind_direction / 360)
    dir_cos = math.cos(2 * math.pi * wind_direction / 360)

    row = pd.DataFrame([{
        "wind_speed": wind_speed,
        "theoretical_power": theoretical_power,
        "dir_sin": dir_sin,
        "dir_cos": dir_cos,
    }])
    row = row[_metadata["features"]]

    pred = float(_model.predict(row)[0])
    return max(0.0, pred)
