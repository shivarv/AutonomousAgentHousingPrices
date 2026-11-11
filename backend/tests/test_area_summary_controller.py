import pytest
from fastapi.testclient import TestClient


def _summary(client: TestClient, level: str, ids: list[str]):
    return client.post("/api/areas/summary", json={"level": level, "ids": ids})


def test_all_counties_add_up_to_state(client: TestClient, seeded) -> None:
    ids = [f["id"] for f in client.get("/api/areas", params={"level": "county"}).json()["features"]]
    s = _summary(client, "county", ids).json()
    state = client.get("/api/stats/overview").json()
    assert s["figures"]["affordable_gap"] == pytest.approx(
        state["metrics"]["affordable_gap_eli"]["value"], abs=1
    )
    assert s["figures"]["homeless"]["label"] == "estimate"
    assert s["figures"]["homeless"]["value"] == pytest.approx(
        state["homelessness"]["official_state"]["years"][-1]["total"], abs=1
    )


def test_all_towns_add_up_to_state(client: TestClient, seeded) -> None:
    ids = [
        f["id"]
        for f in client.get("/api/areas", params={"level": "municipality"}).json()["features"]
    ]
    s = _summary(client, "municipality", ids).json()
    counties = [
        f["id"] for f in client.get("/api/areas", params={"level": "county"}).json()["features"]
    ]
    c = _summary(client, "county", counties).json()
    assert s["figures"]["population"] == pytest.approx(c["figures"]["population"], rel=1e-6)


def test_benefit_area_of_neighbours(client: TestClient, seeded) -> None:
    at = client.get(
        "/api/areas/at", params={"lat": 42.3601, "lon": -71.0589, "level": "municipality"}
    ).json()
    ids = [at["id"], *[n["id"] for n in at["neighbours"][:2]]]
    s = _summary(client, "municipality", ids + [at["id"]]).json()  # duplicate ignored
    assert [a["id"] for a in s["areas"]] == ids
    assert s["figures"]["population"] > at["figures"]["population"]
    assert s["homeless_basis"] == "sum of tract estimates"


def test_coc_summary_is_official(client: TestClient, seeded) -> None:
    s = _summary(client, "coc", ["MA-500", "MA-506"]).json()
    assert s["figures"]["homeless"]["label"] == "official CoC count"
    assert s["homeless_estimate_sum"]["value"] == pytest.approx(
        s["figures"]["homeless"]["value"], abs=1
    )


def test_summary_validation(client: TestClient, seeded) -> None:
    assert _summary(client, "county", ["99999"]).status_code == 404
    assert _summary(client, "county", []).status_code == 422
    assert _summary(client, "planet", ["1"]).status_code == 422
