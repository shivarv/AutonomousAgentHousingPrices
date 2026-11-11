"""reports/STATISTICS.md — Outcome 1 in writing, generated from the loaded database.

Every figure is read through the same services the API uses (StatsService, HomelessnessService,
SiteService), so the report and the web app always agree; nothing is typed in by hand.
Official homelessness figures are HUD PIT/HIC counts per Continuum of Care (CoC); county and
town homelessness figures are sums of modelled tract estimates and are labelled "estimate".

Run: uv run python -m pipeline.stats_report   (after the pipeline has loaded the database and
pipeline.index.report has written reports/municipality_need.csv)
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.dao.area_dao import AreaDao
from app.dao.homelessness_dao import HomelessnessDao
from app.dao.site_dao import SiteDao
from app.schemas.homelessness import CocHomelessness, PitYear
from app.schemas.site import SiteSummary
from app.schemas.stats import StatsOverview
from app.services.homelessness_service import HomelessnessService
from app.services.site_service import SiteService
from app.services.stats_service import StatsService
from pipeline.paths import REPORTS_DIR

log = logging.getLogger("pipeline.stats_report")

OUT = REPORTS_DIR / "STATISTICS.md"
TOWN_CSV = REPORTS_DIR / "municipality_need.csv"
TOP_SITES = 15
TOP_TOWNS = 15
# Towns this small are ranked separately: one or two tracts make their index volatile.
LARGE_TOWN_POPULATION = 10_000


# ---------------------------------------------------------------- formatting helpers
def fmt_int(v: float | None) -> str:
    return "n/a" if v is None else f"{round(v):,}"


def fmt_signed(v: float | None) -> str:
    return "n/a" if v is None else f"{round(v):+,}"


def fmt_pct(v: float | None, digits: int = 1) -> str:
    return "n/a" if v is None else f"{v * 100:.{digits}f}%"


def fmt_num(v: float | None, digits: int = 1) -> str:
    return "n/a" if v is None else f"{v:,.{digits}f}"


def fmt_pct_points(v: float | None) -> str:
    """A value already in percent (e.g. PitYear.pct_change_from_previous)."""
    return "n/a" if v is None else f"{v:+.1f}%"


def pct_change(new: float | None, old: float | None) -> float | None:
    if new is None or old is None or old == 0:
        return None
    return (new - old) / old


def gap_words(gap: float | None) -> str:
    """Positive gap = more ELI renter households than affordable & available units."""
    if gap is None:
        return "n/a"
    if gap > 0:
        return f"shortage of {fmt_int(gap)}"
    if gap < 0:
        return f"surplus of {fmt_int(-gap)}"
    return "balanced"


def table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def metric(o: StatsOverview, key: str) -> float | None:
    m = o.metrics.get(key)
    return None if m is None else m.value


def provenance(o: StatsOverview, key: str) -> str:
    m = o.metrics.get(key)
    if m is None:
        return "n/a"
    return f"{m.source or 'n/a'}, {m.year or 'n/a'}"


# ---------------------------------------------------------------- data collection
def collect(session: Session) -> dict[str, Any]:
    homelessness = HomelessnessService(HomelessnessDao(session))
    stats = StatsService(AreaDao(session), homelessness)
    sites = SiteService(SiteDao(session))

    state = stats.overview("state", None)
    county_table = stats.table("county")
    counties = [
        (row, stats.overview("county", row.id))
        for row in sorted(county_table.rows, key=lambda r: r.name)
    ]
    best_by_county: list[SiteSummary] = []
    for row, _ in counties:
        found = sites.list(row.id, None, 1).sites
        if found:
            best_by_county.append(found[0])
    top = sites.list(None, None, TOP_SITES)
    return {
        "state": state,
        "cocs": homelessness.overview().cocs,
        "counties": counties,
        "top_sites": top.sites,
        "site_total": top.total,
        "best_by_county": best_by_county,
        "towns": pd.read_csv(TOWN_CSV, dtype={"town_geoid": str}) if TOWN_CSV.exists() else None,
    }


# ---------------------------------------------------------------- sections
def _state_section(state: StatsOverview) -> str:
    official = state.homelessness.official_state
    assert official is not None
    years = sorted(official.years, key=lambda y: y.year)
    latest, first = years[-1], years[0]
    prev = years[-2] if len(years) > 1 else None
    est = state.homelessness.area_estimate
    beds = state.shelter_beds
    gap = metric(state, "affordable_gap_eli")
    rows = [
        ("Population", fmt_int(metric(state, "population")), provenance(state, "population")),
        (
            f"People experiencing homelessness, PIT {latest.year} (official CoC count, "
            f"sum of {official.coc_count} CoCs)",
            fmt_int(latest.total),
            f"hud_pit, {latest.year}",
        ),
        ("— sheltered", fmt_int(latest.sheltered), f"hud_pit, {latest.year}"),
        ("— unsheltered", fmt_int(latest.unsheltered), f"hud_pit, {latest.year}"),
        (
            f"Change from {prev.year if prev else 'n/a'}",
            f"{fmt_signed(latest.change_from_previous)} "
            f"({fmt_pct_points(latest.pct_change_from_previous)})",
            "hud_pit",
        ),
        (
            f"Change from {first.year}",
            f"{fmt_signed(latest.total - first.total)} "
            f"({fmt_pct(pct_change(latest.total, first.total))})",
            "hud_pit",
        ),
        (
            f"Year-round shelter beds, HIC {beds.year} (official CoC count)",
            fmt_int(beds.value),
            f"hud_hic, {beds.year}",
        ),
        (
            "Year-round beds per person counted",
            fmt_num(
                None
                if beds.value is None or beds.year != latest.year
                else beds.value / latest.total,
                2,
            ),
            "computed (HIC beds / PIT total, same year)",
        ),
        (
            "Extremely-low-income (<=30% AMI) renter households",
            fmt_int(metric(state, "eli_renter_households")),
            provenance(state, "eli_renter_households"),
        ),
        (
            "— of which severely rent-burdened (at-risk households)",
            fmt_int(metric(state, "eli_severely_burdened_renters")),
            provenance(state, "eli_severely_burdened_renters"),
        ),
        (
            "Units affordable and available to ELI renters",
            fmt_int(metric(state, "units_affordable_available_eli")),
            provenance(state, "units_affordable_available_eli"),
        ),
        ("Affordable housing gap (ELI)", gap_words(gap), provenance(state, "affordable_gap_eli")),
        (
            "Affordable & available units per 100 ELI renter households",
            fmt_num(metric(state, "affordable_units_per_100_eli")),
            provenance(state, "affordable_units_per_100_eli"),
        ),
        (
            "Housing units",
            fmt_int(metric(state, "housing_units")),
            provenance(state, "housing_units"),
        ),
        ("Vacancy rate", fmt_pct(metric(state, "vacancy_rate")), provenance(state, "vacancy_rate")),
        (
            "HUD-assisted units",
            fmt_int(metric(state, "hud_assisted_units")),
            provenance(state, "hud_assisted_units"),
        ),
        (
            "LIHTC low-income units",
            fmt_int(metric(state, "lihtc_low_income_units")),
            provenance(state, "lihtc_low_income_units"),
        ),
        (
            "Housing Need Index (population-weighted mean of tracts, 0-100)",
            fmt_num(metric(state, "need_index")),
            f"computed from 8 components (REPORT.md 3.3), {state.metrics['need_index'].year}"
            if "need_index" in state.metrics
            else "n/a",
        ),
        (
            "Sum of tract homeless estimates (check: equals the official total)",
            f"{fmt_int(est.value)} ({est.label})",
            f"modelled, PIT {est.year}",
        ),
    ]
    return "## 1. Statewide\n\n" + table(("Figure", "Value", "Source, year"), rows)


def _trend_section(state: StatsOverview) -> str:
    official = state.homelessness.official_state
    assert official is not None
    years: list[PitYear] = sorted(official.years, key=lambda y: y.year)
    peak = max(years, key=lambda y: y.total)
    low = min(years, key=lambda y: y.total)
    rows = [
        (
            y.year,
            fmt_int(y.total),
            fmt_int(y.sheltered),
            fmt_int(y.unsheltered),
            fmt_signed(y.change_from_previous),
            fmt_pct_points(y.pct_change_from_previous),
            fmt_int(y.total_year_round_beds),
        )
        for y in years
    ]
    return (
        "## 2. Homelessness trend, Massachusetts (official CoC counts)\n\n"
        "HUD Point-in-Time counts summed over the Massachusetts CoCs (one night each January) and "
        "HUD Housing Inventory Count year-round beds. "
        f"Highest count in the series: {fmt_int(peak.total)} ({peak.year}); "
        f"lowest: {fmt_int(low.total)} ({low.year}).\n\n"
        + table(
            (
                "Year",
                "Total",
                "Sheltered",
                "Unsheltered",
                "Change",
                "Change %",
                "Year-round beds",
            ),
            rows,
        )
    )


def _coc_section(cocs: list[CocHomelessness]) -> str:
    rows = []
    for c in sorted(cocs, key=lambda c: -c.latest.total):
        first = min(c.years, key=lambda y: y.year)
        rows.append(
            (
                f"{c.coc_number} {c.coc_name}",
                c.latest_year,
                fmt_int(c.latest.total),
                fmt_int(c.latest.sheltered),
                fmt_int(c.latest.unsheltered),
                f"{fmt_signed(c.latest.change_from_previous)} "
                f"({fmt_pct_points(c.latest.pct_change_from_previous)})",
                f"{fmt_pct(pct_change(c.latest.total, first.total))} since {first.year}",
                fmt_int(c.latest.total_year_round_beds),
            )
        )
    return (
        "## 3. Homelessness by Continuum of Care (official CoC counts)\n\n"
        "These are the only exact homelessness figures: HUD publishes PIT and HIC per CoC.\n\n"
        + table(
            (
                "CoC",
                "Year",
                "Total",
                "Sheltered",
                "Unsheltered",
                "Change from previous year",
                "Long-run change",
                "Year-round beds",
            ),
            rows,
        )
    )


def _county_section(counties: list[tuple[Any, StatsOverview]]) -> str:
    rows = []
    for row, o in counties:
        cocs = ", ".join(c.coc_number for c in o.homelessness.official_cocs)
        rows.append(
            (
                row.name,
                fmt_int(row.population),
                f"{fmt_int(row.homeless_estimate)} (estimate)",
                cocs or "n/a",
                fmt_int(metric(o, "eli_renter_households")),
                fmt_int(metric(o, "units_affordable_available_eli")),
                gap_words(row.affordable_gap_eli),
                fmt_num(row.affordable_units_per_100_eli),
                fmt_num(row.need_index),
            )
        )
    shortage = sorted(
        (r for r, _ in counties if r.affordable_gap_eli is not None),
        key=lambda r: -(r.affordable_gap_eli or 0),
    )
    top3 = "; ".join(f"{r.name} ({gap_words(r.affordable_gap_eli)})" for r in shortage[:3])
    return (
        "## 4. Counties\n\n"
        "Homeless figures per county are **estimates**: the sum of modelled tract estimates "
        "(method in REPORT.md 3.2), not counts. The CoCs that overlap each county are listed; "
        "their official totals are in section 3 and cover the whole CoC. Affordable gap from "
        "HUD CHAS 2018-2022; Need Index is the population-weighted tract mean.\n\n"
        f"Largest ELI shortages: {top3}.\n\n"
        + table(
            (
                "County",
                "Population",
                "Homeless (estimate)",
                "CoCs",
                "ELI renter households",
                "Affordable & available units",
                "Gap",
                "Units per 100 ELI",
                "Need Index",
            ),
            rows,
        )
    )


def _town_section(towns: pd.DataFrame | None) -> str:
    if towns is None:
        return (
            "## 5. Top need areas\n\n"
            "reports/municipality_need.csv not found; run pipeline.index.report."
        )
    cols = (
        "Rank",
        "Town",
        "County",
        "Need Index",
        "Population",
        "Gap",
        "Units per 100 ELI",
        "Homeless (estimate)",
    )

    def rows(df: pd.DataFrame) -> list[tuple[Any, ...]]:
        return [
            (
                i + 1,
                r.municipality,
                r.county,
                fmt_num(r.need_index_pop_weighted),
                fmt_int(r.population),
                gap_words(r.affordable_gap_eli),
                fmt_num(r.affordable_units_per_100_eli),
                fmt_num(r.homeless_estimate_ESTIMATE),
            )
            for i, r in enumerate(df.itertuples())
        ]

    ranked = towns.dropna(subset=["need_index_pop_weighted"]).sort_values(
        "need_index_pop_weighted", ascending=False
    )
    large = ranked[ranked["population"] >= LARGE_TOWN_POPULATION]
    by_gap = towns.dropna(subset=["affordable_gap_eli"]).sort_values(
        "affordable_gap_eli", ascending=False
    )
    return (
        "## 5. Top need areas\n\n"
        f"Cities and towns by population-weighted Housing Need Index. Small towns (one or two "
        f"tracts) can rank high on a single tract, so towns with at least "
        f"{LARGE_TOWN_POPULATION:,} residents are also ranked separately. Tract-level rankings "
        "are in reports/top_tracts.csv.\n\n"
        f"### 5.1 All towns, top {TOP_TOWNS}\n\n"
        + table(cols, rows(ranked.head(TOP_TOWNS)))
        + f"\n\n### 5.2 Towns with {LARGE_TOWN_POPULATION:,}+ residents, top {TOP_TOWNS}\n\n"
        + table(cols, rows(large.head(TOP_TOWNS)))
        + f"\n\n### 5.3 Largest affordable shortages (ELI households), top {TOP_TOWNS}\n\n"
        + table(cols, rows(by_gap.head(TOP_TOWNS)))
    )


def _site_rows(sites: list[SiteSummary]) -> list[tuple[Any, ...]]:
    return [
        (
            s.rank_state,
            s.municipality,
            s.county,
            fmt_num(s.score),
            fmt_num(s.lot_size_acres, 2),
            fmt_num(s.need_index_5km),
            gap_words(s.affordable_gap_eli_5km),
            f"{fmt_num(s.homeless_5km.value)} ({s.homeless_5km.label})",
            fmt_num(s.nearest_stop_km, 2),
            "yes" if s.in_mbta3a_district else "no",
        )
        for s in sites
    ]


def _sites_section(top: list[SiteSummary], total: int, best: list[SiteSummary]) -> str:
    cols = (
        "State rank",
        "Town",
        "County",
        "Score",
        "Acres",
        "Need Index (5 km)",
        "ELI gap (5 km)",
        "Homeless within 5 km",
        "Nearest stop (km)",
        "3A district",
    )
    first = top[0] if top else None
    lead = f"Top site: {first.municipality} — {first.summary}\n\n" if first else ""
    return (
        "## 6. Top candidate construction sites\n\n"
        f"{fmt_int(total)} screened parcels (vacant or developable land use, at least 0.5 acre, "
        "no more than 50% in protected open space, wetlands or FEMA 100-year flood zones) scored "
        "0-100 (weights in REPORT.md 3.5). Ring figures are area-share-weighted tract totals "
        "within 5 km; homeless figures within rings are estimates. Full lists in "
        "reports/candidate_sites.csv and the site explorer.\n\n"
        + lead
        + f"### 6.1 Statewide, top {len(top)}\n\n"
        + table(cols, _site_rows(top))
        + "\n\n### 6.2 Best site in each county\n\n"
        + table(cols, _site_rows(sorted(best, key=lambda s: s.county)))
    )


def render(data: dict[str, Any], generated: date | None = None) -> str:
    generated = generated or date.today()
    parts = [
        "# Massachusetts housing need — statistics (Outcome 1)",
        f"Generated {generated.isoformat()} by `pipeline.stats_report` from the loaded "
        "database (the same services as the API). Sources and years are given per figure; "
        "dataset details in DATA_SOURCES.md. **Official** homelessness counts exist only per "
        "Continuum of Care; any homelessness figure below CoC level is a modelled **estimate**.",
        _state_section(data["state"]),
        _trend_section(data["state"]),
        _coc_section(data["cocs"]),
        _county_section(data["counties"]),
        _town_section(data["towns"]),
        _sites_section(data["top_sites"], data["site_total"], data["best_by_county"]),
    ]
    return "\n\n".join(parts) + "\n"


def run() -> str:
    with get_session_factory()() as session:
        text = render(collect(session))
    OUT.write_text(text)
    log.info("wrote %s (%d lines)", OUT, text.count("\n"))
    return text


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
