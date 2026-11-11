from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models import DataSource, Shelter


class ShelterDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self, coc_number: str | None = None) -> Sequence[Row[Any]]:
        stmt = (
            select(
                Shelter.id,
                Shelter.name,
                Shelter.shelter_type,
                Shelter.beds,
                Shelter.lat,
                Shelter.lon,
                Shelter.tract_geoid,
                Shelter.coc_number,
                DataSource.key.label("source_key"),
            )
            .join(DataSource, DataSource.id == Shelter.source_id)
            .order_by(Shelter.name)
        )
        if coc_number:
            stmt = stmt.where(Shelter.coc_number == coc_number)
        return self.session.execute(stmt).all()
