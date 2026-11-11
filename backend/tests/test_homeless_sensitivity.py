import pandas as pd
import pytest

from pipeline.features.homeless_sensitivity import compare


def test_identical_allocations() -> None:
    s = pd.Series({"a": 5.0, "b": 3.0, "c": 2.0})
    r = compare(s, s, top_n=2)
    assert r["top_n_overlap"] == 2
    assert r["spearman"] == pytest.approx(1.0)
    assert r["share_reallocated"] == 0.0


def test_reallocated_share_and_overlap() -> None:
    main = pd.Series({"a": 6.0, "b": 3.0, "c": 1.0})
    alt = pd.Series({"a": 1.0, "b": 3.0, "c": 6.0})
    r = compare(main, alt, top_n=1)
    assert r["top_n_overlap"] == 0
    assert r["spearman"] == pytest.approx(-1.0)
    assert r["share_reallocated"] == pytest.approx(0.5)  # 5 of 10 people move
