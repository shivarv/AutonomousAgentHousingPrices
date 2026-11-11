"""Home-value model artifacts: feature importances, error-by-county chart and table, and a
model_runs row. Uses the saved model and the saved test predictions; importances are
permutation importances on a validation sample (the test split is not touched here).

Run: uv run python -m pipeline.model.artifacts   (after pipeline.model.home_value)
"""

from __future__ import annotations

import json
import logging

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from app.core.database import get_session_factory  # noqa: E402
from app.dao.model_run_dao import ModelRunDao  # noqa: E402
from pipeline.model import home_value as hv  # noqa: E402
from pipeline.model.dataset import DATASET_FILE  # noqa: E402
from pipeline.paths import PROCESSED_DIR, PROJECT_ROOT, REPORTS_DIR  # noqa: E402

log = logging.getLogger("pipeline.model.artifacts")

IMPORTANCE_SAMPLE = 30_000
SEED = 20261110
SURFACE = "#fcfcfb"
INK = "#1f1f1e"
MUTED = "#6b6a64"
MODEL_COLOR = "#2a78d6"
BASELINE_COLOR = "#eb6834"


def importances(bundle: dict) -> pd.DataFrame:
    df = pd.read_parquet(DATASET_FILE)
    df = df[df.split == "validation"].sample(IMPORTANCE_SAMPLE, random_state=SEED)
    df = hv.add_encodings(hv.prepare(df, hv.tract_context()), bundle["encodings"])
    x = hv._hgb_frame(df) if bundle["kind"] == "hist_gradient_boosting" else df[hv.FEATURES]
    y = np.log(df.total_val.astype(float))
    r = permutation_importance(
        bundle["model"], x, y, n_repeats=3, random_state=SEED, scoring="r2", n_jobs=1
    )
    return (
        pd.DataFrame(
            {
                "feature": x.columns,
                "importance_mean": r.importances_mean,
                "importance_std": r.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )


def county_errors(pred: pd.DataFrame) -> pd.DataFrame:
    names = pd.read_parquet(PROCESSED_DIR / "counties.parquet").set_index("geoid").name
    p = pred.assign(
        ape_model=(pred.actual - pred.predicted).abs() / pred.actual,
        ape_baseline=(pred.actual - pred.baseline).abs() / pred.actual,
    )
    out = p.groupby("county_geoid").agg(
        test_records=("actual", "size"),
        mape_model=("ape_model", "mean"),
        mape_baseline=("ape_baseline", "mean"),
        median_ape_model=("ape_model", "median"),
    )
    out.insert(0, "county", out.index.map(names).str.replace(" County", "", regex=False))
    return out.sort_values("mape_model").reset_index()


def chart(errors: pd.DataFrame, path) -> None:
    e = errors.sort_values("mape_model", ascending=True).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 6.2), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    y = np.arange(len(e))
    h = 0.36
    ax.barh(y - h / 2 - 0.02, 100 * e.mape_model, height=h, color=MODEL_COLOR, label="Model")
    ax.barh(
        y + h / 2 + 0.02,
        100 * e.mape_baseline,
        height=h,
        color=BASELINE_COLOR,
        label="Baseline (town median)",
    )
    for i, v in enumerate(e.mape_model):
        ax.text(
            100 * v + 0.6, i - h / 2 - 0.02, f"{100 * v:.0f}%", va="center", fontsize=8, color=INK
        )
    ax.set_yticks(y, e.county, fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("Mean absolute percentage error on the test split (%)", color=MUTED, fontsize=9)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d4d3cc")
    ax.set_title(
        "Home-value model error by county (test split)", loc="left", fontsize=12, color=INK, pad=24
    )
    ax.legend(
        loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=9, labelcolor=INK
    )
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def run() -> None:
    bundle = joblib.load(hv.MODEL_FILE)
    metrics = json.loads((REPORTS_DIR / "model_metrics.json").read_text())
    pred = pd.read_parquet(hv.TEST_PRED_FILE)
    errors = county_errors(pred)
    errors.to_csv(REPORTS_DIR / "model_error_by_county.csv", index=False, float_format="%.4f")
    chart(errors, REPORTS_DIR / "model_error_by_county.png")
    imp = importances(bundle)
    imp.to_csv(REPORTS_DIR / "model_feature_importance.csv", index=False, float_format="%.5f")
    metrics["feature_importance"] = {
        "method": f"permutation importance (R2 drop on log value), {IMPORTANCE_SAMPLE} "
        "validation records, 3 repeats",
        "top": imp.head(10).to_dict("records"),
    }
    metrics["artifacts"] = {
        "model": str(hv.MODEL_FILE.relative_to(PROJECT_ROOT)),
        "error_by_county_chart": "reports/model_error_by_county.png",
        "error_by_county_table": "reports/model_error_by_county.csv",
        "feature_importance": "reports/model_feature_importance.csv",
    }
    (REPORTS_DIR / "model_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    with get_session_factory()() as session:
        ModelRunDao(session).replace_kind(
            "home_value",
            params={"model": bundle["kind"], **bundle["params"], "features": bundle["features"]},
            metrics={
                k: metrics[k]
                for k in ("baseline", "chosen_model", "test_improvement_vs_baseline", "target_met")
            },
            artifact_path=str(hv.MODEL_FILE.relative_to(PROJECT_ROOT)),
            notes="HistGradientBoostingRegressor (LightGBM blocked, see BLOCKERS.md); "
            "selection on validation only; test scored once",
        )
        session.commit()
    log.info("artifacts written; top features: %s", imp.head(5).feature.tolist())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
