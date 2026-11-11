"""Checks on the CHAS affordability metrics in the loaded database."""

from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        n = session.execute(
            text("SELECT count(*) FROM tract_metrics WHERE metric = 'affordable_gap_eli'")
        ).scalar()
        if not n:
            pytest.skip("affordability metrics not loaded")
        yield session
    finally:
        session.close()


def _pivot(db: Session, metrics: list[str]) -> dict[str, dict[str, float]]:
    rows = db.execute(
        text("SELECT tract_geoid, metric, value FROM tract_metrics WHERE metric = ANY(:m)"),
        {"m": metrics},
    ).all()
    out: dict[str, dict[str, float]] = {}
    for g, m, v in rows:
        out.setdefault(g, {})[m] = v
    return out


def test_every_tract_has_gap(db: Session) -> None:
    n_tracts = db.execute(text("SELECT count(*) FROM tracts")).scalar()
    n = db.execute(
        text(
            "SELECT count(*) FROM tract_metrics "
            "WHERE metric = 'affordable_gap_eli' AND value IS NOT NULL"
        )
    ).scalar()
    assert n == n_tracts


def test_gap_is_households_minus_available_units(db: Session) -> None:
    data = _pivot(
        db,
        [
            "eli_renter_households",
            "units_affordable_available_eli",
            "affordable_gap_eli",
            "vli_renter_households",
            "units_affordable_available_vli",
            "affordable_gap_vli",
        ],
    )
    for g, m in data.items():
        assert m["affordable_gap_eli"] == pytest.approx(
            m["eli_renter_households"] - m["units_affordable_available_eli"]
        ), g
        assert m["affordable_gap_vli"] == pytest.approx(
            m["vli_renter_households"] - m["units_affordable_available_vli"]
        ), g


def test_vli_includes_eli(db: Session) -> None:
    data = _pivot(db, ["eli_renter_households", "vli_renter_households"])
    assert all(m["vli_renter_households"] >= m["eli_renter_households"] for m in data.values())


@pytest.mark.parametrize(
    "metric",
    [
        "housing_units",
        "vacant_for_rent",
        "vacant_for_sale",
        "hud_assisted_units",
        "lihtc_low_income_units",
    ],
)
def test_context_metric_for_every_tract(db: Session, metric: str) -> None:
    n_tracts = db.execute(text("SELECT count(*) FROM tracts")).scalar()
    n = db.execute(
        text("SELECT count(DISTINCT tract_geoid) FROM tract_metrics WHERE metric = :m"),
        {"m": metric},
    ).scalar()
    assert n == n_tracts
