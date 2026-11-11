from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, Select, func, select
from sqlalchemy.orm import Session

from app.models import (
    County,
    DataSource,
    ModelRun,
    Municipality,
    Parcel,
    SiteCandidate,
    TractMetric,
)


class SiteDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _base(self, with_boundary: bool) -> Select[Any]:
        cols = [
            SiteCandidate.id,
            SiteCandidate.score,
            SiteCandidate.rank_state,
            SiteCandidate.rank_county,
            SiteCandidate.features,
            SiteCandidate.components,
            SiteCandidate.flags,
            SiteCandidate.summary,
            SiteCandidate.model_run_id,
            Parcel.loc_id,
            Parcel.use_code,
            Parcel.lot_size_acres,
            Parcel.centroid_lat,
            Parcel.centroid_lon,
            Parcel.in_mbta3a_district,
            Parcel.openspace_overlap,
            Parcel.wetland_overlap,
            Parcel.flood_overlap,
            Parcel.land_value,
            Parcel.fiscal_year,
            Parcel.municipality_geoid,
            Municipality.name.label("municipality_name"),
            Municipality.county_geoid,
            County.name.label("county_name"),
        ]
        if with_boundary:
            cols.append(Parcel.boundary)
        return (
            select(*cols)
            .join(Parcel, Parcel.loc_id == SiteCandidate.parcel_loc_id)
            .join(Municipality, Municipality.geoid == Parcel.municipality_geoid)
            .join(County, County.geoid == Municipality.county_geoid)
        )

    def list(
        self,
        county: str | None,
        municipality: str | None,
        limit: int,
        offset: int = 0,
        with_boundary: bool = False,
    ) -> Sequence[Row[Any]]:
        stmt = self._base(with_boundary)
        if county:
            stmt = stmt.where(Municipality.county_geoid == county)
        if municipality:
            stmt = stmt.where(Parcel.municipality_geoid == municipality)
        stmt = stmt.order_by(SiteCandidate.rank_state).offset(offset).limit(limit)
        return self.session.execute(stmt).all()

    def get(self, site_id: int) -> Row[Any] | None:
        return self.session.execute(
            self._base(True).where(SiteCandidate.id == site_id)
        ).one_or_none()

    def count(self, county: str | None, municipality: str | None) -> int:
        stmt = (
            select(func.count())
            .select_from(SiteCandidate)
            .join(Parcel, Parcel.loc_id == SiteCandidate.parcel_loc_id)
            .join(Municipality, Municipality.geoid == Parcel.municipality_geoid)
        )
        if county:
            stmt = stmt.where(Municipality.county_geoid == county)
        if municipality:
            stmt = stmt.where(Parcel.municipality_geoid == municipality)
        return self.session.scalar(stmt) or 0

    def scoring_run(self, run_id: int) -> ModelRun | None:
        return self.session.get(ModelRun, run_id)

    def homeless_estimate_year(self) -> int | None:
        return self.session.scalar(
            select(func.max(TractMetric.year)).where(TractMetric.metric == "homeless_estimate")
        )

    def metric_provenance(self, metrics: Sequence[str]) -> dict[str, tuple[int, str]]:
        """Latest year and source key of each tract metric (inputs of the site features)."""
        rows = self.session.execute(
            select(TractMetric.metric, func.max(TractMetric.year), DataSource.key)
            .join(DataSource, DataSource.id == TractMetric.source_id)
            .where(TractMetric.metric.in_(metrics))
            .group_by(TractMetric.metric, DataSource.key)
        ).all()
        return {m: (int(y), k) for m, y, k in rows}
