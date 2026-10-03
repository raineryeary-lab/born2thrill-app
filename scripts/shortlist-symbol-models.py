# Shortlist external library models for each Ausstattung symbol.
#
# The library is 1160 converted FBX files named cgaxis_models_22_07.fbx and
# nothing more. The three hand-written overrides in
# data/furniture-model-overrides.json turned out to be wrong — the file mapped
# to "bathtub" measures 1145 x 501 x 934 mm, and a bath is 1700 x 750 x 580 —
# so guessing from filenames is not a method.
#
# What IS reliable is the measurement: tmp/fbx-library-catalog.json carries a
# real bounding box for every model. A bath is the only bathroom object that is
# 1.7 m long and 0.6 m tall, so size plus category narrows 1160 files to a
# handful that can then be judged by eye from a contact sheet.
#
# This script does the narrowing. It does not decide anything — it produces the
# shortlist that the preview render turns into pictures.
#
# Usage:
#   python scripts/shortlist-symbol-models.py [out.json]

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CATALOG = os.path.join(REPO, "tmp", "fbx-library-catalog.json")

# Expected real size, width x depth x height in mm, and the library categories
# worth searching. Width and depth come from the Simplifier catalogue; height
# is the missing third dimension a floorplan symbol cannot carry.
#
# Height matters more than it looks: width and depth alone cannot tell a shower
# tray from a bath panel, but 2000 mm of height can.
BATH = ["02 BARTHROOMS", "22 BATHROOMS"]
KITCHEN = ["10 KITCHEN APPLIANCES", "33 Kitchen Appliances", "86 KITCHEN FURNITURE"]
LIVING = ["07 FURNITURE", "17 FURNITURE II", "25 FURNITURE III", "38 Furniture IV",
          "68 FURNITURE V", "75 Furniture VI", "97 Furniture", "48_Modern Furniture"]
BED = ["27 BEDROOMS", "49 3D BEDROOMS II"]
KIDS = ["96 Kids Furniture"]
OFFICE = ["11 OFFICE FURNITURE", "80 Office Furniture II"]

TARGETS = {
    # key:               (width, depth, height, categories)
    "badewanne":         (1700, 750, 580, BATH),
    "eckbadewanne":      (1700, 760, 580, BATH),
    "dusche":            (930, 1360, 2000, BATH),
    "dusche_gross":      (990, 1200, 2000, BATH),
    "dusche_klein":      (800, 800, 2000, BATH),
    "wand_wc":           (360, 540, 400, BATH),
    "waschtisch":        (600, 550, 850, BATH),
    "doppelwaschtisch":  (1200, 450, 850, BATH),
    "handwaschbecken":   (450, 340, 850, BATH),
    "badheizkoerper":    (550, 100, 1200, BATH),

    "kuehlschrank":      (600, 600, 1800, KITCHEN),
    "hochschrank_herd":  (600, 600, 2100, KITCHEN),
    "kochfeld":          (600, 520, 50, KITCHEN),
    "spuele":            (500, 400, 200, KITCHEN),
    "waschmaschine":     (600, 600, 850, KITCHEN),
    "trockner":          (600, 600, 850, KITCHEN),

    "ecksofa":           (2600, 2000, 800, LIVING),
    "sofa_3sitzer":      (2100, 900, 800, LIVING),
    "sofa_2sitzer":      (1600, 900, 800, LIVING),
    "sofa_1sitzer":      (900, 900, 800, LIVING),
    "hocker":            (600, 600, 450, LIVING),
    "couchtisch":        (1100, 600, 400, LIVING),
    "lowboard":          (1800, 400, 500, LIVING),
    "sideboard":         (1600, 450, 800, LIVING),
    "fernseher":         (1200, 80, 700, LIVING),
    "essgruppe_6":       (1800, 900, 750, LIVING),

    "doppelbett":        (1800, 2000, 500, BED),
    "einzelbett":        (900, 2000, 500, BED),
    "kleiderschrank":    (2000, 600, 2100, BED),
    "schrank_60":        (600, 600, 2100, BED),
    "schrank_40":        (400, 600, 2100, BED),
    "schreibtisch":      (1600, 800, 750, OFFICE),
    "schreibtisch_kind": (1200, 600, 720, KIDS),
    "garderobe":         (1000, 350, 1900, LIVING),
}

