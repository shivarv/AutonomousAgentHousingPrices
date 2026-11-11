"""Housing Need Index components per tract (raw values and 0-1 scores).

Every component is oriented so that a higher value means more need, then scaled to 0-1 by its
statewide percentile rank among tracts that have a value: score = (rank - 1) / (n - 1), ties
share their average rank. Percentile scaling is robust to the long tails of these ratios
(e.g. small-denominator tracts) and puts every component on the same footing. Missing raw
values stay missing (never filled); the index step handles them.
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import pandas as pd

from pipeline.clean.metrics_common import safe_ratio
from pipeline.geo import MA_CRS


@dataclass(frozen=True)
class Component:
    key: str  # raw metric name
    label: str
    source_key: str
    year: int
    method: str


COMPONENTS: tuple[Component, ...] = (
    Component(
        "affordable_gap_per_eli_renter",
        "Affordable gap per ELI renter household",
        "hud_chas",
        2022,
        "affordable_gap_eli / eli_renter_households (HUD CHAS 2018-2022); NULL if no ELI renters",
    ),
    Component(
        "severe_rent_burden_share",
        "Severe rent burden share",
        "acs5",
        2024,
        "renter households paying >= 50% of income for rent / renters with computed burden "
        "(ACS 2020-2024)",
    ),
    Component(
        "eviction_filing_rate",
        "Eviction filing rate",
        "eviction_lab",
        2016,
        "mean annual eviction filings 2014-2016 (Eviction Lab) / renter households (ACS)",
    ),
    Component("poverty_rate", "Poverty rate", "acs5", 2024, "ACS 2020-2024 poverty rate"),
    Component(
        "overcrowding_rate",
        "Overcrowding rate",
        "acs5",
        2024,
        "occupied units with > 1 person per room (ACS 2020-2024)",
    ),
    Component(
        "zori_growth_5yr",
        "5-year rent growth",
        "zillow_zori",
        2026,
        "Zillow ZORI 5-year growth, ZIP values weighted to tracts by housing units",
    ),
    Component(
        "homeless_estimate_per_1000",
        "Homeless estimate per 1,000 residents (estimate)",
        "hud_pit",
        2025,
        "ESTIMATE: homeless_estimate (PIT 2025 allocated within CoC) / ACS population x 1000; "
        "NULL if population is 0",
    ),
    Component(
        "distance_to_service_km",
        "Distance to nearest shelter or subsidised housing",
        "hud_psh",
        2025,
        "straight-line km from the tract's interior point to the nearest shelter (OSM) or "
        "subsidised housing development (HUD Picture of Subsidized Households 2025, HUD LIHTC); "
        "farther = less access = more need",
    ),
)
COMPONENT_KEYS = [c.key for c in COMPONENTS]


def percentile_score(values: pd.Series) -> pd.Series:
    """0-1 percentile score; NaN stays NaN. A single valid value scores 0.5."""
    valid = values.dropna()
    out = pd.Series(float("nan"), index=values.index)
    if len(valid) == 0:
        return out
    if len(valid) == 1:
        out[valid.index] = 0.5
        return out
    ranks = valid.rank(method="average")
    out[valid.index] = (ranks - 1) / (len(valid) - 1)
    return out


def nearest_distance_km(
    tracts: pd.DataFrame, points: pd.DataFrame, lat: str = "lat", lon: str = "lon"
) -> pd.Series:
    """Planar (MA State Plane) distance from each tract interior point to the nearest point."""
    t = gpd.GeoDataFrame(
        {"geoid": tracts.geoid.values},
        geometry=gpd.points_from_xy(tracts.centroid_lon, tracts.centroid_lat),
        crs="EPSG:4326",
    ).to_crs(MA_CRS)
    p = points.dropna(subset=[lat, lon])
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(p[lon], p[lat]), crs="EPSG:4326").to_crs(
        MA_CRS
    )
    j = gpd.sjoin_nearest(t, pts, how="left", distance_col="d")
    j = j[~j.index.duplicated()]
    return pd.Series(j.d.values / 1000.0, index=tracts.geoid.values)


def raw_components(
    metrics: pd.DataFrame, tracts: pd.DataFrame, service_points: pd.DataFrame
) -> pd.DataFrame:
    """metrics: long tract metrics (tract_geoid, metric, value). Returns a frame indexed by
    tract geoid with one column per component (raw values, higher = more need)."""
    wide = metrics.pivot_table(
        index="tract_geoid", columns="metric", values="value", aggfunc="first"
    ).reindex(tracts.geoid)
    out = pd.DataFrame(index=tracts.geoid.values)
    out.index.name = "geoid"
    out["affordable_gap_per_eli_renter"] = safe_ratio(
        wide.affordable_gap_eli, wide.eli_renter_households
    ).values
    for key in (
        "severe_rent_burden_share",
        "eviction_filing_rate",
        "poverty_rate",
        "overcrowding_rate",
        "zori_growth_5yr",
    ):
        out[key] = wide[key].values if key in wide else float("nan")
    out["homeless_estimate_per_1000"] = (
        1000 * safe_ratio(wide.homeless_estimate, wide.population)
    ).values
    out["distance_to_service_km"] = nearest_distance_km(tracts, service_points).values
    return out[COMPONENT_KEYS]


def scores(raw: pd.DataFrame) -> pd.DataFrame:
    return raw.apply(percentile_score)
