# Resolve each Hub model's true scale using what the model IS.
#
# The library holds at least three different authoring scales: title-case
# catalogue assets at 2.54x (inches read as Blender units), files named
# cgaxis_*_blender already at 1:1, and at least one at 100x. Two earlier
# attempts failed for opposite reasons — a plausibility heuristic was too weak
# and let a 813 mm toilet pass as a 2066 mm wardrobe, and a fixed 2.54 divisor
# was too strong and shrank a real sofa to 791 mm.
#
# The signal that actually works was there all along: the Hub NAMES its assets.
# A file called "Grey Three Seat Sofa" should measure about 2100 x 900 x 800, so
# the right divisor is whichever one lands closest to that. This is verification
# against a known target rather than inference from a number, which is the
# distinction that matters — every failure today came from trusting a
# measurement with nothing to check it against.
#
# Anything that matches no known type, or that lands badly at every candidate
# scale, is reported UNRESOLVED rather than guessed. A wrong scale is worse than
# a missing model: a missing model is visible, a wrong one just looks odd.
#
# Usage:
#   python scripts/resolve-hub-scales.py [catalog.json] [out.json]

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

CANDIDATE_DIVISORS = (1.0, 2.54, 10.0, 100.0, 1000.0)

# Expected real size per type, W x D x H mm, from the German dimensions already
# agreed. Matching is orientation-agnostic: the three dimensions are sorted
# before comparison, because whether a model was authored facing along x or y
# says nothing about how big it is.
#
# Keywords are matched longest-first, so "corner sofa" beats "sofa" and
# "front door" beats "door".
TYPES = [
    ("corner bathtube",   "corner_bath",   (1500, 1500, 600)),
    ("corner bath",       "corner_bath",   (1500, 1500, 600)),
    ("bathtube",          "bathtub",       (1700, 750, 580)),
    ("bathtub",           "bathtub",       (1700, 750, 580)),
    ("shower cabine",     "shower",        (900, 900, 2000)),
    ("square shower",     "shower",        (900, 900, 2000)),
    ("rectangular shower","shower",        (1200, 900, 2000)),
    ("toilet bowl",       "wc",            (380, 600, 800)),
    ("rouded toilet",     "wc",            (380, 600, 800)),
    ("rounded toilet",    "wc",            (380, 600, 800)),
    ("bidet",             "bidet",         (380, 550, 400)),
    # 2026-09-03 korrigiert: das Sollmass 1200 x 500 x 250 beschrieb ein
    # BECKEN, das Modell ist aber ein kompletter Doppelwaschtisch MIT
    # Unterschrank. Gegen ein Beckenmass gewann darum der Divisor 10 und
    # machte daraus 576 x 187 x 226 mm -- einen Waschtisch fuer Puppen. Mit
    # dem Mass eines echten Doppelwaschtisches gewinnt 2,54 und liefert
    # 2269 x 737 x 888, was das Modell tatsaechlich IST.
    ("double bathroom sink", "double_basin", (1600, 600, 850)),
    ("washbasin",         "basin",         (600, 450, 250)),
    ("bathroom sink",     "basin",         (600, 450, 250)),
    ("batroom sink",      "basin",         (600, 450, 250)),
    ("kitchen sink",      "kitchen_sink",  (900, 500, 200)),
    ("bathroom heater",   "towel_radiator",(600, 60, 1300)),
    ("towel hanger",      "towel_rail",    (500, 400, 1000)),
    ("washing machine",   "washer",        (600, 600, 850)),

    ("corner sofa",       "corner_sofa",   (2800, 2000, 800)),
    ("three seat sofa",   "sofa_3",        (2100, 900, 800)),
    ("2 seat",            "sofa_2",        (1700, 900, 800)),
    ("two seat sofa",     "sofa_2",        (1700, 900, 800)),
    ("classic sofa",      "sofa_3",        (2100, 900, 800)),
    ("modern sofa",       "sofa_3",        (2100, 900, 800)),
    ("sofa with pillows",  "sofa_3",       (2100, 900, 800)),
    ("sofa with wooden",  "sofa_3",        (2100, 900, 800)),
    ("leather sofa",      "sofa_3",        (2100, 900, 800)),
    ("sofa",              "sofa_3",        (2100, 900, 800)),
    ("armchair",          "armchair",      (900, 900, 800)),
    ("hocker",            "stool",         (600, 600, 450)),

    ("coffee table",      "coffee_table",  (1200, 600, 420)),
    ("parsons table",     "dining_table",  (1800, 900, 750)),
    ("dining table",      "dining_table",  (1800, 900, 750)),
    ("table and chairs",  "dining_set",    (1800, 900, 750)),
    ("glass topped table","coffee_table",  (1200, 600, 420)),
    ("glass table",       "dining_table",  (1800, 900, 750)),
    ("extension rectangular table", "dining_table", (1800, 900, 750)),
    ("dining chair",      "chair",         (500, 550, 900)),
    ("chair",             "chair",         (500, 550, 900)),

    ("bed with",          "bed",           (1800, 2000, 500)),
    ("bed",               "bed",           (1800, 2000, 500)),
    ("wardrobe",          "wardrobe",      (2000, 600, 2100)),
    ("cupboard",          "cupboard",      (1000, 600, 2000)),
    ("office cabinet",    "cabinet",       (900, 470, 1900)),
    ("cabinets",          "cabinet",       (900, 470, 1900)),
    ("cubby shelf",       "shelf",         (1000, 460, 1800)),

    ("desk workstation",  "desk",          (1600, 800, 720)),
    ("office desk",       "desk",          (1600, 800, 720)),
    ("desk",              "desk",          (1600, 800, 720)),
    ("office chair",      "office_chair",  (650, 650, 1100)),

    ("front door",        "front_door",    (1100, 250, 2100)),
    ("double glass door", "double_door",   (1700, 150, 2400)),
    ("door",              "door",          (1000, 200, 2100)),
    ("tv flatscreen",     "tv",            (1230, 300, 750)),
    ("kitchen furniture set", "kitchen_set", None),   # a scene, not one object

    # Kuechengeraete, ergaenzt 2026-09-03. Sie fehlten hier vollstaendig --
    # deshalb war KEIN einziges Modell vom Typ fridge oder hob im Katalog,
    # obwohl Refrigerator_2 seit Wochen entpackt danebenlag. Ohne Sollmass
    # kann `classify` nichts zuordnen und `resolve` nichts pruefen, und der
    # Planbauer setzte kuehlschrank und kochfeld darum immer prozedural.
    # Die Masse sind europaeische Norm-Einbaumasse.
    ("refrigerator",      "fridge",        (600, 650, 1800)),
    ("fridge",            "fridge",        (600, 650, 1800)),
    ("induction hob",     "hob",           (600, 520, 60)),
    ("hob",               "hob",           (600, 520, 60)),
    ("built in oven",     "oven",          (600, 570, 600)),
    ("built in double oven", "oven",       (600, 570, 900)),
    ("oven",              "oven",          (600, 570, 600)),
    ("built in microwave", "microwave",    (600, 400, 390)),
    ("electric cooker",   "cooker",        (600, 600, 900)),
    ("kitchen utensils",  "utensils",      (400, 300, 300)),
]

