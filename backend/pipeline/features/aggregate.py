"""Aggregate tract metrics to municipality, county, CoC, Boston neighbourhood and state.

County, CoC, neighbourhood and state: each tract is counted once, in the area holding the
largest share of its land (tracts nest in counties exactly). Municipality: 38 tracts cross
town lines and 37 small towns hold no tract on their own, so tract counts are apportioned to
towns by the tract's share of 2020 census-block housing units in each town (area share for
tracts with no housing units). Weights per tract sum to 1, so town totals add up exactly to
the state total. Count metrics are summed; rates are recomputed from summed numerators and
denominators (never averaged). Run after any step that changes tract metrics.

Run: uv run python -m pipeline.features.aggregate
"""

from __future__ import annotations

import logging
import sys

import geopandas as gpd
import pandas as pd

from app.core.database import get_session_factory
from app.dao.bulk_dao import BulkDao
from app.dao.data_source_dao import DataSourceDao
from app.dao.metric_dao import MetricDao
from app.models import AreaMetric, TractMunicipality
from app.services.load_service import LoadService
from pipeline.drops import record_drop
from pipeline.geo import MA_CRS
from pipeline.paths import INTERIM_DIR, RAW_DIR

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

# population-weighted means: metric -> weight metric. Computed as sum(value x weight) /
# sum(weight) over tracts that have a value; helper sums are not stored.
WEIGHTED_MEANS = {"need_index": "population"}
WEIGHTED_METHOD = (
    "population-weighted mean of tract values (ACS 2020-2024 population); "
    "tracts without a value are excluded"
)

MUNICIPALITY_METHOD = (
    "sum of tracts; tracts crossing town lines apportioned by 2020 census-block housing-unit "
    "share (area share where a tract has no housing units)"
)

# levels where each tract belongs to exactly one (its primary) area
LEVELS = {
    "county": "county_geoid",
    "coc": "coc_number",
    "neighbourhood": "neighbourhood_id",
    "state": "state",
}


def housing_weights(tm: pd.DataFrame, blocks: pd.DataFrame) -> pd.DataFrame:
    """tm: tract_geoid, municipality_geoid, area_share. blocks: tract_geoid,
    municipality_geoid, hu (housing units of blocks located in each town). Returns tm with
    ``housing_share`` (sums to 1 per tract) and ``weight_basis`` ('housing' or 'area')."""
    pairs = tm.merge(blocks, on=["tract_geoid", "municipality_geoid"], how="left")
    pairs["hu"] = pairs.hu.fillna(0.0)
    tract_hu = pairs.groupby("tract_geoid").hu.transform("sum")
    area_total = pairs.groupby("tract_geoid").area_share.transform("sum")
    has_hu = tract_hu > 0
    pairs["housing_share"] = (pairs.hu / tract_hu).where(has_hu, pairs.area_share / area_total)
    pairs["weight_basis"] = has_hu.map({True: "housing", False: "area"})
    return pairs.drop(columns=["hu"])


def block_housing_by_town() -> pd.DataFrame:
    """2020 block housing units summed per (tract, town); block internal points are located in
    the town polygons (blocks nest in towns, so each block is in exactly one)."""
    blocks = gpd.read_file(
        RAW_DIR / "census_relationship/tl_2020_25_tabblock20.zip",
        columns=["GEOID20", "HOUSING20", "INTPTLAT20", "INTPTLON20"],
        ignore_geometry=True,
    )
    blocks = blocks[blocks.HOUSING20.astype(int) > 0]
    pts = gpd.GeoDataFrame(
        {"tract_geoid": blocks.GEOID20.str[:11].values, "hu": blocks.HOUSING20.astype(int).values},
        geometry=gpd.points_from_xy(
            blocks.INTPTLON20.astype(float), blocks.INTPTLAT20.astype(float)
        ),
        crs="EPSG:4269",
    ).to_crs(MA_CRS)
    towns = gpd.read_parquet(INTERIM_DIR / "municipalities_geom.parquet")[["geoid", "geometry"]]
    j = gpd.sjoin(pts, towns.to_crs(MA_CRS), how="left", predicate="within")
    j = j[~j.index.duplicated()]
    record_drop(
        "aggregate", "2020 blocks with housing outside any town polygon", int(j.geoid.isna().sum())
    )
    j = j.dropna(subset=["geoid"])
    return (
        j.rename(columns={"geoid": "municipality_geoid"})
        .groupby(["tract_geoid", "municipality_geoid"], as_index=False)
        .hu.sum()
    )


