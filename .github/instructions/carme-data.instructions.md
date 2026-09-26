---
applyTo: "src/riabita/data/**/*.py,tests/test_loader.py"
---
# CArME data guidance

- Use `src/riabita/data/zona_carme_riabita/zone_carme_riabita.shp` and its shapefile sidecars as the only district source.
- The DBF fields `zc_code`, `nome`, `MO`, `CO`, `TO`, and `SO` provide IDs, names, and embedded dimension indicators. Preserve `(M, C, T, S)` order and scale normalized values by 100.
- Reproject source geometry to `EPSG:4326` in memory. Do not read or generate GeoJSON, join a CSV, or synthesize missing indicators or geometry.
- Skip invalid records with localized warnings. A0 has no dimension indicators and is excluded, leaving 26 playable zones.
- `RIABITA_DISTRICTS_PATH` may override the default only with another shapefile. Missing or invalid data raises `DataSourceError`; there is no demo fallback.
- Keep filesystem access in the data layer. The simulation engine must not import GeoPandas or Streamlit.
