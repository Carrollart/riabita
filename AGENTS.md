# RIABITA Agent Guide

## CArME data workflow

- Runtime source: `src/riabita/data/zona_carme_riabita/zone_carme_riabita.shp` and its `.dbf`, `.shx`, `.prj`, and `.cpg` sidecars.
- The DBF embeds zone IDs, names, `MO`, `CO`, `TO`, `SO`, `RI_z`, and `Classe`. Map the four dimensions to `(M, C, T, S)` and multiply normalized values by 100.
- A0 has missing dimension values and is skipped with a warning. The source provides 26 playable districts.
- GeoPandas reads and reprojects the shapefile to `EPSG:4326` in memory. Do not read GeoJSON, join a CSV, or create proxy values.
- `RIABITA_DISTRICTS_PATH` overrides the bundled shapefile path and must point to a shapefile. Invalid sources raise `DataSourceError`; there is no demo fallback.

## Application integration

- `config.get_settings()` uses the bundled shapefile by default. `RIABITA_DISTRICTS_PATH` overrides it.
- `data.loader.load_districts()` is the only district reader and validates embedded fields, scales values, handles CRS, and reports omitted records.
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

- Focused tests: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_loader.py tests/test_app.py tests/test_i18n.py -q -p no:cacheprovider`
- Full suite: `PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider`
- Keep generated caches, local databases, and credentials out of source control.
- For GWR changes, also run `tests/test_events_and_strategies.py`, `tests/test_app.py`,
  and `tests/test_i18n.py`; verify `A10 → 10` and `C6 → 30` minute profiles.
