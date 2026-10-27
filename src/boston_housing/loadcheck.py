import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import threading
import time
import tracemalloc

import numpy as np
from fastapi.testclient import TestClient

from boston_housing.contracts import FEATURES
from boston_housing.web import create_app


def run_load(users: int = 1000, concurrency: int = 16) -> dict:
    if not 1 <= users <= 1000 or not 1 <= concurrency <= 32:
        raise ValueError("Load is restricted to 1-1000 local workflows and 1-32 workers")
    started = time.perf_counter()
    latencies, errors, statuses = [], [], Counter()
    lock, active, peak = threading.Lock(), 0, 0
    tracemalloc.start()
    with TestClient(create_app()) as client:
        expected_hash = client.get("/api/health").json()["model_sha256"]

        def journey(index):
            nonlocal active, peak
            before = time.perf_counter()
            with lock:
                active += 1
                peak = max(active, peak)
            local_statuses = []
            try:
                values = {key: value["default"] for key, value in FEATURES.items()}
                values["RM"] = 4.0 + index % 90 / 20
                health = client.get("/api/health")
                prediction = client.post("/api/predict", json=values)
                denied = client.get("/housepred.pkl")
                local_statuses.extend([health.status_code, prediction.status_code, denied.status_code])
                if local_statuses != [200, 200, 404]:
                    raise ValueError(f"Unexpected statuses: {local_statuses}")
                result = prediction.json()
                if (
                    result["model_sha256"] != expected_hash
                    or not 5 <= result["lower_kusd"] <= result["estimate_kusd"] <= result["upper_kusd"] <= 50
                ):
                    raise ValueError("Prediction integrity/range check failed")
            except Exception as error:
                with lock:
                    errors.append({"workflow": index, "error": str(error)[:160]})
            finally:
                with lock:
                    active -= 1
                    statuses.update(local_statuses)
                    latencies.append((time.perf_counter() - before) * 1000)

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            list(executor.map(journey, range(users)))
        attacks = []
        for key, value in [("B", 1), ("LSTAT", 1), ("MEDV", 1), ("RM", "<script>alert(1)</script>")]:
            payload = {name: spec["default"] for name, spec in FEATURES.items()}
            payload[key] = value
            response = client.post("/api/predict", json=payload)
            attacks.append({"field": key, "expected": 422, "actual": response.status_code})
    _, allocation_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Owned local in-process ASGI simulation; no external/public endpoints or paid providers contacted",
        "workflows": users,
        "configured_workers": concurrency,
        "peak_active_workflows": peak,
        "workflow_steps": ["health", "real ONNX prediction", "legacy artifact denial"],
        "workflow_requests_observed": sum(statuses.values()),
        "status_counts": dict(statuses),
        "failed_workflows": len(errors),
        "failures": errors[:20],
        "journey_p95_ms": float(np.percentile(latencies, 95)),
        "journey_p99_ms": float(np.percentile(latencies, 99)),
        "duration_seconds": time.perf_counter() - started,
        "python_traced_peak_bytes": allocation_peak,
        "memory_caveat": "Python traced allocations only, not process RSS or native ONNX memory",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "model_sha256": expected_hash,
        "adversarial_checks": attacks,
        "limitations": "1,000 total synthetic journeys, NOT 1,000 simultaneous humans, browser clients, or a production capacity SLA.",
        "passed": not errors and all(attack["actual"] == attack["expected"] for attack in attacks),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--output", type=Path, default=Path("artifacts/load-report.json"))
    args = parser.parse_args()
    report = run_load(args.users, args.concurrency)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
