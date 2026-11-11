from sqlalchemy import (
    BigInteger,
    Float,
    ForeignKey,
    Identity,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class HomelessnessCount(Base):
    """Official HUD Point-in-Time count for one CoC and year (the only exact figures)."""

    __tablename__ = "homelessness_counts"
    __table_args__ = (UniqueConstraint("coc_number", "year"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    coc_number: Mapped[str] = mapped_column(ForeignKey("cocs.coc_number"), index=True)
    year: Mapped[int] = mapped_column(SmallInteger, index=True)
    sheltered: Mapped[int | None] = mapped_column(Integer)
    unsheltered: Mapped[int | None] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class CocBedCount(Base):
    """HUD Housing Inventory Count: year-round beds per CoC and year."""

    __tablename__ = "coc_bed_counts"
    __table_args__ = (UniqueConstraint("coc_number", "year"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    coc_number: Mapped[str] = mapped_column(ForeignKey("cocs.coc_number"), index=True)
    year: Mapped[int] = mapped_column(SmallInteger, index=True)
    emergency_shelter_beds: Mapped[int | None] = mapped_column(Integer)
    transitional_beds: Mapped[int | None] = mapped_column(Integer)
    safe_haven_beds: Mapped[int | None] = mapped_column(Integer)
    total_year_round_beds: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)


class Shelter(Base):
    """Public shelter location. Domestic-violence shelters are never stored."""

    __tablename__ = "shelters"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    external_id: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    shelter_type: Mapped[str] = mapped_column(Text)
    beds: Mapped[int | None] = mapped_column(Integer)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    tract_geoid: Mapped[str | None] = mapped_column(ForeignKey("tracts.geoid"), index=True)
    coc_number: Mapped[str | None] = mapped_column(ForeignKey("cocs.coc_number"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
