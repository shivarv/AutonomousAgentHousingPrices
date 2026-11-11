"""Bulk write access used by the data pipeline (insert/upsert in batches, table replace)."""

from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Session

BATCH = 5000


def _batches(rows: Sequence[dict[str, Any]], size: int = BATCH) -> Iterable[Sequence[dict]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


class BulkDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        model: type[DeclarativeBase],
        rows: Sequence[dict[str, Any]],
        conflict_cols: list[str],
    ) -> int:
        for chunk in _batches(rows):
            stmt = insert(model).values(list(chunk))
            update = {c: stmt.excluded[c] for c in chunk[0] if c not in conflict_cols}
            stmt = (
                stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update)
                if update
                else stmt.on_conflict_do_nothing(index_elements=conflict_cols)
            )
            self.session.execute(stmt)
        self.session.flush()
        return len(rows)

    def replace(self, model: type[DeclarativeBase], rows: Sequence[dict[str, Any]]) -> int:
        """Delete every row of the table, then insert ``rows`` (for tables nothing references)."""
        self.session.execute(delete(model))
        for chunk in _batches(rows):
            self.session.execute(insert(model).values(list(chunk)))
        self.session.flush()
        return len(rows)

    def delete_where(self, model: type[DeclarativeBase], *criteria: Any) -> None:
        self.session.execute(delete(model).where(*criteria))
        self.session.flush()

    def count(self, model: type[DeclarativeBase]) -> int:
        return self.session.scalar(select(func.count()).select_from(model)) or 0
