"""Generate MOCK noise readings around the Feng Chia Night Market, in dB(A) on a weekend evening.

Nothing here is measured: the readings stand in for a sensor network so the
map's noise layer can be designed before real data exists.

Sensors sit on a GRID_M grid over the market extent padded by PAD_M. Each
reading is the energetic sum (10 log10 of summed 10^(L/10)) of
  - a quiet background, BACKGROUND_DB;
  - the market streets (centrelines from data/derived/fengjia_night_market_extent.geojson,
    see scripts/fengjia_extent.py): MARKET_DB at 5 m, falling 6 dB per doubling
    of distance (crowds and vendors behave like many point sources);
  - the main roads around the market (OSM primary / secondary / tertiary from
    data/derived/roads_osm.geojson): TRAFFIC_DB at 5 m by road class, falling
    3 dB per doubling (a line source);
plus Gaussian sensor noise (SENSOR_SD), rounded to 0.5 dB. A fixed seed makes
the output reproducible.

Writes data/derived/fengjia_noise_mock.geojson. Standard library only.
"""

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTENT = ROOT / "data" / "derived" / "fengjia_night_market_extent.geojson"
ROADS = ROOT / "data" / "derived" / "roads_osm.geojson"
OUT = ROOT / "data" / "derived" / "fengjia_noise_mock.geojson"

SEED = 2027
GRID_M = 30.0                # sensor spacing
PAD_M = 200.0                # area around the market extent
BACKGROUND_DB = 48.0
MARKET_DB = 76.0             # at 5 m from a market street centreline
TRAFFIC_DB = {"trunk": 74.0, "primary": 72.0, "secondary": 68.0, "tertiary": 64.0}
SENSOR_SD = 1.5

LAT0, LON0 = 24.178, 120.645
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110574


def to_m(lon, lat):
    return (lon - LON0) * KX, (lat - LAT0) * KY


def to_deg(x, y):
    return round(x / KX + LON0, 7), round(y / KY + LAT0, 7)


def seg_dist(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def line_dist(p, pts):
    return min(seg_dist(p, a, b) for a, b in zip(pts, pts[1:]))


def main():
    fc = json.loads(EXTENT.read_text(encoding="utf-8"))
    market = [[to_m(*c) for c in f["geometry"]["coordinates"]]
              for f in fc["features"][1:] if f["properties"].get("kind") == "street"]
    if not market:
        raise SystemExit("no street centrelines in the extent file; rerun scripts/fengjia_extent.py")
    ext = fc["features"][0]["geometry"]
    ring = [to_m(*c) for c in (ext["coordinates"][0] if ext["type"] == "Polygon" else ext["coordinates"][0][0])]
    x0, x1 = min(x for x, _ in ring) - PAD_M, max(x for x, _ in ring) + PAD_M
    y0, y1 = min(y for _, y in ring) - PAD_M, max(y for _, y in ring) + PAD_M

    roads = []
    for f in json.loads(ROADS.read_text(encoding="utf-8"))["features"]:
        level = TRAFFIC_DB.get(f["properties"]["kind"])
        if level is None:
            continue
        pts = [to_m(*c) for c in f["geometry"]["coordinates"]]
        # keep roads that come within 300 m of the area
        if any(x0 - 300 < x < x1 + 300 and y0 - 300 < y < y1 + 300 for x, y in pts):
            roads.append((level, pts))

    rng = random.Random(SEED)
    features = []
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            p = (x, y)
            energy = 10 ** (BACKGROUND_DB / 10)
            d = max(5.0, min(line_dist(p, s) for s in market))
            energy += 10 ** ((MARKET_DB - 20 * math.log10(d / 5)) / 10)
            for level, pts in roads:
                d = max(5.0, line_dist(p, pts))
                energy += 10 ** ((level - 10 * math.log10(d / 5)) / 10)
            db = 10 * math.log10(energy) + rng.gauss(0, SENSOR_SD)
            lon, lat = to_deg(x, y)
            features.append({"type": "Feature", "properties": {"db": round(db * 2) / 2},
                             "geometry": {"type": "Point", "coordinates": [lon, lat]}})
            x += GRID_M
        y += GRID_M

    out = {
        "type": "FeatureCollection",
        "name": "fengjia_noise_mock",
        "mock": True,
        "note": f"MOCK DATA: modelled noise levels in dB(A) on a {GRID_M:g} m sensor grid around the Feng Chia Night Market "
                f"(market streets, main roads, background, random sensor error; seed {SEED}); nothing here was measured.",
        "unit": "dB(A)",
        "grid_m": GRID_M,
        "features": features,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    dbs = [f["properties"]["db"] for f in features]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} mock readings, {min(dbs)}-{max(dbs)} dB(A), "
          f"{len(roads)} road ways as traffic sources")


if __name__ == "__main__":
    main()
