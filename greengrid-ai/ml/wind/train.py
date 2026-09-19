"""
GreenGrid AI — Wind model training

Trains and compares Linear Regression (baseline) vs. Random Forest on
real Kaggle wind turbine SCADA data (full year, 10-min resolution).
Saves whichever wins on held-out test RMSE.
"""
import json
import joblib
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from preprocess import build_dataset, chronological_split, FEATURE_COLUMNS, TARGET_COLUMN

MODEL_OUT_DIR = Path(__file__).resolve().parents[2] / "backend" / "models" / "wind_model"
MODEL_OUT_DIR.mkdir(parents=True, exist_ok=True)


def evaluate(model, X, y, label):
    preds = np.clip(model.predict(X), 0, None)
    mae = mean_absolute_error(y, preds)
    rmse = mean_squared_error(y, preds) ** 0.5
    r2 = r2_score(y, preds)
    print(f"  [{label}] MAE={mae:.2f} kW  RMSE={rmse:.2f} kW  R2={r2:.4f}")
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 4)}


def main():
    print("Loading and preparing wind dataset...")
    df = build_dataset()
    train, val, test = chronological_split(df)
    print(f"train={len(train)}  val={len(val)}  test={len(test)}")

    X_train, y_train = train[FEATURE_COLUMNS], train[TARGET_COLUMN]
    X_val, y_val = val[FEATURE_COLUMNS], val[TARGET_COLUMN]
    X_test, y_test = test[FEATURE_COLUMNS], test[TARGET_COLUMN]

    results = {}

    print("\nTraining Linear Regression (baseline)...")
    lin = LinearRegression()
    lin.fit(X_train, y_train)
    print(" Validation:")
    evaluate(lin, X_val, y_val, "linear/val")
    print(" Test:")
    results["linear_regression"] = evaluate(lin, X_test, y_test, "linear/test")

    print("\nTraining Random Forest Regressor...")
    rf = RandomForestRegressor(
        n_estimators=200, max_depth=14, min_samples_leaf=3,
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    print(" Validation:")
    evaluate(rf, X_val, y_val, "rf/val")
    print(" Test:")
    results["random_forest"] = evaluate(rf, X_test, y_test, "rf/test")

    winner_name = min(results, key=lambda k: results[k]["rmse"])
    winner_model = lin if winner_name == "linear_regression" else rf
    print(f"\nSelected model: {winner_name} (lower test RMSE)")

    joblib.dump(winner_model, MODEL_OUT_DIR / "model.joblib")
    metadata = {
        "target": "active_power",
        "target_unit": "kW",
        "features": FEATURE_COLUMNS,
        "selected_model": winner_name,
        "all_results": results,
        "train_rows": len(train),
        "val_rows": len(val),
        "test_rows": len(test),
        "data_source": "Kaggle Wind Turbine SCADA Dataset (berkerisen), T1.csv, full year 2018",
        "notes": "theoretical_power is a deterministic function of wind_speed (manufacturer power curve), not derived from the actual target, so it does not leak the label.",
    }
    with open(MODEL_OUT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model + metadata to {MODEL_OUT_DIR}")


if __name__ == "__main__":
    main()
