from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_area_service
from app.schemas.area import (
    AreaAt,
    AreaLevel,
    AreaOutlines,
    AreaStatsRequest,
    AreaStatsResponse,
    AreaSummary,
    AreaSummaryRequest,
)
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


@router.get("/areas", response_model=AreaOutlines)
def areas(
    service: Service,
    level: AreaLevel = "municipality",
    bbox: Annotated[str | None, Query(description="minLon,minLat,maxLon,maxLat")] = None,
) -> Response:
    return Response(
        content=service.outlines(level, bbox),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.post("/areas/summary", response_model=AreaSummary)
def areas_summary(body: AreaSummaryRequest, service: Service) -> AreaSummary:
    return service.summary(body.level, body.ids)
