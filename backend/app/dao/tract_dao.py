from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models import (
    BostonNeighbourhood,
    Coc,
    County,
    DataSource,
    Municipality,
    Tract,
    TractMetric,
    TractMunicipality,
)


class TractDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def tracts(
        self,
        county: str | None = None,
        municipality: str | None = None,
        geoid: str | None = None,
    ) -> Sequence[Row[Any]]:
        """Tracts with names of their county, main town, CoC and neighbourhood. A town filter
        matches every tract with land in the town (tract_municipalities)."""
        stmt = (
            select(
                Tract.geoid,
                Tract.name,
                Tract.county_geoid,
                County.name.label("county_name"),
                Tract.municipality_geoid,
                Municipality.name.label("municipality_name"),
                Tract.coc_number,
                Coc.name.label("coc_name"),
                Tract.neighbourhood_id,
                BostonNeighbourhood.name.label("neighbourhood_name"),
                Tract.land_area_m2,
                Tract.centroid_lat,
                Tract.centroid_lon,
                Tract.boundary,
            )
            .join(County, County.geoid == Tract.county_geoid)
            .join(Municipality, Municipality.geoid == Tract.municipality_geoid)
            .join(Coc, Coc.coc_number == Tract.coc_number)
            .outerjoin(BostonNeighbourhood, BostonNeighbourhood.id == Tract.neighbourhood_id)
            .order_by(Tract.geoid)
        )
        if geoid:
            stmt = stmt.where(Tract.geoid == geoid)
        if county:
            stmt = stmt.where(Tract.county_geoid == county)
        if municipality:
            stmt = stmt.where(
                Tract.geoid.in_(
                    select(TractMunicipality.tract_geoid).where(
                        TractMunicipality.municipality_geoid == municipality
                    )
                )
            )
        return self.session.execute(stmt).all()

    def tract(self, geoid: str) -> Row[Any] | None:
        rows = self.tracts(geoid=geoid)
        return rows[0] if rows else None

    def metric_rows(
        self, metrics: Sequence[str] | None = None, geoid: str | None = None
    ) -> Sequence[Row[Any]]:
        stmt = select(
            TractMetric.tract_geoid,
            TractMetric.metric,
            TractMetric.year,
            TractMetric.value,
            TractMetric.is_estimate,
            TractMetric.method,
            TractMetric.flag,
            DataSource.key.label("source_key"),
        ).join(DataSource, DataSource.id == TractMetric.source_id)
        if metrics is not None:
            stmt = stmt.where(TractMetric.metric.in_(list(metrics)))
        if geoid is not None:
            stmt = stmt.where(TractMetric.tract_geoid == geoid)
        return self.session.execute(stmt).all()

    def municipality_shares(self, geoid: str) -> Sequence[Row[Any]]:
        return self.session.execute(
            select(
                TractMunicipality.municipality_geoid,
                Municipality.name,
                TractMunicipality.area_share,
                TractMunicipality.housing_share,
            )
            .join(Municipality, Municipality.geoid == TractMunicipality.municipality_geoid)
            .where(TractMunicipality.tract_geoid == geoid)
            .order_by(TractMunicipality.housing_share.desc())
        ).all()
