"""HUD CHAS (Comprehensive Housing Affordability Strategy) tract-level data, 2018-2022 ACS.

National tract file (all tables + data dictionary). Kept untouched in data/raw/chas/.

Run: uv run python -m pipeline.download.chas
"""

from pipeline.download.common import (
    BROWSER_USER_AGENT,
    check_zip,
    download,
    setup_logging,
    source_dir,
)

CHAS_PERIOD = "2018thru2022"
CHAS_URL = f"https://www.huduser.gov/portal/datasets/cp/{CHAS_PERIOD}-140-csv.zip"
DICTIONARY_URL = "https://www.huduser.gov/portal/datasets/cp/CHAS-data-dictionary-18-22.xlsx"


def run() -> None:
    folder = source_dir("chas")
    path = download(
        CHAS_URL,
        folder,
        min_bytes=1_000_000,
        timeout=600,
        user_agent=BROWSER_USER_AGENT,
        extra={"period": CHAS_PERIOD, "summary_level": "140 (tract)"},
    )
    check_zip(path)
    download(DICTIONARY_URL, folder, min_bytes=10_000, user_agent=BROWSER_USER_AGENT)


if __name__ == "__main__":
    setup_logging()
    run()
