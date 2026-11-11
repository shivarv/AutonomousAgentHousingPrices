"""Address search through the US Census Geocoder (no API key). Only Massachusetts matches
are returned. The browser cannot call the geocoder directly (no CORS), so the API relays."""

from typing import Any

import requests

from app.core.exceptions import DomainError, ValidationError
from app.schemas.geocode import GeocodeMatch, GeocodeResult

URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
TIMEOUT_S = 10
MAX_QUERY = 200


class GeocoderUnavailableError(DomainError):
    status_code = 502


def parse_matches(body: dict[str, Any]) -> list[GeocodeMatch]:
    matches = body.get("result", {}).get("addressMatches", [])
    out = []
    for m in matches:
        if m.get("addressComponents", {}).get("state") != "MA":
            continue
        c = m.get("coordinates", {})
        if "x" in c and "y" in c:
            out.append(GeocodeMatch(address=m.get("matchedAddress", ""), lat=c["y"], lon=c["x"]))
    return out


class GeocodeService:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.http = session or requests.Session()

    def search(self, query: str) -> GeocodeResult:
        q = query.strip()
        if not q:
            raise ValidationError("enter an address to search")
        if len(q) > MAX_QUERY:
            raise ValidationError(f"address is longer than {MAX_QUERY} characters")
        if "MA" not in q.upper() and "MASSACHUSETTS" not in q.upper():
            q = f"{q}, MA"
        try:
            r = self.http.get(
                URL,
                params={"address": q, "benchmark": "Public_AR_Current", "format": "json"},
                timeout=TIMEOUT_S,
            )
            r.raise_for_status()
            body = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise GeocoderUnavailableError(
                "The Census address search is unavailable right now; try again or drop a pin"
            ) from exc
        return GeocodeResult(query=q, matches=parse_matches(body))
