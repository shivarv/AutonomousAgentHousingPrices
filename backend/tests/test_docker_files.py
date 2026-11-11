"""Static checks for the Docker files (Docker is not installed here, so nothing is built/run).

Checks that compose.yaml parses, that every build context, Dockerfile, COPY source and bind
mount it refers to exists, and that the services are wired as PLAN.md Phase 11 asks.
"""

import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "compose.yaml"


@pytest.fixture(scope="module")
def compose() -> dict:
    return yaml.safe_load(COMPOSE.read_text())


def _instructions(dockerfile: Path) -> list[tuple[str, str]]:
    """(INSTRUCTION, arguments) pairs with line continuations joined, comments dropped."""
    text = re.sub(r"\\\n", " ", dockerfile.read_text())
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        word, _, rest = line.partition(" ")
        out.append((word.upper(), rest.strip()))
    return out


def _copy_sources(args: str) -> list[str] | None:
    """Local source paths of a COPY instruction, or None when it copies from a stage/image."""
    parts = shlex.split(args)
    if any(p.startswith("--from=") for p in parts):
        return None
    paths = [p for p in parts if not p.startswith("--")]
    return paths[:-1]


def test_compose_has_required_services(compose: dict) -> None:
    services = compose["services"]
    assert {"db", "backend", "frontend"} <= set(services)
    for name, svc in services.items():
        if "image" in svc:
            assert ":" in svc["image"] and not svc["image"].endswith(":latest"), name


def test_postgres_18_with_healthcheck(compose: dict) -> None:
    db = compose["services"]["db"]
    assert db["image"].startswith("postgres:18")
    assert "pg_isready" in " ".join(db["healthcheck"]["test"])
    vol = db["volumes"][0].split(":")[0]
    assert vol in compose["volumes"]


def test_dependencies_wait_for_health(compose: dict) -> None:
    services = compose["services"]
    assert services["backend"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["frontend"]["depends_on"]["backend"]["condition"] == "service_healthy"
    for svc in services.values():
        for dep, rule in svc.get("depends_on", {}).items():
            if rule.get("condition") == "service_healthy":
                has_compose_check = "healthcheck" in services[dep]
                dockerfile = ROOT / services[dep].get("build", {}).get("context", "/nonexistent")
                has_image_check = (dockerfile / "Dockerfile").exists() and any(
                    i == "HEALTHCHECK" for i, _ in _instructions(dockerfile / "Dockerfile")
                )
                assert has_compose_check or has_image_check, dep


def test_no_plaintext_password(compose: dict) -> None:
    text = COMPOSE.read_text()
    for match in re.finditer(r"^\s*\w*PASSWORD:\s*(\S+)", text, re.M):
        assert match.group(1).startswith("${"), match.group(0)
    assert "CENSUS_API_KEY: ${CENSUS_API_KEY" in text


@pytest.mark.parametrize("service", ["backend", "frontend", "pipeline"])
def test_build_paths_exist(compose: dict, service: str) -> None:
    build = compose["services"][service]["build"]
    context = ROOT / build["context"]
    dockerfile = context / build.get("dockerfile", "Dockerfile")
    assert context.is_dir() and dockerfile.is_file()
    assert (context / ".dockerignore").is_file()
    ignored = (context / ".dockerignore").read_text().splitlines()
    assert ".env" in ignored
    for instr, args in _instructions(dockerfile):
        if instr == "COPY":
            for src in _copy_sources(args) or []:
                assert (context / src).exists(), f"{dockerfile}: COPY {src}"
        if instr == "RUN":
            for src in re.findall(r"type=bind,source=([^,\s]+)", args):
                assert (context / src).exists(), f"{dockerfile}: bind {src}"


@pytest.mark.parametrize("folder", ["backend", "frontend"])
def test_runtime_stage_is_multi_stage_and_non_root(folder: str) -> None:
    instrs = _instructions(ROOT / folder / "Dockerfile")
    stages = [a for i, a in instrs if i == "FROM"]
    assert len(stages) >= 2
    assert all(" AS " in s.upper() for s in stages)
    last_from = max(n for n, (i, _) in enumerate(instrs) if i == "FROM")
    users = [a for i, a in instrs[last_from:] if i == "USER"]
    assert users and users[-1].split(":")[0] not in {"root", "0"}
    assert "EXPOSE" in {i for i, _ in instrs[last_from:]}


def test_backend_runs_migrations_then_uvicorn() -> None:
    instrs = _instructions(ROOT / "backend" / "Dockerfile")
    cmd = [a for i, a in instrs if i == "CMD"][-1]
    assert cmd.index("alembic upgrade head") < cmd.index("uvicorn app.main:app")
    assert "uv sync --locked --no-dev" in " ".join(a for i, a in instrs if i == "RUN")
    assert "app = create_app()" in (ROOT / "backend" / "app" / "main.py").read_text()


def test_nginx_proxies_api_to_backend_service(compose: dict) -> None:
    conf = (ROOT / "frontend" / "nginx.conf").read_text()
    match = re.search(r"proxy_pass http://([\w-]+):(\d+);", conf)
    assert match is not None
    assert match.group(1) in compose["services"]
    assert f"{match.group(2)}:{match.group(2)}" in compose["services"]["backend"]["ports"][0]
    assert "try_files $uri $uri/ /index.html" in conf


def test_pipeline_mounts_match_paths_module(compose: dict) -> None:
    from pipeline import paths

    mounts = dict(v.split(":", 1)[::-1] for v in compose["services"]["pipeline"]["volumes"])
    # In the image the code is at /srv/backend, so paths.PROJECT_ROOT resolves to /srv.
    rel = {
        "/srv/" + str(p.relative_to(paths.PROJECT_ROOT))
        for p in (paths.DATA_DIR, paths.REPORTS_DIR)
    }
    assert rel <= set(mounts)
    assert "/srv/DATA_SOURCES.md" in mounts
    for container, host in mounts.items():
        if container != "/srv/data":  # data/ is git-ignored and created by the pipeline
            assert (ROOT / host).exists(), host
    assert compose["services"]["pipeline"]["profiles"] == ["pipeline"]