# How far off a candidate may be before it stops being that object. Furniture
# genuinely varies — sofas come in every length — so this is deliberately loose
# on the two floor dimensions and tighter on height, which is the dimension
# that distinguishes categories of object rather than sizes of one object.
PLAN_TOLERANCE = 0.35
HEIGHT_TOLERANCE = 0.45

# A percentage tolerance is unfair to thin objects. A hob is 50 mm thick and a
# TV panel 80 mm deep, so 35 % is +/- 20 mm — tighter than the difference
# between modelling a hob with or without its worktop cutout. The first run
# found no candidate at all for the hob, the TV and the towel radiator for
# exactly this reason. Every dimension therefore gets an absolute floor as
# well, and whichever allowance is larger applies.
PLAN_FLOOR_MM = 200
HEIGHT_FLOOR_MM = 300


def score(size_mm, target):
    """Lower is better; None if the candidate is not this object at all.

    Both floor orientations are tried, because whether a model was authored
    facing along x or along y says nothing about what it is.
    """
    tw, td, th = target
    best = None
    for cw, cd in ((tw, td), (td, tw)):
        errors = []
        for got, want, tolerance, floor_mm in (
                (size_mm[0], cw, PLAN_TOLERANCE, PLAN_FLOOR_MM),
                (size_mm[1], cd, PLAN_TOLERANCE, PLAN_FLOOR_MM),
                (size_mm[2], th, HEIGHT_TOLERANCE, HEIGHT_FLOOR_MM)):
            if want <= 0:
                continue
            allowed = max(tolerance * want, floor_mm)
            deviation = abs(got - want)
            if deviation > allowed:
                errors = None
                break
            # Scored against the allowance, so a 20 mm miss on a hob and a
            # 200 mm miss on a sofa rank as equally good fits.
            errors.append(deviation / allowed)
        if errors is None:
            continue
        total = sum(errors) / len(errors)
        if best is None or total < best:
            best = total
    return best


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "tmp", "symbol-model-shortlist.json")
    with open(CATALOG, "r", encoding="utf-8") as handle:
        catalog = json.load(handle)

    # The catalogue lists the same model twice where a set ships both a C4D and
    # a C4DVRAY folder. Same geometry, same size — keep one.
    seen = set()
    items = []
    for item in catalog["items"]:
        fingerprint = (item["file"], tuple(item["size_mm"]))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        items.append(item)

    shortlist = {}
    for key, (width, depth, height, categories) in TARGETS.items():
        allowed = set(categories)
        scored = []
        for item in items:
            if item.get("category") not in allowed:
                continue
            value = score(item["size_mm"], (width, depth, height))
            if value is None:
                continue
            scored.append((value, item))
        scored.sort(key=lambda pair: pair[0])
        shortlist[key] = [
            {
                "path": item["path"],
                "file": item["file"],
                "category": item["category"],
                "size_mm": item["size_mm"],
                "polygons": item["polygons"],
                "size_error": round(value, 4),
            }
            for value, item in scored[:12]
        ]

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({
            "schema": "dmh-symbol-model-shortlist-v1",
            "library_root": catalog["library_root"],
            "unique_models": len(items),
            "shortlist": shortlist,
        }, handle, indent=1)

    empty = [key for key, rows in shortlist.items() if not rows]
    total = sum(len(rows) for rows in shortlist.values())
    print(f"[shortlist] {len(items)} unique models, {total} candidates across {len(shortlist)} symbols")
    print(f"[shortlist] no candidate found for: {', '.join(empty) if empty else 'none'}")
    for key in sorted(shortlist):
        rows = shortlist[key]
        head = rows[0] if rows else None
        print(f"  {key:20} {len(rows):2} candidates"
              + (f"  best {head['file']} {head['size_mm']} err={head['size_error']}" if head else ""))
    print(f"[shortlist] written to {out_path}")


if __name__ == "__main__":
    main()
