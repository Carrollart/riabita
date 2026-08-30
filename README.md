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

The app runs immediately with bundled demo data and a local SQLite leaderboard at
`.data/riabita.sqlite3`. The directory and schema are created on first use.

## Configuration

All settings are optional. The application resolves them from environment
variables first, then from `.streamlit/secrets.toml`, and finally uses the
defaults shown below. Environment variables therefore override values in the
configuration file.

| Variable | Purpose | Default |
|---|---|---|
| `RIABITA_DATABASE_URL` | SQLAlchemy URL for SQLite or PostgreSQL | `sqlite+pysqlite:///<project>/.data/riabita.sqlite3` |
| `RIABITA_DISTRICTS_PATH` | Path to a district GeoJSON override | Generated CArME GeoJSON |
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
RIABITA_DISTRICTS_PATH = "./data/quartieri.geojson"
RIABITA_DEFAULT_LANGUAGE = "it"
RIABITA_LEADERBOARD_LIMIT = 10
```

Do not commit `.streamlit/secrets.toml` when it contains credentials or machine-
specific paths. The example file contains only safe placeholder values.

### CArME district map

The repository includes the tabular source at `src/riabita/data/carme_indicators.csv` and a
reproducible generated map at `src/riabita/data/carme_zones.geojson`. Regenerate
the map after changing the CSV:

```bash
PYTHONPATH=src .venv/bin/python -m riabita.data.convert_csv_to_geojson \
  src/riabita/data/carme_indicators.csv src/riabita/data/carme_zones.geojson
```

The converter projects each zone around the Velabro anchor using the documented
bearing and walking-distance heuristics. The polygons are visual approximations,
not authoritative cadastral boundaries. The CSV contains `Mean_RIz` but does not
contain the four simulator baselines, so `M0`, `C0`, `T0`, and `S0` are transparent
modeled proxy estimates. The generated properties identify them with
`baseline_source = "modeled_proxy"`.

The app uses this generated GeoJSON by default. Set `RIABITA_DISTRICTS_PATH` to
load another GeoJSON; an invalid or missing source still falls back to bundled
demo data.

The implementation is split across these modules:

- `src/riabita/data/convert_csv_to_geojson.py` reads the CSV, applies the
  Velabro placement table, derives the labeled proxy baselines, and writes the
  FeatureCollection.
- `src/riabita/data/loader.py` validates and loads GeoJSON into `District`
  objects. It remains the only runtime GeoJSON reader.
- `src/riabita/ui/charts.py` builds the token-free Plotly Mapbox overview, and
  `src/riabita/ui/views.py` renders it.
- `src/main.py` composes the overview map with the existing selectbox. The map
  is exploratory; the selectbox remains the authoritative district selector.

### Supplying real district data

Point `RIABITA_DISTRICTS_PATH` at a GeoJSON whose features carry these
properties:

```json
{
  "type": "Feature",
  "properties": { "nome": "San Lorenzo", "M0": 55, "C0": 40, "T0": 80, "S0": 35 },
  "geometry": { "type": "Polygon", "coordinates": [[[12.51, 41.89], "..."]] }
}
```

`M0`, `C0`, `T0` and `S0` must each be between 0 and 100. Invalid features are
skipped with a warning; an unusable file falls back to demo data so a round can
always start. Files are expected in `EPSG:4326`. To load a file in another
coordinate system, install the optional extra:

```bash
.venv/bin/python -m pip install -e ".[geo]"
```

> The bundled districts are **illustrative placeholders**, not authoritative RIz
> research output. Their geometries are simplified rectangles.

### Converting a Shapefile to GeoJSON

The application reads GeoJSON files. To read a Shapefile or convert it to
GeoJSON, install the optional GeoPandas dependency:

```bash
.venv/bin/python -m pip install -e ".[geo]"
```

Keep all files belonging to the Shapefile in the same directory, especially:

```text
quartieri.shp
quartieri.shx
quartieri.dbf
quartieri.prj
```

Convert the file with this Python command:

```bash
.venv/bin/python - <<'PY'
import geopandas as gpd

districts = gpd.read_file("quartieri.shp")
districts = districts.to_crs("EPSG:4326")
districts.to_file("quartieri.geojson", driver="GeoJSON")
PY
```

The `.prj` file identifies the source coordinate system. Reprojecting to
`EPSG:4326` makes the result compatible with the district loader. The resulting
GeoJSON must contain the properties `nome`, `M0`, `C0`, `T0`, and `S0`, with each
dimension value between 0 and 100. Configure it with `RIABITA_DISTRICTS_PATH` in
the environment or in `.streamlit/secrets.toml`.

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
    ├── data/                GeoJSON loading and demo districts
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
