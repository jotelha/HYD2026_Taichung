# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The Boba Index ("Built On Belonging and Authenticity", shown as a tagline under the page title): a prototype for rating Taichung night markets on authenticity and belonging, built for #HackYourDistrict 2026 out of an earlier research map of the former Taichung City and the Shuinan Economic and Trade Park. It is a static GitHub Pages site (served from the root of branch `2026-10-15-HYD2026`, `.nojekyll`) whose single page maps the OSM markets and night markets in the eight districts. No real index scores exist yet; Feng Chia carries mock booths with random scores. There is no package manager, test suite or linter. The README is the authoritative user-facing doc (English first, then a Chinese section that mirrors it — keep both in step when changing documented behaviour).

## Commands

```sh
python3 scripts/build_map.py                 # regenerate index.html and the map/index.html redirect (stdlib only)
python3 scripts/build_map.py --fragment f.html  # also write a body-only map fragment without the basemap
python3 scripts/fengjia_extent.py            # -> data/derived/fengjia_night_market_extent.geojson (needs shapely + Overpass)
python3 scripts/mock_booths.py               # -> data/derived/fengjia_booths_mock.geojson (MOCK booths, random scores, fixed seed)
python3 -m http.server 8000                  # local preview (tiles often fail from file://)
node scripts/check_basemap.mjs http://localhost:8000/  # Playwright smoke test of the basemap
```

`fetch_roads.py` / `fetch_landmarks.py` query the Overpass API, which the usual build environment cannot reach; they run in the "Fetch OSM road network" GitHub Actions workflow (manual dispatch), which also runs `locate_projects.py` and `build_map.py` and commits the results. Overpass does answer from some machines when the `fetch_roads.USER_AGENT` header is sent (`fetch_roads.overpass()`). "Check basemap" runs `check_basemap.mjs` in CI; it measures alignment at the Feng Chia marker and clicks the first night market's "Show on map" button.

## Architecture

**Build pipeline.** `templates/basemap.html` is a self-contained HTML/CSS/JS fragment (no `<html>`/`<head>`). `build_map.py` reads the district boundaries and the markets, inlines them as one JSON payload, substitutes markers (`/*__DATA__*/null`, `/*__BASEMAP__*/true`, `<!--__EYEBROW__-->`), wraps the result in a page skeleton and writes `index.html`; `map/index.html` (the map's old address) becomes a redirect. `fill()` aborts if a marker is missing from the template. The generated files are committed — always rebuild and commit them after touching the template or data; never hand-edit them.

**Data flow.** `data/raw/` is source data; `data/derived/` is produced by scripts. The page uses only `former_city_8_districts.geojson`, `landmarks_osm.geojson`, `fengjia_night_market_extent.geojson` and `fengjia_booths_mock.geojson`:
- `load_markets()` in `build_map.py` keeps `amenity=marketplace` features plus untagged features named …夜市, drops features inside another market's footprint or repeating a nearby name, clips to the districts and attaches each night market's OSM outline (`foot`). The Feng Chia entry also gets the street-buffer extent from `fengjia_extent.py` (one-off, not in CI; its street stretches and buffer are constants at the top). The extent file's first feature is the polygon; the rest are the clipped street centrelines (`kind: "street"`).
- `mock_booths.py` lays mock booths along those centrelines and gives each a Boba Index (0.0–5.0) sampled around a smooth field of seeded hot and cold spots (`FIELD_*`, centres saved as `score_field`) and an invented zh/en stall name (pattern parts in `OWNERS` / `DESCRIPTORS` / `DISHES`, own seed so scores stay put). Names must never contain a real stall name: extend `REAL_STALLS` if new real names turn up. `load_booths()` inlines them as compact rows `[lon, lat, bearing, score, street #, name_zh, name_en]`; the template draws true-size rects coloured on viridis (`RAMP`, same stops in every theme) once they are ≥ 4 px long. Everything from this file must stay labelled as mock in the UI.
- The heat map is computed in the browser from the booth scores only (Gaussian-weighted mean on a 2 m grid, `buildHeat()` / `kernelAt()`, bandwidth from the slider), drawn as an SVG `<image>` in world units and clipped to the Feng Chia extent (`#heat-clip`). It uses `HEAT_RAMP` (plasma), stretched to the min/max of the fully weighted cells and shown in the heat-map key; the booths keep `RAMP` (viridis, fixed 0–5). Keep it independent of `score_field`: real booth data will not have one.
- Booth search (`searchBooths()` / `selectBooth()`) matches every typed word against each booth's `hay` (names, id, street). The selection ring `#g-booth-sel` is screen-space and drawn in `drawBooths()`. Headless checks of anything that zooms with animation need `--force-prefers-reduced-motion`, or headless Chrome hangs on the animation frames.
- The village, Shuinan plan, zoning, project, reference-point and road data and their scripts (`georef_plan.py`, `register_plan.py`, `locate_projects.py`, `fetch_roads.py`) are kept from the research map but no longer reach the page.

**Map page (`templates/basemap.html`).** Hand-rolled SVG overlay in Web Mercator (district fills and outlines, night-market areas, market dots) layered over a MapLibre GL vector basemap (OpenFreeMap `positron`, labels switched to `name:en`), with a raster OSM tile fallback. The SVG and MapLibre must stay aligned within a pixel; `window.__hydBasemap` exposes mode/map for the smoke test. Basemap sources are `VECTOR_STYLE` / `TILE_URL`; keep the on-map attribution when changing them. World-space shapes go in `#world` (scaled by the view transform); markers and labels are screen-space groups repositioned in `draw()`. The legend is a `<details>` overlay in the map's top-left corner (`#map-legend`; the booth and heat keys follow their layers in `drawBooths()` / `drawHeat()`); layer switches, the smoothing slider and the district list are in the side panel's Layers section. The north arrow sits under the zoom buttons. The opening view is `homeView()` (Feng Chia at booth zoom); the full-extent button and `0` fit the whole city. The smoke test's first view ("overview") is therefore the Feng Chia view.

**Styling.** `data-style` on `:root` (`"boba"` = the brand style and the default, set by the inline script when nothing is stored; none = "Deck"; `"program"`) × `data-theme` (`light` | `white` | `dark`, none = follow system), persisted in `localStorage` keys `hyd2026-style` / `hyd2026-theme`. Components read only the colour tokens defined per style and tone at the top of the template; `--mkt-area` is the market-area colour. Program and Boba share the rounded "card" rules (`:root:is([data-style="program"], [data-style="boba"])`). Brand assets live in `img/` (made by the team, publishable); `build_map.py` puts the favicon, apple-touch-icon and Open Graph tags (`SITE_URL`, banner) into the page head. The pearl meter (`cup()`) redraws the brand's pearl scale in SVG with `currentColor`.

## Conventions

- UI is English-first with Chinese secondary; Chinese text goes in spans with `lang="zh-Hant-TW"`.
- Coordinates are WGS84 lon/lat (CRS84). District boundaries are simplified — areas come from the attribute table, not geometry.
- Python scripts that ship in the build/CI path use only the standard library (`register_plan.py` and `fengjia_extent.py`, both run by hand, are the exceptions).
- OSM data is ODbL: keep "© OpenStreetMap contributors" credits.
