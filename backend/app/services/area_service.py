"""Map statistics around a point (POST /api/area-stats) and for areas.

Ring totals sum tract values weighted by the share of each tract's area inside a geodesic
circle (app.services.rings). Homeless numbers below CoC level are sums of modelled tract
estimates and always travel as HomelessFigure(label="estimate").
"""

from __future__ import annotations

from typing import Any

import numpy as np
import shapely

from app.core.exceptions import NotFoundError, OutsideCoverageError, ValidationError
from app.schemas.area import (
    AreaAt,
    AreaFigures,
    AreaRef,
    AreaStatsResponse,
    NearbyShelter,
    NearbyTract,
    RingStats,
)
from app.schemas.estimate import HomelessFigure
from app.services import rings
from app.services.geo_index import LEVELS, GeoIndex

MIN_RADIUS_KM = 0.5
MAX_RADIUS_KM = 80.0
RING_HOMELESS_METHOD = (
    "sum of modelled tract estimates (CoC Point-in-Time count allocated to tracts), weighted "
    "by the share of each tract's area inside the ring; not a count"
)
BEDS_NOTE = (
    "Shelter bed counts are published only per Continuum of Care (HUD Housing Inventory "
    "Count); shelter locations come from OpenStreetMap and carry no bed counts."
)
SPREAD_NOTE = (
    "Tract figures are assumed to be spread evenly over each tract's area when a ring cuts "
    "through a tract."
)
AREA_HOMELESS_METHOD = (
    "sum of modelled tract estimates (CoC Point-in-Time count allocated to tracts); towns get "
    "each tract's housing-unit share; not a count"
)
COC_NOTE = (
    "Official HUD Point-in-Time count for the whole Continuum of Care; the tract estimates "
    "inside it sum to this count. Shelter beds are the CoC's HIC year-round beds."
)
AREA_NOTE = (
    "Homeless figures below CoC level are modelled estimates; official counts exist only "
    "per Continuum of Care."
)
COUNT_KEYS = (
    "population",
    "homeless_estimate",
    "eli_severely_burdened_renters",
    "eli_renter_households",
    "units_affordable_available_eli",
    "affordable_gap_eli",
    "hud_assisted_units",
    "lihtc_low_income_units",
)


def gap_status(gap: float | None) -> str | None:
    if gap is None:
        return None
    if gap >= 0.5:
        return "shortage"
    if gap <= -0.5:
        return "surplus"
    return "balanced"


def _r(v: float | None, nd: int = 0) -> float | None:
    return None if v is None else round(float(v), nd)


def beds_total(shelters: list[dict[str, Any]]) -> int | None:
    beds = [s["beds"] for s in shelters if s["beds"] is not None]
    return sum(beds) if beds else None


