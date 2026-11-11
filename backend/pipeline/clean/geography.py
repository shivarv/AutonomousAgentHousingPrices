"""Clean boundaries into analysis-ready tables (data/processed/*.parquet).

Outputs: counties, municipalities, cocs, coc_municipalities, boston_neighbourhoods,
neighbourhood_tracts, tracts, tract_municipalities. Also writes the full-resolution tract,
municipality, county, CoC and neighbourhood polygons (MA_CRS) to data/interim/ as GeoParquet
for later spatial work.

Run: uv run python -m pipeline.clean.geography
"""

from __future__ import annotations

import json
import logging
import zipfile

import geopandas as gpd
import pandas as pd

from pipeline.drops import record_drop, reset
from pipeline.geo import MA_CRS, centroids_wgs84, overlay_shares, simplified_geojson
from pipeline.paths import INTERIM_DIR, MA_STATE_FIPS, PROCESSED_DIR, RAW_DIR

log = logging.getLogger("pipeline.clean.geography")
BOSTON_GEOID = "2502507000"


def _read(path, **kw) -> gpd.GeoDataFrame:
    return gpd.read_file(path, **kw).to_crs(MA_CRS)


def load_counties() -> gpd.GeoDataFrame:
    c = _read(RAW_DIR / "tiger/tl_2026_us_county.zip", where=f"STATEFP = '{MA_STATE_FIPS}'")
    return c.rename(columns={"GEOID": "geoid", "NAMELSAD": "name"})


def load_municipalities() -> gpd.GeoDataFrame:
    m = _read(RAW_DIR / "tiger/tl_2026_25_cousub.zip")
    dropped = m[m.COUSUBFP == "00000"]
    record_drop("geography", "county subdivision 'not defined' (water) records", len(dropped))
    m = m[m.COUSUBFP != "00000"].copy()
    m["county_geoid"] = m.STATEFP + m.COUNTYFP
    return m.rename(columns={"GEOID": "geoid", "NAME": "name"})


def load_cocs() -> gpd.GeoDataFrame:
    path = RAW_DIR / "hud_coc/CoC_GIS_State_Shapefile_MA_2025.zip"
    with zipfile.ZipFile(path) as zf:
        shps = sorted(n for n in zf.namelist() if n.endswith(".shp"))
    parts = [gpd.read_file(f"/vsizip/{path}/{s}") for s in shps]
    c = pd.concat([p.to_crs(MA_CRS) for p in parts], ignore_index=True)
    c = c.dissolve(by="COCNUM", aggfunc={"COCNAME": "first"}).reset_index()
    return gpd.GeoDataFrame(
        c.rename(columns={"COCNUM": "coc_number", "COCNAME": "name"}), crs=MA_CRS
    )


def load_neighbourhoods() -> gpd.GeoDataFrame:
    b = _read(RAW_DIR / "boston_neighbourhoods/boston_neighborhood_boundaries.geojson")
    return b[["name", "geometry"]].copy()


def load_tracts() -> gpd.GeoDataFrame:
    t = _read(RAW_DIR / "tiger/tl_2026_25_tract.zip")
    t["county_geoid"] = t.STATEFP + t.COUNTYFP
    return t.rename(columns={"GEOID": "geoid", "NAMELSAD": "name"})


def _primary(shares: pd.DataFrame, key: str, other: str) -> pd.Series:
    best = shares.sort_values("share", ascending=False).drop_duplicates(key)
    return best.set_index(key)[other]


def _nearest(missing: gpd.GeoDataFrame, key: str, polys: gpd.GeoDataFrame, other: str) -> pd.Series:
    joined = gpd.sjoin_nearest(missing[[key, "geometry"]], polys[[other, "geometry"]])
    return joined.drop_duplicates(key).set_index(key)[other]


