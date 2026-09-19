"""
GreenGrid AI — Solar preprocessing

Source data: Kaggle "Solar Power Generation Data" (anikannal), 2 plants,
15-minute resolution, 34 days (15 May - 17 Jun 2020).

Target: total plant AC_POWER (sum of AC_POWER across all inverters at a
plant, at a given timestamp) — this is "how much the plant is generating
right now", which is the number GreenGrid's dashboard needs to predict.

Features used: IRRADIATION, AMBIENT_TEMPERATURE, MODULE_TEMPERATURE (from
the plant's weather sensor), hour-of-day (as sin/cos), and which plant the
reading is from (one-hot).

Features deliberately EXCLUDED (data leakage):
- DC_POWER: measured at (almost) the same instant as AC_POWER by the same
  inverter. Using it to "predict" AC_POWER is not a real forecast — it's
  just inverter-efficiency modeling, and DC_POWER isn't known in advance.
- DAILY_YIELD, TOTAL_YIELD: these are running cumulative sums of AC_POWER
  itself. Using them as inputs would leak the target directly.
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "solar"

PLANT_CONFIG = {
    1: {
        "gen_file": "Plant_1_Generation_Data.csv",
        "weather_file": "Plant_1_Weather_Sensor_Data.csv",
        "gen_dt_format": "%d-%m-%Y %H:%M",   # Plant 1 generation file uses DD-MM-YYYY
    },
    2: {
        "gen_file": "Plant_2_Generation_Data.csv",
        "weather_file": "Plant_2_Weather_Sensor_Data.csv",
        "gen_dt_format": None,                # Plant 2 files are already ISO (YYYY-MM-DD)
    },
}


def _load_plant(plant_id: int) -> pd.DataFrame:
    cfg = PLANT_CONFIG[plant_id]

    gen = pd.read_csv(DATA_DIR / cfg["gen_file"])
    if cfg["gen_dt_format"]:
        gen["dt"] = pd.to_datetime(gen["DATE_TIME"], format=cfg["gen_dt_format"])
    else:
        gen["dt"] = pd.to_datetime(gen["DATE_TIME"])

    # Sum AC_POWER across all 22 inverters at each timestamp -> plant-level output.
    plant_power = gen.groupby("dt", as_index=False)["AC_POWER"].sum()

    weather = pd.read_csv(DATA_DIR / cfg["weather_file"])
    weather["dt"] = pd.to_datetime(weather["DATE_TIME"])
    weather = weather[["dt", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"]]

    merged = pd.merge(plant_power, weather, on="dt", how="inner")
    merged["plant_id"] = plant_id
    return merged


def build_dataset() -> pd.DataFrame:
    frames = [_load_plant(pid) for pid in PLANT_CONFIG]
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["plant_id", "dt"]).reset_index(drop=True)

    # Basic cleaning
    before = len(df)
    df = df.dropna(subset=["AC_POWER", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"])
    df = df[df["AC_POWER"] >= 0]  # generation can't be physically negative
    dropped = before - len(df)

    # Time-of-day features (cyclical, so 23:59 is "close to" 00:00)
    hour_float = df["dt"].dt.hour + df["dt"].dt.minute / 60.0
    df["hour_sin"] = np.sin(2 * np.pi * hour_float / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour_float / 24)

    # One-hot the plant id (small cardinality, 2 plants in this dataset)
    df["is_plant_2"] = (df["plant_id"] == 2).astype(int)

    df.attrs["rows_dropped_cleaning"] = dropped
    return df


FEATURE_COLUMNS = [
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "hour_sin",
    "hour_cos",
    "is_plant_2",
]
TARGET_COLUMN = "AC_POWER"


def chronological_split(df: pd.DataFrame, train_frac=0.7, val_frac=0.15):
    """Split each plant's series chronologically (not randomly), then
    concatenate, so no future reading ever appears in the training set."""
    train_parts, val_parts, test_parts = [], [], []
    for pid, group in df.groupby("plant_id"):
        group = group.sort_values("dt")
        n = len(group)
        n_train = int(n * train_frac)
        n_val = int(n * val_frac)
        train_parts.append(group.iloc[:n_train])
        val_parts.append(group.iloc[n_train:n_train + n_val])
        test_parts.append(group.iloc[n_train + n_val:])
    train = pd.concat(train_parts).sort_values("dt").reset_index(drop=True)
    val = pd.concat(val_parts).sort_values("dt").reset_index(drop=True)
    test = pd.concat(test_parts).sort_values("dt").reset_index(drop=True)
    return train, val, test


if __name__ == "__main__":
    df = build_dataset()
    print(f"Built solar dataset: {len(df)} rows (dropped {df.attrs['rows_dropped_cleaning']} in cleaning)")
    print(df[["dt", "plant_id"] + FEATURE_COLUMNS + [TARGET_COLUMN]].head())
    train, val, test = chronological_split(df)
    print(f"train={len(train)} val={len(val)} test={len(test)}")
