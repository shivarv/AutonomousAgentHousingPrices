"""Transfer object for modelled values. Every API response that carries a tract (or summed
tract) homeless figure uses ``HomelessFigure`` so the label "estimate" and its method always
travel with the number; only CoC-level figures may say "official CoC count"."""

from typing import Literal

from pydantic import BaseModel

ESTIMATE_LABEL = "estimate"
OFFICIAL_LABEL = "official CoC count"
ESTIMATE_METHOD_URL = "/methodology#homeless-estimate"


class HomelessFigure(BaseModel):
    value: float | None
    label: Literal["estimate", "official CoC count"]
    year: int | None
    method: str | None = None
    method_url: str = ESTIMATE_METHOD_URL

    @classmethod
    def estimate(
        cls, value: float | None, year: int | None, method: str | None
    ) -> "HomelessFigure":
        return cls(value=value, label=ESTIMATE_LABEL, year=year, method=method)

    @classmethod
    def official(cls, value: float | None, year: int | None) -> "HomelessFigure":
        return cls(value=value, label=OFFICIAL_LABEL, year=year, method="HUD Point-in-Time count")
