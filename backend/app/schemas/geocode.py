from pydantic import BaseModel


class GeocodeMatch(BaseModel):
    address: str
    lat: float
    lon: float


class GeocodeResult(BaseModel):
    query: str
    matches: list[GeocodeMatch]
    source: str = "US Census Geocoder (Public_AR_Current)"
