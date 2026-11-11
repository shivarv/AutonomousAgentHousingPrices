import numpy as np
import pandas as pd
import pytest

from pipeline.model import home_value as hv


def test_mape_and_median_ape() -> None:
    y = np.array([100.0, 200.0, 400.0])
    pred = np.array([110.0, 180.0, 400.0])
    assert hv.mape(y, pred) == pytest.approx((0.1 + 0.1 + 0.0) / 3)
    assert hv.median_ape(y, pred) == pytest.approx(0.1)


def _train() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "total_val": [100.0, 300.0, 200.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
            "municipality_geoid": ["m1", "m1", "m1", "m2", "m2", "m2", "m2", "m2"],
            "county_geoid": ["c1", "c1", "c1", "c1", "c1", "c1", "c1", "c1"],
            "tract_geoid": ["t1", "t1", "t1", "t2", "t2", "t2", "t2", "t2"],
        }
    )


def test_encodings_are_train_only_and_baseline_falls_back_to_county() -> None:
    enc = hv.Encodings.fit(_train())
    other = pd.DataFrame({"municipality_geoid": ["m1", "m9"], "county_geoid": ["c1", "c1"]})
    base = enc.baseline(other)
    assert base[0] == 200.0
    assert base[1] == pytest.approx(_train().total_val.median())
    # t1 has 3 records (< MIN_TRACT_RECORDS): no tract encoding
    assert "t1" not in enc.tract_median_log.index
    assert enc.tract_median_log["t2"] == pytest.approx(np.log(1000.0))


def test_prepare_marks_unrecorded_values_missing() -> None:
    df = pd.DataFrame(
        {
            "res_area": [0.0, 1500.0],
            "bld_area": [0.0, 2000.0],
            "num_rooms": [0.0, 6.0],
            "year_built": [0.0, 1950.0],
            "lot_size_acres": [0.0, 0.25],
            "area_m2": [500.0, 800.0],
            "tract_geoid": ["t1", "t2"],
        }
    )
    ctx = pd.DataFrame({"tract_zhvi": [5e5]}, index=pd.Index(["t1"], name="tract_geoid"))
    out = hv.prepare(df, ctx)
    assert (
        out.loc[0, ["res_area", "bld_area", "num_rooms", "year_built", "lot_size_acres"]]
        .isna()
        .all()
    )
    assert out.loc[1, "year_built"] == 1950.0
    assert out.loc[0, "tract_zhvi"] == 5e5
    assert np.isnan(out.loc[1, "tract_zhvi"])


def test_selection_uses_validation_only(monkeypatch) -> None:
    """fit_and_select never receives the test split: its signature takes train and validation
    only, and choosing a model is based on the returned validation scores."""
    rng = np.random.default_rng(0)
    n = 400

    def frame(k: int) -> pd.DataFrame:
        d = pd.DataFrame({c: rng.random(k) for c in hv.NUMERIC})
        d["use3"] = rng.choice(["101", "102"], k)
        d["county_geoid"] = rng.choice(["25025", "25017"], k)
        d["total_val"] = np.exp(12 + d.res_area * 2 + rng.normal(0, 0.05, k))
        return d

    monkeypatch.setattr(
        hv, "HGB_GRID", [{"learning_rate": 0.1, "max_leaf_nodes": 15, "max_iter": 50}]
    )
    monkeypatch.setattr(hv, "RIDGE_ALPHAS", (1.0,))
    kind, model, params, trials = hv.fit_and_select(frame(n), frame(n // 4))
    assert len(trials) == 2
    assert all("validation_mape" in t for t in trials)
    best = min(trials, key=lambda t: t["validation_mape"])
    assert best["params"] == params
    assert hv.predict(kind, model, frame(10)).shape == (10,)