def run() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    reset("geography")

    counties = load_counties()
    munis = load_municipalities()
    cocs = load_cocs()
    hoods = load_neighbourhoods()
    tracts = load_tracts()
    log.info(
        "counties %d, municipalities %d, cocs %d, neighbourhoods %d, tracts %d",
        len(counties),
        len(munis),
        len(cocs),
        len(hoods),
        len(tracts),
    )

    # tract x municipality and tract x CoC area shares
    tm = overlay_shares(tracts, "geoid", munis.rename(columns={"geoid": "muni"}), "muni")
    tm = tm[tm.share > 0.001]
    tc = overlay_shares(tracts, "geoid", cocs, "coc_number")
    tracts["municipality_geoid"] = tracts.geoid.map(_primary(tm, "geoid", "muni"))
    tracts["coc_number"] = tracts.geoid.map(_primary(tc, "geoid", "coc_number"))
    for col, polys, other in (
        ("municipality_geoid", munis.rename(columns={"geoid": "muni"}), "muni"),
        ("coc_number", cocs, "coc_number"),
    ):
        missing = tracts[tracts[col].isna()]
        if len(missing):
            log.info("%d tracts without %s overlap (water); using nearest", len(missing), col)
            tracts.loc[missing.index, col] = missing.geoid.map(
                _nearest(missing, "geoid", polys, other)
            )

    # municipality x CoC (members)
    mc = overlay_shares(munis, "geoid", cocs, "coc_number")
    mc = mc[mc.share > 0.01]

    # Boston neighbourhoods: tract area shares, for tracts overlapping Boston
    hoods = hoods.reset_index(drop=True)
    hoods["neighbourhood_id"] = hoods.index + 1
    boston_tracts = tracts[tracts.geoid.isin(tm[tm.muni == BOSTON_GEOID].geoid)]
    nt = overlay_shares(boston_tracts, "geoid", hoods, "neighbourhood_id")
    nt = nt[nt.share > 0.01]
    primary_hood = _primary(nt, "geoid", "neighbourhood_id")
    in_boston = tracts.municipality_geoid == BOSTON_GEOID
    tracts["neighbourhood_id"] = pd.NA
    tracts.loc[in_boston, "neighbourhood_id"] = tracts.loc[in_boston, "geoid"].map(primary_hood)

    def finish(gdf: gpd.GeoDataFrame, tol: float, cols: list[str]) -> pd.DataFrame:
        lat, lon = centroids_wgs84(gdf)
        out = pd.DataFrame(gdf[cols]).copy()
        out["centroid_lat"], out["centroid_lon"] = lat.values, lon.values
        # stored as GeoJSON text in parquet; loaded into jsonb
        out["boundary"] = simplified_geojson(gdf, tol).apply(json.dumps).values
        return out

    area_cols = ["ALAND", "AWATER"]
    rename_area = {"ALAND": "land_area_m2", "AWATER": "water_area_m2"}
    finish(counties, 150, ["geoid", "name", *area_cols]).rename(columns=rename_area).to_parquet(
        PROCESSED_DIR / "counties.parquet"
    )
    finish(munis, 50, ["geoid", "name", "county_geoid", *area_cols]).rename(
        columns=rename_area
    ).to_parquet(PROCESSED_DIR / "municipalities.parquet")
    finish(cocs, 150, ["coc_number", "name"]).to_parquet(PROCESSED_DIR / "cocs.parquet")
    finish(hoods, 15, ["neighbourhood_id", "name"]).to_parquet(
        PROCESSED_DIR / "boston_neighbourhoods.parquet"
    )
    t_out = finish(
        tracts,
        20,
        [
            "geoid",
            "name",
            "county_geoid",
            "municipality_geoid",
            "coc_number",
            "neighbourhood_id",
            *area_cols,
        ],
    ).rename(columns=rename_area)
    t_out["neighbourhood_id"] = t_out.neighbourhood_id.astype("Int64")
    t_out.to_parquet(PROCESSED_DIR / "tracts.parquet")
    mc.rename(columns={"geoid": "municipality_geoid", "share": "area_share"}).to_parquet(
        PROCESSED_DIR / "coc_municipalities.parquet"
    )
    nt.rename(columns={"geoid": "tract_geoid", "share": "area_share"}).to_parquet(
        PROCESSED_DIR / "neighbourhood_tracts.parquet"
    )
    tm.rename(
        columns={"geoid": "tract_geoid", "muni": "municipality_geoid", "share": "area_share"}
    ).to_parquet(PROCESSED_DIR / "tract_municipalities.parquet")

    # full-resolution polygons for spatial work in later steps
    tracts[["geoid", "geometry"]].to_parquet(INTERIM_DIR / "tracts_geom.parquet")
    munis[["geoid", "name", "geometry"]].to_parquet(INTERIM_DIR / "municipalities_geom.parquet")
    counties[["geoid", "geometry"]].to_parquet(INTERIM_DIR / "counties_geom.parquet")
    cocs[["coc_number", "geometry"]].to_parquet(INTERIM_DIR / "cocs_geom.parquet")
    hoods[["neighbourhood_id", "name", "geometry"]].to_parquet(
        INTERIM_DIR / "neighbourhoods_geom.parquet"
    )
    log.info("geography written")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
