"""Read access to areas (counties, towns, CoCs, Boston neighbourhoods, state) and their
aggregated metrics."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models import (
    AreaMetric,
    BostonNeighbourhood,
    Coc,
    CocMunicipality,
    County,
    DataSource,
    Municipality,
    Tract,
)

AREA_MODELS = {
    "county": (County, County.geoid),
    "municipality": (Municipality, Municipality.geoid),
    "coc": (Coc, Coc.coc_number),
    "neighbourhood": (BostonNeighbourhood, BostonNeighbourhood.id),
}
TRACT_AREA_COLUMN = {
    "county": Tract.county_geoid,
    "municipality": Tract.municipality_geoid,
    "coc": Tract.coc_number,
    "neighbourhood": Tract.neighbourhood_id,
}


class AreaDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def area_rows(self, level: str, with_boundary: bool = True) -> list[dict[str, Any]]:
        """id, name (and boundary) for every area at ``level`` (not tract/state)."""
        model, key = AREA_MODELS[level]
        cols = [key.label("id"), model.name.label("name")]
        if with_boundary:
            cols.append(model.boundary.label("boundary"))
        if level == "municipality":
            cols.append(Municipality.county_geoid.label("county_geoid"))
        rows = self.session.execute(select(*cols).order_by(key)).all()
        return [dict(r._mapping) | {"id": str(r.id)} for r in rows]

    def area_name(self, level: str, area_id: str) -> str | None:
        model, key = AREA_MODELS[level]
        value: Any = int(area_id) if level == "neighbourhood" else area_id
        if level == "neighbourhood" and not area_id.isdigit():
            return None
        return self.session.scalar(select(model.name).where(key == value))

    def metrics(self, level: str, area_ids: Sequence[str]) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                AreaMetric.area_id,
                AreaMetric.metric,
                AreaMetric.year,
                AreaMetric.value,
                AreaMetric.is_estimate,
                AreaMetric.method,
                DataSource.key.label("source_key"),
            )
            .join(DataSource, DataSource.id == AreaMetric.source_id)
            .where(AreaMetric.level == level, AreaMetric.area_id.in_(list(area_ids)))
        ).all()

    def cocs_of(self, level: str, area_id: str) -> list[str]:
        """CoCs holding at least one tract of the area (tracts nest in one CoC each)."""
        if level == "state":
            return list(self.session.scalars(select(Coc.coc_number).order_by(Coc.coc_number)))
        if level == "coc":
            return [area_id]
        if level == "municipality":  # 37 small towns hold no tract of their own
            return list(
                self.session.scalars(
                    select(CocMunicipality.coc_number)
                    .where(CocMunicipality.municipality_geoid == area_id)
                    .order_by(CocMunicipality.coc_number)
                )
            )
        col = TRACT_AREA_COLUMN[level]
        value: Any = int(area_id) if level == "neighbourhood" else area_id
        return list(
            self.session.scalars(
                select(Tract.coc_number).where(col == value).distinct().order_by(Tract.coc_number)
            )
        )
