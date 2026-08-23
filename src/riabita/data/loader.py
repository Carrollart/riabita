"""District loading with schema validation and a demo-data fallback.

GeoJSON is parsed with the standard library. GeoPandas is imported only when a
file declares a coordinate system other than EPSG:4326 and needs reprojecting,
so the app runs without it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from riabita import config
from riabita.domain.errors import DataSourceError
from riabita.domain.models import Dimensions, District

DEMO_PATH = Path(__file__).with_name("demo_districts.geojson")

_VALUE_KEYS = ("M0", "C0", "T0", "S0")
_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}
_DEFAULT_CRS = "EPSG:4326"
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class DistrictCatalog:
    """Loaded districts plus what went wrong getting them."""

    districts: tuple[District, ...]
    used_fallback: bool
    warnings: tuple[str, ...] = ()

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.districts)

    def get(self, district_id: str) -> District | None:
        return next((d for d in self.districts if d.district_id == district_id), None)


def slugify(name: str) -> str:
    return _SLUG_PATTERN.sub("-", name.strip().lower()).strip("-")


def load_districts(path: str | Path | None = None) -> DistrictCatalog:
    """Load districts from `path`, falling back to bundled demo data.

    Never raises: an unreadable or invalid source degrades to demo data with a
    warning so a round can always start.
    """
    warnings: list[str] = []

    if path:
        try:
            districts, feature_warnings = _load_file(Path(path), is_demo=False)
            warnings.extend(feature_warnings)
            if districts:
                return DistrictCatalog(districts, False, tuple(warnings))
            warnings.append(f"no valid districts in {path}")
        except DataSourceError as error:
            warnings.append(str(error))

    districts, feature_warnings = _load_file(DEMO_PATH, is_demo=True)
    warnings.extend(feature_warnings)
    if not districts:
        raise DataSourceError("bundled demo district data is unusable")
    return DistrictCatalog(districts, True, tuple(warnings))


def _load_file(path: Path, *, is_demo: bool) -> tuple[tuple[District, ...], list[str]]:
    payload = _read_geojson(path)
    features = payload.get("features")
    if not isinstance(features, list):
        raise DataSourceError(f"{path.name} has no feature list")

    features = _reproject(features, payload.get("crs"), path)

    districts: list[District] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for index, feature in enumerate(features):
        try:
            district = _parse_feature(feature, index, is_demo=is_demo)
        except DataSourceError as error:
            warnings.append(str(error))
            continue
        if district.district_id in seen:
            warnings.append(f"duplicate district '{district.name}' ignored")
            continue
        seen.add(district.district_id)
        districts.append(district)

    return tuple(districts), warnings


def _read_geojson(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise DataSourceError(f"cannot read {path.name}: {error.strerror}") from error
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise DataSourceError(f"{path.name} is not valid JSON: {error.msg}") from error
    if not isinstance(payload, dict):
        raise DataSourceError(f"{path.name} is not a GeoJSON object")
    return payload


def _parse_feature(feature: Any, index: int, *, is_demo: bool) -> District:
    if not isinstance(feature, dict):
        raise DataSourceError(f"feature {index} is not an object")

    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise DataSourceError(f"feature {index} has no properties")

    name = properties.get("nome") or properties.get("name")
    if not isinstance(name, str) or not name.strip():
        raise DataSourceError(f"feature {index} has no name")

    values: list[float] = []
    for key in _VALUE_KEYS:
        raw = properties.get(key)
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            raise DataSourceError(f"district '{name}' has a non-numeric {key}")
        value = float(raw)
        if value < config.DIMENSION_MIN or value > config.DIMENSION_MAX:
            raise DataSourceError(f"district '{name}' has {key} outside 0..100")
        values.append(value)

    identifier = feature.get("id")
    district_id = (
        str(identifier) if isinstance(identifier, (str, int)) else slugify(name)
    )

    return District(
        district_id=district_id,
        name=name.strip(),
        baseline=Dimensions.from_array(values),
        geometry=_clean_geometry(feature.get("geometry")),
        is_demo=is_demo,
    )


def _clean_geometry(geometry: Any) -> dict[str, Any] | None:
    """Return usable polygon geometry, or None when the map cannot be drawn."""
    if not isinstance(geometry, dict):
        return None
    if geometry.get("type") not in _GEOMETRY_TYPES:
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        return None
    return geometry


def _reproject(features: list[Any], crs: Any, path: Path) -> list[Any]:
    """Convert to EPSG:4326 when the file declares a different system."""
    name = _crs_name(crs)
    if name is None or name.upper().endswith("4326") or "CRS84" in name.upper():
        return features
    try:
        import geopandas as gpd
    except ImportError:
        raise DataSourceError(
            f"{path.name} uses {name}; install the 'geo' extra to reproject it"
        ) from None
    frame = gpd.read_file(path).to_crs(_DEFAULT_CRS)
    return json.loads(frame.to_json()).get("features", [])


def _crs_name(crs: Any) -> str | None:
    if isinstance(crs, str):
        return crs
    if isinstance(crs, dict):
        properties = crs.get("properties")
        if isinstance(properties, dict):
            candidate = properties.get("name")
            if isinstance(candidate, str):
                return candidate
    return None
