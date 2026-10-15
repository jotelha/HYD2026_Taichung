"""Build the static site: the landing page (index.html) and the base map (map/index.html).

Reads the former Taichung City district and village GeoJSON (8 districts, 214
villages; the old downtown is marked by the old_downtown flag) plus the
Shuinan tables from data/raw, fills templates/index.html and
templates/basemap.html, and writes self-contained HTML pages ready for GitHub
Pages (deploy from branch, root).

Usage:
    python3 scripts/build_map.py                     # writes index.html and map/index.html
    python3 scripts/build_map.py --fragment out.html # also writes a body-only map fragment
                                                     # without the OSM basemap (for Artifact publish)

Standard library only.
"""

import argparse
import csv
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
TEMPLATES = ROOT / "templates"
MAP_OUT = ROOT / "map" / "index.html"
LANDING_OUT = ROOT / "index.html"

# The former-city files hold every boundary; the old-downtown and Xitun-Beitun files are subsets of them.
DISTRICTS = RAW / "former_city_8_districts.geojson"
VILLAGES = RAW / "former_city_villages.geojson"
VILLAGE_TABLE = RAW / "former_city_villages.csv"
SUBSETS = [
    (RAW / "old_downtown_5_districts.geojson", "district_code"),
    (RAW / "old_downtown_villages.geojson", "village_code"),
    (RAW / "context_xitun_beitun_districts.geojson", "district_code"),
    (RAW / "context_xitun_beitun_villages.geojson", "village_code"),
]
ZONING = RAW / "shuinan_zoning_areas_2024.csv"
PROJECTS = RAW / "shuinan_major_projects_2026.csv"
REFS = RAW / "reference_points.csv"
PLAN_DXF = RAW / "Figure_7-1_Detailed_Plan_A3_English_CAD.dxf"
# Georeferenced trace of the detailed plan; regenerate with scripts/georef_plan.py.
PLAN = ROOT / "data" / "derived" / "shuinan_detailed_plan_traced.geojson"
# OSM road network; fetched by scripts/fetch_roads.py (the "Fetch OSM road network" workflow). Optional.
ROADS = ROOT / "data" / "derived" / "roads_osm.geojson"
# Major-project points from scripts/locate_projects.py. Optional.
PROJECT_LOC = ROOT / "data" / "derived" / "project_locations.geojson"
# OSM landmarks, including markets, from scripts/fetch_landmarks.py. Optional.
LANDMARKS = ROOT / "data" / "derived" / "landmarks_osm.geojson"

# Status chip per project, keyed by project_zh in shuinan_major_projects_2026.csv:
# "open" = opened / in use / in service / existing, "pending" = not yet open.
# This grouping is ours, read from status_en; unlisted projects show "unknown".
PROJECT_PHASE = {
    "臺中綠美圖": "open",
    "臺中國際會展中心": "open",
    "水湳轉運中心": "open",
    "臺中流行影音中心（原中臺灣電影中心）": "pending",
    "臺中超巨蛋": "pending",
    "中央公園": "open",
    "捷運綠線文華高中站": "open",
    "園區停車供給": "open",
}

UNOFFICIAL = re.compile(r"\s*\(unofficial translation\)\s*$", re.I)

