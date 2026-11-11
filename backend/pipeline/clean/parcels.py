"""MassGIS Level 3 parcels: assessor attributes and parcel locations.

Outputs (data/interim/, git-ignored):
- parcel_assess.parquet: one row per assessor record (record_id = town:PROP_ID:n). Owner
  names/addresses and site addresses are never read. lot_size_acres = LOT_SIZE converted from
  LOT_UNITS (A acres, S square feet).
- parcel_points.parquet: one row per tax parcel polygon (LOC_ID) with area, interior point
  (MA State Plane x/y and WGS84 lat/lon) and the tract, town and county containing the point.

Run: uv run python -m pipeline.clean.parcels
"""

from __future__ import annotations

import logging
import warnings

import geopandas as gpd
import pandas as pd
import pyogrio

from pipeline.drops import record_drop
from pipeline.geo import MA_CRS, WGS84
from pipeline.paths import INTERIM_DIR, RAW_DIR

log = logging.getLogger("pipeline.clean.parcels")

GDB = f"/vsizip/{RAW_DIR / 'massgis_parcels/MassGIS_L3_Parcels_gdb.zip'}/MassGIS_L3_Parcels.gdb"
SQFT_PER_ACRE = 43_560.0
ASSESS_COLUMNS = [
    "PROP_ID",
    "LOC_ID",
    "TOWN_ID",
    "USE_CODE",
    "FY",
    "TOTAL_VAL",
    "LAND_VAL",
    "BLDG_VAL",
    "OTHER_VAL",
    "LOT_SIZE",
    "LOT_UNITS",
    "YEAR_BUILT",
    "BLD_AREA",
    "RES_AREA",
    "UNITS",
    "NUM_ROOMS",
    "STORIES",
    "STYLE",
]


def lot_size_acres(size: pd.Series, units: pd.Series) -> pd.Series:
    """LOT_SIZE in acres: units 'A' = acres, 'S' = square feet; anything else -> NaN."""
    size = pd.to_numeric(size, errors="coerce")
    u = units.fillna("").str.upper().str.strip()
    return size.where(u == "A", size / SQFT_PER_ACRE).where(u.isin(["A", "S"]))


def stories_number(s: pd.Series) -> pd.Series:
    """'2', '1 1/2', '2.5' -> float; unparseable -> NaN."""
    t = s.fillna("").astype(str).str.strip()
    frac = t.str.extract(r"^(\d+)\s+1/2$")[0]
    out = pd.to_numeric(t, errors="coerce")
    return out.where(frac.isna(), pd.to_numeric(frac, errors="coerce") + 0.5)


def clean_assess() -> pd.DataFrame:
    a = pyogrio.read_dataframe(
        GDB, layer="L3_ASSESS", columns=ASSESS_COLUMNS, read_geometry=False, use_arrow=True
    )
    a.columns = [c.lower() for c in a.columns]
    a["lot_size_acres"] = lot_size_acres(a.lot_size, a.lot_units)
    a["stories_num"] = stories_number(a.stories)
    a["use_code"] = a.use_code.fillna("").astype(str).str.strip()
    # PROP_ID is unique only within a town, and a few towns list one PROP_ID twice (e.g. a
    # taxable and an exempt line), so only fully identical rows are dropped.
    dup = a.duplicated(keep="first")
    record_drop("parcels", "assessor rows identical to another row", int(dup.sum()))
    a = a[~dup].drop(columns=["lot_size", "lot_units", "stories"]).reset_index(drop=True)
    a.insert(0, "record_id", a.town_id.astype(str) + ":" + a.prop_id.astype(str))
    a["record_id"] = a.record_id + ":" + a.groupby("record_id").cumcount().astype(str)
    return a


def clean_points() -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        # non-Arrow reader: GDAL linearises the few curved parcel boundaries
        g = pyogrio.read_dataframe(
            GDB, layer="L3_TAXPAR_POLY", columns=["LOC_ID", "POLY_TYPE", "TOWN_ID"]
        )
    g = g.to_crs(MA_CRS)
    missing = g.LOC_ID.isna()
    record_drop("parcels", "parcel polygons without LOC_ID", int(missing.sum()))
    g = g[~missing]
    pts = gpd.GeoDataFrame(
        {"loc_id": g.LOC_ID.values, "poly_type": g.POLY_TYPE.values, "town_id": g.TOWN_ID.values},
        geometry=g.geometry.representative_point().values,
        crs=MA_CRS,
    )
    pts["area_m2"] = g.geometry.area.values
    tracts = gpd.read_parquet(INTERIM_DIR / "tracts_geom.parquet").to_crs(MA_CRS)
    towns = gpd.read_parquet(INTERIM_DIR / "municipalities_geom.parquet").to_crs(MA_CRS)
    j = gpd.sjoin(pts, tracts[["geoid", "geometry"]], how="left", predicate="within")
    j = (
        j[~j.index.duplicated()]
        .rename(columns={"geoid": "tract_geoid"})
        .drop(columns="index_right")
    )
    j = gpd.sjoin(j, towns[["geoid", "geometry"]], how="left", predicate="within")
    j = (
        j[~j.index.duplicated()]
        .rename(columns={"geoid": "municipality_geoid"})
        .drop(columns="index_right")
    )
    record_drop(
        "parcels",
        "parcel points outside every MA tract (kept, tract NULL)",
        int(j.tract_geoid.isna().sum()),
    )
    j["county_geoid"] = j.tract_geoid.str[:5]
    wgs = j.geometry.to_crs(WGS84)
    out = pd.DataFrame(j.drop(columns="geometry"))
    out["x"], out["y"] = j.geometry.x.values, j.geometry.y.values
    out["lat"], out["lon"] = wgs.y.round(6).values, wgs.x.round(6).values
    return out.reset_index(drop=True)


def run() -> None:
    a = clean_assess()
    a.to_parquet(INTERIM_DIR / "parcel_assess.parquet")
    log.info("assessor records: %d", len(a))
    p = clean_points()
    p.to_parquet(INTERIM_DIR / "parcel_points.parquet")
    log.info("parcel points: %d (%d without tract)", len(p), int(p.tract_geoid.isna().sum()))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
