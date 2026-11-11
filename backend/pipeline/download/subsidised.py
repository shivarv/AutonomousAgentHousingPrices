"""Subsidised housing: HUD LIHTC property database and HUD Picture of Subsidized Households
(2025, 2020 census geography: tract file covering AK-MN, which includes MA, and project file).

Run: uv run python -m pipeline.download.subsidised
"""

from pipeline.download.common import (
    BROWSER_USER_AGENT,
    check_zip,
    download,
    setup_logging,
    source_dir,
)

LIHTC_URL = "https://www.huduser.gov/lihtc/lihtcpub.zip"
PSH_YEAR = 2025
PSH_BASE = "https://www.huduser.gov/portal/datasets/pictures/files"
PSH_FILES = [
    f"{PSH_BASE}/TRACT_AK_MN_{PSH_YEAR}_2020census.xlsx",
    f"{PSH_BASE}/PROJECT_{PSH_YEAR}_2020census.xlsx",
]


def run() -> None:
    lihtc = source_dir("hud_lihtc")
    check_zip(
        download(LIHTC_URL, lihtc, min_bytes=100_000, user_agent=BROWSER_USER_AGENT, timeout=300)
    )
    psh = source_dir("hud_psh")
    for url in PSH_FILES:
        download(url, psh, min_bytes=100_000, user_agent=BROWSER_USER_AGENT, timeout=300)


if __name__ == "__main__":
    setup_logging()
    run()
