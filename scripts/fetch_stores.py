"""Fetch convenience stores in the former Taichung City from OpenStreetMap, with whether they have toilets.

Pulls every shop=convenience feature (ways and relations at their centre),
leaves out the Shopee parcel pick-up points (蝦皮店到店, Shopee Xpress / SPX Express)
that are tagged as convenience stores, and writes data/derived/convenience_stores_osm.geojson
with each store's toilets tag ("yes", "no" or missing). Most 7-Eleven and
FamilyMart branches in Taiwan have customer toilets, but only a minority of
stores carry a toilets tag in OSM, so the map's toilet layer shows the stores
tagged toilets=yes, not every store with a toilet.

Data (c) OpenStreetMap contributors, ODbL 1.0.

Standard library only; run where Overpass is reachable (the GitHub Actions workflow).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fetch_roads import overpass, STUDY_BBOX, bbox

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "convenience_stores_osm.geojson"

QUERY = f"""
[out:json][timeout:120];
nwr["shop"="convenience"]({bbox(STUDY_BBOX)});
out tags center;
"""
NOT_STORES = ("shopee", "spx", "蝦皮")  # Shopee parcel pick-up points (蝦皮店到店) tagged as convenience stores
KEEP_TAGS = ("name", "name:en", "name:zh", "brand", "brand:en", "branch", "toilets", "toilets:wheelchair",
             "opening_hours", "addr:street", "addr:housenumber")


def main():
    print("querying Overpass for convenience stores ...")
    result, used = overpass(QUERY)
    features = []
    for el in result.get("elements", []):
        tags = el.get("tags", {})
        label = " ".join(tags.get(k, "") for k in ("brand", "brand:en", "name", "name:en", "name:zh")).lower()
        if any(word in label for word in NOT_STORES):
            continue
        lat, lon = (el["lat"], el["lon"]) if el["type"] == "node" else (el["center"]["lat"], el["center"]["lon"])
        features.append({
            "type": "Feature",
            "properties": {"osm_type": el["type"], "osm_id": el["id"], "tags": {k: v for k, v in tags.items() if k in KEEP_TAGS}},
            "geometry": {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]},
        })
    features.sort(key=lambda f: (f["properties"]["osm_type"], f["properties"]["osm_id"]))
    out = {
        "type": "FeatureCollection",
        "name": "convenience_stores_osm",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "osm_base": result.get("osm3s", {}).get("timestamp_osm_base"),
        "endpoint": used,
        "query": QUERY.strip(),
        "features": features,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    counts = {}
    for f in features:
        t = f["properties"]["tags"].get("toilets", "unknown")
        counts[t] = counts.get(t, 0) + 1
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} stores, toilets {counts}")


if __name__ == "__main__":
    main()
