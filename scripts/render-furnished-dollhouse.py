# Furnished dollhouse cutaway render — proof of pipeline.
#
# Consumes a render plan from scripts/build-furnished-render-plan.mjs and
# produces a PNG: room floor plates with real textures, cutaway walls, and
# furniture instanced from the generated .glb library, lit by an HDRI.
#
# Deliberately standalone. It does not touch export-floorplan-blender.py, the
# scene manifest, or geometry_hash. Furniture is presentation data only.
#
# External texture/HDRI assets are optional. If TEXTURE_ROOT is unavailable
# every material falls back to a flat colour and the render still completes.
#
# Usage:
#   blender --background --python scripts/render-furnished-dollhouse.py -- <plan.json> <out.png>

import bpy
import json
import math
import mathutils
import os
import sys

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 2:
    raise SystemExit("expected: <render-plan.json> <output.png>")
plan_path, out_path = args

with open(plan_path, "r", encoding="utf-8") as handle:
    plan = json.load(handle)
if plan.get("schema") != "dmh-furnished-render-plan-proof-v1":
    raise SystemExit("invalid render plan schema")

MM = 0.001  # millimetres -> Blender metres

# Reset the file BEFORE creating any data. read_factory_settings wipes every
# datablock, so anything built above this line becomes a dangling reference.
bpy.ops.wm.read_factory_settings(use_empty=True)

# ------------------------------------------------------------ external assets

TEXTURE_ROOT = os.environ.get("DMH_TEXTURE_ROOT", r"E:\_maps")

HDRI = os.path.join(TEXTURE_ROOT, r"BG\hdr\spericalhdris\cloud_layers_4k.hdr")
WOOD_DIFFUSE = os.path.join(TEXTURE_ROOT, r"Floors\Oak_01\VizPeople_Oak_1_Diffuse_1.jpg")

# CGAxis grey_freckled_granite rendered blue enough to read as carpet.
# Stone/granit-hell.jpg is a true white-and-black speckled granite. It ships
# without a normal map, so polish comes from low roughness instead.
GRANITE_DIFFUSE = os.path.join(TEXTURE_ROOT, r"Stone\granit-hell.jpg")
GRANITE_NORMAL = None

# Real-world size of one texture repeat, in metres. Wrong values here are the
# usual reason a textured floor reads as either wallpaper or mush.
WOOD_TILE_SIZE_M = 2.0
GRANITE_TILE_SIZE_M = 0.6  # standard granite slab format

missing_assets = []


def asset(path):
    if os.path.isfile(path):
        return path
    missing_assets.append(path)
    return None


# ---------------------------------------------------------------- materials

def flat(name, color, roughness=0.6, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    mat.diffuse_color = (*color, 1.0)
    return mat


def textured(name, image_path, tile_size_m, roughness, fallback_color, normal_path=None):
    """Image-textured material tiled at real-world scale.

    Floor plates are built from raw polygons and have no UV map, so this uses
    Object coordinates. The mesh is created with world coordinates and its
    origin at 0, so object space == world space and every room tiles on the
    same grid rather than stretching to each room's bounding box."""
    path = asset(image_path)
    if path is None:
        return flat(name, fallback_color, roughness)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = roughness

    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0 / tile_size_m, 1.0 / tile_size_m, 1.0)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.extension = "REPEAT"

    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    # A normal map is what makes stone read as stone rather than as a
    # photograph printed on a flat plane.
    normal_file = asset(normal_path) if normal_path else None
    if normal_file:
        normal_tex = nodes.new("ShaderNodeTexImage")
        normal_tex.image = bpy.data.images.load(normal_file)
        normal_tex.image.colorspace_settings.name = "Non-Color"
        normal_tex.extension = "REPEAT"
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = 0.6
        links.new(mapping.outputs["Vector"], normal_tex.inputs["Vector"])
        links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


WALL_MAT = flat("dollhouse-wall", (0.90, 0.89, 0.87), roughness=0.9)
WOOD_MAT = textured("floor-wood", WOOD_DIFFUSE, WOOD_TILE_SIZE_M, 0.45, (0.62, 0.42, 0.24))
GRANITE_MAT = textured("floor-granite", GRANITE_DIFFUSE, GRANITE_TILE_SIZE_M, 0.25,
                       (0.55, 0.55, 0.57), normal_path=GRANITE_NORMAL)
SCREED_MAT = flat("floor-screed", (0.52, 0.52, 0.50), roughness=0.8)

