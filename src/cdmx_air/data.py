"""Loading SEDEMA hourly pollutant files into a single long-format table."""

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from .config import MISSING_CODES, POLLUTANT_FILES, RAW_DATA_DIR

INDEX_COLUMNS = ["datetime", "station"]


def read_pollutant_file(path: Path, pollutant: str) -> pd.DataFrame:
    """Read one SEDEMA .xls file (wide: one column per station) as long format.

    SEDEMA reports the hour as 1-24 (hour ending), so hour 24 maps to 00:00
    of the following day.
    """
    wide = pd.read_excel(path)
    wide = wide.rename(columns={wide.columns[0]: "date", wide.columns[1]: "hour"})
    wide["datetime"] = pd.to_datetime(wide["date"]) + pd.to_timedelta(wide["hour"], unit="h")
    long = wide.drop(columns=["date", "hour"]).melt(
        id_vars="datetime", var_name="station", value_name=pollutant
    )
    long[pollutant] = long[pollutant].astype(float)
    return long


def load_year(year: int, data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Merge every pollutant file of one year into a single table."""
    merged = None
    for pollutant in POLLUTANT_FILES:
        path = data_dir / f"{year}{pollutant}.xls"
        if not path.exists():
            raise FileNotFoundError(f"Missing {path.name}. See data/README.md.")
        long = read_pollutant_file(path, pollutant)
        merged = long if merged is None else merged.merge(long, on=INDEX_COLUMNS, how="outer")
    return merged


def load_years(years: Iterable[int], data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load several years, with missing-value codes already converted to NaN."""
    df = pd.concat([load_year(year, data_dir) for year in years], ignore_index=True)
    df = replace_missing_codes(df)
    return df.sort_values(["station", "datetime"]).reset_index(drop=True)


def replace_missing_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Replace SEDEMA sentinel values (-99, -999) with NaN."""
    df = df.copy()
    value_columns = df.columns.difference(INDEX_COLUMNS)
    df[value_columns] = df[value_columns].replace(MISSING_CODES, np.nan)
    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add hour, weekday, month and weekend columns derived from `datetime`."""
    df = df.copy()
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.dayofweek  # 0 = Monday
    df["month"] = df["datetime"].dt.month
    df["is_weekend"] = df["weekday"] >= 5
    return df
