# Implementation Plan

Phased task list for RIABITA ROMA. Phases are ordered by dependency: finish and test
one phase before starting the next.

`[P]` marks tasks that are parallelizable with their immediate siblings because they
touch different files and share no state.

## Current implementation status

Phases 0–9 and the automated parts of Phase 10 are implemented in the workspace and
covered by the test suite. The remaining manual check is T101: verify the layout on a
narrow viewport. Deferred items D01 and D02 remain intentionally out of scope.

Read [simulation-rules.md](./simulation-rules.md) before Phase 2, and
[architecture.md](./architecture.md) before Phase 1. Verification IDs (`V-*`) refer to
groups in [verification.md](./verification.md).

## Phase 0 — Project setup

- [ ] T001 Add runtime dependencies to `requirements.txt`: `streamlit`, `pandas`,
      `numpy`, `plotly`, `SQLAlchemy`, `psycopg[binary]`. Omit `scipy`; NumPy
      covers every statistic this project needs. GeoPandas belongs in the
      optional `geo` extra, not the runtime set.
- [ ] T002 Add `pyproject.toml` with `[tool.pytest.ini_options]` setting
      `pythonpath = ["src"]` and `testpaths = ["tests"]`, plus a `dev` dependency
      group containing `pytest`.
- [ ] T003 [P] Extend `.gitignore` with `.env`, local shapefile overrides, `.pytest_cache/`,
      and any local database artifacts. [REQ-069]
- [ ] T004 [P] Create the package skeleton under `src/riabita/` per
      [architecture.md](./architecture.md), with `__init__.py` in each subpackage.
- [ ] T005 Create `tests/__init__.py` and confirm `pytest` collects an empty suite.

## Phase 1 — Configuration and domain

- [ ] T010 Write `riabita/config.py` with `RULES_VERSION`, `BUDGET_TOTAL = 100`, the
      impact matrix, weights, and every threshold, bonus, and penalty constant from
      [simulation-rules.md](./simulation-rules.md). No literals elsewhere. [REQ-080, REQ-081]
- [ ] T011 Add `get_settings()` to `config.py`, resolving `RIABITA_DATABASE_URL`,
      `RIABITA_DISTRICTS_PATH`, `RIABITA_DEFAULT_LANGUAGE` (`it`, `en`, or `fr`), and
      `RIABITA_LEADERBOARD_LIMIT` from the environment, then Streamlit secrets, then
      defaults. Use a project-local SQLite file when no database URL is configured.
      Never log resolved secrets. [REQ-060, REQ-069]
- [ ] T012 Write `riabita/domain/models.py` with the frozen dataclasses in
      [architecture.md](./architecture.md), including `Dimensions.as_array()` and
      `Dimensions.from_array()` in `(M, C, T, S)` order. [REQ-039, REQ-082]
- [ ] T013 [P] Write `riabita/domain/errors.py` with `RiabitaError`,
      `ValidationError`, `DataSourceError`, and `LeaderboardUnavailable`.
- [ ] T014 Write `riabita/domain/validation.py` returning the failed rule identifiers
      and the signed sum difference. Pure, no exceptions raised. [REQ-021, REQ-024]
- [ ] T015 Tests for validation and dataclass immutability. → V-VAL

## Phase 2 — Simulation engine

- [ ] T020 Implement the atomic matrix step in `riabita/engine/simulator.py`:
      `delta = (b / 10) @ MATRIX`, applied once to the baseline. [REQ-030, REQ-031]
- [ ] T021 Implement tourism pressure on post-matrix `T`, highest tier only, scaled by
      `B_T / 10`. [REQ-032]
- [ ] T022 Implement event application as vector addition, with `None` treated as a
      zero vector. [REQ-033]
- [ ] T023 Implement clamping of dimensions to `0..100`. [REQ-034]
- [ ] T024 Implement the four modifiers in `riabita/engine/metrics.py`, each returning
      a `Modifier` record including zero-point outcomes. Use the **population**
      standard deviation. [REQ-035, REQ-058]
