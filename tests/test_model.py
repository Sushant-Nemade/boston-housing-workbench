import json
import shutil

import numpy as np
import pytest

from boston_housing.contracts import FEATURES, Scenario
from boston_housing.data import DATA_SHA256, load_data
from boston_housing.runtime import Predictor
from boston_housing.train import ARTIFACTS, split_indices


def test_splits_are_disjoint_complete_and_reproducible():
    first = split_indices()
    second = split_indices()
    assert set.union(*(set(part) for part in first)) == set(range(506))
    assert len(set.intersection(set(first[0]), set(first[1]))) == 0
    assert len(set.intersection(set(first[0]), set(first[2]))) == 0
    assert len(set.intersection(set(first[1]), set(first[2]))) == 0
    assert all(np.array_equal(left, right) for left, right in zip(first, second))


def test_tampered_dataset_is_rejected(tmp_path):
    path = tmp_path / "source.arff"
    path.write_bytes(b"not the pinned dataset")
    with pytest.raises(ValueError, match="SHA-256"):
        load_data(path)
    assert len(DATA_SHA256) == 64


def test_exported_model_matches_real_training_predictions():
    predictor = Predictor()
    probes = json.loads((ARTIFACTS / "parity.json").read_text())
    assert len(probes) == 20
    for probe in probes:
        result = predictor.predict(Scenario.model_validate(probe["input"]))
        assert result["estimate_kusd"] == pytest.approx(probe["expected_kusd"], abs=0.002)
        assert 5 <= result["lower_kusd"] <= result["estimate_kusd"] <= result["upper_kusd"] <= 50


def test_model_tampering_is_rejected_before_session_creation(tmp_path):
    shutil.copy(ARTIFACTS / "report.json", tmp_path)
    (tmp_path / "model.onnx").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA-256"):
        Predictor(tmp_path)


def test_metadata_carries_scope_and_real_baseline():
    predictor = Predictor()
    report = predictor.report
    assert report["evaluation"]["test"]["mae_kusd"] < report["evaluation"]["median_baseline"]["mae_kusd"]
    assert report["excluded_features"] == ["B", "LSTAT"]
    assert report["purpose"] == "historical-education-only"
    assert report["evaluation"]["onnx_max_error_kusd"] < 0.002
    assert Predictor().predict(
        Scenario.model_validate({key: value["default"] for key, value in FEATURES.items()})
    )
