"""Home-value model: predicts a residential parcel's assessed value (cost context for sites).

Models (all fit on the train split only):
- baseline: median assessed value of the record's municipality (county median if the town
  has no train records);
- ridge regression on log value;
- gradient boosting (scikit-learn HistGradientBoostingRegressor) on log value.

Hyper-parameters and the model choice use the validation split only. The test split is
scored once, at the end, for the chosen model and the baseline. Target from PLAN.md: the
chosen model's test MAPE is at least 25% lower than the baseline's.

Run: uv run python -m pipeline.model.home_value
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from pipeline.model.dataset import DATASET_FILE, MODEL_DIR
from pipeline.paths import PROCESSED_DIR, REPORTS_DIR

log = logging.getLogger("pipeline.model.home_value")

TARGET_IMPROVEMENT = 0.25
MODEL_FILE = MODEL_DIR / "home_value_model.joblib"
TEST_PRED_FILE = MODEL_DIR / "test_predictions.parquet"
SEED = 20261110
MIN_TRACT_RECORDS = 5
TRACT_CONTEXT = {
    "median_household_income": "tract_median_income",
    "median_home_value": "tract_acs_median_value",
    "zhvi_latest": "tract_zhvi",
}
NUMERIC = [
    "fy",
    "lot_size_acres",
    "res_area",
    "bld_area",
    "year_built",
    "units",
    "num_rooms",
    "stories_num",
    "x",
    "y",
    "parcel_area_m2",
    "town_median_log",
    "tract_median_log",
    *TRACT_CONTEXT.values(),
]
CATEGORICAL = ["use3", "county_geoid"]
# long-tailed sizes and values: log1p for the linear model (trees do not need it)
SKEWED = [
    "lot_size_acres",
    "res_area",
    "bld_area",
    "units",
    "num_rooms",
    "parcel_area_m2",
    "tract_median_income",
    "tract_acs_median_value",
    "tract_zhvi",
]
FEATURES = NUMERIC + CATEGORICAL
HGB_GRID = [
    {"learning_rate": lr, "max_leaf_nodes": leaves, "max_iter": iters}
    for lr in (0.1, 0.2)
    for leaves in (63, 255)
    for iters in (300, 600)
]
RIDGE_ALPHAS = (0.1, 1.0, 10.0)


def mape(y: np.ndarray | pd.Series, pred: np.ndarray | pd.Series) -> float:
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    return float(np.mean(np.abs(y - pred) / y))


def median_ape(y: np.ndarray | pd.Series, pred: np.ndarray | pd.Series) -> float:
    y = np.asarray(y, dtype=float)
    return float(np.median(np.abs(y - np.asarray(pred, dtype=float)) / y))


@dataclass
class Encodings:
    """Statistics learnt from the train split only."""

    town_median: pd.Series
    county_median: pd.Series
    town_median_log: pd.Series
    tract_median_log: pd.Series
    global_median_log: float
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def fit(cls, train: pd.DataFrame) -> Encodings:
        logv = np.log(train.total_val.astype(float))
        tract = logv.groupby(train.tract_geoid)
        tract_med = tract.median()[tract.size() >= MIN_TRACT_RECORDS]
        return cls(
            town_median=train.groupby("municipality_geoid").total_val.median(),
            county_median=train.groupby("county_geoid").total_val.median(),
            town_median_log=logv.groupby(train.municipality_geoid).median(),
            tract_median_log=tract_med,
            global_median_log=float(logv.median()),
        )

    def baseline(self, df: pd.DataFrame) -> pd.Series:
        town = df.municipality_geoid.map(self.town_median)
        return town.fillna(df.county_geoid.map(self.county_median)).astype(float)


def prepare(df: pd.DataFrame, tract_context: pd.DataFrame) -> pd.DataFrame:
    """Clean model inputs: non-positive areas, rooms and years are 'not recorded' (NaN)."""
    out = df.copy()
    for col in ("res_area", "bld_area", "num_rooms"):
        out[col] = out[col].where(out[col] > 0)
    out["year_built"] = out.year_built.where(out.year_built.between(1600, 2030))
    out["lot_size_acres"] = out.lot_size_acres.where(out.lot_size_acres > 0)
    out["parcel_area_m2"] = out.area_m2
    out = out.join(tract_context, on="tract_geoid")
    return out


def add_encodings(df: pd.DataFrame, enc: Encodings) -> pd.DataFrame:
    out = df.copy()
    out["town_median_log"] = out.municipality_geoid.map(enc.town_median_log)
    out["tract_median_log"] = out.tract_geoid.map(enc.tract_median_log)
    return out


def _log1p_nonneg(x: np.ndarray) -> np.ndarray:
    return np.log1p(np.clip(x, 0, None))


def ridge_model(alpha: float) -> Pipeline:
    linear = [c for c in NUMERIC if c not in SKEWED]
    pre = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                linear,
            ),
            (
                "skewed",
                Pipeline(
                    [
                        ("log", FunctionTransformer(_log1p_nonneg)),
                        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                SKEWED,
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ]
    )
    return Pipeline([("pre", pre), ("ridge", Ridge(alpha=alpha))])


def hgb_model(params: dict[str, Any]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss="squared_error",
        categorical_features="from_dtype",
        early_stopping=False,
        random_state=SEED,
        **params,
    )


def _hgb_frame(df: pd.DataFrame) -> pd.DataFrame:
    x = df[FEATURES].copy()
    for c in CATEGORICAL:
        x[c] = x[c].astype("category")
    return x


def tract_context() -> pd.DataFrame:
    frames = [
        pd.read_parquet(PROCESSED_DIR / f)
        for f in ("metrics_acs.parquet", "metrics_context.parquet")
    ]
    m = pd.concat(frames, ignore_index=True)
    m = m[m.metric.isin(TRACT_CONTEXT)]
    wide = m.pivot_table(index="tract_geoid", columns="metric", values="value", aggfunc="first")
    return wide.rename(columns=TRACT_CONTEXT)


def fit_and_select(
    train: pd.DataFrame, val: pd.DataFrame
) -> tuple[str, Any, dict[str, Any], list[dict[str, Any]]]:
    """Fit candidates on train, score on validation; returns (kind, model, params, trials)."""
    y_tr = np.log(train.total_val.astype(float))
    log_range = (float(y_tr.min()), float(y_tr.max()))
    trials: list[dict[str, Any]] = []
    best: tuple[float, str, Any, dict[str, Any]] | None = None
    for alpha in RIDGE_ALPHAS:
        t0 = time.time()
        m = ridge_model(alpha).fit(train[FEATURES], y_tr)
        score = mape(val.total_val, predict("ridge", m, val, log_range))
        trials.append({"model": "ridge", "params": {"alpha": alpha}, "validation_mape": score})
        log.info("ridge alpha=%s val MAPE %.4f (%.0fs)", alpha, score, time.time() - t0)
        if best is None or score < best[0]:
            best = (score, "ridge", m, {"alpha": alpha})
    x_tr = _hgb_frame(train)
    for params in HGB_GRID:
        t0 = time.time()
        m = hgb_model(params).fit(x_tr, y_tr)
        score = mape(val.total_val, predict("hist_gradient_boosting", m, val, log_range))
        trials.append(
            {"model": "hist_gradient_boosting", "params": params, "validation_mape": score}
        )
        log.info("hgb %s val MAPE %.4f (%.0fs)", params, score, time.time() - t0)
        if score < best[0]:
            best = (score, "hist_gradient_boosting", m, params)
    assert best is not None
    return best[1], best[2], best[3], trials


def predict(
    kind: str, model: Any, df: pd.DataFrame, log_range: tuple[float, float] | None = None
) -> np.ndarray:
    """Predicted value; log predictions are clipped to the train target range if given."""
    x = _hgb_frame(df) if kind == "hist_gradient_boosting" else df[FEATURES]
    p = model.predict(x)
    if log_range is not None:
        p = np.clip(p, *log_range)
    return np.exp(p)


def run() -> dict[str, Any]:
    df = pd.read_parquet(DATASET_FILE)
    df = prepare(df, tract_context())
    train = df[df.split == "train"]
    enc = Encodings.fit(train)
    df = add_encodings(df, enc)
    train, val, test = (df[df.split == s] for s in ("train", "validation", "test"))
    log.info("train %d, validation %d, test %d", len(train), len(val), len(test))

    base_val = mape(val.total_val, enc.baseline(val))
    kind, model, params, trials = fit_and_select(train, val)
    best_val = min(t["validation_mape"] for t in trials)

    # final evaluation: the only use of the test split
    base_test_pred = enc.baseline(test)
    y_tr = np.log(train.total_val.astype(float))
    log_range = (float(y_tr.min()), float(y_tr.max()))
    test_pred = predict(kind, model, test, log_range)
    base_test = mape(test.total_val, base_test_pred)
    model_test = mape(test.total_val, test_pred)
    improvement = 1 - model_test / base_test
    by_county = (
        pd.DataFrame(
            {
                "county_geoid": test.county_geoid.values,
                "ape_model": np.abs(test.total_val.values - test_pred) / test.total_val.values,
                "ape_baseline": np.abs(test.total_val.values - base_test_pred.values)
                / test.total_val.values,
            }
        )
        .groupby("county_geoid")
        .agg(
            records=("ape_model", "size"),
            mape_model=("ape_model", "mean"),
            mape_baseline=("ape_baseline", "mean"),
        )
    )
    metrics: dict[str, Any] = {
        "target": "assessed TOTAL_VAL of residential parcels (MassGIS L3, FY2023-2027)",
        "metric": "MAPE (mean absolute percentage error)",
        "target_rule": f"test MAPE at least {TARGET_IMPROVEMENT:.0%} below the baseline's",
        "split_sizes": {"train": len(train), "validation": len(val), "test": len(test)},
        "baseline": {
            "name": "municipality median assessed value (train), county median fallback",
            "validation_mape": base_val,
            "test_mape": base_test,
            "test_median_ape": median_ape(test.total_val, base_test_pred),
        },
        "chosen_model": {
            "name": kind,
            "params": params,
            "validation_mape": best_val,
            "test_mape": model_test,
            "test_median_ape": median_ape(test.total_val, test_pred),
        },
        "test_improvement_vs_baseline": improvement,
        "target_met": bool(improvement >= TARGET_IMPROVEMENT),
        "selection": "hyper-parameters and model chosen on validation MAPE only; test scored once",
        "validation_trials": trials,
        "test_error_by_county": by_county.reset_index().to_dict("records"),
        "features": FEATURES,
    }
    REPORTS_DIR.joinpath("model_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "kind": kind,
            "model": model,
            "encodings": enc,
            "log_range": log_range,
            "features": FEATURES,
            "params": params,
        },
        MODEL_FILE,
    )
    pd.DataFrame(
        {
            "record_id": test.record_id.values,
            "county_geoid": test.county_geoid.values,
            "actual": test.total_val.values,
            "predicted": test_pred,
            "baseline": base_test_pred.values,
        }
    ).to_parquet(TEST_PRED_FILE)
    log.info(
        "baseline test MAPE %.4f, %s test MAPE %.4f, improvement %.1f%% (target %s)",
        base_test,
        kind,
        model_test,
        100 * improvement,
        "met" if metrics["target_met"] else "NOT met",
    )
    return {
        "metrics": metrics,
        "model": model,
        "kind": kind,
        "encodings": enc,
        "test": test,
        "test_pred": test_pred,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
