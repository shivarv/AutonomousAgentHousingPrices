from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.data_source import DataSource


class DataSourceDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> Sequence[DataSource]:
        return self.session.scalars(select(DataSource).order_by(DataSource.id)).all()

    def get_by_key(self, key: str) -> DataSource | None:
        return self.session.scalar(select(DataSource).where(DataSource.key == key))

    def upsert_many(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        stmt = insert(DataSource).values(rows)
        update_cols = {c: stmt.excluded[c] for c in rows[0] if c != "key"}
        self.session.execute(stmt.on_conflict_do_update(index_elements=["key"], set_=update_cols))
        self.session.flush()
