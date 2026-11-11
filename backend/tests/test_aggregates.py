"""Area totals must equal the sum of their tracts (checked on the loaded database)."""

from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory

LEVEL_COLUMN = {
    "county": "county_geoid",
    "coc": "coc_number",
}
METRICS = ["affordable_gap_eli", "affordable_gap_vli", "eli_renter_households", "population"]


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        if not session.execute(text("SELECT count(*) FROM area_metrics")).scalar():
            pytest.skip("area metrics not built")
        yield session
    finally:
        session.close()


def _state_total(db: Session, metric: str) -> float:
    return db.execute(
        text("SELECT value FROM area_metrics WHERE level='state' AND area_id='25' AND metric=:m"),
        {"m": metric},
    ).scalar()


@pytest.mark.parametrize("metric", METRICS)
def test_state_total_equals_tract_sum(db: Session, metric: str) -> None:
    tract_sum = db.execute(
        text("SELECT sum(value) FROM tract_metrics WHERE metric = :m"), {"m": metric}
    ).scalar()
    assert _state_total(db, metric) == pytest.approx(tract_sum)


@pytest.mark.parametrize("level", list(LEVEL_COLUMN))
@pytest.mark.parametrize("metric", METRICS)
def test_area_totals_equal_tract_sums(db: Session, level: str, metric: str) -> None:
    col = LEVEL_COLUMN[level]
    rows = db.execute(
        text(
            f"SELECT t.{col}, sum(m.value) FROM tract_metrics m "
            f"JOIN tracts t ON t.geoid = m.tract_geoid WHERE m.metric = :m GROUP BY t.{col}"
        ),
        {"m": metric},
    ).all()
    stored = dict(
        db.execute(
            text("SELECT area_id, value FROM area_metrics WHERE level=:l AND metric=:m"),
            {"l": level, "m": metric},
        ).all()
    )
    assert len(stored) == len(rows)
    for area, total in rows:
        assert stored[str(area)] == pytest.approx(total), area
    assert sum(stored.values()) == pytest.approx(_state_total(db, metric))


@pytest.mark.parametrize("metric", METRICS)
def test_municipality_totals_equal_weighted_tract_sums(db: Session, metric: str) -> None:
    rows = dict(
        db.execute(
            text(
                "SELECT tm.municipality_geoid, sum(m.value * tm.housing_share) "
                "FROM tract_metrics m JOIN tract_municipalities tm "
                "ON tm.tract_geoid = m.tract_geoid "
                "WHERE m.metric = :m AND tm.housing_share > 0 GROUP BY 1"
            ),
            {"m": metric},
        ).all()
    )
    stored = dict(
        db.execute(
            text(
                "SELECT area_id, value FROM area_metrics WHERE level='municipality' AND metric=:m"
            ),
            {"m": metric},
        ).all()
    )
    assert stored.keys() == rows.keys()
    for area, total in rows.items():
        assert stored[area] == pytest.approx(total), area
    assert sum(stored.values()) == pytest.approx(_state_total(db, metric))


def test_town_weights_sum_to_one_per_tract(db: Session) -> None:
    bad = db.execute(
        text(
            "SELECT tract_geoid FROM tract_municipalities GROUP BY 1 "
            "HAVING abs(sum(coalesce(housing_share, -1)) - 1) > 1e-9"
        )
    ).all()
    assert bad == []


def test_351_municipalities_and_14_counties_aggregated(db: Session) -> None:
    counts = dict(
        db.execute(
            text(
                "SELECT level, count(DISTINCT area_id) FROM area_metrics "
                "WHERE metric='affordable_gap_eli' GROUP BY level"
            )
        ).all()
    )
    assert counts["county"] == 14
    assert counts["coc"] == 11
    assert counts["state"] == 1
    assert counts["municipality"] == 351
