"""Generate MOCK booths for the Feng Chia Night Market, each with a random Boba Index.

Nothing here is surveyed: booth positions are laid out along both sides of the
market streets and the scores are random. The data exists so the Boba Index
map can be designed before real booth data is collected.

Reads the street centrelines and the extent polygon from
data/derived/fengjia_night_market_extent.geojson (scripts/fengjia_extent.py).
Along each street, booths of BOOTH_W x BOOTH_D metres sit every PITCH metres on
both sides, set back from the centreline by half the carriageway (CARRIAGEWAY,
by OSM highway class). A booth is skipped if it would stand in another street's
carriageway (at junctions), overlap a booth already placed, or fall outside
the extent. Each booth gets a Boba Index drawn uniformly from 0.0 to 5.0 in
steps of 0.1, from a fixed seed so the output is reproducible.

Writes data/derived/fengjia_booths_mock.geojson. Standard library only.
"""

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTENT = ROOT / "data" / "derived" / "fengjia_night_market_extent.geojson"
OUT = ROOT / "data" / "derived" / "fengjia_booths_mock.geojson"

SEED = 2026
BOOTH_W, BOOTH_D = 2.5, 2.0  # metres along and across the street
PITCH = 3.0                  # metres between booth centres along a street
MIN_GAP = 2.6                # minimum distance between booth centres
# half-width of the carriageway (metres) by OSM highway class; booths stand behind it
CARRIAGEWAY = {"tertiary": 6.0, "residential": 4.5, "service": 2.5}
STREET_EN = {"文華路": "Wenhua Road", "逢甲路": "Fengjia Road", "福星路": "Fuxing Road", "逢甲路20巷": "Fengjia Road Lane 20"}

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


def in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def walk(pts, step, start):
    """Points every `step` metres along a polyline, with the unit direction there."""
    s, out = start, []
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if seg == 0:
            continue
        ux, uy = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        while s <= seg:
            out.append(((a[0] + ux * s, a[1] + uy * s), (ux, uy)))
            s += step
        s -= seg
    return out


def main():
    fc = json.loads(EXTENT.read_text(encoding="utf-8"))
    extent = fc["features"][0]["geometry"]
    polys = [extent["coordinates"]] if extent["type"] == "Polygon" else extent["coordinates"]
    rings = [[[to_m(*c) for c in ring] for ring in poly] for poly in polys]
    streets = [{"name": f["properties"]["name_zh"],
                "half": CARRIAGEWAY.get(f["properties"]["highway"], 4.0),
                "pts": [to_m(*c) for c in f["geometry"]["coordinates"]]}
               for f in fc["features"][1:] if f["properties"].get("kind") == "street"]
    if not streets:
        raise SystemExit("no street centrelines in the extent file; rerun scripts/fengjia_extent.py")

    def inside(x, y):
        return any(in_ring(x, y, poly[0]) and not any(in_ring(x, y, h) for h in poly[1:]) for poly in rings)

    booths = []
    for st in sorted(streets, key=lambda s: -s["half"]):  # main streets claim their kerbs first
        set_back = st["half"] + BOOTH_D / 2
        for (px, py), (ux, uy) in walk(st["pts"], PITCH, PITCH / 2):
            for side in (1, -1):
                # left-hand normal of the walking direction, times side
                cx, cy = px - uy * set_back * side, py + ux * set_back * side
                if not inside(cx, cy):
                    continue
                # 0.5 m of slack keeps booths where one piece of a street continues the next
                if any(o is not st and line_dist((cx, cy), o["pts"]) < o["half"] + BOOTH_D / 2 - 0.5 for o in streets):
                    continue
                if any(math.hypot(cx - b["x"], cy - b["y"]) < MIN_GAP for b in booths):
                    continue
                booths.append({"x": cx, "y": cy, "ux": ux, "uy": uy, "street": st["name"]})

    rng = random.Random(SEED)
    features = []
    for i, b in enumerate(sorted(booths, key=lambda b: (-b["y"], b["x"])), 1):
        hw, hd = BOOTH_W / 2, BOOTH_D / 2
        corners = [(b["x"] + b["ux"] * sa * hw - b["uy"] * sb * hd, b["y"] + b["uy"] * sa * hw + b["ux"] * sb * hd)
                   for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
        features.append({
            "type": "Feature",
            "properties": {
                "id": f"FJ-{i:04d}",
                "street_zh": b["street"],
                "street_en": STREET_EN.get(b["street"], ""),
                "boba_index": round(rng.randint(0, 50) / 10, 1),
                "centre": list(to_deg(b["x"], b["y"])),
                "bearing_deg": round(math.degrees(math.atan2(b["ux"], b["uy"])) % 180, 1),
            },
            "geometry": {"type": "Polygon", "coordinates": [[list(to_deg(x, y)) for x, y in corners]]},
        })

    out = {
        "type": "FeatureCollection",
        "name": "fengjia_booths_mock",
        "mock": True,
        "note": "MOCK DATA: booth positions are laid out along the market streets and Boba Index scores are random (seed "
                f"{SEED}); nothing here describes real booths.",
        "booth_size_m": [BOOTH_W, BOOTH_D],
        "features": features,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    counts = {}
    for f in features:
        counts[f["properties"]["street_zh"]] = counts.get(f["properties"]["street_zh"], 0) + 1
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} mock booths {counts}")


if __name__ == "__main__":
    main()