# Granite in Diele, Bad, DU-WC and HWR. The kitchen is open-plan with the
# living room in this plan, so it keeps wood — tiling only the kitchen half
# would visually cut one room in two.
FLOOR_MATERIALS = {
    "living": WOOD_MAT,
    "sleeping": WOOD_MAT,
    "flex": WOOD_MAT,
    "circulation": GRANITE_MAT,
    "wet": GRANITE_MAT,
    "sanitary": GRANITE_MAT,
    "service": GRANITE_MAT,
    "storage": SCREED_MAT,
}

# Colour/roughness/metallic values taken from FURNITURE_FINISHES in
# src/lib/generator/furniture-catalog.mjs, honouring TYPE_FINISH_CATEGORIES
# (a sofa gets fabric, a wardrobe wood, a washer metal). The first render
# ignored that module and used an invented near-white palette, which is why
# everything read as white plastic.
FINISHES = {
    "fabric-charcoal": ((0.16, 0.16, 0.18), 0.0, 0.85),
    "fabric-navy": ((0.09, 0.13, 0.28), 0.0, 0.85),
    "fabric-cream": ((0.88, 0.84, 0.76), 0.0, 0.85),
    "fabric-terracotta": ((0.62, 0.32, 0.22), 0.0, 0.85),
    "wood-oak": ((0.72, 0.58, 0.40), 0.0, 0.55),
    "wood-walnut": ((0.32, 0.20, 0.14), 0.0, 0.50),
    "wood-white-oak": ((0.82, 0.76, 0.66), 0.0, 0.60),
    "metal-matte-black": ((0.06, 0.06, 0.07), 0.6, 0.35),
    "metal-brushed-steel": ((0.62, 0.63, 0.65), 0.75, 0.30),
    "glass-clear": ((0.85, 0.90, 0.92), 0.05, 0.08),
}

TYPE_FINISH = {
    "bed_double": "fabric-navy",
    "sofa": "fabric-charcoal",
    "wardrobe": "wood-white-oak",
    "dressing_wardrobe": "wood-white-oak",
    "nightstand": "wood-walnut",
    "coffee_table": "wood-walnut",
    "dining_table": "wood-oak",
    "desk": "wood-oak",
    "tv_unit": "metal-matte-black",
    "storage_shelving": "wood-oak",
    "washer_dryer_unit": "metal-brushed-steel",
    "bathroom_vanity": "wood-walnut",
    "office_chair": "metal-matte-black",
    "coat_rack": "metal-matte-black",
    "rug": "fabric-terracotta",
    "wall_art": "wood-walnut",
    "mirror": "metal-brushed-steel",
    "floor_lamp": "metal-matte-black",
    "table_lamp": "metal-brushed-steel",
    "shoe_rack": "wood-oak",
    "clothing_rack": "metal-brushed-steel",
}

FURNITURE_MATERIALS = {}


def furniture_material(furniture_type):
    if furniture_type not in FURNITURE_MATERIALS:
        finish_name = TYPE_FINISH.get(furniture_type, "wood-oak")
        color, metallic, roughness = FINISHES[finish_name]
        FURNITURE_MATERIALS[furniture_type] = flat(
            f"furn-{furniture_type}-{finish_name}", color, roughness, metallic)
    return FURNITURE_MATERIALS[furniture_type]


# ---------------------------------------------------------------- geometry

