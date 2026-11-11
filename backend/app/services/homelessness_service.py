"""Official homelessness layer: HUD PIT counts and HIC beds, presented only as CoC totals."""

from collections import defaultdict
from typing import Any

from app.core.exceptions import NotFoundError
from app.dao.homelessness_dao import HomelessnessDao
from app.schemas.homelessness import (
    CocHomelessness,
    HomelessnessOverview,
    PitYear,
    StateHomelessness,
)

BED_FIELDS = (
    "emergency_shelter_beds",
    "transitional_beds",
    "safe_haven_beds",
    "total_year_round_beds",
)


def _sum(values: list[int | None]) -> int | None:
    """Sum that is None if any part is missing (a partial sum would understate the total)."""
    if any(v is None for v in values):
        return None
    return sum(v for v in values if v is not None)


def build_years(rows: list[dict[str, Any]]) -> list[PitYear]:
    """rows sorted by year with PIT and (optional) bed fields -> PitYear with trend."""
    out: list[PitYear] = []
    prev: dict[str, Any] | None = None
    for r in rows:
        change = pct = None
        if prev is not None and prev["year"] == r["year"] - 1:
            change = r["total"] - prev["total"]
            pct = round(100.0 * change / prev["total"], 1) if prev["total"] else None
        out.append(
            PitYear(
                year=r["year"],
                sheltered=r.get("sheltered"),
                unsheltered=r.get("unsheltered"),
                total=r["total"],
                change_from_previous=change,
                pct_change_from_previous=pct,
                **{f: r.get(f) for f in BED_FIELDS},
            )
        )
        prev = r
    return out


class HomelessnessService:
    def __init__(self, dao: HomelessnessDao) -> None:
        self.dao = dao

    def _merged(self, coc_number: str | None) -> dict[str, list[dict[str, Any]]]:
        beds = {(b.coc_number, b.year): b._asdict() for b in self.dao.bed_counts(coc_number)}
        series: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in self.dao.pit_counts(coc_number):
            row = p._asdict()
            bed = beds.get((p.coc_number, p.year))
            row["bed_source_key"] = bed["source_key"] if bed else None
            for f in BED_FIELDS:
                row[f] = bed[f] if bed else None
            series[p.coc_number].append(row)
        return series

    @staticmethod
    def _coc(rows: list[dict[str, Any]]) -> CocHomelessness:
        years = build_years(rows)
        sources = sorted(
            {r["source_key"] for r in rows}
            | {r["bed_source_key"] for r in rows if r["bed_source_key"]}
        )
        return CocHomelessness(
            coc_number=rows[0]["coc_number"],
            coc_name=rows[0]["coc_name"],
            latest_year=years[-1].year,
            latest=years[-1],
            years=years,
            sources=sources,
        )

    def coc(self, coc_number: str) -> CocHomelessness:
        series = self._merged(coc_number)
        if coc_number not in series:
            raise NotFoundError(f"no PIT counts for CoC '{coc_number}'")
        return self._coc(series[coc_number])

    def overview(self) -> HomelessnessOverview:
        series = self._merged(None)
        cocs = [self._coc(rows) for _, rows in sorted(series.items())]
        # statewide only for years every CoC reported (otherwise the sum would be partial)
        by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for rows in series.values():
            for r in rows:
                by_year[r["year"]].append(r)
        state_rows = []
        for year in sorted(by_year):
            parts = by_year[year]
            if len(parts) != len(series):
                continue
            row: dict[str, Any] = {"year": year, "total": sum(p["total"] for p in parts)}
            for f in ("sheltered", "unsheltered", *BED_FIELDS):
                row[f] = _sum([p[f] for p in parts])
            state_rows.append(row)
        state = StateHomelessness(coc_count=len(series), years=build_years(state_rows))
        return HomelessnessOverview(state=state, cocs=cocs)
