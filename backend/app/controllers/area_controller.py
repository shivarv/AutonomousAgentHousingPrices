from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_area_service
from app.schemas.area import AreaStatsRequest, AreaStatsResponse
from app.services.area_service import AreaService

router = APIRouter(prefix="/api", tags=["areas"])
Service = Annotated[AreaService, Depends(get_area_service)]


@router.post("/area-stats", response_model=AreaStatsResponse)
def area_stats(body: AreaStatsRequest, service: Service) -> AreaStatsResponse:
    return service.ring_stats(body.lat, body.lon, body.radii_km)
