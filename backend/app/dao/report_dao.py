"""Read-only queries that feed the generated CSV/markdown reports."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models import AreaMetric, County, Municipality, Tract, TractMetric


class ReportDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def tract_metric_values(self, metrics: Sequence[str]) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                TractMetric.tract_geoid,
                TractMetric.metric,
                TractMetric.value,
                TractMetric.flag,
            ).where(TractMetric.metric.in_(metrics))
        ).all()

    def tracts(self) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                Tract.geoid,
                Tract.name.label("tract_name"),
                Tract.county_geoid,
                County.name.label("county"),
                Tract.municipality_geoid,
                Municipality.name.label("municipality"),
                Tract.coc_number,
            )
            .join(County, County.geoid == Tract.county_geoid)
            .join(Municipality, Municipality.geoid == Tract.municipality_geoid)
        ).all()

    def municipalities(self) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                Municipality.geoid,
                Municipality.name.label("municipality"),
                County.name.label("county"),
            ).join(County, County.geoid == Municipality.county_geoid)
        ).all()

    def area_metric_values(self, level: str, metrics: Sequence[str]) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                AreaMetric.area_id,
                AreaMetric.metric,
                AreaMetric.value,
                AreaMetric.tract_count,
            ).where(AreaMetric.level == level, AreaMetric.metric.in_(metrics))
        ).all()
