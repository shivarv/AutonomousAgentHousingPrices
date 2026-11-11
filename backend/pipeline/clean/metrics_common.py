"""Helpers for building long-format tract metric tables:
columns tract_geoid, metric, year, value, moe, source_key, is_estimate, method, flag."""

from __future__ import annotations

import numpy as np
import pandas as pd

METRIC_COLUMNS = [
    "tract_geoid",
    "metric",
    "year",
    "value",
    "moe",
    "source_key",
    "is_estimate",
    "method",
    "flag",
]


def long_metric(
    geoids: pd.Series,
    metric: str,
    year: int,
    value: pd.Series,
    source_key: str,
    *,
    moe: pd.Series | None = None,
    flag: pd.Series | None = None,
    is_estimate: bool = False,
    method: str | None = None,
) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "tract_geoid": geoids.values,
            "metric": metric,
            "year": year,
            "value": pd.to_numeric(value, errors="coerce").astype(float).values,
            "moe": (
                pd.to_numeric(moe, errors="coerce").astype(float).values
                if moe is not None
                else np.nan
            ),
            "source_key": source_key,
            "is_estimate": is_estimate,
            "method": method,
            "flag": flag.values if flag is not None else None,
        }
    )
    return df[METRIC_COLUMNS]


def safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """num/den, NaN where the denominator is 0 or missing (never silently 0)."""
    den = den.astype(float)
    return (num.astype(float) / den.where(den > 0)).astype(float)
