---
applyTo: "src/riabita/data/**/*.py,src/riabita/data/**/*.geojson,src/riabita/data/**/*.csv,tests/test_converter.py"
---
# CArME data guidance

- The authoritative tabular input for this integration is `src/riabita/data/carme_indicators.csv`.
- Generate `src/riabita/data/carme_zones.geojson` with `generate_carme_geojson()` from `convert_csv_to_geojson.py`; do not hand-edit generated GeoJSON.
- Preserve the 23 source columns and the canonical playable properties `nome`, `M0`, `C0`, `T0`, `S0`, `Mean_RIz`, `Classe`, `centroid_lat`, and `centroid_lon`.
- Keep all vectors in `(M, C, T, S)` order. The CSV has `Mean_RIz`, but no authoritative dimension columns; generated dimensions use `baseline_source: modeled_proxy` and must not be described as official measurements.
- Use the Velabro anchor at latitude `41.889`, longitude `12.482`, clockwise bearings, metre offsets, WGS84 `[longitude, latitude]` coordinates, and closed polygon rings.
- The generated octagons are spatial visualization heuristics, not cadastral boundaries.
- Keep filesystem access in the data layer. The simulation engine must not import Pandas, GeoPandas, Streamlit, or read GeoJSON directly.
- Validate generated output through `load_districts()` and keep the explicit `RIABITA_DISTRICTS_PATH` override plus demo fallback working.
