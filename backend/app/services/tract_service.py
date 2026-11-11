"""Tract layer for the map (GeoJSON) and tract detail panels."""

from __future__ import annotations

import json
import threading
from typing import Any

from app.core.exceptions import NotFoundError
from app.dao.tract_dao import TractDao
from app.schemas.estimate import HomelessFigure
from app.schemas.metric import MetricValue
from app.schemas.tract import MetricInfo, MunicipalityShare, TractDetail

# properties drawn on the map (latest year of each)
MAP_METRICS = (
    "need_index",
    "population",
    "homeless_estimate",
    "eli_renter_households",
    "eli_severely_burdened_renters",
    "units_affordable_available_eli",
    "affordable_gap_eli",
    "affordable_units_per_100_eli",
    "poverty_rate",
    "vacancy_rate",
    "land_value_per_sqft",
)
ROUND = 3

_cache: dict[tuple[str, str | None, str | None], bytes] = {}
_lock = threading.Lock()


def _round(v: float | None) -> float | None:
    return None if v is None else round(float(v), ROUND)


class TractService:
    def __init__(self, dao: TractDao, cache_key: str) -> None:
        self.dao = dao
        self.cache_key = cache_key

    def geojson(self, county: str | None, municipality: str | None) -> bytes:
        """Serialised FeatureCollection, cached per filter for the life of the process."""
        key = (self.cache_key, county, municipality)
        with _lock:
            if key not in _cache:
                _cache[key] = json.dumps(
                    self._collection(county, municipality), separators=(",", ":")
                ).encode()
            return _cache[key]

    def _collection(self, county: str | None, municipality: str | None) -> dict[str, Any]:
        tracts = self.dao.tracts(county=county, municipality=municipality)
        if not tracts and (county or municipality):
            raise NotFoundError("no tracts match this filter")
        values: dict[str, dict[str, float | None]] = {}
        info: dict[str, MetricInfo] = {}
        latest: dict[tuple[str, str], int] = {}
        for r in self.dao.metric_rows(MAP_METRICS):
            k = (r.tract_geoid, r.metric)
            if k in latest and latest[k] >= r.year:
                continue
            latest[k] = r.year
            values.setdefault(r.tract_geoid, {})[r.metric] = _round(r.value)
            cur = info.get(r.metric)
            if cur is None or (cur.year or 0) < r.year:
                info[r.metric] = MetricInfo(
                    year=r.year,
                    source=r.source_key,
                    label="estimate" if r.is_estimate else None,
                )
        features = []
        for t in tracts:
            props = {
                "name": t.name,
                "county": t.county_name,
                "municipality": t.municipality_name,
                "coc_number": t.coc_number,
                "neighbourhood": t.neighbourhood_name,
                "centroid_lat": t.centroid_lat,
                "centroid_lon": t.centroid_lon,
                **{m: values.get(t.geoid, {}).get(m) for m in MAP_METRICS},
                "homeless_label": "estimate",
            }
            features.append(
                {"type": "Feature", "id": t.geoid, "geometry": t.boundary, "properties": props}
            )
        return {
            "type": "FeatureCollection",
            "features": features,
            "metrics": {k: v.model_dump() for k, v in info.items()},
        }

    def detail(self, geoid: str) -> TractDetail:
        t = self.dao.tract(geoid)
        if t is None:
            raise NotFoundError(f"no tract '{geoid}'")
        metrics: dict[str, MetricValue] = {}
        flags: dict[str, str] = {}
        for r in sorted(self.dao.metric_rows(geoid=geoid), key=lambda r: r.year):
            metrics[r.metric] = MetricValue.from_row(r)
            if r.flag:
                flags[r.metric] = r.flag
        est = metrics.get("homeless_estimate")
        homeless = HomelessFigure.estimate(
            None if est is None or est.value is None else round(est.value, 1),
            est.year if est else None,
            est.method if est else None,
        )
        return TractDetail(
            geoid=t.geoid,
            name=t.name,
            county_geoid=t.county_geoid,
            county_name=t.county_name,
            municipality_geoid=t.municipality_geoid,
            municipality_name=t.municipality_name,
            municipalities=[
                MunicipalityShare(
                    geoid=m.municipality_geoid,
                    name=m.name,
                    area_share=m.area_share,
                    housing_share=m.housing_share,
                )
                for m in self.dao.municipality_shares(geoid)
            ],
            coc_number=t.coc_number,
            coc_name=t.coc_name,
            neighbourhood_id=t.neighbourhood_id,
            neighbourhood_name=t.neighbourhood_name,
            centroid_lat=t.centroid_lat,
            centroid_lon=t.centroid_lon,
            land_area_km2=round(t.land_area_m2 / 1e6, 3),
            boundary=t.boundary,
            homeless=homeless,
            metrics=metrics,
            flags=flags,
        )
