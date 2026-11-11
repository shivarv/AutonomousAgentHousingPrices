import numpy as np
import pandas as pd
import pytest

from pipeline.sites import score as sc


def test_pct_rank_bounds_direction_and_nan() -> None:
    s = pd.Series([1.0, 2.0, 3.0, np.nan])
    up = sc.pct_rank(s)
    down = sc.pct_rank(s, higher_is_better=False)
    assert up.tolist()[:3] == pytest.approx([0.0, 0.5, 1.0])
    assert down.tolist()[:3] == pytest.approx([1.0, 0.5, 0.0])
    assert np.isnan(up.iloc[3])


def test_score_range_and_missing_components_score_zero() -> None:
    c = pd.DataFrame({k: [1.0, 0.0] for k in sc.WEIGHTS})
    c.loc[0, "land_cost"] = np.nan
    s = sc.score(c)
    w = sc.WEIGHTS["land_cost"][0] / sum(v for v, _ in sc.WEIGHTS.values())
    assert s.iloc[0] == pytest.approx(100 * (1 - w), abs=0.01)
    assert s.iloc[1] == 0.0
    assert sum(v for v, _ in sc.WEIGHTS.values()) == pytest.approx(1.0)


def test_summary_uses_only_site_features() -> None:
    f = pd.Series(
        {
            "lot_size_acres": 2.25,
            "use_description": "developable residential land",
            "municipality": "Worcester city",
            "need_index_5km": 61.4,
            "gap_eli_5km": -120.0,
            "homeless_est_5km": 43.2,
            "nearest_stop_name": "Main St",
            "nearest_stop_mode": "bus",
            "nearest_stop_km": 0.31,
            "in_mbta3a_district": False,
            "est_land_cost": np.nan,
            "tract_land_value_per_sqft": np.nan,
            "site_flags": [],
        }
    )
    text = sc.summary(f)
    assert "2.2-acre" in text or "2.3-acre" in text
    assert "surplus of 120" in text
    assert "estimate" in text
    assert "land cost" not in text  # missing value is not reported
