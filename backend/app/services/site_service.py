"""Candidate construction sites: ranked lists, best site for a filter, site detail."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.dao.site_dao import SiteDao
from app.schemas.estimate import HomelessFigure
from app.schemas.site import SiteDetail, SiteList, SiteRing, SiteSummary

MAX_LIMIT = 500
RING_METHOD = (
    "sum of modelled tract homeless estimates, weighted by the share of each tract's area "
    "inside the ring"
)
SITE_SOURCES = [
    "massgis_parcels",
    "massgis_openspace",
    "massgis_wetlands",
    "massgis_flood",
    "massgis_mbta3a",
    "hud_chas",
    "hud_pit",
    "acs5",
    "mbta_gtfs",
    "rta_gtfs",
    "osm_shelters",
]


def ring_tag(r: float) -> str:
    return f"{r:g}km".replace(".", "_")


class SiteService:
    def __init__(self, dao: SiteDao) -> None:
        self.dao = dao
        self._year: int | None = None

    def _homeless(self, value: float | None) -> HomelessFigure:
        if self._year is None:
            self._year = self.dao.homeless_estimate_year()
        return HomelessFigure.estimate(
            None if value is None else round(float(value), 1), self._year, RING_METHOD
        )

    def _summary(self, r: Any) -> dict[str, Any]:
        f = r.features
        return {
            "id": r.id,
            "rank_state": r.rank_state,
            "rank_county": r.rank_county,
            "score": r.score,
            "loc_id": r.loc_id,
            "municipality_geoid": r.municipality_geoid,
            "municipality": r.municipality_name,
            "county_geoid": r.county_geoid,
            "county": r.county_name,
            "lat": r.centroid_lat,
            "lon": r.centroid_lon,
            "lot_size_acres": round(r.lot_size_acres, 3),
            "use_code": r.use_code,
            "use_description": f.get("use_description"),
            "in_mbta3a_district": r.in_mbta3a_district,
            "need_index_5km": f.get("need_index_5km"),
            "affordable_gap_eli_5km": f.get("gap_eli_5km"),
            "homeless_5km": self._homeless(f.get("homeless_est_5km")),
            "nearest_stop_km": f.get("nearest_stop_km"),
            "est_land_cost": f.get("est_land_cost"),
            "flags": list(r.flags or []),
            "summary": r.summary,
        }

    @staticmethod
    def _check(limit: int, offset: int) -> None:
        if not 1 <= limit <= MAX_LIMIT:
            raise ValidationError(f"limit must be 1-{MAX_LIMIT}")
        if offset < 0:
            raise ValidationError("offset must be >= 0")

    def list(
        self, county: str | None, municipality: str | None, limit: int, offset: int = 0
    ) -> SiteList:
        self._check(limit, offset)
        rows = self.dao.list(county, municipality, limit, offset)
        return SiteList(
            total=self.dao.count(county, municipality),
            offset=offset,
            sites=[SiteSummary(**self._summary(r)) for r in rows],
        )

    def best(self, county: str | None, municipality: str | None, offset: int = 0) -> SiteDetail:
        """Top-ranked site for the filter; offset 1, 2, ... steps through the next best."""
        self._check(1, offset)
        rows = self.dao.list(county, municipality, 1, offset)
        if not rows:
            raise NotFoundError("no candidate site matches this filter")
        return self.detail(rows[0].id)

    def detail(self, site_id: int) -> SiteDetail:
        r = self.dao.get(site_id)
        if r is None:
            raise NotFoundError(f"no site with id {site_id}")
        run = self.dao.scoring_run(r.model_run_id)
        params = run.params if run else {}
        radii = params.get("radii_km", [])
        f = r.features
        rings = [
            SiteRing(
                radius_km=rad,
                need_index=f.get(f"need_index_{ring_tag(rad)}"),
                affordable_gap_eli=f.get(f"gap_eli_{ring_tag(rad)}"),
                homeless=self._homeless(f.get(f"homeless_est_{ring_tag(rad)}")),
                population=f.get(f"population_{ring_tag(rad)}"),
                shelters=f.get(f"shelters_{ring_tag(rad)}"),
            )
            for rad in radii
        ]
        # homeless ring values travel only inside HomelessFigure (always labelled)
        features = {k: v for k, v in f.items() if not k.startswith("homeless_est")}
        return SiteDetail(
            **self._summary(r),
            boundary=r.boundary,
            rings=rings,
            components=r.components,
            weights=params.get("weights", {}),
            component_descriptions=params.get("descriptions", {}),
            features=features,
            overlaps={
                "open_space": r.openspace_overlap,
                "wetlands": r.wetland_overlap,
                "flood_zone_100yr": r.flood_overlap,
            },
            land_value=float(r.land_value) if r.land_value is not None else None,
            fiscal_year=r.fiscal_year,
            sources=SITE_SOURCES,
        )