- [ ] T025 Implement `riz()`, initial RIz without modifiers, final RIz with modifiers
      clamped to `0..100`. [REQ-036]
- [ ] T026 Implement yield, risk, and Sharpe with the `1e-9` zero-risk guard, and
      `classify_profile()` using the ordered rules. [REQ-036, REQ-057]
- [ ] T027 Compose `run_simulation(district, allocation, event=None)` in the fixed
      8-step order, raising `ValidationError` on invalid input, mutating nothing, and
      stamping `rules_version`. [REQ-037, REQ-038, REQ-039]
- [ ] T028 Engine tests including the golden example and every threshold boundary.
      → V-ENG

## Phase 3 — Events

- [ ] T030 Write `riabita/events.py` with the five catalog entries, their stable IDs,
      translation keys, and impact vectors. [REQ-040, REQ-041]
- [ ] T031 Add `draw_event(rng)` using the injected generator and `get_event(event_id)`
      for scripted scenarios. [REQ-042, REQ-044]
- [ ] T032 Event tests: catalog completeness, seeded reproducibility, unknown ID
      handling. → V-EVT

## Phase 4 — Benchmark strategies

- [ ] T040 Implement `ai_allocation(baseline, budget_total)` as the deterministic
      three-step heuristic. Verify the 100-credit San Lorenzo worked example yields
      `[25, 25, 10, 40]`. [REQ-053]
- [ ] T041 Implement `random_allocation(rng, budget_total)` using Dirichlet weights
      and the largest-remainder integer conversion. [REQ-053]
- [ ] T042 Strategy tests: both always sum to the supplied positive turn budget, stay
      within range, and reproduce under a seed; neither function accepts an event
      parameter. → V-STRAT
      [REQ-054, REQ-055]

## Phase 5 — District data

- [x] T050 Load the bundled shapefile and its embedded dimension indicators directly.
- [ ] T051 Implement schema validation in `riabita/data/loader.py`: required
      properties, numeric ranges, unique names, geometry type check. [REQ-012]
- [x] T052 Implement `load_districts()` with shapefile overrides, per-record warning
      collection, and `DataSourceError` instead of propagating raw I/O failures.
- [ ] T053 Add CRS normalization to `EPSG:4326` and null-geometry tolerance. [REQ-015]
- [ ] T054 Loader tests against valid, malformed, missing, and empty files, using
      temporary fixtures only. → V-DATA

## Phase 6 — Localization

- [ ] T060 Write `riabita/i18n.py` with the `it`, `en`, and `fr` catalogs and
      `t(key, **params)` using the active-then-Italian-then-key fallback. [REQ-001, REQ-004]
- [ ] T061 Populate keys for navigation, dimensions, budget, results, modifiers,
      profiles, events, leaderboard, and every error and empty state. [REQ-003, REQ-086]
- [ ] T062 Add `get_language()` and `set_language()` backed by session state, defaulting
      from settings. [REQ-002]
- [ ] T063 Catalog tests: identical key sets, no empty values, placeholder parity.
      → V-I18N

## Phase 7 — Leaderboard

- [ ] T070 Write `riabita/leaderboard/models.py` with the `leaderboard_entries`
      SQLAlchemy mapping, the unique `round_id` constraint, and the ranking index.
      [REQ-061]
- [ ] T071 Define the `LeaderboardRepository` protocol with `add`, `top`, and
      `exists`. [REQ-068]
- [ ] T072 Implement `SqlAlchemyLeaderboardRepository` using ORM constructs and bound
      parameters only, with engine creation from `RIABITA_DATABASE_URL` and schema
      initialization on first use. Support file-backed SQLite, including parent
      directory creation, and PostgreSQL. [REQ-060, REQ-070]
- [ ] T073 [P] Implement `InMemoryLeaderboardRepository` with identical ordering
      semantics for tests. [REQ-083]
