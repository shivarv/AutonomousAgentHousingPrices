"""Affordable housing shortage per tract from HUD CHAS 2018-2022.

Definitions (renter households; HAMFI = HUD area median family income):
- eli_renter_households: renters with income <= 30% HAMFI (Table 8, T8_est69)
- vli_renter_households: renters with income <= 50% HAMFI (T8_est69 + T8_est82)
- eli_severely_burdened_renters: ELI renters paying > 50% of income (T8_est76)
- vli_severely_burdened_renters: <= 50% HAMFI renters paying > 50% (T8_est76 + T8_est89)
- units_affordable_available_eli: units with rent <= RHUD30 that are occupied by an ELI
  household (Table 15C T15C_est5) or vacant for rent at that level (Table 14B T14B_est4)
- units_affordable_available_vli: units with rent <= RHUD50 occupied by a <= 50% HAMFI household
  (T15C_est5 + est9 + est26 + est30) or vacant for rent at <= RHUD50 (T14B_est4 + est8)
- affordable_gap_eli = eli_renter_households - units_affordable_available_eli (negative = surplus)
- affordable_gap_vli likewise; affordable_units_per_100_eli = 100 * available / ELI renters.

Units lacking complete kitchen or plumbing are not counted as available (CHAS 15C/14B
subtotals cover complete-facility units only). MOEs: sqrt of summed squared MOEs.

Run: uv run python -m pipeline.features.affordability
"""

from __future__ import annotations

import logging
import zipfile

import numpy as np
import pandas as pd

from pipeline.clean.metrics_common import long_metric, safe_ratio
from pipeline.paths import PROCESSED_DIR, RAW_DIR

log = logging.getLogger("pipeline.features.affordability")
CHAS_ZIP = RAW_DIR / "chas/2018thru2022-140-csv.zip"
CHAS_YEAR = 2022  # end year of the 2018-2022 period
SOURCE = "hud_chas"


def _table(name: str, cols: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(CHAS_ZIP) as zf, zf.open(f"140/{name}.csv") as fh:
        df = pd.read_csv(fh, encoding="latin-1", dtype={"st": str, "geoid": str})
    df = df[df.st.str.zfill(2) == "25"].copy()
    df["geoid11"] = df.geoid.str[-11:]
    wanted = [f"{name.replace('Table', 'T')}_{kind}{c}" for c in cols for kind in ("est", "moe")]
    return df.set_index("geoid11")[wanted]


def _sum(df: pd.DataFrame, prefix: str, cells: list[int]) -> tuple[pd.Series, pd.Series]:
    est = sum(df[f"{prefix}_est{c}"] for c in cells)
    moe = np.sqrt(sum(df[f"{prefix}_moe{c}"] ** 2 for c in cells))
    return est.astype(float), moe.astype(float)


def build(tract_ids: set[str]) -> pd.DataFrame:
    t8 = _table("Table8", [69, 76, 82, 89])
    t15 = _table("Table15C", [5, 9, 26, 30])
    t14 = _table("Table14B", [4, 8])
    df = t8.join(t15, how="outer").join(t14, how="outer")
    missing = tract_ids - set(df.index)
    extra = set(df.index) - tract_ids
    if missing or extra:
        raise ValueError(f"CHAS tracts mismatch: missing {len(missing)}, extra {len(extra)}")
    df = df.loc[sorted(tract_ids)]
    g = pd.Series(df.index)

    eli, eli_m = _sum(df, "T8", [69])
    vli, vli_m = _sum(df, "T8", [69, 82])
    eli_sev, eli_sev_m = _sum(df, "T8", [76])
    vli_sev, vli_sev_m = _sum(df, "T8", [76, 89])
    occ_eli, occ_eli_m = _sum(df, "T15C", [5])
    vac_eli, vac_eli_m = _sum(df, "T14B", [4])
    occ_vli, occ_vli_m = _sum(df, "T15C", [5, 9, 26, 30])
    vac_vli, vac_vli_m = _sum(df, "T14B", [4, 8])
    aa_eli = occ_eli + vac_eli
    aa_eli_m = np.sqrt(occ_eli_m**2 + vac_eli_m**2)
    aa_vli = occ_vli + vac_vli
    aa_vli_m = np.sqrt(occ_vli_m**2 + vac_vli_m**2)

    rows = [
        ("eli_renter_households", eli, eli_m),
        ("vli_renter_households", vli, vli_m),
        ("eli_severely_burdened_renters", eli_sev, eli_sev_m),
        ("vli_severely_burdened_renters", vli_sev, vli_sev_m),
        ("units_affordable_available_eli", aa_eli, aa_eli_m),
        ("units_affordable_available_vli", aa_vli, aa_vli_m),
        ("affordable_gap_eli", eli - aa_eli, np.sqrt(eli_m**2 + aa_eli_m**2)),
        ("affordable_gap_vli", vli - aa_vli, np.sqrt(vli_m**2 + aa_vli_m**2)),
        ("affordable_units_per_100_eli", 100 * safe_ratio(aa_eli, eli), None),
        ("affordable_units_per_100_vli", 100 * safe_ratio(aa_vli, vli), None),
        ("eli_severe_burden_share", safe_ratio(eli_sev, eli), None),
    ]
    out = pd.concat(
        [
            long_metric(
                g,
                name,
                CHAS_YEAR,
                val.reset_index(drop=True),
                SOURCE,
                moe=None if moe is None else moe.reset_index(drop=True),
            )
            for name, val, moe in rows
        ],
        ignore_index=True,
    )
    eli_total = float(eli.sum())
    log.info(
        "statewide ELI renters %.0f, available units %.0f, gap %.0f",
        eli_total,
        float(aa_eli.sum()),
        float((eli - aa_eli).sum()),
    )
    return out


def run() -> None:
    tract_ids = set(pd.read_parquet(PROCESSED_DIR / "tracts.parquet").geoid)
    build(tract_ids).to_parquet(PROCESSED_DIR / "metrics_chas.parquet")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
