from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.estimate import HomelessFigure
from app.schemas.metric import MetricValue


class TractFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: dict[str, Any]
    properties: dict[str, Any]


class MetricInfo(BaseModel):
    year: int | None
    source: str | None
    label: str | None = None


class TractFeatureCollection(BaseModel):
    """Tract boundaries (simplified) with the Need Index and key metrics as properties.
    ``homeless_estimate`` is a modelled estimate (see ``metrics`` and the methodology)."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[TractFeature]
    metrics: dict[str, MetricInfo]


class MunicipalityShare(BaseModel):
    geoid: str
    name: str
    area_share: float
    housing_share: float | None


class TractDetail(BaseModel):
    geoid: str
    name: str
    county_geoid: str
    county_name: str
    municipality_geoid: str
    municipality_name: str
    municipalities: list[MunicipalityShare]
    coc_number: str
    coc_name: str
    neighbourhood_id: int | None
    neighbourhood_name: str | None
    centroid_lat: float
    centroid_lon: float
    land_area_km2: float
    boundary: dict[str, Any]
    homeless: HomelessFigure
    metrics: dict[str, MetricValue]
    flags: dict[str, str]
