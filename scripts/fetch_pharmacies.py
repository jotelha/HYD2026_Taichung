"""Fetch pharmacies in the former Taichung City from OpenStreetMap.

Pulls amenity=pharmacy (Taiwan's 藥局; ways and relations at their centre)
and writes data/derived/pharmacies_osm.geojson. Drugstore chains such as
Watsons or Cosmed are tagged shop=chemist and are not included. OSM shows
what is mapped; some pharmacies are missing and opening hours are often
not recorded.

Data (c) OpenStreetMap contributors, ODbL 1.0.

Standard library only; run where Overpass is reachable (the GitHub Actions workflow).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fetch_roads import overpass, STUDY_BBOX, bbox

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "pharmacies_osm.geojson"

QUERY = f"""
[out:json][timeout:120];
nwr["amenity"="pharmacy"]({bbox(STUDY_BBOX)});
out tags center;
"""
KEEP_TAGS = ("name", "name:en", "name:zh", "brand", "brand:en", "branch", "dispensing", "healthcare",
             "opening_hours", "phone", "contact:phone", "addr:street", "addr:housenumber")


def main():
    print("querying Overpass for pharmacies ...")
    result, used = overpass(QUERY)
    features = []
    for el in result.get("elements", []):
        tags = el.get("tags", {})
        lat, lon = (el["lat"], el["lon"]) if el["type"] == "node" else (el["center"]["lat"], el["center"]["lon"])
        features.append({
            "type": "Feature",
            "properties": {"osm_type": el["type"], "osm_id": el["id"], "tags": {k: v for k, v in tags.items() if k in KEEP_TAGS}},
            "geometry": {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]},
        })
    features.sort(key=lambda f: (f["properties"]["osm_type"], f["properties"]["osm_id"]))
    out = {
        "type": "FeatureCollection",
        "name": "pharmacies_osm",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "osm_base": result.get("osm3s", {}).get("timestamp_osm_base"),
        "endpoint": used,
        "query": QUERY.strip(),
        "features": features,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    disp = {}
    for f in features:
        d = f["properties"]["tags"].get("dispensing", "unknown")
        disp[d] = disp.get(d, 0) + 1
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} pharmacies, dispensing {disp}")


if __name__ == "__main__":
    main()
