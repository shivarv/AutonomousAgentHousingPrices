"""End-to-end acceptance checks (PLAN.md "Definition of done").

Run from the project root:  uv run --project backend python scripts/validate.py
Options:  --skip-git       skip the git/PR checks (use while working on a task branch)
          --skip-commands  skip pytest/ruff/npm (only the data, API and report checks)
Exit code 0 only if every check passes. Reads the `housing` database (DATABASE_URL).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(BACKEND))

import pyogrio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from shapely.geometry import Point, shape  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import get_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from pipeline.paths import RAW_DIR  # noqa: E402

TIGER_TRACTS = RAW_DIR / "tiger/tl_2026_25_tract.zip"
POINTS = {
    "Boston": (42.3601, -71.0589),
    "Worcester": (42.2626, -71.8023),
    "Springfield": (42.1015, -72.5898),
}
RING_METRICS = (
    "population",
    "homeless",
    "at_risk_households",
    "eli_renter_households",
    "affordable_units_available",
    "affordable_gap",
    "gap_status",
    "subsidised_units",
    "need_index",
    "shelters",
)
TOL = 0.5  # people / households: rounding tolerance for sums of fractional estimates

results: list[tuple[bool, str, str]] = []


def check(name: str) -> Callable[[Callable[..., str]], Callable[..., None]]:
    """Decorator: the function returns a detail string or raises AssertionError."""

    def wrap(fn: Callable[..., str]) -> Callable[..., None]:
        def run(*args: object) -> None:
            try:
                detail = fn(*args)
                results.append((True, name, detail))
            except Exception as exc:  # noqa: BLE001 - report every failure, keep going
                results.append((False, name, f"{type(exc).__name__}: {exc}"))

        return run

    return wrap


def scalar(db: Session, sql: str, **params: object):
    return db.execute(text(sql), params).scalar()


def rows(db: Session, sql: str, **params: object):
    return db.execute(text(sql), params).all()


# ---------------------------------------------------------------- database checks
@check("coverage: all MA tracts, 351 municipalities, 14 counties")
def coverage(db: Session) -> str:
    tiger = pyogrio.read_info(f"zip://{TIGER_TRACTS}")["features"]
    tracts = scalar(db, "SELECT count(*) FROM tracts")
    dup = scalar(db, "SELECT count(*) - count(DISTINCT geoid) FROM tracts")
    towns = scalar(db, "SELECT count(*) FROM municipalities")
    counties = scalar(db, "SELECT count(*) FROM counties")
    assert tracts == tiger, f"{tracts} tracts in DB vs {tiger} in TIGER"
    assert dup == 0, f"{dup} duplicate geoids"
    assert towns == 351, f"{towns} municipalities"
    assert counties == 14, f"{counties} counties"
    return f"{tracts} tracts (= TIGER), {towns} municipalities, {counties} counties"


@check("every metric has a source in data_sources, listed in DATA_SOURCES.md")
def sources(db: Session) -> str:
    for table in ("tract_metrics", "area_metrics"):
        missing = scalar(
            db,
            f"SELECT count(*) FROM {table} m LEFT JOIN data_sources s ON s.id = m.source_id "
            "WHERE s.id IS NULL",
        )
        assert missing == 0, f"{missing} {table} rows without a data_sources row"
    used = rows(
        db,
        "SELECT DISTINCT s.key, s.name, s.url FROM tract_metrics m "
        "JOIN data_sources s ON s.id = m.source_id",
    )
    md = (ROOT / "DATA_SOURCES.md").read_text()
    absent = [r.key for r in used if r.name not in md or (r.url and r.url not in md)]
    assert not absent, f"not in DATA_SOURCES.md: {absent}"
    all_sources = rows(db, "SELECT key, name FROM data_sources")
    absent_all = [r.key for r in all_sources if r.name not in md]
    assert not absent_all, f"data_sources rows not in DATA_SOURCES.md: {absent_all}"
    return f"{len(used)} sources used by tract metrics; {len(all_sources)} data_sources rows"


@check("homeless estimates per tract sum to the official CoC totals")
def homeless_sums(db: Session) -> str:
    est = rows(
        db,
        "SELECT t.coc_number, min(m.year) AS y0, max(m.year) AS y1, sum(m.value) AS v, "
        "bool_and(m.is_estimate) AS flagged, count(m.method) AS with_method, count(*) AS n "
        "FROM tract_metrics m JOIN tracts t ON t.geoid = m.tract_geoid "
        "WHERE m.metric = 'homeless_estimate' GROUP BY t.coc_number",
    )
    official = {
        r.coc_number: (r.year, r.total)
        for r in rows(
            db,
            "SELECT DISTINCT ON (coc_number) coc_number, year, total FROM homelessness_counts "
            "ORDER BY coc_number, year DESC",
        )
    }
    assert est, "no homeless_estimate rows"
    assert {r.coc_number for r in est} == set(official), "CoC sets differ"
    for r in est:
        year, total = official[r.coc_number]
        assert r.y0 == r.y1 == year, f"{r.coc_number}: estimate year {r.y0}-{r.y1} vs PIT {year}"
        assert abs(r.v - total) <= TOL, f"{r.coc_number}: estimates {r.v:.2f} vs official {total}"
        assert r.flagged and r.with_method == r.n, f"{r.coc_number}: unlabelled estimate rows"
    negative = scalar(
        db, "SELECT count(*) FROM tract_metrics WHERE metric='homeless_estimate' AND value < 0"
    )
    assert negative == 0, f"{negative} negative estimates"
    return f"{len(est)} CoCs, estimates = official PIT totals, all flagged estimate with method"


@check("tract affordable-gap sums match municipality/county/state totals")
def gap_sums(db: Session) -> str:
    metric = "affordable_gap_eli"
    stored = {
        (r.level, r.area_id): r.value
        for r in rows(
            db, "SELECT level, area_id, value FROM area_metrics WHERE metric = :m", m=metric
        )
    }
    tract_total = scalar(db, "SELECT sum(value) FROM tract_metrics WHERE metric = :m", m=metric)
    assert math.isclose(stored[("state", "25")], tract_total, abs_tol=TOL), "state total"
    county = rows(
        db,
        "SELECT t.county_geoid AS id, sum(m.value) AS v FROM tract_metrics m "
        "JOIN tracts t ON t.geoid = m.tract_geoid WHERE m.metric = :m GROUP BY 1",
        m=metric,
    )
    assert len(county) == 14
    for r in county:
        assert math.isclose(stored[("county", r.id)], r.v, abs_tol=TOL), f"county {r.id}"
    town = rows(
        db,
        "SELECT tm.municipality_geoid AS id, sum(m.value * tm.housing_share) AS v "
        "FROM tract_metrics m JOIN tract_municipalities tm ON tm.tract_geoid = m.tract_geoid "
        "WHERE m.metric = :m AND tm.housing_share > 0 GROUP BY 1",
        m=metric,
    )
    stored_towns = {k[1] for k in stored if k[0] == "municipality"}
    assert len(stored_towns) == 351, f"{len(stored_towns)} towns with a gap"
    for r in town:
        assert math.isclose(stored[("municipality", r.id)], r.v, abs_tol=TOL), f"town {r.id}"
    town_sum = sum(v for (lvl, _), v in stored.items() if lvl == "municipality")
    assert math.isclose(town_sum, tract_total, abs_tol=TOL * 351), "towns do not add to state"
    return f"state {tract_total:,.0f}; 14 counties and 351 towns match tract sums"


@check("Need Index within 0-100; every missing value flagged")
def need_index(db: Session) -> str:
    total = scalar(db, "SELECT count(*) FROM tracts")
    r = db.execute(
        text(
            "SELECT count(*) AS n, count(value) AS with_value, min(value) AS lo, "
            "max(value) AS hi, count(*) FILTER (WHERE value IS NULL AND flag IS NULL) AS bare "
            "FROM tract_metrics WHERE metric = 'need_index'"
        )
    ).one()
    assert r.n == total, f"{r.n} need_index rows for {total} tracts"
    assert r.lo >= 0 and r.hi <= 100, f"range {r.lo}-{r.hi}"
    assert r.bare == 0, f"{r.bare} missing values without a flag"
    return (
        f"{r.with_value} tracts in {r.lo:.1f}-{r.hi:.1f}; {r.n - r.with_value} missing, all flagged"
    )


@check("site_candidates non-empty, scores 0-100, none >50% constrained")
def sites(db: Session) -> str:
    r = db.execute(
        text(
            "SELECT count(*) AS n, count(score) AS scored, min(score) AS lo, max(score) AS hi, "
            "max(greatest(p.openspace_overlap, p.wetland_overlap, p.flood_overlap)) AS layer, "
            "max((s.features->>'constrained_share')::float) AS union_share, "
            "count(*) FILTER (WHERE s.features->>'constrained_share' IS NULL) AS no_union "
            "FROM site_candidates s JOIN parcels p ON p.loc_id = s.parcel_loc_id"
        )
    ).one()
    assert r.n > 0, "no candidate sites"
    assert r.scored == r.n, f"{r.n - r.scored} sites without a score"
    assert r.lo >= 0 and r.hi <= 100, f"score range {r.lo}-{r.hi}"
    assert r.layer <= 0.5, f"a site overlaps a constraint layer by {r.layer:.0%}"
    assert r.no_union == 0 and r.union_share <= 0.5, f"union overlap up to {r.union_share}"
    return (
        f"{r.n:,} sites, scores {r.lo}-{r.hi}; max overlap {r.layer:.0%} per layer, "
        f"{r.union_share:.0%} combined"
    )


# ---------------------------------------------------------------- API checks
def _containing(db: Session, table: str, id_col: str, lat: float, lon: float) -> list[str]:
    """Independent brute-force point-in-polygon over the stored boundaries."""
    pt = Point(lon, lat)
    out = []
    for r in rows(db, f"SELECT {id_col} AS id, boundary FROM {table}"):
        b = r.boundary if isinstance(r.boundary, dict) else json.loads(r.boundary)
        if shape(b).covers(pt):
            out.append(str(r.id))
    return out


@check("/api/area-stats: all metrics for 3 rings at Boston, Worcester, Springfield")
def area_stats(client: TestClient) -> str:
    for city, (lat, lon) in POINTS.items():
        resp = client.post(
            "/api/area-stats", json={"lat": lat, "lon": lon, "radii_km": [1.5, 5, 15]}
        )
        assert resp.status_code == 200, f"{city}: HTTP {resp.status_code}"
        rings = resp.json()["rings"]
        assert len(rings) == 3, f"{city}: {len(rings)} rings"
        for ring in rings:
            missing = [m for m in RING_METRICS if ring.get(m) is None]
            assert not missing, f"{city} {ring['radius_km']} km: missing {missing}"
            assert ring["homeless"]["label"] == "estimate", f"{city}: homeless not labelled"
    return "3 rings x 3 cities, every metric present, homeless labelled estimate"


@check("/api/areas/at: right tract, town, county and CoC; CoC estimate sum = official")
def areas_at(client: TestClient, db: Session) -> str:
    levels = {
        "tract": ("tracts", "geoid"),
        "municipality": ("municipalities", "geoid"),
        "county": ("counties", "geoid"),
        "coc": ("cocs", "coc_number"),
    }
    found = []
    for city, (lat, lon) in POINTS.items():
        ids = []
        for level, (table, col) in levels.items():
            resp = client.get("/api/areas/at", params={"lat": lat, "lon": lon, "level": level})
            assert resp.status_code == 200, f"{city} {level}: HTTP {resp.status_code}"
            body = resp.json()
            expected = _containing(db, table, col, lat, lon)
            assert body["id"] in expected and len(expected) >= 1, (
                f"{city} {level}: API {body['id']} vs containing {expected}"
            )
            if level == "municipality":
                assert body["name"] == city, f"{city}: town {body['name']}"
            if level == "coc":
                official = body["figures"]["homeless"]
                est = body["homeless_estimate_sum"]
                assert official["label"] == "official CoC count", f"{city}: CoC label"
                assert est["label"] == "estimate", f"{city}: estimate label"
                assert abs(est["value"] - official["value"]) <= TOL, (
                    f"{city}: estimates {est['value']} vs official {official['value']}"
                )
            else:
                assert body["figures"]["homeless"]["label"] == "estimate", f"{city} {level}"
            ids.append(body["id"])
        found.append(f"{city}: " + "/".join(ids))
    return "; ".join(found)


# ---------------------------------------------------------------- report checks
@check("reports/model_metrics.json exists; target met or REPORT.md says it is not")
def model_metrics() -> str:
    m = json.loads((REPORTS / "model_metrics.json").read_text())
    test = m["chosen_model"]["test_mape"]
    base = m["baseline"]["test_mape"]
    improvement = 1 - test / base
    met = improvement >= 0.25
    assert m["target_met"] == met, "target_met disagrees with the recorded MAPEs"
    if not met:
        report = (REPORTS / "REPORT.md").read_text().lower()
        assert "not met" in report, "target missed but REPORT.md does not say so"
    status = "met" if met else "NOT met (stated in REPORT.md)"
    return f"test MAPE {test:.1%} vs baseline {base:.1%} ({improvement:.0%} lower): target {status}"


@check("STATISTICS.md, REPORT.md, top_tracts.csv, candidate_sites.csv exist and aren't empty")
def reports() -> str:
    sizes = {}
    for name in ("STATISTICS.md", "REPORT.md", "top_tracts.csv", "candidate_sites.csv"):
        path = REPORTS / name
        assert path.exists(), f"{name} missing"
        lines = path.read_text().strip().splitlines()
        assert len(lines) > (1 if name.endswith(".csv") else 5), f"{name} is empty"
        sizes[name] = len(lines)
    report = (REPORTS / "REPORT.md").read_text()
    assert "To be completed" not in report, "REPORT.md still has unfinished sections"
    return ", ".join(f"{k} {v} lines" for k, v in sizes.items())


# ---------------------------------------------------------------- commands and git
def command_check(name: str, cmd: list[str], cwd: Path) -> None:
    @check(name)
    def run() -> str:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=os.environ)
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]
        assert proc.returncode == 0, f"exit {proc.returncode}: {tail[0]}"
        return tail[0][:120]

    run()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


@check("git: no unmerged task/* branches, clean tree, no open PRs")
def git_state() -> str:
    status = git("status", "--porcelain")
    assert not status, f"working tree not clean: {status.splitlines()[:5]}"
    branch = git("branch", "--show-current")
    assert branch == "main", f"on branch {branch}, expected main"
    local = git("branch", "--list", "task/*", "--no-merged", "main")
    assert not local, f"unmerged local task branches: {local.split()}"
    remote = git("branch", "-r", "--list", "origin/task/*", "--no-merged", "main")
    assert not remote, f"unmerged remote task branches: {remote.split()}"
    detail = "clean main, no unmerged task branches"
    if os.environ.get("MERGE_MODE", "pr") == "pr":
        prs = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "number"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert json.loads(prs) == [], f"open PRs: {prs.strip()}"
        detail += ", no open PRs"
    return detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-git", action="store_true")
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args()

    with get_session_factory()() as db:
        coverage(db)
        sources(db)
        homeless_sums(db)
        gap_sums(db)
        need_index(db)
        sites(db)
        with TestClient(create_app()) as client:
            area_stats(client)
            areas_at(client, db)
    model_metrics()
    reports()
    if not args.skip_commands:
        command_check("backend pytest", ["uv", "run", "pytest", "-q"], BACKEND)
        command_check("backend ruff check", ["uv", "run", "ruff", "check", "."], BACKEND)
        command_check("frontend npm run build", ["npm", "run", "build"], FRONTEND)
        command_check("frontend npm run lint", ["npm", "run", "lint"], FRONTEND)
    if not args.skip_git:
        git_state()

    for ok, name, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} — {detail}")
    failed = sum(not ok for ok, _, _ in results)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
