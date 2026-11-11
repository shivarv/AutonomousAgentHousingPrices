import math

import pandas as pd
import pytest

from pipeline.index.components import (
    COMPONENT_KEYS,
    nearest_distance_km,
    percentile_score,
    raw_components,
)


def test_percentile_score_range_order_ties_and_missing() -> None:
    s = percentile_score(pd.Series([10.0, None, 30.0, 20.0, 20.0]))
    assert s[0] == 0.0
    assert s[2] == 1.0
    assert s[3] == s[4] == pytest.approx(0.5)
    assert math.isnan(s[1])


def test_percentile_score_single_and_empty() -> None:
    assert percentile_score(pd.Series([3.0, None])).iloc[0] == 0.5
    assert percentile_score(pd.Series([None, None], dtype=float)).isna().all()


TRACTS = pd.DataFrame(
    {"geoid": ["t1", "t2"], "centroid_lat": [42.36, 42.36], "centroid_lon": [-71.06, -71.00]}
)


def test_nearest_distance_km() -> None:
    pts = pd.DataFrame({"lat": [42.36, None], "lon": [-71.06, -71.0]})
    d = nearest_distance_km(TRACTS, pts)
    assert d["t1"] == pytest.approx(0.0, abs=0.01)
    # 0.06 degrees of longitude at 42.36N is about 4.93 km
    assert d["t2"] == pytest.approx(4.93, rel=0.02)


def test_raw_components_ratios_and_null_denominators() -> None:
    rows = [
        ("t1", "affordable_gap_eli", 50.0),
        ("t1", "eli_renter_households", 100.0),
        ("t1", "homeless_estimate", 2.0),
        ("t1", "population", 1000.0),
        ("t1", "poverty_rate", 0.2),
        ("t2", "affordable_gap_eli", 0.0),
        ("t2", "eli_renter_households", 0.0),
        ("t2", "homeless_estimate", 0.0),
        ("t2", "population", 0.0),
    ]
    m = pd.DataFrame(rows, columns=["tract_geoid", "metric", "value"])
    pts = pd.DataFrame({"lat": [42.36], "lon": [-71.06]})
    r = raw_components(m, TRACTS, pts)
    assert list(r.columns) == COMPONENT_KEYS
    assert r.loc["t1", "affordable_gap_per_eli_renter"] == pytest.approx(0.5)
    assert r.loc["t1", "homeless_estimate_per_1000"] == pytest.approx(2.0)
    assert math.isnan(r.loc["t2", "affordable_gap_per_eli_renter"])
    assert math.isnan(r.loc["t2", "homeless_estimate_per_1000"])
    assert math.isnan(r.loc["t2", "poverty_rate"])
    assert math.isnan(r.loc["t1", "zori_growth_5yr"])  # absent metric stays missing
