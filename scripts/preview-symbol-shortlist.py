# Render every shortlisted model to a thumbnail, grouped by symbol.
#
# The shortlist narrows 741 models to ~180 candidates by measurement, but
# measurement cannot tell a bath from a shower tray of similar size, and the
# filenames say nothing. This turns the shortlist into pictures so the choice
# can be made by looking.
#
# One PNG per candidate, named so the ranking is visible in the filename:
#   tmp/model-previews/<symbol>/<rank>_<err>_<file>.png
#
# Models are imported, framed and dropped, one at a time. A failed import is
# reported and skipped rather than killing the batch — some converted FBX files
# are macOS resource-fork stubs and contain no geometry at all.
#
# Usage:
#   blender --background --python scripts/preview-symbol-shortlist.py -- <shortlist.json> <out_dir>

import bpy
import json
import math
import mathutils
import os
import sys

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) < 2:
    raise SystemExit("expected: <shortlist.json> <out_dir>")
shortlist_path, out_root = args[0], args[1]

RESOLUTION = 420

with open(shortlist_path, "r", encoding="utf-8") as handle:
    shortlist = json.load(handle)["shortlist"]


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def imported_objects(before):
    return [obj for obj in bpy.context.scene.objects if obj not in before]


def bounds(objects):
    minimums = [math.inf] * 3
    maximums = [-math.inf] * 3
    found = False
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for axis in range(3):
                minimums[axis] = min(minimums[axis], world[axis])
                maximums[axis] = max(maximums[axis], world[axis])
            found = True
    return (minimums, maximums) if found else None


def build_stage(minimums, maximums):
    """Neutral backdrop, three-point-ish light, camera framing the object."""
    centre = mathutils.Vector([(minimums[i] + maximums[i]) / 2 for i in range(3)])
    size = max(maximums[i] - minimums[i] for i in range(3)) or 1.0

    bpy.ops.mesh.primitive_plane_add(size=size * 20,
                                     location=(centre.x, centre.y, minimums[2]))
    ground = bpy.context.active_object
    material = bpy.data.materials.new("backdrop")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1)
    ground.data.materials.append(material)

    camera_data = bpy.data.cameras.new("preview-camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = size * 1.5
    camera = bpy.data.objects.new("preview-camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    direction = mathutils.Vector((1.0, -1.2, 0.75)).normalized()
    camera.location = centre + direction * size * 3
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bpy.context.scene.camera = camera

    key = bpy.data.lights.new("key", type="AREA")
    key.energy = size * size * 900
    key.size = size * 2
    key_object = bpy.data.objects.new("key", key)
    key_object.location = centre + mathutils.Vector((size * 2, -size * 2, size * 2.5))
    key_object.rotation_euler = mathutils.Vector((-1, 1, -1)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(key_object)

    world = bpy.data.worlds.new("preview-world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.63, 0.68, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    bpy.context.scene.world = world


def render(path):
    scene = bpy.context.scene
    # Blender 5.0 dropped the BLENDER_EEVEE_NEXT identifier that 4.x used and
    # went back to BLENDER_EEVEE. Pick whichever this build actually offers.
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = RESOLUTION
    scene.render.resolution_y = RESOLUTION
    scene.render.filepath = path
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)


total = 0
failed = []
for symbol, candidates in shortlist.items():
    if not candidates:
        continue
    directory = os.path.join(out_root, symbol)
    os.makedirs(directory, exist_ok=True)
    for rank, candidate in enumerate(candidates):
        name = f"{rank:02d}_{int(candidate['size_error'] * 1000):04d}_{os.path.splitext(candidate['file'])[0]}"
        out_path = os.path.join(directory, f"{name}.png")
        if os.path.exists(out_path):
            continue

        clear()
        before = set(bpy.context.scene.objects)
        try:
            bpy.ops.import_scene.fbx(filepath=candidate["path"])
        except Exception as error:                       # noqa: BLE001
            failed.append((symbol, candidate["file"], str(error)[:80]))
            continue

        objects = imported_objects(before)
        extent = bounds(objects)
        if extent is None:
            failed.append((symbol, candidate["file"], "no mesh geometry"))
            continue

        build_stage(*extent)
        render(out_path)
        total += 1
        print(f"[preview] {symbol:20} {candidate['file']}")

print(f"[preview] rendered {total}")
for symbol, file, reason in failed:
    print(f"[preview] FAILED {symbol:20} {file}: {reason}")
