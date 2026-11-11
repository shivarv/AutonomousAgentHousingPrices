"""Candidate construction sites, step 1: screen developable parcels.

1. Land use: MassGIS L3 assessor records whose state use code (first three digits) is
   developable or potentially developable vacant land (DEVELOPABLE_CODES). Undevelopable
   vacant land (132, 392, 442) and tax-exempt land are not used.
2. Parcel polygons: tax parcels only (POLY_TYPE FEE or TAX; rights of way and water dropped).
3. Lot size: GIS polygon area >= MIN_ACRES (assessor LOT_SIZE is missing or unreliable for
   many vacant parcels; it is kept as an attribute).
4. Constraints, in MA State Plane: MassGIS protected and recreational open space (all
   levels of protection), MassDEP wetlands (all wetland types, including open water) and
   FEMA NFHL 100-year flood zones (SFHA_TF = 'T': zones A, AE, AH, AO, VE). For every parcel
   the share of its area in each layer and in their union is computed; parcels with more
   than MAX_CONSTRAINED of their area constrained (union) are dropped, and any remaining
   partial overlap is flagged.
5. MBTA Communities (Section 3A) district: the parcel's interior point lies in a district.

Output: data/processed/site_parcels.parquet (one row per screened parcel, simplified WGS84
GeoJSON boundary) and the parcels table (via pipeline.sites.load).

Run: uv run python -m pipeline.sites.screen
"""

from __future__ import annotations

import json
import logging
import warnings

import geopandas as gpd
import pandas as pd
import pyogrio

from pipeline.clean.parcels import GDB
from pipeline.drops import record_drop
from pipeline.geo import MA_CRS, simplified_geojson
from pipeline.paths import INTERIM_DIR, PROCESSED_DIR, RAW_DIR

log = logging.getLogger("pipeline.sites.screen")

# MA DOR property type classification codes (first three digits of USE_CODE)
DEVELOPABLE_CODES = {
    "130": "developable residential land",
    "131": "potentially developable residential land",
    "390": "developable commercial land",
    "391": "potentially developable commercial land",
    "440": "developable industrial land",
    "441": "potentially developable industrial land",
}
TAX_POLY_TYPES = ("FEE", "TAX")
MIN_ACRES = 0.5
MAX_CONSTRAINED = 0.5
PARTIAL_FLAG_MIN = 0.01  # overlaps below 1% of the lot are slivers from boundary mismatch
SQM_PER_ACRE = 4046.8564224
SIMPLIFY_M = 2.0
SITES_FILE = PROCESSED_DIR / "site_parcels.parquet"

CONSTRAINTS = {
    "openspace": (
        f"/vsizip/{RAW_DIR / 'massgis_openspace/openspace.zip'}/OPENSPACE_POLY.shp",
        None,
    ),
    "wetland": (
        f"/vsizip/{RAW_DIR / 'massgis_wetlands/wetlandsdep_poly.zip'}"
        "/wetlandsdep_poly/WETLANDSDEP_POLY.shp",
        None,
    ),
    "flood": (
        f"/vsizip/{RAW_DIR / 'massgis_flood/nfhl.zip'}/FEMA_NFHL_POLY.shp",
        "SFHA_TF = 'T'",
    ),
}
MBTA3A = f"/vsizip/{RAW_DIR / 'massgis_mbta3a/MBTA3A.zip'}/MBTA3A_DISTRICTS_POLY.shp"


def developable_records(assess: pd.DataFrame) -> pd.DataFrame:
    """One row per parcel (loc_id) with a developable use code; values summed over its
    assessor records, use code taken from the record with the largest land value."""
    a = assess[assess.use_code.str[:3].isin(DEVELOPABLE_CODES) & assess.loc_id.notna()].copy()
    a = a.sort_values(["loc_id", "land_val"], ascending=[True, False])
    first = a.drop_duplicates("loc_id").set_index("loc_id")
    sums = a.groupby("loc_id")[["land_val", "bldg_val", "total_val"]].sum(min_count=1)
    out = pd.DataFrame(
        {
            "use_code": first.use_code,
            "fiscal_year": a.groupby("loc_id").fy.max(),
            "assessor_lot_acres": a.groupby("loc_id").lot_size_acres.max(),
        }
    ).join(sums)
    out["use3"] = out.use_code.str[:3]
    return out.reset_index()