# How far a model may sit from its type's nominal size and still be accepted.
# Furniture genuinely varies, so this is generous — it only has to separate
# 2.54x from 1x, which is a factor of two and a half apart.
ACCEPT_RATIO = 0.55


def classify(label):
    """Match on WORDS present, not on substring.

    "grey corner modern sofa" does not contain the substring "corner sofa", so
    substring matching classed a corner sofa as a three-seater and then picked
    the scale that fitted a three-seater. Requiring every word of the key to
    appear, in any order, gets it right — and more specific keys still win,
    because they have more words to satisfy.
    """
    words = set(label.lower().replace("_", " ").replace("-", " ").split())
    best = None
    for needle, kind, expected in TYPES:
        needed = set(needle.split())
        if needed <= words and (best is None or len(needed) > best[0]):
            best = (len(needed), kind, expected)
    return (best[1], best[2]) if best else (None, None)


def error(size_mm, expected):
    """Orientation-agnostic fit: compare sorted dimensions."""
    got = sorted(size_mm, reverse=True)
    want = sorted(expected, reverse=True)
    total = 0.0
    for a, b in zip(got, want):
        if b <= 0:
            continue
        total += abs(a - b) / float(b)
    return total / 3.0


def main():
    catalog_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "tmp", "hub-model-catalog.json")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "tmp", "hub-models-resolved.json")

    with open(catalog_path, "r", encoding="utf-8") as handle:
        catalog = json.load(handle)

    resolved = []
    unresolved = []
    for entry in catalog["models"]:
        if "error" in entry:
            unresolved.append({"label": entry.get("label", entry["file"]),
                               "reason": entry["error"]})
            continue

        label = entry["label"]
        kind, expected = classify(label)
        raw = entry["raw_size_mm"]

        # CGAxis names windows with their actual dimensions, e.g.
        # "Metal Window 1180mm x 1260mm". A stated size beats a nominal one.
        stated = re.findall(r"(\d{3,4})\s*mm", label)
        if len(stated) >= 2:
            kind = kind or "window"
            expected = (int(stated[0]), 120, int(stated[1]))

        if kind is None:
            unresolved.append({"label": label, "reason": "no type matched the name"})
            continue

        if expected is None:
            # A staged scene rather than a single object. Its scale is settled
            # by the parts it contains, handled where kitchens are assembled.
            resolved.append({"label": label, "path": entry["path"], "type": kind,
                             "divisor": None, "size_mm": None,
                             "objects": entry["objects"],
                             "note": "scene; scale resolved per part"})
            continue

        best = None
        for divisor in CANDIDATE_DIVISORS:
            size = [v / divisor for v in raw]
            score = error(size, expected)
            if best is None or score < best[0]:
                best = (score, divisor, [round(v) for v in size])

        score, divisor, size = best
        if score > ACCEPT_RATIO:
            unresolved.append({"label": label, "type": kind, "raw_size_mm": raw,
                               "best_try": size, "expected_mm": list(expected),
                               "reason": f"no scale fits (best error {score:.2f})"})
            continue

        resolved.append({"label": label, "path": entry["path"], "type": kind,
                         "divisor": divisor, "size_mm": size,
                         "expected_mm": list(expected), "fit_error": round(score, 3),
                         "objects": entry["objects"]})

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({"schema": "dmh-hub-models-resolved-v1",
                   "resolved": resolved, "unresolved": unresolved}, handle, indent=1)

    by_divisor = {}
    for item in resolved:
        by_divisor[item["divisor"]] = by_divisor.get(item["divisor"], 0) + 1

    print(f"[scale] resolved {len(resolved)}, unresolved {len(unresolved)}")
    print(f"[scale] divisors used: {by_divisor}")
    for item in sorted(resolved, key=lambda i: i.get("fit_error") or 0, reverse=True)[:10]:
        if item.get("size_mm"):
            print(f"[scale] worst fit {item['fit_error']:.2f}  {item['label'][:40]:40} "
                  f"{item['size_mm']} vs {item['expected_mm']}")
    for item in unresolved:
        print(f"[scale] UNRESOLVED {item['label'][:44]:44} {item['reason']}")
    print(f"[scale] wrote {out_path}")


if __name__ == "__main__":
    main()
