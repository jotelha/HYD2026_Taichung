"""Generate MOCK PM2.5 readings around the Feng Chia Night Market, in µg/m³ on a weekend evening.

Nothing here is measured: the readings stand in for a sensor network so the
map's air-quality layer can be designed before real data exists.

Sensors sit on the same grid as scripts/mock_noise.py (GRID_M over the market
extent padded by PAD_M). Each reading adds
  - a regional background, BACKGROUND (a typical Taichung evening);
  - traffic on the main roads (OSM primary / secondary / tertiary from
    data/derived/roads_osm.geojson): TRAFFIC by road class at the kerb,
    falling as exp(-d / 40 m) beyond the kerb;
  - cooking at the mock booths (data/derived/fengjia_booths_mock.geojson,
    scripts/mock_booths.py): each booth adds a Gaussian plume of width
    COOK_SIGMA_M, strong for frying and grilling (FRY_WORDS in its name),
    weak for drinks and desserts, so smoke stays local;
times a log-normal sensor error (SENSOR_SD), rounded to 0.5 µg/m³. A fixed
seed makes the output reproducible.

Writes data/derived/fengjia_air_mock.geojson. Standard library only.
"""

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTENT = ROOT / "data" / "derived" / "fengjia_night_market_extent.geojson"
ROADS = ROOT / "data" / "derived" / "roads_osm.geojson"
BOOTHS = ROOT / "data" / "derived" / "fengjia_booths_mock.geojson"
OUT = ROOT / "data" / "derived" / "fengjia_air_mock.geojson"

SEED = 2028
GRID_M = 30.0
PAD_M = 200.0
BACKGROUND = 17.0                                    # µg/m³
TRAFFIC = {"trunk": 9.0, "primary": 8.0, "secondary": 6.0, "tertiary": 4.0}
COOK_SIGMA_M = 18.0
FRY_WORDS = ("雞排", "鹽酥雞", "烤", "串燒", "鐵板燒", "臭豆腐", "蔥油餅", "胡椒餅", "地瓜球", "章魚燒",
             "蚵仔煎", "大腸包小腸", "牛肉捲", "香酥")
FRY_EMISSION, OTHER_EMISSION = 6.5, 1.0             # µg/m³ added at a booth's own position
SENSOR_SD = 0.12                                     # log-normal, about ±12 %

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
    ext = fc["features"][0]["geometry"]
    ring = [to_m(*c) for c in (ext["coordinates"][0] if ext["type"] == "Polygon" else ext["coordinates"][0][0])]
    x0, x1 = min(x for x, _ in ring) - PAD_M, max(x for x, _ in ring) + PAD_M
    y0, y1 = min(y for _, y in ring) - PAD_M, max(y for _, y in ring) + PAD_M

    roads = []
    for f in json.loads(ROADS.read_text(encoding="utf-8"))["features"]:
        add = TRAFFIC.get(f["properties"]["kind"])
        if add is None:
            continue
        pts = [to_m(*c) for c in f["geometry"]["coordinates"]]
        if any(x0 - 300 < x < x1 + 300 and y0 - 300 < y < y1 + 300 for x, y in pts):
            roads.append((add, pts))

    stalls = []
    for f in json.loads(BOOTHS.read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        fry = any(w in p["name_zh"] for w in FRY_WORDS)
        stalls.append((*to_m(*p["centre"]), FRY_EMISSION if fry else OTHER_EMISSION))
    n_fry = sum(1 for *_, e in stalls if e == FRY_EMISSION)

    rng = random.Random(SEED)
    features = []
    inv = 1 / (2 * COOK_SIGMA_M ** 2)
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            p = (x, y)
            pm = BACKGROUND
            for add, pts in roads:
                pm += add * math.exp(-max(0.0, line_dist(p, pts) - 5) / 40)
            for sx, sy, e in stalls:
                d2 = (sx - x) ** 2 + (sy - y) ** 2
                if d2 < 9 * COOK_SIGMA_M ** 2:
                    pm += e * math.exp(-d2 * inv)
            pm *= math.exp(rng.gauss(0, SENSOR_SD))
            lon, lat = to_deg(x, y)
            features.append({"type": "Feature", "properties": {"pm25": round(pm * 2) / 2},
                             "geometry": {"type": "Point", "coordinates": [lon, lat]}})
            x += GRID_M
        y += GRID_M

    out = {
        "type": "FeatureCollection",
        "name": "fengjia_air_mock",
        "mock": True,
        "note": f"MOCK DATA: modelled PM2.5 in µg/m³ on a {GRID_M:g} m sensor grid around the Feng Chia Night Market "
                f"(background, main roads, cooking at the mock booths, random sensor error; seed {SEED}); nothing here was measured.",
        "unit": "µg/m³",
        "pollutant": "PM2.5",
        "grid_m": GRID_M,
        "features": features,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    v = [f["properties"]["pm25"] for f in features]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} mock readings, PM2.5 {min(v)}-{max(v)} µg/m³; "
          f"{n_fry} of {len(stalls)} booths fry or grill, {len(roads)} road ways")


if __name__ == "__main__":
    main()
