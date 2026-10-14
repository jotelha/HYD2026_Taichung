# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static GitHub Pages site (served from the branch root, `.nojekyll`) with research data and an interactive map of the former Taichung City and the Shuinan Economic and Trade Park, for #HackYourDistrict 2026. There is no package manager, test suite or linter. The README is the authoritative user-facing doc (English first, then a Chinese section that mirrors it — keep both in step when changing documented behaviour).

## Commands

```sh
python3 scripts/build_map.py                 # regenerate index.html and map/index.html (stdlib only)
python3 scripts/build_map.py --fragment f.html  # also write a body-only map fragment without the basemap
python3 scripts/georef_plan.py               # DXF plan trace -> data/derived/shuinan_detailed_plan_traced.geojson
python3 scripts/register_plan.py             # refit plan to OSM roads (needs numpy scipy shapely)
python3 scripts/locate_projects.py           # -> data/derived/project_locations.geojson
python3 -m http.server 8000                  # local preview (tiles often fail from file://)
node scripts/check_basemap.mjs http://localhost:8000/map/index.html  # Playwright smoke test of the basemap
```

`fetch_roads.py` / `fetch_landmarks.py` query the Overpass API, which the usual build environment cannot reach; they run in the "Fetch OSM road network" GitHub Actions workflow (manual dispatch), which also runs `locate_projects.py` and `build_map.py` and commits the results. "Check basemap" runs `check_basemap.mjs` in CI.

## Architecture

**Build pipeline.** `templates/basemap.html` and `templates/index.html` are self-contained HTML/CSS/JS fragments (no `<html>`/`<head>`). `build_map.py` loads everything in `data/raw` and `data/derived`, inlines it as one JSON payload, substitutes markers (`/*__DATA__*/null`, `/*__BASEMAP__*/true`, `<!--__EYEBROW__-->`, and landing-page markers built in `landing_values`), and wraps each in a page skeleton. `fill()` aborts if a marker is missing from a template. The generated `index.html` and `map/index.html` are committed — always rebuild and commit them after touching templates or data; never hand-edit them.

**Data flow.** `data/raw/` is source data; `data/derived/` is produced by scripts:
- DXF plan trace (A3 sheet mm, no CRS) → `georef_plan.py` applies a similarity transform (`SCALE`, `ROTATION_DEG`, `TRANSLATION_M` constants) → plan GeoJSON. Those constants come from `register_plan.py` (fit to OSM road centrelines) or from the map's "Adjust position → Copy parameters" panel.
- `locate_projects.py` places each row of `shuinan_major_projects_2026.csv` using, in order: a typed OSM landmark match, a named road junction, a traced plan block, then a `reference_points.csv` coordinate. Per-project rules live in its `RULES` dict.
- `build_map.py` treats the old-downtown and Xitun–Beitun files as subsets of the former-city files: it reads only the former-city files and warns if a subset drifts. Old downtown = districts flagged `old_downtown`. Per-project impact notes come from `shuinan_project_impacts.csv` (long format: one row per project × impact key in `IMPACT_KEYS`; titles live in the template's `IMPACTS` list). Project status chips come from `PROJECT_PHASE` (keyed by `project_zh`); the landing-page download table from `DOWNLOADS`.

**Map page (`templates/basemap.html`).** Hand-rolled SVG overlay in Web Mercator (districts, villages, roads, plan, projects) layered over a MapLibre GL vector basemap (OpenFreeMap `positron`, labels switched to `name:en`), with a raster OSM tile fallback. The SVG and MapLibre must stay aligned within a pixel; `window.__hydBasemap` exposes mode/map for the smoke test. Basemap sources are `VECTOR_STYLE` / `TILE_URL`; keep the on-map attribution when changing them.

**Styling.** Both templates share style/theme switching: `data-style` on `:root` (none = "Deck", `"program"`) × `data-theme` (`light` | `white` | `dark`, none = follow system), persisted in `localStorage` keys `hyd2026-style` / `hyd2026-theme` so the landing page and map stay in sync. Style changes generally need to be made in both templates.

## Conventions

- UI is English-first with Chinese secondary; Chinese text goes in spans with `lang="zh-Hant-TW"`.
- Coordinates are WGS84 lon/lat (CRS84). Village boundaries are simplified — areas come from the attribute CSV, not geometry. Futai Village (富台里) has no geometry and is drawn as a dashed circle by design.
- Python scripts that ship in the build/CI path use only the standard library (`register_plan.py` is the exception).
- OSM data is ODbL: keep "© OpenStreetMap contributors" credits.
