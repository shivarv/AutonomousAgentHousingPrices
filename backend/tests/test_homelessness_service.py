"""Official homelessness layer: trend arithmetic (fake DAO) and checks on the loaded data."""

from collections import namedtuple
from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.core.exceptions import NotFoundError
from app.dao.homelessness_dao import HomelessnessDao
from app.services.homelessness_service import HomelessnessService

Pit = namedtuple("Pit", "coc_number coc_name year sheltered unsheltered total source_key")
Bed = namedtuple(
    "Bed",
    "coc_number year emergency_shelter_beds transitional_beds safe_haven_beds "
    "total_year_round_beds source_key",
)


class FakeDao:
    def pit_counts(self, coc_number=None):
        rows = [
            Pit("MA-1", "A", 2023, 90, 10, 100, "hud_pit"),
            Pit("MA-1", "A", 2024, 110, 10, 120, "hud_pit"),
            Pit("MA-1", "A", 2025, 100, 8, 108, "hud_pit"),
            Pit("MA-2", "B", 2024, 40, 10, 50, "hud_pit"),
            Pit("MA-2", "B", 2025, 45, None, 60, "hud_pit"),
        ]
        return [r for r in rows if coc_number in (None, r.coc_number)]

    def bed_counts(self, coc_number=None):
        rows = [
            Bed("MA-1", 2025, 80, 10, 0, 90, "hud_hic"),
            Bed("MA-2", 2025, 30, 5, 0, 35, "hud_hic"),
        ]
        return [r for r in rows if coc_number in (None, r.coc_number)]


def _svc() -> HomelessnessService:
    return HomelessnessService(FakeDao())  # type: ignore[arg-type]


def test_coc_trend_and_beds() -> None:
    c = _svc().coc("MA-1")
    assert c.label == "official CoC count"
    assert c.latest_year == 2025
    assert c.latest.change_from_previous == -12
    assert c.latest.pct_change_from_previous == pytest.approx(-10.0)
    assert c.latest.total_year_round_beds == 90
    assert c.years[0].change_from_previous is None
    assert c.sources == ["hud_hic", "hud_pit"]


def test_unknown_coc() -> None:
    with pytest.raises(NotFoundError):
        _svc().coc("MA-999")


def test_state_sums_only_complete_years_and_keeps_missing_parts_missing() -> None:
    state = _svc().overview().state
    assert [y.year for y in state.years] == [2024, 2025]  # 2023 lacks MA-2
    y2025 = state.years[-1]
    assert y2025.total == 168
    assert y2025.sheltered == 145
    assert y2025.unsheltered is None  # MA-2 unsheltered missing -> no partial sum
    assert y2025.total_year_round_beds == 125
    assert y2025.change_from_previous == 168 - 170


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        if not session.execute(text("SELECT count(*) FROM homelessness_counts")).scalar():
            pytest.skip("homelessness counts not loaded")
        yield session
    finally:
        session.close()


def test_loaded_every_coc_has_latest_year_and_state_is_sum(db: Session) -> None:
    ov = HomelessnessService(HomelessnessDao(db)).overview()
    n_cocs = db.execute(text("SELECT count(*) FROM cocs")).scalar()
    assert len(ov.cocs) == n_cocs
    latest = max(c.latest_year for c in ov.cocs)
    assert all(c.latest_year == latest for c in ov.cocs)
    state_latest = ov.state.years[-1]
    assert state_latest.year == latest
    assert state_latest.total == sum(c.latest.total for c in ov.cocs)
    assert state_latest.total_year_round_beds is not None
