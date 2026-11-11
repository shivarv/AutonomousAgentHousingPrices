"""Outcome 1 statistics for the state, a county or a town (GET /api/stats/overview)."""

from app.core.exceptions import NotFoundError, ValidationError
from app.dao.area_dao import AreaDao
from app.schemas.estimate import HomelessFigure
from app.schemas.homelessness import CocHomelessness
from app.schemas.metric import MetricValue
from app.schemas.stats import OverviewHomelessness, ShelterBeds, StatsOverview
from app.services.homelessness_service import HomelessnessService

STATE_ID = "25"
STATE_NAME = "Massachusetts"
OVERVIEW_METRICS = (
    "population",
    "households",
    "renter_households",
    "eli_renter_households",
    "eli_severely_burdened_renters",
    "units_affordable_available_eli",
    "affordable_gap_eli",
    "affordable_units_per_100_eli",
    "housing_units",
    "vacant_units",
    "vacancy_rate",
    "poverty_rate",
    "severe_rent_burden_share",
    "hud_assisted_units",
    "lihtc_low_income_units",
    "need_index",
    "homeless_estimate",
)
AREA_NOTE = (
    "Official homelessness counts exist only per Continuum of Care (CoC). The area figure "
    "is a sum of modelled tract estimates (label 'estimate'); the CoC counts listed are for "
    "the whole CoC, which can be larger than this area."
)
STATE_NOTE = (
    "The statewide official count is the sum of the Massachusetts CoC Point-in-Time counts."
)


def beds_for(cocs: list[CocHomelessness]) -> ShelterBeds:
    """Sum of HIC year-round beds over ``cocs`` for the latest year all of them report."""
    if not cocs:
        return ShelterBeds(value=None, year=None, geography="no CoC")
    years = [{y.year for y in c.years if y.total_year_round_beds is not None} for c in cocs]
    common = set.intersection(*years) if years else set()
    names = ", ".join(c.coc_number for c in cocs)
    geography = f"CoC {names}" if len(cocs) == 1 else f"sum of CoCs {names}"
    if not common:
        return ShelterBeds(value=None, year=None, geography=geography)
    year = max(common)
    total = sum(y.total_year_round_beds or 0 for c in cocs for y in c.years if y.year == year)
    return ShelterBeds(value=total, year=year, geography=geography)


class StatsService:
    def __init__(self, areas: AreaDao, homelessness: HomelessnessService) -> None:
        self.areas = areas
        self.homelessness = homelessness

    def overview(self, level: str, area_id: str | None) -> StatsOverview:
        if level == "state":
            area_id, name = STATE_ID, STATE_NAME
        elif level in ("county", "municipality"):
            if not area_id:
                raise ValidationError(f"id is required for level={level}")
            name = self.areas.area_name(level, area_id)
            if name is None:
                raise NotFoundError(f"no {level} with id '{area_id}'")
        else:
            raise ValidationError("level must be state, county or municipality")

        rows = [r for r in self.areas.metrics(level, [area_id]) if r.metric in OVERVIEW_METRICS]
        metrics = {r.metric: MetricValue.from_row(r) for r in rows}
        est = metrics.pop("homeless_estimate", None)
        area_estimate = HomelessFigure.estimate(
            None if est is None or est.value is None else round(est.value, 1),
            est.year if est else None,
            est.method if est else None,
        )
        overview = self.homelessness.overview()
        wanted = set(self.areas.cocs_of(level, area_id))
        cocs = [c for c in overview.cocs if c.coc_number in wanted]
        return StatsOverview(
            level=level,  # type: ignore[arg-type]
            id=area_id,
            name=name,
            metrics=metrics,
            homelessness=OverviewHomelessness(
                official_state=overview.state if level == "state" else None,
                official_cocs=cocs,
                area_estimate=area_estimate,
                note=STATE_NOTE if level == "state" else AREA_NOTE,
            ),
            shelter_beds=beds_for(cocs),
        )