def _sum_by(m: pd.DataFrame, key: str, weight: str | None) -> pd.DataFrame:
    m = m.dropna(subset=[key])
    if weight is not None:
        m = m.assign(value=m.value * m[weight])
    return m.groupby([key, "metric", "year"], as_index=False).agg(
        value=("value", lambda s: s.sum(min_count=1)),
        tract_count=("tract_geoid", "nunique"),
        source_key=("source_key", "first"),
        is_estimate=("is_estimate", "max"),
        method=("method", "first"),
    )


def aggregate(
    metrics: pd.DataFrame, assign: pd.DataFrame, town_weights: pd.DataFrame
) -> pd.DataFrame:
    """metrics: tract_geoid, metric, year, value, is_estimate, method, source_key.
    assign: geoid + one column per LEVELS entry. town_weights: tract_geoid,
    municipality_geoid, housing_share. Returns long area metrics."""
    sums_in = pd.concat(
        [metrics[metrics.metric.isin(SUM_METRICS)], weighted_mean_parts(metrics)],
        ignore_index=True,
    )
    out = []
    m = sums_in.merge(assign, left_on="tract_geoid", right_on="geoid", how="left")
    for level, col in LEVELS.items():
        g = _sum_by(m, col, None)
        g["level"] = level
        g["area_id"] = g[col].astype(str)
        out.append(g.drop(columns=[col]))
    mt = sums_in.merge(town_weights, on="tract_geoid", how="inner")
    mt = mt[mt.housing_share > 0]
    g = _sum_by(mt, "municipality_geoid", "housing_share")
    g["level"] = "municipality"
    g["area_id"] = g.municipality_geoid.astype(str)
    g["method"] = [
        f"{meth}; {MUNICIPALITY_METHOD}" if isinstance(meth, str) and meth else MUNICIPALITY_METHOD
        for meth in g.method
    ]
    out.append(g.drop(columns=["municipality_geoid"]))
    sums = pd.concat(out, ignore_index=True)

    ratio_rows = []
    present = set(sums.metric)
    ratios = {**RATIOS, **{m: (f"_{m}_x_w", f"_{m}_w", 1.0) for m in WEIGHTED_MEANS}}
    for name, (num, den, scale) in ratios.items():
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
        r["method"] = WEIGHTED_METHOD if name in WEIGHTED_MEANS else None
        ratio_rows.append(r)
    result = pd.concat([sums, *ratio_rows], ignore_index=True)
    return result[~result.metric.str.startswith("_")].reset_index(drop=True)


def weighted_mean_parts(metrics: pd.DataFrame) -> pd.DataFrame:
    """Helper rows _<m>_x_w (value x weight) and _<m>_w (weight) for tracts with a value."""
    parts = []
    for name, weight in WEIGHTED_MEANS.items():
        v = metrics[(metrics.metric == name) & metrics.value.notna()]
        w = metrics[metrics.metric == weight].set_index("tract_geoid").value
        v = v.assign(w=v.tract_geoid.map(w)).dropna(subset=["w"])
        if v.empty:
            continue
        v = v.assign(value=v.value.astype(float), w=v.w.astype(float))
        base = v.drop(columns=["w"])
        parts.append(base.assign(metric=f"_{name}_x_w", value=v.value * v.w))
        parts.append(base.assign(metric=f"_{name}_w", value=v.w))
    if not parts:
        return metrics.iloc[0:0]
    return pd.concat(parts, ignore_index=True)


def main() -> int:
    with get_session_factory()() as session:
        dao = MetricDao(session)
        metrics = pd.DataFrame(
            dao.tract_metric_rows(SUM_METRICS + list(WEIGHTED_MEANS)),
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
        tm = pd.DataFrame(
            dao.tract_municipality_rows(),
            columns=["tract_geoid", "municipality_geoid", "area_share"],
        )
        blocks = block_housing_by_town()
        unmatched = blocks.merge(
            tm, on=["tract_geoid", "municipality_geoid"], how="left", indicator=True
        )
        record_drop(
            "aggregate",
            "housing units (not rows) in blocks of a tract-town pair below the 0.1% area threshold",
            int(unmatched.loc[unmatched._merge == "left_only", "hu"].sum()),
        )
        weights = housing_weights(tm, blocks)
        log.info(
            "town weights: %d tract-town pairs, %d tracts on area share",
            len(weights),
            weights[weights.weight_basis == "area"].tract_geoid.nunique(),
        )
        loader = LoadService(BulkDao(session), DataSourceDao(session))
        loader.upsert(
            TractMunicipality,
            weights[["tract_geoid", "municipality_geoid", "area_share", "housing_share"]].to_dict(
                "records"
            ),
            ["tract_geoid", "municipality_geoid"],
        )
        result = aggregate(metrics, assign, weights)
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
        n = loader.replace(AreaMetric, records)
    log.info("area_metrics: %d rows", n)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(main())
