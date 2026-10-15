"""Fetch named landmarks around the Shuinan site from OpenStreetMap.

Pulls every node, way and relation near the site whose name matches one of the
major projects (Green Museumbrary, exhibition centre, transfer centre, pop
music and film centre, dome, Central Park, Wenhua Senior High station), plus
markets across the former city (amenity=marketplace, or a name containing 夜市
such as the Feng Chia Night Market), with full geometry, and writes
data/derived/landmarks_osm.geojson. Polygons carry an area-weighted centroid;
scripts/locate_projects.py picks the right feature for each project.

Data (c) OpenStreetMap contributors, ODbL 1.0.

Standard library only; run where Overpass is reachable (the GitHub Actions workflow).
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from fetch_roads import overpass, SITE_BBOX, STUDY_BBOX, bbox

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "landmarks_osm.geojson"

NAMES_ZH = "綠美圖|會展中心|轉運中心|流行影音中心|電影中心|巨蛋|中央公園|文華高中"
NAMES_EN = "Museumbrary|Exhibition Center|Transfer Center|Transit Center|Pop Music|Film Center|Dome|Central Park|Wenhua"

QUERY = f"""
[out:json][timeout:120];
(
  nwr["name"~"{NAMES_ZH}"]({bbox(SITE_BBOX)});
  nwr["name:en"~"{NAMES_EN}",i]({bbox(SITE_BBOX)});
  nwr["amenity"="marketplace"]({bbox(STUDY_BBOX)});
  nwr["name"~"夜市"]({bbox(STUDY_BBOX)});
);
out tags geom;
"""


def ring_centroid(ring):
    """Area and area-weighted centroid of a closed lon/lat ring (planar, fine at this size)."""
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(a) < 1e-15:
        xs, ys = zip(*ring)
        return 0.0, (sum(xs) / len(xs), sum(ys) / len(ys))
    return a / 2, (cx / (3 * a), cy / (3 * a))


def area_m2(signed_deg2, lat):
    return abs(signed_deg2) * 111320 * math.cos(math.radians(lat)) * 110574


def assemble_rings(ways):
    """Join member ways (lists of [lon, lat]) into closed rings."""
    ways = [list(w) for w in ways if len(w) >= 2]
    rings = []
    while ways:
        ring = ways.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, w in enumerate(ways):
                if w[0] == ring[-1]:
                    ring += w[1:]
                elif w[-1] == ring[-1]:
                    ring += w[-2::-1]
                elif w[-1] == ring[0]:
                    ring = w[:-1] + ring
                elif w[0] == ring[0]:
                    ring = w[:0:-1] + ring
                else:
                    continue
                ways.pop(i)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings


def main():
    print("querying Overpass for landmarks ...")
    result, used = overpass(QUERY)
    features = []
    for el in result.get("elements", []):
        tags = el.get("tags", {})
        props = {"osm_type": el["type"], "osm_id": el["id"], "tags": tags}
        geom = None
        if el["type"] == "node":
            geom = {"type": "Point", "coordinates": [round(el["lon"], 7), round(el["lat"], 7)]}
            props["centroid"] = geom["coordinates"]
        elif el["type"] == "way" and "geometry" in el:
            pts = [[round(g["lon"], 7), round(g["lat"], 7)] for g in el["geometry"]]
            if pts[0] == pts[-1] and len(pts) >= 4:
                a, c = ring_centroid(pts)
                geom = {"type": "Polygon", "coordinates": [pts]}
                props["area_m2"] = round(area_m2(a, c[1]))
            else:
                geom = {"type": "LineString", "coordinates": pts}
                c = pts[len(pts) // 2]
            props["centroid"] = [round(c[0], 7), round(c[1], 7)]
        elif el["type"] == "relation":
            outers = [[[round(g["lon"], 7), round(g["lat"], 7)] for g in m["geometry"]]
                      for m in el.get("members", []) if m.get("type") == "way" and m.get("role", "outer") in ("outer", "")
                      and "geometry" in m]
            rings = assemble_rings(outers)
            if not rings:
                continue
            parts = [ring_centroid(r) for r in rings]
            total = sum(a for a, _ in parts) or 1e-12
            cx = sum(a * c[0] for a, c in parts) / total
            cy = sum(a * c[1] for a, c in parts) / total
            geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
            props["area_m2"] = round(sum(area_m2(a, cy) for a, _ in parts))
            props["centroid"] = [round(cx, 7), round(cy, 7)]
        if geom:
            features.append({"type": "Feature", "properties": props, "geometry": geom})

    out = {
        "type": "FeatureCollection",
        "name": "landmarks_osm",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "osm_base": result.get("osm3s", {}).get("timestamp_osm_base"),
        "endpoint": used,
        "query": QUERY.strip(),
        "features": features,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} features")
    for f in features:
        t = f["properties"]["tags"]
        print(f"  {f['properties']['osm_type']}/{f['properties']['osm_id']}: {t.get('name')} | "
              f"{ {k: v for k, v in t.items() if k in ('amenity', 'building', 'leisure', 'railway', 'public_transport', 'tourism', 'landuse', 'construction')} } "
              f"area={f['properties'].get('area_m2')}")


if __name__ == "__main__":
    main()
