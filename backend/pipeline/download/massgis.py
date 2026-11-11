"""MassGIS statewide layers (download.massgis.digital.mass.gov):

- Standardized Assessors' Parcels (Level 3), statewide file geodatabase (polygons + assessing
  table: land use code, lot size, land/building/total values, fiscal year).
- Protected and Recreational Open Space.
- MassDEP Wetlands (polygons).
- FEMA National Flood Hazard Layer (MassGIS statewide extract).
- MBTA Communities (Section 3A) multifamily zoning districts.

Run: uv run python -m pipeline.download.massgis
"""

from pipeline.download.common import check_zip, download, setup_logging, source_dir

BASE = "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov"

LAYERS: dict[str, list[str]] = {
    "massgis_parcels": [f"{BASE}/gdbs/l3parcels/MassGIS_L3_Parcels_gdb.zip"],
    "massgis_openspace": [f"{BASE}/shapefiles/state/openspace.zip"],
    "massgis_wetlands": [f"{BASE}/shapefiles/state/wetlandsdep_poly.zip"],
    "massgis_flood": [f"{BASE}/shapefiles/state/nfhl.zip"],
    "massgis_mbta3a": [
        f"{BASE}/shapefiles/state/MBTA3A.zip",
        f"{BASE}/shapefiles/state/MBTACommunitiesAtlas_2026-10-27_WithNotes.xlsx",
    ],
}


def run() -> None:
    for source, urls in LAYERS.items():
        folder = source_dir(source)
        for url in urls:
            path = download(url, folder, min_bytes=10_000, timeout=1800)
            if path.suffix == ".zip":
                check_zip(path)


if __name__ == "__main__":
    setup_logging()
    run()
