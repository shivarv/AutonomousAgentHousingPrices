import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from pipeline.geo import MA_CRS
from pipeline.sites import screen


def test_developable_records_codes_and_sums() -> None:
    assess = pd.DataFrame(
        {
            "loc_id": ["A", "A", "B", "C", None],
            "use_code": ["1300", "130", "132", "3910", "130"],
            "land_val": [100.0, 50.0, 10.0, 20.0, 5.0],
            "bldg_val": [0.0, 0.0, 0.0, 0.0, 0.0],
            "total_val": [100.0, 50.0, 10.0, 20.0, 5.0],
            "fy": [2026, 2026, 2026, 2025, 2026],
            "lot_size_acres": [1.0, 1.0, 2.0, 3.0, 1.0],
        }
    )
    r = screen.developable_records(assess).set_index("loc_id")
    assert set(r.index) == {"A", "C"}  # 132 is undevelopable; no loc_id dropped
    assert r.loc["A", "land_val"] == 150.0
    assert r.loc["A", "use_code"] == "1300"  # record with the largest land value
    assert r.loc["C", "use3"] == "391"


def test_screen_lots_min_size_and_poly_type() -> None:
    records = pd.DataFrame({"loc_id": ["A", "B", "C"], "use_code": ["130"] * 3})
    acre = screen.SQM_PER_ACRE
    points = pd.DataFrame(
        {
            "loc_id": ["A", "B", "C"],
            "poly_type": ["FEE", "FEE", "ROW"],
            "area_m2": [acre, 0.4 * acre, 5 * acre],
            "tract_geoid": ["t"] * 3,
        }
    )
    out = screen.screen_lots(records, points)
    assert out.loc_id.tolist() == ["A"]
    assert out.lot_size_acres.iloc[0] == pytest.approx(1.0)


def test_overlap_shares_union_not_double_counted() -> None:
    parcels = gpd.GeoDataFrame(
        {"loc_id": ["P", "Q"]}, geometry=[box(0, 0, 100, 100), box(500, 500, 600, 600)], crs=MA_CRS
    )
    layers = {
        "openspace": gpd.GeoDataFrame(geometry=[box(0, 0, 60, 100)], crs=MA_CRS),
        "wetland": gpd.GeoDataFrame(geometry=[box(40, 0, 100, 100)], crs=MA_CRS),
        "flood": gpd.GeoDataFrame(geometry=[box(1000, 1000, 1100, 1100)], crs=MA_CRS),
    }
    s = screen.overlap_shares(parcels, layers).set_index("loc_id")
    assert s.loc["P", "openspace_overlap"] == pytest.approx(0.6)
    assert s.loc["P", "wetland_overlap"] == pytest.approx(0.6)
    assert s.loc["P", "flood_overlap"] == 0.0
    assert s.loc["P", "constrained_share"] == pytest.approx(1.0)  # union, not 1.2
    assert s.loc["Q", "constrained_share"] == 0.0
