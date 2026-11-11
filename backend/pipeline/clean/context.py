"""Housing context layers:

- subsidised_housing points (HUD LIHTC properties, HUD Picture of Subsidized Households
  project-based properties) and tract metrics (HUD-assisted units, LIHTC low-income units);
- transit stops (MBTA + RTAs) with mode;
- ZIP -> tract residential weights (2020 block housing units) and Zillow ZHVI/ZORI tract metrics;
- Eviction Lab filings on 2020 tracts.

Run: uv run python -m pipeline.clean.context
"""

from __future__ import annotations

import logging
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.clean.metrics_common import long_metric, safe_ratio
from pipeline.drops import record_drop, reset
from pipeline.geo import MA_CRS, WGS84
from pipeline.paths import INTERIM_DIR, PROCESSED_DIR, RAW_DIR

log = logging.getLogger("pipeline.clean.context")
PSH_YEAR = 2025
ZILLOW_YEAR = 2026  # latest month in the Zillow files is September 2026
EVICTION_YEARS = (2014, 2015, 2016)  # best-covered validated years for MA


def _tracts() -> gpd.GeoDataFrame:
    return gpd.read_parquet(INTERIM_DIR / "tracts_geom.parquet")


def _locate(df: pd.DataFrame, lat: str = "lat", lon: str = "lon") -> pd.Series:
    """Tract GEOID containing each point (NaN outside MA)."""
    pts = gpd.GeoDataFrame(df[[]], geometry=gpd.points_from_xy(df[lon], df[lat]), crs=WGS84).to_crs(
        MA_CRS
    )
    joined = gpd.sjoin(pts, _tracts(), how="left", predicate="within")
    return joined[~joined.index.duplicated()].geoid


