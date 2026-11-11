"""Modelled distribution of each CoC's official PIT count across its tracts (ESTIMATES).

Official homelessness counts exist only per Continuum of Care. This step allocates the latest
PIT count of each CoC to the tracts whose primary CoC it is:

    estimate_t = PIT_c * w_t / sum(w over tracts of c)

with w = the tract's extremely-low-income renter households paying > 50% of income for rent
(HUD CHAS 2018-2022, Table 8). Sheltered and unsheltered counts are allocated separately with
the same weight and added, so tract estimates sum exactly (floating point) to the CoC
sheltered, unsheltered and total counts. Values are not rounded: they are expected counts, not
people.

PLAN.md asks for sheltered people to be allocated by each tract's share of the CoC's shelter
beds; no public source gives shelter bed counts by location (BLOCKERS.md), so the sheltered
count uses the same at-risk weight. If a CoC's weights sum to 0, the tract population share
(ACS 2020-2024) is used and the rows are flagged.

Run: uv run python -m pipeline.features.homeless_estimate   (then pipeline.load, aggregate)
"""

from __future__ import annotations

import logging

import pandas as pd

from pipeline.clean.metrics_common import METRIC_COLUMNS, long_metric
from pipeline.paths import PROCESSED_DIR

log = logging.getLogger("pipeline.features.homeless_estimate")

WEIGHT_METRIC = "eli_severely_burdened_renters"
FALLBACK_METRIC = "population"
SOURCE = "hud_pit"
METHOD = (
    "ESTIMATE: HUD PIT {year} count of the tract's CoC ({part}) allocated to its tracts by each "
    "tract's share of the CoC's extremely-low-income renter households with severe rent burden "
    "(HUD CHAS 2018-2022); sheltered people use the same weight because shelter bed locations "
    "are not published. Sums exactly to the official CoC count. Not a count of people in the tract."
)
FALLBACK_FLAG = "CoC has no severely burdened ELI renters: allocated by population share (ACS)"
PARTS = {
    "homeless_estimate_sheltered": "sheltered",
    "homeless_estimate_unsheltered": "unsheltered",
}


def allocate(
    tracts: pd.DataFrame, weights: pd.Series, fallback: pd.Series, pit: pd.DataFrame
) -> pd.DataFrame:
    """tracts: geoid, coc_number. weights/fallback: indexed by geoid. pit: one row per CoC with
    coc_number, year, sheltered, unsheltered, total. Returns geoid, coc_number, year, share,
    flag, sheltered, unsheltered, total."""
    t = tracts[["geoid", "coc_number"]].copy()
    t["w"] = t.geoid.map(weights).astype(float)
    t["w_fb"] = t.geoid.map(fallback).astype(float)
    if t.w.isna().any():
        raise ValueError(f"{int(t.w.isna().sum())} tracts lack the weight metric {WEIGHT_METRIC}")
    w_sum = t.groupby("coc_number").w.transform("sum")
    fb_sum = t.groupby("coc_number").w_fb.transform("sum")
    use_fb = w_sum <= 0
    t["share"] = (t.w / w_sum).where(~use_fb, t.w_fb / fb_sum)
    t["flag"] = use_fb.map({True: FALLBACK_FLAG, False: None})
    missing = set(t.coc_number) - set(pit.coc_number)
    if missing:
        raise ValueError(f"no PIT count for CoCs {sorted(missing)}")
    t = t.merge(pit, on="coc_number", how="left")
    for part in ("sheltered", "unsheltered"):
        t[part] = t[part].astype(float) * t.share
    t["total"] = t.sheltered + t.unsheltered
    return t[["geoid", "coc_number", "year", "share", "flag", "sheltered", "unsheltered", "total"]]


def latest_pit(pit: pd.DataFrame) -> pd.DataFrame:
    year = int(pit.year.max())
    latest = pit[pit.year == year].copy()
    bad = latest[latest.sheltered.isna() | latest.unsheltered.isna()]
    if len(bad):
        raise ValueError(f"PIT {year} lacks sheltered/unsheltered for {list(bad.coc_number)}")
    if not (latest.sheltered + latest.unsheltered == latest.total).all():
        raise ValueError("PIT sheltered + unsheltered != total")
    return latest


def build() -> pd.DataFrame:
    tracts = pd.read_parquet(PROCESSED_DIR / "tracts.parquet")
    chas = pd.read_parquet(PROCESSED_DIR / "metrics_chas.parquet")
    acs = pd.read_parquet(PROCESSED_DIR / "metrics_acs.parquet")
    weights = chas[chas.metric == WEIGHT_METRIC].set_index("tract_geoid").value
    pop = acs[acs.metric == FALLBACK_METRIC].set_index("tract_geoid").value
    pit = latest_pit(pd.read_parquet(PROCESSED_DIR / "homelessness_counts.parquet"))
    year = int(pit.year.iloc[0])
    a = allocate(tracts, weights, pop, pit)
    frames = []
    for metric, part in [*PARTS.items(), ("homeless_estimate", "sheltered + unsheltered")]:
        col = PARTS.get(metric, "total")
        method = METHOD.format(year=year, part=part)
        frames.append(
            long_metric(
                a.geoid, metric, year, a[col], SOURCE, flag=a.flag, is_estimate=True, method=method
            )
        )
    out = pd.concat(frames, ignore_index=True)[METRIC_COLUMNS]
    log.info(
        "PIT %d: allocated %.0f people to %d tracts (%d tracts on population fallback)",
        year,
        a.total.sum(),
        len(a),
        int(a.flag.notna().sum()),
    )
    return out


def run() -> None:
    build().to_parquet(PROCESSED_DIR / "metrics_homeless.parquet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
