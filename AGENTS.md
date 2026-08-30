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

## GWR AI planner

- `riabita.strategies.GWR_COEFFICIENTS` is the canonical six-band matrix for
  5/10/15/20/25/30-minute walking bands. Keep values in `(M, C, T, S)` order:
  Mobility, Culture, Tourism, Socio-demographic.
- `strategies.temporal_band()` maps exact `A0` to 5 minutes and numeric A/B/C
  IDs by suffix (`0–4` lower band, higher suffix upper band). Composite IDs such
  as `A1B1`, `Studio_*`, malformed IDs, and unknown IDs use fallback band 15.
- District-aware `strategies.ai_allocation()` performs a deterministic progressive
  grid search. It maximizes the official game result first, then breaks ties with
  the GWR suitability projection of final dimensions. It receives the current AI
  baseline and cumulative allocation, never the event.
- Keep the benchmark event-blind and fair: AI and player spend the same per-turn
  credits and receive the same event after allocations are chosen. Preserve step
  mode and queue behavior.
- `views.render_gwr_profile()` displays the active band and coefficients in both
  the sidebar and main dashboard. Maintain i18n parity for it/en/fr.

## Validation

- Focused tests: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_converter.py tests/test_loader.py -q -p no:cacheprovider`
- Full suite: `PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider`
- Keep generated caches, local databases, credentials, and override GeoJSON files out of source control.
- For GWR changes, also run `tests/test_events_and_strategies.py`, `tests/test_app.py`,
  and `tests/test_i18n.py`; verify `A10 → 10` and `C6 → 30` minute profiles.