# ---------------------------------------------------------------- subsidised housing
def build_subsidised(tract_ids: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(RAW_DIR / "hud_lihtc/lihtcpub.zip") as zf, zf.open("LIHTCPUB.xlsx") as fh:
        lihtc = pd.read_excel(fh, engine="calamine")
    lihtc = lihtc[lihtc.proj_st == "MA"].copy()
    lihtc_pts = pd.DataFrame(
        {
            "program": "LIHTC",
            "external_id": lihtc.hud_id.astype(str),
            "name": lihtc.project,
            "lat": pd.to_numeric(lihtc.latitude, errors="coerce"),
            "lon": pd.to_numeric(lihtc.longitude, errors="coerce"),
            "total_units": pd.to_numeric(lihtc.n_units, errors="coerce"),
            "assisted_units": pd.to_numeric(lihtc.li_units, errors="coerce"),
            "year": pd.to_numeric(lihtc.yr_pis, errors="coerce").where(lambda s: s < 8888),
            "source_key": "hud_lihtc",
        }
    )

    proj = pd.read_excel(RAW_DIR / "hud_psh/PROJECT_2025_2020census.xlsx", engine="calamine")
    proj = proj[proj.states.astype(str).str.startswith("MA ")].copy()
    units = pd.to_numeric(proj.total_units, errors="coerce")
    psh_pts = pd.DataFrame(
        {
            "program": proj.program_label.astype(str),
            "external_id": proj.code.astype(str),
            "name": proj.name,
            "lat": pd.to_numeric(proj.latitude, errors="coerce"),
            "lon": pd.to_numeric(proj.longitude, errors="coerce"),
            "total_units": units.where(units >= 0),  # negative = missing/suppressed code
            "assisted_units": units.where(units >= 0),
            "year": PSH_YEAR,
            "source_key": "hud_psh",
        }
    )
    pts = pd.concat([lihtc_pts, psh_pts], ignore_index=True)
    has_xy = pts.lat.notna() & pts.lon.notna() & (pts.lat != 0)
    pts["tract_geoid"] = pd.Series(dtype=object)
    pts.loc[has_xy, "tract_geoid"] = _locate(pts[has_xy]).values
    log.info(
        "subsidised points: %d (%d without coordinates, kept without tract)",
        len(pts),
        int((~has_xy).sum()),
    )

    # tract metrics
    t = pd.read_excel(RAW_DIR / "hud_psh/TRACT_AK_MN_2025_2020census.xlsx", engine="calamine")
    t = t[t.states.astype(str).str.startswith("MA ") & (t.program == 1)].copy()
    # codes are numbers (leading zero dropped); placeholders like 25XXX999999 = unknown tract
    t["geoid"] = t.code.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    unmatched = t[~t.geoid.isin(tract_ids)]
    record_drop("context", "HUD PSH tract rows with unknown/non-2020 tract code", len(unmatched))
    t = t[t.geoid.isin(tract_ids)]
    hud_units = pd.to_numeric(t.total_units, errors="coerce")
    flag = pd.Series(np.where(hud_units < 0, "suppressed/missing in HUD PSH (negative code)", None))
    metrics = [
        long_metric(
            t.geoid,
            "hud_assisted_units",
            PSH_YEAR,
            hud_units.where(hud_units >= 0),
            "hud_psh",
            flag=flag,
        )
    ]
    li = (
        lihtc_pts.assign(
            geoid=lihtc.fips2020.astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(11)
            .values
        )
        .groupby("geoid")
        .assisted_units.sum(min_count=1)
    )
    all_t = pd.Series(sorted(tract_ids))
    li_val = all_t.map(li).fillna(0.0)  # no LIHTC property in tract = 0 units (not missing)
    metrics.append(long_metric(all_t, "lihtc_low_income_units", 2024, li_val, "hud_lihtc"))
    return pts, pd.concat(metrics, ignore_index=True)


# ---------------------------------------------------------------- transit
MBTA_MODE = {"0": "subway", "1": "subway", "2": "rail", "3": "bus", "4": "ferry"}


def build_transit() -> pd.DataFrame:
    frames = []
    for path in sorted((RAW_DIR / "gtfs").glob("*.zip")):
        slug = path.stem
        with zipfile.ZipFile(path) as zf:
            member = next(n for n in zf.namelist() if n.endswith("stops.txt"))
            with zf.open(member) as fh:
                s = pd.read_csv(fh, dtype=str)
        lt = s.get("location_type", pd.Series("0", index=s.index)).fillna("0").str.strip()
        s = s[lt.isin(["0", ""])].copy()
        if slug == "mbta" and "vehicle_type" in s:
            mode = s.vehicle_type.map(MBTA_MODE).fillna("bus")
        else:
            mode = "bus"
        frames.append(
            pd.DataFrame(
                {
                    "agency": slug.upper(),
                    "stop_id": s.stop_id,
                    "name": s.stop_name.fillna(""),
                    "mode": mode,
                    "lat": pd.to_numeric(s.stop_lat, errors="coerce"),
                    "lon": pd.to_numeric(s.stop_lon, errors="coerce"),
                    "source_key": "mbta_gtfs" if slug == "mbta" else "rta_gtfs",
                }
            )
        )
    stops = pd.concat(frames, ignore_index=True).dropna(subset=["lat", "lon"])
    stops["tract_geoid"] = _locate(stops).values
    record_drop("context", "transit stops outside MA tracts", int(stops.tract_geoid.isna().sum()))
    return stops[stops.tract_geoid.notna()].drop_duplicates(["agency", "stop_id"])


# ---------------------------------------------------------------- ZIP -> tract
def build_zip_tracts() -> pd.DataFrame:
    blocks = gpd.read_file(
        RAW_DIR / "census_relationship/tl_2020_25_tabblock20.zip",
        columns=["GEOID20", "HOUSING20", "INTPTLAT20", "INTPTLON20"],
        ignore_geometry=True,
    )
    blocks = blocks[blocks.HOUSING20.astype(int) > 0]
    pts = gpd.GeoDataFrame(
        {"tract_geoid": blocks.GEOID20.str[:11].values, "hu": blocks.HOUSING20.astype(int).values},
        geometry=gpd.points_from_xy(
            blocks.INTPTLON20.astype(float), blocks.INTPTLAT20.astype(float)
        ),
        crs="EPSG:4269",
    ).to_crs(MA_CRS)
    zcta = gpd.read_file(
        RAW_DIR / "census_relationship/cb_2020_us_zcta520_500k.zip",
        bbox=(-73.6, 41.1, -69.8, 42.95),
    ).to_crs(MA_CRS)[["ZCTA5CE20", "geometry"]]
    j = gpd.sjoin(pts, zcta, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    unassigned = j.ZCTA5CE20.isna()
    record_drop(
        "context", "2020 blocks with housing outside any ZCTA polygon", int(unassigned.sum())
    )
    j = j[~unassigned]
    zt = j.groupby(["ZCTA5CE20", "tract_geoid"], as_index=False).hu.sum()
    zt["res_share_of_zip"] = zt.hu / zt.groupby("ZCTA5CE20").hu.transform("sum")
    zt["res_share_of_tract"] = zt.hu / zt.groupby("tract_geoid").hu.transform("sum")
    return zt.rename(columns={"ZCTA5CE20": "zcta"})[
        ["zcta", "tract_geoid", "res_share_of_zip", "res_share_of_tract"]
    ]


def _zip_to_tract(zip_values: pd.Series, zt: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Residential-share weighted mean of ZIP values per tract, renormalised over ZIPs that
    have a value. Returns (value, covered share of the tract's housing)."""
    d = zt.assign(v=zt.zcta.map(zip_values)).dropna(subset=["v"])
    covered = d.groupby("tract_geoid").res_share_of_tract.sum()
    value = (d.v * d.res_share_of_tract).groupby(d.tract_geoid).sum() / covered
    return value, covered


def build_zillow(zt: pd.DataFrame) -> pd.DataFrame:
    out = []
    for fname, key, metric in (
        ("Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv", "zillow_zhvi", "zhvi"),
        ("Zip_zori_uc_sfrcondomfr_sm_month.csv", "zillow_zori", "zori"),
    ):
        df = pd.read_csv(RAW_DIR / "zillow" / fname, dtype={"RegionName": str})
        df = df[df.State == "MA"].set_index(df[df.State == "MA"].RegionName.str.zfill(5))
        months = [c for c in df.columns if c[:2] in ("19", "20")]
        latest, five_ago = months[-1], months[-61]
        log.info("%s latest month %s, 5 years earlier %s", metric, latest, five_ago)
        for name, series in (
            (f"{metric}_latest", df[latest]),
            (f"{metric}_growth_5yr", df[latest] / df[five_ago] - 1),
        ):
            value, covered = _zip_to_tract(series.dropna(), zt)
            flag = pd.Series(
                np.where(covered < 0.999, "ZIP data covers only part of the tract's housing", None),
                index=covered.index,
            )
            out.append(
                long_metric(
                    pd.Series(value.index),
                    name,
                    ZILLOW_YEAR,
                    value,
                    key,
                    flag=flag.reindex(value.index),
                )
            )
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------- evictions
def build_evictions(renters: pd.Series) -> pd.DataFrame:
    m = pd.read_csv(
        RAW_DIR / "eviction_lab/tract_monthly_proprietary_valid_2000_2018_tracts2020.csv",
        dtype={"fips_tract": str, "fips_state": str},
    )
    m = m[(m.fips_state == "25") & m.year.isin(EVICTION_YEARS)]
    annual = m.groupby(["fips_tract", "year"]).filings_observed.sum()
    avg = annual.groupby("fips_tract").mean()
    rate = safe_ratio(avg, renters.reindex(avg.index))
    method = (
        f"mean annual observed filings {EVICTION_YEARS[0]}-{EVICTION_YEARS[-1]} "
        "(Eviction Lab, validated tract-years) / ACS 2020-2024 renter households"
    )
    g = pd.Series(avg.index)
    return pd.concat(
        [
            long_metric(
                g, "eviction_filings_annual", EVICTION_YEARS[-1], avg, "eviction_lab", method=method
            ),
            long_metric(
                g, "eviction_filing_rate", EVICTION_YEARS[-1], rate, "eviction_lab", method=method
            ),
        ],
        ignore_index=True,
    )


def run() -> None:
    reset("context")
    tracts = pd.read_parquet(PROCESSED_DIR / "tracts.parquet")
    tract_ids = set(tracts.geoid)
    pts, sub_metrics = build_subsidised(tract_ids)
    pts.to_parquet(PROCESSED_DIR / "subsidised_housing.parquet")
    build_transit().to_parquet(PROCESSED_DIR / "transit_stops.parquet")
    zt = build_zip_tracts()
    zt.to_parquet(PROCESSED_DIR / "zip_tracts.parquet")
    acs = pd.read_parquet(PROCESSED_DIR / "metrics_acs.parquet")
    renters = acs[acs.metric == "renter_households"].set_index("tract_geoid").value
    metrics = pd.concat(
        [sub_metrics, build_zillow(zt), build_evictions(renters)], ignore_index=True
    )
    metrics.to_parquet(PROCESSED_DIR / "metrics_context.parquet")
    log.info("context metrics: %s", metrics.groupby("metric").size().to_dict())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
