# Verification

Acceptance checks for RIABITA ROMA. [plan.md](./plan.md) maps every requirement to
one of these groups.

Follow the repository test conventions in `.github/instructions/python-tests.instructions.md`:
deterministic, isolated, no network, no real credentials, descriptive names.

## Commands

| Purpose | Command |
|---|---|
| Full suite | `pytest` |
| One group | `pytest tests/test_engine.py -q` |
| One case | `pytest tests/test_engine.py -k golden_example -q` |
| App smoke run | `streamlit run src/main.py --server.headless true` |

Run the narrowest relevant command while iterating, then the full suite before
reporting a phase complete.

## V-VAL — Validation

- Rejects three or five allocations with `allocation_length`.
- Rejects a non-integer allocation with `allocation_not_integer`.
- Rejects `-1` and `101` with `allocation_out_of_range`.
- Rejects sums of `99` and `101` with `allocation_sum`, and the reported difference is
  signed (`-1` and `+1`).
- Accepts `[100, 0, 0, 0]`: it is valid input that later earns a concentration penalty.
- Rejects a baseline dimension outside `0..100`.
- Dataclass instances reject attribute assignment.
- `run_simulation` leaves its input `District` and `Allocation` unchanged.

## V-ENG — Engine

**Golden example.** San Lorenzo `(55, 40, 80, 35)`, allocation `(25, 25, 25, 25)`, no
event. Assert with tolerance:

| Value | Expected |
|---|---|
| delta | `(4.0, 5.0, 4.25, 4.0)` |
| final dimensions | `(59.0, 45.0, 84.25, 38.5)` |
| risk | `17.5529` |
| modifier total | `-5` |
| `riz_initial` | `52.5` |
| `riz_final` | `51.6875` |
| yield | `-0.8125` |
| sharpe | `-0.0463` |
| profile | `stagnant` |

**Matrix.** Each single-dimension allocation of 100 credits produces exactly ten times
its matrix row. With baseline `(0, 0, 0, 0)` and allocation `(100, 0, 0, 0)` the result
is exactly `(10, 4, 3, 2)`. Confirm the negative coefficient: 100 credits into
socio-demographic lowers `T` by `1.0`.

**Pressure evaluated on the complete matrix result.** This is the easiest step to get
wrong, because the brief's sample code checks `T` after the tourism row but before the
socio-demographic row subtracts its `-0.1`. Use baseline `(50, 50, 65.2, 50)` with
allocation `(0, 0, 50, 50)`:

- `ΔT = 5 × 1.0 + 5 × (-0.1) = 4.5`, so post-matrix `T = 69.7` and **no** pressure applies.
- Checking `T` early would see `70.2`, cross the threshold, and wrongly cut `S` by `1.0`.

Assert `S` is unreduced. A test that only uses round baselines will not catch this.

**Boundaries.** One test per row; only the stated tier applies.

| Rule | Input | Expected |
|---|---|---|
| Tourism pressure | post-matrix `T = 70.0` | no reduction |
| Tourism pressure | post-matrix `T = 70.1` | `0.2` coefficient |
| Tourism pressure | post-matrix `T = 85.0` | `0.2` coefficient |
| Tourism pressure | post-matrix `T = 85.1` | `0.5` coefficient |
| Tourism pressure | `B_T = 0`, `T = 90` | no reduction |
| Gap | `T = S + 25.0` | `0` |
| Gap | `T = S + 25.1` | `-5` |
| Gap | `T = S + 40.0` | `-5` |
| Gap | `T = S + 40.1` | `-10` |
| Equilibrium | `σ = 9.9` | `+10` |
| Equilibrium | `σ = 10.0` | `+5` |
| Equilibrium | `σ = 15.0` | `0` |
| Equilibrium | `σ = 25.0` | `0` |
| Equilibrium | `σ = 25.1` | `-5` |
| Concentration | `max(b) = 60` | `0` |
| Concentration | `max(b) = 61` | `-5` |
| Concentration | two allocations above 60 | `-5`, applied once |
| Diversification | `k = 4` | `+5` |
| Diversification | `k = 3` | `+2` |
| Diversification | `k = 2` | `0` |

**Standard deviation.** `(0, 0, 0, 100)` gives population `σ = 43.30`, not the sample
value `50.0`. This test catches an accidental `ddof=1`.

**Clamping.** A baseline of `(98, 98, 98, 98)` with heavy investment clamps at `100`.
A baseline of `(2, 2, 2, 2)` with the heatwave event floors at `0`. Final RIz clamps
to `0..100` after modifiers.

**Order.** A case where a dimension exceeds `100` before the event and would fall back
under `100` after it yields a different score if clamping happens early. Assert the
documented order.

**Zero risk.** Four identical final dimensions give `risk == 0.0` and `sharpe == 0.0`
with no exception raised.

**Profile order.** A high-RIz, high-risk run with a positive yield is `vulnerable`. A
low-risk run with a yield of exactly `0.0` is `stagnant`, not `resilient`.

**Determinism.** Two runs with the same seed produce identical results; a different
seed produces a different event across a reasonable sample.

**Purity.** A test module that imports only `riabita.engine.simulator` passes with no
Streamlit, GeoPandas, or SQLAlchemy import anywhere in its import graph.

