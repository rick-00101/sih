"""
GreenGrid AI — Solar model evaluation (standalone check)

Loads the already-trained, saved model (does NOT retrain) and re-computes
metrics on the test split, purely as a sanity check that the saved
artifact still behaves as expected.
"""
import json
import joblib
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocess import build_dataset, chronological_split, FEATURE_COLUMNS, TARGET_COLUMN

MODEL_DIR = Path(__file__).resolve().parents[2] / "backend" / "models" / "solar_model"


def main():
    model_path = MODEL_DIR / "model.joblib"
    if not model_path.exists():
        print(f"No saved model found at {model_path}. Run train.py first.")
        return

    model = joblib.load(model_path)
    with open(MODEL_DIR / "metadata.json") as f:
        meta = json.load(f)
    print(f"Loaded model: {meta['selected_model']} (target={meta['target']} {meta['target_unit']})")

    df = build_dataset()
    _, _, test = chronological_split(df)
    X_test, y_test = test[FEATURE_COLUMNS], test[TARGET_COLUMN]

    preds = np.clip(model.predict(X_test), 0, None)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds) ** 0.5
    r2 = r2_score(y_test, preds)

    print(f"Re-checked on {len(test)} test rows:")
    print(f"  MAE  = {mae:.2f} kW")
    print(f"  RMSE = {rmse:.2f} kW")
    print(f"  R2   = {r2:.4f}")

    assert abs(mae - meta["all_results"][meta["selected_model"]]["mae"]) < 1.0, \
        "Re-evaluated MAE drifted from saved metadata — investigate before trusting this model."
    print("OK: matches metadata recorded at training time.")


if __name__ == "__main__":
    main()
