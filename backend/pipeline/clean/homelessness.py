"""HUD PIT counts and HIC beds per MA CoC and year; OSM shelters located in tracts.

Historical CoCs that later merged are summed into their current (post-merger) CoC using HUD's
"CoC Mergers" sheet, so every year is reported on today's 11 MA CoCs. Years 2007-2011 include
CoCs (MA-501 Holyoke, MA-514 Framingham/Waltham) that HUD lists in no merger record, so they
cannot be placed on today's boundaries; the series therefore starts in FIRST_YEAR = 2012.

Run: uv run python -m pipeline.clean.homelessness
"""

from __future__ import annotations

import json
import logging

import geopandas as gpd
import pandas as pd

from pipeline.drops import record_drop, reset
from pipeline.geo import MA_CRS, WGS84
from pipeline.paths import INTERIM_DIR, PROCESSED_DIR, RAW_DIR

log = logging.getLogger("pipeline.clean.homelessness")
PIT = RAW_DIR / "hud_pit_hic/2007-2025-PIT-Counts-by-CoC.xlsb"
HIC = RAW_DIR / "hud_pit_hic/2007-2025-HIC-Counts-by-CoC.xlsx"
FIRST_YEAR = 2012


def merger_map(current: set[str]) -> dict[str, str]:
    m = pd.read_excel(PIT, "CoC Mergers", engine="calamine")
    m.columns = [str(c).strip() for c in m.columns]
    pre = next(c for c in m.columns if "Pre" in c)
    post = next(c for c in m.columns if "Post" in c)
    mapping = dict(
        zip(m[pre].astype(str).str.strip(), m[post].astype(str).str.strip(), strict=True)
    )

    def resolve(code: str) -> str:
        seen = set()
        while code in mapping and code not in current and code not in seen:
            seen.add(code)
            code = mapping[code]
        return code

    return {k: resolve(k) for k in mapping}


def _year_sheets(path, engine: str) -> list[str]:
    sheets = pd.ExcelFile(path, engine=engine).sheet_names
    return [s for s in sheets if s.isdigit() and int(s) >= FIRST_YEAR]


def build_pit(current: set[str]) -> pd.DataFrame:
    mapping = merger_map(current)
    rows = []
    for sheet in _year_sheets(PIT, "calamine"):
        d = pd.read_excel(PIT, sheet, engine="calamine")
        d = d[d["CoC Number"].astype(str).str.startswith("MA-")].copy()
        d["coc"] = d["CoC Number"].astype(str).map(lambda c: mapping.get(c, c))
        unsheltered = (
            d["Unsheltered Homeless"]
            if "Unsheltered Homeless" in d
            else d["Overall Homeless"] - d["Sheltered Total Homeless"]
        )
        part = pd.DataFrame(
            {
                "coc_number": d.coc,
                "year": int(sheet),
                "total": d["Overall Homeless"],
                "sheltered": d["Sheltered Total Homeless"],
                "unsheltered": unsheltered,
            }
        )
        rows.append(part)
    pit = pd.concat(rows).groupby(["coc_number", "year"], as_index=False).sum(min_count=1)
    unknown = set(pit.coc_number) - current
    if unknown:
        raise ValueError(f"PIT CoCs not mapped to a current CoC: {sorted(unknown)}")
    return pit


