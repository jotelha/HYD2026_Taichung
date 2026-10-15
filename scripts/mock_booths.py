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
the extent.

Scores are spatially clustered rather than uniform: a smooth field over the
market starts at FIELD_BASE and adds FIELD_PEAKS Gaussian maxima and as many
minima (amplitude FIELD_AMP, width FIELD_SIGMA), centred on randomly chosen
booths at least FIELD_SPACING apart. Each booth's Boba Index is the field at
its position plus Gaussian noise (FIELD_NOISE); a draw outside 0.0-5.0 is
redrawn rather than clipped (a truncated normal), so no scores pile up at the
ends. Scores are rounded to 0.1. The noise is strong, so single booths vary a
lot, while the hot and cold spots show in averages such as the heat map. The field's centres are written to the output (score_field). A fixed
seed makes the output reproducible.

Each booth also gets an invented name in Chinese and English, built from the
patterns real stalls use (阿 + a given name, a surname + 記, a surname + a
title, a place of origin, optionally a descriptor such as 古早味 or 手工,
then the dish) and the dishes typical of Taiwanese night markets. Names come
from their own seed, so they can change without moving the scores. No name may
contain a real Feng Chia stall name (REAL_STALLS): a real stall shown with a
random score would read as a rating of that business.

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
# spatial score field (see the docstring)
FIELD_BASE = 2.5
FIELD_PEAKS = 3                # maxima, and as many minima
FIELD_AMP = (1.6, 2.3)         # bump height range, Boba Index points
FIELD_SIGMA = (40.0, 80.0)     # bump width range, metres
FIELD_SPACING = 120.0          # minimum distance between bump centres, metres
FIELD_NOISE = 2.5              # booth-to-booth noise (standard deviation, before truncation to 0-5)
BOOTH_W, BOOTH_D = 3.5, 3.0  # metres along and across the street
PITCH = 10.2                  # metres between booth centres along a street
MIN_GAP = 4.5                # minimum distance between booth centres
# half-width of the carriageway (metres) by OSM highway class; booths stand behind it
CARRIAGEWAY = {"tertiary": 6.0, "residential": 4.5, "service": 2.5}
STREET_EN = {"文華路": "Wenhua Road", "逢甲路": "Fengjia Road", "福星路": "Fuxing Road", "逢甲路20巷": "Fengjia Road Lane 20"}

# Name parts. Patterns and dishes follow night-market guides (e.g. TVBS 食尚玩家 and funtime.com.tw on Feng Chia,
# Smile Taiwan on Michelin-listed night-market stalls); the combinations themselves are invented.
OWNERS = [  # (zh, en)
    *[(f"阿{c}", f"A-{e}'s") for c, e in [("明", "Ming"), ("珠", "Zhu"), ("忠", "Zhong"), ("美", "Mei"), ("德", "De"), ("勇", "Yong"),
                                          ("芳", "Fang"), ("成", "Cheng"), ("龍", "Long"), ("雄", "Xiong"), ("鳳", "Feng"), ("輝", "Hui")]],
    ("阿嬤", "Grandma's"), ("阿伯", "Uncle's"), ("阿姨", "Auntie's"),
    *[(f"{c}記", f"{e}'s") for c, e in [("林", "Lin"), ("陳", "Chen"), ("黃", "Huang"), ("張", "Zhang"), ("李", "Li"), ("王", "Wang"),
                                        ("吳", "Wu"), ("劉", "Liu"), ("蔡", "Tsai"), ("楊", "Yang"), ("許", "Hsu"), ("鄭", "Cheng")]],
    ("林媽媽", "Mama Lin's"), ("陳姐", "Sister Chen's"), ("黃伯", "Old Huang's"), ("王老闆", "Boss Wang's"), ("張爸", "Papa Zhang's"),
    ("台南", "Tainan"), ("鹿港", "Lukang"), ("府城", "Old Capital"), ("嘉義", "Chiayi"), ("澎湖", "Penghu"), ("宜蘭", "Yilan"),
    ("東港", "Donggang"), ("大甲", "Dajia"), ("豐原", "Fengyuan"), ("北港", "Beigang"),
]
DESCRIPTORS = [("古早味", "Old-Style"), ("老牌", "Veteran"), ("正宗", "Original"), ("招牌", "Signature"), ("手工", "Handmade"),
               ("炭烤", "Charcoal"), ("現做", "Made-to-Order"), ("祖傳", "Heirloom"), ("排隊", "Queue-Worthy"), ("巨無霸", "Jumbo"),
               ("香酥", "Crispy"), ("超大", "Extra-Large")]
