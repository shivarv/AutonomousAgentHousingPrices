"""Write reports/data_audit.md: rows, years, geography, missing-value rates and known issues for
every downloaded dataset (Massachusetts subset where the file is national).

Run: uv run python -m pipeline.audit
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field

import geopandas as gpd
import pandas as pd
import pyogrio

from pipeline.paths import RAW_DIR, REPORTS_DIR
from pipeline.sources import DATASETS

MA = "25"


@dataclass
class Audit:
    rows: str
    years: str
    geography: str
    missing: dict[str, float] = field(default_factory=dict)  # column -> share missing (0-1)
    issues: list[str] = field(default_factory=list)


def _missing(df: pd.DataFrame, cols: list[str], sentinels: tuple = ()) -> dict[str, float]:
    out = {}
    for c in cols:
        s = df[c]
        miss = s.isna()
        if sentinels:
            num = pd.to_numeric(s, errors="coerce")
            miss |= num.isin(sentinels)
        out[c] = float(miss.mean()) if len(s) else 0.0
    return out


def _zip_first(path, suffix: str) -> str:
    with zipfile.ZipFile(path) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(suffix))
    return f"/vsizip/{path}/{name}"


def audit_tiger_tracts() -> Audit:
    t = gpd.read_file(RAW_DIR / "tiger/tl_2026_25_tract.zip", ignore_geometry=True)
    water = int((t.ALAND == 0).sum())
    return Audit(
        f"{len(t):,} tracts",
        "2026 vintage (2020 tract definitions)",
        "census tract",
        _missing(t, ["GEOID", "ALAND", "INTPTLAT"]),
        [f"{water} tracts are water-only (ALAND = 0); they have no residents."],
    )


def audit_tiger_cousub() -> Audit:
    c = gpd.read_file(RAW_DIR / "tiger/tl_2026_25_cousub.zip", ignore_geometry=True)
    undefined = int((c.COUSUBFP == "00000").sum())
    return Audit(
        f"{len(c):,} records; {len(c) - undefined} cities/towns",
        "2026 vintage",
        "county subdivision (municipality)",
        _missing(c, ["GEOID", "NAME"]),
        [f"{undefined} 'County subdivisions not defined' water records excluded from the 351."],
    )


def audit_tiger_counties() -> Audit:
    c = gpd.read_file(RAW_DIR / "tiger/tl_2026_us_county.zip", ignore_geometry=True)
    ma = c[c.STATEFP == MA]
    return Audit(
        f"{len(c):,} US counties; {len(ma)} in MA",
        "2026 vintage",
        "county",
        _missing(ma, ["GEOID", "NAME"]),
        ["Several MA counties no longer have county government; used here as statistical units."],
    )


def audit_boston() -> Audit:
    b = gpd.read_file(RAW_DIR / "boston_neighbourhoods/boston_neighborhood_boundaries.geojson")
    return Audit(
        f"{len(b)} neighbourhoods",
        "current",
        "Boston neighbourhood",
        _missing(b, [c for c in b.columns if c != "geometry"][:4]),
        ["Neighbourhoods do not nest in tracts; tract membership is by area share."],
    )


def audit_coc() -> Audit:
    path = RAW_DIR / "hud_coc/CoC_GIS_State_Shapefile_MA_2025.zip"
    with zipfile.ZipFile(path) as zf:
        shps = [n for n in zf.namelist() if n.endswith(".shp")]
    nums = [s.split("/")[-1].removesuffix(".shp").replace("_", "-") for s in shps]
    return Audit(
        f"{len(shps)} CoCs",
        "2025",
        "Continuum of Care",
        {},
        [f"CoCs: {', '.join(nums)}. One shapefile per CoC inside the zip."],
    )


def audit_acs() -> Audit:
    table = json.loads((RAW_DIR / "acs/acs5_2024_tracts_ma.json").read_text())
    df = pd.DataFrame(table[1:], columns=table[0])
    est = [c for c in df.columns if c.endswith("E") and c[0] == "B"]
    # Census API annotation values (e.g. -666666666) mean "not available"
    miss = _missing(df, est, sentinels=(-666666666, -999999999, -888888888, -222222222))
    return Audit(
        f"{len(df):,} tracts x {len(est)} estimates (+ margins of error)",
        "2020-2024 5-year",
        "census tract",
        miss,
        [
            "Medians (income, rent, value) are suppressed for tracts with few households.",
            "5-year estimates have large margins of error in small tracts.",
        ],
    )


def audit_chas() -> Audit:
    path = RAW_DIR / "chas/2018thru2022-140-csv.zip"
    with zipfile.ZipFile(path) as zf, zf.open("140/Table18C.csv") as fh:
        df = pd.read_csv(fh, encoding="latin-1", dtype={"st": str})
    ma = df[df.st.str.zfill(2) == MA]
    cols = [c for c in ma.columns if c.startswith("T18C_est")][:10]
    return Audit(
        f"{len(df):,} US tracts; {len(ma):,} in MA (per table)",
        "2018-2022 ACS",
        "census tract",
        _missing(ma, cols),
        [
            "CHAS counts are rounded and derived from ACS samples (high margins in small tracts).",
            "Tract geography is 2020 definitions, matching TIGER 2026.",
        ],
    )


def _pit_hic(fname: str, label: str) -> Audit:
    path = RAW_DIR / "hud_pit_hic" / fname
    engine = "calamine"
    x = pd.ExcelFile(path, engine=engine)
    years = sorted(s for s in x.sheet_names if s.isdigit())
    latest = pd.read_excel(x, years[-1])
    ma = latest[latest["CoC Number"].astype(str).str.startswith("MA-")]
    cols = [c for c in latest.columns[:8] if c != "CoC Number"]
    return Audit(
        f"{len(ma)} MA CoCs in {years[-1]} ({len(latest):,} US CoCs)",
        f"{years[0]}-{years[-1]}",
        "Continuum of Care",
        _missing(ma, cols),
        [
            f"{label} figures exist only per CoC; CoC mergers change series over time.",
            "Figures describe a single night in late January.",
        ],
    )


def audit_lihtc() -> Audit:
    path = RAW_DIR / "hud_lihtc/lihtcpub.zip"
    with zipfile.ZipFile(path) as zf, zf.open("LIHTCPUB.xlsx") as fh:
        df = pd.read_excel(fh, engine="calamine")
    ma = df[df["proj_st"] == "MA"]
    known = ma.yr_pis[ma.yr_pis < 8888]
    return Audit(
        f"{len(ma):,} MA properties ({len(df):,} US)",
        f"placed in service {int(known.min())}-{int(known.max())}",
        "property (lat/lon)",
        _missing(ma, ["latitude", "longitude", "li_units", "n_units", "yr_pis"]),
        ["YR_PIS 8888/9999 are codes for unknown years.", "Some properties lack coordinates."],
    )


def audit_psh() -> Audit:
    df = pd.read_excel(RAW_DIR / "hud_psh/TRACT_AK_MN_2025_2020census.xlsx", engine="calamine")
    ma = df[df["states"].astype(str).str.startswith("MA ")]
    tracts = ma["code"].nunique()
    return Audit(
        f"{len(ma):,} MA tract x program rows ({tracts:,} tracts)",
        "2025",
        "census tract",
        _missing(ma, ["total_units", "people_total", "hh_income"], sentinels=(-1, -4, -5)),
        [
            "Negative codes mean missing (-1), suppressed for privacy (-4) or not reported (-5).",
            "Tract code is stored as a number (leading zero dropped).",
        ],
    )


def audit_gtfs(slugs: list[str]) -> Audit:
    total = 0
    issues = []
    for slug in slugs:
        with zipfile.ZipFile(RAW_DIR / f"gtfs/{slug}.zip") as zf:
            names = zf.namelist()
            member = next((n for n in names if n.endswith("stops.txt")), None)
            if member is None:
                issues.append(f"{slug}: no stops.txt")
                continue
            with zf.open(member) as fh:
                stops = pd.read_csv(fh, dtype=str)
            total += len(stops)
            with zf.open(
                next(
                    n
                    for n in names
                    if n.endswith("calendar.txt") or n.endswith("calendar_dates.txt")
                )
            ) as fh:
                cal = pd.read_csv(fh, dtype=str)
            end_col = "end_date" if "end_date" in cal else "date"
            end = cal[end_col].dropna().max()
            note = ""
            if not isinstance(end, str):
                end = "unknown (no dates in calendar.txt)"
            if isinstance(end, str) and end < "20261110":
                note = " (feed expired; stop locations used as last published)"
            issues.append(f"{slug}: {len(stops):,} stops, service through {end}{note}")
    return Audit(
        f"{total:,} stops in {len(slugs)} feeds", "current feeds", "stop (lat/lon)", {}, issues
    )


def _zillow(fname: str) -> Audit:
    df = pd.read_csv(RAW_DIR / "zillow" / fname, dtype={"RegionName": str})
    ma = df[df.State == "MA"]
    months = [c for c in df.columns if c[:2] in ("19", "20")]
    last = months[-1]
    return Audit(
        f"{len(ma):,} MA ZIPs ({len(df):,} US)",
        f"{months[0][:7]} to {last[:7]} monthly",
        "ZIP code",
        {last: float(ma[last].isna().mean()), months[-61]: float(ma[months[-61]].isna().mean())},
        ["ZIP codes are postal routes, not areas; moved to tracts via ZCTA weights."],
    )


def audit_zcta() -> Audit:
    rel = pd.read_csv(
        RAW_DIR / "census_relationship/tab20_zcta520_tract20_natl.txt",
        sep="|",
        dtype=str,
    )
    ma = rel[rel.GEOID_TRACT_20.str.startswith(MA)]
    blocks = pyogrio.read_info(RAW_DIR / "census_relationship/tl_2020_25_tabblock20.zip")
    return Audit(
        f"{len(ma):,} MA ZCTA-tract pairs; {blocks['features']:,} MA blocks",
        "2020",
        "ZCTA x tract; block",
        {"GEOID_ZCTA5_20": float(ma.GEOID_ZCTA5_20.isna().mean())},
        ["Rows with an empty ZCTA are tract parts outside any ZCTA (water/unpopulated)."],
    )


def audit_parcels() -> Audit:
    path = _zip_first(RAW_DIR / "massgis_parcels/MassGIS_L3_Parcels_gdb.zip", ".gdb/")
    cols = [
        "USE_CODE",
        "LOT_SIZE",
        "LAND_VAL",
        "BLDG_VAL",
        "TOTAL_VAL",
        "FY",
        "YEAR_BUILT",
        "RES_AREA",
        "TOWN_ID",
    ]
    df = pyogrio.read_dataframe(path, layer="L3_ASSESS", columns=cols, read_geometry=False)
    poly = pyogrio.read_info(path, layer="L3_TAXPAR_POLY")["features"]
    miss = _missing(df, cols)
    for c in ("LOT_SIZE", "TOTAL_VAL", "LAND_VAL"):
        miss[f"{c} = 0"] = float((pd.to_numeric(df[c], errors="coerce") == 0).mean())
    fy = df.FY[df.FY > 0]
    return Audit(
        f"{len(df):,} assessing records; {poly:,} parcel polygons",
        f"fiscal years {int(fy.min())}-{int(fy.max())}",
        "parcel",
        miss,
        [
            "Fiscal year differs by town; values are assessed (not market) values.",
            "Condominium units share one polygon (many assessing rows per LOC_ID).",
            "Use codes follow the MA DOR classification; some towns add local suffixes.",
            "Owner name/address columns exist but are never read.",
        ],
    )


def _layer_info(folder: str, fname: str, notes: list[str]) -> Audit:
    path = _zip_first(RAW_DIR / folder / fname, ".shp")
    info = pyogrio.read_info(path)
    return Audit(
        f"{info['features']:,} polygons",
        "see DATA_SOURCES.md",
        "polygon",
        {},
        [f"CRS: {info['crs']}", *notes],
    )


def audit_osm() -> Audit:
    d = json.loads((RAW_DIR / "osm_shelters/osm_shelters_ma.json").read_text())
    el = d["elements"]
    cap = sum("capacity" in e.get("tags", {}) for e in el)
    return Audit(
        f"{len(el)} shelters",
        "snapshot",
        "point",
        {"capacity": 1 - cap / len(el) if el else 1.0},
        [
            "Very incomplete: OSM maps few shelters and almost none have bed counts.",
            "DV-tagged facilities excluded at query time.",
        ],
    )


def audit_eviction() -> Audit:
    df = pd.read_csv(
        RAW_DIR / "eviction_lab/tract_proprietary_valid_2000_2018_y2024m12.csv",
        dtype={"fips": str},
    )
    ma = df[df.fips.str.startswith(MA)]
    return Audit(
        f"{len(ma):,} MA tract-years ({ma.fips.nunique():,} tracts)",
        f"{ma.year.min()}-{ma.year.max()}",
        "census tract",
        _missing(ma, ["filings", "filing_rate"]),
        [
            "Only 'validated' tract-years are included; coverage of MA tracts is partial.",
            "Latest year 2018: predates the pandemic moratorium and current conditions.",
        ],
    )


AUDITS: dict[str, Callable[[], Audit]] = {
    "tiger_tracts": audit_tiger_tracts,
    "tiger_cousub": audit_tiger_cousub,
    "tiger_counties": audit_tiger_counties,
    "boston_neighbourhoods": audit_boston,
    "hud_coc_boundaries": audit_coc,
    "acs5": audit_acs,
    "hud_chas": audit_chas,
    "hud_pit": lambda: _pit_hic("2007-2025-PIT-Counts-by-CoC.xlsb", "Homeless count"),
    "hud_hic": lambda: _pit_hic("2007-2025-HIC-Counts-by-CoC.xlsx", "Bed inventory"),
    "hud_lihtc": audit_lihtc,
    "hud_psh": audit_psh,
    "mbta_gtfs": lambda: audit_gtfs(["mbta"]),
    "rta_gtfs": lambda: audit_gtfs(
        [
            "bat",
            "brta",
            "cata",
            "ccrta",
            "frta",
            "gatra",
            "lrta",
            "mart",
            "mvrta",
            "mwrta",
            "nrta",
            "pvta",
            "srta",
            "vta",
            "wrta",
        ]
    ),
    "zillow_zhvi": lambda: _zillow("Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"),
    "zillow_zori": lambda: _zillow("Zip_zori_uc_sfrcondomfr_sm_month.csv"),
    "census_zcta_tract": audit_zcta,
    "massgis_parcels": audit_parcels,
    "massgis_openspace": lambda: _layer_info(
        "massgis_openspace", "openspace.zip", ["Includes unprotected recreation land."]
    ),
    "massgis_wetlands": lambda: _layer_info(
        "massgis_wetlands", "wetlandsdep_poly.zip", ["Mapped from 2005 imagery."]
    ),
    "massgis_flood": lambda: _layer_info(
        "massgis_flood",
        "nfhl.zip",
        ["Flood zones per FEMA FLD_ZONE; 100-year = SFHA zones (A*, V*)."],
    ),
    "massgis_mbta3a": lambda: _layer_info(
        "massgis_mbta3a", "MBTA3A.zip", ["Districts still being adopted; layer changes often."]
    ),
    "osm_shelters": audit_osm,
    "eviction_lab": audit_eviction,
}


def render(results: dict[str, Audit | Exception]) -> str:
    names = {d.key: d.name for d in DATASETS}
    out = [
        "# Data audit",
        "",
        "Generated by `uv run --project backend python -m pipeline.audit` from the untouched files",
        "in data/raw/. Missing-value rates are shares of rows (MA subset) that are empty or carry",
        "a 'not available' code. See DATA_SOURCES.md for URLs, licences and download dates.",
        "",
        "| Dataset | Rows | Years | Geography |",
        "|---|---|---|---|",
    ]
    for key, res in results.items():
        if isinstance(res, Exception):
            out.append(f"| {names[key]} | audit failed | | |")
        else:
            out.append(f"| {names[key]} | {res.rows} | {res.years} | {res.geography} |")
    out.append("")
    for key, res in results.items():
        out += [f"## {names[key]}", ""]
        if isinstance(res, Exception):
            out += [f"Audit failed: `{res}`", ""]
            continue
        if res.missing:
            out.append(
                "Missing values: " + ", ".join(f"{c} {v:.1%}" for c, v in res.missing.items()) + "."
            )
            out.append("")
        if res.issues:
            out += [f"- {i}" for i in res.issues]
            out.append("")
    return "\n".join(out)


def main() -> int:
    results: dict[str, Audit | Exception] = {}
    for key, fn in AUDITS.items():
        try:
            results[key] = fn()
        except Exception as exc:  # report, don't hide: the failure is written into the audit
            results[key] = exc
        print(key, "ok" if not isinstance(results[key], Exception) else results[key])
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "data_audit.md").write_text(render(results))
    return 1 if any(isinstance(r, Exception) for r in results.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
