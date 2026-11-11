"""A number with its provenance: every figure the API returns carries year and source."""

from typing import Any

from pydantic import BaseModel


class MetricValue(BaseModel):
    value: float | None
    year: int | None
    source: str | None
    is_estimate: bool = False
    label: str | None = None  # "estimate" for modelled values
    method: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> "MetricValue":
        return cls(
            value=row.value,
            year=row.year,
            source=row.source_key,
            is_estimate=bool(row.is_estimate),
            label="estimate" if row.is_estimate else None,
            method=row.method,
        )
