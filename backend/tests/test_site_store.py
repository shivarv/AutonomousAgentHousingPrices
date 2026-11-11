import numpy as np
import pandas as pd

from app.dao import bulk_dao
from pipeline.sites import load


def test_batches_respect_parameter_limit() -> None:
    rows = [{f"c{i}": 1 for i in range(20)} for _ in range(10_000)]
    sizes = [len(b) for b in bulk_dao._batches(rows)]
    assert sum(sizes) == 10_000
    assert max(sizes) * 20 <= bulk_dao.MAX_PARAMS


def test_json_value_cleans_numpy_and_nan() -> None:
    assert load._json_value(np.float64(1.5)) == 1.5
    assert load._json_value(float("nan")) is None
    assert load._json_value(None) is None


def test_report_has_top_100_and_top_10_per_county(monkeypatch) -> None:
    n = 300
    f = pd.DataFrame(
        {c: 0.0 for c in load.REPORT_COLUMNS if c not in ("county", "flags")}, index=range(n)
    )
    f["rank_state"] = np.arange(1, n + 1)
    f["county_geoid"] = np.where(np.arange(n) < 250, "a", "b")
    f["rank_county"] = f.groupby("county_geoid").cumcount() + 1
    f["site_flags"] = [["x"]] * n
    monkeypatch.setattr(
        load.pd,
        "read_parquet",
        lambda *_a, **_k: pd.DataFrame({"geoid": ["a", "b"], "name": ["A", "B"]}),
    )
    rep = load.report(f)
    assert len(rep) == 100 + 10  # county b's top 10 start at rank 251
    assert "homeless_estimate_5km" in rep.columns
    assert rep["flags"].iloc[0] == "x"
