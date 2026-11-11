"""Geographic units: counties, municipalities, Continuums of Care, Boston neighbourhoods, tracts.

Boundaries are simplified GeoJSON geometries (WGS84) stored in jsonb (no PostGIS).
"""

from typing import Any

from sqlalchemy import BigInteger, Float, ForeignKey, Identity, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class County(Base):
    __tablename__ = "counties"

    geoid: Mapped[str] = mapped_column(String(5), primary_key=True)  # e.g. 25025
    name: Mapped[str] = mapped_column(Text)
    land_area_m2: Mapped[float] = mapped_column(Float)
    water_area_m2: Mapped[float] = mapped_column(Float)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    boundary: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class Municipality(Base):
    __tablename__ = "municipalities"

    geoid: Mapped[str] = mapped_column(String(10), primary_key=True)  # county subdivision GEOID
    name: Mapped[str] = mapped_column(Text, index=True)
    county_geoid: Mapped[str] = mapped_column(ForeignKey("counties.geoid"), index=True)
    land_area_m2: Mapped[float] = mapped_column(Float)
    water_area_m2: Mapped[float] = mapped_column(Float)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    boundary: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class Coc(Base):
    """HUD Continuum of Care (homelessness region)."""

    __tablename__ = "cocs"

    coc_number: Mapped[str] = mapped_column(String(8), primary_key=True)  # e.g. MA-500
    name: Mapped[str] = mapped_column(Text)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    boundary: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class CocMunicipality(Base):
    """Member municipalities of a CoC, with the share of the municipality's land in the CoC."""

    __tablename__ = "coc_municipalities"

    coc_number: Mapped[str] = mapped_column(ForeignKey("cocs.coc_number"), primary_key=True)
    municipality_geoid: Mapped[str] = mapped_column(
        ForeignKey("municipalities.geoid"), primary_key=True, index=True
    )
    area_share: Mapped[float] = mapped_column(Float)


class BostonNeighbourhood(Base):
    __tablename__ = "boston_neighbourhoods"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    boundary: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class NeighbourhoodTract(Base):
    """Tracts overlapping a Boston neighbourhood, with the share of the tract's area inside it."""

    __tablename__ = "neighbourhood_tracts"

    neighbourhood_id: Mapped[int] = mapped_column(
        ForeignKey("boston_neighbourhoods.id"), primary_key=True
    )
    tract_geoid: Mapped[str] = mapped_column(
        ForeignKey("tracts.geoid"), primary_key=True, index=True
    )
    area_share: Mapped[float] = mapped_column(Float)


class Tract(Base):
    __tablename__ = "tracts"

    geoid: Mapped[str] = mapped_column(String(11), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    county_geoid: Mapped[str] = mapped_column(ForeignKey("counties.geoid"), index=True)
    # municipality / CoC / neighbourhood holding the largest share of the tract's area
    municipality_geoid: Mapped[str] = mapped_column(ForeignKey("municipalities.geoid"), index=True)
    coc_number: Mapped[str] = mapped_column(ForeignKey("cocs.coc_number"), index=True)
    neighbourhood_id: Mapped[int | None] = mapped_column(
        ForeignKey("boston_neighbourhoods.id"), index=True
    )
    land_area_m2: Mapped[float] = mapped_column(Float)
    water_area_m2: Mapped[float] = mapped_column(Float)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    boundary: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class TractMunicipality(Base):
    """Tract x municipality overlap (area share of the tract), for tracts crossing town lines."""

    __tablename__ = "tract_municipalities"

    tract_geoid: Mapped[str] = mapped_column(ForeignKey("tracts.geoid"), primary_key=True)
    municipality_geoid: Mapped[str] = mapped_column(
        ForeignKey("municipalities.geoid"), primary_key=True, index=True
    )
    area_share: Mapped[float] = mapped_column(Float)


class ZipTract(Base):
    """ZCTA -> tract weights by residential share (2020 block housing units)."""

    __tablename__ = "zip_tracts"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    zcta: Mapped[str] = mapped_column(String(5), index=True)
    tract_geoid: Mapped[str] = mapped_column(ForeignKey("tracts.geoid"), index=True)
    res_share_of_zip: Mapped[float] = mapped_column(Float)  # share of ZIP housing units in tract
    res_share_of_tract: Mapped[float] = mapped_column(Float)  # share of tract housing in ZIP
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
