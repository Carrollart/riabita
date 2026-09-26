# RIABITA ROMA

An urban simulation game that turns the **Riabitability Index (RIz)** into an
interactive decision-making experience. You play a public decision-maker,
allocate a fixed budget across a Rome district, absorb a random shock, and try to
build a balanced city rather than a lopsided one.

## Core idea

Each district is described by four dimensions, always in this order:

| Dimension | Meaning |
|---|---|
| Mobility (M) | Accessibility and transport |
| Culture (C) | Cultural vitality and local identity |
| Tourism (T) | Attractiveness and visitor flow |
| Socio-demographic (S) | Resident quality of life |

You invest a total of **100 credits** across the four dimensions over one or
more turns. Every turn may spend any positive number of the remaining credits,
updates the district immediately, and draws a random event. The final score
rewards balance through equilibrium and diversification bonuses while
penalizing concentration.

Every turn is scored against an AI planner and random choices using the **same
district, the same number of credits, and the same event**. A completed
100-credit game can then be submitted to the leaderboard.

### GWR-aware AI planner

The AI Planner uses the CArME Geographically Weighted Regression (GWR) profiles
to model local spatial priorities while preserving the game’s official scoring
rules. For each progressive turn it:

1. searches valid allocations for the credits available in that turn;
2. maximizes the authoritative game score, including modifiers; and
3. uses the active GWR projection of the final `(M, C, T, S)` dimensions only to
  break equal-score ties.

The supplied profiles cover 5, 10, 15, 20, 25, and 30-minute walking bands.
`A0` uses 5 minutes; numeric A/B/C district IDs use the lower band for suffixes
0–4 and the upper band for higher suffixes. Composite IDs, `Studio_*`, malformed
IDs, and unknown IDs use the 15-minute fallback profile. The active profile is
shown in the sidebar and main dashboard after you select a district.

The planner is deterministic, event-blind, and progressive: it uses the AI’s
current dimensions and cumulative allocation, chooses before the shared event,
and spends the same number of credits as the player. The complete coefficient
matrix is maintained in [`strategies.py`](src/riabita/strategies.py) and described
in [GWR Coefficients and Spatial AI Planning Strategy](docs/GWR%20Coefficients%20and%20Spatial%20AI%20Planning%20Strategy.md).

## Prerequisites

Use Python **3.11 or newer**, as required by `pyproject.toml`. From the project
root, create and activate a virtual environment, then install the dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Quick start

```bash
.venv/bin/python -m streamlit run src/main.py
```

Then open the URL shown by Streamlit, normally `http://localhost:8501`. Do not
start the application with `python src/main.py`: the entry point detects this
case and prints the Streamlit command to use.

The app loads the bundled CArME shapefile and uses a local SQLite leaderboard at
`.data/riabita.sqlite3`. The directory and schema are created on first use.

## Configuration

All settings are optional. The application resolves them from environment
variables first, then from `.streamlit/secrets.toml`, and finally uses the
defaults shown below. Environment variables therefore override values in the
configuration file.

| Variable | Purpose | Default |
|---|---|---|
| `RIABITA_DATABASE_URL` | SQLAlchemy URL for SQLite or PostgreSQL | `sqlite+pysqlite:///<project>/.data/riabita.sqlite3` |
| `RIABITA_DISTRICTS_PATH` | Path to a district shapefile override | `src/riabita/data/zona_carme_riabita/zone_carme_riabita.shp` |
| `RIABITA_DEFAULT_LANGUAGE` | Starting language (`it`, `en`, or `fr`) | `it` |
| `RIABITA_LEADERBOARD_LIMIT` | Rows shown in the leaderboard | `10` |

The default SQLite file persists scores between local app restarts. You can also
point development at another SQLite file:

```bash
export RIABITA_DATABASE_URL="sqlite+pysqlite:///./my-leaderboard.sqlite3"
```

