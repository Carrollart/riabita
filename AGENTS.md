# RIABITA Agent Guide

## CArME data workflow

- Source CSV: `src/riabita/data/carme_indicators.csv`.
- Generated GeoJSON: `src/riabita/data/carme_zones.geojson`.
- Regenerate the map with:
  `PYTHONPATH=src .venv/bin/python -m riabita.data.convert_csv_to_geojson src/riabita/data/carme_indicators.csv src/riabita/data/carme_zones.geojson`
- The converter entry point is `generate_carme_geojson()` in `src/riabita/data/convert_csv_to_geojson.py`.
- The converter preserves the source columns, adds `M0`, `C0`, `T0`, `S0`, `baseline_source`, and centroid fields, and emits 35 WGS84 Polygon features.
- Geometry uses the Velabro anchor (`41.889, 12.482`), documented bearing/distance/radius placements, and closed octagons. Geometry is a visualization heuristic, not authoritative cadastral data.
- The CSV provides `Mean_RIz`, not simulator dimension baselines. Treat the generated dimensions as `modeled_proxy` estimates, not official research measurements.

## Application integration

- `config.get_settings()` uses the generated GeoJSON by default when it exists. `RIABITA_DISTRICTS_PATH` always overrides it.
- `data.loader.load_districts()` is the only GeoJSON reader and retains validation, caching, CRS handling, and demo fallback.
- `ui.charts.build_selection_map()` creates the Plotly overview figure; `ui.views.render_selection_map()` displays it.
- The overview map is exploratory. The existing district selectbox remains the authoritative selection control because polygon-click state integration is not implemented.
- Preserve the `(M, C, T, S)` order and keep CArME parsing outside the simulation engine.

## Validation

- Focused tests: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_converter.py tests/test_loader.py -q -p no:cacheprovider`
- Full suite: `PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider`
- Keep generated caches, local databases, credentials, and override GeoJSON files out of source control.
