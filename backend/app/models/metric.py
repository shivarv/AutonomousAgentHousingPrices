from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Identity,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TractMetric(Base):
    """One value of one metric for one tract and year. Every row is traceable to a source.

    ``is_estimate`` marks modelled values (e.g. ``homeless_estimate``), which must carry a
    ``method``. ``flag`` records imputation or data-quality notes (never silent fills).
    """

    __tablename__ = "tract_metrics"
    __table_args__ = (UniqueConstraint("tract_geoid", "metric", "year"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    tract_geoid: Mapped[str] = mapped_column(ForeignKey("tracts.geoid"), index=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    year: Mapped[int] = mapped_column(SmallInteger, index=True)
    value: Mapped[float | None] = mapped_column(Float)
    moe: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), index=True)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=False)
    method: Mapped[str | None] = mapped_column(Text)
    flag: Mapped[str | None] = mapped_column(Text)
