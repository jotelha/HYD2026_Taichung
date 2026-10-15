"""Build the static site: the Boba Index markets map (index.html).

Reads the eight district boundaries of the former Taichung City from data/raw
and the OpenStreetMap markets from data/derived (scripts/fetch_landmarks.py,
plus the Feng Chia extent from scripts/fengjia_extent.py and the mock booths
from scripts/mock_booths.py), fills
templates/basemap.html and writes a self-contained page ready for GitHub Pages
(deploy from branch, root). map/index.html, the old address of the map, becomes
a redirect to the root.

Usage:
    python3 scripts/build_map.py                     # writes index.html and map/index.html
    python3 scripts/build_map.py --fragment out.html # also writes a body-only map fragment
                                                     # without the OSM basemap (for Artifact publish)

Standard library only.
"""

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
TEMPLATES = ROOT / "templates"
OUT = ROOT / "index.html"
OLD_MAP_OUT = ROOT / "map" / "index.html"

DISTRICTS = RAW / "former_city_8_districts.geojson"
# OSM landmarks, including markets, from scripts/fetch_landmarks.py. Optional.
LANDMARKS = ROOT / "data" / "derived" / "landmarks_osm.geojson"
# Approximate full extent of the Feng Chia Night Market from scripts/fengjia_extent.py. Optional.
FENGJIA_EXTENT = ROOT / "data" / "derived" / "fengjia_night_market_extent.geojson"
# OSM garbage bins and recycling points from scripts/fetch_bins.py. Optional.
BINS = ROOT / "data" / "derived" / "waste_bins_osm.geojson"
# OSM convenience stores with their toilets tag, from scripts/fetch_stores.py. Optional.
STORES = ROOT / "data" / "derived" / "convenience_stores_osm.geojson"
# OSM pharmacies, from scripts/fetch_pharmacies.py. Optional.
PHARMACIES = ROOT / "data" / "derived" / "pharmacies_osm.geojson"
# Hand-placed market bins (the team's own, not in OSM). Optional.
CUSTOM_BINS = RAW / "custom_bins.csv"
# MOCK noise readings around Feng Chia from scripts/mock_noise.py. Optional.
NOISE = ROOT / "data" / "derived" / "fengjia_noise_mock.geojson"
# MOCK PM2.5 readings around Feng Chia from scripts/mock_air.py. Optional.
AIR = ROOT / "data" / "derived" / "fengjia_air_mock.geojson"
# MOCK booths with random Boba Index scores from scripts/mock_booths.py. Optional.
BOOTHS = ROOT / "data" / "derived" / "fengjia_booths_mock.geojson"
EYEBROW = "#HackYourDistrict 2026 · Taichung · Night market prototype"
# Public address of the site (GitHub Pages); social previews need absolute image URLs.
SITE_URL = "https://jotelha.github.io/HYD2026_Taichung/"
DESCRIPTION = ("Taste a deeper Taichung. Boba Index (Built On Belonging and Authenticity): a map rating Taichung's "
               "night markets, down to the booths of Feng Chia.")
# Brand assets in img/ (made by the team): favicon, home-screen icon and the banner used for link previews.
HEAD_LINKS = f"""<meta name="description" content="{DESCRIPTION}">
<meta name="theme-color" content="#fd9f02">
<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:title" content="Boba Index · Built On Belonging and Authenticity">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}img/boba-index-banner.jpg">
<meta property="og:image:width" content="1395">
<meta property="og:image:height" content="752">
<meta name="twitter:card" content="summary_large_image">
"""

