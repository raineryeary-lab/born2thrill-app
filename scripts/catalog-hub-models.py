# Measure every .blend in the Hub library and write a typed catalogue.
#
# The Hub assets arrive NAMED, which solves the identification problem that the
# 741 converted FBX files never solved. What they do not arrive with is a
# guaranteed scale: the kitchen sets are out by exactly 2.54, and a model whose
# size is wrong is as useless as one whose type is wrong — that is how a vanity
# unit ended up standing in for a bath.
#
# So this measures rather than trusts. For each file it reports the raw bounding
# box, and a suggested scale correction where the raw size is implausible for
# furniture. It does not silently apply anything: a guessed scale factor is
# exactly the sort of unverified assumption that cost a day.
#
# Kitchen sets ship as whole scenes — walls, floor, ceiling — alongside the
# cabinets that matter, and a 4 m wall would swamp the bounding box if it
# weren't told apart from the furniture.
#
# This used to EXCLUDE anything past a size threshold outright, on the theory
# that it must be a room shell. That silently threw away real furniture: a
# double glass door (2440mm tall) and a wardrobe (its 3082mm-wide main
# carcass, a legitimate multi-door wardrobe, not a wall) both lost objects
# this way — one of them lost every single object and catalogued with zero
# usable parts. A guessed size threshold cannot tell a wide wardrobe from a
# wide wall; only a human deciding what to place can. So this only FLAGS —
# every object survives in `parts` with its measured size; `large: true`
# marks anything past the threshold for a human (or a downstream picker with
# more context, like the target footprint) to judge. Nothing is ever
# dropped here.
#
# Usage:
#   blender --background --python scripts/catalog-hub-models.py -- <root> <out.json>

import bpy
import json
import math
import mathutils
import os
import sys

args = sys.argv[sys.argv.index("--") + 1:]
root, out_path = args[0], args[1]

# Anything wider or deeper than this, after scaling, is flagged `large` —
# worth a second look before placing, not excluded from the catalogue.
SHELL_WIDTH_MM = 3000

# Plausible extent for a single piece of furniture, longest dimension.
PLAUSIBLE_MIN_MM = 150
PLAUSIBLE_MAX_MM = 3500

# The whole Hub library is authored at 2.54x — inches read as Blender units.
#
# The first pass tried to infer this per file, correcting only where the longest
# dimension fell outside furniture range. That let anything plausible-looking
# slip through uncorrected: a WC measuring 2066 mm tall passed as a wardrobe,
# when it is an 813 mm toilet. Checked against known dimensions, a fixed divisor
# lands every one of them — a coffee table on 1200 x 600 x 410, a washing
# machine on 600 x 800. A constant beats a guess.
HUB_SCALE_DIVISOR = 2.54

# Some files contain degenerate objects — empties or lattices with enormous
# transforms — that would otherwise swamp the bounding box with numbers like
# 1e30. Anything past this is not geometry.
ABSURD_MM = 100000


def measure(objects):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    found = False
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])
            found = True
    if not found:
        return None
    return [round((hi[a] - lo[a]) * 1000) for a in range(3)]


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(path, link=False) as (source, target):
        target.objects = list(source.objects)
    meshes = []
    for obj in target.objects:
        if obj and obj.type == "MESH" and obj.data and len(obj.data.vertices):
            bpy.context.scene.collection.objects.link(obj)
            meshes.append(obj)
    bpy.context.view_layer.update()
    return meshes


def sane(size_mm):
    return size_mm is not None and max(size_mm) < ABSURD_MM


# Some archives were extracted twice (Kitchen Furniture Set 9 exists at both
# `Kitchen_Furniture_Set_9\` and `Kitchen_Furniture_Set_9_BLEND\`, confirmed
# byte-identical). Cataloguing both risked a picker resolving to either copy
# nondeterministically. Group by content hash first and catalogue each
# distinct file once, preferring the `_BLEND`-suffixed folder since that is
# the naming convention every other single-model extraction uses.
def content_hash(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


all_blend_paths = []
for directory, _, files in os.walk(root):
    for name in sorted(files):
        if name.lower().endswith(".blend"):
            all_blend_paths.append(os.path.join(directory, name))

by_hash = {}
for path in all_blend_paths:
    by_hash.setdefault(content_hash(path), []).append(path)

canonical_paths = []
duplicates_skipped = []
for digest, paths in by_hash.items():
    if len(paths) == 1:
        canonical_paths.append(paths[0])
        continue
    blend_suffixed = [p for p in paths if os.path.basename(os.path.dirname(p)).endswith("_BLEND")]
    keep = sorted(blend_suffixed or paths)[0]
    canonical_paths.append(keep)
    for p in sorted(paths):
        if p != keep:
            duplicates_skipped.append((p, keep))

if duplicates_skipped:
    print(f"[hub] {len(duplicates_skipped)} duplicate extraction(s) skipped (byte-identical to a catalogued copy):")
    for dupe, keep in duplicates_skipped:
        print(f"       {dupe}")
        print(f"       -> kept {keep}")

entries = []
for path in sorted(canonical_paths):
    name = os.path.basename(path)
    try:
        meshes = load(path)
    except Exception as error:                       # noqa: BLE001
        entries.append({"file": name, "path": path, "error": str(error)[:120]})
        print(f"[hub] FAILED {name}: {str(error)[:80]}")
        continue

    if not meshes:
        entries.append({"file": name, "path": path, "error": "no mesh geometry"})
        continue

    meshes = [obj for obj in meshes if sane(measure([obj]))]
    if not meshes:
        entries.append({"file": name, "path": path, "error": "no sane geometry"})
        print(f"[hub] SKIPPED {name}: degenerate transforms only")
        continue

    raw = measure(meshes)
    factor = HUB_SCALE_DIVISOR
    corrected = [round(v / factor) for v in raw]

    # Every object is kept. `large` flags anything wider or deeper than
    # SHELL_WIDTH_MM for a human to judge — it does not remove it.
    pieces = []
    large_count = 0
    for obj in meshes:
        size = measure([obj])
        if not size:
            continue
        scaled = [v / factor for v in size]
        is_large = max(scaled[0], scaled[1]) > SHELL_WIDTH_MM
        if is_large:
            large_count += 1
        pieces.append({"name": obj.name, "size_mm": [round(v) for v in scaled],
                        "large": is_large})

    entries.append({
        "file": name,
        "path": path,
        "label": os.path.splitext(name)[0],
        "objects": len(meshes),
        "raw_size_mm": raw,
        "scale_divisor": factor,
        "size_mm": corrected,
        "large_objects": large_count,
        "parts": pieces,
        "materials": len(bpy.data.materials),
    })
    flag = "" if factor == 1.0 else f"  /{factor}"
    print(f"[hub] {os.path.splitext(name)[0][:44]:44} {corrected} "
          f"objects={len(meshes)} large={large_count}{flag}")

with open(out_path, "w", encoding="utf-8") as handle:
    json.dump({"schema": "dmh-hub-model-catalog-v1", "root": root,
               "count": len(entries), "models": entries}, handle, indent=1)

good = [e for e in entries if "error" not in e]
rescaled = [e for e in good if e["scale_divisor"] != 1.0]
print(f"[hub] catalogued {len(good)} models, {len(entries) - len(good)} failed")
print(f"[hub] {len(rescaled)} needed a scale correction")
print(f"[hub] wrote {out_path}")