For a deployed, multi-instance leaderboard, override it with PostgreSQL:

```bash
export RIABITA_DATABASE_URL="postgresql+psycopg://user:password@host:5432/riabita"
```

The schema is created on first use for either database. Never commit credentials or
local score files; `.env`, `.streamlit/secrets.toml`, and `.data/` are ignored by git.

### Configuration file

To configure the application without environment variables, copy
`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and edit the values:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

The file uses TOML syntax and is read by `config.py` through Streamlit Secrets:

```toml
RIABITA_DATABASE_URL = "sqlite+pysqlite:///./.data/riabita.sqlite3"
RIABITA_DISTRICTS_PATH = "./src/riabita/data/zona_carme_riabita/zone_carme_riabita.shp"
RIABITA_DEFAULT_LANGUAGE = "it"
RIABITA_LEADERBOARD_LIMIT = 10
```

Do not commit `.streamlit/secrets.toml` when it contains credentials or machine-
specific paths. The example file contains only safe placeholder values.

### CArME district data

The app reads `src/riabita/data/zona_carme_riabita/zone_carme_riabita.shp`
directly. Keep its companion `.dbf`, `.shx`, `.prj`, and `.cpg` files beside it.
The DBF embeds district codes, names, and indicators `MO`, `CO`, `TO`, and `SO`.
These normalized values are scaled from `0..1` to the game's `0..100` dimension
range in `(M, C, T, S)` order. Geometry is reprojected in memory to `EPSG:4326`.

The shapefile has 27 records. A0 has no numeric dimension values and is skipped
with a localized warning, leaving 26 playable districts. If the shapefile cannot
be read or contains no valid districts, the app reports an error; it does not
load GeoJSON or demo data. `RIABITA_DISTRICTS_PATH` can point to another complete
ESRI shapefile. GeoPandas is installed with the standard requirements.

`src/riabita/data/loader.py` is the only district reader. The map remains an
exploratory view; the district selectbox is the authoritative selection control.

## Running the tests

```bash
.venv/bin/python -m pytest
```

The suite needs no external database, no network, and no running Streamlit server.
It uses temporary SQLite files and a headless `AppTest` smoke test exercises the
real application.

```bash
.venv/bin/python -m pytest tests/test_engine.py -q      # one module
.venv/bin/python -m pytest -k golden_example -q         # one case
```

## Project layout

```
src/
├── main.py                  Streamlit entry point, composition only
└── riabita/
    ├── config.py            Every tunable constant and runtime setting
    ├── i18n.py              Translation catalogs and lookup
    ├── domain/              Frozen types, errors, validation
    ├── engine/              Simulation pipeline and scoring
    ├── events.py            Random event catalog
    ├── strategies.py        AI and random benchmarks
    ├── data/                CArME shapefile loading
    ├── leaderboard/         SQLAlchemy models, repository, service
    └── ui/                  Session state, charts, Streamlit views
tests/                       Mirrors the module layout
```

The engine is pure: no I/O, no global state, and no imports of Streamlit,
GeoPandas, or SQLAlchemy. A test enforces that boundary in a subprocess.

## Adding a language

Add one entry to `CATALOG` in [src/riabita/i18n.py](src/riabita/i18n.py) with the
same key set as the others and a display name in `LANGUAGE_NAMES`. The test
suite fails if any key or placeholder is missing, so nothing can silently fall
back to another language.

## Rules and documentation

The authoritative specification lives in the implementation skill:

- [Game rules and formulas](.github/skills/riabita-implementation/references/simulation-rules.md)
- [Requirements](.github/skills/riabita-implementation/references/requirements.md)
- [Architecture](.github/skills/riabita-implementation/references/architecture.md)
- [Implementation plan](.github/skills/riabita-implementation/references/plan.md)
- [Verification](.github/skills/riabita-implementation/references/verification.md)

The original research documents in [docs/](docs/) are historical context. Where
they disagree with the references above, the references win.
