# Data and UI

Geospatial loading, localization, layout, charts, and accessibility.

## District data

### CArME source and generated map

The CArME table is `src/riabita/data/carme_indicators.csv`. Generate
`src/riabita/data/carme_zones.geojson` with:

```text
PYTHONPATH=src .venv/bin/python -m riabita.data.convert_csv_to_geojson src/riabita/data/carme_indicators.csv src/riabita/data/carme_zones.geojson
```

The converter emits 35 WGS84 Polygon features, preserves the source indicators,
and adds `M0`, `C0`, `T0`, `S0`, `nome`, centroid coordinates, and
`baseline_source`. Because the table contains `Mean_RIz` rather than the four
dimension baselines, generated dimensions are modeled proxy estimates. Keep
that caveat visible in research and product documentation.

The Velabro anchor is latitude `41.889`, longitude `12.482`. Bearings, walking
distances, and polygon radii follow the supplied spatial-modeling brief. Each
generated octagon is a visualization approximation, not an authoritative
cadastral boundary.

### Schema

Each GeoJSON feature must carry these properties:

| Property | Type | Constraint |
|---|---|---|
| `nome` | string | Non-empty, unique across features |
| `M0`, `C0`, `T0`, `S0` | number | `0..100` inclusive |

Geometry must be `Polygon` or `MultiPolygon`, or `null`. A feature `id` is optional;
derive a stable `district_id` by slugifying `nome` when `id` is absent.

### Loading order

1. If `RIABITA_DISTRICTS_PATH` is set, read that file.
2. Otherwise, use the generated CArME GeoJSON when it exists.
3. Validate the schema. Drop individual features that fail validation and record why.
4. If the selected path is unset, unreadable, malformed, or yields zero valid features, load
   the bundled `data/demo_districts.geojson` and mark every district `is_demo=True`
   (REQ-013).

Never raise out of the loader to the top level. Convert failures into a
`DataSourceError` the UI catches, and always end with a usable district list. An
unreadable custom file degrades to demo data; it never produces an empty app.

### Demo dataset

Seed `data/demo_districts.geojson` from the district table in
the original research document (Centro, San Lorenzo, Trastevere, Montesacro,
Trieste-Parioli, EUR, Ostia, Tuscolano, Magliana, Nomentano) with their documented
`M0`, `C0`, `T0`, `S0` values and simplified polygons.

Those polygons are rough rectangles and the indicators are illustrative. Label them
in the UI as demo data, not research output (REQ-014). Do not present them as the
university RIz dataset.

### Geometry handling

- Assume and enforce `EPSG:4326`. Reproject when the source declares another CRS.
- Treat missing, empty, or invalid geometry as "no map available" for that district.
  Values still work; only the map hides (REQ-015).
- Cache the parsed result with `st.cache_data` keyed on the resolved path and its
  modification time (REQ-016). Do not cache the raw GeoDataFrame across a path change.
- GeoPandas is imported only inside the loader, so the rest of the app runs without it.

## Localization

`i18n.py` holds one nested catalog: `CATALOG[language][key] -> str`. Language codes
are `it`, `en`, and `fr`, with `it` as default. The selector displays the matching
flag for each language.

Key naming uses `area.element`, for example `sidebar.budget_total`,
`event.tourist_boom.name`, `error.allocation_sum`, `profile.resilient`.

- The view layer calls `t(key, **params)` and never contains literal display text
  (REQ-003).
- Parameterize with named placeholders, never string concatenation, so word order can
  differ between languages.
- Resolution order is active language, then Italian, then the key itself (REQ-004).
  A test asserts all catalogs have identical key sets, so a missing key fails CI
  rather than reaching a player.
- Dimension labels: Italian uses `Mobilità`, `Cultura`, `Turismo`, `Comunità`.
  English uses `Mobility`, `Culture`, `Tourism`, `Community`. The domain name for the
  fourth dimension stays `socio` in code regardless of its display label.
- Changing language stores the new code in session state and re-renders. The current
  round, allocations, and results survive the switch (REQ-002).

## Layout

**Sidebar**

1. Language selector.
2. District selector, showing the demo-data notice when applicable.
3. Baseline values and initial RIz for the selected district.
4. Four budget sliders in `(M, C, T, S)` order, integer step 1, range `0..100`.
5. Cumulative invested total, current turn total, and remaining credits, updating
   live (REQ-022).
6. Clear-investment and restart-game controls (REQ-026).
7. Confirm-investment button.

**Main area**

