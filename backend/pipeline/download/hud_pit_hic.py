"""HUD Point-in-Time (PIT) homeless counts and Housing Inventory Count (HIC) by CoC, 2007-2025.

National workbooks (one sheet per year). These are the only official homelessness figures and
they exist only per Continuum of Care.

Run: uv run python -m pipeline.download.hud_pit_hic
"""

from pipeline.download.common import BROWSER_USER_AGENT, download, setup_logging, source_dir

LATEST_YEAR = 2025
BASE = "https://www.huduser.gov/portal/sites/default/files/xls"
PIT_URL = f"{BASE}/2007-{LATEST_YEAR}-PIT-Counts-by-CoC.xlsb"
HIC_URL = f"{BASE}/2007-{LATEST_YEAR}-HIC-Counts-by-CoC.xlsx"


def run() -> None:
    folder = source_dir("hud_pit_hic")
    for url in (PIT_URL, HIC_URL):
        download(url, folder, min_bytes=100_000, user_agent=BROWSER_USER_AGENT, timeout=300)


if __name__ == "__main__":
    setup_logging()
    run()
