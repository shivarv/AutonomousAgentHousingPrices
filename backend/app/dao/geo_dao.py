"""Bulk reads for the in-memory spatial index (tracts, area boundaries, point layers)."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dao.area_dao import AreaDao
from app.models import (
    CocBedCount,
    DataSource,
    HomelessnessCount,
    Shelter,
    SubsidisedHousing,
    Tract,
    TractMetric,
    TractMunicipality,
)


class GeoDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def tracts(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            select(
                Tract.geoid,
                Tract.name,
                Tract.county_geoid,
                Tract.municipality_geoid,
                Tract.coc_number,
                Tract.neighbourhood_id,
                Tract.centroid_lat,
                Tract.centroid_lon,
                Tract.boundary,
            ).order_by(Tract.geoid)
        ).all()
        return [dict(r._mapping) for r in rows]

    def latest_tract_metrics(self, metrics: Sequence[str]) -> list[dict[str, Any]]:
        """One row per (tract, metric): the latest year."""
        rows = self.session.execute(
            select(
                TractMetric.tract_geoid,
                TractMetric.metric,
                TractMetric.year,
                TractMetric.value,
                TractMetric.method,
                DataSource.key.label("source_key"),
            )
            .join(DataSource, DataSource.id == TractMetric.source_id)
            .where(TractMetric.metric.in_(list(metrics)))
            .order_by(TractMetric.tract_geoid, TractMetric.metric, TractMetric.year.desc())
        ).all()
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for r in rows:
            if (r.tract_geoid, r.metric) not in seen:
                seen.add((r.tract_geoid, r.metric))
                out.append(dict(r._mapping))
        return out

    def areas(self, level: str) -> list[dict[str, Any]]:
        return AreaDao(self.session).area_rows(level)

    def shelters(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            select(Shelter.name, Shelter.shelter_type, Shelter.beds, Shelter.lat, Shelter.lon)
        ).all()
        return [dict(r._mapping) for r in rows]

    def subsidised(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            select(
                SubsidisedHousing.name,
                SubsidisedHousing.program,
                SubsidisedHousing.assisted_units,
                SubsidisedHousing.lat,
                SubsidisedHousing.lon,
            ).where(SubsidisedHousing.lat.is_not(None), SubsidisedHousing.lon.is_not(None))
        ).all()
        return [dict(r._mapping) for r in rows]

    def town_weights(self) -> list[dict[str, Any]]:
        """(tract, town, housing_share): how each tract's counts are apportioned to towns."""
        rows = self.session.execute(
            select(
                TractMunicipality.tract_geoid,
                TractMunicipality.municipality_geoid,
                TractMunicipality.housing_share,
            )
        ).all()
        return [dict(r._mapping) for r in rows]

    def latest_pit(self) -> dict[str, dict[str, Any]]:
        """Latest official PIT count per CoC, with that year's HIC year-round beds."""
        pit = self.session.execute(
            select(
                HomelessnessCount.coc_number,
                HomelessnessCount.year,
                HomelessnessCount.total,
                HomelessnessCount.sheltered,
                HomelessnessCount.unsheltered,
            ).order_by(HomelessnessCount.coc_number, HomelessnessCount.year.desc())
        ).all()
        beds = {
            (b.coc_number, b.year): b.total_year_round_beds
            for b in self.session.execute(
                select(CocBedCount.coc_number, CocBedCount.year, CocBedCount.total_year_round_beds)
            ).all()
        }
        out: dict[str, dict[str, Any]] = {}
        for r in pit:
            if r.coc_number not in out:
                out[r.coc_number] = dict(r._mapping) | {"beds": beds.get((r.coc_number, r.year))}
        return out
