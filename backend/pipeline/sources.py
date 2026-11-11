"""Registry of every dataset the pipeline uses.

DATA_SOURCES.md is generated from this registry plus the download manifests
(``uv run python -m pipeline.sources``), and the ``data_sources`` table is loaded from
DATA_SOURCES.md (``uv run python -m pipeline.load_sources``). Each dataset has a stable ``key``
that metric rows reference via ``source_id``.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from pipeline.paths import PROJECT_ROOT, RAW_DIR

DATA_SOURCES_MD = PROJECT_ROOT / "DATA_SOURCES.md"


@dataclass(frozen=True)
class Dataset:
    key: str
    name: str
    folder: str
    files: tuple[str, ...]  # file names inside data/raw/<folder>/ ("*" = every manifest entry)
    licence: str
    geography: str
    years: str
    columns: str
    url: str | None = None  # override (e.g. API endpoints / URL patterns)


DATASETS: tuple[Dataset, ...] = (
    Dataset(
        "tiger_tracts",
        "Census TIGER/Line 2026 census tracts (MA)",
        "tiger",
        ("tl_2026_25_tract.zip",),
        "US Census Bureau, public domain",
        "census tract (2020 definitions)",
        "2026 vintage",
        "GEOID, COUNTYFP, NAMELSAD, ALAND, AWATER, INTPTLAT, INTPTLON, geometry",
    ),
    Dataset(
        "tiger_cousub",
        "Census TIGER/Line 2026 county subdivisions = MA cities and towns",
        "tiger",
        ("tl_2026_25_cousub.zip",),
        "US Census Bureau, public domain",
        "municipality (county subdivision)",
        "2026 vintage",
        "GEOID, COUSUBFP, COUNTYFP, NAME, NAMELSAD, ALAND, AWATER, geometry",
    ),
    Dataset(
        "tiger_counties",
        "Census TIGER/Line 2026 counties (national file, MA rows)",
        "tiger",
        ("tl_2026_us_county.zip",),
        "US Census Bureau, public domain",
        "county",
        "2026 vintage",
        "STATEFP, COUNTYFP, GEOID, NAME, NAMELSAD, ALAND, AWATER, geometry",
    ),
    Dataset(
        "boston_neighbourhoods",
        "BPDA Boston neighbourhood boundaries (Analyze Boston)",
        "boston_neighbourhoods",
        ("boston_neighborhood_boundaries.geojson",),
        "Open Data Commons PDDL",
        "Boston neighbourhood",
        "current",
        "name, geometry",
    ),
    Dataset(
        "hud_coc_boundaries",
        "HUD Continuum of Care GIS boundaries, Massachusetts",
        "hud_coc",
        ("CoC_GIS_State_Shapefile_MA_2025.zip",),
        "HUD, public domain",
        "Continuum of Care",
        "2025",
        "COCNUM, COCNAME, geometry",
    ),
    Dataset(
        "acs5",
        "ACS 5-year estimates via api.census.gov (MA tracts)",
        "acs",
        ("acs5_2024_tracts_ma.json",),
        "US Census Bureau, public domain (API terms of service)",
        "census tract",
        "2020-2024",
        "B01003_001, B11001_001, B19013_001, B17001_001/002, B25001_001, B25002_002/003, "
        "B25004_002-005, B25003_001-003, B25014_001/005-007/011-013, B25070_001/007-011, "
        "B25064_001, B25077_001 (estimates and margins of error)",
    ),
    Dataset(
        "hud_chas",
        "HUD CHAS tract-level tables (2018-2022 ACS)",
        "chas",
        ("2018thru2022-140-csv.zip", "CHAS-data-dictionary-18-22.xlsx"),
        "HUD, public domain",
        "census tract",
        "2018-2022",
        "geoid; Table 15C, Table 18C, Table 8 / Table 7 renter household income and cost burden "
        "cells and rent-affordability unit cells (per the data dictionary)",
    ),
    Dataset(
        "hud_pit",
        "HUD Point-in-Time homeless counts by CoC",
        "hud_pit_hic",
        ("2007-2025-PIT-Counts-by-CoC.xlsb",),
        "HUD, public domain",
        "Continuum of Care",
        "2007-2025",
        "CoC Number, CoC Name, Overall Homeless, Sheltered Total Homeless, Unsheltered Homeless",
    ),
    Dataset(
        "hud_hic",
        "HUD Housing Inventory Count by CoC",
        "hud_pit_hic",
        ("2007-2025-HIC-Counts-by-CoC.xlsx",),
        "HUD, public domain",
        "Continuum of Care",
        "2007-2025",
        "CoC Number, Total Year-Round Beds (ES, TH, SH), Total Year-Round Beds (ES/TH/SH)",
    ),
    Dataset(
        "hud_lihtc",
        "HUD Low-Income Housing Tax Credit property database",
        "hud_lihtc",
        ("lihtcpub.zip",),
        "HUD, public domain",
        "property (lat/lon, tract)",
        "1987-2024 placed in service",
        "HUD_ID, PROJECT, PROJ_ST, LATITUDE, LONGITUDE, FIPS2020, LI_UNITS, N_UNITS, YR_PIS",
    ),
    Dataset(
        "hud_psh",
        "HUD Picture of Subsidized Households 2025 (tract and project files)",
        "hud_psh",
        ("TRACT_AK_MN_2025_2020census.xlsx", "PROJECT_2025_2020census.xlsx"),
        "HUD, public domain",
        "census tract; project (lat/lon)",
        "2025",
        "program, code (tract GEOID), total_units, name, latitude, longitude, states",
    ),
    Dataset(
        "mbta_gtfs",
        "MBTA GTFS schedule feed",
        "gtfs",
        ("mbta.zip",),
        "MassDOT developers licence agreement",
        "transit stop (lat/lon)",
        "current feed",
        "stops.txt: stop_id, stop_name, stop_lat, stop_lon, location_type; routes.txt route_type",
    ),
    Dataset(
        "rta_gtfs",
        "Massachusetts regional transit authority GTFS feeds (MobilityData mirror)",
        "gtfs",
        (
            "bat.zip",
            "brta.zip",
            "cata.zip",
            "ccrta.zip",
            "frta.zip",
            "gatra.zip",
            "lrta.zip",
            "mart.zip",
            "mvrta.zip",
            "mwrta.zip",
            "nrta.zip",
            "pvta.zip",
            "srta.zip",
            "vta.zip",
            "wrta.zip",
        ),
        "Agency open data terms as listed in the MobilityData catalogue",
        "transit stop (lat/lon)",
        "latest archived feed per agency",
        "stops.txt: stop_id, stop_name, stop_lat, stop_lon",
        url="https://files.mobilitydatabase.org/<feed id>/latest.zip",
    ),
    Dataset(
        "zillow_zhvi",
        "Zillow Home Value Index (ZHVI), all homes, by ZIP",
        "zillow",
        ("Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",),
        "Zillow Research data, free use with attribution",
        "ZIP code",
        "2000-2026 monthly",
        "RegionName (ZIP), State, monthly values",
    ),
    Dataset(
        "zillow_zori",
        "Zillow Observed Rent Index (ZORI), all homes, by ZIP",
        "zillow",
        ("Zip_zori_uc_sfrcondomfr_sm_month.csv",),
        "Zillow Research data, free use with attribution",
        "ZIP code",
        "2015-2026 monthly",
        "RegionName (ZIP), State, monthly values",
    ),
    Dataset(
        "census_zcta_tract",
        "Census 2020 ZCTA-to-tract relationship file, 2020 blocks and ZCTA shapes",
        "census_relationship",
        (
            "tab20_zcta520_tract20_natl.txt",
            "tl_2020_25_tabblock20.zip",
            "cb_2020_us_zcta520_500k.zip",
        ),
        "US Census Bureau, public domain",
        "ZCTA x tract; census block",
        "2020",
        "GEOID_ZCTA5_20, GEOID_TRACT_20, AREALAND_PART; blocks GEOID20, HOUSING20, POP20, "
        "INTPTLAT20, INTPTLON20; ZCTA5CE20, geometry",
    ),
    Dataset(
        "massgis_parcels",
        "MassGIS Standardized Assessors' Parcels (Level 3), statewide",
        "massgis_parcels",
        ("MassGIS_L3_Parcels_gdb.zip",),
        "MassGIS, free public data (no owner fields used)",
        "parcel",
        "assessor fiscal years 2024-2027 (per town)",
        "L3_TAXPAR_POLY: LOC_ID, TOWN_ID, geometry; L3_ASSESS: LOC_ID, USE_CODE, LOT_SIZE, "
        "LOT_UNITS, LAND_VAL, BLDG_VAL, TOTAL_VAL, FY, YEAR_BUILT, BLD_AREA, RES_AREA, UNITS, "
        "NUM_ROOMS, STYLE, ZIP, TOWN_ID",
    ),
    Dataset(
        "massgis_openspace",
        "MassGIS Protected and Recreational Open Space",
        "massgis_openspace",
        ("openspace.zip",),
        "MassGIS, free public data",
        "polygon",
        "2026 release",
        "geometry, LEV_PROT, PRIM_PURP",
    ),
    Dataset(
        "massgis_wetlands",
        "MassDEP Wetlands (polygons)",
        "massgis_wetlands",
        ("wetlandsdep_poly.zip",),
        "MassGIS / MassDEP, free public data",
        "polygon",
        "2005 mapping (2021 package)",
        "geometry, IT_VALDESC",
    ),
    Dataset(
        "massgis_flood",
        "FEMA National Flood Hazard Layer (MassGIS statewide extract)",
        "massgis_flood",
        ("nfhl.zip",),
        "FEMA, public domain",
        "polygon",
        "2025 extract",
        "geometry, FLD_ZONE, SFHA_TF",
    ),
    Dataset(
        "massgis_mbta3a",
        "MBTA Communities (Section 3A) multifamily zoning districts and atlas",
        "massgis_mbta3a",
        ("MBTA3A.zip", "MBTACommunitiesAtlas_2026-10-27_WithNotes.xlsx"),
        "MassGIS / EOHLC, free public data",
        "zoning district polygon",
        "2026-10 release",
        "geometry, municipality, district name, compliance status",
    ),
    Dataset(
        "osm_shelters",
        "OpenStreetMap homeless shelters in MA (Overpass API; DV-tagged facilities excluded)",
        "osm_shelters",
        ("osm_shelters_ma.json",),
        "Open Database License (ODbL), (c) OpenStreetMap contributors",
        "point",
        "snapshot at download date",
        "id, lat/lon (or center), tags.name, tags.social_facility:for, tags.capacity",
    ),
    Dataset(
        "eviction_lab",
        "Eviction Lab tract-level eviction filings (validated proprietary series)",
        "eviction_lab",
        (
            "tract_proprietary_valid_2000_2018_y2024m12.csv",
            "tract_monthly_proprietary_valid_2000_2018_tracts2020.csv",
        ),
        "Eviction Lab, Princeton University; free for non-commercial use with attribution",
        "census tract",
        "2000-2018",
        "fips, year, filings, filing_rate",
    ),
)


def _manifest(folder: str) -> dict:
    path = RAW_DIR / folder / "manifest.json"
    return json.loads(path.read_text())["files"] if path.exists() else {}


def build_rows() -> list[dict[str, str]]:
    rows = []
    for ds in DATASETS:
        manifest = _manifest(ds.folder)
        missing = [f for f in ds.files if f not in manifest]
        if missing:
            raise SystemExit(f"{ds.key}: not downloaded yet: {missing}")
        entries = [manifest[f] for f in ds.files]
        urls = sorted({e["url"] for e in entries})
        dates = sorted({e["downloaded_at"][:10] for e in entries})
        rows.append(
            {
                "key": ds.key,
                "name": ds.name,
                "url": ds.url or "; ".join(urls),
                "download_date": dates[-1],
                "licence": ds.licence,
                "geography": ds.geography,
                "years": ds.years,
                "file_path": "; ".join(f"data/raw/{ds.folder}/{f}" for f in ds.files),
                "columns": ds.columns,
            }
        )
    return rows


HEADER = (
    "name | URL | download date | licence/terms | geography | year(s) | file path | columns used"
)
FIELDS = [
    "name",
    "url",
    "download_date",
    "licence",
    "geography",
    "years",
    "file_path",
    "columns",
]


def render(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Data sources",
        "",
        "Generated by `uv run --project backend python -m pipeline.sources` from the download",
        "manifests (data/raw/<source>/manifest.json, which also hold sha256 checksums).",
        "Download dates are UTC. One line per dataset (format required by CLAUDE.md).",
        "",
        HEADER,
        "---|---|---|---|---|---|---|---",
    ]
    for r in rows:
        cells = [r[f] for f in FIELDS]
        lines.append(" | ".join(c.replace("|", "/") for c in cells))
    return "\n".join(lines) + "\n"


def parse(text: str) -> list[dict[str, str]]:
    """Parse DATA_SOURCES.md back into rows (used by the data_sources loader and validate.py).

    Each row gets its registry ``key`` by matching the dataset name.
    """
    keys = FIELDS
    by_name = {ds.name: ds.key for ds in DATASETS}
    rows = []
    started = False
    for line in text.splitlines():
        if line.startswith("name | URL"):
            started = True
            continue
        if not started or line.startswith("---") or not line.strip():
            continue
        cells = [c.strip() for c in line.split(" | ")]
        if len(cells) != len(keys):
            raise ValueError(f"malformed DATA_SOURCES.md line: {line}")
        row = dict(zip(keys, cells, strict=True))
        if row["name"] not in by_name:
            raise ValueError(f"DATA_SOURCES.md dataset not in registry: {row['name']}")
        row["key"] = by_name[row["name"]]
        rows.append(row)
    return rows


def main() -> int:
    DATA_SOURCES_MD.write_text(render(build_rows()))
    print(f"wrote {DATA_SOURCES_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