# Landing-page download table: (file, English description, Chinese description).
DOWNLOADS = [
    (DISTRICTS, "Former Taichung City: 8 district boundaries", "原臺中市8區區界"),
    (VILLAGES, "Former Taichung City: 214 village boundaries", "原臺中市214里里界"),
    (VILLAGE_TABLE, "Village attribute table (214 rows)", "里別屬性表（214筆）"),
    (SUBSETS[0][0], "Old downtown: 5 district boundaries (subset)", "舊市區5區區界（子集）"),
    (SUBSETS[1][0], "Old downtown: 108 village boundaries (subset)", "舊市區108里里界（子集）"),
    (SUBSETS[2][0], "Xitun and Beitun district boundaries (subset)", "西屯區、北屯區區界（子集）"),
    (SUBSETS[3][0], "Xitun and Beitun: 81 village boundaries (subset)", "西屯區、北屯區81里里界（子集）"),
    (ZONING, "Shuinan Airport site detailed plan: land-use areas (2024)", "水湳機場原址細部計畫土地使用分區面積"),
    (PROJECTS, "Shuinan park major projects and status (2026)", "水湳經貿園區重大建設進度"),
    (PLAN, "Detailed plan trace, fitted to OSM roads (errors of a few tens of metres)", "細部計畫描圖（已對齊OSM路網）"),
    (PLAN_DXF, "Detailed plan, English reference CAD (A3 sheet units, not georeferenced)", "細部計畫圖英文參考版CAD"),
    (REFS, "Reference point coordinates and sources", "參考點座標與出處"),
    (ROADS, "Road and rail network from OpenStreetMap (ODbL)", "OSM路網（ODbL授權）"),
    (PROJECT_LOC, "Major project locations with method and source", "重大建設位置與定位依據"),
]

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def read_csv(path):
    # utf-8-sig: the source CSVs are saved with a byte-order mark (Excel-friendly).
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_geojson(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_subsets(districts, villages):
    """Warn if an old-downtown or Xitun-Beitun file no longer matches the former-city files."""
    full = {"district_code": {f["properties"]["district_code"]: f for f in districts["features"]},
            "village_code": {f["properties"]["village_code"]: f for f in villages["features"]}}
    for path, key in SUBSETS:
        if not path.exists():
            continue
        for f in read_geojson(path)["features"]:
            g = full[key].get(f["properties"][key])
            if g is None or g["geometry"] != f["geometry"] or g["properties"] != f["properties"]:
                print(f"warning: {path.name}: {f['properties'][key]} differs from the former-city file")


def dissolve(features):
    """Outer rings of the union of polygons that share vertices along common edges.

    An edge used by two polygons is interior and cancels; the remaining edges are
    chained back into rings. Enough for these topologically clean boundaries.
    """
    count = {}
    for f in features:
        for poly in rings(f["geometry"]):
            for ring in poly:
                for a, b in zip(ring, ring[1:]):
                    key = (min(tuple(a), tuple(b)), max(tuple(a), tuple(b)))
                    count[key] = count.get(key, 0) + 1
    nxt = {}
    for f in features:
        for poly in rings(f["geometry"]):
            for ring in poly:
                for a, b in zip(ring, ring[1:]):
                    if count[(min(tuple(a), tuple(b)), max(tuple(a), tuple(b)))] == 1:
                        nxt.setdefault(tuple(a), []).append(tuple(b))
    out = []
    while nxt:
        start = next(iter(nxt))
        ring, cur = [list(start)], start
        while True:
            b = nxt[cur].pop()
            if not nxt[cur]:
                del nxt[cur]
            ring.append(list(b))
            cur = b
            if cur == start or cur not in nxt:
                break
        out.append(ring)
    return out


def in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def in_geom(x, y, geom):
    """Point in (Multi)Polygon, holes included."""
    return any(in_ring(x, y, poly[0]) and not any(in_ring(x, y, h) for h in poly[1:]) for poly in rings(geom))


def load_markets(districts):
    """Markets and night markets in the former city from the OSM landmarks file.

    Keeps amenity=marketplace features, plus untagged features whose name ends
    in 夜市 (the parking lots, access ways and a restaurant that only share the
    name are dropped). A feature whose point lies inside another market's
    footprint (stalls zones, a node on top of the outline) or that repeats a
    nearby market's name is a duplicate. Markets outside the eight districts go.
    """
    if not LANDMARKS.exists():
        return None
    lm = read_json(LANDMARKS)
    cand = []
    for f in lm["features"]:
        t = f["properties"]["tags"]
        name = t.get("name", "")
        if t.get("amenity") != "marketplace" and not ("amenity" not in t and name.endswith("夜市")):
            continue
        cand.append(f)
    polys = [f for f in cand if f["geometry"]["type"] in ("Polygon", "MultiPolygon")]
    # bigger footprints first, so a sub-area never outranks the market around it
    cand.sort(key=lambda f: (f["geometry"]["type"] != "Point", f["properties"].get("area_m2") or 0), reverse=True)
    kept = []
    for f in cand:
        lon, lat = f["properties"]["centroid"]
        name = f["properties"]["tags"].get("name", "")
        if any(g is not f and in_geom(lon, lat, g["geometry"]) for g in polys if g in kept):
            continue
        if name and any(k["properties"]["tags"].get("name") == name
                        and math.dist(k["properties"]["centroid"], (lon, lat)) < 0.003 for k in kept):
            continue
        kept.append(f)
    out = []
    for f in kept:
        lon, lat = f["properties"]["centroid"]
        dist = next((d for d in districts["features"] if in_geom(lon, lat, d["geometry"])), None)
        if dist is None:
            continue
        t, p = f["properties"]["tags"], f["properties"]
        name = t.get("name", "")
        out.append({
            "zh": name,
            "en": t.get("name:en", ""),
            "night": "夜市" in name or "night market" in t.get("name:en", "").lower(),
            "lon": lon,
            "lat": lat,
            "ha": round(p["area_m2"] / 10000, 2) if p.get("area_m2") else None,
            "district_en": dist["properties"]["district_en"],
            "district_zh": dist["properties"]["district_zh"],
            "osm": f"{p['osm_type']}/{p['osm_id']}",
        })
    out.sort(key=lambda m: (not m["night"], m["lat"]))
    return {"fetched": lm.get("fetched"), "features": out}


def load_data():
    districts = read_geojson(DISTRICTS)
    villages = read_geojson(VILLAGES)
    check_subsets(districts, villages)
    old_outline = dissolve([f for f in districts["features"] if f["properties"].get("old_downtown")])

    zoning = []
    for row in read_csv(ZONING):
        zoning.append({
            "zh": row["zone_zh"],
            "en": row["zone_en"],
            "ha": float(row["area_ha"]),
            "pct": float(row["share_of_plan_area_pct"]),
            "source": row["source"],
        })

    projects = []
    for row in read_csv(PROJECTS):
        en = row["project_en"]
        projects.append({
            "zh": row["project_zh"],
            # "(unofficial translation)" becomes a flag so the English name reads cleanly
            "en": UNOFFICIAL.sub("", en),
            "en_unofficial": bool(UNOFFICIAL.search(en)),
            "status": row["status_en"],
            "figures": row["key_figures_en"],
            "phase": PROJECT_PHASE.get(row["project_zh"], "unknown"),
            "source": row["source"],
        })

    # Drop properties the page never reads to keep the inline payload small.
    keep_v = ("village_code", "village_zh", "village_en", "district_code",
              "district_zh", "district_en", "area_km2", "label_lon", "label_lat")
    keep_d = ("district_code", "district_zh", "district_en", "area_km2",
              "village_count", "label_lon", "label_lat", "old_downtown")
    boundary_source = villages["features"][0]["properties"]["source"]
    markets = load_markets(districts)
    for fc, keep in ((villages, keep_v), (districts, keep_d)):
        for f in fc["features"]:
            f["properties"] = {k: f["properties"][k] for k in keep}
        fc.pop("crs", None)

    return {
        "districts": districts,
        "villages": villages,
        "zoning": zoning,
        "projects": projects,
        "boundary_source": boundary_source,
        # rings of the five old-downtown districts merged into one outline
        "old_downtown_outline": old_outline,
        "plan": read_json(PLAN),
        "refs": read_csv(REFS),
        "roads": read_json(ROADS) if ROADS.exists() else None,
        "project_locations": read_json(PROJECT_LOC) if PROJECT_LOC.exists() else None,
        "markets": markets,
    }


def inline_json(obj):
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    # Keep the payload from closing the surrounding <script> element.
    return text.replace("</", "<\\/")


def fill(template, values):
    for marker, value in values.items():
        if marker not in template:
            raise SystemExit(f"marker {marker!r} not found in template")
        template = template.replace(marker, value)
    return template


def wrap_page(fragment, lang):
    return (
        "<!doctype html>\n"
        f'<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        # OSM tile servers expect a Referer from web pages; keep the browser default explicit.
        '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
        "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
    )


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(text.encode('utf-8')) / 1024:.0f} KB)")


