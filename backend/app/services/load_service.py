"""Loads cleaned pipeline tables into Postgres in one transaction per call."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import DeclarativeBase

from app.core.exceptions import ValidationError
from app.dao.bulk_dao import BulkDao
from app.dao.data_source_dao import DataSourceDao


def _clean_value(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):  # numpy scalar
        v = v.item()
        if isinstance(v, float) and math.isnan(v):
            return None
    try:
        import pandas as pd

        if v is pd.NA or v is pd.NaT:
            return None
    except ImportError:  # pragma: no cover
        pass
    return v


class LoadService:
    def __init__(self, bulk: BulkDao, sources: DataSourceDao) -> None:
        self.bulk = bulk
        self.sources = sources
        self._source_ids: dict[str, int] = {}

    def source_id(self, key: str) -> int:
        if key not in self._source_ids:
            src = self.sources.get_by_key(key)
            if src is None:
                raise ValidationError(f"data source '{key}' missing: run pipeline.load_sources")
            self._source_ids[key] = src.id
        return self._source_ids[key]

    def _rows(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in records:
            row = {k: _clean_value(v) for k, v in r.items()}
            if "source_key" in row:
                row["source_id"] = self.source_id(row.pop("source_key"))
            out.append(row)
        return out

    def _run(self, fn: Callable[[], int]) -> int:
        try:
            n = fn()
            self.bulk.session.commit()
            return n
        except Exception:
            self.bulk.session.rollback()
            raise

    def upsert(
        self, model: type[DeclarativeBase], records: list[dict[str, Any]], conflict: list[str]
    ) -> int:
        return self._run(lambda: self.bulk.upsert(model, self._rows(records), conflict))

    def replace(self, model: type[DeclarativeBase], records: list[dict[str, Any]]) -> int:
        return self._run(lambda: self.bulk.replace(model, self._rows(records)))

    def replace_metrics(self, model: type[DeclarativeBase], records: list[dict[str, Any]]) -> int:
        """Upsert tract metrics; rows must all carry a source (never sourceless numbers)."""
        rows = self._rows(records)
        if any(r.get("source_id") is None for r in rows):
            raise ValidationError("every metric row needs a source")
        return self._run(lambda: self.bulk.upsert(model, rows, ["tract_geoid", "metric", "year"]))
