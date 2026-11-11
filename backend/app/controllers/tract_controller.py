from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_tract_service
from app.schemas.tract import TractDetail, TractFeatureCollection
from app.services.tract_service import TractService

router = APIRouter(prefix="/api/tracts", tags=["tracts"])


@router.get("", response_model=TractFeatureCollection)
def tracts(
    service: Annotated[TractService, Depends(get_tract_service)],
    county: Annotated[str | None, Query(description="county GEOID, e.g. 25025")] = None,
    municipality: Annotated[str | None, Query(description="town GEOID (10 digits)")] = None,
) -> Response:
    # pre-serialised and cached by the service (statewide layer is ~1.5 MB)
    return Response(
        content=service.geojson(county, municipality),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/{geoid}", response_model=TractDetail)
def tract(geoid: str, service: Annotated[TractService, Depends(get_tract_service)]) -> TractDetail:
    return service.detail(geoid)
