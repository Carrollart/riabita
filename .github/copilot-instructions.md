# Repository Instructions

## Working Practices

- Inspect the relevant existing files and nearby tests before making changes.
- Preserve user changes and avoid modifying unrelated files.
- Prefer the smallest clear change that solves the request.
- Keep public APIs and existing behavior stable unless the task explicitly requires a change.
- Do not add dependencies when the standard library or existing project code is sufficient.
- Use the repository's virtual environment and established commands when they are available.
- If the project does not document a tool or convention, make the least-assumptive choice and record important assumptions.

## Validation

- Add or update focused tests when behavior changes.
- Run the narrowest relevant test, lint, format, or type-check command after editing.
- Report what was validated and call out checks that were unavailable or not configured.
- Keep generated files, caches, credentials, and local environment files out of source control.

## CArME data integration

- Use `src/riabita/data/carme_indicators.csv` as the CArME source and
	`src/riabita/data/carme_zones.geojson` as generated spatial output.
- Regenerate the map with `riabita.data.convert_csv_to_geojson` after changing
	the CSV; do not hand-edit the generated GeoJSON.
- The converter preserves source indicators and emits 35 WGS84 Polygon features
	with `M0`, `C0`, `T0`, `S0`, centroid fields, and `baseline_source`.
- The source contains aggregate `Mean_RIz`, not the four simulator baselines.
	Generated dimensions are transparent `modeled_proxy` estimates, not official
	research measurements.
- Velabro-centered bearing/distance polygons are heuristic visualizations, not
	cadastral boundaries. Keep coordinates in `[longitude, latitude]` order and
	close every polygon ring.
- `config.get_settings()` uses the generated map by default,
	`RIABITA_DISTRICTS_PATH` overrides it, and `load_districts()` retains demo
	fallback behavior. Keep CArME parsing outside the simulation engine.

## GWR planner integration

- Store the supplied six-band GWR coefficient matrix in
	`riabita.strategies.GWR_COEFFICIENTS`, always ordered `(M, C, T, S)`.
- Use `strategies.temporal_band()` for district mapping: `A0` maps to 5 minutes;
	numeric A/B/C IDs use lower bands for suffixes 0–4 and upper bands otherwise;
	composite, `Studio_*`, malformed, and unknown IDs fall back to 15 minutes.
- The production AI uses `strategies.ai_allocation()` with district and cumulative
	context. It searches valid progressive allocations, maximizes the authoritative
	RIz/game score first, and uses `final_dimensions · GWR_coefficients` only as a
	tie-breaker. It must remain deterministic and event-blind.
- Preserve partial-turn budgets: use five-credit candidate steps when divisible
	by five and unit steps otherwise. Do not replace the progressive benchmark with
	a one-shot 100-credit planner.
- Render active GWR band and coefficients with `views.render_gwr_profile()` in
	both sidebar and main dashboard. Route all labels through the Italian, English,
	and French i18n catalogs.