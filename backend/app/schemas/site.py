from typing import Any

from pydantic import BaseModel

from app.schemas.estimate import HomelessFigure


class SiteRing(BaseModel):
    radius_km: float
    need_index: float | None
    affordable_gap_eli: float | None  # > 0 shortage, < 0 surplus
    homeless: HomelessFigure
    population: float | None
    shelters: int | None


class SiteSummary(BaseModel):
    id: int
    rank_state: int
    rank_county: int
    score: float
    loc_id: str
    municipality_geoid: str
    municipality: str
    county_geoid: str
    county: str
    lat: float
    lon: float
    lot_size_acres: float
    use_code: str
    use_description: str | None
    in_mbta3a_district: bool
    need_index_5km: float | None
    affordable_gap_eli_5km: float | None
    homeless_5km: HomelessFigure
    nearest_stop_km: float | None
    est_land_cost: float | None
    flags: list[str]
    summary: str


class SiteList(BaseModel):
    total: int
    offset: int
    sites: list[SiteSummary]


class SiteDetail(SiteSummary):
    boundary: dict[str, Any]
    rings: list[SiteRing]
    components: dict[str, float | None]
    weights: dict[str, float]
    component_descriptions: dict[str, str]
    features: dict[str, Any]
    overlaps: dict[str, float]
    land_value: float | None
    fiscal_year: int | None
    sources: list[str]
