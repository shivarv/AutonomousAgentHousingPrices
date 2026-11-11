"""Shared geometry helpers. Areas and overlaps are computed in Massachusetts State Plane
(EPSG:26986, metres); stored boundaries are simplified WGS84 GeoJSON."""

from __future__ import annotations

import json
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

MA_CRS = "EPSG:26986"
WGS84 = "EPSG:4326"


def to_geojson(geom: BaseGeometry, precision: int = 5) -> dict[str, Any]:
    """GeoJSON dict with coordinates rounded to ``precision`` decimals (~1 m at 5)."""
    text = json.dumps(mapping(geom))
    data = json.loads(text, parse_float=lambda v: round(float(v), precision))
    return data


def simplified_geojson(gdf: gpd.GeoDataFrame, tolerance_m: float) -> pd.Series:
    """Simplify in metres (gdf must be in MA_CRS), then convert to WGS84 GeoJSON dicts."""
    simple = gdf.geometry.simplify(tolerance_m, preserve_topology=True)
    simple = gpd.GeoSeries(simple, crs=gdf.crs).to_crs(WGS84)
    return simple.apply(to_geojson)


def centroids_wgs84(gdf: gpd.GeoDataFrame) -> tuple[pd.Series, pd.Series]:
    """Representative interior point (always inside the polygon) as lat/lon."""
    pts = gpd.GeoSeries(gdf.geometry.representative_point(), crs=gdf.crs).to_crs(WGS84)
    return pts.y.round(6), pts.x.round(6)


def overlay_shares(
    left: gpd.GeoDataFrame,
    left_key: str,
    right: gpd.GeoDataFrame,
    right_key: str,
) -> pd.DataFrame:
    """Share of each left polygon's area that falls in each right polygon (both in MA_CRS)."""
    l_area = left.geometry.area.rename("left_area")
    inter = gpd.overlay(
        left[[left_key, "geometry"]],
        right[[right_key, "geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
    inter["area"] = inter.geometry.area
    inter = inter.merge(
        pd.DataFrame({left_key: left[left_key].values, "left_area": l_area.values}), on=left_key
    )
    inter["share"] = inter["area"] / inter["left_area"]
    return (
        inter[[left_key, right_key, "share"]].groupby([left_key, right_key], as_index=False).sum()
    )
