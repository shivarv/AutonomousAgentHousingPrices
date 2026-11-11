from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models import DataSource, Tract, TractMetric, TractMunicipality


class MetricDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def tract_metric_rows(self, metrics: Sequence[str] | None = None) -> Sequence[Row[Any]]:
        stmt = select(
            TractMetric.tract_geoid,
            TractMetric.metric,
            TractMetric.year,
            TractMetric.value,
            TractMetric.is_estimate,
            TractMetric.method,
            DataSource.key.label("source_key"),
        ).join(DataSource, DataSource.id == TractMetric.source_id)
        if metrics is not None:
            stmt = stmt.where(TractMetric.metric.in_(metrics))
        return self.session.execute(stmt).all()

    def tract_assignments(self) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                Tract.geoid,
                Tract.municipality_geoid,
                Tract.county_geoid,
                Tract.coc_number,
                Tract.neighbourhood_id,
            )
        ).all()

    def tract_municipality_rows(self) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                TractMunicipality.tract_geoid,
                TractMunicipality.municipality_geoid,
                TractMunicipality.area_share,
            )
        ).all()
