from fastapi.testclient import TestClient


def test_state_overview_official_sum_and_estimate(client: TestClient, seeded) -> None:
    r = client.get("/api/stats/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Massachusetts"
    h = body["homelessness"]
    latest = h["official_state"]["years"][-1]
    assert latest["total"] == sum(c["latest"]["total"] for c in h["official_cocs"])
    assert h["area_estimate"]["label"] == "estimate"
    assert abs(h["area_estimate"]["value"] - latest["total"]) < 1
    assert body["metrics"]["population"]["source"] == "acs5"
    assert body["shelter_beds"]["label"] == "official CoC count"
    assert body["shelter_beds"]["value"] > 0
    for m in ("eli_renter_households", "affordable_gap_eli", "vacancy_rate", "need_index"):
        assert body["metrics"][m]["value"] is not None
        assert body["metrics"][m]["year"] is not None


def test_county_and_town_overview(client: TestClient, seeded) -> None:
    r = client.get("/api/stats/overview", params={"level": "county", "id": "25025"})
    assert r.status_code == 200
    b = r.json()
    assert b["name"].startswith("Suffolk")
    assert b["homelessness"]["official_state"] is None
    assert {c["coc_number"] for c in b["homelessness"]["official_cocs"]} >= {"MA-500"}
    r = client.get("/api/stats/overview", params={"level": "municipality", "id": "2502507000"})
    assert r.status_code == 200
    assert r.json()["name"] == "Boston"


def test_overview_errors(client: TestClient, seeded) -> None:
    assert client.get("/api/stats/overview", params={"level": "county"}).status_code == 422
    r = client.get("/api/stats/overview", params={"level": "county", "id": "99999"})
    assert r.status_code == 404
    assert client.get("/api/stats/overview", params={"level": "planet"}).status_code == 422


def test_area_tables(client: TestClient, seeded) -> None:
    counties = client.get("/api/stats/areas", params={"level": "county"}).json()
    assert len(counties["rows"]) == 14
    state = client.get("/api/stats/overview").json()
    gap = sum(r["affordable_gap_eli"] for r in counties["rows"])
    assert abs(gap - state["metrics"]["affordable_gap_eli"]["value"]) < 1
    assert counties["homeless_label"] == "estimate"
    towns = client.get("/api/stats/areas", params={"level": "municipality"}).json()
    assert len(towns["rows"]) == 351
    assert all(r["county_geoid"] for r in towns["rows"])
    assert client.get("/api/stats/areas", params={"level": "tract"}).status_code == 422