- [ ] T074 Implement nickname validation: 3–24 characters, letters, digits, spaces,
      hyphens, underscores; trimmed. [REQ-063]
- [ ] T075 Implement `submit_result()` in `service.py`, building the entry from a
      `SimulationResult` only, skipping duplicates by `round_id`, and raising
      `LeaderboardUnavailable` on operational errors. [REQ-064, REQ-065, REQ-071]
- [ ] T076 Implement `top_entries(limit, district_id=None)` ranked by RIz descending
      with earliest-timestamp tie-breaking. [REQ-066, REQ-067]
- [ ] T077 Leaderboard tests against the in-memory repository and temporary SQLite
      files, including persistence across repository instances and a SQL-injection
      attempt through the nickname and district filter. → V-LB

## Phase 8 — Charts

- [ ] T080 Implement `build_radar(initial, final, labels)` in `riabita/ui/charts.py`
      with closed polygons, `range=[0, 100]`, and `line=dict(dash="dash")` on the
      baseline trace. [REQ-052]
- [ ] T081 [P] Implement `build_comparison(scores, labels)` as a sorted horizontal bar
      chart with numeric annotations. [REQ-056, REQ-085]
- [ ] T082 Chart tests asserting trace counts, closure, and the fixed radial range,
      with no Streamlit involved. → V-CHART

## Phase 9 — Streamlit application

- [ ] T090 Implement `riabita/ui/state.py`: session keys, progressive turn history,
      stable `round_id`, remaining credits, `player_id`, language, and cached district
      loading. [REQ-016, REQ-020, REQ-062]
- [ ] T091 Implement the progressive round orchestration described in
      [architecture.md](./architecture.md): one generator and event per turn,
      equal-credit benchmark allocations built before the event is drawn, and three
      cumulative simulations against the same event. [REQ-033, REQ-053, REQ-054]
- [ ] T092 Build the sidebar: language selector, district selector with localized
      warnings for skipped source records, baseline display, four turn sliders, cumulative/current totals and
      remainder, clear/restart controls, and the investment button gated on a positive
      total no greater than the remainder. [REQ-010, REQ-011, REQ-013, REQ-020, REQ-022, REQ-023, REQ-026]
- [ ] T093 Add the concentration warning when any allocation exceeds 60. [REQ-025]
- [ ] T094 Build the results section: before-and-after deltas, RIz and yield, the
      profile badge, and the itemized modifier list. [REQ-050, REQ-051, REQ-057, REQ-058]
- [ ] T095 [P] Render the radar chart and the event panel with per-dimension impact.
      [REQ-043, REQ-052]
- [ ] T096 [P] Render the benchmark comparison chart, including the highest saved
      score for the selected district when available. [REQ-056, REQ-056a]
- [ ] T097 Render the district map for valid geometry, hiding it with an explanation
      otherwise. [REQ-015]
- [ ] T098 Build the submission form and the leaderboard panel, locked until all
      credits are invested, with the district filter, empty state, and unavailable
      state. [REQ-060, REQ-063, REQ-066, REQ-067, REQ-071]
- [ ] T099 Write `src/main.py` as composition only: load settings, build the
      repository, and call the view functions. No game logic. [REQ-038]

## Phase 10 — Documentation and hardening

- [x] T100 Document setup, environment variables, tests, and the bundled shapefile
      data contract in `README.md`. [REQ-087]
- [ ] T101 Verify the layout on a narrow viewport; confirm columns stack and no
      `st.columns` weight list mismatches its unpacking. [REQ-084]
- [ ] T102 Audit chart and badge accessibility: labeled series, non-color-only
      encoding, explicit input labels. [REQ-085]
- [ ] T103 Audit every user-facing failure path for localized, non-technical copy and
      confirm no traceback or connection string reaches the UI. [REQ-071, REQ-086]
- [ ] T104 Confirm the boundary: import `riabita.engine.simulator` in a test that does
      not import Streamlit, GeoPandas, or SQLAlchemy. [REQ-038]
