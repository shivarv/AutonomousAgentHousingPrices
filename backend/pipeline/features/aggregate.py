"""Aggregate tract metrics to municipality, county, CoC, Boston neighbourhood and state.

Each tract is counted once, in the area holding the largest share of its land (its primary
municipality / CoC / neighbourhood), so area totals add up exactly to the tract sums.
Count metrics are summed; rates are recomputed from summed numerators and denominators
(never averaged). Run after any step that changes tract metrics.

Run: uv run python -m pipeline.features.aggregate
"""

from __future__ import annotations

import logging
import sys

import pandas as pd

from app.core.database import get_session_factory
from app.dao.bulk_dao import BulkDao
from app.dao.data_source_dao import DataSourceDao
from app.dao.metric_dao import MetricDao
from app.models import AreaMetric
from app.services.load_service import LoadService

log = logging.getLogger("pipeline.features.aggregate")

SUM_METRICS = [
    "population",
    "households",
    "housing_units",
    "occupied_units",
    "vacant_units",
    "vacant_for_rent",
    "vacant_for_sale",
    "renter_households",
    "owner_households",
    "poverty_universe",
    "poverty_count",
    "overcrowded_households",
    "rent_burden_universe",
    "rent_burdened_households",
    "severely_rent_burdened_households",
    "hud_assisted_units",
    "lihtc_low_income_units",
    "eli_renter_households",
    "vli_renter_households",
    "eli_severely_burdened_renters",
    "vli_severely_burdened_renters",
    "units_affordable_available_eli",
    "units_affordable_available_vli",
    "affordable_gap_eli",
    "affordable_gap_vli",
    "homeless_estimate",
    "homeless_estimate_sheltered",
    "homeless_estimate_unsheltered",
    "eviction_filings_annual",
]

# derived metric -> (numerator, denominator, scale)
RATIOS = {
    "poverty_rate": ("poverty_count", "poverty_universe", 1.0),
    "vacancy_rate": ("vacant_units", "housing_units", 1.0),
    "rent_burden_share": ("rent_burdened_households", "rent_burden_universe", 1.0),
    "severe_rent_burden_share": ("severely_rent_burdened_households", "rent_burden_universe", 1.0),
    "affordable_units_per_100_eli": (
        "units_affordable_available_eli",
        "eli_renter_households",
        100.0,
    ),
    "affordable_units_per_100_vli": (
        "units_affordable_available_vli",
        "vli_renter_households",
        100.0,
    ),
    "eli_severe_burden_share": ("eli_severely_burdened_renters", "eli_renter_households", 1.0),
}

LEVELS = {
    "municipality": "municipality_geoid",
    "county": "county_geoid",
    "coc": "coc_number",
    "neighbourhood": "neighbourhood_id",
    "state": "state",
}


def aggregate(metrics: pd.DataFrame, assign: pd.DataFrame) -> pd.DataFrame:
    """metrics: tract_geoid, metric, year, value, is_estimate, method, source_key.
    assign: geoid + one column per level. Returns long area metrics."""
    m = metrics[metrics.metric.isin(SUM_METRICS)].merge(
        assign, left_on="tract_geoid", right_on="geoid", how="left"
    )
    out = []
    for level, col in LEVELS.items():
        part = m.dropna(subset=[col])
        g = part.groupby([col, "metric", "year"], as_index=False).agg(
            value=("value", lambda s: s.sum(min_count=1)),
            tract_count=("tract_geoid", "nunique"),
            source_key=("source_key", "first"),
            is_estimate=("is_estimate", "max"),
            method=("method", "first"),
        )
        g["level"] = level
        g["area_id"] = g[col].astype(str)
        out.append(g.drop(columns=[col]))
    sums = pd.concat(out, ignore_index=True)

    ratio_rows = []
    present = set(sums.metric)
    for name, (num, den, scale) in RATIOS.items():
        if num not in present or den not in present:
            continue
        nn = sums[sums.metric == num].set_index(["level", "area_id", "year"])
        dd = sums[sums.metric == den].set_index(["level", "area_id", "year"])
        joined = nn.join(dd[["value"]].rename(columns={"value": "value_den"}), how="inner")
        val = scale * joined.value / joined.value_den.where(joined.value_den > 0)
        r = joined.reset_index()[["level", "area_id", "year", "tract_count", "source_key"]]
        r["metric"] = name
        r["value"] = val.values
        r["is_estimate"] = False
        r["method"] = None
        ratio_rows.append(r)
    return pd.concat([sums, *ratio_rows], ignore_index=True)


def main() -> int:
    with get_session_factory()() as session:
        dao = MetricDao(session)
        metrics = pd.DataFrame(
            dao.tract_metric_rows(SUM_METRICS),
            columns=[
                "tract_geoid",
                "metric",
                "year",
                "value",
                "is_estimate",
                "method",
                "source_key",
            ],
        )
        assign = pd.DataFrame(
            dao.tract_assignments(),
            columns=[
                "geoid",
                "municipality_geoid",
                "county_geoid",
                "coc_number",
                "neighbourhood_id",
            ],
        )
        assign["neighbourhood_id"] = (
            assign.neighbourhood_id.astype("Int64")
            .astype(str)
            .where(assign.neighbourhood_id.notna())
        )
        assign["state"] = "25"
        result = aggregate(metrics, assign)
        cols = [
            "level",
            "area_id",
            "metric",
            "year",
            "value",
            "tract_count",
            "source_key",
            "is_estimate",
            "method",
        ]
        records = result[cols].astype(object).where(result[cols].notna(), None).to_dict("records")
        n = LoadService(BulkDao(session), DataSourceDao(session)).replace(AreaMetric, records)
    log.info("area_metrics: %d rows", n)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(main())
