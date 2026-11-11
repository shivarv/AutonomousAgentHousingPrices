from datetime import date

from app.core.exceptions import ValidationError
from app.dao.data_source_dao import DataSourceDao
from app.schemas.data_source import DataSourceRead


class DataSourceService:
    def __init__(self, dao: DataSourceDao) -> None:
        self.dao = dao

    def list_sources(self) -> list[DataSourceRead]:
        return [DataSourceRead.model_validate(s) for s in self.dao.list_all()]

    def sync_from_rows(self, rows: list[dict[str, str]]) -> int:
        """Upsert parsed DATA_SOURCES.md rows (keyed by dataset key) and commit."""
        keys = [r["key"] for r in rows]
        if len(keys) != len(set(keys)):
            raise ValidationError("duplicate dataset keys in DATA_SOURCES.md")
        records = [
            {
                "key": r["key"],
                "name": r["name"],
                "url": r["url"],
                "download_date": date.fromisoformat(r["download_date"]),
                "licence": r["licence"],
                "geography": r["geography"],
                "years": r["years"],
                "file_path": r["file_path"],
                "columns_used": r["columns"],
            }
            for r in rows
        ]
        try:
            self.dao.upsert_many(records)
            self.dao.session.commit()
        except Exception:
            self.dao.session.rollback()
            raise
        return len(records)
