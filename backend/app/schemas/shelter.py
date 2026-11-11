from pydantic import BaseModel, ConfigDict


class ShelterRead(BaseModel):
    """A publicly listed shelter (OpenStreetMap). Domestic-violence shelters are never
    downloaded or shown; per-shelter bed counts are not published (beds is null)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    shelter_type: str
    beds: int | None
    lat: float
    lon: float
    tract_geoid: str | None
    coc_number: str | None
    source: str


class ShelterList(BaseModel):
    shelters: list[ShelterRead]
    note: str
