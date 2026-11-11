from fastapi.testclient import TestClient

from app.services.geocode_service import parse_matches

BODY = {
    "result": {
        "addressMatches": [
            {
                "coordinates": {"x": -71.0592, "y": 42.3578},
                "addressComponents": {"state": "MA"},
                "matchedAddress": "1 CITY HALL AVE, BOSTON, MA, 02108",
            },
            {
                "coordinates": {"x": -71.4, "y": 41.8},
                "addressComponents": {"state": "RI"},
                "matchedAddress": "1 MAIN ST, PROVIDENCE, RI",
            },
        ]
    }
}


def test_parse_keeps_massachusetts_only() -> None:
    m = parse_matches(BODY)
    assert len(m) == 1
    assert m[0].lat == 42.3578 and m[0].lon == -71.0592


def test_geocode_validation(client: TestClient) -> None:
    assert client.get("/api/geocode", params={"q": "  "}).status_code == 422
    assert client.get("/api/geocode", params={"q": "x" * 300}).status_code == 422
