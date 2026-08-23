"""District loading, schema validation, and demo fallback."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from riabita.data import loader

VALID_FEATURE = {
    "type": "Feature",
    "id": "testaccio",
    "properties": {"nome": "Testaccio", "M0": 50, "C0": 70, "T0": 40, "S0": 60},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[12.47, 41.87], [12.48, 41.87], [12.48, 41.88], [12.47, 41.87]]],
    },
}


def write(tmp_path: Path, payload: object, name: str = "districts.geojson") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def collection(*features: object) -> dict[str, object]:
    return {"type": "FeatureCollection", "features": list(features)}


# --- Demo dataset -----------------------------------------------------------


def test_demo_dataset_loads_ten_districts() -> None:
    catalog = loader.load_districts(None)
    assert catalog.used_fallback is True
    assert len(catalog.districts) == 10
    assert all(d.is_demo for d in catalog.districts)


def test_demo_dataset_matches_the_documented_san_lorenzo_baseline() -> None:
    catalog = loader.load_districts(None)
    district = catalog.get("san-lorenzo")
    assert district is not None
    assert district.baseline.as_array().tolist() == [55.0, 40.0, 80.0, 35.0]


def test_demo_values_are_all_within_range() -> None:
    for district in loader.load_districts(None).districts:
        assert all(0 <= v <= 100 for v in district.baseline.as_array())


# --- External files ---------------------------------------------------------


def test_valid_file_is_used_without_fallback(tmp_path: Path) -> None:
    path = write(tmp_path, collection(VALID_FEATURE))
    catalog = loader.load_districts(path)
    assert catalog.used_fallback is False
    assert catalog.names == ("Testaccio",)
    assert catalog.districts[0].is_demo is False


def test_missing_file_falls_back_to_demo(tmp_path: Path) -> None:
    catalog = loader.load_districts(tmp_path / "absent.geojson")
    assert catalog.used_fallback is True
    assert catalog.warnings


def test_malformed_json_falls_back_to_demo(tmp_path: Path) -> None:
    path = tmp_path / "broken.geojson"
    path.write_text("{not json", encoding="utf-8")
    catalog = loader.load_districts(path)
    assert catalog.used_fallback is True
    assert any("valid JSON" in w for w in catalog.warnings)


def test_file_without_features_falls_back(tmp_path: Path) -> None:
    path = write(tmp_path, {"type": "FeatureCollection"})
    assert loader.load_districts(path).used_fallback is True


def test_empty_feature_list_falls_back(tmp_path: Path) -> None:
    path = write(tmp_path, collection())
    catalog = loader.load_districts(path)
    assert catalog.used_fallback is True


# --- Per-feature validation -------------------------------------------------


def test_feature_missing_a_value_is_dropped(tmp_path: Path) -> None:
    broken = {
        "type": "Feature",
        "properties": {"nome": "Incomplete", "C0": 1, "T0": 1, "S0": 1},
    }
    path = write(tmp_path, collection(VALID_FEATURE, broken))
    catalog = loader.load_districts(path)
    assert catalog.names == ("Testaccio",)
    assert any("M0" in w for w in catalog.warnings)


def test_out_of_range_value_is_dropped(tmp_path: Path) -> None:
    broken = {
        "type": "Feature",
        "properties": {"nome": "TooHot", "M0": 10, "C0": 10, "T0": 120, "S0": 10},
    }
    path = write(tmp_path, collection(VALID_FEATURE, broken))
    catalog = loader.load_districts(path)
    assert catalog.names == ("Testaccio",)
    assert any("0..100" in w for w in catalog.warnings)


def test_unnamed_feature_is_dropped(tmp_path: Path) -> None:
    broken = {"type": "Feature", "properties": {"M0": 1, "C0": 1, "T0": 1, "S0": 1}}
    path = write(tmp_path, collection(VALID_FEATURE, broken))
    assert loader.load_districts(path).names == ("Testaccio",)


def test_duplicate_districts_are_ignored(tmp_path: Path) -> None:
    path = write(tmp_path, collection(VALID_FEATURE, VALID_FEATURE))
    catalog = loader.load_districts(path)
    assert len(catalog.districts) == 1
    assert any("duplicate" in w for w in catalog.warnings)


def test_identifier_is_derived_from_the_name_when_absent(tmp_path: Path) -> None:
    feature = {
        "type": "Feature",
        "properties": {"nome": "Trieste-Parioli", "M0": 1, "C0": 1, "T0": 1, "S0": 1},
    }
    path = write(tmp_path, collection(feature))
    assert loader.load_districts(path).districts[0].district_id == "trieste-parioli"


# --- Geometry ---------------------------------------------------------------


def test_null_geometry_still_loads_values(tmp_path: Path) -> None:
    feature = dict(VALID_FEATURE, geometry=None)
    path = write(tmp_path, collection(feature))
    district = loader.load_districts(path).districts[0]
    assert district.geometry is None
    assert district.baseline.mobility == 50.0


def test_unsupported_geometry_type_is_discarded(tmp_path: Path) -> None:
    feature = dict(VALID_FEATURE, geometry={"type": "Point", "coordinates": [12.4, 41.9]})
    path = write(tmp_path, collection(feature))
    assert loader.load_districts(path).districts[0].geometry is None


def test_polygon_geometry_is_preserved(tmp_path: Path) -> None:
    path = write(tmp_path, collection(VALID_FEATURE))
    geometry = loader.load_districts(path).districts[0].geometry
    assert geometry is not None
    assert geometry["type"] == "Polygon"


def test_declared_wgs84_crs_needs_no_reprojection(tmp_path: Path) -> None:
    payload = collection(VALID_FEATURE)
    payload["crs"] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}
    path = write(tmp_path, payload)
    assert loader.load_districts(path).used_fallback is False


def test_foreign_crs_falls_back_when_geopandas_is_absent(tmp_path: Path) -> None:
    if importlib.util.find_spec("geopandas") is not None:
        pytest.skip("geopandas is installed, so reprojection is attempted instead")
    payload = collection(VALID_FEATURE)
    payload["crs"] = {"type": "name", "properties": {"name": "EPSG:3857"}}
    path = write(tmp_path, payload)
    catalog = loader.load_districts(path)
    assert catalog.used_fallback is True
    assert any("reproject" in w for w in catalog.warnings)


def test_slugify_handles_accents_and_spacing() -> None:
    assert loader.slugify("  San  Lorenzo ") == "san-lorenzo"
