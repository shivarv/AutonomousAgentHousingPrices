"""In-memory spatial index for the map services, built once per process from the database.

Holds tract polygons (MA State Plane) with their latest metric values as arrays, every area
level's polygons in an STRtree for point-in-polygon, neighbour lists, and point layers
(shelters, subsidised housing). Rebuilt only on process restart (data change = reload).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import shapely
from shapely.geometry import Point

from app.dao.geo_dao import GeoDao
from app.services import rings

LEVELS = ("tract", "neighbourhood", "municipality", "county", "coc")
NEIGHBOUR_TOLERANCE_M = 5.0
TRACT_METRICS = (
    "population",
    "homeless_estimate",
    "eli_renter_households",
    "eli_severely_burdened_renters",
    "units_affordable_available_eli",
    "affordable_gap_eli",
    "hud_assisted_units",
    "lihtc_low_income_units",
    "need_index",
)


@dataclass
class AreaLayer:
    level: str
    ids: list[str]
    names: list[str]
    geoms: np.ndarray
    boundaries: list[dict[str, Any]]
    tree: shapely.STRtree
    neighbours: list[list[str]] = field(default_factory=list)
    pos: dict[str, int] = field(default_factory=dict)

    @classmethod
    def build(cls, level: str, rows: list[dict[str, Any]]) -> AreaLayer:
        geoms = rings.geojson_to_state_plane([r["boundary"] for r in rows])
        shapely.prepare(geoms)
        tree = shapely.STRtree(geoms)
        ids = [str(r["id"]) for r in rows]
        layer = cls(
            level=level,
            ids=ids,
            names=[r["name"] for r in rows],
            geoms=geoms,
            boundaries=[r["boundary"] for r in rows],
            tree=tree,
            pos={a: i for i, a in enumerate(ids)},
        )
        buffered = shapely.buffer(geoms, NEIGHBOUR_TOLERANCE_M)
        left, right = tree.query(buffered, predicate="intersects")
        nb: list[list[str]] = [[] for _ in ids]
        for i, j in zip(left, right, strict=True):
            if i != j:
                nb[i].append(ids[j])
        layer.neighbours = [sorted(set(n)) for n in nb]
        return layer

    def at(self, x: float, y: float) -> int | None:
        hits = self.tree.query(Point(x, y), predicate="intersects")
        if len(hits) == 0:
            return None
        return int(min(hits))  # deterministic if boundaries touch exactly at the point


@dataclass
class GeoIndex:
    tracts: rings.TractGeometry
    tract_rows: list[dict[str, Any]]
    centroid_xy: np.ndarray
    metrics: dict[str, np.ndarray]
    metric_meta: dict[str, dict[str, Any]]
    layers: dict[str, AreaLayer]
    shelters: list[dict[str, Any]]
    shelter_xy: np.ndarray
    subsidised: list[dict[str, Any]]
    subsidised_xy: np.ndarray
    members: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]]
    official: dict[str, dict[str, Any]]

    @classmethod
    def build(cls, dao: GeoDao) -> GeoIndex:
        tract_rows = dao.tracts()
        geoids = [t["geoid"] for t in tract_rows]
        pos = {g: i for i, g in enumerate(geoids)}
        tg = rings.TractGeometry.build(
            geoids, rings.geojson_to_state_plane([t["boundary"] for t in tract_rows])
        )
        metrics = {m: np.full(len(geoids), np.nan) for m in TRACT_METRICS}
        meta: dict[str, dict[str, Any]] = {}
        for r in dao.latest_tract_metrics(TRACT_METRICS):
            if r["value"] is not None and r["tract_geoid"] in pos:
                metrics[r["metric"]][pos[r["tract_geoid"]]] = r["value"]
            meta.setdefault(
                r["metric"],
                {"year": r["year"], "source": r["source_key"], "method": r["method"]},
            )
        layers = {
            "tract": AreaLayer.build(
                "tract",
                [
                    {"id": t["geoid"], "name": t["name"], "boundary": t["boundary"]}
                    for t in tract_rows
                ],
            )
        }
        for level in LEVELS[1:]:
            layers[level] = AreaLayer.build(level, dao.areas(level))
        shelters = [r for r in dao.shelters() if r["lat"] is not None and r["lon"] is not None]
        subs = dao.subsidised()
        members = build_members(tract_rows, dao.town_weights(), layers)
        cx, cy = rings.to_state_plane_many(
            np.array([t["centroid_lon"] for t in tract_rows]),
            np.array([t["centroid_lat"] for t in tract_rows]),
        )
        return cls(
            tracts=tg,
            tract_rows=tract_rows,
            centroid_xy=np.column_stack([cx, cy]),
            metrics=metrics,
            metric_meta=meta,
            layers=layers,
            shelters=shelters,
            shelter_xy=_xy(shelters),
            subsidised=subs,
            subsidised_xy=_xy(subs),
            members=members,
            official=dao.latest_pit(),
        )


def build_members(
    tract_rows: list[dict[str, Any]],
    town_weights: list[dict[str, Any]],
    layers: dict[str, AreaLayer],
) -> dict[str, dict[str, tuple[np.ndarray, np.ndarray]]]:
    """level -> area id -> (tract indexes, weights). County, CoC and neighbourhood hold each
    tract once (the area with most of its land); towns use the tract's housing share in the
    town, so towns sum exactly to the state (same rules as the area_metrics aggregates)."""
    pos = {t["geoid"]: i for i, t in enumerate(tract_rows)}
    acc: dict[str, dict[str, list[tuple[int, float]]]] = {lvl: {} for lvl in LEVELS}
    for i, t in enumerate(tract_rows):
        acc["tract"].setdefault(t["geoid"], []).append((i, 1.0))
        acc["county"].setdefault(t["county_geoid"], []).append((i, 1.0))
        acc["coc"].setdefault(t["coc_number"], []).append((i, 1.0))
        if t["neighbourhood_id"] is not None:
            acc["neighbourhood"].setdefault(str(t["neighbourhood_id"]), []).append((i, 1.0))
    for w in town_weights:
        if w["tract_geoid"] in pos and w["housing_share"]:
            acc["municipality"].setdefault(w["municipality_geoid"], []).append(
                (pos[w["tract_geoid"]], float(w["housing_share"]))
            )
    out: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]] = {}
    for level, areas in acc.items():
        out[level] = {}
        for area_id in layers[level].ids:
            pairs = areas.get(area_id, [])
            out[level][area_id] = (
                np.array([p[0] for p in pairs], dtype=int),
                np.array([p[1] for p in pairs], dtype=float),
            )
    return out


def _xy(rows: list[dict[str, Any]]) -> np.ndarray:
    """State Plane coordinates of point rows (all rows have lat/lon: the DAO filters)."""
    if not rows:
        return np.zeros((0, 2))
    x, y = rings.to_state_plane_many(
        np.array([r["lon"] for r in rows]), np.array([r["lat"] for r in rows])
    )
    return np.column_stack([x, y])


_lock = threading.Lock()
_cache: dict[str, GeoIndex] = {}


def get_geo_index(dao: GeoDao, key: str) -> GeoIndex:
    """Process-wide index per database URL (tests use a different database)."""
    with _lock:
        if key not in _cache:
            _cache[key] = GeoIndex.build(dao)
        return _cache[key]
