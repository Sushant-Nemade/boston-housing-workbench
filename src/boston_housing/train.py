import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

from boston_housing.contracts import FEATURES, FEATURE_NAMES
from boston_housing.data import DATA_SHA256, DATA_URL, fetch_data, load_data

ARTIFACTS = Path(__file__).parent / "artifacts"


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    return {
        "mae_kusd": float(mean_absolute_error(actual, predicted)),
        "rmse_kusd": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def split_indices() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_cal, test = train_test_split(np.arange(506), test_size=0.2, random_state=42)
    train, calibration = train_test_split(train_cal, test_size=0.2, random_state=43)
    return np.sort(train), np.sort(calibration), np.sort(test)


def train(data_path: Path, destination: Path = ARTIFACTS) -> dict:
    features, target = load_data(fetch_data(data_path))
    fit, calibration, test = split_indices()
    cv = KFold(5, shuffle=True, random_state=44)
    candidates = [
        ("standardized-ridge", make_pipeline(StandardScaler(), Ridge()), {"ridge__alpha": [1, 10, 100]}),
        (
            "gradient-boosting",
            GradientBoostingRegressor(random_state=45),
            {"n_estimators": [100, 200], "max_depth": [2, 3], "learning_rate": [0.05]},
        ),
    ]
    searches = []
    for name, estimator, grid in candidates:
        search = GridSearchCV(estimator, grid, cv=cv, scoring="neg_mean_absolute_error", n_jobs=1)
        search.fit(features[fit], target[fit])
        searches.append((name, search))
    name, selected = max(searches, key=lambda item: item[1].best_score_)
    model = selected.best_estimator_

    def clipped(values):
        return np.clip(model.predict(values), 5, 50)

    calibration_errors = np.abs(clipped(features[calibration]) - target[calibration])
    rank = min(len(calibration), int(np.ceil((len(calibration) + 1) * 0.9)))
    radius = float(np.sort(calibration_errors)[rank - 1])
    predicted = clipped(features[test])
    lower, upper = np.maximum(5, predicted - radius), np.minimum(50, predicted + radius)
    exported = convert_sklearn(
        model,
        name="boston-housing-historical-v1",
        initial_types=[("features", FloatTensorType([None, 11]))],
        target_opset=15,
    )
    onnx.checker.check_model(exported)
    model_bytes = exported.SerializeToString()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    session = ort.InferenceSession(model_bytes, options, providers=["CPUExecutionProvider"])
    onnx_predictions = session.run(None, {"features": features})[0].reshape(-1)
    max_error = float(np.max(np.abs(onnx_predictions - model.predict(features))))
    if max_error > 0.002:
        raise ValueError(f"ONNX parity failed: {max_error}")
    median = float(np.median(target[fit]))
    report = {
        "schema_version": 1,
        "purpose": "historical-education-only",
        "model": name,
        "model_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "features": FEATURES,
        "feature_names": list(FEATURE_NAMES),
        "excluded_features": ["B", "LSTAT"],
        "dataset": {
            "name": "Boston Housing",
            "openml_id": 531,
            "version": 1,
            "rows": 506,
            "source": DATA_URL,
            "sha256": DATA_SHA256,
            "publisher_license_label": "Public",
            "license_caveat": "Nonstandard publisher label; no CC/OSI license or commercial-use certification asserted.",
            "historical_period": "1970 census-era data; published 1978",
            "target_unit": "historical USD thousands",
        },
        "splits": {
            key: {
                "rows": len(indices),
                "indices": indices.tolist(),
                "sha256": hashlib.sha256(indices.astype("<i8").tobytes()).hexdigest(),
            }
            for key, indices in zip(["train", "calibration", "test"], [fit, calibration, test])
        },
        "selection": [
            {
                "model": candidate_name,
                "training_cv_mae_kusd": float(-search.best_score_),
                "parameters": search.best_params_,
            }
            for candidate_name, search in searches
        ],
        "evaluation": {
            "test": metrics(target[test], predicted),
            "median_baseline": metrics(target[test], np.full(len(test), median)),
            "interval_coverage": float(np.mean((target[test] >= lower) & (target[test] <= upper))),
            "mean_interval_width_kusd": float(np.mean(upper - lower)),
            "onnx_max_error_kusd": max_error,
            "capped_test_rows": int(np.sum(target[test] == 50)),
            "slices": [
                {
                    "slice": label,
                    "rows": int(mask.sum()),
                    "mae_kusd": float(np.mean(np.abs(target[test][mask] - predicted[mask]))),
                }
                for label, mask in [("river", features[test, 3] == 1), ("not-river", features[test, 3] == 0)]
                if mask.any()
            ],
        },
        "interval": {
            "nominal_coverage": 0.9,
            "radius_kusd": radius,
            "interpretation": "Historical calibration residual band, not guaranteed individual/current-price coverage.",
        },
        "limitations": [
            "Historical tract-level medians, NOT individual houses or current Boston prices.",
            "Not for buying, selling, appraisal, lending, eligibility, or housing allocation.",
            "B and LSTAT are excluded, but other inputs and target can retain discriminatory proxies and historic bias.",
            "Random row split is not spatially or temporally independent; neighbouring tracts can remain dependent.",
            "MEDV is top-coded at $50,000; estimates and residual bands are clipped to the observed 5-50 range.",
            "Small, historical sample; neither fairness certification nor modern geographic generalization is established.",
        ],
    }
    generator = np.random.default_rng(20261027)
    authored = np.column_stack(
        [
            generator.integers(int(spec["min"]), int(spec["max"]) + 1, 20)
            if key in {"CHAS", "RAD"}
            else generator.uniform(spec["min"], spec["max"], 20)
            for key, spec in FEATURES.items()
        ]
    ).astype(np.float32)
    probes = [
        {
            "input": {
                key: int(value) if key in {"CHAS", "RAD"} else float(value)
                for key, value in zip(FEATURE_NAMES, row)
            },
            "expected_kusd": float(value),
        }
        for row, value in zip(authored, clipped(authored))
    ]
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "model.onnx").write_bytes(model_bytes)
    for filename, payload in [("report.json", report), ("parity.json", probes)]:
        (destination / filename).write_text(
            json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path(".cache/boston.arff"))
    parser.add_argument("--output", type=Path, default=ARTIFACTS)
    args = parser.parse_args()
    print(json.dumps(train(args.data, args.output)["evaluation"], indent=2))


if __name__ == "__main__":
    main()
