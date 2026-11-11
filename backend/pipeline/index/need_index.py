"""Housing Need Index (0-100) per tract.

index = 100 x sum(w_k x score_k) / sum(w_k) over the components the tract has (equal weights
by default). A tract needs at least MIN_COMPONENTS of the 8 components; otherwise its index is
NULL and flagged. Tracts missing some components carry a flag naming them (the weights are
renormalised over the available ones; no value is imputed).

Stores, as tract metrics: need_index, need_score_<component> (0-1) for each component, the
raw components not already stored (affordable_gap_per_eli_renter, homeless_estimate_per_1000,
distance_to_service_km) and need_index_components (number of components used).

Run: uv run python -m pipeline.index.need_index   (then pipeline.load)
"""

from __future__ import annotations

import logging

import pandas as pd

from pipeline.clean.metrics_common import METRIC_COLUMNS, long_metric
from pipeline.index.components import COMPONENT_KEYS, COMPONENTS, raw_components, scores
from pipeline.paths import PROCESSED_DIR

log = logging.getLogger("pipeline.index.need_index")

MIN_COMPONENTS = 5
INDEX_YEAR = 2026  # year the index was built from the latest inputs (inputs span 2014-2026)
INDEX_SOURCE = "hud_chas"  # primary component; the method text lists every input source
EQUAL_WEIGHTS: dict[str, float] = {k: 1.0 for k in COMPONENT_KEYS}
NEW_RAW = ("affordable_gap_per_eli_renter", "homeless_estimate_per_1000", "distance_to_service_km")
INPUT_METRIC_FILES = ["metrics_acs", "metrics_context", "metrics_chas", "metrics_homeless"]


def index_from_scores(
    sc: pd.DataFrame, weights: dict[str, float], min_components: int = MIN_COMPONENTS
) -> pd.DataFrame:
    """sc: tracts x components (0-1, NaN = missing). Returns index (0-100 or NaN), n_used,
    flag."""
    w = pd.Series(weights, dtype=float).reindex(sc.columns).fillna(0.0)
    if (w < 0).any() or w.sum() <= 0:
        raise ValueError("weights must be non-negative and not all zero")
    used = sc.columns[w > 0]
    s = sc[used]
    avail = s.notna()
    wsum = (avail * w[used]).sum(axis=1)
    value = 100 * (s.fillna(0.0) * w[used]).sum(axis=1) / wsum.where(wsum > 0)
    n_used = avail.sum(axis=1)
    enough = n_used >= min_components
    value = value.where(enough)
    flags = []
    for geoid in sc.index:
        missing = [c for c in used if not avail.loc[geoid, c]]
        if not enough[geoid]:
            flags.append(
                f"index not computed: only {n_used[geoid]} of {len(used)} components "
                f"(minimum {min_components}); missing {', '.join(missing)}"
            )
        elif missing:
            flags.append(f"missing components (weights renormalised): {', '.join(missing)}")
        else:
            flags.append(None)
    return pd.DataFrame(
        {"need_index": value.clip(0, 100), "n_used": n_used, "flag": flags}, index=sc.index
    )


def _inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics = pd.concat(
        [pd.read_parquet(PROCESSED_DIR / f"{f}.parquet") for f in INPUT_METRIC_FILES],
        ignore_index=True,
    )
    tracts = pd.read_parquet(PROCESSED_DIR / "tracts.parquet")
    points = pd.concat(
        [
            pd.read_parquet(PROCESSED_DIR / "shelters.parquet")[["lat", "lon"]],
            pd.read_parquet(PROCESSED_DIR / "subsidised_housing.parquet")[["lat", "lon"]],
        ],
        ignore_index=True,
    )
    return metrics, tracts, points


def compute() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (raw components, scores, equal-weight index)."""
    metrics, tracts, points = _inputs()
    raw = raw_components(metrics, tracts, points)
    sc = scores(raw)
    return raw, sc, index_from_scores(sc, EQUAL_WEIGHTS)


def build() -> pd.DataFrame:
    raw, sc, idx = compute()
    geoids = pd.Series(raw.index)
    frames = []
    by_key = {c.key: c for c in COMPONENTS}
    for key in NEW_RAW:
        c = by_key[key]
        frames.append(
            long_metric(
                geoids,
                key,
                c.year,
                raw[key].reset_index(drop=True),
                c.source_key,
                is_estimate=key == "homeless_estimate_per_1000",
                method=c.method,
            )
        )
    for c in COMPONENTS:
        frames.append(
            long_metric(
                geoids,
                f"need_score_{c.key}",
                INDEX_YEAR,
                sc[c.key].reset_index(drop=True),
                c.source_key,
                is_estimate=c.key == "homeless_estimate_per_1000",
                method=f"statewide percentile rank (0-1) of {c.key}: {c.method}",
            )
        )
    sources = ", ".join(sorted({c.source_key for c in COMPONENTS}))
    method = (
        f"Housing Need Index: 100 x equal-weight mean of the 0-1 percentile scores of "
        f"{', '.join(COMPONENT_KEYS)} available for the tract (minimum {MIN_COMPONENTS} of "
        f"{len(COMPONENT_KEYS)}). Inputs: {sources}. The homeless component is an estimate."
    )
    flag = pd.Series(idx.flag.values)
    frames.append(
        long_metric(
            geoids,
            "need_index",
            INDEX_YEAR,
            idx.need_index.reset_index(drop=True),
            INDEX_SOURCE,
            flag=flag,
            method=method,
        )
    )
    frames.append(
        long_metric(
            geoids,
            "need_index_components",
            INDEX_YEAR,
            idx.n_used.reset_index(drop=True),
            INDEX_SOURCE,
            method="number of Need Index components available for the tract",
        )
    )
    out = pd.concat(frames, ignore_index=True)[METRIC_COLUMNS]
    log.info(
        "need index: %d tracts, %d without index, %d with missing components",
        len(idx),
        int(idx.need_index.isna().sum()),
        int(idx.flag.notna().sum()),
    )
    return out


def run() -> None:
    build().to_parquet(PROCESSED_DIR / "metrics_need.parquet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
