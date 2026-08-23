# Requirements

Normalized product contract for RIABITA ROMA. Every requirement has a stable ID.
[plan.md](./plan.md) maps each ID to implementation tasks;
[verification.md](./verification.md) maps each ID to acceptance checks.

Priority: **MVP** requirements must all ship for the app to be considered complete.
**Later** requirements are deferred but must not be architecturally blocked.

## Glossary

| Term | Meaning |
|---|---|
| RIz | Riabitability Index, the composite 0–100 score being maximized |
| M, C, T, S | Mobility, Culture, Tourism, Socio-demographic dimensions, always in this order |
| Dimension value | A 0–100 score for one of M, C, T, S |
| Allocation | Credits assigned to one dimension; the four allocations sum to exactly 100 |
| Round | One simulation: allocate, draw an event, score, compare, optionally submit |
| Event | A random shock applied once per round to all three strategies |

## Localization

| ID | Requirement | Priority |
|---|---|---|
| REQ-001 | The interface supports Italian and English. Italian is the default. | MVP |
| REQ-002 | The player switches language at any time. Switching re-renders all visible text, including results already on screen, without losing the current round. | MVP |
| REQ-003 | Every user-facing string resolves from a central catalog keyed by a stable identifier. No literal display text is embedded in view or engine code. | MVP |
| REQ-004 | Both catalogs define the same key set. A missing key is a test failure, not a runtime crash; at runtime an unresolved key falls back to Italian and then to the key itself. | MVP |
| REQ-005 | Numbers and dates render in a format appropriate to the active language. | Later |

## District selection

| ID | Requirement | Priority |
|---|---|---|
| REQ-010 | The player selects one Rome district before allocating. | MVP |
| REQ-011 | Selecting a district displays its baseline `M0`, `C0`, `T0`, `S0` values and its initial RIz. | MVP |
| REQ-012 | District data loads from an external GeoJSON path when one is configured. | MVP |
| REQ-012a | GeoJSON parsing uses the standard library. GeoPandas is an optional extra, imported only to reproject a file that declares a coordinate system other than EPSG:4326. | MVP |
| REQ-013 | When no path is configured, or the configured file is missing, unreadable, or fails schema validation, the app loads a bundled demo dataset and shows a clearly worded non-blocking notice that demo data is in use. | MVP |
| REQ-014 | The app labels demo indicator values and demo geometries as illustrative, not authoritative research data. | MVP |
| REQ-015 | The app renders a map highlighting the selected district when usable geometry exists. When geometry is absent or invalid, the app hides the map and explains why, without breaking the round. | MVP |
| REQ-016 | Loading district data is cached so that re-rendering does not re-read the file on every interaction. | MVP |

## Budget allocation

| ID | Requirement | Priority |
|---|---|---|
| REQ-020 | The player distributes exactly 100 credits across M, C, T, and S. | MVP |
| REQ-021 | Each allocation is an integer in the range 0–100 inclusive. | MVP |
| REQ-022 | The app continuously displays the allocated total and the remaining credits. | MVP |
| REQ-023 | The app blocks simulation while the total is not exactly 100 and states the exact corrective action, including the signed difference. | MVP |
| REQ-024 | The engine rejects any allocation set that fails validation, independently of the UI, and reports which rule failed. | MVP |
| REQ-025 | The app warns before simulating when an allocation exceeds 60, because that triggers the concentration penalty. The warning informs, it does not block. | MVP |
| REQ-026 | The player resets allocations to the default even split in one action. | MVP |

## Simulation

| ID | Requirement | Priority |
|---|---|---|
| REQ-030 | Investments apply direct and cross-dimensional effects using the impact matrix in [simulation-rules.md](./simulation-rules.md). | MVP |
| REQ-031 | Matrix effects are computed from the pre-investment dimension values and applied atomically. | MVP |
| REQ-032 | Tourism pressure reduces S when post-matrix T crosses the documented thresholds, using only the highest matching tier. | MVP |
| REQ-033 | Exactly one random event applies per round, after investment effects. | MVP |
| REQ-034 | Dimension values and the final RIz clamp to the range 0–100. | MVP |
| REQ-035 | The engine applies equilibrium, overtourism-gap, concentration, and diversification modifiers, and returns each modifier as an individually itemized, explainable record. | MVP |
| REQ-036 | The engine returns initial RIz, final RIz, urban yield, urban risk, and urban Sharpe ratio. | MVP |
| REQ-037 | The engine is deterministic: identical inputs and an identical seed produce identical output. | MVP |
| REQ-038 | The engine is pure. It performs no I/O, reads no global mutable state, and does not import Streamlit, GeoPandas, or database libraries. | MVP |
| REQ-039 | Simulating does not mutate its input arguments. | MVP |

## Events

