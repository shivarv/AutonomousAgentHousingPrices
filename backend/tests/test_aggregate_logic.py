"""Unit tests for the aggregation arithmetic (no database)."""

import pandas as pd
import pytest

from pipeline.features.aggregate import aggregate, housing_weights


def _metrics() -> pd.DataFrame:
    rows = [
        ("t1", "affordable_gap_eli", 100.0),
        ("t2", "affordable_gap_eli", -20.0),
        ("t1", "eli_renter_households", 200.0),
        ("t2", "eli_renter_households", 50.0),
        ("t1", "units_affordable_available_eli", 100.0),
        ("t2", "units_affordable_available_eli", 70.0),
    ]
    df = pd.DataFrame(rows, columns=["tract_geoid", "metric", "value"])
    df["year"], df["is_estimate"], df["method"], df["source_key"] = 2022, False, None, "hud_chas"
    return df


def _assign() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geoid": ["t1", "t2"],
            "county_geoid": ["c1", "c1"],
            "coc_number": ["A", "B"],
            "neighbourhood_id": [None, None],
            "state": ["25", "25"],
        }
    )


def test_housing_weights_split_and_area_fallback() -> None:
    tm = pd.DataFrame(
        {
            "tract_geoid": ["t1", "t1", "t2", "t2"],
            "municipality_geoid": ["m1", "m2", "m2", "m3"],
            "area_share": [0.5, 0.5, 0.75, 0.25],
        }
    )
    blocks = pd.DataFrame(
        {"tract_geoid": ["t1", "t1"], "municipality_geoid": ["m1", "m2"], "hu": [30, 10]}
    )
    w = housing_weights(tm, blocks).set_index(["tract_geoid", "municipality_geoid"])
    assert w.loc[("t1", "m1"), "housing_share"] == pytest.approx(0.75)
    assert w.loc[("t1", "m2"), "housing_share"] == pytest.approx(0.25)
    # t2 has no housing units: area share used, and flagged
    assert w.loc[("t2", "m2"), "housing_share"] == pytest.approx(0.75)
    assert w.loc[("t2", "m2"), "weight_basis"] == "area"


def test_aggregate_sums_and_recomputes_ratios() -> None:
    weights = pd.DataFrame(
        {
            "tract_geoid": ["t1", "t1", "t2"],
            "municipality_geoid": ["m1", "m2", "m2"],
            "housing_share": [0.75, 0.25, 1.0],
        }
    )
    out = aggregate(_metrics(), _assign(), weights).set_index(["level", "area_id", "metric"])
    v = out.value
    assert v[("state", "25", "affordable_gap_eli")] == pytest.approx(80.0)
    assert v[("county", "c1", "affordable_gap_eli")] == pytest.approx(80.0)
    assert v[("coc", "B", "affordable_gap_eli")] == pytest.approx(-20.0)
    assert v[("municipality", "m1", "affordable_gap_eli")] == pytest.approx(75.0)
    assert v[("municipality", "m2", "affordable_gap_eli")] == pytest.approx(5.0)
    # per-100 ratio from summed parts, not an average of tract ratios
    assert v[("state", "25", "affordable_units_per_100_eli")] == pytest.approx(100 * 170 / 250)
    towns = out.xs("municipality", level="level").xs("affordable_gap_eli", level="metric").value
    assert towns.sum() == pytest.approx(80.0)
    assert out.loc[("municipality", "m1", "affordable_gap_eli"), "method"].startswith("sum of")


def test_population_weighted_need_index() -> None:
    m = _metrics()
    extra = pd.DataFrame(
        [
            ("t1", "need_index", 2026, 80.0),
            ("t2", "need_index", 2026, 20.0),
            ("t1", "population", 2024, 300.0),
            ("t2", "population", 2024, 100.0),
        ],
        columns=["tract_geoid", "metric", "year", "value"],
    ).assign(is_estimate=False, method=None, source_key="hud_chas")
    weights = pd.DataFrame(
        {"tract_geoid": ["t1", "t2"], "municipality_geoid": ["m1", "m1"], "housing_share": 1.0}
    )
    out = aggregate(pd.concat([m, extra]), _assign(), weights).set_index(
        ["level", "area_id", "metric"]
    )
    assert out.value[("state", "25", "need_index")] == pytest.approx(65.0)
    assert out.value[("municipality", "m1", "need_index")] == pytest.approx(65.0)
    assert not out.index.get_level_values("metric").str.startswith("_").any()
