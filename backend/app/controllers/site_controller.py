from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_site_service
from app.schemas.site import SiteDetail, SiteList
from app.services.site_service import SiteService

router = APIRouter(prefix="/api/sites", tags=["sites"])
Service = Annotated[SiteService, Depends(get_site_service)]


@router.get("", response_model=SiteList)
def sites(
    service: Service,
    county: str | None = None,
    municipality: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> SiteList:
    return service.list(county, municipality, limit, offset)


@router.get("/best", response_model=SiteDetail)
def best_site(
    service: Service,
    county: str | None = None,
    municipality: str | None = None,
    offset: Annotated[int, Query(description="0 = best, 1 = next best, ...")] = 0,
) -> SiteDetail:
    return service.best(county, municipality, offset)


@router.get("/{site_id}", response_model=SiteDetail)
def site(site_id: int, service: Service) -> SiteDetail:
    return service.detail(site_id)