def rings(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def thumbnail_svg(data, width=560, pad=6):
    """Static outline of districts and villages for the landing page (Web Mercator, like the map)."""
    def merc(lon, lat):
        return math.radians(lon), math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    pts = [merc(lon, lat)
           for f in data["districts"]["features"]
           for poly in rings(f["geometry"]) for ring in poly for lon, lat in ring]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    scale = (width - 2 * pad) / (x1 - x0)
    height = (y1 - y0) * scale + 2 * pad

    def path(geom):
        out = []
        for poly in rings(geom):
            for ring in poly:
                cmds = []
                for i, (lon, lat) in enumerate(ring):
                    x, y = merc(lon, lat)
                    cmds.append(f"{'L' if i else 'M'}{pad + (x - x0) * scale:.1f} {pad + (y1 - y) * scale:.1f}")
                out.append("".join(cmds) + "Z")
        return "".join(out)

    # d0 = old downtown, d1 = the outer districts, as on the map
    group = {f["properties"]["district_code"]: 0 if f["properties"].get("old_downtown") else 1
             for f in data["districts"]["features"]}
    parts = [f'<path class="v d{group[f["properties"]["district_code"]]}" d="{path(f["geometry"])}"/>'
             for f in data["villages"]["features"] if f["geometry"]]
    outline = {"type": "Polygon", "coordinates": data["old_downtown_outline"]}
    parts.append(f'<path class="old" d="{path(outline)}"/>')
    parts += [f'<path class="dist" d="{path(f["geometry"])}"/>' for f in data["districts"]["features"]]
    return (f'<svg class="thumb" viewBox="0 0 {width} {height:.0f}" role="img" '
            f'aria-label="Outline of the district and village boundaries of the former Taichung City, '
            f'with the old downtown marked">{"".join(parts)}</svg>')


def landing_values(data):
    villages = data["villages"]["features"]
    districts = data["districts"]["features"]
    area = sum(f["properties"]["area_km2"] for f in districts)
    n_old = sum(1 for f in districts if f["properties"].get("old_downtown"))

    m = re.search(r"village boundaries \((\d{4}-\d{2}-\d{2})\)", data["boundary_source"])
    boundary_date = f"NLSC village boundaries, {m.group(1)}" if m else "NLSC village boundaries"
    zoning_src = data["zoning"][0]["source"]
    zd = DATE_RE.search(zoning_src)
    project_dates = sorted(d for p in data["projects"] for d in DATE_RE.findall(p["source"]))

    rows = []
    for path, en, zh in DOWNLOADS:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT).as_posix()
        size_kb = path.stat().st_size / 1024
        rows.append(
            f'<tr><td class="file"><a href="{rel}" download>{html.escape(path.name)}</a>'
            f'<span class="fmt">{path.suffix[1:].upper()}</span></td>'
            f'<td>{html.escape(en)}<span class="zh block" lang="zh-Hant-TW">{html.escape(zh)}</span></td>'
            f'<td class="size num">{size_kb:.1f} KB</td></tr>'
        )

    sources = [
        f"Boundaries: {html.escape(data['boundary_source'])}",
        "Boundaries are simplified: use them for context, not for measurement or precise overlay. The old-downtown and "
        "Xitun–Beitun files are subsets of the former-city files, with identical geometry and attributes. Futai Village "
        "(富台里, East District) has no boundary in the source; the map shows it as a circle of the same area at its "
        "label point.",
        f"Land-use areas: {html.escape(zoning_src)}",
        "Major projects: Taichung City Government project reports and news coverage; each row's source is in the CSV.",
        "Detailed plan overlay: colour patches auto-traced from Figure 7-1 (unofficial English reference) and fitted to "
        "OpenStreetMap road centrelines; block edges sit a median 11 m from the nearest road, so expect errors of a few "
        "tens of metres. The Chinese plan and official GIS/CAD data prevail.",
        'Basemap: vector tiles from <a href="https://openfreemap.org">OpenFreeMap</a> (© <a href="https://www.openmaptiles.org/">'
        'OpenMapTiles</a>), drawn with MapLibre GL JS, labelled with English names (OSM name:en) where mapped; the standard '
        'OpenStreetMap tiles serve as a fallback under the <a href="https://operations.osmfoundation.org/policies/tiles/">OSM '
        'tile usage policy</a>.',
        '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a>: basemap data and the road network '
        '(Open Database License 1.0, fetched through the Overpass API).',
    ]

    return {
        "<!--__THUMB__-->": thumbnail_svg(data),
        "<!--__N_VILLAGES__-->": str(len(villages)),
        "<!--__EXTENT__-->": (f'Former Taichung City, {len(districts)} districts ({n_old} in the old downtown) · '
                              f'{len(villages)} villages · <span class="num">{area:.2f}</span> km²'),
        "<!--__BOUNDARY_DATE__-->": boundary_date,
        "<!--__ZONING_DATE__-->": f"2nd comprehensive review, public briefing{', ' + zd.group(0) if zd else ''}",
        "<!--__PROJECT_DATE__-->": f"Sources up to {project_dates[-1]}" if project_dates else "",
        "<!--__DOWNLOADS__-->": "".join(rows),
        "<!--__SOURCES__-->": "".join(f"<li>{s}</li>" for s in sources),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fragment", type=Path,
                        help="also write a body-only map fragment (no doctype/html/head, no OSM basemap) to this path")
    args = parser.parse_args()

    data = load_data()
    map_template = (TEMPLATES / "basemap.html").read_text(encoding="utf-8")
    payload = inline_json(data)

    map_page = fill(map_template, {
        "/*__DATA__*/null": payload,
        "/*__BASEMAP__*/true": "true",
        "<!--__EYEBROW__-->": '<a href="../index.html">#HackYourDistrict 2026</a> · Taichung · Former city and Shuinan layers',
    })
    write(MAP_OUT, wrap_page(map_page, "en"))  # English leads; Chinese spans carry lang="zh-Hant-TW"

    landing = fill((TEMPLATES / "index.html").read_text(encoding="utf-8"), landing_values(data))
    write(LANDING_OUT, wrap_page(landing, "en"))

    if args.fragment:
        fragment = fill(map_template, {
            "/*__DATA__*/null": payload,
            "/*__BASEMAP__*/true": "false",
            "<!--__EYEBROW__-->": "#HackYourDistrict 2026 · Taichung · Former city and Shuinan layers",
        })
        args.fragment.write_text(fragment, encoding="utf-8")
        print(f"wrote {args.fragment}")


if __name__ == "__main__":
    main()
