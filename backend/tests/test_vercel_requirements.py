"""The Vercel API deployment installs only /requirements.txt: it must cover app/ imports."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "backend" / "app"

# import name -> distribution name in requirements.txt
DIST_NAMES = {"psycopg": "psycopg", "pydantic_settings": "pydantic-settings"}
# imported only inside pipeline-only code paths (bulk loading), never while serving requests
PIPELINE_ONLY = {"pandas"}


def _requirement_names() -> set[str]:
    names = set()
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line.split("==")[0].split("[")[0].strip().lower())
    return names


def _third_party_imports() -> set[str]:
    found = set()
    for path in APP_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0])
    return {n for n in found if n != "app" and n not in sys.stdlib_module_names}


def test_requirements_cover_app_imports() -> None:
    required = _requirement_names()
    missing = {
        name
        for name in _third_party_imports() - PIPELINE_ONLY
        if DIST_NAMES.get(name, name).lower() not in required
    }
    assert not missing, f"add to requirements.txt: {sorted(missing)}"


def test_vercel_entrypoint_exposes_app() -> None:
    source = (ROOT / "api" / "index.py").read_text()
    assert "from app.main import app" in source
