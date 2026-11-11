"""Modelled homeless estimates: allocation arithmetic and checks on the loaded database."""

from collections.abc import Iterator

import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from pipeline.features.homeless_estimate import FALLBACK_FLAG, allocate, latest_pit

TRACTS = pd.DataFrame({"geoid": ["a", "b", "c", "d"], "coc_number": ["X", "X", "Y", "Y"]})
PIT = pd.DataFrame(
    {
        "coc_number": ["X", "Y"],
        "year": 2025,
        "sheltered": [90, 7],
        "unsheltered": [10, 3],
        "total": [100, 10],
    }
)


def test_allocation_is_proportional_and_sums_to_coc() -> None:
    w = pd.Series({"a": 30.0, "b": 10.0, "c": 1.0, "d": 0.0})
    pop = pd.Series({"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0})
    a = allocate(TRACTS, w, pop, PIT).set_index("geoid")
    assert a.loc["a", "total"] == pytest.approx(75.0)
    assert a.loc["a", "sheltered"] == pytest.approx(67.5)
    assert a.loc["d", "total"] == 0.0
    sums = a.groupby("coc_number")[["sheltered", "unsheltered", "total"]].sum()
    assert sums.loc["X"].tolist() == pytest.approx([90, 10, 100])
    assert sums.loc["Y"].tolist() == pytest.approx([7, 3, 10])
    assert a.flag.isna().all()


def test_zero_weight_coc_falls_back_to_population_with_flag() -> None:
    w = pd.Series({"a": 1.0, "b": 1.0, "c": 0.0, "d": 0.0})
    pop = pd.Series({"a": 1.0, "b": 1.0, "c": 300.0, "d": 100.0})
    a = allocate(TRACTS, w, pop, PIT).set_index("geoid")
    assert a.loc["c", "total"] == pytest.approx(7.5)
    assert a.loc["c", "flag"] == FALLBACK_FLAG
    assert pd.isna(a.loc["a", "flag"])


def test_missing_weight_or_pit_is_an_error() -> None:
    w = pd.Series({"a": 1.0, "b": 1.0, "c": 1.0})
    with pytest.raises(ValueError):
        allocate(TRACTS, w, w, PIT)
    full = pd.Series({"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0})
    with pytest.raises(ValueError):
        allocate(TRACTS, full, full, PIT[PIT.coc_number == "X"])


def test_latest_pit_requires_consistent_parts() -> None:
    with pytest.raises(ValueError):
        latest_pit(PIT.assign(total=[101, 10]))
    assert len(latest_pit(PIT)) == 2


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        n = session.execute(
            text("SELECT count(*) FROM tract_metrics WHERE metric = 'homeless_estimate'")
        ).scalar()
        if not n:
            pytest.skip("homeless estimates not loaded")
        yield session
    finally:
        session.close()


@pytest.mark.parametrize(
    ("metric", "column"),
    [
        ("homeless_estimate", "total"),
        ("homeless_estimate_sheltered", "sheltered"),
        ("homeless_estimate_unsheltered", "unsheltered"),
    ],
)
def test_loaded_estimates_sum_to_official_coc_counts(db: Session, metric: str, column: str) -> None:
    rows = db.execute(
        text(
            f"SELECT h.coc_number, h.{column}, sum(m.value) FROM tract_metrics m "
            "JOIN tracts t ON t.geoid = m.tract_geoid "
            "JOIN homelessness_counts h ON h.coc_number = t.coc_number AND h.year = m.year "
            "WHERE m.metric = :m GROUP BY 1, 2"
        ),
        {"m": metric},
    ).all()
    n_cocs = db.execute(text("SELECT count(*) FROM cocs")).scalar()
    assert len(rows) == n_cocs
    for coc, official, est in rows:
        assert est == pytest.approx(official, abs=1e-6), coc


def test_loaded_estimates_are_labelled(db: Session) -> None:
    latest = db.execute(text("SELECT max(year) FROM homelessness_counts")).scalar()
    total, good = db.execute(
        text(
            "SELECT count(*), count(*) FILTER (WHERE is_estimate AND method LIKE 'ESTIMATE:%' "
            "AND year = :y AND value >= 0) "
            "FROM tract_metrics WHERE metric LIKE 'homeless_estimate%'"
        ),
        {"y": latest},
    ).one()
    tracts = db.execute(text("SELECT count(*) FROM tracts")).scalar()
    assert total == 3 * tracts
    assert good == total
