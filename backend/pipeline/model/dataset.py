"""Residential parcel dataset for the home-value model, and its train/validation/test split.

Rows: assessor records with a residential use code (RESIDENTIAL_CODES, first three digits of
the MA DOR use code), a building value and total assessed value >= MIN_VALUE, located on a
parcel inside a Massachusetts tract. Target: TOTAL_VAL (assessed value).

Split: 70/15/15, stratified by county. Records are split by parcel (LOC_ID), so condo units
of one building never sit on both sides. The split is written once to
data/processed/model/split.parquet and reused on every later run; the test split is only for
the final evaluation.

Run: uv run python -m pipeline.model.dataset
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from pipeline.drops import record_drop
from pipeline.paths import INTERIM_DIR, PROCESSED_DIR

log = logging.getLogger("pipeline.model.dataset")

MODEL_DIR = PROCESSED_DIR / "model"
SPLIT_FILE = MODEL_DIR / "split.parquet"
DATASET_FILE = MODEL_DIR / "residential.parquet"
SEED = 20261110
FRACTIONS = {"train": 0.70, "validation": 0.15, "test": 0.15}
MIN_VALUE = 10_000
# MA DOR use codes: 101 single family, 102 condominium, 103 mobile home, 104 two-family,
# 105 three-family, 109 multiple houses on one parcel, 111 apartments 4-8 units,
# 112 apartments > 8 units.
RESIDENTIAL_CODES = ("101", "102", "103", "104", "105", "109", "111", "112")


def residential(assess: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    a = assess.copy()
    a["use3"] = a.use_code.str[:3]
    keep = a.use3.isin(RESIDENTIAL_CODES)
    a = a[keep]
    low = (a.total_val.fillna(0) < MIN_VALUE) | (a.bldg_val.fillna(0) <= 0)
    record_drop(
        "model_dataset",
        f"residential records with total value < {MIN_VALUE} or no building value",
        int(low.sum()),
    )
    a = a[~low]
    pts = points.drop_duplicates("loc_id").set_index("loc_id")
    a = a.join(
        pts[["tract_geoid", "municipality_geoid", "county_geoid", "x", "y", "area_m2"]],
        on="loc_id",
    )
    unlocated = a.tract_geoid.isna()
    record_drop(
        "model_dataset", "residential records without a located parcel", int(unlocated.sum())
    )
    return a[~unlocated].reset_index(drop=True)


def make_split(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Assign each parcel (loc_id) to train/validation/test within its county; every record of
    a parcel gets the parcel's split. Returns record_id, loc_id, county_geoid, split."""
    parcels = df.drop_duplicates("loc_id")[["loc_id", "county_geoid"]]
    rng = np.random.default_rng(seed)
    labels = []
    for _, g in parcels.groupby("county_geoid", sort=True):
        n = len(g)
        n_train = int(round(FRACTIONS["train"] * n))
        n_val = int(round(FRACTIONS["validation"] * n))
        lab = np.array(
            ["train"] * n_train + ["validation"] * n_val + ["test"] * (n - n_train - n_val)
        )
        rng.shuffle(lab)
        labels.append(pd.Series(lab, index=g.loc_id.values))
    by_parcel = pd.concat(labels)
    out = df[["record_id", "loc_id", "county_geoid"]].copy()
    out["split"] = out.loc_id.map(by_parcel)
    return out


def load_or_create_split(df: pd.DataFrame) -> pd.DataFrame:
    """The split is created once. Later runs reuse it; records not in the saved split (new
    data) are left out rather than re-splitting."""
    if SPLIT_FILE.exists():
        split = pd.read_parquet(SPLIT_FILE)
        log.info("reusing saved split (%d records)", len(split))
        return split
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    split = make_split(df)
    split.to_parquet(SPLIT_FILE)
    log.info("created split: %s", split.split.value_counts().to_dict())
    return split


def run() -> pd.DataFrame:
    assess = pd.read_parquet(INTERIM_DIR / "parcel_assess.parquet")
    points = pd.read_parquet(INTERIM_DIR / "parcel_points.parquet")
    df = residential(assess, points)
    split = load_or_create_split(df)
    df = df.merge(split[["record_id", "split"]], on="record_id", how="inner")
    df.to_parquet(DATASET_FILE)
    log.info("residential dataset: %d records, %s", len(df), df.split.value_counts().to_dict())
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
