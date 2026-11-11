from fastapi.testclient import TestClient


def test_site_list_ranked_and_filtered(client: TestClient, seeded) -> None:
    r = client.get("/api/sites", params={"limit": 20})
    assert r.status_code == 200
    body = r.json()
    ranks = [s["rank_state"] for s in body["sites"]]
    assert ranks == sorted(ranks) and ranks[0] == 1
    assert body["total"] > 1000
    s = body["sites"][0]
    assert 0 <= s["score"] <= 100
    assert s["homeless_5km"]["label"] == "estimate"
    county = client.get("/api/sites", params={"county": "25025", "limit": 5}).json()
    assert county["sites"] and all(x["county_geoid"] == "25025" for x in county["sites"])
    town = client.get("/api/sites", params={"municipality": "2502507000", "limit": 5}).json()
    assert all(x["municipality"] == "Boston" for x in town["sites"])


def test_best_and_next_best(client: TestClient, seeded) -> None:
    best = client.get("/api/sites/best").json()
    assert best["rank_state"] == 1
    nxt = client.get("/api/sites/best", params={"offset": 1}).json()
    assert nxt["rank_state"] == 2
    w = client.get("/api/sites/best", params={"county": "25027"}).json()
    assert w["county_geoid"] == "25027" and w["rank_county"] == 1
    assert len(best["rings"]) == 3
    assert all(ring["homeless"]["label"] == "estimate" for ring in best["rings"])
    assert abs(sum(best["weights"].values()) - 1) < 1e-9
    assert best["boundary"]["type"] in ("Polygon", "MultiPolygon")
    assert not any(k.startswith("homeless_est") for k in best["features"])
    assert max(best["overlaps"].values()) <= 0.5


def test_site_errors(client: TestClient, seeded) -> None:
    assert client.get("/api/sites/0").status_code == 404
    assert client.get("/api/sites", params={"limit": 0}).status_code == 422
    assert client.get("/api/sites/best", params={"county": "00000"}).status_code == 404
