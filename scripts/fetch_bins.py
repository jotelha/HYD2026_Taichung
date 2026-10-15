"""Fetch public garbage bins and recycling points in the former Taichung City from OpenStreetMap.

Pulls amenity=waste_basket (public bins), amenity=waste_disposal (larger
containers) and amenity=recycling, except recycling centres (facilities, not
bins), and writes data/derived/waste_bins_osm.geojson as points (ways and
relations at their centre). Public bins are rare in Taiwan, where household
rubbish goes to the garbage trucks, and OSM coverage is patchy, so the layer
shows what is mapped, not every bin.

Data (c) OpenStreetMap contributors, ODbL 1.0.

Standard library only; run where Overpass is reachable (the GitHub Actions workflow).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fetch_roads import overpass, STUDY_BBOX, bbox

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "waste_bins_osm.geojson"

QUERY = f"""
[out:json][timeout:120];
nwr["amenity"~"^(waste_basket|waste_disposal|recycling)$"]({bbox(STUDY_BBOX)});
out tags center;
"""
KEEP_TAGS = ("amenity", "recycling_type", "waste", "name", "name:en", "operator", "description")


def main():
    print("querying Overpass for garbage bins ...")
    result, used = overpass(QUERY)
    features = []
    for el in result.get("elements", []):
        tags = el.get("tags", {})
        if tags.get("amenity") == "recycling" and tags.get("recycling_type") == "centre":
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
        "name": "waste_bins_osm",
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
        counts[f["properties"]["tags"]["amenity"]] = counts.get(f["properties"]["tags"]["amenity"], 0) + 1
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} bins {counts}")


if __name__ == "__main__":
    main()