1. Title and one-line premise.
2. Before-and-after dimension comparison with signed deltas (REQ-050).
3. Initial RIz, final RIz, and yield (REQ-051).
4. Urban profile and the itemized bonus and penalty list (REQ-057, REQ-058).
5. Radar chart (REQ-052).
6. Event panel (REQ-043).
7. Benchmark comparison chart (REQ-056).
8. Nickname field and score submission after all credits are invested (REQ-060).
9. Leaderboard with a district filter (REQ-066, REQ-067).

Before the first simulation, show the baseline radar and a short how-to-play summary
instead of empty result panels.

## Budget controls

The current turn and cumulative totals drive these states:

| Condition | Behavior |
|---|---|
| `0 < turn_total <= remaining` | Confirm investment enabled |
| `turn_total == 0` | Confirm investment disabled |
| `turn_total > remaining` | Confirm investment disabled; message names the exact number of credits to remove (REQ-023) |
| any cumulative allocation `> 60` | Non-blocking warning that the concentration penalty will apply (REQ-025) |
| `remaining == 0` | Turn controls hide and leaderboard submission becomes available |

Compute the difference from the validation result rather than duplicating the rule in
the view. Never let the view decide what is valid.

## Charts

Both figures use `plotly.graph_objects`, take plain Python or NumPy values, and return
a `Figure` without calling Streamlit. That keeps them unit-testable (REQ-083).

### Radar

- Categories are the four localized dimension labels.
- Close each polygon by repeating the first value and the first category at the end.
  A four-point trace that is not closed renders as an open path.
- Two traces: the baseline as a dashed, muted line; the final state as a solid filled
  line.
- Fix the radial axis to `range=[0, 100]` (REQ-052). An auto-scaled axis makes small
  changes look dramatic and breaks comparability between rounds.
- Set `dash` inside `line`, as `line=dict(color=..., dash="dash")`.

### Comparison

Horizontal bar chart of final RIz for the player, the AI planner, and the random
choices, sorted descending. When saved scores exist for the selected district, add
the highest saved score as `Best player: <nickname>`. Annotate each bar with its
numeric value so the ranking does not depend on bar length or color alone (REQ-085).

### Known defects in the brief

The sample code in the original research document is incomplete in ways that are
easy to copy by accident. Do not reproduce these:

- `dash='dash'` passed as a top-level `Scatterpolar` argument. It belongs in `line`.
- `radialaxis=dict(visible=True, range=)`, a syntax error. Use `range=[0, 100]`.
- `r=initial_values + [initial_values]`, which appends the list to itself. Append the
  first element instead.
- `st.columns([2, 4])` unpacked into three variables, which raises at runtime.
- `.iloc` without an index, and `allocations[5]` / `allocations[6]` on a length-4
  array, which raise `IndexError`.

## Turn history

The turn history lists the total credits and the player's credits assigned to each
dimension in `(M, C, T, S)` order, together with the event for that turn.

## Score submission

- Generate the player ID once per session with `uuid4` and keep it in session state.
- Generate a `round_id` when a round is simulated; reuse it for submission so a
  double click cannot create duplicates (REQ-065).
- Validate the nickname before submitting and show a localized message on failure
  (REQ-063).
- Pass the stored `SimulationResult` to the service. The view never assembles metric
  values by hand (REQ-064).
- After a successful submission, disable the button for that round and confirm.

## Leaderboard display

- Show at most `RIABITA_LEADERBOARD_LIMIT` rows, ranked by final RIz descending, ties
  broken by earliest `created_at` (REQ-066).
- Columns: rank, nickname, district, final RIz, yield, risk, profile.
- Filter by district, defaulting to the currently selected one, with an all-districts
  option.
- Empty state: a localized "no scores yet" message, not a blank table.
- Unavailable state: a localized notice that scores cannot load right now. Never
  surface the connection string, driver error, or traceback (REQ-071).

## Responsiveness and accessibility

- Use `st.columns` for wide layouts but keep each column readable when stacked. Avoid
  more than three side-by-side columns in the results row (REQ-084).
- Column weight lists must match the number of unpacked variables.
- Do not rely on color alone: pair the profile badge with its text label, and label
  every chart series in the legend (REQ-085).
- Give every input an explicit non-empty label. When a label is visually redundant,
  use `label_visibility="collapsed"` rather than passing an empty string, so screen
  readers still announce it.
- Keep numeric text at default size or larger; do not shrink metric captions for
  layout reasons.
- Every error, warning, and empty state resolves through the catalog and states what
  the player can do next (REQ-086).
