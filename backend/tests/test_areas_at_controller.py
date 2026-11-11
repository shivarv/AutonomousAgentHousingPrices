import pytest
from fastapi.testclient import TestClient

# point -> expected (tract county prefix, town, county, CoC)
POINTS = {
    "boston": ((42.3601, -71.0589), ("25025", "Boston", "25025", "MA-500")),
    "worcester": ((42.2626, -71.8023), ("25027", "Worcester", "25027", "MA-506")),
    "springfield": ((42.1015, -72.5898), ("25013", "Springfield", "25013", "MA-504")),
}


def _at(client: TestClient, latlon: tuple[float, float], level: str):
    return client.get("/api/areas/at", params={"lat": latlon[0], "lon": latlon[1], "level": level})


@pytest.mark.parametrize("city", POINTS)
def test_areas_at_every_level(client: TestClient, seeded, city: str) -> None:
    latlon, (tract_prefix, town, county, coc) = POINTS[city]
    tract = _at(client, latlon, "tract").json()
    assert tract["id"].startswith(tract_prefix)
    assert _at(client, latlon, "municipality").json()["name"] == town
    assert _at(client, latlon, "county").json()["id"] == county
    c = _at(client, latlon, "coc").json()
    assert c["id"] == coc
    # official count at CoC level, and the tract estimates inside it add up to it
    assert c["homeless_basis"] == "official CoC count"
    assert c["figures"]["homeless"]["label"] == "official CoC count"
    assert c["homeless_estimate_sum"]["label"] == "estimate"
    assert c["homeless_estimate_sum"]["value"] == pytest.approx(
        c["figures"]["homeless"]["value"], abs=0.5
    )
    assert c["figures"]["shelter_beds"] > 0
    for level in ("tract", "municipality", "county"):
        body = _at(client, latlon, level).json()
        assert body["figures"]["homeless"]["label"] == "estimate"
        assert body["boundary"]["type"] in ("Polygon", "MultiPolygon")
        assert body["neighbours"]
        assert body["figures"]["affordable_gap"] is not None


def test_neighbourhood_inside_and_outside_boston(client: TestClient, seeded) -> None:
    r = _at(client, POINTS["boston"][0], "neighbourhood")
    assert r.status_code == 200 and r.json()["name"] == "Downtown"
    r = _at(client, POINTS["worcester"][0], "neighbourhood")
    assert r.status_code == 422
    assert "outside Boston" in r.json()["detail"]


def test_areas_at_validation(client: TestClient, seeded) -> None:
    assert _at(client, (40.7128, -74.006), "tract").status_code == 422
    assert _at(client, (42.36, -71.06), "planet").status_code == 422
