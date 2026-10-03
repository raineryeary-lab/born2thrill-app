"""Both storeys in ONE scene: the whole house, upper floor cut through.

Rainer, 2026-08-18: "i want to see the whole house but with the upper floor
cut through ... the people are looking at the floors and it looks as if the
upper floor is a second ground floor."

Rendering each storey on its own is what caused that: an Obergeschoss alone,
sitting on the ground, reads as another ground floor. Stacked on the storey
it actually belongs to, it reads as what it is.

This appends the already-built storey scenes rather than rebuilding them, so
every rule that passed in those files still holds here -- the Obergeschoss
blend already carries its +2800mm elevation.

Usage:
  blender --background --python scripts/assemble-house.py -- \
      <ground.blend> <upper.blend> <out.png> [--save house.blend]
"""
import math
import os
import sys

import bpy
import mathutils

MM = 0.001

args = sys.argv[sys.argv.index("--") + 1:]
ground_blend, upper_blend, out_png = args[0], args[1], args[2]
save_blend = args[args.index("--save") + 1] if "--save" in args else None

bpy.ops.wm.open_mainfile(filepath=ground_blend)

# Everything that is scenery rather than building: the ground plane belongs to
# the ground floor only, and the upper storey's copy would hang in mid-air.
DROP = ("ground", "cut-solid", "flat-cut-solid", "treppenloch", "source-underlay")

before = set(bpy.data.objects.keys())
with bpy.data.libraries.load(upper_blend, link=False) as (source, target):
    target.objects = [n for n in source.objects
                      if not n.startswith(DROP) and "camera" not in n.lower()
                      and "sun" not in n.lower() and "key" not in n.lower()]
linked = 0
for obj in target.objects:
    if obj is None:
        continue
    bpy.context.scene.collection.objects.link(obj)
    linked += 1
bpy.context.view_layer.update()
print(f"[house] appended {linked} objects from the upper storey")

# Frame the whole building.
points = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH" or not len(obj.data.vertices) or obj.hide_render:
        continue
    if obj.name.startswith(DROP):
        continue
    points += [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
lo = [min(p[i] for p in points) for i in range(3)]
hi = [max(p[i] for p in points) for i in range(3)]
centre = mathutils.Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))
span = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
print(f"[house] extent x {lo[0]:.1f}..{hi[0]:.1f}  y {lo[1]:.1f}..{hi[1]:.1f}  "
      f"z {lo[2]:.1f}..{hi[2]:.1f} m")

camera = bpy.context.scene.camera
if camera is None:
    camera = bpy.data.objects.new("house-camera", bpy.data.cameras.new("house-camera"))
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera
direction = mathutils.Vector((1.0, -1.0, 0.95)).normalized()
camera.location = centre + direction * span * 2.05
look = centre - camera.location
camera.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 42

bpy.context.scene.render.filepath = os.path.abspath(out_png)
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print(f"[house] wrote {out_png}")
if save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save_blend))
    print(f"[house] saved {save_blend}")
