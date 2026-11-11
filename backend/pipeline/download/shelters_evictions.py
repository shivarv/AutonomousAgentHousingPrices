"""Best-effort sources:

- Shelters: OpenStreetMap (Overpass API, ODbL) features tagged as homeless shelters in
  Massachusetts. Facilities tagged for abused people / victims / women are excluded in the query
  itself, so domestic-violence shelter locations are never downloaded or stored. OSM has no
  reliable bed counts; official bed totals come from the HUD HIC per CoC.
- Evictions: Eviction Lab tract-level filing data (validated proprietary series, 2000-2018).
  The MA Trial Court filings dashboard offers no machine-readable download.

Run: uv run python -m pipeline.download.shelters_evictions
"""

import requests

from pipeline.download.common import USER_AGENT, download, save_json, setup_logging, source_dir

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """[out:json][timeout:120];
area["ISO3166-2"="US-MA"]->.ma;
(
  nwr["social_facility"="shelter"]["social_facility:for"!~"abused|victim|woman"](area.ma);
  nwr["amenity"="shelter"]["shelter_type"="homeless"](area.ma);
);
out center tags;"""

EVICTION_BASE = "https://eviction-lab-data-downloads.s3.amazonaws.com/data-for-analysis"
EVICTION_FILES = [
    f"{EVICTION_BASE}/tract_proprietary_valid_2000_2018_y2024m12.csv",
    f"{EVICTION_BASE}/tract_monthly_proprietary_valid_2000_2018_tracts2020.csv",
]


def run() -> None:
    shelters = source_dir("osm_shelters")
    target = "osm_shelters_ma.json"
    if not (shelters / target).exists():
        resp = requests.post(
            OVERPASS_URL,
            data={"data": OVERPASS_QUERY},
            timeout=300,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        save_json(shelters, target, resp.json(), OVERPASS_URL, query=OVERPASS_QUERY)

    evictions = source_dir("eviction_lab")
    for url in EVICTION_FILES:
        download(url, evictions, min_bytes=1_000_000, timeout=900)


if __name__ == "__main__":
    setup_logging()
    run()