def polygon_object(name, points_mm, z_m, thickness_m, material):
    verts = [(p[0] * MM, p[1] * MM, z_m) for p in points_mm]
    mesh = bpy.data.meshes.new(f"{name}-mesh")
    mesh.from_pydata(verts, [], [list(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    solidify = obj.modifiers.new("thickness", "SOLIDIFY")
    solidify.thickness = thickness_m
    solidify.offset = -1.0
    return obj


GLASS_MAT = flat("window-glass", (0.55, 0.72, 0.82), roughness=0.08, metallic=0.0)
FRAME_MAT = flat("opening-frame", (0.12, 0.13, 0.14), roughness=0.35, metallic=0.2)
DOOR_MAT = flat("door-leaf-white", (0.94, 0.94, 0.93), roughness=0.40)
HANDLE_MAT = flat("handle-brushed-steel", (0.62, 0.63, 0.65), roughness=0.30, metallic=0.75)

DOOR_LEAF_THICKNESS_M = 0.040
DOOR_OPEN_DEG = 45.0
HANDLE_HEIGHT_M = 1.05

# Doors swing into the room they serve. Below this area the room is too tight
# for that — the classic Gaeste-WC case — so the leaf swings outward instead.
SMALL_ROOM_OUTWARD_M2 = 4.0


def box(name, location, dimensions, angle, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.rotation_euler[2] = angle
    if material:
        obj.data.materials.append(material)
    return obj


def opening_transform(wall, opening, height_mm_override=None):
    """World position and wall angle for an opening. `position` is a 0..1
    fraction along the wall."""
    x1, y1 = wall["start_mm"]
    x2, y2 = wall["end_mm"]
    t = opening["position"]
    height = (height_mm_override or opening["height_mm"]) * MM
    centre = (
        (x1 + (x2 - x1) * t) * MM,
        (y1 + (y2 - y1) * t) * MM,
        opening["sill_height_mm"] * MM + height / 2,
    )
    angle = math.atan2(y2 - y1, x2 - x1)
    return centre, angle, height


def point_in_polygon(point, polygon_mm):
    """Ray-cast test. Polygon is in mm, point in metres."""
    x, y = point[0] / MM, point[1] / MM
    inside = False
    count = len(polygon_mm)
    for i in range(count):
        x1, y1 = polygon_mm[i]
        x2, y2 = polygon_mm[(i + 1) % count]
        if (y1 > y) != (y2 > y):
            crossing = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < crossing:
                inside = not inside
    return inside


def room_at(point, rooms):
    for room in rooms:
        if point_in_polygon(point, room["polygon_mm"]):
            return room
    return None


def add_door_leaf(name, wall, opening, leaf_height, rooms):
    """A white leaf hinged at one jamb and swung 45 deg open, with a brushed
    steel lever handle.

    Two decisions, both derived from geometry rather than guessed:

    1. Which side it swings to. The leaf goes into the room the door serves,
       not into the Diele — five doors folded out into one hallway would block
       the circulation they exist to serve. Where one side is outside, it
       swings inward.
    2. Which jamb it hinges on. The leaf must fold back toward the nearer
       corner so it reveals the open part of the room instead of swinging
       across it and presenting a blank wall.

    Passages get no leaf — a passage is a doorway-sized opening with no door
    by definition.
    """
    x1, y1 = wall["start_mm"]
    x2, y2 = wall["end_mm"]
    wall_angle = math.atan2(y2 - y1, x2 - x1)
    width = opening["width_mm"] * MM

    centre_x = (x1 + (x2 - x1) * opening["position"]) * MM
    centre_y = (y1 + (y2 - y1) * opening["position"]) * MM

    # --- which side does it open into? -------------------------------------
    normal = (-math.sin(wall_angle), math.cos(wall_angle))
    probe = 0.6
    side_a = room_at((centre_x + normal[0] * probe, centre_y + normal[1] * probe), rooms)
    side_b = room_at((centre_x - normal[0] * probe, centre_y - normal[1] * probe), rooms)

    def area(room):
        return room["area_m2"] if room else -1.0

    if side_a is None and side_b is None:
        swing_sign = 1.0
        target = None
    elif side_a is None:
        swing_sign, target = -1.0, side_b
    elif side_b is None:
        swing_sign, target = 1.0, side_a
    else:
        # Into the served room: the smaller of the two, which keeps the
        # hallway clear.
        if area(side_a) < area(side_b):
            swing_sign, target, other = 1.0, side_a, side_b
        else:
            swing_sign, target, other = -1.0, side_b, side_a

        # Exception: a Gaeste-WC is usually too tight for an inward swing, so
        # the leaf goes outward instead. Threshold, not a guess about this
        # specific plan — DU-WC here is 6.9 m2 and stays inward.
        if area(target) < SMALL_ROOM_OUTWARD_M2:
            swing_sign, target = -swing_sign, other

    # --- which jamb does it hinge on? --------------------------------------
    # Fold toward whichever end of the wall the opening already sits nearer,
    # so the open leaf lies back along the wall.
    hinge_sign = -1.0 if opening["position"] <= 0.5 else 1.0

    hinge_x = centre_x + math.cos(wall_angle) * (width / 2) * hinge_sign
    hinge_y = centre_y + math.sin(wall_angle) * (width / 2) * hinge_sign

    # Swing away from the hinge, rotated off the wall line into the target room.
    swing = wall_angle + math.pi if hinge_sign > 0 else wall_angle
    swing -= swing_sign * hinge_sign * math.radians(DOOR_OPEN_DEG)

    leaf_x = hinge_x + math.cos(swing) * width / 2
    leaf_y = hinge_y + math.sin(swing) * width / 2

    box(name, (leaf_x, leaf_y, leaf_height / 2),
        (width, DOOR_LEAF_THICKNESS_M, leaf_height), swing, DOOR_MAT)

    # Lever handle near the free edge, projecting from the leaf face.
    reach = width / 2 - 0.07
    handle_x = leaf_x + math.cos(swing) * reach
    handle_y = leaf_y + math.sin(swing) * reach
    box(f"{name}-handle", (handle_x, handle_y, HANDLE_HEIGHT_M),
        (0.022, 0.13, 0.022), swing, HANDLE_MAT)
    box(f"{name}-rose", (handle_x, handle_y, HANDLE_HEIGHT_M),
        (0.055, DOOR_LEAF_THICKNESS_M + 0.02, 0.055), swing, HANDLE_MAT)


def cut_opening(wall_obj, cutter):
    modifier = wall_obj.modifiers.new("opening-void", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = wall_obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def wall_object(name, wall, openings, height_mm, rooms):
    """Build a wall and boolean-cut its doors, windows and passages. Without
    the cuts every wall is a solid slab and the plan reads as a maze."""
    x1, y1 = wall["start_mm"][0] * MM, wall["start_mm"][1] * MM
    x2, y2 = wall["end_mm"][0] * MM, wall["end_mm"][1] * MM
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return None

    height = height_mm * MM
    thickness = wall["thickness_mm"] * MM
    angle = math.atan2(y2 - y1, x2 - x1)
    obj = box(name, ((x1 + x2) / 2, (y1 + y2) / 2, height / 2),
              (length, thickness, height), angle, WALL_MAT)

    for opening in openings:
        # Clamp to wall height so a 2010mm door in a 2400mm wall keeps a
        # lintel, but nothing ever exceeds the wall it sits in.
        available = height_mm - opening["sill_height_mm"]
        if available <= 0:
            continue
        cut_height = min(opening["height_mm"], available)
        centre, opening_angle, cut_h = opening_transform(wall, opening, cut_height)

        cutter = box(f"{name}-cut", centre,
                     (opening["width_mm"] * MM, thickness * 3.0, cut_h),
                     opening_angle, None)
        bpy.ops.object.select_all(action="DESELECT")
        cut_opening(obj, cutter)

        if opening["opening_type"] == "window":
            box(f"{name}-glass", centre,
                (opening["width_mm"] * MM * 0.94, 0.02, cut_h * 0.94),
                opening_angle, GLASS_MAT)
        elif opening["opening_type"] == "door":
            add_door_leaf(f"{name}-door", wall, opening, cut_h, rooms)

    return obj


# ---------------------------------------------------- furniture normalisation

def import_model(filepath):
    """Import a .glb or .fbx and join it into a single mesh object.

    Tracks object NAMES rather than object references: join() destroys the
    merged-away objects, and holding a Python reference to one and then
    touching it raises ReferenceError (StructRNA has been removed). Names stay
    valid because they are just strings, looked up again afterwards."""
    before = set(bpy.data.objects.keys())
    if filepath.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=filepath)
    else:
        bpy.ops.import_scene.gltf(filepath=filepath)
    imported_names = set(bpy.data.objects.keys()) - before

    mesh_names = [n for n in imported_names if bpy.data.objects[n].type == "MESH"]
    if not mesh_names:
        for name in imported_names:
            if name in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        return None

    bpy.ops.object.select_all(action="DESELECT")
    for name in mesh_names:
        bpy.data.objects[name].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[mesh_names[0]]
    if len(mesh_names) > 1:
        bpy.ops.object.join()
    obj = bpy.context.active_object

    for name in imported_names:
        if name in bpy.data.objects and bpy.data.objects[name] is not obj:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def local_dimensions(obj):
    coords = [mathutils.Vector(c) for c in obj.bound_box]
    mins = mathutils.Vector((min(c.x for c in coords), min(c.y for c in coords), min(c.z for c in coords)))
    maxs = mathutils.Vector((max(c.x for c in coords), max(c.y for c in coords), max(c.z for c in coords)))
    return mins, maxs, (maxs - mins)


def rest_on_floor(obj):
    """Centre a natively-scaled model in X/Y and sit its base on z=0, without
    touching its dimensions or materials."""
    mins, maxs, _ = local_dimensions(obj)
    offset = mathutils.Vector(((mins.x + maxs.x) / 2, (mins.y + maxs.y) / 2, mins.z))
    for vertex in obj.data.vertices:
        vertex.co -= offset
    obj.data.update()
    return obj


def normalise_to_bbox(obj, target_mm):
    """Tripo returns every mesh normalised into a ~1-unit box, and the axis
    ordering is NOT consistent between pieces (measured: the chair's long axis
    is Y, the bed's and sofa's is Z). So a single global transform cannot work.

    Match raw axes to target axes by descending extent, rotate so the matched
    axes align with world X/Y/Z, then scale each axis to the catalogue
    dimension. Ties are broken by axis index so the result is deterministic
    rather than dependent on sort stability."""
    target = [target_mm["width_mm"] * MM, target_mm["depth_mm"] * MM, target_mm["height_mm"] * MM]

    _, _, dims = local_dimensions(obj)
    raw = [max(dims.x, 1e-6), max(dims.y, 1e-6), max(dims.z, 1e-6)]

    raw_order = sorted(range(3), key=lambda i: (-raw[i], i))
    target_order = sorted(range(3), key=lambda i: (-target[i], i))
    mapping = {raw_order[i]: target_order[i] for i in range(3)}

    matrix = mathutils.Matrix.Identity(3)
    for raw_axis, target_axis in mapping.items():
        column = [0.0, 0.0, 0.0]
        column[target_axis] = 1.0
        matrix[0][raw_axis] = column[0]
        matrix[1][raw_axis] = column[1]
        matrix[2][raw_axis] = column[2]
    if matrix.determinant() < 0:
        for row in range(3):
            matrix[row][raw_order[0]] *= -1

    obj.matrix_world = matrix.to_4x4() @ obj.matrix_world
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    _, _, dims = local_dimensions(obj)
    now = [max(dims.x, 1e-6), max(dims.y, 1e-6), max(dims.z, 1e-6)]
    obj.scale = (target[0] / now[0], target[1] / now[1], target[2] / now[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mins, maxs, _ = local_dimensions(obj)
    offset = mathutils.Vector(((mins.x + maxs.x) / 2, (mins.y + maxs.y) / 2, mins.z))
    for vertex in obj.data.vertices:
        vertex.co -= offset
    obj.data.update()
    return obj


# ------------------------------------------------------------------- scene

scene = bpy.context.scene
scene["source_geometry_hash"] = plan["source_geometry_hash"]
scene["furniture_style"] = plan["style"]
scene["render_plan_schema"] = plan["schema"]

floor = plan["floors"][0]

# Wall height: the first render cut walls to 1200mm, below a 2100mm wardrobe
# and below the 1400mm mirror mount height, so tall furniture speared through
# the walls and wall-mounted items floated above them. Full storey height with
# a steeper camera keeps every room visible without that.
wall_height = 2400

for room in floor["rooms"]:
    material = FLOOR_MATERIALS.get(room.get("kind"), SCREED_MAT)
    polygon_object(f"floor-{room['id']}", room["polygon_mm"], 0.0, 0.02, material)

openings_by_wall = {}
for opening in floor.get("openings", []):
    openings_by_wall.setdefault(opening["wall_id"], []).append(opening)

cut_count = 0
for index, wall in enumerate(floor["walls"]):
    wall_openings = openings_by_wall.get(wall.get("id"), [])
    wall_object(f"wall-{index}", wall, wall_openings, wall_height, floor["rooms"])
    cut_count += len(wall_openings)

prototypes = {}
placed = 0
failed = []

for item in floor["placements"]:
    asset_id = item["asset_id"]
    if asset_id not in prototypes:
        obj = import_model(item["mesh_path"])
        if obj is None:
            failed.append(asset_id)
            prototypes[asset_id] = None
            continue

        if item.get("preserve_native_scale"):
            # Library models are authored at true size and carry their own
            # materials. Rescaling would distort them and overwriting their
            # materials would throw away the reason to use them at all.
            rest_on_floor(obj)
        else:
            normalise_to_bbox(obj, item["target_bbox_mm"])
            obj.data.materials.clear()
            obj.data.materials.append(furniture_material(item["type"]))

        obj.name = f"proto-{asset_id}"
        obj.hide_render = True
        obj.hide_viewport = True
        prototypes[asset_id] = obj

    proto = prototypes[asset_id]
    if proto is None:
        continue

    instance = bpy.data.objects.new(f"{asset_id}-{placed}", proto.data)
    bpy.context.collection.objects.link(instance)

    # `height_mm` is a MOUNT height — where the centre of a wall-mounted item
    # sits — but prototypes are re-origined with their base at z=0. Placing a
    # 1600mm mirror with its base at 1400mm put its top at 3000mm, a full
    # 600mm above a 2400mm wall, which is why mirrors appeared to float in
    # mid-air. Offset by half the item's height so the centre lands on the
    # mount instead.
    mount_mm = item.get("height_mm", 0)
    if mount_mm:
        z = mount_mm * MM - (item["target_bbox_mm"]["height_mm"] * MM) / 2
    else:
        z = 0.0

    instance.location = (
        item["position_mm"][0] * MM,
        item["position_mm"][1] * MM,
        z,
    )
    instance.rotation_euler[2] = math.radians(item.get("rotation_deg", 0.0))
    placed += 1

# ------------------------------------------------------------ camera + light

points = [p for room in floor["rooms"] for p in room["polygon_mm"]]
min_x = min(p[0] for p in points) * MM
max_x = max(p[0] for p in points) * MM
min_y = min(p[1] for p in points) * MM
max_y = max(p[1] for p in points) * MM
centre = mathutils.Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, 0.0))
span = max(max_x - min_x, max_y - min_y)

camera_data = bpy.data.cameras.new("dollhouse-camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 1.4
camera = bpy.data.objects.new("dollhouse-camera", camera_data)
bpy.context.collection.objects.link(camera)

# Steeper than the first attempt so full-height walls don't hide the rooms
# behind them.
direction = mathutils.Vector((1.0, -1.0, 1.65)).normalized()
camera.location = centre + direction * (span * 2.2)
camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
scene.camera = camera

# HDRI environment does the lighting. The first render used a flat grey world
# at strength 1.6 plus a 4.0 sun, which blew everything to white.
world = bpy.data.worlds.new("dollhouse-world")
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
bg = nodes["Background"]
hdri_path = asset(HDRI)
if hdri_path:
    env = nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdri_path)
    links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.9

    # The HDRI's lower hemisphere was showing behind the house as a dark olive
    # void. Light the scene with it, but give camera rays a clean backdrop:
    # Is Camera Ray = 1 selects the plain colour, everything else keeps the
    # HDRI so reflections and bounce light are unaffected.
    backdrop = nodes.new("ShaderNodeBackground")
    backdrop.inputs["Color"].default_value = (0.87, 0.89, 0.92, 1.0)
    backdrop.inputs["Strength"].default_value = 1.0
    light_path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(light_path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    links.new(bg.outputs["Background"], mix.inputs[1])
    links.new(backdrop.outputs["Background"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["World Output"].inputs["Surface"])
else:
    bg.inputs["Color"].default_value = (0.87, 0.89, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

# A soft key sun for shadow direction; the HDRI supplies fill.
sun_data = bpy.data.lights.new("key-sun", type="SUN")
sun_data.energy = 2.2
sun_data.angle = math.radians(6.0)
sun = bpy.data.objects.new("key-sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = centre + mathutils.Vector((span, -span, span * 1.6))
sun.rotation_euler = (math.radians(48), 0.0, math.radians(-55))

for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue

# Raytraced shadows/AO where available — flat ambient light was a large part
# of why the first render read as cardboard.
try:
    scene.eevee.use_raytracing = True
except AttributeError:
    pass
try:
    scene.eevee.use_shadows = True
    scene.eevee.taa_render_samples = 64
except AttributeError:
    pass

try:
    scene.view_settings.view_transform = "AgX"
except TypeError:
    pass
scene.view_settings.exposure = 0.2

scene.render.resolution_x = 2000
scene.render.resolution_y = 1500
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.abspath(out_path)

print(f"[dollhouse] floor           {floor['name']}")
print(f"[dollhouse] rooms           {len(floor['rooms'])}")
print(f"[dollhouse] walls           {len(floor['walls'])} at {wall_height}mm")
print(f"[dollhouse] openings cut    {cut_count}")
print(f"[dollhouse] furniture       {placed} instances from {len([p for p in prototypes.values() if p])} meshes")
print(f"[dollhouse] engine          {scene.render.engine}")
print(f"[dollhouse] hdri            {'yes' if hdri_path else 'NO — flat sky fallback'}")
if missing_assets:
    print("[dollhouse] MISSING ASSETS (fell back to flat colour):")
    for path in missing_assets:
        print(f"              {path}")
if failed:
    print(f"[dollhouse] FAILED IMPORT  {', '.join(sorted(set(failed)))}")

bpy.ops.render.render(write_still=True)
print(f"[dollhouse] wrote           {scene.render.filepath}")