**Version.** `SimulationResult.rules_version` equals `config.RULES_VERSION`.

## V-EVT — Events

- The catalog contains the five documented IDs with the exact impact vectors.
- Every event resolves a name and description key in both catalogs.
- `draw_event` with a fixed seed returns the same event every time.
- `draw_event` covers all five events across many seeded draws.
- `get_event` returns `None` or raises a defined error for an unknown ID; it never
  returns a partially built event.
- Applying `tourist_boom` adds exactly `(0, 0, +10, -5)` and does not re-trigger
  tourism pressure.

## V-STRAT — Benchmark strategies

- `ai_allocation((55, 40, 80, 35))` returns `[25, 25, 10, 40]`.
- The AI result always sums to `100`, stays within `0..60`, and passes validation for
  every district in the demo dataset.
- The AI skips the lift when it would breach `0` or `60`, and still sums to `100`.
- `random_allocation` sums to exactly `100` across many seeded draws, with every value
  within `0..100`.
- `random_allocation` is reproducible under a fixed seed.
- Neither function accepts an event argument, verified by signature inspection.

## V-DATA — District loading

Use `tmp_path` fixtures; never a machine-specific path.

- A valid GeoJSON loads all districts with `is_demo=False`.
- A missing path falls back to demo data with `is_demo=True`.
- Malformed JSON falls back to demo data and raises no unhandled exception.
- A feature missing `M0` is dropped, and the reason is recorded.
- A feature with `T0 = 120` is dropped as out of range.
- A file with zero valid features falls back to demo data.
- Null geometry loads successfully with values intact and geometry `None`.
- A non-`EPSG:4326` source reprojects.
- The demo dataset parses, contains the ten documented districts, and every value is
  within `0..100`.

## V-I18N — Localization

- `it` and `en` have identical key sets; the assertion message lists the differing
  keys.
- No value is empty or whitespace.
- Keys with placeholders declare the same placeholder names in both languages.
- An unknown key resolves to Italian, then to the key itself, without raising.
- Every event ID, modifier ID, profile ID, and validation error identifier has a
  corresponding key in both catalogs.

## V-CHART — Charts

- The radar figure has exactly two traces.
- Each radar trace repeats its first value and first category at the end.
- The radial axis range is exactly `[0, 100]`.
- The baseline trace sets `dash` inside `line`.
- The comparison figure contains three labeled entries sorted by RIz descending, each
  with a numeric annotation.
- Both builders return a figure without importing Streamlit.

## V-LB — Leaderboard

Run pure ordering cases against `InMemoryLeaderboardRepository` and persistence cases
against temporary file-backed SQLite. No test requires a live database server.

- `submit_result` builds an entry whose metrics equal the `SimulationResult` values.
- Submitting the same `round_id` twice stores one entry.
- `top` returns at most the limit, ordered by RIz descending.
- Equal RIz values order by earliest `created_at`.
- Filtering by district returns only that district.
- An empty repository returns an empty list, not `None`.
- Nickname validation accepts `Ana`, `mario_rossi`, and `Roma 2024`; rejects `ab`,
  a 25-character string, and `<script>alert(1)</script>`.
- A nickname or district value containing SQL metacharacters is stored and retrieved
  literally, proving parameterization.
- A repository that raises an operational error surfaces `LeaderboardUnavailable`, and
  the message contains no connection string.
- The stored `rules_version` matches the result's version.
- With no configured URL, settings resolve to the project-local SQLite database.
- An explicit SQLite URL is preserved and enables the leaderboard.
- A score written by one SQLite repository instance is visible after closing it and
  opening a second instance against the same file.

## V-UI — Application

Use `streamlit.testing.v1.AppTest` so these run headless in the suite.

- The app starts and renders without exception using demo data and an isolated local
  SQLite database.
- Selecting a district displays its baseline values.
- A total other than `100` disables the simulate button.
- A total of exactly `100` enables it.
- Running a round produces exactly one event and three results that all reference that
  same event ID.
- Benchmark allocations are computed before the event is applied, verified by asserting
  the same benchmark allocation across two runs that differ only in the drawn event.
- Re-rendering without a new simulation does not change the event or the scores.
- `player_id` is stable within a session and absent from any user input widget.
- With no database URL configured, the local SQLite leaderboard renders and accepts
  scores. With an unreachable configured database, results still render and the
  leaderboard panel shows its unavailable state.

## V-MAN — Manual review

Perform before declaring the project complete.

- [ ] Play a full round in Italian and in English; all visible text switches and the
      round survives the switch.
- [ ] Switch language after viewing results; the results stay and re-render translated.
- [ ] Narrow the browser to a phone width; columns stack and nothing overflows.
- [ ] Confirm the demo-data notice appears with no configured GeoJSON, and disappears
      with a valid one.
- [ ] Select a district with null geometry; the map hides with an explanation and the
      round still completes.
- [ ] Stop the database, run a round, and confirm results still render with a localized
      notice and no traceback.
- [ ] Submit a score from two different browsers and confirm both appear in the same
      leaderboard.
- [ ] Double-click submit and confirm only one entry is created.
- [ ] Grep the diff for hardcoded display strings, credentials, and game constants
      outside `config.py`.
- [ ] Confirm the README instructions work from a clean checkout.