| ID | Requirement | Priority |
|---|---|---|
| REQ-040 | The event catalog contains at least the five documented events: new transport line, cultural festival, tourist boom, housing crisis, and heatwave. | MVP |
| REQ-041 | Each event has a stable ID, a localized name, a localized description, and an impact vector in `(M, C, T, S)` order. | MVP |
| REQ-042 | Event selection uses the injected generator so a seeded run reproduces the same event. | MVP |
| REQ-043 | The results view names the drawn event, describes it, and shows its per-dimension impact. | MVP |
| REQ-044 | A specific event is selectable by ID for testing and scripted scenarios. | MVP |

## Results and comparison

| ID | Requirement | Priority |
|---|---|---|
| REQ-050 | The results view compares each dimension before and after, showing the signed delta. | MVP |
| REQ-051 | The results view shows initial RIz, final RIz, and the yield between them. | MVP |
| REQ-052 | A radar chart overlays the initial profile and the final profile on a fixed 0–100 radial axis. | MVP |
| REQ-053 | The app scores an AI benchmark strategy and a random benchmark strategy on the same district and the same event as the player. | MVP |
| REQ-054 | Benchmark strategies allocate without access to the drawn event. | MVP |
| REQ-055 | Both benchmark strategies produce allocations that satisfy the same validation rules as the player. | MVP |
| REQ-056 | A comparison chart ranks the player against both benchmarks by final RIz. | MVP |
| REQ-057 | The app assigns an urban profile from the final risk and yield, using the classification in [simulation-rules.md](./simulation-rules.md). | MVP |
| REQ-058 | The app itemizes every applied bonus and penalty with its localized reason and signed value. | MVP |
| REQ-059 | The results view shows the percentage change in RIz relative to the starting score, as required by section A.10 of the original research document. | MVP |

## Leaderboard

| ID | Requirement | Priority |
|---|---|---|
| REQ-060 | Completed rounds persist through SQLAlchemy. Development defaults to a project-local SQLite file; deployments use a configured PostgreSQL URL when scores must be shared across instances, browsers, and devices. | MVP |
| REQ-061 | Each entry records a generated player ID, a nickname, the district, the four allocations, the event ID, the final RIz, yield, risk, Sharpe, the rules version, and a UTC timestamp. | MVP |
| REQ-062 | The player ID is generated by the app and persists for the browser session. The player never supplies it. | MVP |
| REQ-063 | Nicknames are validated for length and character set and are rejected when invalid, with a localized message. | MVP |
| REQ-064 | The app persists only metrics that the engine computed during that request. It never accepts a score from the client. | MVP |
| REQ-065 | Submission is idempotent per round: re-running submission for the same round does not create duplicate entries. | MVP |
| REQ-066 | The leaderboard displays a bounded number of top entries, ranked by final RIz descending, with ties broken deterministically by earliest timestamp. | MVP |
| REQ-067 | The leaderboard is filterable by district. | MVP |
| REQ-068 | All database access goes through a repository interface, so the engine and views never build queries. | MVP |
| REQ-069 | An explicitly configured database URL comes from environment or secrets configuration. No credential or generated local SQLite file is committed to the repository or logged. | MVP |
| REQ-070 | All queries are parameterized through the ORM or bound parameters. String-built SQL is prohibited. | MVP |
| REQ-071 | If the database is unreachable, the round still completes and the results still display. The app shows a localized notice that scores are unavailable, and it does not leak connection details or stack traces to the user. | MVP |
| REQ-072 | Submission rate is limited per player to prevent trivial flooding. | Later |

## Quality and operations

| ID | Requirement | Priority |
|---|---|---|
| REQ-080 | All tunable game constants live in one configuration module, not scattered as inline literals. | MVP |
| REQ-081 | The rules carry a version identifier that is stored with each leaderboard entry, so score comparability survives rule changes. | MVP |
| REQ-082 | Public functions carry type annotations and docstrings, per the repository Python instructions. | MVP |
| REQ-083 | The engine, events, strategies, validation, and repository logic are unit tested without a running Streamlit server. | MVP |
| REQ-084 | The layout remains usable on a narrow viewport; controls stack instead of overflowing. | MVP |
| REQ-085 | Charts do not encode meaning by color alone. Each series carries a label or marker, and text meets normal contrast expectations. | MVP |
| REQ-086 | Error and empty states are localized and actionable, never raw exception text. | MVP |
| REQ-087 | The README documents setup, configuration variables, how to run the app, and how to run the tests. | MVP |

## Out of scope

Do not implement these without an explicit new instruction from the user.

- Sourcing or certifying authoritative RIz indicators or official Rome geometries.
- User registration, login, password reset, or any authenticated identity.
- Strong anti-cheat guarantees beyond server-side score computation.
- Deployment infrastructure, CI pipelines, containers, or hosting configuration.
- Multiplayer turns, persistent campaigns, or multi-round progression.
- Real-time data feeds or live municipal API integration.
