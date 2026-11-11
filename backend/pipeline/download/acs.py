"""ACS 5-year estimates for every Massachusetts census tract (api.census.gov).

The API key comes from the CENSUS_API_KEY environment variable and is never written to disk:
the manifest records the URL without the key.

Run: uv run python -m pipeline.download.acs
"""

import os

import requests

from pipeline.download.common import USER_AGENT, save_json, setup_logging, source_dir

ACS_YEAR = 2024  # 2020-2024 5-year estimates (latest release)

# variable -> meaning (E = estimate, M = margin of error)
VARIABLES: dict[str, str] = {
    "B01003_001": "total population",
    "B11001_001": "households",
    "B19013_001": "median household income",
    "B17001_001": "poverty status universe",
    "B17001_002": "income below poverty level",
    "B25001_001": "housing units",
    "B25002_002": "occupied housing units",
    "B25002_003": "vacant housing units",
    "B25004_002": "vacant: for rent",
    "B25004_003": "vacant: rented, not occupied",
    "B25004_004": "vacant: for sale only",
    "B25004_005": "vacant: sold, not occupied",
    "B25003_001": "occupied units (tenure universe)",
    "B25003_002": "owner occupied",
    "B25003_003": "renter occupied",
    "B25014_001": "occupants per room universe",
    "B25014_005": "owner 1.01-1.50 per room",
    "B25014_006": "owner 1.51-2.00 per room",
    "B25014_007": "owner 2.01+ per room",
    "B25014_011": "renter 1.01-1.50 per room",
    "B25014_012": "renter 1.51-2.00 per room",
    "B25014_013": "renter 2.01+ per room",
    "B25070_001": "renter households (gross rent % income universe)",
    "B25070_007": "rent 30.0-34.9% of income",
    "B25070_008": "rent 35.0-39.9% of income",
    "B25070_009": "rent 40.0-49.9% of income",
    "B25070_010": "rent 50%+ of income",
    "B25070_011": "rent burden not computed",
    "B25064_001": "median gross rent",
    "B25077_001": "median home value",
}


def _fetch(year: int, variables: list[str], key: str) -> list[list[str]]:
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(["NAME", *variables]),
        "for": "tract:*",
        "in": "state:25",
        "key": key,
    }
    resp = requests.get(url, params=params, timeout=120, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.json()


def run(year: int = ACS_YEAR) -> None:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set")
    folder = source_dir("acs")
    filename = f"acs5_{year}_tracts_ma.json"
    if (folder / filename).exists():
        return
    codes = [f"{v}E" for v in VARIABLES] + [f"{v}M" for v in VARIABLES]
    # the API allows at most 50 variables per call; join batches on the geography columns
    rows: dict[tuple[str, str, str], dict[str, str]] = {}
    for start in range(0, len(codes), 45):
        batch = codes[start : start + 45]
        table = _fetch(year, batch, key)
        header = table[0]
        for raw in table[1:]:
            rec = dict(zip(header, raw, strict=True))
            geo = (rec["state"], rec["county"], rec["tract"])
            rows.setdefault(geo, {}).update(rec)
    header = ["NAME", *codes, "state", "county", "tract"]
    table = [header] + [[rec.get(h) for h in header] for rec in rows.values()]
    public_url = (
        f"https://api.census.gov/data/{year}/acs/acs5?get=NAME,<variables>&for=tract:*&in=state:25"
    )
    save_json(folder, filename, table, public_url, year=year, variables=VARIABLES)


if __name__ == "__main__":
    setup_logging()
    run()
