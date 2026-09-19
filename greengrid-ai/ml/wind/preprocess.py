"""
GreenGrid AI — Wind preprocessing

Source data: Kaggle "Wind Turbine SCADA Dataset" (berkerisen), T1.csv,
one turbine, 10-minute resolution, full year 2018 (50,530 rows).

Target: LV ActivePower (kW) — actual active power output.

Features used: Wind Speed (m/s), Wind Direction (as sin/cos, since 359
degrees is "close to" 0 degrees), Theoretical_Power_Curve (KWh).

Note on Theoretical_Power_Curve: this column is the manufacturer's
expected output for a given wind speed (a fixed lookup curve) - it is a
deterministic function of wind speed, not something derived from the
*actual* measured active power. It does not leak future/target
information, so it is safe to use as an input feature. It's also useful
signal: the gap between it and the real output is exactly what a
predictive-maintenance / anomaly-detection feature would look at later.
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "wind"


def build_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "T1.csv")
    df["dt"] = pd.to_datetime(df["Date/Time"], format="%d %m %Y %H:%M")
    df = df.rename(columns={
        "LV ActivePower (kW)": "active_power",
        "Wind Speed (m/s)": "wind_speed",
        "Theoretical_Power_Curve (KWh)": "theoretical_power",
        "Wind Direction (°)": "wind_direction",
    })

    before = len(df)
    df = df.dropna(subset=["active_power", "wind_speed", "theoretical_power", "wind_direction"])
    # Active power can't be physically negative; the ~57 tiny-negative rows
    # in this dataset are sensor noise around zero wind, so clip rather than drop.
    df["active_power"] = df["active_power"].clip(lower=0)
    dropped = before - len(df)

    df["dir_sin"] = np.sin(2 * np.pi * df["wind_direction"] / 360)
    df["dir_cos"] = np.cos(2 * np.pi * df["wind_direction"] / 360)

    df = df.sort_values("dt").reset_index(drop=True)
    df.attrs["rows_dropped_cleaning"] = dropped
    return df


FEATURE_COLUMNS = ["wind_speed", "theoretical_power", "dir_sin", "dir_cos"]
TARGET_COLUMN = "active_power"


def chronological_split(df: pd.DataFrame, train_frac=0.7, val_frac=0.15):
    df = df.sort_values("dt").reset_index(drop=True)
    n = len(df)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    train = df.iloc[:n_train].reset_index(drop=True)
    val = df.iloc[n_train:n_train + n_val].reset_index(drop=True)
    test = df.iloc[n_train + n_val:].reset_index(drop=True)
    return train, val, test


if __name__ == "__main__":
    df = build_dataset()
    print(f"Built wind dataset: {len(df)} rows (dropped {df.attrs['rows_dropped_cleaning']} in cleaning)")
    train, val, test = chronological_split(df)
    print(f"train={len(train)} val={len(val)} test={len(test)}")
    print(f"Date range: {df['dt'].min()} to {df['dt'].max()}")