def build_hic(current: set[str]) -> pd.DataFrame:
    """Year-round beds by type. The total is always ES + TH + SH (some years' published totals
    also include rapid re-housing, so they are not used)."""
    mapping = merger_map(current)
    # column names (spaces removed) used by HUD in different years, first match wins
    components = {
        "emergency_shelter_beds": [
            "TotalYear-RoundBeds(ES)",
            "TotalEmergencyShelter(ES)Beds(excludingseasonal+overflow)",
        ],
        "transitional_beds": ["TotalYear-RoundBeds(TH)", "TotalTransitionalHousing(TH)Beds"],
        "safe_haven_beds": ["TotalYear-RoundBeds(SH)", "TotalSafeHaven(SH)Beds"],
    }
    rows = []
    for sheet in _year_sheets(HIC, "calamine"):
        raw = pd.read_excel(HIC, sheet, engine="calamine", header=None)
        header_row = next(
            i for i in range(5) if str(raw.iloc[i, 0]).strip() in ("CoC Number", "CoC")
        )
        names = [str(c).replace(" ", "") for c in raw.iloc[header_row]]
        d = raw.iloc[header_row + 1 :].copy()
        d.columns = range(len(names))
        coc = d[0].astype(str).str.strip()
        keep = coc.str.startswith("MA-")
        part = pd.DataFrame({"coc_number": coc[keep].map(lambda c: mapping.get(c, c))})
        for dst, candidates in components.items():
            src = next((c for c in candidates if c in names), None)
            if src is None:
                raise ValueError(f"HIC {sheet}: no column for {dst}")
            part[dst] = pd.to_numeric(d.loc[keep, names.index(src)], errors="coerce")
        part["total_year_round_beds"] = part[list(components)].sum(axis=1, min_count=3)
        part["year"] = int(sheet)
        rows.append(part)
    hic = pd.concat(rows).groupby(["coc_number", "year"], as_index=False).sum(min_count=1)
    unknown = set(hic.coc_number) - current
    if unknown:
        raise ValueError(f"HIC CoCs not mapped to a current CoC: {sorted(unknown)}")
    return hic


def build_shelters() -> pd.DataFrame:
    data = json.loads((RAW_DIR / "osm_shelters/osm_shelters_ma.json").read_text())
    recs = []
    for e in data["elements"]:
        tags = e.get("tags", {})
        if any(k in tags.get("social_facility:for", "") for k in ("abused", "victim", "woman")):
            continue  # defensive: DV-related facilities are never stored
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None or lon is None:
            continue
        cap = tags.get("capacity")
        recs.append(
            {
                "external_id": f"osm:{e['type']}/{e['id']}",
                "name": tags.get("name", "Unnamed shelter"),
                "shelter_type": "homeless shelter",
                "beds": int(cap) if cap and cap.isdigit() else None,
                "lat": float(lat),
                "lon": float(lon),
            }
        )
    df = pd.DataFrame(recs)
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=WGS84).to_crs(
        MA_CRS
    )
    tracts = gpd.read_parquet(INTERIM_DIR / "tracts_geom.parquet")
    cocs = gpd.read_parquet(INTERIM_DIR / "cocs_geom.parquet")
    pts = gpd.sjoin(pts, tracts, how="left", predicate="within").drop(columns="index_right")
    pts = gpd.sjoin(pts, cocs, how="left", predicate="within").drop(columns="index_right")
    out = pd.DataFrame(pts.drop(columns="geometry")).rename(columns={"geoid": "tract_geoid"})
    # OSM sometimes maps one facility twice (node + building outline): keep one per name/tract
    deduped = out.drop_duplicates("external_id").drop_duplicates(["name", "tract_geoid"])
    record_drop(
        "homelessness",
        "duplicate OSM shelter features (same name and tract)",
        len(out) - len(deduped),
    )
    return deduped


def run() -> None:
    reset("homelessness")
    record_drop("homelessness", f"PIT/HIC year sheets before {FIRST_YEAR} (unmappable CoCs)", 5)
    current = set(pd.read_parquet(PROCESSED_DIR / "cocs.parquet").coc_number)
    pit = build_pit(current)
    hic = build_hic(current)
    shelters = build_shelters()
    log.info(
        "PIT rows %d (%d-%d), HIC rows %d, shelters %d",
        len(pit),
        pit.year.min(),
        pit.year.max(),
        len(hic),
        len(shelters),
    )
    pit.to_parquet(PROCESSED_DIR / "homelessness_counts.parquet")
    hic.to_parquet(PROCESSED_DIR / "coc_bed_counts.parquet")
    shelters.to_parquet(PROCESSED_DIR / "shelters.parquet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
