from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models import Coc, CocBedCount, DataSource, HomelessnessCount


class HomelessnessDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def pit_counts(self, coc_number: str | None = None) -> Sequence[Row[Any]]:
        """PIT rows joined to CoC name and source key, ordered by CoC then year."""
        stmt = (
            select(
                HomelessnessCount.coc_number,
                Coc.name.label("coc_name"),
                HomelessnessCount.year,
                HomelessnessCount.sheltered,
                HomelessnessCount.unsheltered,
                HomelessnessCount.total,
                DataSource.key.label("source_key"),
            )
            .join(Coc, Coc.coc_number == HomelessnessCount.coc_number)
            .join(DataSource, DataSource.id == HomelessnessCount.source_id)
            .order_by(HomelessnessCount.coc_number, HomelessnessCount.year)
        )
        if coc_number is not None:
            stmt = stmt.where(HomelessnessCount.coc_number == coc_number)
        return self.session.execute(stmt).all()

    def bed_counts(self, coc_number: str | None = None) -> Sequence[Row[Any]]:
        stmt = (
            select(
                CocBedCount.coc_number,
                CocBedCount.year,
                CocBedCount.emergency_shelter_beds,
                CocBedCount.transitional_beds,
                CocBedCount.safe_haven_beds,
                CocBedCount.total_year_round_beds,
                DataSource.key.label("source_key"),
            )
            .join(DataSource, DataSource.id == CocBedCount.source_id)
            .order_by(CocBedCount.coc_number, CocBedCount.year)
        )
        if coc_number is not None:
            stmt = stmt.where(CocBedCount.coc_number == coc_number)
        return self.session.execute(stmt).all()
