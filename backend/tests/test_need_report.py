import csv

import pandas as pd

from pipeline.index.report import TOP_COUNTY, TOP_STATE, top_tracts
from pipeline.paths import REPORTS_DIR


def test_top_tracts_statewide_then_per_county() -> None:
    rows = [(f"t{i}", float(i), "A County" if i % 2 else "B County") for i in range(80)]
    rows.append(("tnull", None, "A County"))
    df = pd.DataFrame(rows, columns=["geoid", "need_index", "county"])
    out = top_tracts(df)
    state = out[out.scope == "Massachusetts"]
    assert len(state) == TOP_STATE
    assert state.iloc[0].geoid == "t79"
    assert state["rank"].tolist() == list(range(1, TOP_STATE + 1))
    for county in ("A County", "B County"):
        part = out[out.scope == county]
        assert len(part) == TOP_COUNTY
        assert part.need_index.is_monotonic_decreasing
    assert "tnull" not in set(out.geoid)


def test_generated_csvs_present_and_complete() -> None:
    path = REPORTS_DIR / "top_tracts.csv"
    towns = REPORTS_DIR / "municipality_need.csv"
    if not path.exists() or not towns.exists():
        import pytest

        pytest.skip("reports not generated")
    with path.open() as f:
        rows = list(csv.DictReader(f))
    scopes = {r["scope"] for r in rows}
    assert sum(r["scope"] == "Massachusetts" for r in rows) == TOP_STATE
    assert len(scopes) == 15  # state + 14 counties
    assert all(0 <= float(r["need_index"]) <= 100 for r in rows)
    assert "homeless_estimate_ESTIMATE" in rows[0]
    with towns.open() as f:
        town_rows = list(csv.DictReader(f))
    assert len(town_rows) == 351
