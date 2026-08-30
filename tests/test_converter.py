"""CArME CSV to GeoJSON conversion contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from riabita.data.convert_csv_to_geojson import generate_carme_geojson, proxy_dimensions
from riabita.data.loader import load_districts

CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "riabita"
    / "data"
    / "carme_indicators.csv"
)


def test_carme_csv_generates_all_zones_and_valid_rings(tmp_path: Path) -> None:
    output = tmp_path / "carme_zones.geojson"
    payload = generate_carme_geojson(CSV_PATH, output)

    assert len(payload["features"]) == 35
    assert output.is_file()
    for feature in payload["features"]:
        ring = feature["geometry"]["coordinates"][0]
        assert feature["id"]
        assert len(ring) == 9
        assert ring[0] == ring[-1]
        values = [feature["properties"][key] for key in ("M0", "C0", "T0", "S0")]
        assert all(0 <= value <= 100 for value in values)


def test_generated_geojson_round_trips_through_district_loader(tmp_path: Path) -> None:
    output = tmp_path / "carme_zones.geojson"
    generate_carme_geojson(CSV_PATH, output)

    catalog = load_districts(output)

    assert catalog.used_fallback is False
    assert len(catalog.districts) == 35
    assert catalog.get("A0") is not None
    assert catalog.get("A0").geometry is not None  # type: ignore[union-attr]


def test_converter_preserves_null_csv_values_as_json_null(tmp_path: Path) -> None:
    output = tmp_path / "carme_zones.geojson"
    generate_carme_geojson(CSV_PATH, output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    a0 = next(feature for feature in payload["features"] if feature["id"] == "A0")
    assert a0["properties"]["Tasso_Occupazione_Pct"] is None
    assert a0["properties"]["baseline_source"] == "modeled_proxy"


def test_proxy_dimensions_use_neutral_values_for_missing_inputs() -> None:
    row = pd.Series(dtype=float)
    dimensions = proxy_dimensions(row)

    assert set(dimensions) == {"M0", "C0", "T0", "S0"}
    assert all(value == 50.0 for value in dimensions.values())


def test_converter_rejects_duplicate_zone_ids(tmp_path: Path) -> None:
    source = tmp_path / "zones.csv"
    pd.DataFrame(
        [{"Zona_ID": "A0", "Nome": "One", "Mean_RIz": 0.5, "Classe": "Media"},
         {"Zona_ID": "A0", "Nome": "Two", "Mean_RIz": 0.5, "Classe": "Media"}]
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="unique"):
        generate_carme_geojson(source, tmp_path / "zones.geojson")
