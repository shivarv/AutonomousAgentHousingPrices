"""ACS 5-year tract variables -> tract metrics (data/processed/metrics_acs.parquet).

Census API annotation values (large negative numbers) mean the estimate is unavailable or
suppressed; they become NULL values with a flag, never zeros. MOEs of derived sums use the
Census approximation sqrt(sum of squared MOEs).

Run: uv run python -m pipeline.clean.acs
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd

from pipeline.clean.metrics_common import long_metric, safe_ratio
from pipeline.download.acs import ACS_YEAR
from pipeline.paths import PROCESSED_DIR, RAW_DIR

log = logging.getLogger("pipeline.clean.acs")
SOURCE = "acs5"


def load_raw(year: int = ACS_YEAR) -> pd.DataFrame:
    table = json.loads((RAW_DIR / f"acs/acs5_{year}_tracts_ma.json").read_text())
    df = pd.DataFrame(table[1:], columns=table[0])
    df["geoid"] = df.state + df.county + df.tract
    for c in df.columns:
        if c[:1] == "B":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _clean(df: pd.DataFrame, var: str) -> tuple[pd.Series, pd.Series, pd.Series]:
    est, moe = df[f"{var}E"], df[f"{var}M"]
    bad = est < 0
    flag = pd.Series(np.where(bad, "suppressed or unavailable in ACS (annotation code)", None))
    est = est.where(~bad)
    moe = moe.where(moe >= 0)
    return est, moe, flag


def _sum(df: pd.DataFrame, vars_: list[str]) -> tuple[pd.Series, pd.Series]:
    est = sum(df[f"{v}E"].where(df[f"{v}E"] >= 0) for v in vars_)
    moe = np.sqrt(sum(df[f"{v}M"].where(df[f"{v}M"] >= 0) ** 2 for v in vars_))
    return est, moe


def build(year: int = ACS_YEAR) -> pd.DataFrame:
    df = load_raw(year)
    g = df.geoid
    out = []

    direct = {
        "population": "B01003_001",
        "households": "B11001_001",
        "median_household_income": "B19013_001",
        "housing_units": "B25001_001",
        "occupied_units": "B25002_002",
        "vacant_units": "B25002_003",
        "vacant_for_rent": "B25004_002",
        "renter_households": "B25003_003",
        "owner_households": "B25003_002",
        "median_gross_rent": "B25064_001",
        "median_home_value": "B25077_001",
        "poverty_universe": "B17001_001",
        "poverty_count": "B17001_002",
    }
    for metric, var in direct.items():
        est, moe, flag = _clean(df, var)
        out.append(long_metric(g, metric, year, est, SOURCE, moe=moe, flag=flag))

    for_sale, for_sale_moe = _sum(df, ["B25004_004"])
    out.append(long_metric(g, "vacant_for_sale", year, for_sale, SOURCE, moe=for_sale_moe))

    over, over_moe = _sum(
        df, ["B25014_005", "B25014_006", "B25014_007", "B25014_011", "B25014_012", "B25014_013"]
    )
    out.append(long_metric(g, "overcrowded_households", year, over, SOURCE, moe=over_moe))
    out.append(long_metric(g, "overcrowding_rate", year, safe_ratio(over, df.B25014_001E), SOURCE))

    out.append(
        long_metric(g, "poverty_rate", year, safe_ratio(df.B17001_002E, df.B17001_001E), SOURCE)
    )

    # rent burden: universe excludes households whose burden is not computed
    universe = df.B25070_001E - df.B25070_011E
    burdened, burdened_moe = _sum(df, ["B25070_007", "B25070_008", "B25070_009", "B25070_010"])
    severe, severe_moe = _sum(df, ["B25070_010"])
    out.append(long_metric(g, "rent_burden_universe", year, universe, SOURCE))
    out.append(long_metric(g, "rent_burdened_households", year, burdened, SOURCE, moe=burdened_moe))
    out.append(
        long_metric(g, "severely_rent_burdened_households", year, severe, SOURCE, moe=severe_moe)
    )
    out.append(long_metric(g, "rent_burden_share", year, safe_ratio(burdened, universe), SOURCE))
    out.append(
        long_metric(g, "severe_rent_burden_share", year, safe_ratio(severe, universe), SOURCE)
    )
    out.append(
        long_metric(g, "vacancy_rate", year, safe_ratio(df.B25002_003E, df.B25001_001E), SOURCE)
    )
    result = pd.concat(out, ignore_index=True)
    log.info("ACS metrics: %d rows, %d null values", len(result), int(result.value.isna().sum()))
    return result


def run() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    build().to_parquet(PROCESSED_DIR / "metrics_acs.parquet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
