"""Boundaries: Census TIGER/Line (tracts, county subdivisions = MA cities/towns, counties),
Boston neighbourhoods (Analyze Boston / BPDA) and HUD Continuum of Care boundaries.

Run: uv run python -m pipeline.download.boundaries
"""

from pipeline.download.common import check_zip, download, setup_logging, source_dir

TIGER_YEAR = 2026
TIGER_BASE = f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}"
TIGER_FILES = {
    "tract": f"{TIGER_BASE}/TRACT/tl_{TIGER_YEAR}_25_tract.zip",
    "cousub": f"{TIGER_BASE}/COUSUB/tl_{TIGER_YEAR}_25_cousub.zip",
    "county": f"{TIGER_BASE}/COUNTY/tl_{TIGER_YEAR}_us_county.zip",
}

BOSTON_NEIGHBOURHOODS_URL = (
    "https://data.boston.gov/dataset/bf1a7b50-4c72-4637-b0fa-11d632e3aff1/resource/"
    "e5849875-a6f6-4c9c-9d8a-5048b0fbd03e/download/boston_neighborhood_boundaries.geojson"
)

COC_YEAR = 2025
COC_URL = (
    f"https://files.hudexchange.info/reports/published/CoC_GIS_State_Shapefile_MA_{COC_YEAR}.zip"
)


def run() -> None:
    tiger = source_dir("tiger")
    for url in TIGER_FILES.values():
        check_zip(download(url, tiger, min_bytes=10_000))

    boston = source_dir("boston_neighbourhoods")
    download(BOSTON_NEIGHBOURHOODS_URL, boston, "boston_neighborhood_boundaries.geojson")

    coc = source_dir("hud_coc")
    check_zip(download(COC_URL, coc, min_bytes=10_000))


if __name__ == "__main__":
    setup_logging()
    run()
