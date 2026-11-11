from fastapi.testclient import TestClient


def test_homelessness_is_coc_level(client: TestClient, seeded) -> None:
    body = client.get("/api/homelessness").json()
    assert len(body["cocs"]) == 11
    assert all(c["label"] == "official CoC count" for c in body["cocs"])
    years = [y["year"] for y in body["state"]["years"]]
    assert years == sorted(years) and len(years) > 5
    one = client.get("/api/homelessness/MA-500").json()
    assert one["coc_number"] == "MA-500"
    assert client.get("/api/homelessness/XX-000").status_code == 404


def test_shelters_have_no_dv_and_note(client: TestClient, seeded) -> None:
    body = client.get("/api/shelters").json()
    assert body["shelters"]
    assert "domestic-violence" in body["note"]
    assert all("domestic" not in s["shelter_type"].lower() for s in body["shelters"])
    assert all(s["source"] == "osm_shelters" for s in body["shelters"])


def test_model_metrics_and_sources(client: TestClient, seeded) -> None:
    m = client.get("/api/model/metrics").json()
    assert m["home_value"]["metrics"]["target_met"] in (True, False)
    assert "weights" in m["site_scoring"]["params"]
    src = client.get("/api/sources").json()
    keys = {s["key"] for s in src}
    assert {"acs5", "hud_chas", "hud_pit", "massgis_parcels"} <= keys