REDIRECT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Boba Index</title>
<meta http-equiv="refresh" content="0; url=../">
<link rel="canonical" href="../">
</head>
<body><p>The map has moved to <a href="../">the home page</a>.</p></body>
</html>
"""


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_geojson(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


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
    Night markets carry their mapped outline; Feng Chia also gets the street-based
    extent from scripts/fengjia_extent.py.
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
        night = "夜市" in name or "night market" in t.get("name:en", "").lower()
        out.append({
            "zh": name,
            "en": t.get("name:en", ""),
            "night": night,
            "foot": round_rings(f["geometry"]) if night and f["geometry"]["type"] != "Point" else None,
            "lon": lon,
            "lat": lat,
            "ha": round(p["area_m2"] / 10000, 2) if p.get("area_m2") else None,
            "district_en": dist["properties"]["district_en"],
            "district_zh": dist["properties"]["district_zh"],
            "osm": f"{p['osm_type']}/{p['osm_id']}",
        })
    if FENGJIA_EXTENT.exists():
        ext = read_json(FENGJIA_EXTENT)["features"][0]
        for m in out:
            if m["osm"] == ext["properties"]["osm_market"]:
                m["extent"] = round_rings(ext["geometry"])
                m["extent_ha"] = ext["properties"]["area_ha"]
                m["extent_note"] = ext["properties"]["source"]
    out.sort(key=lambda m: (not m["night"], m["lat"]))
    return {"fetched": lm.get("fetched"), "features": out}


def round_rings(geom):
    """Polygon rings as a list of polygons (lists of rings), coordinates rounded to ~10 cm."""
    return [[[[round(x, 6), round(y, 6)] for x, y in ring] for ring in poly] for poly in rings(geom)]


def load_booths():
    """Mock booths as compact rows [lon, lat, bearing, boba_index, street #, name_zh, name_en]; ids follow the row order."""
    if not BOOTHS.exists():
        return None
    fc = read_json(BOOTHS)
    streets, rows = [], []
    for f in fc["features"]:
        p = f["properties"]
        key = [p["street_zh"], p["street_en"]]
        if key not in streets:
            streets.append(key)
        rows.append([*p["centre"], p["bearing_deg"], p["boba_index"], streets.index(key), p["name_zh"], p["name_en"]])
    return {"market": "way/450771065", "size_m": fc["booth_size_m"], "pitch_m": fc["pitch_m"],
            "id_prefix": "FJ-", "streets": streets, "rows": rows}


def load_bins(districts):
    """Bins inside the eight districts as rows [lon, lat, kind, ref, label]: kind 0 = bin, 1 = container,
    2 = recycling (all OSM, ref "type/id"), 3 = a hand-placed market bin from custom_bins.csv (ref = its id)."""
    if not BINS.exists() and not CUSTOM_BINS.exists():
        return None
    fc = read_json(BINS) if BINS.exists() else {"features": []}
    kinds = {"waste_basket": 0, "waste_disposal": 1, "recycling": 2}
    rows = []
    for f in fc["features"]:
        lon, lat = f["geometry"]["coordinates"]
        if not any(in_geom(lon, lat, d["geometry"]) for d in districts["features"]):
            continue
        p = f["properties"]
        rows.append([lon, lat, kinds[p["tags"]["amenity"]], f"{p['osm_type']}/{p['osm_id']}", None])
    # the team's own bins last, so they draw on top
    if CUSTOM_BINS.exists():
        with CUSTOM_BINS.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append([float(r["lon"]), float(r["lat"]), 3, r["id"], [r["name_en"], r["name_zh"]]])
    return {"fetched": fc.get("fetched"), "rows": rows}


def load_toilet_stores(districts):
    """Convenience stores tagged toilets=yes inside the eight districts, as rows
    [lon, lat, name_en, name_zh, opening_hours, "type/id"]."""
    if not STORES.exists():
        return None
    fc = read_json(STORES)
    rows = []
    for f in fc["features"]:
        t = f["properties"]["tags"]
        if t.get("toilets") != "yes":
            continue
        lon, lat = f["geometry"]["coordinates"]
        if not any(in_geom(lon, lat, d["geometry"]) for d in districts["features"]):
            continue
        # English line: the brand ("7-Eleven", "FamilyMart"); local line: the name plus the branch ("興大門市")
        en = t.get("name:en") or t.get("brand:en") or t.get("brand") or t.get("name", "")
        local = " ".join(x for x in (t.get("name", ""), t.get("branch", "")) if x)
        rows.append([lon, lat, en, local, t.get("opening_hours", ""),
                     f"{f['properties']['osm_type']}/{f['properties']['osm_id']}"])
    total = len(fc["features"])
    return {"fetched": fc.get("fetched"), "stores_total": total, "rows": rows}


def load_pharmacies(districts):
    """Pharmacies inside the eight districts as rows [lon, lat, name_en, name_local, opening_hours, dispensing, "type/id"]."""
    if not PHARMACIES.exists():
        return None
    fc = read_json(PHARMACIES)
    rows = []
    for f in fc["features"]:
        lon, lat = f["geometry"]["coordinates"]
        if not any(in_geom(lon, lat, d["geometry"]) for d in districts["features"]):
            continue
        t = f["properties"]["tags"]
        rows.append([lon, lat, t.get("name:en") or t.get("brand:en") or "",
                     " ".join(x for x in (t.get("name", ""), t.get("branch", "")) if x),
                     t.get("opening_hours", ""), t.get("dispensing", ""),
                     f"{f['properties']['osm_type']}/{f['properties']['osm_id']}"])
    return {"fetched": fc.get("fetched"), "rows": rows}


def load_noise():
    """Mock noise readings as compact rows [lon, lat, dB(A)]."""
    if not NOISE.exists():
        return None
    fc = read_json(NOISE)
    return {"unit": fc.get("unit", "dB(A)"), "grid_m": fc.get("grid_m"),
            "rows": [[*f["geometry"]["coordinates"], f["properties"]["db"]] for f in fc["features"]]}


def load_air():
    """Mock PM2.5 readings as compact rows [lon, lat, µg/m³]."""
    if not AIR.exists():
        return None
    fc = read_json(AIR)
    return {"unit": fc.get("unit", "µg/m³"), "grid_m": fc.get("grid_m"),
            "rows": [[*f["geometry"]["coordinates"], f["properties"]["pm25"]] for f in fc["features"]]}


def load_data():
    districts = read_geojson(DISTRICTS)
    markets = load_markets(districts)
    bins = load_bins(districts)
    toilets = load_toilet_stores(districts)
    pharmacies = load_pharmacies(districts)
    boundary_source = districts["features"][0]["properties"]["source"]
    # Drop properties the page never reads to keep the inline payload small.
    keep = ("district_code", "district_zh", "district_en", "area_km2", "label_lon", "label_lat")
    for f in districts["features"]:
        f["properties"] = {k: f["properties"][k] for k in keep}
    districts.pop("crs", None)
    return {"districts": districts, "markets": markets, "booths": load_booths(), "bins": bins, "toilets": toilets, "pharmacies": pharmacies, "noise": load_noise(), "air": load_air(), "boundary_source": boundary_source}


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


def wrap_page(fragment, lang, head=""):
    return (
        "<!doctype html>\n"
        f'<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        # OSM tile servers expect a Referer from web pages; keep the browser default explicit.
        '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
        + head + "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
    )


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(text.encode('utf-8')) / 1024:.0f} KB)")


def rings(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fragment", type=Path,
                        help="also write a body-only map fragment (no doctype/html/head, no OSM basemap) to this path")
    args = parser.parse_args()

    data = load_data()
    template = (TEMPLATES / "basemap.html").read_text(encoding="utf-8")
    payload = inline_json(data)

    page = fill(template, {
        "/*__DATA__*/null": payload,
        "/*__BASEMAP__*/true": "true",
        "<!--__EYEBROW__-->": EYEBROW,
    })
    write(OUT, wrap_page(page, "en", HEAD_LINKS))  # English leads; Chinese spans carry lang="zh-Hant-TW"
    write(OLD_MAP_OUT, REDIRECT)

    if args.fragment:
        fragment = fill(template, {
            "/*__DATA__*/null": payload,
            "/*__BASEMAP__*/true": "false",
            "<!--__EYEBROW__-->": EYEBROW,
        })
        args.fragment.write_text(fragment, encoding="utf-8")
        print(f"wrote {args.fragment}")


if __name__ == "__main__":
    main()
