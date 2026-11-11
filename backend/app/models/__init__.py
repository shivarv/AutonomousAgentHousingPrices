"""Every ORM model is imported here so Alembic autogenerate sees it."""

from app.models.base import Base
from app.models.data_source import DataSource
from app.models.geography import (
    BostonNeighbourhood,
    Coc,
    CocMunicipality,
    County,
    Municipality,
    NeighbourhoodTract,
    Tract,
    TractMunicipality,
    ZipTract,
)
from app.models.homelessness import CocBedCount, HomelessnessCount, Shelter
from app.models.housing import Parcel, SubsidisedHousing, TransitStop
from app.models.metric import TractMetric
from app.models.site import ModelRun, SiteCandidate

__all__ = [
    "Base",
    "BostonNeighbourhood",
    "Coc",
    "CocBedCount",
    "CocMunicipality",
    "County",
    "DataSource",
    "HomelessnessCount",
    "ModelRun",
    "Municipality",
    "NeighbourhoodTract",
    "Parcel",
    "Shelter",
    "SiteCandidate",
    "SubsidisedHousing",
    "Tract",
    "TractMetric",
    "TractMunicipality",
    "TransitStop",
    "ZipTract",
]
