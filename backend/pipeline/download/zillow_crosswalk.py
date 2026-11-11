"""Zillow Research ZHVI (home values) and ZORI (observed rents) for all US ZIP codes, plus the
Census 2020 ZCTA-to-tract relationship file used to move ZIP data onto tracts.

The HUD USPS ZIP-tract crosswalk (primary source in PLAN.md) needs a registered API token, which
this pipeline does not have; the Census relationship file is the documented fallback.

Run: uv run python -m pipeline.download.zillow_crosswalk
"""

from pipeline.download.common import download, setup_logging, source_dir

ZILLOW_BASE = "https://files.zillowstatic.com/research/public_csvs"
ZHVI_URL = f"{ZILLOW_BASE}/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
ZORI_URL = f"{ZILLOW_BASE}/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv"
ZCTA_TRACT_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
    "tab20_zcta520_tract20_natl.txt"
)
# Residential weights for ZIP -> tract: 2020 blocks carry HOUSING20/POP20; ZCTA polygons let us
# place each block (by internal point) in a ZCTA.
BLOCKS_URL = "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_25_tabblock20.zip"
ZCTA_SHAPES_URL = "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip"


def run() -> None:
    zillow = source_dir("zillow")
    download(ZHVI_URL, zillow, min_bytes=1_000_000, timeout=600)
    download(ZORI_URL, zillow, min_bytes=100_000, timeout=600)
    crosswalk = source_dir("census_relationship")
    download(ZCTA_TRACT_URL, crosswalk, min_bytes=1_000_000, timeout=600)
    download(BLOCKS_URL, crosswalk, min_bytes=1_000_000, timeout=600)
    download(ZCTA_SHAPES_URL, crosswalk, min_bytes=1_000_000, timeout=600)


if __name__ == "__main__":
    setup_logging()
    run()
