"""Every API route has at least one test that calls it (guards against untested endpoints)."""

import re
from pathlib import Path

from app.main import create_app

TESTS = Path(__file__).parent


def _route_regex(path: str) -> re.Pattern[str]:
    # /api/sites/{site_id} -> matches "/api/sites/0" or f"/api/sites/{x}" in test source
    parts = re.split(r"\{[^}]+\}", path)
    return re.compile(r"[^/\"']+".join(re.escape(p) for p in parts) + r"[\"'?]")


def test_every_route_is_called_by_a_test() -> None:
    source = "\n".join(
        p.read_text() for p in TESTS.glob("test_*.py") if p.name != "test_api_coverage.py"
    )
    routes = list(create_app().openapi()["paths"])
    missing = [p for p in routes if not _route_regex(p).search(source)]
    assert routes
    assert not missing, f"routes without an API test: {missing}"
