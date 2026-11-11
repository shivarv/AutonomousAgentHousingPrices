import pytest
from fastapi.testclient import TestClient

COUNTS = {"county": 14, "municipality": 351, "coc": 11, "tract": 1620}


@pytest.mark.parametrize("level", COUNTS)
def test_outlines_every_area(client: TestClient, seeded, level: str) -> None:
    r = client.get("/api/areas", params={"level": level})
    assert r.status_code == 200
    body = r.json()
    assert body["level"] == level
    assert len(body["features"]) == COUNTS[level]
    assert body["features"][0]["properties"]["name"]


def test_outlines_bbox_filters(client: TestClient, seeded) -> None:
    bbox = "-71.2,42.2,-70.9,42.45"  # around Boston
    towns = client.get("/api/areas", params={"level": "municipality", "bbox": bbox}).json()
    names = {f["properties"]["name"] for f in towns["features"]}
    assert "Boston" in names and "Springfield" not in names
    assert 5 < len(names) < 60
    hoods = client.get("/api/areas", params={"level": "neighbourhood"}).json()
    assert len(hoods["features"]) >= 20


def test_outlines_validation(client: TestClient, seeded) -> None:
    assert client.get("/api/areas", params={"level": "x"}).status_code == 422
    assert client.get("/api/areas", params={"bbox": "1,2,3"}).status_code == 422
    assert client.get("/api/areas", params={"bbox": "-70,42,-71,43"}).status_code == 422
