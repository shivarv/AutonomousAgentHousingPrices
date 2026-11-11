from typing import Literal

from pydantic import BaseModel

from app.schemas.estimate import OFFICIAL_LABEL


class PitYear(BaseModel):
    """One year of the HUD Point-in-Time count for a CoC (or the state = sum of CoCs)."""

    year: int
    sheltered: int | None
    unsheltered: int | None
    total: int
    change_from_previous: int | None
    pct_change_from_previous: float | None
    emergency_shelter_beds: int | None
    transitional_beds: int | None
    safe_haven_beds: int | None
    total_year_round_beds: int | None


class CocHomelessness(BaseModel):
    coc_number: str
    coc_name: str
    label: Literal["official CoC count"] = OFFICIAL_LABEL
    geography: Literal["Continuum of Care"] = "Continuum of Care"
    latest_year: int
    latest: PitYear
    years: list[PitYear]
    sources: list[str]


class StateHomelessness(BaseModel):
    """Statewide figures are the sum of the official CoC counts (MA CoCs cover the state)."""

    label: Literal["official CoC count"] = OFFICIAL_LABEL
    geography: Literal["sum of Massachusetts CoCs"] = "sum of Massachusetts CoCs"
    coc_count: int
    years: list[PitYear]


class HomelessnessOverview(BaseModel):
    state: StateHomelessness
    cocs: list[CocHomelessness]
