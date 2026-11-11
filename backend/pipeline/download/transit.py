"""Transit stops: MBTA GTFS (direct from MBTA) and the 15 Massachusetts regional transit
authorities (RTAs) via the MobilityData catalogue mirror (latest archived feed per agency).

Run: uv run python -m pipeline.download.transit
"""

from pipeline.download.common import check_zip, download, setup_logging, source_dir

MBTA_URL = "https://cdn.mbta.com/MBTA_GTFS.zip"
MOBILITYDATA = "https://files.mobilitydatabase.org/{id}/latest.zip"

# slug -> (MobilityData feed id, agency name)
RTA_FEEDS: dict[str, tuple[str, str]] = {
    "brta": ("mdb-537", "Berkshire Regional Transit Authority"),
    "bat": ("mdb-422", "Brockton Area Transit Authority"),
    "cata": ("mdb-447", "Cape Ann Transportation Authority"),
    "ccrta": ("mdb-645", "Cape Cod Regional Transit Authority"),
    "frta": ("mdb-429", "Franklin Regional Transit Authority"),
    "gatra": ("mdb-418", "Greater Attleboro Taunton Regional Transit Authority"),
    "lrta": ("mdb-444", "Lowell Regional Transit Authority"),
    "mart": ("mdb-433", "Montachusett Regional Transit Authority"),
    "mwrta": ("mdb-439", "MetroWest Regional Transit Authority"),
    "mvrta": ("mdb-445", "Merrimack Valley Regional Transit Authority"),
    "nrta": ("mdb-426", "Nantucket Regional Transit Authority"),
    "pvta": ("mdb-2416", "Pioneer Valley Transit Authority"),
    "srta": ("mdb-421", "Southeastern Regional Transit Authority"),
    "vta": ("mdb-420", "Martha's Vineyard Transit Authority"),
    "wrta": ("mdb-432", "Worcester Regional Transit Authority"),
}


def run() -> None:
    folder = source_dir("gtfs")
    check_zip(download(MBTA_URL, folder, "mbta.zip", min_bytes=100_000, extra={"agency": "MBTA"}))
    for slug, (feed_id, agency) in RTA_FEEDS.items():
        path = download(
            MOBILITYDATA.format(id=feed_id),
            folder,
            f"{slug}.zip",
            min_bytes=1_000,
            extra={"agency": agency, "mobilitydata_id": feed_id},
        )
        check_zip(path)


if __name__ == "__main__":
    setup_logging()
    run()
