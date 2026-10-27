from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "frontend/dist"
destination = ROOT / "src/boston_housing/site"
if not (source / "index.html").is_file() or not (source / "model.onnx").is_file():
    raise SystemExit("Build the complete frontend first")
if destination.exists():
    shutil.rmtree(destination)
shutil.copytree(source, destination)
print("Packaged the exact current static build")
