"""Need Index: weighting arithmetic and checks on the loaded database."""

from collections.abc import Iterator

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from pipeline.index.need_index import index_from_scores

COLS = ["a", "b", "c"]
EQUAL = {"a": 1.0, "b": 1.0, "c": 1.0}


def _scores() -> pd.DataFrame:
    return pd.DataFrame(
        {"a": [1.0, 0.0, 0.5, np.nan], "b": [1.0, 0.0, np.nan, np.nan], "c": [1.0, 0.0, 0.0, 0.2]},
        index=["full_high", "full_low", "one_missing", "too_few"],
    )


def test_equal_weights_and_range() -> None:
    idx = index_from_scores(_scores(), EQUAL, min_components=2)
    assert idx.loc["full_high", "need_index"] == pytest.approx(100.0)
    assert idx.loc["full_low", "need_index"] == pytest.approx(0.0)
    assert idx.need_index.dropna().between(0, 100).all()
    assert pd.isna(idx.loc["full_high", "flag"])


def test_missing_component_renormalises_and_flags() -> None:
    idx = index_from_scores(_scores(), EQUAL, min_components=2)
    assert idx.loc["one_missing", "need_index"] == pytest.approx(25.0)
    assert "b" in idx.loc["one_missing", "flag"]
    assert idx.loc["one_missing", "n_used"] == 2


def test_below_minimum_is_null_with_flag() -> None:
    idx = index_from_scores(_scores(), EQUAL, min_components=2)
    assert np.isnan(idx.loc["too_few", "need_index"])
    assert idx.loc["too_few", "flag"].startswith("index not computed")


def test_unequal_weights_and_zero_weight_excluded() -> None:
    idx = index_from_scores(_scores(), {"a": 3.0, "b": 0.0, "c": 1.0}, min_components=1)
    assert idx.loc["one_missing", "need_index"] == pytest.approx(100 * 1.5 / 4)
    # b has weight 0, so it is not "missing" for one_missing
    assert pd.isna(idx.loc["one_missing", "flag"])


def test_invalid_weights() -> None:
    with pytest.raises(ValueError):
        index_from_scores(_scores(), {"a": 0.0, "b": 0.0, "c": 0.0})
    with pytest.raises(ValueError):
        index_from_scores(_scores(), {"a": -1.0, "b": 1.0, "c": 1.0})


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        if not session.execute(
            text("SELECT count(*) FROM tract_metrics WHERE metric = 'need_index'")
        ).scalar():
            pytest.skip("need index not loaded")
        yield session
    finally:
        session.close()


def test_loaded_index_range_and_documented_gaps(db: Session) -> None:
    n_tracts = db.execute(text("SELECT count(*) FROM tracts")).scalar()
    total, valid, bad_range, undocumented = db.execute(
        text(
            "SELECT count(*), count(value), count(*) FILTER (WHERE value < 0 OR value > 100), "
            "count(*) FILTER (WHERE value IS NULL AND flag IS NULL) "
            "FROM tract_metrics WHERE metric = 'need_index'"
        )
    ).one()
    assert total == n_tracts
    assert bad_range == 0
    assert undocumented == 0
    assert valid >= 0.95 * n_tracts


def test_loaded_scores_within_0_1(db: Session) -> None:
    bad = db.execute(
        text(
            "SELECT count(*) FROM tract_metrics WHERE metric LIKE 'need_score_%' "
            "AND (value < 0 OR value > 1)"
        )
    ).scalar()
    n_metrics = db.execute(
        text("SELECT count(DISTINCT metric) FROM tract_metrics WHERE metric LIKE 'need_score_%'")
    ).scalar()
    assert bad == 0
    assert n_metrics == 8
