from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.estimate import HomelessFigure

AreaLevel = Literal["tract", "neighbourhood", "municipality", "county", "coc"]
GapStatus = Literal["shortage", "surplus", "balanced"]


class AreaFigures(BaseModel):
    """Totals for a ring or an area. Counts of households and units are CHAS 2018-2022 /
    ACS; homeless figures are estimates except at CoC level (official PIT count)."""

    population: float | None
    homeless: HomelessFigure
    at_risk_households: float | None = Field(
        description="extremely-low-income renter households with severe rent burden"
    )
    eli_renter_households: float | None
    affordable_units_available: float | None = Field(
        description="units affordable and available to extremely-low-income renters"
    )
    affordable_gap: float | None = Field(description="ELI renters minus units; > 0 = shortage")
    gap_status: GapStatus | None
    subsidised_units: float | None = Field(
        description="HUD-assisted plus LIHTC low-income units (programmes can overlap)"
    )
    need_index: float | None
    shelters: int
    shelter_beds: int | None
    tract_count: int


class RingStats(AreaFigures):
    radius_km: float


class AreaStatsRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    radii_km: list[float] = Field(default=[1.5, 5.0, 15.0], min_length=1, max_length=3)


class NearbyTract(BaseModel):
    geoid: str
    lat: float
    lon: float
    homeless: HomelessFigure


class NearbyShelter(BaseModel):
    name: str
    shelter_type: str
    beds: int | None
    lat: float
    lon: float


class AreaStatsResponse(BaseModel):
    lat: float
    lon: float
    rings: list[RingStats]
    nearby_tracts: list[NearbyTract]
    nearby_shelters: list[NearbyShelter]
    sources: dict[str, dict[str, Any]]
    notes: list[str]


class AreaRef(BaseModel):
    id: str
    name: str


class AreaAt(BaseModel):
    """The area of ``level`` containing a point. At level=coc the homeless figure is the
    official PIT count; at every other level it is the sum of tract estimates."""

    level: AreaLevel
    id: str
    name: str
    boundary: dict[str, Any]
    neighbours: list[AreaRef]
    figures: AreaFigures
    homeless_estimate_sum: HomelessFigure
    homeless_basis: Literal["official CoC count", "sum of tract estimates"]
    note: str
