"""Data-quality diagnostics, outlier capping and missing-value imputation.

Functions that learn something from the data (capping bounds, the MICE
imputer) are split into fit / apply steps so they can be fitted on the
training period only and reused on validation and test data.
"""

import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

from .config import RANDOM_STATE


def quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Data type, missing count and missing percentage per column."""
    return pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "missing": df.isna().sum(),
            "missing_pct": (df.isna().mean() * 100).round(2),
        }
    ).sort_values("missing_pct", ascending=False)


def missing_by_station(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Percentage of missing values per station (rows) and pollutant (columns)."""
    return df[columns].isna().groupby(df["station"]).mean() * 100


def iqr_upper_bounds(df: pd.DataFrame, columns: list[str], k: float = 1.5) -> pd.Series:
    """Upper outlier fence Q3 + k * IQR for each column."""
    q1 = df[columns].quantile(0.25)
    q3 = df[columns].quantile(0.75)
    return q3 + k * (q3 - q1)


def outlier_report(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Count of readings above the IQR upper fence, per pollutant."""
    bounds = iqr_upper_bounds(df, columns)
    above = df[columns].gt(bounds)
    return pd.DataFrame(
        {
            "q1": df[columns].quantile(0.25),
            "q3": df[columns].quantile(0.75),
            "upper_fence": bounds,
            "max": df[columns].max(),
            "outliers": above.sum(),
            "outliers_pct": (above.mean() * 100).round(2),
        }
    ).round(2).sort_values("outliers_pct", ascending=False)


def cap_outliers(df: pd.DataFrame, bounds: pd.Series) -> pd.DataFrame:
    """Clip each column at its upper bound (capping keeps the extreme hours)."""
    df = df.copy()
    df[bounds.index] = df[bounds.index].clip(upper=bounds, axis=1)
    return df


def interpolate_short_gaps(df: pd.DataFrame, columns: list[str], limit: int = 3) -> pd.DataFrame:
    """Linearly interpolate gaps of up to `limit` hours, within each station.

    Rows must be one hourly series per station; interpolating across stations
    would mix readings from different places.
    """
    df = df.sort_values(["station", "datetime"]).copy()
    df[columns] = df.groupby("station")[columns].transform(
        lambda s: s.interpolate(method="linear", limit=limit, limit_area="inside")
    )
    return df


def fit_imputer(df: pd.DataFrame, columns: list[str]) -> IterativeImputer:
    """Fit a MICE imputer that estimates each pollutant from the others."""
    imputer = IterativeImputer(max_iter=10, random_state=RANDOM_STATE, min_value=0)
    return imputer.fit(df[columns])


def apply_imputer(df: pd.DataFrame, columns: list[str], imputer: IterativeImputer) -> pd.DataFrame:
    df = df.copy()
    df[columns] = imputer.transform(df[columns])
    return df
