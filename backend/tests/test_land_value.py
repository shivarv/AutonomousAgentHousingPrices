import numpy as np
import pandas as pd
import pytest

from pipeline.features.land_value import (
    FEW_FLAG,
    MIN_PARCELS,
    parcel_land_values,
    tract_land_values,
)


def test_parcel_land_values_filters_and_sums_records() -> None:
    assess = pd.DataFrame(
        {
            "loc_id": ["A", "A", "B", "C", "D", "E"],
            "use_code": ["101", "101", "102", "930", "130", "101"],
            "land_val": [43_560.0, 43_560.0, 50_000.0, 10_000.0, 87_120.0, 1_000.0],
            "lot_size_acres": [1.0, 1.0, 0.5, 2.0, 2.0, 0.001],
            "fy": [2026] * 6,
        }
    )
    points = pd.DataFrame({"loc_id": list("ABCDE"), "tract_geoid": ["t1"] * 5})
    p = parcel_land_values(assess, points).set_index("loc_id")
    assert set(p.index) == {"A", "D"}  # condo, exempt and tiny lot excluded
    assert p.loc["A", "value_per_sqft"] == pytest.approx(2.0)  # two records summed
    assert p.loc["D", "value_per_sqft"] == pytest.approx(1.0)


def test_tract_median_flag_and_missing() -> None:
    parcels = pd.DataFrame(
        {
            "tract_geoid": ["t1"] * MIN_PARCELS + ["t2"] * 2,
            "value_per_sqft": list(range(1, MIN_PARCELS + 1)) + [5.0, 7.0],
            "fy": 2026,
        }
    )
    t = tract_land_values(parcels, pd.Series(["t1", "t2", "t3"]))
    assert t.loc["t1", "median"] == pytest.approx(np.median(range(1, MIN_PARCELS + 1)))
    assert pd.isna(t.loc["t1", "flag"])
    assert t.loc["t2", "median"] == pytest.approx(6.0)
    assert t.loc["t2", "flag"] == FEW_FLAG
    assert np.isnan(t.loc["t3", "median"])
    assert t.loc["t3", "n"] == 0
