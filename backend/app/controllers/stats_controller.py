from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_stats_service
from app.schemas.stats import OverviewLevel, StatsOverview
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverview)
def overview(
    service: Annotated[StatsService, Depends(get_stats_service)],
    level: OverviewLevel = "state",
    id: Annotated[str | None, Query(description="county GEOID or town GEOID")] = None,
) -> StatsOverview:
    return service.overview(level, id)
