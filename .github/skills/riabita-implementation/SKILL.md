---
name: riabita-implementation
description: "Implementation guide for RIABITA ROMA, the multilingual Streamlit urban simulation game built on the Riabitability Index (RIz). Use when implementing, extending, reviewing, or debugging the simulation engine, impact matrix, overtourism and equilibrium penalties, random events, AI and random benchmark strategies, district GeoJSON loading, Plotly radar and comparison charts, Italian/English/others localization, or the SQLite/PostgreSQL leaderboard. Provides normalized game rules, module contracts, a phased task plan, and acceptance tests."
argument-hint: "Optional: phase number or module to implement (for example 'phase 2' or 'engine')"
---

# RIABITA ROMA Implementation Guide

Build RIABITA ROMA: a gamified urban simulation where a player allocates a fixed
budget of 100 credits over one or more progressive turns across four dimensions
of a Rome district and maximizes the Riabitability Index (RIz) under penalties,
bonuses, and random event shocks.

## When to Use

- Implementing any module of the application from scratch.
- Changing simulation math, thresholds, bonuses, penalties, or scoring.
- Adding districts, events, translations, charts, or leaderboard behavior.
- Reviewing a change for rule correctness or architectural boundaries.

## Source of Truth

[docs/DOC-20260609-WA0016.md](../../../docs/DOC-20260609-WA0016.md) is the original
Italian research document and the highest authority on intent. It is historical
context only; its inline code samples may contain defects and leave several
constants undefined.

**The references in this skill override both sources wherever they disagree.** Never
copy code verbatim out of the brief.

## References

Load only what the current task needs.

| Reference | Load when |
|---|---|
| [requirements.md](./references/requirements.md) | Scoping work, tracing a feature, checking what is out of scope |
| [simulation-rules.md](./references/simulation-rules.md) | Touching engine math, thresholds, events, or scoring |
| [architecture.md](./references/architecture.md) | Creating modules, types, config, or persistence |
| [data-and-ui.md](./references/data-and-ui.md) | Working on GeoJSON loading, localization, layout, or charts |
| [plan.md](./references/plan.md) | Choosing what to build next; phased task checklist |
| [verification.md](./references/verification.md) | Writing or running tests before declaring work done |

## Procedure

1. **Locate the work.** Open [plan.md](./references/plan.md) and pick the lowest
   unfinished phase. Phases are ordered by dependency; do not skip ahead.
2. **Load the rules.** For engine or scoring work, read
   [simulation-rules.md](./references/simulation-rules.md) in full before editing.
   It is the only authoritative statement of constants and operation order.
3. **Respect the boundaries.** Follow the module map and dependency direction in
   [architecture.md](./references/architecture.md). The engine stays pure: no
   Streamlit, no GeoPandas, no database, no direct `random` calls.
4. **Implement one phase.** Keep changes scoped to that phase's task list.
5. **Test it.** Add the tests listed for that phase in
   [verification.md](./references/verification.md) and run them.
6. **Report.** State which phase completed, what was validated, and what remains.

## Non-Negotiable Rules

These cause silent, hard-to-detect bugs if violated.

- **Vector order is always `(M, C, T, S)`** — Mobility, Culture, Tourism,
  Socio-demographic. Every array, tuple, and matrix row/column uses this order.
- **Impact matrix effects are computed atomically** from the original dimension
  values, then applied. Never mutate `M` and then use the new `M` to compute `C`.
- **Operation order is fixed**: validate → matrix → overtourism pressure → event →
  clamp → modifiers → RIz → metrics. See
  [simulation-rules.md](./references/simulation-rules.md).
- **Randomness is injected**, never called at module level. The engine accepts a
  seeded generator so every simulation is reproducible in tests.
- **One event per turn, shared by all three strategies.** The player, AI, and
  random benchmarks receive the same turn budget and are scored against the same
  drawn event; none of the strategies may see it before allocating.
- **Scores are computed server-side.** The leaderboard persists results the engine
  produced in that request; it never trusts a score value supplied by the client.

## Clarify Before Guessing

Stop and ask the user when a task requires any of these, which this skill
intentionally does not decide:

- Authoritative RIz indicator values or official Rome district geometries.
- Replacing a documented assumption in
  [simulation-rules.md](./references/simulation-rules.md) with a research-backed
  constant.
- Adding user accounts, deployment infrastructure, or anti-cheat guarantees.

## CArME Rome data

The repository includes `src/riabita/data/carme_indicators.csv` and the
generated `src/riabita/data/carme_zones.geojson`. Regenerate the 35-feature map
with `riabita.data.convert_csv_to_geojson.generate_carme_geojson()` after
changing the table.

The converter anchors Velabro at `41.889, 12.482`, places zones with the
supplied bearing/distance heuristics, and creates closed octagonal WGS84
polygons. These are visualization approximations, not cadastral boundaries.

The CSV provides `Mean_RIz` and territorial indicators but no authoritative
`M0`, `C0`, `T0`, and `S0` values. The converter derives proxy baselines and
marks them `baseline_source: "modeled_proxy"`; do not describe them as official
research measurements. Preserve `(M, C, T, S)` ordering and keep this mapping
in the data layer, outside the pure simulation engine.
