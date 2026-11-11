import numpy as np
import pytest
from shapely.geometry import box

from app.services import rings


def test_geodesic_circle_radius_and_area() -> None:
    lon, lat = -71.0589, 42.3601  # Boston City Hall
    c = rings.geodesic_circle(lon, lat, 5000)
    cx, cy = rings.to_state_plane(lon, lat)
    assert c.area == pytest.approx(np.pi * 5000**2, rel=0.005)
    assert c.centroid.distance(c.centroid.__class__(cx, cy)) < 5


def test_shares_inside_crossing_and_outside() -> None:
    tg = rings.TractGeometry.build(
        ["a", "b", "c"],
        [box(-10, -10, 10, 10), box(0, -50, 100, 50), box(500, 500, 600, 600)],
    )
    circle = box(-20, -20, 20, 20)  # stands in for a circle
    idx, share = tg.shares(circle)
    got = dict(zip(tg.geoids[idx], share, strict=True))
    assert got["a"] == pytest.approx(1.0)
    assert got["b"] == pytest.approx(20 * 40 / (100 * 100))
    assert "c" not in got


def test_ring_totals_and_weighted_mean_skip_missing() -> None:
    idx = np.array([0, 1, 2])
    share = np.array([1.0, 0.5, 0.25])
    totals = rings.ring_totals(
        idx,
        share,
        {"pop": np.array([100.0, 200.0, np.nan]), "none": np.array([np.nan] * 3)},
    )
    assert totals["pop"] == pytest.approx(200.0)
    assert totals["none"] is None
    m = rings.weighted_mean(
        idx, share, np.array([10.0, 40.0, np.nan]), np.array([100.0, 200.0, 50.0])
    )
    assert m == pytest.approx((10 * 100 + 40 * 100) / 200)
