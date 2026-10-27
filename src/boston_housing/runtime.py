import hashlib
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort

from boston_housing.contracts import FEATURE_NAMES, Scenario
from boston_housing.train import ARTIFACTS


class Predictor:
    def __init__(self, directory: Path = ARTIFACTS):
        report_path, model_path = directory / "report.json", directory / "model.onnx"
        if report_path.stat().st_size > 100_000 or model_path.stat().st_size > 5_000_000:
            raise ValueError("Model/report exceeds size limit")
        self.report = json.loads(report_path.read_text(encoding="utf-8"))
        raw = model_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != self.report["model_sha256"]:
            raise ValueError("Model SHA-256 integrity verification failed")
        if self.report["feature_names"] != list(FEATURE_NAMES):
            raise ValueError("Unexpected feature order")
        self.radius = float(self.report["interval"]["radius_kusd"])
        if not np.isfinite(self.radius) or not 0 < self.radius < 50:
            raise ValueError("Invalid interval radius")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        self.session = ort.InferenceSession(raw, options, providers=["CPUExecutionProvider"])

    def predict(self, scenario: Scenario) -> dict:
        output = self.session.run(None, {"features": np.asarray([scenario.vector()], dtype=np.float32)})[0]
        value = float(output[0, 0])
        if not np.isfinite(value):
            raise ValueError("Non-finite model output")
        estimate = float(np.clip(value, 5, 50))
        return {
            "estimate_kusd": estimate,
            "lower_kusd": max(5, estimate - self.radius),
            "upper_kusd": min(50, estimate + self.radius),
            "unit": "historical USD thousands",
            "scope": "historical tract median; not current/individual valuation",
            "model_sha256": self.report["model_sha256"],
            "input": scenario.model_dump(),
        }
