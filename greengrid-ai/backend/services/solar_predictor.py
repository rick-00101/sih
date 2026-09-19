"""
Loads the trained solar model ONCE at import time. The backend never
retrains — it only loads the artifact that ml/solar/train.py produced.
"""
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "solar_model"

_model = None
_metadata = None
_load_error = None

try:
    _model = joblib.load(MODEL_DIR / "model.joblib")
    with open(MODEL_DIR / "metadata.json") as f:
        _metadata = json.load(f)
except Exception as exc:  # noqa: BLE001 - we want to report this at /health, not crash the app
    _load_error = str(exc)


def is_loaded() -> bool:
    return _model is not None


def load_error() -> str | None:
    return _load_error


def metadata() -> dict:
    return _metadata or {}


def predict(irradiation: float, ambient_temperature: float, module_temperature: float,
            hour: float, plant_id: int = 1) -> float:
    if _model is None:
        raise RuntimeError(f"Solar model is not loaded: {_load_error}")

    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)
    is_plant_2 = 1 if plant_id == 2 else 0

    row = pd.DataFrame([{
        "IRRADIATION": irradiation,
        "AMBIENT_TEMPERATURE": ambient_temperature,
        "MODULE_TEMPERATURE": module_temperature,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "is_plant_2": is_plant_2,
    }])
    # Column order must match training (FEATURE_COLUMNS in ml/solar/preprocess.py)
    row = row[_metadata["features"]]

    pred = float(_model.predict(row)[0])
    return max(0.0, pred)  # generation can't be negative
