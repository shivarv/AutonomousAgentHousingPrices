"""Ring (circle) statistics over census tracts, shared by site scoring and /api/area-stats.

A ring is a geodesic circle: buffered in an azimuthal-equidistant projection centred on the
point (distances from the centre are exact), then projected to Massachusetts State Plane.
Each tract contributes the share of its area that lies inside the circle; count metrics are
summed with those shares (assumes people and homes are spread evenly within a tract), and
the Need Index is the population-weighted mean of the overlapping tracts' indexes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

MA_CRS = "EPSG:26986"
QUAD_SEGS = 32
_TO_MA = Transformer.from_crs("EPSG:4326", MA_CRS, always_xy=True)


def geodesic_circle(lon: float, lat: float, radius_m: float) -> BaseGeometry:
    """Circle of ``radius_m`` metres around (lon, lat), returned in MA State Plane."""
    aeqd = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0 +ellps=GRS80 +units=m"
    to_ma = Transformer.from_crs(aeqd, MA_CRS, always_xy=True)
    circle = Point(0, 0).buffer(radius_m, quad_segs=QUAD_SEGS)
    return shapely.transform(
        circle, lambda xy: np.column_stack(to_ma.transform(xy[:, 0], xy[:, 1]))
    )


def to_state_plane(lon: float, lat: float) -> tuple[float, float]:
    return _TO_MA.transform(lon, lat)


def to_state_plane_many(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y = _TO_MA.transform(np.asarray(lon, float), np.asarray(lat, float))
    return np.asarray(x), np.asarray(y)


def geojson_to_state_plane(features: Sequence[dict]) -> np.ndarray:
    """WGS84 GeoJSON geometries -> valid shapely geometries in MA State Plane."""
    geoms = np.array([shape(f) for f in features], dtype=object)
    coords = shapely.get_coordinates(geoms)
    x, y = _TO_MA.transform(coords[:, 0], coords[:, 1])
    out = shapely.set_coordinates(geoms.copy(), np.column_stack([x, y]))
    return shapely.make_valid(out)


@dataclass
class TractGeometry:
    """Tract polygons in MA State Plane, in a fixed order (index i <-> geoids[i])."""

    geoids: np.ndarray
    geoms: np.ndarray
    areas: np.ndarray
    tree: shapely.STRtree

    @classmethod
    def build(cls, geoids: Sequence[str], geoms: Sequence[BaseGeometry]) -> TractGeometry:
        g = np.asarray(geoms, dtype=object)
        shapely.prepare(g)
        return cls(np.asarray(geoids), g, shapely.area(g), shapely.STRtree(g))

    def shares(self, circle: BaseGeometry) -> tuple[np.ndarray, np.ndarray]:
        """(tract indexes, share of each tract's area inside ``circle``), shares > 0 only."""
        idx = self.tree.query(circle, predicate="intersects")
        if len(idx) == 0:
            return idx, np.zeros(0)
        geoms = self.geoms[idx]
        inside = shapely.contains_properly(circle, geoms)
        share = np.ones(len(idx))
        cross = ~inside
        if cross.any():
            share[cross] = shapely.area(shapely.intersection(geoms[cross], circle)) / np.where(
                self.areas[idx][cross] > 0, self.areas[idx][cross], 1.0
            )
        keep = share > 0
        return idx[keep], np.clip(share[keep], 0.0, 1.0)


def ring_totals(
    idx: np.ndarray,
    share: np.ndarray,
    counts: dict[str, np.ndarray],
) -> dict[str, float | None]:
    """Share-weighted sums of tract count arrays (NaN tract values are skipped; None when no
    overlapping tract has a value)."""
    out: dict[str, float | None] = {}
    for name, values in counts.items():
        v = values[idx]
        ok = ~np.isnan(v)
        out[name] = float(np.sum(v[ok] * share[ok])) if ok.any() else None
    return out


def weighted_mean(
    idx: np.ndarray, share: np.ndarray, values: np.ndarray, weights: np.ndarray
) -> float | None:
    """Mean of tract ``values`` weighted by weight x share (tracts without a value skipped)."""
    v, w = values[idx], weights[idx] * share
    ok = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    if not ok.any():
        return None
    return float(np.sum(v[ok] * w[ok]) / np.sum(w[ok]))
