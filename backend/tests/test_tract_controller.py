import time

from fastapi.testclient import TestClient


def test_statewide_tracts_geojson_fast_and_complete(client: TestClient, seeded) -> None:
    client.get("/api/tracts")  # warm the cache
    t0 = time.perf_counter()
    r = client.get("/api/tracts")
    assert time.perf_counter() - t0 < 1.0
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1620
    f = body["features"][0]
    assert f["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert "need_index" in f["properties"]
    assert f["properties"]["homeless_label"] == "estimate"
    assert body["metrics"]["homeless_estimate"]["label"] == "estimate"
    assert body["metrics"]["need_index"]["year"] is not None


def test_tract_filters(client: TestClient, seeded) -> None:
    county = client.get("/api/tracts", params={"county": "25025"}).json()
    assert county["features"]
    assert all(f["id"].startswith("25025") for f in county["features"])
    town = client.get("/api/tracts", params={"municipality": "2502507000"}).json()
    assert 150 < len(town["features"]) < 260  # Boston
    assert client.get("/api/tracts", params={"county": "00000"}).status_code == 404


def test_tract_detail_labels_estimate(client: TestClient, seeded) -> None:
    geoid = client.get("/api/tracts", params={"county": "25025"}).json()["features"][0]["id"]
    r = client.get(f"/api/tracts/{geoid}")
    assert r.status_code == 200
    d = r.json()
    assert d["homeless"]["label"] == "estimate"
    assert d["homeless"]["method"]
    assert d["metrics"]["population"]["source"] == "acs5"
    assert d["municipalities"]
    assert client.get("/api/tracts/0").status_code == 404
