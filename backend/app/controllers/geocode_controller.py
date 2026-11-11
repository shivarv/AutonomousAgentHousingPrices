from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_geocode_service
from app.schemas.geocode import GeocodeResult
from app.services.geocode_service import GeocodeService

router = APIRouter(prefix="/api", tags=["geocode"])


@router.get("/geocode", response_model=GeocodeResult)
def geocode(
    service: Annotated[GeocodeService, Depends(get_geocode_service)],
    q: Annotated[str, Query(description="one-line address in Massachusetts")] = "",
) -> GeocodeResult:
    return service.search(q)
