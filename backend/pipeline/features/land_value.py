"""Assessed land value per square foot by tract (land-cost context for candidate sites).

From MassGIS L3 assessor records: LAND_VAL / lot size in square feet, per parcel, for taxable
parcels with a usable lot size. Condominium units (use code 102) are excluded because their
land value is a unit share while the lot size, where recorded, is the whole lot; tax-exempt
parcels (9xx) are excluded because many towns record nominal land values for them.
A parcel with several assessor records (e.g. split taxable/exempt lines) counts once, with
its records' land values summed.

Per tract: the median of parcel values (robust to outliers), the number of parcels used, and
a flag when fewer than MIN_PARCELS parcels support it. Tracts with no usable parcel stay NULL.

Run: uv run python -m pipeline.features.land_value   (then pipeline.load)
"""

from __future__ import annotations

import logging

import pandas as pd

from pipeline.clean.metrics_common import METRIC_COLUMNS, long_metric
from pipeline.drops import record_drop
from pipeline.paths import INTERIM_DIR, PROCESSED_DIR

log = logging.getLogger("pipeline.features.land_value")

SQFT_PER_ACRE = 43_560.0
MIN_PARCELS = 10
MIN_ACRES = 0.01
MAX_ACRES = 500.0
SOURCE = "massgis_parcels"
METHOD = (
    "median over the tract's taxable non-condominium parcels of assessed LAND_VAL / lot size "
    "(sq ft), MassGIS L3 parcels; lots 0.01-500 acres with land value > 0"
)
FEW_FLAG = f"fewer than {MIN_PARCELS} parcels support this median"


def parcel_land_values(assess: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    """One row per parcel (loc_id): tract_geoid, land_val, acres, value_per_sqft, fy."""
    a = assess[~assess.use_code.str[:3].eq("102") & ~assess.use_code.str.startswith("9")]
    a = a[a.land_val.fillna(0) > 0]
    per_parcel = a.groupby("loc_id").agg(
        land_val=("land_val", "sum"),
        acres=("lot_size_acres", "max"),
        fy=("fy", "max"),
    )
    ok = per_parcel.acres.between(MIN_ACRES, MAX_ACRES)
    record_drop(
        "land_value",
        f"parcels with lot size missing or outside {MIN_ACRES}-{MAX_ACRES} acres",
        int((~ok).sum()),
    )
    p = per_parcel[ok].join(points.drop_duplicates("loc_id").set_index("loc_id").tract_geoid)
    p = p.dropna(subset=["tract_geoid"])
    p["value_per_sqft"] = p.land_val / (p.acres * SQFT_PER_ACRE)
    return p.reset_index()


def tract_land_values(parcels: pd.DataFrame, tract_ids: pd.Series) -> pd.DataFrame:
    g = parcels.groupby("tract_geoid")
    out = pd.DataFrame(
        {"median": g.value_per_sqft.median(), "n": g.size(), "fy": g.fy.median()}
    ).reindex(tract_ids)
    out["n"] = out.n.fillna(0).astype(int)
    out["flag"] = (out.n.between(1, MIN_PARCELS - 1)).map({True: FEW_FLAG, False: None})
    return out


def build() -> pd.DataFrame:
    assess = pd.read_parquet(INTERIM_DIR / "parcel_assess.parquet")
    points = pd.read_parquet(INTERIM_DIR / "parcel_points.parquet")
    tracts = pd.read_parquet(PROCESSED_DIR / "tracts.parquet").geoid
    parcels = parcel_land_values(assess, points)
    t = tract_land_values(parcels, tracts)
    year = int(parcels.fy.mode().iloc[0])
    geoids = pd.Series(t.index)
    out = pd.concat(
        [
            long_metric(
                geoids,
                "land_value_per_sqft",
                year,
                t["median"].reset_index(drop=True),
                SOURCE,
                flag=t.flag.reset_index(drop=True),
                method=METHOD,
            ),
            long_metric(
                geoids,
                "land_value_parcels",
                year,
                t.n.reset_index(drop=True),
                SOURCE,
                method="number of parcels behind land_value_per_sqft",
            ),
        ],
        ignore_index=True,
    )[METRIC_COLUMNS]
    log.info(
        "land value: %d parcels, %d tracts with a value, %d flagged",
        len(parcels),
        int(t["median"].notna().sum()),
        int(t.flag.notna().sum()),
    )
    return out


def run() -> None:
    build().to_parquet(PROCESSED_DIR / "metrics_land.parquet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
