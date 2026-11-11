import time

import pytest
from fastapi.testclient import TestClient

POINTS = {
    "boston": (42.3601, -71.0589),
    "worcester": (42.2626, -71.8023),
    "springfield": (42.1015, -72.5898),
}
METRICS = (
    "population",
    "homeless",
    "at_risk_households",
    "eli_renter_households",
    "affordable_units_available",
    "affordable_gap",
    "gap_status",
    "subsidised_units",
    "need_index",
    "shelters",
)


@pytest.mark.parametrize("city", POINTS)
def test_three_rings_all_metrics_fast(client: TestClient, seeded, city: str) -> None:
    lat, lon = POINTS[city]
    client.post("/api/area-stats", json={"lat": lat, "lon": lon})  # warm the index
    t0 = time.perf_counter()
    r = client.post("/api/area-stats", json={"lat": lat, "lon": lon, "radii_km": [1.5, 5, 15]})
    assert time.perf_counter() - t0 < 1.0
    assert r.status_code == 200
    body = r.json()
    assert [x["radius_km"] for x in body["rings"]] == [1.5, 5, 15]
    for ring in body["rings"]:
        for m in METRICS:
            assert ring[m] is not None, (city, ring["radius_km"], m)
        assert ring["homeless"]["label"] == "estimate"
        assert ring["gap_status"] in ("shortage", "surplus", "balanced")
    pops = [x["population"] for x in body["rings"]]
    assert pops == sorted(pops)
    assert body["nearby_tracts"]
    assert all(t["homeless"]["label"] == "estimate" for t in body["nearby_tracts"])
    assert body["sources"]["population"]["source"] == "acs5"


def test_ring_never_exceeds_state_total(client: TestClient, seeded) -> None:
    state = client.get("/api/stats/overview").json()
    total = state["homelessness"]["area_estimate"]["value"]
    lat, lon = POINTS["boston"]
    ring = client.post("/api/area-stats", json={"lat": lat, "lon": lon, "radii_km": [80]}).json()[
        "rings"
    ][0]
    assert ring["homeless"]["value"] <= total + 1


def test_area_stats_validation(client: TestClient, seeded) -> None:
    r = client.post("/api/area-stats", json={"lat": 40.7128, "lon": -74.006})
    assert r.status_code == 422
    assert "outside Massachusetts" in r.json()["detail"]
    for radii in ([0.2], [81], [1, 2, 3, 4], []):
        r = client.post("/api/area-stats", json={"lat": 42.36, "lon": -71.06, "radii_km": radii})
        assert r.status_code == 422, radii
    assert client.post("/api/area-stats", json={"lat": 95, "lon": 0}).status_code == 422
