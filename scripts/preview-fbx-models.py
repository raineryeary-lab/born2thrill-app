# Render preview thumbnails of converted FBX models so they can be judged and
# identified without opening each one by hand.
#
# CGAxis files are named cgaxis_models_22_07.fbx, which says nothing about what
# the object is. This renders each to its own PNG on a neutral backdrop, at a
# consistent camera angle, with the real bounding box printed to the console.
#
# Usage:
#   blender --background --python scripts/preview-fbx-models.py -- <folder> <out_dir> [limit]

import bpy
import math
import mathutils
import os
import sys

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) < 2:
    raise SystemExit("expected: <folder> <out_dir> [limit]")
folder = args[0]
out_dir = args[1]
limit = int(args[2]) if len(args) > 2 else 12

RESOLUTION = 640


def scene_bounds():
    minimums = [math.inf] * 3
    maximums = [-math.inf] * 3
    found = False
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        found = True
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for axis in range(3):
                minimums[axis] = min(minimums[axis], world[axis])
                maximums[axis] = max(maximums[axis], world[axis])
    if not found:
        return None
    return minimums, maximums


def build_environment():
    world = bpy.data.worlds.new("preview-world")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.85, 0.86, 0.88, 1.0)
    background.inputs["Strength"].default_value = 1.2
    bpy.context.scene.world = world

    sun_data = bpy.data.lights.new("preview-sun", type="SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("preview-sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-50))


def frame_and_render(out_path):
    bounds = scene_bounds()
    if bounds is None:
        return None
    minimums, maximums = bounds
    centre = mathutils.Vector([(minimums[i] + maximums[i]) / 2 for i in range(3)])
    size = [maximums[i] - minimums[i] for i in range(3)]
    span = max(size) or 1.0

    # Ground plane so the object reads as standing on something.
    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(centre.x, centre.y, minimums[2]))
    plane = bpy.context.object
    plane_material = bpy.data.materials.new("preview-ground")
    plane_material.use_nodes = True
    plane_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.76, 0.78, 1.0)
    plane.data.materials.append(plane_material)

    camera_data = bpy.data.cameras.new("preview-camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = span * 1.6
    camera = bpy.data.objects.new("preview-camera", camera_data)
    bpy.context.collection.objects.link(camera)
    direction = mathutils.Vector((1.0, -1.2, 0.7)).normalized()
    camera.location = centre + direction * (span * 3.0)
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    bpy.context.scene.camera = camera

    build_environment()

    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = RESOLUTION
    scene.render.resolution_y = RESOLUTION
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    return size


def main():
    files = sorted(
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.lower().endswith(".fbx")
    )[:limit]

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    print("[preview] %d models from %s" % (len(files), folder))
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        out_path = os.path.join(out_dir, name + ".png")
        try:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=path)
            size = frame_and_render(out_path)
            if size is None:
                print("  %-44s NO MESH" % name)
                continue
            print("  %-44s %6.0f x %6.0f x %6.0f  (raw units)"
                  % (name, size[0], size[1], size[2]))
        except Exception as error:
            print("  %-44s FAILED: %s" % (name, error))

    print("[preview] wrote to %s" % out_dir)


main()
