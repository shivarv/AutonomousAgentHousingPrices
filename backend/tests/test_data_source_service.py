import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.dao.data_source_dao import DataSourceDao
from app.services.data_source_service import DataSourceService
from pipeline.sources import DATA_SOURCES_MD, DATASETS, parse, render

ROW = {
    "key": "test_source",
    "name": "Test source",
    "url": "https://example.org/x.csv",
    "download_date": "2026-11-10",
    "licence": "public domain",
    "geography": "tract",
    "years": "2024",
    "file_path": "data/raw/test/x.csv",
    "columns": "a, b",
}


class _NoCommitSession:
    """Wrap the test session so the service's commit does not persist outside the test."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def commit(self) -> None:
        self._s.flush()

    def __getattr__(self, name):
        return getattr(self._s, name)


def _service(db_session: Session) -> DataSourceService:
    return DataSourceService(DataSourceDao(_NoCommitSession(db_session)))  # type: ignore[arg-type]


def test_sync_is_idempotent_upsert(db_session: Session) -> None:
    service = _service(db_session)
    assert service.sync_from_rows([ROW]) == 1
    service.sync_from_rows([{**ROW, "years": "2025"}])
    source = DataSourceDao(db_session).get_by_key("test_source")
    assert source is not None
    assert source.years == "2025"


def test_duplicate_keys_rejected(db_session: Session) -> None:
    with pytest.raises(ValidationError):
        _service(db_session).sync_from_rows([ROW, ROW])


def test_data_sources_md_round_trips_and_covers_registry() -> None:
    rows = parse(DATA_SOURCES_MD.read_text())
    assert {r["key"] for r in rows} == {d.key for d in DATASETS}
    assert parse(render(rows)) == rows
