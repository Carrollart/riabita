"""Convert the tabular CArME indicators into playable GeoJSON districts.

The source table contains an aggregate ``Mean_RIz`` value, not the four
dimension baselines required by the game. This module therefore derives
transparent proxy values from the available indicators and labels them as
modeled estimates in the output metadata.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

ANCHOR_LATITUDE = 41.889
ANCHOR_LONGITUDE = 12.482
METERS_PER_DEGREE_LATITUDE = 111_320.0
REQUIRED_COLUMNS = {"Zona_ID", "Nome", "Mean_RIz", "Classe"}

# Bearing is measured clockwise from north. Distances and radii are metres.
PLACEMENTS: dict[str, tuple[float, float, float]] = {
    "A0": (0, 0, 250),
    "A1": (270, 550, 300), "A2": (315, 550, 300), "A3": (30, 550, 300),
    "A4": (75, 650, 300), "A6": (100, 650, 300), "A7": (135, 650, 300),
    "A8": (180, 800, 300), "A9": (210, 650, 300), "A10": (240, 750, 300),
    "B1": (280, 1100, 400), "B2": (310, 1200, 400), "B3": (25, 1200, 400),
    "B4": (60, 1200, 400), "B5": (90, 1300, 400), "B6": (120, 1400, 400),
    "B7": (175, 1500, 400), "B8": (205, 1300, 400), "B10": (235, 1400, 400),
    "C1": (295, 1900, 500), "C2": (345, 1900, 500), "C3": (45, 2000, 500),
    "C4": (80, 2000, 500), "C5": (115, 2100, 500), "C6": (160, 2300, 500),
    "C7": (215, 1900, 500), "C8": (245, 2100, 500),
    "A1B1": (275, 800, 450), "A2B2": (312, 850, 450), "A3B3": (27, 850, 450),
    "Studio_1": (5, 1500, 450), "Studio_2": (77, 1500, 450),
    "Studio_3": (149, 1500, 450), "Studio_4": (221, 1500, 450),
    "Studio_5": (293, 1500, 450),
}
DEFAULT_PLACEMENT = (180, 1500, 400)


def _number(row: pd.Series, column: str, default: float = 50.0) -> float:
    value = row.get(column)
    if value is None or pd.isna(value):
        return default
    return float(value)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 50.0


def proxy_dimensions(row: pd.Series) -> dict[str, float]:
    """Return clamped 0..100 playable dimension estimates for one row."""
    indicator_columns = (
        "Tasso_Occupazione_Pct", "Quota_Laureati_Pct", "Edifici_Attivita_Culturali",
        "Spettacoli_Dal_Vivo_Media_Giornaliera", "Spettacoli_Totali_Media_Giornaliera",
        "Rapporto_Posti_Letto_Turistici_Popolazione_Pct",
        "Rapporto_Alloggi_Turistici_Abitativi_Pct", "Quota_Giovani_Pct",
        "Quota_Anziani_Pct", "Quota_Stranieri_Pct", "Dimensione_Media_Famiglia",
    )
    if not any(column in row.index and not pd.isna(row[column]) for column in indicator_columns):
        return {key: 50.0 for key in ("M0", "C0", "T0", "S0")}

    employment = _number(row, "Tasso_Occupazione_Pct")
    graduates = _number(row, "Quota_Laureati_Pct")
    culture_buildings = min(_number(row, "Edifici_Attivita_Culturali"), 100)
    live_events = min(_number(row, "Spettacoli_Dal_Vivo_Media_Giornaliera") * 10, 100)
    total_events = min(_number(row, "Spettacoli_Totali_Media_Giornaliera") * 5, 100)
    tourist_beds = min(_number(row, "Rapporto_Posti_Letto_Turistici_Popolazione_Pct"), 100)
    tourist_housing = min(_number(row, "Rapporto_Alloggi_Turistici_Abitativi_Pct") * 2, 100)
    youth = _number(row, "Quota_Giovani_Pct")
    elderly = _number(row, "Quota_Anziani_Pct")
    foreigners = _number(row, "Quota_Stranieri_Pct")
    family_size = min(_number(row, "Dimensione_Media_Famiglia") * 25, 100)

    return {
        "M0": round(max(0.0, min(100.0, employment)), 4),
        "C0": round(max(0.0, min(100.0, _mean([graduates, culture_buildings, live_events, total_events]))), 4),
        "T0": round(max(0.0, min(100.0, _mean([tourist_beds, tourist_housing]))), 4),
        "S0": round(max(0.0, min(100.0, _mean([youth, 100 - elderly, 100 - foreigners, employment, family_size]))), 4),
    }


def _json_value(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return str(value)


def _centroid(zona_id: str) -> tuple[float, float, float]:
    bearing, distance, radius = PLACEMENTS.get(zona_id, DEFAULT_PLACEMENT)
    angle = math.radians(bearing)
    north = distance * math.cos(angle)
    east = distance * math.sin(angle)
    latitude = ANCHOR_LATITUDE + north / METERS_PER_DEGREE_LATITUDE
    longitude = ANCHOR_LONGITUDE + east / (
        METERS_PER_DEGREE_LATITUDE * math.cos(math.radians(ANCHOR_LATITUDE))
    )
    return latitude, longitude, radius


def _octagon(latitude: float, longitude: float, radius: float) -> list[list[float]]:
    points: list[list[float]] = []
    for index in range(8):
        angle = 2 * math.pi * index / 8
        east = radius * math.sin(angle)
        north = radius * math.cos(angle)
        points.append([
            longitude + east / (METERS_PER_DEGREE_LATITUDE * math.cos(math.radians(latitude))),
            latitude + north / METERS_PER_DEGREE_LATITUDE,
        ])
    points.append(points[0].copy())
    return points


def generate_carme_geojson(csv_path: str | Path, output_geojson_path: str | Path) -> dict[str, Any]:
    """Convert ``csv_path`` and write a GeoJSON FeatureCollection."""
    frame = pd.read_csv(csv_path, keep_default_na=True)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
    identifiers = frame["Zona_ID"].astype(str).str.strip()
    if identifiers.eq("").any() or identifiers.duplicated().any():
        raise ValueError("CSV must contain unique, non-empty Zona_ID values")

    features: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        zona_id = str(row["Zona_ID"]).strip()
        latitude, longitude, radius = _centroid(zona_id)
        properties = {column: _json_value(row[column]) for column in frame.columns}
        properties.update(proxy_dimensions(row))
        properties.update({
            "nome": str(row["Nome"]).strip(),
            "baseline_source": "modeled_proxy",
            "centroid_lat": round(latitude, 5),
            "centroid_lon": round(longitude, 5),
        })
        features.append({
            "type": "Feature",
            "id": zona_id,
            "properties": properties,
            "geometry": {"type": "Polygon", "coordinates": [_octagon(latitude, longitude, radius)]},
        })

    payload = {
        "type": "FeatureCollection",
        "name": "carme_zones",
        "metadata": {
            "source": str(Path(csv_path)),
            "baseline_source": "modeled_proxy",
            "geometry_source": "heuristic_octagons",
            "crs": "EPSG:4326",
        },
        "features": features,
    }
    destination = Path(output_geojson_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    """Run the converter from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("output_geojson_path", type=Path)
    args = parser.parse_args()
    payload = generate_carme_geojson(args.csv_path, args.output_geojson_path)
    print(f"Generated {len(payload['features'])} CArME zones in {args.output_geojson_path}")


if __name__ == "__main__":
    main()