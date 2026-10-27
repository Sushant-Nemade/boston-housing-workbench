import hashlib
from io import StringIO
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from scipy.io import arff

from boston_housing.contracts import FEATURE_NAMES

DATA_URL = "https://www.openml.org/data/v1/download/52643/boston.arff"
DATA_SHA256 = "2826ddb8cbce925e98114491f4774544b17d70ff0b7b1eede2af0a2ffd85a4f0"
MAX_BYTES = 500_000


def load_data(path: Path) -> tuple[np.ndarray, np.ndarray]:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Training data exceeds size limit")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != DATA_SHA256:
        raise ValueError("Training data failed pinned SHA-256 verification")
    rows, _ = arff.loadarff(StringIO(raw.decode("utf-8")))
    features = np.column_stack([rows[name].astype(np.float32) for name in FEATURE_NAMES])
    target = rows["MEDV"].astype(np.float64)
    if features.shape != (506, 11) or not np.isfinite(features).all() or not np.isfinite(target).all():
        raise ValueError("Unexpected dataset shape or non-finite data")
    return features, target


def fetch_data(path: Path) -> Path:
    if path.exists():
        load_data(path)
        return path
    with urlopen(DATA_URL, timeout=60) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != DATA_SHA256:
        raise ValueError("Downloaded dataset failed size/checksum verification")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    load_data(path)
    return path
