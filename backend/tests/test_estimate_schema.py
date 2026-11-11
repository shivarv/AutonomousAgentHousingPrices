import pytest
from pydantic import ValidationError

from app.schemas.estimate import HomelessFigure
from app.schemas.homelessness import OFFICIAL_LABEL


def test_estimate_and_official_labels() -> None:
    est = HomelessFigure.estimate(12.3, 2025, "ESTIMATE: ...")
    assert est.label == "estimate"
    assert est.method_url
    assert HomelessFigure.official(100, 2025).label == OFFICIAL_LABEL


def test_unknown_label_rejected() -> None:
    with pytest.raises(ValidationError):
        HomelessFigure(value=1.0, label="count", year=2025)  # type: ignore[arg-type]
