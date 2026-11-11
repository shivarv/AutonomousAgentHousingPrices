"""Need Index reports: reports/top_tracts.csv (top 50 statewide + top 10 per county) and
reports/municipality_need.csv (every town, population-weighted Need Index).

Run: uv run python -m pipeline.index.report   (after pipeline.load and features.aggregate)
"""

from __future__ import annotations

import logging

import pandas as pd

from app.core.database import get_session_factory
from app.dao.report_dao import ReportDao
from pipeline.paths import REPORTS_DIR

log = logging.getLogger("pipeline.index.report")

TOP_STATE = 50
TOP_COUNTY = 10

TRACT_METRICS = {
    "need_index": "need_index",
    "need_index_components": "components_used",
    "population": "population",
    "eli_renter_households": "eli_renter_households",
    "affordable_gap_eli": "affordable_gap_eli",
    "affordable_units_per_100_eli": "affordable_units_per_100_eli",
    "severe_rent_burden_share": "severe_rent_burden_share",
    "poverty_rate": "poverty_rate",
    "homeless_estimate": "homeless_estimate_ESTIMATE",
    "homeless_estimate_per_1000": "homeless_estimate_per_1000_ESTIMATE",
}
TOWN_METRICS = {
    "need_index": "need_index_pop_weighted",
    "population": "population",
    "eli_renter_households": "eli_renter_households",
    "affordable_gap_eli": "affordable_gap_eli",
    "affordable_units_per_100_eli": "affordable_units_per_100_eli",
    "severely_rent_burdened_households": "severely_rent_burdened_households",
    "homeless_estimate": "homeless_estimate_ESTIMATE",
}


def top_tracts(tracts: pd.DataFrame) -> pd.DataFrame:
    """tracts: one row per tract with need_index, county. Returns statewide top 50 then the
    top 10 of each county, with scope and rank columns (a tract can appear in both)."""
    ranked = tracts.dropna(subset=["need_index"]).sort_values(
        ["need_index", "geoid"], ascending=[False, True]
    )
    state = ranked.head(TOP_STATE).assign(scope="Massachusetts")
    state.insert(0, "rank", range(1, len(state) + 1))
    parts = [state]
    for county, g in ranked.groupby("county", sort=True):
        top = g.head(TOP_COUNTY).assign(scope=f"{county}")
        top.insert(0, "rank", range(1, len(top) + 1))
        parts.append(top)
    out = pd.concat(parts, ignore_index=True)
    cols = ["scope", "rank"] + [c for c in out.columns if c not in ("scope", "rank")]
    return out[cols]


def run() -> tuple[pd.DataFrame, pd.DataFrame]:
    with get_session_factory()() as session:
        dao = ReportDao(session)
        t = pd.DataFrame(dao.tracts(), columns=list(dao.tracts()[0]._fields))
        mv = pd.DataFrame(
            dao.tract_metric_values(list(TRACT_METRICS)),
            columns=["tract_geoid", "metric", "value", "flag"],
        )
        towns = pd.DataFrame(dao.municipalities(), columns=["geoid", "municipality", "county"])
        av = pd.DataFrame(
            dao.area_metric_values("municipality", list(TOWN_METRICS)),
            columns=["area_id", "metric", "value", "tract_count"],
        )
    wide = mv.pivot(index="tract_geoid", columns="metric", values="value").rename(
        columns=TRACT_METRICS
    )
    flags = mv[mv.metric == "need_index"].set_index("tract_geoid").flag.rename("need_index_flag")
    tracts = (
        t.drop(columns=["county_geoid", "municipality_geoid"])
        .set_index("geoid")
        .join(wide)
        .join(flags)
        .reset_index()
    )
    tracts["need_index"] = tracts.need_index.round(1)
    first = ["geoid", "tract_name", "municipality", "county", "coc_number"]
    tracts = tracts[first + list(TRACT_METRICS.values()) + ["need_index_flag"]]
    top = top_tracts(tracts)
    top.to_csv(REPORTS_DIR / "top_tracts.csv", index=False, float_format="%.4g")

    tw = av.pivot(index="area_id", columns="metric", values="value").rename(columns=TOWN_METRICS)
    tw["tracts_contributing"] = av[av.metric == "need_index"].set_index("area_id").tract_count
    town = towns.set_index("geoid").join(tw).reset_index().rename(columns={"geoid": "town_geoid"})
    town = town.sort_values("need_index_pop_weighted", ascending=False, na_position="last")
    town = town[
        ["town_geoid", "municipality", "county", *TOWN_METRICS.values(), "tracts_contributing"]
    ]
    town.insert(0, "rank", range(1, len(town) + 1))
    town["need_index_pop_weighted"] = town.need_index_pop_weighted.round(1)
    town.to_csv(REPORTS_DIR / "municipality_need.csv", index=False, float_format="%.6g")
    log.info("top_tracts.csv %d rows; municipality_need.csv %d rows", len(top), len(town))
    return top, town


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
