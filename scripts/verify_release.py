import hashlib
import json
from pathlib import Path
import tarfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
wheel = ROOT / f"dist/boston_housing_workbench-{version}-py3-none-any.whl"
source = ROOT / f"dist/boston_housing_workbench-{version}.tar.gz"
report = json.loads((ROOT / "src/boston_housing/artifacts/report.json").read_text())
with zipfile.ZipFile(wheel) as archive:
    names = archive.namelist()
    assert not any(name.endswith((".pkl", ".arff")) or "/.env" in name for name in names)
    model = archive.read("boston_housing/artifacts/model.onnx")
    assert hashlib.sha256(model).hexdigest() == report["model_sha256"]
    assert archive.read("boston_housing/site/model.onnx") == model
    expected_assets = {
        path.relative_to(ROOT / "frontend/dist").as_posix()
        for path in (ROOT / "frontend/dist").rglob("*")
        if path.is_file()
    }
    actual_assets = {
        name.removeprefix("boston_housing/site/")
        for name in names
        if name.startswith("boston_housing/site/") and not name.endswith("/")
    }
    assert actual_assets == expected_assets
    records = json.loads(archive.read("boston_housing/site/licenses.json"))
    assert any(record["name"] == "onnxruntime-web" for record in records)
    assert any(record["license"] == "CC BY-SA 4.0" for record in records)
with tarfile.open(source) as archive:
    names = archive.getnames()
    assert not any("/node_modules/" in name or name.endswith((".pkl", ".arff")) for name in names)
    for suffix in [
        "/uv.lock",
        "/frontend/package-lock.json",
        "/frontend/src/engine.ts",
        "/NOTICE.md",
        "/tests/test_api.py",
    ]:
        assert any(name.endswith(suffix) for name in names), suffix
print("Verified wheel UI/model/notice identity, source completeness and raw-data/legacy-pickle exclusions")
