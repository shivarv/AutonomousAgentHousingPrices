"""Candidate construction sites, step 2: features for every screened parcel.

- rings of 1.5, 5 and 15 km (geodesic, app.services.rings, tract area shares): population-
  weighted Need Index, affordable gap for extremely-low-income renters (shortage > 0,
  surplus < 0), estimated people experiencing homelessness (sum of modelled tract
  estimates; an estimate, not a count), population, and OpenStreetMap shelters in the ring
  (bed counts are not published per shelter, see BLOCKERS.md);
- distance to the nearest MBTA/RTA stop (any mode) and nearest rail/subway/ferry stop;
- inside an MBTA Communities (Section 3A) multifamily district (from screening);
- estimated land cost = tract median assessed land value per sq ft x lot area (sq ft);
- lot size (GIS acres) and municipality.

Run: uv run python -m pipeline.sites.features   (after pipeline.sites.screen)
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from app.services import rings
from pipeline.paths import PROCESSED_DIR
from pipeline.sites.screen import SITES_FILE

log = logging.getLogger("pipeline.sites.features")

RADII_KM = (1.5, 5.0, 15.0)
SQFT_PER_ACRE = 43_560.0
FEATURES_FILE = PROCESSED_DIR / "site_features.parquet"
RING_PREFIXES = ("need_index", "gap_eli", "homeless_est", "population", "shelters")
COUNT_METRICS = ("affordable_gap_eli", "homeless_estimate", "population")


def ring_tag(r: float) -> str:
    return f"{r:g}km".replace(".", "_")


def tract_inputs() -> tuple[rings.TractGeometry, dict[str, np.ndarray], pd.DataFrame]:
    # the same simplified boundaries the database and API use, so ring numbers match
    g = pd.read_parquet(PROCESSED_DIR / "tracts.parquet", columns=["geoid", "boundary"])
    g = g.sort_values("geoid").reset_index(drop=True)
    geoms = rings.geojson_to_state_plane([json.loads(b) for b in g.boundary])
    frames = [
        pd.read_parquet(PROCESSED_DIR / f"{f}.parquet")
        for f in ("metrics_acs", "metrics_chas", "metrics_homeless", "metrics_need", "metrics_land")
    ]
    m = pd.concat(frames, ignore_index=True)
    wanted = [*COUNT_METRICS, "need_index", "land_value_per_sqft"]
    wide = (
        m[m.metric.isin(wanted)]
        .pivot_table(index="tract_geoid", columns="metric", values="value", aggfunc="first")
        .reindex(g.geoid)
    )
    flags = m[(m.metric == "land_value_per_sqft")].set_index("tract_geoid").flag.reindex(g.geoid)
    wide["land_flag"] = flags
    arrays = {c: wide[c].to_numpy(dtype=float) for c in wanted}
    return rings.TractGeometry.build(g.geoid.to_numpy(), geoms), arrays, wide


def ring_features(
    sites: pd.DataFrame, tg: rings.TractGeometry, arrays: dict[str, np.ndarray]
) -> pd.DataFrame:
    counts = {k: arrays[k] for k in COUNT_METRICS}
    rows = []
    for lon, lat in zip(sites.lon.to_numpy(), sites.lat.to_numpy(), strict=True):
        row: dict[str, float | None] = {}
        for r in RADII_KM:
            circle = rings.geodesic_circle(lon, lat, r * 1000)
            idx, share = tg.shares(circle)
            tot = rings.ring_totals(idx, share, counts)
            tag = ring_tag(r)
            row[f"gap_eli_{tag}"] = tot["affordable_gap_eli"]
            row[f"homeless_est_{tag}"] = tot["homeless_estimate"]
            row[f"population_{tag}"] = tot["population"]
            row[f"need_index_{tag}"] = rings.weighted_mean(
                idx, share, arrays["need_index"], arrays["population"]
            )
        rows.append(row)
    return pd.DataFrame(rows, index=sites.index)


def point_features(sites: pd.DataFrame) -> pd.DataFrame:
    xy = np.column_stack([sites.x.to_numpy(), sites.y.to_numpy()])
    stops = pd.read_parquet(PROCESSED_DIR / "transit_stops.parquet")
    sxy = np.column_stack(rings.to_state_plane_many(stops.lon.to_numpy(), stops.lat.to_numpy()))
    d_any, i_any = cKDTree(sxy).query(xy)
    rapid = stops["mode"].isin(["subway", "rail", "ferry"]).to_numpy()
    d_rapid, i_rapid = cKDTree(sxy[rapid]).query(xy)
    shelters = pd.read_parquet(PROCESSED_DIR / "shelters.parquet")
    hxy = np.column_stack(
        rings.to_state_plane_many(shelters.lon.to_numpy(), shelters.lat.to_numpy())
    )
    out = pd.DataFrame(index=sites.index)
    out["nearest_stop_km"] = d_any / 1000
    out["nearest_stop_name"] = stops.name.to_numpy()[i_any]
    out["nearest_stop_mode"] = stops["mode"].to_numpy()[i_any]
    out["nearest_rapid_km"] = d_rapid / 1000
    out["nearest_rapid_name"] = stops.name.to_numpy()[rapid][i_rapid]
    tree = cKDTree(hxy)
    for r in RADII_KM:
        tag = ring_tag(r)
        out[f"shelters_{tag}"] = [len(v) for v in tree.query_ball_point(xy, r * 1000)]
    return out


def land_cost(sites: pd.DataFrame, wide: pd.DataFrame) -> pd.DataFrame:
    per_sqft = sites.tract_geoid.map(wide.land_value_per_sqft)
    out = pd.DataFrame(index=sites.index)
    out["tract_land_value_per_sqft"] = per_sqft
    out["est_land_cost"] = per_sqft * sites.lot_size_acres * SQFT_PER_ACRE
    out["land_value_flag"] = sites.tract_geoid.map(wide.land_flag)
    return out


def build() -> pd.DataFrame:
    sites = pd.read_parquet(SITES_FILE)
    tg, arrays, wide = tract_inputs()
    log.info("features for %d sites", len(sites))
    f = pd.concat(
        [sites, ring_features(sites, tg, arrays), point_features(sites), land_cost(sites, wide)],
        axis=1,
    )
    towns = pd.read_parquet(PROCESSED_DIR / "municipalities.parquet").set_index("geoid").name
    f["municipality"] = f.municipality_geoid.map(towns)
    return f


def run() -> None:
    f = build()
    f.to_parquet(FEATURES_FILE)
    log.info(
        "site features written: %d sites, %d without land value, median 5 km need %.1f",
        len(f),
        int(f.tract_land_value_per_sqft.isna().sum()),
        f.need_index_5km.median(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