def screen_lots(records: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    p = points.drop_duplicates("loc_id")
    df = records.merge(p, on="loc_id", how="inner")
    record_drop("sites", "developable records without a parcel polygon", len(records) - len(df))
    tax = df.poly_type.isin(TAX_POLY_TYPES)
    record_drop("sites", "developable parcels that are rights of way or water", int((~tax).sum()))
    df = df[tax].copy()
    df["lot_size_acres"] = df.area_m2 / SQM_PER_ACRE
    small = df.lot_size_acres < MIN_ACRES
    record_drop("sites", f"developable parcels under {MIN_ACRES} acre", int(small.sum()))
    df = df[~small & df.tract_geoid.notna()]
    return df.reset_index(drop=True)


def parcel_polygons(loc_ids: pd.Series) -> gpd.GeoDataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        g = pyogrio.read_dataframe(GDB, layer="L3_TAXPAR_POLY", columns=["LOC_ID"])
    g = g[g.LOC_ID.isin(set(loc_ids))].to_crs(MA_CRS)
    g["geometry"] = g.geometry.make_valid()
    g = g.dissolve(by="LOC_ID").reset_index().rename(columns={"LOC_ID": "loc_id"})
    return g[["loc_id", "geometry"]]


def read_constraint(path: str, where: str | None, bbox: tuple) -> gpd.GeoDataFrame:
    # the filtered column must be read for the OGR attribute filter to apply
    columns = ["SFHA_TF"] if where else []
    g = pyogrio.read_dataframe(path, columns=columns, where=where, bbox=bbox)
    g = g[g.geometry.notna() & ~g.geometry.is_empty].to_crs(MA_CRS)
    g["geometry"] = g.geometry.make_valid()
    return g[["geometry"]]


def overlap_shares(parcels: gpd.GeoDataFrame, layers: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    """Share of each parcel's area inside each constraint layer and inside their union
    (overlapping constraint polygons are dissolved per parcel, so nothing is counted twice)."""
    area = parcels.set_index("loc_id").geometry.area
    pieces = []
    out = pd.DataFrame(index=area.index)
    for name, layer in layers.items():
        hit = gpd.sjoin(parcels, layer, how="inner", predicate="intersects")
        cand = parcels[parcels.loc_id.isin(hit.loc_id)]
        inter = gpd.overlay(cand, layer, how="intersection", keep_geom_type=True)
        inter = inter[["loc_id", "geometry"]]
        pieces.append(inter)
        per = inter.dissolve(by="loc_id").geometry.area
        out[f"{name}_overlap"] = (per / area).reindex(area.index).fillna(0.0).clip(0, 1)
        log.info("%s: %d parcels touched", name, int((out[f"{name}_overlap"] > 0).sum()))
    allp = gpd.GeoDataFrame(pd.concat(pieces, ignore_index=True), crs=MA_CRS)
    union = allp.dissolve(by="loc_id").geometry.area
    out["constrained_share"] = (union / area).reindex(area.index).fillna(0.0).clip(0, 1)
    return out.reset_index()


def in_mbta3a(points_xy: pd.DataFrame) -> pd.Series:
    d = pyogrio.read_dataframe(MBTA3A, columns=["MUNI"]).to_crs(MA_CRS)
    pts = gpd.GeoDataFrame(
        points_xy[["loc_id"]],
        geometry=gpd.points_from_xy(points_xy.x, points_xy.y),
        crs=MA_CRS,
    )
    j = gpd.sjoin(pts, d, how="left", predicate="within")
    return j.groupby("loc_id").index_right.apply(lambda s: s.notna().any())


def flags_for(row: pd.Series) -> list[str]:
    labels = {
        "openspace_overlap": "open space",
        "wetland_overlap": "wetlands",
        "flood_overlap": "FEMA 100-year flood zone",
    }
    return [
        f"partly in {label} ({row[col]:.0%} of lot)"
        for col, label in labels.items()
        if row[col] >= PARTIAL_FLAG_MIN
    ]


def build() -> pd.DataFrame:
    assess = pd.read_parquet(INTERIM_DIR / "parcel_assess.parquet")
    points = pd.read_parquet(INTERIM_DIR / "parcel_points.parquet")
    lots = screen_lots(developable_records(assess), points)
    log.info("lots >= %.1f acre with developable codes: %d", MIN_ACRES, len(lots))
    polys = parcel_polygons(lots.loc_id)
    bbox = tuple(polys.total_bounds)  # layers are in MA State Plane too
    layers = {
        name: read_constraint(path, where, bbox) for name, (path, where) in CONSTRAINTS.items()
    }
    for name, layer in layers.items():
        log.info("%s: %d constraint polygons", name, len(layer))
        if layer.empty:
            raise RuntimeError(f"constraint layer '{name}' read no polygons")
    shares = overlap_shares(polys, layers)
    df = lots.merge(shares, on="loc_id", how="inner")
    blocked = df.constrained_share > MAX_CONSTRAINED
    record_drop(
        "sites",
        f"parcels with more than {MAX_CONSTRAINED:.0%} of their area in open space, wetlands "
        "or FEMA 100-year flood zones",
        int(blocked.sum()),
    )
    df = df[~blocked].copy()
    df["in_mbta3a_district"] = df.loc_id.map(in_mbta3a(df)).fillna(False).astype(bool)
    df["site_flags"] = df.apply(flags_for, axis=1)
    df["use_description"] = df.use3.map(DEVELOPABLE_CODES)
    geo = polys[polys.loc_id.isin(df.loc_id)].set_index("loc_id")
    geo["boundary"] = simplified_geojson(geo, SIMPLIFY_M).apply(json.dumps)
    df = df.merge(geo[["boundary"]], left_on="loc_id", right_index=True)
    log.info(
        "screened sites: %d (%d flagged partial overlap, %d in 3A districts)",
        len(df),
        int(df.site_flags.str.len().gt(0).sum()),
        int(df.in_mbta3a_district.sum()),
    )
    return df.reset_index(drop=True)


def run() -> None:
    build().to_parquet(SITES_FILE)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