- [ ] T105 Run the full suite and record what was validated. → V-MAN

## Deferred

Do not start these without an explicit instruction.

- [ ] D01 Locale-aware number and date formatting. [REQ-005]
- [ ] D02 Per-player submission rate limiting. [REQ-072]

## Requirement mapping

| REQ | Tasks | Checks |
|---|---|---|
| REQ-001 | T060 | V-I18N |
| REQ-002 | T062, T092 | V-I18N, V-MAN |
| REQ-003 | T061 | V-I18N |
| REQ-004 | T060, T063 | V-I18N |
| REQ-005 | D01 | deferred |
| REQ-010 | T092 | V-UI |
| REQ-011 | T092 | V-UI |
| REQ-012 | T051 | V-DATA |
| REQ-012a | T001, T052 | V-DATA |
| REQ-013 | T052, T092 | V-DATA, V-MAN |
| REQ-014 | T050, T092 | V-DATA, V-MAN |
| REQ-015 | T053, T097 | V-DATA, V-MAN |
| REQ-016 | T090 | V-UI |
| REQ-020 | T092 | V-VAL, V-UI |
| REQ-021 | T014 | V-VAL |
| REQ-022 | T092 | V-UI, V-MAN |
| REQ-023 | T092 | V-UI, V-MAN |
| REQ-024 | T014, T027 | V-VAL, V-ENG |
| REQ-025 | T093 | V-MAN |
| REQ-026 | T092 | V-MAN |
| REQ-030 | T020 | V-ENG |
| REQ-031 | T020 | V-ENG |
| REQ-032 | T021 | V-ENG |
| REQ-033 | T022, T091 | V-ENG, V-UI |
| REQ-034 | T023 | V-ENG |
| REQ-035 | T024 | V-ENG |
| REQ-036 | T025, T026 | V-ENG |
| REQ-037 | T027 | V-ENG, V-EVT |
| REQ-038 | T027, T099, T104 | V-ENG |
| REQ-039 | T012, T027 | V-ENG, V-VAL |
| REQ-040 | T030 | V-EVT |
| REQ-041 | T030 | V-EVT |
| REQ-042 | T031 | V-EVT |
| REQ-043 | T095 | V-UI, V-MAN |
| REQ-044 | T031 | V-EVT |
| REQ-050 | T094 | V-UI |
| REQ-051 | T094 | V-UI |
| REQ-052 | T080, T095 | V-CHART |
| REQ-053 | T040, T041, T091 | V-STRAT, V-UI |
| REQ-054 | T042, T091 | V-STRAT, V-UI |
| REQ-055 | T042 | V-STRAT |
| REQ-056 | T081, T096 | V-CHART |
| REQ-057 | T026, T094 | V-ENG |
| REQ-058 | T024, T094 | V-ENG, V-UI |
| REQ-059 | T026, T094 | V-ENG |
| REQ-060 | T072, T098 | V-LB, V-MAN |
| REQ-061 | T070 | V-LB |
| REQ-062 | T090 | V-UI |
| REQ-063 | T074, T098 | V-LB |
| REQ-064 | T075 | V-LB |
| REQ-065 | T075 | V-LB |
| REQ-066 | T076, T098 | V-LB |
| REQ-067 | T076, T098 | V-LB |
| REQ-068 | T071 | V-LB |
| REQ-069 | T003, T011 | V-MAN |
| REQ-070 | T072 | V-LB |
| REQ-071 | T075, T098, T103 | V-LB, V-MAN |
| REQ-072 | D02 | deferred |
| REQ-080 | T010 | V-ENG |
| REQ-081 | T010, T027 | V-ENG, V-LB |
| REQ-082 | T012 | V-MAN |
| REQ-083 | T073 | V-LB |
| REQ-084 | T101 | V-MAN |
| REQ-085 | T081, T102 | V-CHART, V-MAN |
| REQ-086 | T061, T103 | V-I18N, V-MAN |
| REQ-087 | T100 | V-MAN |
