"""Sliding-window sequences for next-hour scenario forecasting."""

import numpy as np
import pandas as pd


def make_sequences(
    df: pd.DataFrame,
    features: list[str],
    target: str,
    look_back: int,
) -> tuple[np.ndarray, np.ndarray, pd.DatetimeIndex, np.ndarray]:
    """Build (X, y) windows per station.

    Each sample uses the `look_back` hours ending at t to predict the target
    at t + 1. Windows never cross from one station to another.

    Returns X with shape (n, look_back, n_features), y with shape (n,), the
    timestamp of each target hour, and the station of each sample. The target
    timestamps are what the train/validation/test split is based on.
    """
    X_parts, y_parts, time_parts, station_parts = [], [], [], []
    for station, group in df.sort_values("datetime").groupby("station", sort=True):
        values = group[features].to_numpy(dtype=np.float32)
        labels = group[target].to_numpy()
        n = len(group) - look_back
        if n <= 0:
            continue
        windows = np.lib.stride_tricks.sliding_window_view(values, look_back, axis=0)
        # sliding_window_view puts the window axis last: (n, features, look_back)
        X_parts.append(windows[:n].transpose(0, 2, 1))
        y_parts.append(labels[look_back:])
        time_parts.append(group["datetime"].to_numpy()[look_back:])
        station_parts.append(np.full(n, station))
    return (
        np.concatenate(X_parts),
        np.concatenate(y_parts),
        pd.DatetimeIndex(np.concatenate(time_parts)),
        np.concatenate(station_parts),
    )
