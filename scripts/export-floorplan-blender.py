import bpy
import json
import math
import mathutils
import os
import sys

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 3:
    raise SystemExit("expected manifest, blend, png paths")
manifest_path, blend_path, png_path = args
with open(manifest_path, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
if manifest.get("schema") != "dmh-blender-scene-manifest-v1" or not manifest.get("source_geometry_hash"):
    raise SystemExit("invalid scene manifest")
if manifest.get("roof", {}).get("representation") != "deterministic_gable":
    raise SystemExit("geometry lock requires deterministic gable roof")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene["source_geometry_hash"] = manifest["source_geometry_hash"]
scene["presentation_hash"] = manifest["presentation_hash"]
scene["manifest_schema"] = manifest["schema"]
render_view = manifest.get("render_view", "garden")
if render_view not in {"garden", "street", "east", "west"}:
    raise SystemExit("unsupported render view")
scene["render_view"] = render_view
scale = 0.001

def material(name, color, metallic=0.0, roughness=0.5):
    item = bpy.data.materials.new(name)
    item.diffuse_color = (*color, 1.0)
    item.metallic = metallic
    item.roughness = roughness
    return item

wall_material = material("wall-material", (0.78, 0.76, 0.72), roughness=0.75)
frame_material = material("frame-material", (0.06, 0.07, 0.08), metallic=0.2, roughness=0.32)
door_material = material("door-material", (0.12, 0.13, 0.14), metallic=0.1, roughness=0.4)
glass_material = material("glass-material", (0.15, 0.32, 0.42), metallic=0.05, roughness=0.12)
roof_material = material("roof-material", (0.09, 0.10, 0.11), metallic=0.05, roughness=0.7)
slab_material = material("slab-material", (0.48, 0.48, 0.46), roughness=0.85)

def box(name, location, dimensions, assigned_material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if assigned_material:
        obj.data.materials.append(assigned_material)
    return obj

def slab(item):
    polygon = item["polygon_mm"]
    z = (item["base_z_mm"] - item["thickness_mm"] / 2) * scale
    vertices = [(point[0] * scale, point[1] * scale, z) for point in polygon]
    mesh = bpy.data.meshes.new("slab-mesh")
    mesh.from_pydata(vertices, [], [list(range(len(vertices)))])
    obj = bpy.data.objects.new("slab-" + str(item["base_z_mm"]), mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(slab_material)
    solidify = obj.modifiers.new("slab-thickness", "SOLIDIFY")
    solidify.thickness = item["thickness_mm"] * scale

def apply_boolean_difference(target, cutter):
    modifier = target.modifiers.new("opening-void", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    cutter.select_set(False)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    target.select_set(False)

def opening_center(opening, wall):
    x1, y1 = wall["start_mm"]
    x2, y2 = wall["end_mm"]
    position = opening["position"]
    return (
        (x1 + (x2 - x1) * position) * scale,
        (y1 + (y2 - y1) * position) * scale,
        (opening["base_z_mm"] + opening["sill_height_mm"] + opening["height_mm"] / 2) * scale,
    )

def add_frame_piece(name, center, dimensions, angle, z_offset=0.0):
    piece = box(name, (center[0], center[1], center[2] + z_offset), dimensions, frame_material)
    piece.rotation_euler[2] = angle
    return piece

def add_opening_assembly(opening, wall, center, angle):
    width = opening["width_mm"] * scale
    height = opening["height_mm"] * scale
    depth = max(0.06, wall["thickness_mm"] * scale * 0.18)
    frame = 0.075
    role = opening.get("role", "standard")
    is_glazed = opening["opening_type"] == "window" or opening.get("glazed") is True

    if is_glazed:
        glass = box("glass-" + opening["id"], center, (max(0.05, width - 2 * frame), depth * 0.35, max(0.05, height - 2 * frame)), glass_material)
        glass.rotation_euler[2] = angle
        add_frame_piece("frame-left-" + opening["id"], center, (frame, depth, height), angle, 0)
        local_x = math.cos(angle)
        local_y = math.sin(angle)
        for sign, suffix in [(-1, "left"), (1, "right")]:
            piece = bpy.context.collection.objects.get("frame-left-" + opening["id"]) if sign == -1 else None
            if sign == -1:
                piece.location.x = center[0] + local_x * sign * (width / 2 - frame / 2)
                piece.location.y = center[1] + local_y * sign * (width / 2 - frame / 2)
            else:
                piece = add_frame_piece("frame-right-" + opening["id"], center, (frame, depth, height), angle, 0)
                piece.location.x = center[0] + local_x * sign * (width / 2 - frame / 2)
                piece.location.y = center[1] + local_y * sign * (width / 2 - frame / 2)
        add_frame_piece("frame-top-" + opening["id"], center, (width, depth, frame), angle, height / 2 - frame / 2)
        add_frame_piece("frame-bottom-" + opening["id"], center, (width, depth, frame), angle, -height / 2 + frame / 2)
    else:
        panel = box("door-" + role + "-" + opening["id"], center, (max(0.1, width - 0.08), depth, max(0.1, height - 0.05)), door_material)
        panel.rotation_euler[2] = angle

for floor in manifest["floors"]:
    slab(floor["slab"])
    walls = {wall["id"]: wall for wall in floor["walls"]}
    wall_objects = {}
    for wall in floor["walls"]:
        x1, y1 = wall["start_mm"]
        x2, y2 = wall["end_mm"]
        length = wall["length_mm"] * scale
        obj = box(
            "wall-" + wall["id"],
            ((x1 + x2) * scale / 2, (y1 + y2) * scale / 2, (wall["base_z_mm"] + wall["height_mm"] / 2) * scale),
            (length, wall["thickness_mm"] * scale, wall["height_mm"] * scale),
            wall_material,
        )
        obj.rotation_euler[2] = math.atan2(y2 - y1, x2 - x1)
        wall_objects[wall["id"]] = obj

    for opening in floor["openings"]:
        wall = walls[opening["wall_id"]]
        wall_obj = wall_objects[opening["wall_id"]]
        x1, y1 = wall["start_mm"]
        x2, y2 = wall["end_mm"]
        angle = math.atan2(y2 - y1, x2 - x1)
        center = opening_center(opening, wall)
        cutter = box(
            "opening-void-" + opening["id"],
            center,
            (
                opening["width_mm"] * scale,
                wall["thickness_mm"] * scale + 0.12,
                opening["height_mm"] * scale,
            ),
        )
        cutter.rotation_euler[2] = angle
        apply_boolean_difference(wall_obj, cutter)
        add_opening_assembly(opening, wall, center, angle)

roof = manifest["roof"]
footprint = manifest["floors"][0]["slab"]["polygon_mm"]
min_x = min(point[0] for point in footprint) * scale
max_x = max(point[0] for point in footprint) * scale
min_y = min(point[1] for point in footprint) * scale
max_y = max(point[1] for point in footprint) * scale
center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2
roof_base = roof["base_z_mm"] * scale
overhang = roof["overhang_mm"] * scale
pitch = math.radians(roof["pitch_deg"])
roof_thickness = roof["thickness_mm"] * scale

def roof_plane(name, vertices):
    mesh = bpy.data.meshes.new(name + "-mesh")
    mesh.from_pydata(vertices, [], [[0, 1, 2, 3]])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(roof_material)
    solidify = obj.modifiers.new("roof-thickness", "SOLIDIFY")
    solidify.thickness = roof_thickness
    return obj

def gable_triangle(name, vertices):
    mesh = bpy.data.meshes.new(name + "-mesh")
    mesh.from_pydata(vertices, [], [[0, 1, 2]])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(wall_material)
    solidify = obj.modifiers.new("gable-thickness", "SOLIDIFY")
    solidify.thickness = 0.35
    return obj

if roof["ridge_axis"] == "x":
    ridge_y = center_y
    ridge_z = roof_base + ((max_y - min_y) / 2 + overhang) * math.tan(pitch)
    roof_plane("roof-plane-garden", [
        (min_x - overhang, ridge_y, ridge_z),
        (max_x + overhang, ridge_y, ridge_z),
        (max_x + overhang, max_y + overhang, roof_base),
        (min_x - overhang, max_y + overhang, roof_base),
    ])
    roof_plane("roof-plane-street", [
        (min_x - overhang, min_y - overhang, roof_base),
        (max_x + overhang, min_y - overhang, roof_base),
        (max_x + overhang, ridge_y, ridge_z),
        (min_x - overhang, ridge_y, ridge_z),
    ])
    gable_triangle("gable-west", [(min_x, min_y, roof_base), (min_x, max_y, roof_base), (min_x, ridge_y, ridge_z)])
    gable_triangle("gable-east", [(max_x, max_y, roof_base), (max_x, min_y, roof_base), (max_x, ridge_y, ridge_z)])
else:
    ridge_x = center_x
    ridge_z = roof_base + ((max_x - min_x) / 2 + overhang) * math.tan(pitch)
    roof_plane("roof-plane-east", [
        (ridge_x, min_y - overhang, ridge_z),
        (max_x + overhang, min_y - overhang, roof_base),
        (max_x + overhang, max_y + overhang, roof_base),
        (ridge_x, max_y + overhang, ridge_z),
    ])
    roof_plane("roof-plane-west", [
        (min_x - overhang, min_y - overhang, roof_base),
        (ridge_x, min_y - overhang, ridge_z),
        (ridge_x, max_y + overhang, ridge_z),
        (min_x - overhang, max_y + overhang, roof_base),
    ])
    gable_triangle("gable-street", [(min_x, min_y, roof_base), (max_x, min_y, roof_base), (ridge_x, min_y, ridge_z)])
    gable_triangle("gable-garden", [(max_x, max_y, roof_base), (min_x, max_y, roof_base), (ridge_x, max_y, ridge_z)])

bpy.ops.object.light_add(type="SUN", location=(4, -4, 12))
bpy.context.object.rotation_euler = (math.radians(28), 0, math.radians(35))
camera_spec = manifest["camera"]
camera_angle = math.radians(camera_spec["angle_deg"])
normal = camera_spec["outward_normal"]
adjacent = camera_spec["adjacent_normal"]
view_vector = (
    math.cos(camera_angle) * normal[0] + math.sin(camera_angle) * adjacent[0],
    math.cos(camera_angle) * normal[1] + math.sin(camera_angle) * adjacent[1],
)
footprint_span = max(max_x - min_x, max_y - min_y)
camera_distance = footprint_span * 2.8
camera_location = (
    center_x + view_vector[0] * camera_distance,
    center_y + view_vector[1] * camera_distance,
    max(8.5, roof_base + 3.0),
)
bpy.ops.object.camera_add(location=camera_location)
camera = bpy.context.object
camera.data.lens = camera_spec.get("focal_length_mm", 48)
target = (center_x, center_y, max(2.0, roof_base * 0.55))
camera.rotation_euler = ((mathutils.Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler())
scene.camera = camera

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = png_path
scene.world = bpy.data.worlds.new("World")
scene.world.color = (0.08, 0.08, 0.08)
os.makedirs(os.path.dirname(blend_path), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
bpy.ops.render.render(write_still=True)
with open(blend_path + ".metadata.json", "w", encoding="utf-8") as handle:
    json.dump({
        "source_geometry_hash": manifest["source_geometry_hash"],
        "presentation_hash": manifest["presentation_hash"],
        "manifest_schema": manifest["schema"],
        "render_view": render_view,
        "selected_facade_id": camera_spec["selected_facade_id"],
        "adjacent_facade_id": camera_spec["adjacent_facade_id"],
        "camera_angle_deg": camera_spec["angle_deg"],
        "camera_location": list(camera_location),
        "camera_target": list(target),
        "camera_distance": camera_distance,
        "camera_focal_length_mm": camera.data.lens,
        "footprint_span": footprint_span,
        "opening_ids": [opening["id"] for floor in manifest["floors"] for opening in floor["openings"]],
        "roof_representation": roof["representation"],
    }, handle, sort_keys=True)
