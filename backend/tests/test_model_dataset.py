import numpy as np
import pandas as pd
import pytest

from pipeline.clean.parcels import lot_size_acres, stories_number
from pipeline.model import dataset


def _df(n: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    loc = [f"L{i // 2}" for i in range(n)]  # two records (e.g. condo units) per parcel
    county = ["25025" if i % 3 else "25017" for i in range(n // 2) for _ in range(2)]
    return pd.DataFrame(
        {
            "record_id": [f"r{i}" for i in range(n)],
            "loc_id": loc,
            "county_geoid": county,
            "v": rng.random(n),
        }
    )


def test_split_proportions_stratified_and_grouped() -> None:
    s = dataset.make_split(_df())
    for _, g in s.drop_duplicates("loc_id").groupby("county_geoid"):
        share = g.split.value_counts(normalize=True)
        assert share["train"] == pytest.approx(0.70, abs=0.01)
        assert share["validation"] == pytest.approx(0.15, abs=0.01)
        assert share["test"] == pytest.approx(0.15, abs=0.01)
    assert s.groupby("loc_id").split.nunique().max() == 1


def test_split_is_deterministic() -> None:
    a = dataset.make_split(_df())
    b = dataset.make_split(_df())
    assert a.split.tolist() == b.split.tolist()


def test_saved_split_is_reused_not_regenerated(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dataset, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(dataset, "SPLIT_FILE", tmp_path / "split.parquet")
    first = dataset.load_or_create_split(_df())
    other = _df().assign(county_geoid="25001")
    again = dataset.load_or_create_split(other)
    assert again.split.tolist() == first.split.tolist()
    assert set(again.county_geoid) == {"25025", "25017"}


def test_lot_size_units() -> None:
    out = lot_size_acres(pd.Series([2.0, 43560.0, 5.0]), pd.Series(["A", "S", None]))
    assert out[0] == 2.0
    assert out[1] == pytest.approx(1.0)
    assert np.isnan(out[2])


def test_stories_parsing() -> None:
    out = stories_number(pd.Series(["2", "1 1/2", "2.5", "split", None]))
    assert out.tolist()[:3] == [2.0, 1.5, 2.5]
    assert out[3:].isna().all()


def test_residential_filters_codes_values_and_location() -> None:
    assess = pd.DataFrame(
        {
            "record_id": ["a", "b", "c", "d", "e"],
            "loc_id": ["L1", "L2", "L3", "L4", "LX"],
            "use_code": ["1010", "102", "340", "101", "101"],
            "total_val": [500_000, 300_000, 900_000, 5_000, 400_000],
            "bldg_val": [300_000, 250_000, 600_000, 1_000, 200_000],
        }
    )
    points = pd.DataFrame(
        {
            "loc_id": ["L1", "L2", "L3", "L4"],
            "tract_geoid": ["t"] * 4,
            "municipality_geoid": ["m"] * 4,
            "county_geoid": ["c"] * 4,
            "x": 0.0,
            "y": 0.0,
            "area_m2": 1.0,
        }
    )
    out = dataset.residential(assess, points)
    assert out.record_id.tolist() == ["a", "b"]
