# Measure every converted FBX so models can be matched to furniture types by
# real-world size instead of by opening 1200 files by hand.
#
# CGAxis volumes are organised by category (BATHROOMS, BEDROOMS, KITCHEN
# APPLIANCES...) but individual files are named cgaxis_models_22_07.fbx, which
# says nothing about what the object is. Dimensions plus category narrow each
# furniture type to a handful of candidates; a thumbnail pass then confirms.
#
# Writes incrementally, so an interrupted run resumes rather than restarting.
#
# Usage:
#   blender --background --python scripts/catalog-fbx-library.py -- <library_root> <out.json>

import bpy
import json
import math
import mathutils
import os
import sys
import time

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 2:
    raise SystemExit("expected: <library_root> <out.json>")
library_root, out_path = args

# Written every N models so a crash or interrupt keeps the work done so far.
FLUSH_EVERY = 25


def find_fbx(root):
    found = []
    for folder, dirs, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".fbx"):
                found.append(os.path.join(folder, name))
    found.sort()
    return found


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def scene_dimensions():
    """Combined bounding box of every mesh in the scene, in Blender units."""
    minimums = [math.inf] * 3
    maximums = [-math.inf] * 3
    meshes = 0
    polygons = 0

    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        meshes += 1
        polygons += len(obj.data.polygons)
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for axis in range(3):
                minimums[axis] = min(minimums[axis], world[axis])
                maximums[axis] = max(maximums[axis], world[axis])

    if meshes == 0:
        return None
    return {
        "meshes": meshes,
        "polygons": polygons,
        "size": [maximums[i] - minimums[i] for i in range(3)],
        "min_z": minimums[2],
    }


def guess_unit_scale(size):
    """CGAxis exports are usually centimetres. Infer from the largest extent:
    furniture is roughly 0.3-3 m, so 30-300 reads as cm and 300-3000 as mm."""
    largest = max(size)
    if largest <= 0:
        return None, 0.0
    if largest < 30:
        return "m", 1000.0
    if largest < 300:
        return "cm", 10.0
    return "mm", 1.0


def main():
    files = find_fbx(library_root)
    total = len(files)
    print("[catalog] %d FBX under %s" % (total, library_root))

    existing = {}
    if os.path.isfile(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as handle:
                for item in json.load(handle).get("items", []):
                    existing[item["path"]] = item
            print("[catalog] resuming, %d already measured" % len(existing))
        except Exception:
            existing = {}

    items = []
    failed = 0
    started = time.time()

    def flush():
        folder = os.path.dirname(os.path.abspath(out_path))
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump({
                "schema": "dmh-fbx-library-catalog-v1",
                "library_root": library_root,
                "measured": len(items),
                "items": items,
            }, handle, indent=1)

    for index, path in enumerate(files, 1):
        if path in existing:
            items.append(existing[path])
            continue

        relative = os.path.relpath(path, library_root)
        category = relative.split(os.sep)[0]

        try:
            clear_scene()
            bpy.ops.import_scene.fbx(filepath=path)
            info = scene_dimensions()
            if info is None:
                raise RuntimeError("no mesh in file")

            unit, to_mm = guess_unit_scale(info["size"])
            items.append({
                "path": path,
                "file": os.path.basename(path),
                "category": category,
                "meshes": info["meshes"],
                "polygons": info["polygons"],
                "raw_size": [round(v, 4) for v in info["size"]],
                "guessed_unit": unit,
                "size_mm": [round(v * to_mm) for v in info["size"]],
            })
        except Exception as error:
            failed += 1
            items.append({
                "path": path,
                "file": os.path.basename(path),
                "category": category,
                "error": str(error),
            })

        if index % FLUSH_EVERY == 0 or index == total:
            flush()
            elapsed = time.time() - started
            rate = index / elapsed if elapsed > 0 else 0
            left = (total - index) / rate if rate > 0 else 0
            print("[catalog] %d/%d  failed %d  ~%d min left"
                  % (index, total, failed, left / 60))

    flush()
    print("[catalog] done: %d measured, %d failed" % (len(items), failed))
    print("[catalog] wrote %s" % out_path)


main()
