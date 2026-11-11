from typing import Literal

from pydantic import BaseModel

from app.schemas.estimate import HomelessFigure
from app.schemas.homelessness import CocHomelessness, StateHomelessness
from app.schemas.metric import MetricValue

OverviewLevel = Literal["state", "county", "municipality"]


class ShelterBeds(BaseModel):
    """HUD Housing Inventory Count year-round beds; published per CoC only."""

    value: int | None
    year: int | None
    label: Literal["official CoC count"] = "official CoC count"
    geography: str
    source: str = "hud_hic"


class OverviewHomelessness(BaseModel):
    official_state: StateHomelessness | None = None
    official_cocs: list[CocHomelessness]
    area_estimate: HomelessFigure
    note: str


class StatsOverview(BaseModel):
    level: OverviewLevel
    id: str
    name: str
    metrics: dict[str, MetricValue]
    homelessness: OverviewHomelessness
    shelter_beds: ShelterBeds
