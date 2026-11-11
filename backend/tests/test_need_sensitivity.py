import pandas as pd
import pytest

from pipeline.index.components import COMPONENT_KEYS
from pipeline.index.sensitivity import ALTERNATIVES, stability


def test_three_alternatives_cover_all_components() -> None:
    assert len(ALTERNATIVES) == 3
    for _, weights in ALTERNATIVES.values():
        assert set(weights) == set(COMPONENT_KEYS)


def test_stability_identical_and_reversed() -> None:
    s = pd.Series({"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0})
    same = stability(s, s, top_n=2)
    assert same["top_n_overlap"] == 2
    assert same["spearman"] == pytest.approx(1.0)
    assert same["worst_alt_rank_of_main_top_n"] == 2
    rev = stability(s, -s, top_n=2)
    assert rev["top_n_overlap"] == 0
    assert rev["worst_alt_rank_of_main_top_n"] == 4


def test_stability_ignores_missing() -> None:
    main = pd.Series({"a": 2.0, "b": 1.0, "c": None})
    assert stability(main, main, top_n=1)["tracts_compared"] == 2
