---
applyTo: "src/riabita/data/**/*.py,src/riabita/data/**/*.geojson,src/riabita/data/**/*.csv,tests/test_converter.py"
---
# CArME data guidance

- The authoritative tabular input for this integration is `src/riabita/data/carme_indicators.csv`.
- The authoritative geometry source for the real zones is `docs/zone_carme/zone_carme.shp`; generate `src/riabita/data/carme_zones.geojson` with `generate_carme_geojson()` from `convert_csv_to_geojson.py` and pass `--shapefile` when regenerating the active main map.
- Do not hand-edit generated GeoJSON. The converter writes WGS84 features that the app can load directly.
- Preserve the source columns and the canonical playable properties `nome`, `M0`, `C0`, `T0`, `S0`, `Mean_RIz`, `Classe`, `centroid_lat`, and `centroid_lon`.
- Keep all vectors in `(M, C, T, S)` order. The CSV has `Mean_RIz`, but no authoritative dimension columns; generated dimensions use `baseline_source: modeled_proxy` and must not be described as official measurements.
- For base zones present in the shapefile, use the real polygon geometry and reproject to `EPSG:4326`. For composite/study zones without real geometry, keep the CSV-derived fallback polygon generation.
- The historical Velabro heuristic is retained as a fallback only; the shapefile-backed geometry is authoritative for the main map and should not be replaced by a synthetic layout without explicit review.
- Keep filesystem access in the data layer. The simulation engine must not import Pandas, GeoPandas, Streamlit, or read GeoJSON directly.
- Validate generated output through `load_districts()` and keep the explicit `RIABITA_DISTRICTS_PATH` override plus demo fallback working.