class AreaService:
    def __init__(self, index: GeoIndex) -> None:
        self.index = index

    # ---------------------------------------------------------------- helpers
    def locate(self, lat: float, lon: float) -> tuple[float, float]:
        """State Plane x/y of a point inside Massachusetts, else OutsideCoverageError."""
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValidationError("lat must be -90..90 and lon -180..180")
        x, y = rings.to_state_plane(lon, lat)
        if self.index.layers["county"].at(x, y) is None:
            raise OutsideCoverageError(
                "The point is outside Massachusetts; statistics cover Massachusetts only."
            )
        return x, y

    def shelters_in(self, geom: Any) -> list[int]:
        xy = self.index.shelter_xy
        if len(xy) == 0:
            return []
        return [int(i) for i in np.flatnonzero(shapely.contains_xy(geom, xy[:, 0], xy[:, 1]))]

    def figures(
        self,
        idx: np.ndarray,
        share: np.ndarray,
        shelter_ids: list[int],
        homeless: HomelessFigure | None = None,
    ) -> AreaFigures:
        m = self.index.metrics
        tot = rings.ring_totals(idx, share, {k: m[k] for k in COUNT_KEYS})
        if homeless is None:
            meta = self.index.metric_meta.get("homeless_estimate", {})
            homeless = HomelessFigure.estimate(
                _r(tot["homeless_estimate"], 1), meta.get("year"), RING_HOMELESS_METHOD
            )
        hud, lihtc = tot["hud_assisted_units"], tot["lihtc_low_income_units"]
        shelters = [self.index.shelters[i] for i in shelter_ids]
        return AreaFigures(
            population=_r(tot["population"]),
            homeless=homeless,
            at_risk_households=_r(tot["eli_severely_burdened_renters"]),
            eli_renter_households=_r(tot["eli_renter_households"]),
            affordable_units_available=_r(tot["units_affordable_available_eli"]),
            affordable_gap=_r(tot["affordable_gap_eli"]),
            gap_status=gap_status(tot["affordable_gap_eli"]),  # type: ignore[arg-type]
            subsidised_units=None
            if hud is None and lihtc is None
            else _r((hud or 0) + (lihtc or 0)),
            need_index=_r(rings.weighted_mean(idx, share, m["need_index"], m["population"]), 1),
            shelters=len(shelters),
            shelter_beds=beds_total(shelters),
            tract_count=int(len(idx)),
        )

    def sources(self) -> dict[str, dict[str, Any]]:
        keys = (*COUNT_KEYS, "need_index")
        return {
            k: {kk: v for kk, v in self.index.metric_meta[k].items() if kk != "method"}
            for k in keys
            if k in self.index.metric_meta
        }

    # ---------------------------------------------------------------- rings
    def ring_stats(self, lat: float, lon: float, radii_km: list[float]) -> AreaStatsResponse:
        if not 1 <= len(radii_km) <= 3:
            raise ValidationError("give 1 to 3 radii")
        for r in radii_km:
            if not MIN_RADIUS_KM <= r <= MAX_RADIUS_KM:
                raise ValidationError(
                    f"radius {r} km is outside the allowed range "
                    f"{MIN_RADIUS_KM:g}-{MAX_RADIUS_KM:g} km"
                )
        self.locate(lat, lon)
        out: list[RingStats] = []
        circle = None
        idx = np.zeros(0, dtype=int)
        for r in sorted(radii_km):
            circle = rings.geodesic_circle(lon, lat, r * 1000)
            idx, share = self.index.tracts.shares(circle)
            fig = self.figures(idx, share, self.shelters_in(circle))
            out.append(RingStats(radius_km=r, **fig.model_dump()))
        assert circle is not None
        return AreaStatsResponse(
            lat=lat,
            lon=lon,
            rings=out,
            nearby_tracts=self.nearby_tracts(circle, idx),
            nearby_shelters=[
                NearbyShelter(**self.index.shelters[i]) for i in self.shelters_in(circle)
            ],
            sources=self.sources(),
            notes=[BEDS_NOTE, SPREAD_NOTE],
        )

    def nearby_tracts(self, circle: Any, idx: np.ndarray) -> list[NearbyTract]:
        """Tracts whose centroid lies inside the largest ring, with their estimate."""
        if len(idx) == 0:
            return []
        cx = self.index.centroid_xy[idx]
        inside = idx[shapely.contains_xy(circle, cx[:, 0], cx[:, 1])]
        meta = self.index.metric_meta.get("homeless_estimate", {})
        est = self.index.metrics["homeless_estimate"]
        out = []
        for i in inside:
            t = self.index.tract_rows[i]
            v = est[i]
            out.append(
                NearbyTract(
                    geoid=t["geoid"],
                    lat=t["centroid_lat"],
                    lon=t["centroid_lon"],
                    homeless=HomelessFigure.estimate(
                        None if np.isnan(v) else round(float(v), 1),
                        meta.get("year"),
                        meta.get("method"),
                    ),
                )
            )
        return out

    # ---------------------------------------------------------------- areas
    def _check_level(self, level: str) -> None:
        if level not in LEVELS:
            raise ValidationError(f"level must be one of {', '.join(LEVELS)}")

    def area_figures(self, level: str, area_ids: list[str]) -> tuple[AreaFigures, HomelessFigure]:
        """Combined figures for areas of one level (weights summed per tract) and the summed
        tract estimate. At CoC level the homeless figure and beds are the official ones."""
        members = self.index.members[level]
        layer = self.index.layers[level]
        weights: dict[int, float] = {}
        shelter_ids: set[int] = set()
        for a in area_ids:
            if a not in members:
                raise NotFoundError(f"no {level} with id '{a}'")
            for i, w in zip(*members[a], strict=True):
                weights[int(i)] = weights.get(int(i), 0.0) + float(w)
            shelter_ids.update(self.shelters_in(layer.geoms[layer.pos[a]]))
        idx = np.array(sorted(weights), dtype=int)
        share = np.array([weights[i] for i in idx], dtype=float)
        fig = self.figures(idx, share, sorted(shelter_ids))
        meta = self.index.metric_meta.get("homeless_estimate", {})
        est = HomelessFigure.estimate(fig.homeless.value, meta.get("year"), AREA_HOMELESS_METHOD)
        if level == "coc":
            off = [self.index.official.get(a) for a in area_ids]
            years = {o["year"] for o in off if o}
            if all(off) and len(years) == 1:
                fig.homeless = HomelessFigure.official(
                    float(sum(o["total"] for o in off)), years.pop()
                )
                beds = [o["beds"] for o in off]
                fig.shelter_beds = None if any(b is None for b in beds) else int(sum(beds))
            else:
                fig.homeless = est
        else:
            fig.homeless = est
        return fig, est

    def area_at(self, lat: float, lon: float, level: str) -> AreaAt:
        self._check_level(level)
        x, y = self.locate(lat, lon)
        layer = self.index.layers[level]
        i = layer.at(x, y)
        if i is None:
            if level == "neighbourhood":
                raise OutsideCoverageError(
                    "Boston neighbourhoods cover the City of Boston only; this point is "
                    "outside Boston. Choose another boundary level."
                )
            raise OutsideCoverageError(f"no {level} boundary contains this point")
        area_id = layer.ids[i]
        fig, est = self.area_figures(level, [area_id])
        return AreaAt(
            level=level,  # type: ignore[arg-type]
            id=area_id,
            name=layer.names[i],
            boundary=layer.boundaries[i],
            neighbours=[AreaRef(id=n, name=layer.names[layer.pos[n]]) for n in layer.neighbours[i]],
            figures=fig,
            homeless_estimate_sum=est,
            homeless_basis="official CoC count" if level == "coc" else "sum of tract estimates",
            note=COC_NOTE if level == "coc" else AREA_NOTE,
        )
