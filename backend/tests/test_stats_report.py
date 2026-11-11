import re
from datetime import date

from sqlalchemy.orm import Session

from app.dao.homelessness_dao import HomelessnessDao
from app.services.homelessness_service import HomelessnessService
from pipeline.paths import REPORTS_DIR
from pipeline.stats_report import (
    collect,
    fmt_int,
    fmt_pct,
    fmt_pct_points,
    fmt_signed,
    gap_words,
    pct_change,
    render,
    table,
)


def test_formatting_helpers() -> None:
    assert fmt_int(1234.6) == "1,235"
    assert fmt_int(None) == "n/a"
    assert fmt_signed(-1049) == "-1,049"
    assert fmt_signed(12) == "+12"
    assert fmt_pct(0.0809) == "8.1%"
    assert fmt_pct_points(-3.57) == "-3.6%"
    assert pct_change(150, 100) == 0.5
    assert pct_change(1, 0) is None
    assert gap_words(120) == "shortage of 120"
    assert gap_words(-30) == "surplus of 30"
    assert gap_words(0) == "balanced"
    assert gap_words(None) == "n/a"


def test_table_markdown() -> None:
    assert table(("a", "b"), [(1, 2)]) == "| a | b |\n|---|---|\n| 1 | 2 |"


def test_render_from_database(seeded: Session) -> None:
    data = collect(seeded)
    text = render(data, date(2026, 1, 1))
    official = HomelessnessService(HomelessnessDao(seeded)).overview().state
    latest = max(official.years, key=lambda y: y.year)

    # Statewide official total, and the estimate sum check equals it.
    assert f"| {fmt_int(latest.total)} | hud_pit, {latest.year} |" in text
    assert f"| {fmt_int(latest.total)} (estimate) |" in text
    # Every CoC and every county appears; county homeless figures are labelled estimates.
    for coc in data["cocs"]:
        assert coc.coc_number in text
    county_rows = [
        line for line in text.splitlines() if line.startswith("| ") and " County |" in line
    ]
    county_names = {row.name for row, _ in data["counties"]}
    assert len(county_names) == 14
    for name in county_names:
        assert any(line.startswith(f"| {name} |") and "(estimate)" in line for line in county_rows)
    # Site tables: every ring homeless figure is labelled an estimate.
    site_lines = [
        line for line in text.splitlines() if re.match(r"\| \d+ \| .* \| (yes|no) \|$", line)
    ]
    assert site_lines and all("(estimate)" in line for line in site_lines)
    assert "official CoC count" in text


def test_committed_statistics_present() -> None:
    path = REPORTS_DIR / "STATISTICS.md"
    assert path.exists()
    text = path.read_text()
    for heading in (
        "## 1. Statewide",
        "## 3. Homelessness by Continuum of Care",
        "## 4. Counties",
        "## 5. Top need areas",
        "## 6. Top candidate construction sites",
    ):
        assert heading in text
