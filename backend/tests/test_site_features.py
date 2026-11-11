import numpy as np
import pandas as pd
import pytest

from pipeline.sites import features as F


def test_ring_tag() -> None:
    assert F.ring_tag(1.5) == "1_5km"
    assert F.ring_tag(5.0) == "5km"


def test_land_cost_uses_tract_median_and_keeps_missing() -> None:
    sites = pd.DataFrame({"tract_geoid": ["t1", "t2"], "lot_size_acres": [2.0, 1.0]})
    wide = pd.DataFrame(
        {"land_value_per_sqft": [10.0, np.nan], "land_flag": [None, None]},
        index=pd.Index(["t1", "t2"], name="tract_geoid"),
    )
    out = F.land_cost(sites, wide)
    assert out.est_land_cost.iloc[0] == pytest.approx(10.0 * 2 * 43_560)
    assert np.isnan(out.est_land_cost.iloc[1])
