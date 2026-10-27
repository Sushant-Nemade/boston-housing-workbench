import ast
from pathlib import Path


def test_active_entrypoint_never_imports_pickle():
    source = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert "pickle" not in imports, "Active app deserializes unreviewed pickle models at import time."
