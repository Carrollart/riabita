"""Load playable districts directly from the bundled CArME shapefile."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from pathlib import Path

from riabita import config
from riabita.domain.errors import DataSourceError
from riabita.domain.models import Dimensions, District

_DIMENSION_FIELDS = ("MO", "CO", "TO", "SO")
_REQUIRED_FIELDS = ("zc_code", "nome", *_DIMENSION_FIELDS)
_WGS84 = "EPSG:4326"


@dataclass(frozen=True)
class DistrictCatalog:
    """Loaded districts and identifiers of records omitted during validation."""

    districts: tuple[District, ...]
    warnings: tuple[str, ...] = ()

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.districts)

    def get(self, district_id: str) -> District | None:
        return next((d for d in self.districts if d.district_id == district_id), None)


def load_districts(path: str | Path | None = None) -> DistrictCatalog:
    """Load districts from the CArME shapefile and its embedded indicators.

    Missing or invalid sources raise ``DataSourceError``; no substitute dataset
    is loaded because the application only supports the supplied CArME data.
    """
    source = Path(path) if path is not None else config.DEFAULT_DISTRICTS_PATH
    if source.suffix.lower() != ".shp":
        raise DataSourceError("district source must be an ESRI shapefile")

    try:
        import geopandas as gpd
    except ImportError as error:
        raise DataSourceError(
            f"GeoPandas could not be imported: {error}"
        ) from error

    try:
        frame = gpd.read_file(source)
    except Exception as error:
        raise DataSourceError(f"cannot read {source.name}: {error}") from error

    if frame.crs is None:
        raise DataSourceError(f"{source.name} has no coordinate reference system")

    missing_fields = [field for field in _REQUIRED_FIELDS if field not in frame.columns]
    if missing_fields:
        raise DataSourceError(
            f"{source.name} is missing required fields: {', '.join(missing_fields)}"
        )

    try:
        frame = frame.to_crs(_WGS84)
    except Exception as error:
        raise DataSourceError(
            f"cannot reproject {source.name} to WGS84: {error}"
        ) from error

    warnings: list[str] = []
    districts: list[District] = []
    seen: set[str] = set()

    for index, row in frame.iterrows():
        district_id = _text(row["zc_code"])
        name = _text(row["nome"])
        label = district_id or name or f"record {index}"
        if not district_id or not name:
            warnings.append(label)
            continue

        raw_values = [row[field] for field in _DIMENSION_FIELDS]
        values = [_scaled_dimension(value) for value in raw_values]
        if any(value is None for value in values):
            warnings.append(district_id)
            continue
        baseline_values = tuple(value for value in values if value is not None)

        if district_id in seen:
            warnings.append(district_id)
            continue
        seen.add(district_id)

        geometry = row.geometry
        geometry_mapping = None
        if geometry is not None and not geometry.is_empty:
            if geometry.geom_type in {"Polygon", "MultiPolygon"}:
                geometry_mapping = geometry.__geo_interface__

        districts.append(
            District(
                district_id=district_id,
                name=name,
                baseline=Dimensions.from_array(baseline_values),
                geometry=geometry_mapping,
            )
        )

    if not districts:
        raise DataSourceError(
            f"{source.name} contains no districts with valid indicators"
        )
    return DistrictCatalog(tuple(districts), tuple(warnings))


def _text(value: object) -> str:
    """Return a non-empty shapefile text field, treating nulls as empty."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _scaled_dimension(value: object) -> float | None:
    """Convert one normalized 0..1 indicator into the game's 0..100 scale."""
    if not isinstance(value, Real) or isinstance(value, bool):
        return None
    normalized = float(value)
    if not math.isfinite(normalized) or not 0 <= normalized <= 1:
        return None
    return normalized * (config.DIMENSION_MAX - config.DIMENSION_MIN)