DISHES = [("臭豆腐", "Stinky Tofu"), ("大腸包小腸", "Sausage in Sticky Rice"), ("雞排", "Fried Chicken Cutlet"),
          ("蚵仔煎", "Oyster Omelette"), ("珍珠奶茶", "Bubble Tea"), ("蔥油餅", "Scallion Pancake"), ("胡椒餅", "Pepper Bun"),
          ("地瓜球", "Sweet Potato Balls"), ("章魚燒", "Takoyaki"), ("蚵仔麵線", "Oyster Vermicelli"), ("滷味", "Lu Wei"),
          ("鹽酥雞", "Popcorn Chicken"), ("烤玉米", "Grilled Corn"), ("豆花", "Tofu Pudding"), ("芋圓", "Taro Balls"),
          ("米血糕", "Rice Blood Cake"), ("潤餅", "Spring Roll"), ("刈包", "Gua Bao"), ("鐵板燒", "Teppanyaki"),
          ("串燒", "Skewers"), ("黑輪", "Oden"), ("綠豆冰沙", "Mung Bean Slush"), ("蛋餅", "Egg Crepe"),
          ("烤香腸", "Grilled Sausage"), ("甘蔗汁", "Sugarcane Juice"), ("麻糬", "Mochi"), ("車輪餅", "Wheel Cake"),
          ("牛肉捲", "Beef Roll"), ("烤魷魚", "Grilled Squid"), ("檸檬愛玉", "Lemon Aiyu")]
# real Feng Chia stalls named in the guides above; no mock name may contain these
REAL_STALLS = ["官芝霖", "明倫", "旺伯", "一心", "日船", "繼光", "香香雞", "天使", "丹丹", "金桑", "阿華", "海邊小屋",
               "金牌", "御品元", "惡魔", "梁記", "駱記", "阿國", "陳董", "福州世祖"]


def score_field(booths, rng):
    """Bump centres for the score field: (x, y, signed amplitude, sigma), on booths spaced FIELD_SPACING apart."""
    centres = []
    signs = [1] * FIELD_PEAKS + [-1] * FIELD_PEAKS
    rng.shuffle(signs)
    for sign in signs:
        for _ in range(1000):
            b = rng.choice(booths)
            if all(math.hypot(b["x"] - c[0], b["y"] - c[1]) >= FIELD_SPACING for c in centres):
                centres.append((b["x"], b["y"], sign * rng.uniform(*FIELD_AMP), rng.uniform(*FIELD_SIGMA)))
                break
        else:
            raise SystemExit("could not place the score-field centres; lower FIELD_SPACING")
    return centres


def noisy_score(mean, rng):
    """mean + N(0, FIELD_NOISE), redrawn until it lies in 0.0-5.0 (the field itself may stray slightly outside)."""
    for _ in range(10000):
        v = mean + rng.gauss(0, FIELD_NOISE)
        if 0.0 <= v <= 5.0:
            return v
    raise SystemExit(f"no score in 0-5 around {mean:.2f}; FIELD_NOISE is too small for this field")


def field_at(x, y, centres):
    return FIELD_BASE + sum(a * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sg * sg)) for cx, cy, a, sg in centres)


def mock_names(n, rng):
    """n distinct (zh, en) stall names: owner or origin, sometimes a descriptor, then the dish."""
    names, seen = [], set()
    while len(names) < n:
        (oz, oe), (dz, de) = rng.choice(OWNERS), rng.choice(DISHES)
        xz, xe = rng.choice(DESCRIPTORS) if rng.random() < 0.45 else ("", "")
        zh = oz + xz + dz
        if zh in seen or any(r in zh for r in REAL_STALLS):
            continue
        seen.add(zh)
        names.append((zh, " ".join(w for w in (oe, xe, de) if w)))
    return names


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
    names = mock_names(len(booths), random.Random(SEED + 1))
    booths.sort(key=lambda b: (-b["y"], b["x"]))
    centres = score_field(booths, rng)
    features = []
    for i, b in enumerate(booths, 1):
        score = noisy_score(field_at(b["x"], b["y"], centres), rng)
        hw, hd = BOOTH_W / 2, BOOTH_D / 2
        corners = [(b["x"] + b["ux"] * sa * hw - b["uy"] * sb * hd, b["y"] + b["uy"] * sa * hw + b["ux"] * sb * hd)
                   for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
        features.append({
            "type": "Feature",
            "properties": {
                "id": f"FJ-{i:04d}",
                "name_zh": names[i - 1][0],
                "name_en": names[i - 1][1],
                "street_zh": b["street"],
                "street_en": STREET_EN.get(b["street"], ""),
                "boba_index": round(score, 1),
                "centre": list(to_deg(b["x"], b["y"])),
                "bearing_deg": round(math.degrees(math.atan2(b["ux"], b["uy"])) % 180, 1),
            },
            "geometry": {"type": "Polygon", "coordinates": [[list(to_deg(x, y)) for x, y in corners]]},
        })

    out = {
        "type": "FeatureCollection",
        "name": "fengjia_booths_mock",
        "mock": True,
        "note": "MOCK DATA: booth positions are laid out along the market streets, names are invented and Boba Index scores are random "
                f"around invented hot and cold spots (seed {SEED}); nothing here describes real booths.",
        "score_field": {"base": FIELD_BASE, "noise_sd": FIELD_NOISE, "centres": [
            {"lonlat": list(to_deg(cx, cy)), "amplitude": round(a, 2), "sigma_m": round(sg, 1)} for cx, cy, a, sg in centres]},
        "booth_size_m": [BOOTH_W, BOOTH_D],
        "pitch_m": PITCH,
        "features": features,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    counts = {}
    for f in features:
        counts[f["properties"]["street_zh"]] = counts.get(f["properties"]["street_zh"], 0) + 1
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} mock booths {counts}")


if __name__ == "__main__":
    main()
