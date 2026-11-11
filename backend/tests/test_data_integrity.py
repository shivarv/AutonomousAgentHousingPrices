"""Integrity checks on the loaded `housing` database (skipped if the pipeline hasn't run)."""

import json
from collections.abc import Iterator

import geopandas as gpd
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.models import (
    Coc,
    County,
    HomelessnessCount,
    Municipality,
    Tract,
    TractMetric,
)
from pipeline.drops import DROPS_FILE
from pipeline.paths import RAW_DIR

TIGER_TRACTS = RAW_DIR / "tiger/tl_2026_25_tract.zip"
COC_ZIP = RAW_DIR / "hud_coc/CoC_GIS_State_Shapefile_MA_2025.zip"


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        if not session.scalar(select(func.count()).select_from(Tract)):
            pytest.skip("housing database not loaded (run pipeline.load)")
        yield session
    finally:
        session.close()


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_tract_count_matches_tiger(db: Session) -> None:
    if not TIGER_TRACTS.exists():
        pytest.skip("TIGER file not downloaded")
    tiger = gpd.read_file(TIGER_TRACTS, ignore_geometry=True)
    assert _count(db, Tract) == len(tiger)
    loaded = set(db.scalars(select(Tract.geoid)))
    assert loaded == set(tiger.GEOID)


def test_351_municipalities_and_14_counties(db: Session) -> None:
    assert _count(db, Municipality) == 351
    assert _count(db, County) == 14


def test_every_ma_coc_present(db: Session) -> None:
    import zipfile

    with zipfile.ZipFile(COC_ZIP) as zf:
        expected = {
            n.split("/")[-1].removesuffix(".shp").replace("_", "-")
            for n in zf.namelist()
            if n.endswith(".shp")
        }
    assert set(db.scalars(select(Coc.coc_number))) == expected
    latest = db.scalar(select(func.max(HomelessnessCount.year)))
    with_counts = set(
        db.scalars(select(HomelessnessCount.coc_number).where(HomelessnessCount.year == latest))
    )
    assert with_counts == expected


def test_no_duplicate_geoids(db: Session) -> None:
    dupes = db.execute(text("SELECT geoid FROM tracts GROUP BY geoid HAVING count(*) > 1")).all()
    assert dupes == []


def test_every_tract_assigned_to_town_county_coc(db: Session) -> None:
    missing = db.scalar(
        select(func.count())
        .select_from(Tract)
        .where(
            (Tract.municipality_geoid.is_(None))
            | (Tract.coc_number.is_(None))
            | (Tract.county_geoid.is_(None))
        )
    )
    assert missing == 0


def test_every_metric_row_has_a_source(db: Session) -> None:
    orphan = db.scalar(
        text(
            "SELECT count(*) FROM tract_metrics m LEFT JOIN data_sources s "
            "ON s.id = m.source_id WHERE s.id IS NULL"
        )
    )
    assert orphan == 0
    assert _count(db, TractMetric) > 0


def test_estimates_carry_a_method(db: Session) -> None:
    bad = db.scalar(
        select(func.count())
        .select_from(TractMetric)
        .where(TractMetric.is_estimate.is_(True), TractMetric.method.is_(None))
    )
    assert bad == 0


def test_dropped_rows_logged() -> None:
    assert DROPS_FILE.exists(), "cleaning steps must write the dropped-row log"
    drops = json.loads(DROPS_FILE.read_text())
    assert {"geography", "context", "homelessness"} <= set(drops)
    assert all(isinstance(n, int) for reasons in drops.values() for n in reasons.values())
