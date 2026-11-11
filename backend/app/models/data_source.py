from datetime import date

from sqlalchemy import BigInteger, Date, Identity, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DataSource(Base):
    """One downloaded dataset (one line of DATA_SOURCES.md). Metric rows reference it."""

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    download_date: Mapped[date] = mapped_column(Date)
    licence: Mapped[str] = mapped_column(Text)
    geography: Mapped[str] = mapped_column(Text)
    years: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text)
    columns_used: Mapped[str] = mapped_column(Text)
