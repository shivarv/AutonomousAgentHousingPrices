"""Store scored candidate sites: reports/candidate_sites.csv (top 100 statewide plus the top
10 in every county) and Postgres (every screened parcel in parcels, every scored site in
site_candidates, and a model_runs row of kind 'site_scoring' holding the weights).

Run: uv run python -m pipeline.sites.load   (after pipeline.sites.score)
"""

from __future__ import annotations

import json
import logging
import math
from typing import Any

import pandas as pd

from app.core.database import get_session_factory
from app.dao.bulk_dao import BulkDao
from app.dao.data_source_dao import DataSourceDao
from app.dao.model_run_dao import ModelRunDao
from app.models import Parcel, SiteCandidate
from app.services.load_service import LoadService
from pipeline.paths import PROCESSED_DIR, REPORTS_DIR
from pipeline.sites import features as ft
from pipeline.sites import score as sc
from pipeline.sites import screen

log = logging.getLogger("pipeline.sites.load")

FEATURE_COLUMNS = [
    "municipality",
    "municipality_geoid",
    "county_geoid",
    "tract_geoid",
    "lat",
    "lon",
    "use_code",
    "use_description",
    "lot_size_acres",
    "assessor_lot_acres",
    "land_val",
    "total_val",
    "fiscal_year",
    *[f"{p}_{ft.ring_tag(r)}" for p in ft.RING_PREFIXES for r in ft.RADII_KM],
    "nearest_stop_km",
    "nearest_stop_name",
    "nearest_stop_mode",
    "nearest_rapid_km",
    "nearest_rapid_name",
    "in_mbta3a_district",
    "tract_land_value_per_sqft",
    "est_land_cost",
    "land_value_flag",
    "openspace_overlap",
    "wetland_overlap",
    "flood_overlap",
    "constrained_share",
]


def _json_value(v: Any) -> Any:
    if v is None:
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def parcel_rows(f: pd.DataFrame) -> list[dict]:
    return [
        {
            "loc_id": r.loc_id,
            "town_id": int(r.town_id),
            "municipality_geoid": r.municipality_geoid,
            "tract_geoid": r.tract_geoid,
            "use_code": r.use_code,
            "lot_size_acres": float(r.lot_size_acres),
            "land_value": _json_value(r.land_val),
            "building_value": _json_value(r.bldg_val),
            "total_value": _json_value(r.total_val),
            "fiscal_year": _json_value(r.fiscal_year),
            "centroid_lat": float(r.lat),
            "centroid_lon": float(r.lon),
            "boundary": json.loads(r.boundary),
            "openspace_overlap": float(r.openspace_overlap),
            "wetland_overlap": float(r.wetland_overlap),
            "flood_overlap": float(r.flood_overlap),
            "in_mbta3a_district": bool(r.in_mbta3a_district),
            "source_key": "massgis_parcels",
        }
        for r in f.itertuples()
    ]


def site_rows(f: pd.DataFrame, run_id: int) -> list[dict]:
    comps = [c for c in f.columns if c.startswith("component_")]
    return [
        {
            "parcel_loc_id": row["loc_id"],
            "model_run_id": run_id,
            "score": float(row["score"]),
            "rank_state": int(row["rank_state"]),
            "rank_county": int(row["rank_county"]),
            "features": {c: _json_value(row[c]) for c in FEATURE_COLUMNS},
            "components": {c.removeprefix("component_"): _json_value(row[c]) for c in comps},
            "flags": list(row["site_flags"]),
            "summary": row["summary"],
        }
        for _, row in f.iterrows()
    ]


REPORT_COLUMNS = [
    "rank_state",
    "rank_county",
    "score",
    "loc_id",
    "municipality",
    "county",
    "lat",
    "lon",
    "use_code",
    "use_description",
    "lot_size_acres",
    "need_index_5km",
    "gap_eli_1_5km",
    "gap_eli_5km",
    "gap_eli_15km",
    "homeless_est_1_5km",
    "homeless_est_5km",
    "homeless_est_15km",
    "shelters_5km",
    "nearest_stop_km",
    "nearest_stop_name",
    "nearest_rapid_km",
    "in_mbta3a_district",
    "tract_land_value_per_sqft",
    "est_land_cost",
    "flags",
    "summary",
]
REPORT_HEADER_NOTE = {
    "homeless_est_1_5km": "homeless_estimate_1_5km",
    "homeless_est_5km": "homeless_estimate_5km",
    "homeless_est_15km": "homeless_estimate_15km",
}


def report(f: pd.DataFrame) -> pd.DataFrame:
    """Top 100 statewide plus the top 10 in every county (each site once). Homeless columns
    are named *_estimate_* (modelled estimates, not counts)."""
    counties = pd.read_parquet(PROCESSED_DIR / "counties.parquet").set_index("geoid").name
    top = f[(f.rank_state <= 100) | (f.rank_county <= 10)].copy()
    top["county"] = top.county_geoid.map(counties)
    top["flags"] = top.site_flags.apply("; ".join)
    return top[REPORT_COLUMNS].sort_values("rank_state").rename(columns=REPORT_HEADER_NOTE)


def run() -> None:
    f = pd.read_parquet(sc.SCORED_FILE)
    rep = report(f)
    rep.to_csv(REPORTS_DIR / "candidate_sites.csv", index=False, float_format="%.4f")
    log.info("candidate_sites.csv: %d rows", len(rep))
    with get_session_factory()() as session:
        bulk = BulkDao(session)
        service = LoadService(bulk, DataSourceDao(session))
        bulk.delete_where(SiteCandidate, SiteCandidate.id.isnot(None))
        n_parcels = service.replace(Parcel, parcel_rows(f))
        run = ModelRunDao(session).replace_kind(
            "site_scoring",
            params={
                "weights": {k: w for k, (w, _) in sc.WEIGHTS.items()},
                "descriptions": {k: d for k, (_, d) in sc.WEIGHTS.items()},
                "radii_km": list(ft.RADII_KM),
                "developable_codes": screen.DEVELOPABLE_CODES,
                "min_acres": screen.MIN_ACRES,
                "max_constrained_share": screen.MAX_CONSTRAINED,
            },
            metrics={
                "sites": len(f),
                "score_min": float(f.score.min()),
                "score_max": float(f.score.max()),
            },
            artifact_path="reports/candidate_sites.csv",
            notes="score = 100 x weighted mean of percentile-ranked components",
        )
        session.commit()
        n_sites = service.replace(SiteCandidate, site_rows(f, run.id))
    log.info("parcels %d, site_candidates %d", n_parcels, n_sites)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
