"""Direct CArME shapefile loading and validation."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import shape

from riabita.data import loader
from riabita.domain.errors import DataSourceError

SHAPEFILE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "riabita"
    / "data"
    / "zona_carme_riabita"
    / "zone_carme_riabita.shp"
)


def test_default_dataset_loads_embedded_indicators() -> None:
    catalog = loader.load_districts(None)
    assert len(catalog.districts) == 26
    assert catalog.get("A0") is None
    assert "A0" in catalog.warnings

    a1 = catalog.get("A1")
    assert a1 is not None
    assert a1.baseline.as_array().tolist() == pytest.approx(
        [62.2076485, 58.5169849, 100.0, 55.2753667]
    )


def test_shapefile_geometry_is_reprojected_to_wgs84() -> None:
    district = loader.load_districts(SHAPEFILE).get("A1")
    assert district is not None
    assert district.geometry is not None
    bounds = shape(district.geometry).bounds
    assert -180 <= bounds[0] <= 180
    assert -90 <= bounds[1] <= 90
    assert -180 <= bounds[2] <= 180
    assert -90 <= bounds[3] <= 90


def test_missing_shapefile_raises_data_source_error(tmp_path: Path) -> None:
    with pytest.raises(DataSourceError, match="cannot read"):
        loader.load_districts(tmp_path / "missing.shp")


def test_non_shapefile_source_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DataSourceError, match="ESRI shapefile"):
        loader.load_districts(tmp_path / "districts.geojson")


def test_shapefile_missing_required_fields_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frame = gpd.GeoDataFrame({"nome": ["Incomplete"]}, geometry=[None], crs="EPSG:4326")
    monkeypatch.setattr(gpd, "read_file", lambda _: frame)

    with pytest.raises(DataSourceError, match="missing required fields"):
        loader.load_districts(tmp_path / "districts.shp")
