import numpy as np
import pandas as pd
import pytest

from cdmx_air.cleaning import cap_outliers, interpolate_short_gaps, iqr_upper_bounds
from cdmx_air.clustering import name_scenarios, transition_matrix
from cdmx_air.data import replace_missing_codes
from cdmx_air.sequences import make_sequences


def hourly_frame(stations=("A", "B"), hours=6):
    times = pd.date_range("2025-01-01", periods=hours, freq="h")
    return pd.DataFrame(
        [(t, s) for s in stations for t in times], columns=["datetime", "station"]
    )


def test_replace_missing_codes():
    df = hourly_frame(hours=2)
    df["O3"] = [10, -99, -999, 5]
    out = replace_missing_codes(df)
    assert out["O3"].isna().sum() == 2


def test_interpolation_stays_within_station():
    df = hourly_frame(hours=3)
    # Station A: 0, NaN, 10. Station B: 100, 100, 100.
    df["O3"] = [0, np.nan, 10, 100, 100, 100]
    # Interleave rows by time, as an outer merge produces.
    df = df.sort_values(["datetime", "station"])
    out = interpolate_short_gaps(df, ["O3"])
    value = out.loc[(out["station"] == "A") & (out["datetime"] == "2025-01-01 01:00"), "O3"]
    assert value.item() == pytest.approx(5)


def test_interpolation_respects_gap_limit():
    df = hourly_frame(stations=("A",), hours=6)
    df["O3"] = [0, np.nan, np.nan, np.nan, np.nan, 50]
    out = interpolate_short_gaps(df, ["O3"], limit=3)
    assert out["O3"].isna().sum() == 1


def test_capping_uses_given_bounds():
    df = pd.DataFrame({"O3": [1.0, 2.0, 3.0, 100.0]})
    bounds = iqr_upper_bounds(df, ["O3"])
    out = cap_outliers(df, bounds)
    assert out["O3"].max() == pytest.approx(bounds["O3"])
    assert out["O3"].iloc[0] == 1.0


def test_sequences_do_not_cross_stations():
    df = hourly_frame(hours=5)
    df["x"] = np.where(df["station"] == "A", 1.0, 2.0)
    df["y"] = np.where(df["station"] == "A", 0, 1)
    X, y, times, stations = make_sequences(df, ["x"], "y", look_back=3)
    assert X.shape == (4, 3, 1)
    for window, label, station in zip(X, y, stations, strict=True):
        expected = 1.0 if station == "A" else 2.0
        assert np.all(window == expected)
        assert label == (0 if station == "A" else 1)
    assert times.min() == pd.Timestamp("2025-01-01 03:00")


def test_sequence_target_is_next_hour():
    df = hourly_frame(stations=("A",), hours=5)
    df["x"] = np.arange(5, dtype=float)
    df["y"] = np.arange(5)
    X, y, _, _ = make_sequences(df, ["x"], "y", look_back=2)
    np.testing.assert_array_equal(X[0, :, 0], [0, 1])
    assert y[0] == 2


def test_name_scenarios_is_label_independent():
    centroids = pd.DataFrame(
        {
            "CO": [2.0, -1.0, 0.0, -0.5],
            "NO": [2.0, -1.0, 0.0, -0.5],
            "NO2": [2.0, -1.0, 0.0, -0.5],
            "PM10": [2.0, -1.0, 0.0, -0.5],
            "PM25": [2.0, -1.0, 0.0, -0.5],
            "O3": [-0.5, -0.5, 0.0, 2.0],
            "SO2": [0.5, -0.5, 0.0, 0.0],
        },
        index=[3, 1, 0, 2],
    )
    names = name_scenarios(centroids)
    assert names == {
        3: "High pollution",
        1: "Clean air",
        0: "Moderate urban",
        2: "Ozone peak",
    }


def test_transition_matrix_within_station():
    df = hourly_frame(hours=2)
    df["scenario"] = ["a", "a", "b", "b"]
    matrix = transition_matrix(df)
    assert matrix.loc["a", "a"] == 100
    assert matrix.loc["b", "b"] == 100
