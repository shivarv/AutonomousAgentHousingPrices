from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_area_service
from app.schemas.area import AreaAt, AreaLevel, AreaStatsRequest, AreaStatsResponse
from app.services.area_service import AreaService

router = APIRouter(prefix="/api", tags=["areas"])
Service = Annotated[AreaService, Depends(get_area_service)]


@router.post("/area-stats", response_model=AreaStatsResponse)
def area_stats(body: AreaStatsRequest, service: Service) -> AreaStatsResponse:
    return service.ring_stats(body.lat, body.lon, body.radii_km)


@router.get("/areas/at", response_model=AreaAt)
def area_at(
    service: Service,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    level: AreaLevel = "tract",
) -> AreaAt:
    return service.area_at(lat, lon, level)
