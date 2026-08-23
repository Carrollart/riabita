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

Every turn is scored against an AI planner and a random visitor using the **same
district, the same number of credits, and the same event**. A completed
100-credit game can then be submitted to the leaderboard.

## Quick start

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run src/main.py
```

The app runs immediately with bundled demo data and a local SQLite leaderboard at
`.data/riabita.sqlite3`. The directory and schema are created on first use.

## Configuration

All settings are optional and resolve from environment variables first, then
Streamlit secrets.

| Variable | Purpose | Default |
|---|---|---|
| `RIABITA_DATABASE_URL` | SQLAlchemy URL for SQLite or PostgreSQL | `sqlite+pysqlite:///<project>/.data/riabita.sqlite3` |
| `RIABITA_DISTRICTS_PATH` | Path to an official district GeoJSON | unset, demo data used |
| `RIABITA_DEFAULT_LANGUAGE` | Starting language (`it` or `en`) | `it` |
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
