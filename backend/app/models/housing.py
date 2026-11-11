from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SubsidisedHousing(Base):
    """Subsidised housing property (LIHTC or HUD-assisted project)."""

    __tablename__ = "subsidised_housing"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    program: Mapped[str] = mapped_column(String(64), index=True)
    external_id: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    tract_geoid: Mapped[str | None] = mapped_column(ForeignKey("tracts.geoid"), index=True)
    total_units: Mapped[int | None] = mapped_column(Integer)
    assisted_units: Mapped[int | None] = mapped_column(Integer)
    year: Mapped[int | None] = mapped_column(SmallInteger)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class TransitStop(Base):
    __tablename__ = "transit_stops"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    agency: Mapped[str] = mapped_column(String(16), index=True)
    stop_id: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(16), index=True)  # subway, rail, bus, ferry
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    tract_geoid: Mapped[str | None] = mapped_column(ForeignKey("tracts.geoid"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class Parcel(Base):
    """Developable candidate parcel (screened in Phase 8), with simplified geometry."""

    __tablename__ = "parcels"

    loc_id: Mapped[str] = mapped_column(Text, primary_key=True)
    town_id: Mapped[int] = mapped_column(SmallInteger, index=True)
    municipality_geoid: Mapped[str | None] = mapped_column(
        ForeignKey("municipalities.geoid"), index=True
    )
    tract_geoid: Mapped[str | None] = mapped_column(ForeignKey("tracts.geoid"), index=True)
    use_code: Mapped[str] = mapped_column(String(8), index=True)
    lot_size_acres: Mapped[float] = mapped_column(Float)
    land_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    building_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    total_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    fiscal_year: Mapped[int | None] = mapped_column(SmallInteger)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    boundary: Mapped[dict[str, Any]] = mapped_column(JSONB)
    openspace_overlap: Mapped[float] = mapped_column(Float, default=0.0)
    wetland_overlap: Mapped[float] = mapped_column(Float, default=0.0)
    flood_overlap: Mapped[float] = mapped_column(Float, default=0.0)
    in_mbta3a_district: Mapped[bool] = mapped_column(Boolean, default=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
