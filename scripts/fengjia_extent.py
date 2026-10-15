"""Approximate the full extent of the Feng Chia Night Market (逢甲夜市) from its streets.

OpenStreetMap maps the market (way 450771065) along Wenhua Road and Fengjia
Road Lane 20 only. No official boundary is published, so this script draws one
from the streets that press coverage names as the market area: Wenhua Road,
Fengjia Road, Fuxing Road and Fengjia Road Lane 20 (Business Today, 2015,
https://www.businesstoday.com.tw/article/category/80392/post/201507160040/).
Each street is clipped to the stretch in STREETS (our reading of where the
stalls run), buffered by BUFFER_M on both sides for the carriageway, arcades
and shopfronts, and merged into one polygon. Treat the result as an
approximation, not a surveyed boundary.

Writes data/derived/fengjia_night_market_extent.geojson. Street geometry
(c) OpenStreetMap contributors, ODbL 1.0.

Needs shapely and Overpass access (not part of the CI build):
    python3 scripts/fengjia_extent.py
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import shapely
from shapely.geometry import LineString, box, mapping
from shapely.ops import unary_union

from fetch_roads import overpass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "fengjia_night_market_extent.geojson"

BUFFER_M = 15
# street name -> stretch kept (west, south, east, north in lon/lat)
STREETS = {
    # from the south end of the OSM outline up to Xi'an Street, including the pedestrian stretch
    "文華路": (120.6440, 24.1751, 120.6480, 24.1820),
    # from Xitun Road Section 2 east to Wenhua Road
    "逢甲路": (120.64225, 24.1770, 120.6466, 24.1800),
    # from the Fengjia Road junction north to where Fuxing Road turns west
    "福星路": (120.6446, 24.17883, 120.6456, 24.1824),
    "逢甲路20巷": (120.6440, 24.1770, 120.6480, 24.1820),
}
QUERY = """
[out:json][timeout:60];
way["highway"]["name"~"^({names})$"](24.170,120.638,24.186,120.652);
out tags geom;
""".format(names="|".join(STREETS))

LAT0 = 24.178
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110574


def to_m(xy):
    return (xy - (120.645, LAT0)) * (KX, KY)


def to_deg(xy):
    return xy / (KX, KY) + (120.645, LAT0)


def main():
    print("querying Overpass for the Feng Chia streets ...")
    result, used = overpass(QUERY)
    pieces, way_ids = [], {}
    for el in result.get("elements", []):
        name = el["tags"]["name"]
        line = LineString([(g["lon"], g["lat"]) for g in el["geometry"]])
        part = shapely.transform(line.intersection(box(*STREETS[name])), to_m)
        # skip ways that only poke a few metres into the stretch at a junction
        if part.length < 10:
            continue
        pieces.append(part)
        way_ids.setdefault(name, []).append(el["id"])
    missing = set(STREETS) - set(way_ids)
    if missing:
        raise SystemExit(f"no geometry for {', '.join(sorted(missing))}")
    area = unary_union([p.buffer(BUFFER_M, quad_segs=4) for p in pieces]).simplify(0.5)
    geom = shapely.transform(area, to_deg)
    geom = json.loads(json.dumps(mapping(geom)), parse_float=lambda s: round(float(s), 7))

    out = {
        "type": "FeatureCollection",
        "name": "fengjia_night_market_extent",
        "attribution": "Street geometry © OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "endpoint": used,
        "features": [{
            "type": "Feature",
            "properties": {
                "name_zh": "逢甲夜市",
                "name_en": "Fengjia Night Market",
                "osm_market": "way/450771065",
                "method": f"OSM street centrelines buffered by {BUFFER_M} m and merged",
                "streets": {name: sorted(ids) for name, ids in way_ids.items()},
                "area_ha": round(area.area / 10000, 2),
                "source": "Streets named as the market area by Business Today (商業周刊), 2015; stretches and buffer are our approximation, not an official boundary",
            },
            "geometry": geom,
        }],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {out['features'][0]['properties']['area_ha']} ha, {geom['type']}")


if __name__ == "__main__":
    main()
