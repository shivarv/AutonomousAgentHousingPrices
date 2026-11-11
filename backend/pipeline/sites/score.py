"""Candidate construction sites, step 3: score 0-100 and a plain-English summary.

Score = 100 x weighted mean of component scores in [0, 1] (WEIGHTS, which sum to 1).
Continuous components are percentile ranks among all screened sites statewide (best = 1,
worst = 0); the zoning component is 1 inside an MBTA Communities (3A) district, else 0.
A missing component scores 0 and is named in the site's flags (never imputed).
The summary is built only from the site's own features.

Run: uv run python -m pipeline.sites.score   (after pipeline.sites.features)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from pipeline.paths import PROCESSED_DIR
from pipeline.sites.features import FEATURES_FILE

log = logging.getLogger("pipeline.sites.score")

SCORED_FILE = PROCESSED_DIR / "site_scores.parquet"

# component -> (weight, plain-English description)
WEIGHTS: dict[str, tuple[float, str]] = {
    "need": (0.25, "Need Index within 5 km (population-weighted)"),
    "shortage": (0.20, "affordable-home shortage for extremely-low-income renters within 5 km"),
    "homeless": (0.15, "estimated people experiencing homelessness within 5 km"),
    "transit": (0.15, "closeness to the nearest MBTA/RTA stop"),
    "zoning": (0.10, "inside an MBTA Communities (Section 3A) multifamily district"),
    "land_cost": (0.10, "lower estimated land cost per sq ft"),
    "lot_size": (0.05, "larger lot"),
}


def pct_rank(s: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Percentile rank in [0, 1] (ties averaged); NaN stays NaN."""
    r = s.rank(method="average", pct=True, ascending=higher_is_better)
    n = s.notna().sum()
    if n <= 1:
        return r.where(s.isna(), 1.0)
    # rescale so the worst value is 0 and the best is 1
    return (r - 1 / n) / (1 - 1 / n)


def components(f: pd.DataFrame) -> pd.DataFrame:
    c = pd.DataFrame(index=f.index)
    c["need"] = pct_rank(f.need_index_5km)
    c["shortage"] = pct_rank(f.gap_eli_5km)
    c["homeless"] = pct_rank(f.homeless_est_5km)
    c["transit"] = pct_rank(f.nearest_stop_km, higher_is_better=False)
    c["zoning"] = f.in_mbta3a_district.astype(float)
    c["land_cost"] = pct_rank(f.tract_land_value_per_sqft, higher_is_better=False)
    c["lot_size"] = pct_rank(np.log(f.lot_size_acres))
    return c


def score(c: pd.DataFrame) -> pd.Series:
    total = sum(w for w, _ in WEIGHTS.values())
    s = sum(c[k].fillna(0.0) * w for k, (w, _) in WEIGHTS.items())
    return (100 * s / total).round(2)


def _fmt_int(v: float) -> str:
    return f"{v:,.0f}"


def _fmt_money(v: float) -> str:
    return f"${v / 1e6:,.1f} M" if v >= 1e6 else f"${v / 1e3:,.0f}k"


STRONG = 0.8


def strengths(f: pd.Series) -> list[str]:
    """Components where the site is in the top 20% statewide (or inside a 3A district)."""
    return [
        WEIGHTS[k][1]
        for k in WEIGHTS
        if pd.notna(f.get(f"component_{k}")) and f[f"component_{k}"] >= STRONG
    ]


def summary(f: pd.Series) -> str:
    """Plain-English reasons, built only from the site's own features."""
    parts = [
        f"{f.lot_size_acres:.1f}-acre parcel of {f.use_description} in {f.municipality}.",
    ]
    top = strengths(f)
    if top:
        parts.append("Scores well on: " + "; ".join(top) + ".")
    if pd.notna(f.need_index_5km):
        parts.append(f"Need Index within 5 km is {f.need_index_5km:.0f} of 100.")
    if pd.notna(f.gap_eli_5km):
        word = "shortage" if f.gap_eli_5km > 0 else "surplus"
        parts.append(
            f"Within 5 km there is an estimated {word} of {_fmt_int(abs(f.gap_eli_5km))} "
            "homes affordable to extremely-low-income renters."
        )
    if pd.notna(f.homeless_est_5km):
        parts.append(
            f"About {_fmt_int(f.homeless_est_5km)} people experiencing homelessness are "
            "estimated within 5 km (modelled estimate)."
        )
    parts.append(
        f"Nearest transit stop: {f.nearest_stop_name} ({f.nearest_stop_mode}, "
        f"{f.nearest_stop_km:.1f} km)."
    )
    if f.in_mbta3a_district:
        parts.append("Inside an MBTA Communities multifamily zoning district.")
    if pd.notna(f.est_land_cost):
        parts.append(
            f"Estimated land cost about {_fmt_money(f.est_land_cost)} "
            f"(${f.tract_land_value_per_sqft:.0f}/sq ft tract median assessed land value)."
        )
    if len(f.site_flags):
        parts.append("Note: " + "; ".join(f.site_flags) + ".")
    return " ".join(parts)


def build() -> pd.DataFrame:
    f = pd.read_parquet(FEATURES_FILE)
    c = components(f)
    f["score"] = score(c)
    missing = [k for k in c.columns if c[k].isna().any()]
    f["site_flags"] = [
        list(fl)
        + [f"no data for {WEIGHTS[k][1]} (scored 0)" for k in missing if pd.isna(c.at[i, k])]
        for i, fl in zip(f.index, f.site_flags, strict=True)
    ]
    for k in c.columns:
        f[f"component_{k}"] = c[k]
    f = f.sort_values(["score", "loc_id"], ascending=[False, True]).reset_index(drop=True)
    f["rank_state"] = np.arange(1, len(f) + 1)
    f["rank_county"] = f.groupby("county_geoid").cumcount() + 1
    f["summary"] = f.apply(summary, axis=1)
    return f


def run() -> None:
    f = build()
    f.to_parquet(SCORED_FILE)
    log.info(
        "scored %d sites; score %.1f-%.1f (median %.1f)",
        len(f),
        f.score.min(),
        f.score.max(),
        f.score.median(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
