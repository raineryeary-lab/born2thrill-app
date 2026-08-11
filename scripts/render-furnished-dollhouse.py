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
GRANITE_TILE_SIZE_M = 1.2  # XXL Feinsteinzeug format: at dollhouse camera
# distance the 0.6m slabs repeated so densely they read as speckle noise
# (Rainer: "the tiles ... dont look good") — double format halves the
# visual frequency, and a light tint below calms the grain contrast.

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


def textured(name, image_path, tile_size_m, roughness, fallback_color, normal_path=None, uv_offset=(0, 0),
             tint=None, tint_factor=0.0):
    """Image-textured material tiled at real-world scale.

    Floor plates are built from raw polygons and have no UV map, so this uses
    Object coordinates. The mesh is created with world coordinates and its
    origin at 0, so object space == world space and every room tiles on the
    same grid rather than stretching to each room's bounding box.
    uv_offset (x, y) adds a deterministic offset to break up obvious tiling
    repetition across adjacent rooms without changing material identity."""
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
    mapping.inputs["Location"].default_value = (uv_offset[0], uv_offset[1], 0.0)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.extension = "REPEAT"

    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    if tint and tint_factor > 0:
        # Finish variants re-colour the SAME floor texture instead of
        # needing a texture per look: multiply toward the tint, keeping the
        # grain. Deterministic, no new assets.
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = tint_factor
        mix.inputs["Color2"].default_value = (*tint, 1.0)
        links.new(tex.outputs["Color"], mix.inputs["Color1"])
        links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    else:
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


# ------------------------------------------------------------- finish sets
# Rainer's variant strategy (2026-08-10): keep the geometry and most of the
# scene identical; swap ONLY wall tone, floor tint, kitchen fronts and
# upholstery. Small changes, big perceived difference — and each style
# (modern/classic furniture picks) gets two finish looks, giving the four
# interior images per home the rollout plan promises. Select with
# DMH_FINISH=<name>; default is the look every render so far used.
FINISH_SETS = {
    "modern-a": {"wall": (0.90, 0.89, 0.87),
                 "floor_tint": None, "floor_tint_factor": 0.0,
                 "kitchen": "metal-matte-black", "sofa": "fabric-charcoal"},
    "modern-b": {"wall": (0.87, 0.84, 0.78),
                 "floor_tint": (0.38, 0.25, 0.18), "floor_tint_factor": 0.85,
                 "kitchen": "lacquer-white", "sofa": "fabric-navy"},
    "classic-a": {"wall": (0.92, 0.89, 0.82),
                  "floor_tint": (0.74, 0.54, 0.34), "floor_tint_factor": 0.35,
                  "kitchen": "wood-walnut", "sofa": "fabric-cream"},
    "classic-b": {"wall": (0.86, 0.88, 0.85),
                  "floor_tint": (0.55, 0.38, 0.25), "floor_tint_factor": 0.45,
                  "kitchen": "wood-oak", "sofa": "fabric-terracotta"},
}
FINISH = FINISH_SETS[os.environ.get("DMH_FINISH", "modern-a")]

WALL_MAT = flat("dollhouse-wall", FINISH["wall"], roughness=0.9)
# Subtle UV offset (0.33, 0.27) breaks up obvious grid tiling without appearing arbitrary.
# Per rulebook 8: "Slight deterministic UV offset or rotation may reduce repetition
# without changing material identity."
WOOD_MAT = textured("floor-wood", WOOD_DIFFUSE, WOOD_TILE_SIZE_M, 0.45, (0.62, 0.42, 0.24),
                    uv_offset=(0.33, 0.27),
                    tint=FINISH["floor_tint"], tint_factor=FINISH["floor_tint_factor"])
GRANITE_MAT = textured("floor-granite", GRANITE_DIFFUSE, GRANITE_TILE_SIZE_M, 0.35,
                       (0.55, 0.55, 0.57), normal_path=GRANITE_NORMAL, uv_offset=(0.17, 0.42),
                       tint=(0.88, 0.88, 0.89), tint_factor=0.45)
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
    "lacquer-white": ((0.92, 0.92, 0.90), 0.0, 0.35),
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
    # Cabinet fronts got no finish and defaulted to a bare white box (visible,
    # confirmed by render, in the standard delivery angle -- not just the
    # top-down check, where the worktop's overhang hides them almost
    # entirely). Matte black is not a guess: it is the measured colour of the
    # door-front objects in the real Hub kitchen sets (Kitchen Furniture Set
    # 1, near-black with no image texture), applied here as a colour/finish
    # only -- no geometry imported, per the redirect that final render
    # distance doesn't show individual door-panel detail anyway.
    "counter": "metal-matte-black",
    # The tall unit (oven housing) is part of the same kitchen run as the
    # counter above -- same reasoning, same finish, so it doesn't render as
    # an unrelated plain box next to matte-black cabinetry.
    "oven_housing": "metal-matte-black",
    "sink": "metal-brushed-steel",
}

# The finish set overrides the variant-bearing surfaces; everything else in
# TYPE_FINISH stays put so a wardrobe doesn't change colour with the kitchen.
TYPE_FINISH["counter"] = FINISH["kitchen"]
TYPE_FINISH["oven_housing"] = FINISH["kitchen"]
TYPE_FINISH["sofa"] = FINISH["sofa"]

FURNITURE_MATERIALS = {}


# Real-model assets whose OWN material should be overridden despite
# `preserve_materials: true` -- checked case by case, not applied broadly.
# Both `sofa_1sitzer` ("Light-Grey Armchair") and `sofa_2sitzer` ("Grey Two
# Seat Sofa") have their Base Color linked to an image texture node, not a
# flat default -- and in BOTH cases the texture file
# (E:\_models_hub\_extracted\extracted\cgaxis_models_68_1{2,2,0}\...\.jpg)
# does not exist on disk (confirmed with a plain file check on both). A real
# living-room set matches the armchair to the sofa; putting both on the same
# explicit finish is a deliberate matching colour, not a guess at whatever
# each one's broken-texture fallback happened to render as.
ACCENT_OVERRIDE = {
    "sofa_1sitzer": FINISHES["fabric-charcoal"],
    "sofa_2sitzer": FINISHES["fabric-charcoal"],
    # Keys may also be MODEL LABELS (checked first at the instance site):
    # the classic dining set rendered as a black blob (Rainer), so it gets
    # a light oak finish — label-keyed so the modern table's own black-and-
    # white materials stay untouched.
    "Black Table and Chairs Set": FINISHES["wood-oak"],
}

# See ROTATION_OVERRIDE's use at the instance-placement site for the reason.
ROTATION_OVERRIDE = {
    # In-situ contact sheet 2026-08-11 (tmp/chair-picker.png): Rainer
    # picked Bild 2 = 135. Never eyeball chair facing from a perspective
    # render — sheet only.
    "sofa_1sitzer": 135,
}

# (dx_mm, dy_mm) shift applied to the annotated position_mm. Rainer gave an
# explicit target clearance from the wall for each; both were measured
# against the actual rendered bounding box (not the annotated footprint,
# which can differ from the real model's fitted size), against wall-21
# (a vertical wall, constant x, room on the +X side, so closing the gap
# means moving in -X):
#   schreibtisch: near edge measured at x=5.427m, wall face at x=4.83m ->
#     597mm gap. Target 40mm -> shift -557mm.
#   sofa_2sitzer: near edge measured at x=5.243m, same wall face -> 413mm
#     gap. Target 100mm -> shift -313mm.
POSITION_OVERRIDE = {
    "schreibtisch": (-557, 0),
    "sofa_2sitzer": (-313, 0),
}


def accent_material(asset_id):
    color, metallic, roughness = ACCENT_OVERRIDE[asset_id]
    return flat(f"accent-{asset_id}", color, roughness, metallic)


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
    collection("Architecture").objects.link(obj)
    obj.data.materials.append(material)
    solidify = obj.modifiers.new("thickness", "SOLIDIFY")
    solidify.thickness = thickness_m
    solidify.offset = -1.0
    return obj


def glazing(name):
    """Glass by ALPHA, not transmission.

    Transmission needs raytracing that this EEVEE setup is not doing, so a
    transmissive material rendered as a dark green panel — worse than the flat
    pale blue it replaced. Alpha blending is what actually reads as glass in
    this engine: you see the room through it, with a faint tint and a
    highlight.
    """
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.82, 0.90, 0.94, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.05
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.18
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.8
    for attribute, value in (("blend_method", "BLEND"),
                             # Blender 5's EEVEE Next reads THIS property, not
                             # blend_method, for how alpha is rendered. Its
                             # default is DITHERED -- a stipple pattern that
                             # approximates transparency with noise, which is
                             # exactly why glass was rendering as a solid,
                             # noisy-looking white/grey panel instead of
                             # reading as glass. Confirmed by checking the
                             # material's own default value directly in this
                             # Blender build, not assumed.
                             ("surface_render_method", "BLENDED"),
                             ("shadow_method", "NONE"),
                             ("use_backface_culling", False)):
        if hasattr(material, attribute):
            try:
                setattr(material, attribute, value)
            except (TypeError, AttributeError):
                pass
    # Blender 5 moved shadow control onto the object; glass should not cast a
    # solid shadow either way.
    material.diffuse_color = (0.82, 0.90, 0.94, 0.18)
    return material


GLASS_MAT = glazing("window-glass")
TV_MAT = flat("dark-panel", (0.04, 0.04, 0.05), roughness=0.25, metallic=0.3)
# Was (0.94, 0.94, 0.93) -- effectively the same tone as WALL_MAT's (0.90,
# 0.89, 0.87), so a door frame sitting against its own wall had almost no
# contrast and read as invisible ("the frame is not visible", confirmed by
# cropping several doors: the jamb is only a faint line, sometimes not
# distinguishable from the wall at all). Anthracite was tried and rejected
# for the same reason in the other direction -- against a light floor/wall it
# also lost contrast. A mid grey sits between both backdrops it's ever seen
# against (light walls, light floors, dark furniture) instead of matching
# either one.
DOOR_FRAME_MAT = flat("opening-frame-door", (0.32, 0.31, 0.29), roughness=0.5, metallic=0.0)
# Anthracite requested for WINDOW frames specifically -- this used to be one
# shared FRAME_MAT for both doors and windows, so changing it made door
# frames go dark too ("disappear into the floor" -- against the cut-down
# wall stub and floor tones, the near-black door frame lost all contrast).
# Doors keep a light-but-distinct colour; only windows get anthracite.
WINDOW_FRAME_MAT = flat("opening-frame-window", (0.08, 0.08, 0.09), roughness=0.4, metallic=0.15)
DOOR_MAT = flat("door-leaf-white", (0.94, 0.94, 0.93), roughness=0.40)
HANDLE_MAT = flat("handle-brushed-steel", (0.62, 0.63, 0.65), roughness=0.30, metallic=0.75)

DOOR_LEAF_THICKNESS_M = 0.040
DOOR_OPEN_DEG = 45.0
HANDLE_HEIGHT_M = 1.05

# Doors swing into the room they serve. Below this area the room is too tight
# for that — the classic Gaeste-WC case — so the leaf swings outward instead.
SMALL_ROOM_OUTWARD_M2 = 4.0


# Scene is split into collections rather than one flat list. Architecture and
# furniture are separate concerns — furniture is presentation data that must
# never affect geometry_hash — and the split is what makes "render this floor
# unfurnished" or "hide the near walls" a one-line operation instead of a
# per-object hunt.
COLLECTIONS = {}


def collection(name):
    if name not in COLLECTIONS:
        created = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(created)
        COLLECTIONS[name] = created
    return COLLECTIONS[name]


def place_in(obj, name):
    """Move an object out of whatever collection it landed in and into ours."""
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection(name).objects.link(obj)
    return obj


def box(name, location, dimensions, angle, material, into="Architecture"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.rotation_euler[2] = angle
    if material:
        obj.data.materials.append(material)
    return place_in(obj, into)


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

    # Annotation first. swing_side and hinge_side are set in the Simplifier and
    # carried through the plan; deriving them from room areas instead threw away
    # a decision Rainer had already made, on all seven doors of this plan.
    annotated_swing = opening.get("swing_side")
    annotated_hinge = opening.get("hinge_side")

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

    # The annotated swing wins over everything derived above.
    #
    # `first_room` / `second_room` name the two spaces the opening joins, in the
    # order the wall records them, so they map onto side_a / side_b.
    if annotated_swing == "first_room":
        swing_sign, target = 1.0, side_a
    elif annotated_swing == "second_room":
        swing_sign, target = -1.0, side_b

    # --- which jamb does it hinge on? --------------------------------------
    # Fold toward whichever end of the wall the opening already sits nearer,
    # so the open leaf lies back along the wall.
    if annotated_hinge == "start":
        hinge_sign = -1.0
    elif annotated_hinge == "end":
        hinge_sign = 1.0
    else:
        hinge_sign = -1.0 if opening["position"] <= 0.5 else 1.0

    hinge_x = centre_x + math.cos(wall_angle) * (width / 2) * hinge_sign
    hinge_y = centre_y + math.sin(wall_angle) * (width / 2) * hinge_sign

    # Swing away from the hinge, rotated off the wall line into the target room.
    swing = wall_angle + math.pi if hinge_sign > 0 else wall_angle
    swing -= swing_sign * hinge_sign * math.radians(DOOR_OPEN_DEG)

    leaf_x = hinge_x + math.cos(swing) * width / 2
    leaf_y = hinge_y + math.sin(swing) * width / 2

    leaf = box(name, (leaf_x, leaf_y, leaf_height / 2),
               (width, DOOR_LEAF_THICKNESS_M, leaf_height), swing, DOOR_MAT)

    # Lever handle near the free edge, projecting from the leaf face.
    reach = width / 2 - 0.07
    handle_x = leaf_x + math.cos(swing) * reach
    handle_y = leaf_y + math.sin(swing) * reach
    handle = box(f"{name}-handle", (handle_x, handle_y, HANDLE_HEIGHT_M),
                 (0.022, 0.13, 0.022), swing, HANDLE_MAT)
    rose = box(f"{name}-rose", (handle_x, handle_y, HANDLE_HEIGHT_M),
               (0.055, DOOR_LEAF_THICKNESS_M + 0.02, 0.055), swing, HANDLE_MAT)
    return [leaf, handle, rose]


def cut_opening(wall_obj, cutter):
    modifier = wall_obj.modifiers.new("opening-void", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = wall_obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def opening_frame(name, wall, opening, centre, angle, height, material):
    """Lining round an opening: two jambs, a head, and a sill for windows.

    Frames matter more here than in an ordinary render. The cutaway slices the
    walls down to 500 mm at the front, and openings are deliberately left out
    of that cut — so a door in a cut-down wall would otherwise be a leaf
    standing in thin air with nothing to say it is a doorway. The frame is what
    keeps the opening legible once its wall is gone.
    """
    # A real frame is a slim section, not a slab, and it is NOT as thick as
    # the wall -- that was tried and was wrong. The actual problem was
    # POSITION: a fixed 70mm profile CENTRED in the wall leaves ~85mm of
    # bare wall showing on both the inside and outside face of a 240mm
    # wall, which is exactly "the frame sits inside a hole in the wall"
    # (Rainer's own description). The fix is to sit the frame flush with
    # the ROOM-facing side, the way a real frame is fitted, not to make it
    # deeper. depth_offset below is 0 (flush with wall centreline, the old
    # behaviour) unless a room can be identified on one side of this wall.
    profile = 0.07
    thickness = profile
    width = opening["width_mm"] * MM
    parts = []

    nx, ny = -math.sin(angle), math.cos(angle)
    wall_thickness_m = wall["thickness_mm"] * MM
    probe = 0.3  # metres off the centreline, comfortably past any wall
    inward = None
    for sign in (1.0, -1.0):
        probe_point = (centre[0] + nx * probe * sign, centre[1] + ny * probe * sign)
        if room_at(probe_point, floor["rooms"]):
            inward = sign
            break
    depth_offset = (inward * (wall_thickness_m / 2 - thickness / 2)) if inward else 0.0

    def offset_by_depth(point):
        return (point[0] + nx * depth_offset, point[1] + ny * depth_offset)

    # Jambs, one either side, running the full height of the opening.
    for side in (-1, 1):
        offset = side * (width / 2 + profile / 2)
        ox, oy = offset_by_depth((centre[0] + math.cos(angle) * offset,
                                   centre[1] + math.sin(angle) * offset))
        parts.append(box(f"{name}-jamb", (ox, oy, centre[2]), (profile, thickness, height),
                         angle, material))

    head_z = centre[2] + height / 2 + profile / 2
    hx, hy = offset_by_depth((centre[0], centre[1]))
    parts.append(box(f"{name}-head", (hx, hy, head_z),
                     (width + profile * 2, thickness, profile), angle, material))

    # Window sills only exist on windows with an intentional sill height (above
    # the floor). Floor-reaching bodentief windows still need a bottom frame member
    # to close off the opening properly, otherwise the frame reads as an open-bottomed
    # U with the visible frame-top (the head) disconnected from the glass edges.
    if opening["opening_type"] == "window":
        if opening["sill_height_mm"] > 0:
            sill_z = centre[2] - height / 2 - profile / 2
            sx, sy = offset_by_depth((centre[0], centre[1]))
            # The sill is the one part that should overhang the reveal, so its
            # own depth stays the full wall thickness even though it's now
            # offset the same as the jambs/head -- was previously left centred
            # on the wall while jambs/head moved, an inconsistency that never
            # showed up on THIS project's windows (all bodentief, sill_height 0,
            # never enters this branch) but would have on any window with a
            # sill.
            parts.append(box(f"{name}-sill", (sx, sy, sill_z),
                             (width + profile * 2, wall["thickness_mm"] * MM * 1.1, profile),
                             angle, material))
        else:
            # Bodentief: floor-reaching, no sill. Still need a bottom profile
            # sitting ON the floor to complete the frame and provide visual
            # closure at the base of the glass.
            sill_z = centre[2] - height / 2 - profile / 2
            sx, sy = offset_by_depth((centre[0], centre[1]))
            parts.append(box(f"{name}-sill", (sx, sy, sill_z),
                             (width + profile * 2, thickness, profile),
                             angle, material))

    return parts


def _end_extension_mm(endpoint, outward, own, all_walls):
    """How far one wall END may extend ALONG ITS OWN AXIS: to the far face
    of whatever wall it meets there, and not a millimetre further.

    Two failed versions taught the shape of this function. The blanket rule
    (extend every >=200mm wall by half its own thickness) pushed thick
    walls through thin partitions and planted stubs at free ends. The
    euclidean version (`dist + half`) overshot whenever the endpoint sat
    diagonally off the met wall, poking the wall out its far side --
    isolated on a walls-only render as plus-shaped caps. The reach has to
    be measured along the wall's own outward direction: project onto the
    met wall's NORMAL, extend exactly to its far plane, capped so a near-
    parallel projection can never explode.
    """
    ex, ey = endpoint
    best = 0.0
    for other in all_walls:
        if other is own:
            continue
        sx, sy = other["start_mm"]
        tx, ty = other["end_mm"]
        seg = math.hypot(tx - sx, ty - sy)
        if not seg:
            continue
        t = max(0.0, min(1.0, ((ex - sx) * (tx - sx) + (ey - sy) * (ty - sy)) / seg ** 2))
        px, py = sx + t * (tx - sx), sy + t * (ty - sy)
        dist = math.hypot(ex - px, ey - py)
        touch = (own["thickness_mm"] + other["thickness_mm"]) / 2 + 5
        if dist > touch:
            continue
        # Signed distance from the endpoint to the met wall's centreline,
        # along that wall's normal; positive toward the endpoint's side.
        nx, ny = -(ty - sy) / seg, (tx - sx) / seg
        side = (ex - sx) * nx + (ey - sy) * ny
        if side < 0:
            nx, ny, side = -nx, -ny, -side
        # Along-axis rate of approach to the met wall's centreline. A near-
        # parallel wall barely closes the distance -- skip it rather than
        # divide by almost-zero.
        approach = -(outward[0] * nx + outward[1] * ny)
        if approach < 0.2:
            continue
        # Extend along `outward` until the endpoint's offset `side` becomes
        # -half (the far face): (side + half) / approach, never further
        # than the met wall is deep.
        # +10mm past the far face: exactly-flush faces are coplanar, and the
        # EXACT union leaves seam slivers on coplanar geometry (same trap as
        # the window cutters). A buried overshoot is invisible; a seam isn't.
        reach = (side + other["thickness_mm"] / 2) / approach + 10
        best = max(best, min(reach, other["thickness_mm"] + own["thickness_mm"]))
    return best


def wall_object(name, wall, openings, height_mm, rooms, all_walls=()):
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
    # Per-end, junction-aware extension (see _end_extension_mm). Ends grow
    # asymmetrically, so the box centre shifts by half the difference.
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    e1 = _end_extension_mm(wall["start_mm"], (-ux, -uy), wall, all_walls) * MM
    e2 = _end_extension_mm(wall["end_mm"], (ux, uy), wall, all_walls) * MM
    cx = (x1 + x2) / 2 + ux * (e2 - e1) / 2
    cy = (y1 + y2) / 2 + uy * (e2 - e1) / 2
    obj = box(name, (cx, cy, height / 2),
              (length + e1 + e2, thickness, height), angle, WALL_MAT)
    # The wall BODY and its openings are kept apart on purpose. The angled
    # cutaway slices the body; frames, glazing and door leaves are exempt from
    # it, which is the whole point of the effect Rainer asked for.
    features = []

    for opening in openings:
        # Clamp to wall height so a 2010mm door in a 2400mm wall keeps a
        # lintel, but nothing ever exceeds the wall it sits in.
        available = height_mm - opening["sill_height_mm"]
        if available <= 0:
            continue
        cut_height = min(opening["height_mm"], available)
        centre, opening_angle, cut_h = opening_transform(wall, opening, cut_height)

        # A bodentief (floor-reaching) opening puts the cutter's bottom face
        # exactly coplanar with the wall body's own bottom face (both at
        # z=0) -- confirmed by rendering the frame/glass with the wall body
        # hidden: they sit flush with the floor, but with the wall body
        # shown a ~50-90mm sliver of uncut WALL_MAT is visible below the
        # glass. That is the boolean EXACT solver leaving a degenerate
        # leftover face at an exactly-coincident boundary, not a sizing
        # problem in the glass/frame. A small overshoot on both ends keeps
        # the cutter's faces from ever exactly touching the wall's, whether
        # the opening starts at the floor or reaches the ceiling.
        cut_pad = 0.02
        cutter = box(f"{name}-cut", centre,
                     (opening["width_mm"] * MM, thickness * 3.0, cut_h + cut_pad * 2),
                     opening_angle, None)
        bpy.ops.object.select_all(action="DESELECT")
        cut_opening(obj, cutter)

        if opening["opening_type"] in ("door", "window"):
            frame_mat = WINDOW_FRAME_MAT if opening["opening_type"] == "window" else DOOR_FRAME_MAT
            features.extend(opening_frame(f"{name}-frame", wall, opening, centre,
                                          opening_angle, cut_h, frame_mat))

        if opening["opening_type"] == "window":
            # `panes` (the annotated Fluegel count) was carried into the plan
            # but never read here -- every window rendered as one sheet
            # regardless. N panes need N-1 mullions dividing the width into
            # N equal sections, not N-1 frames at fixed points: a 3-pane
            # window splits into thirds (2 mullions at 1/3 and 2/3), not 2
            # mullions wherever a fixed offset happens to land.
            panes = opening.get("panes") or 1
            # Was a proportional 6% shrink on both axes, centred -- fine for
            # width, wrong for height on a bodentief (floor-to-ceiling)
            # window: 6% of a 2100mm opening is 126mm total, so the glass
            # sat with its bottom 63mm ABOVE the true floor instead of
            # reaching it. Confirmed by measuring the actual glass object:
            # z-range came back 0.063-2.037m against a frame that correctly
            # reaches 0-2.1m. Rainer's own reference: floor runs straight up
            # to the glass, no gap. A small FIXED inset (not proportional to
            # opening size) gives a consistent reveal regardless of window
            # height, and reaches the floor on a bodentief window.
            glass_inset = 0.015
            glazed_w = opening["width_mm"] * MM - glass_inset * 2
            glass_h = cut_h - glass_inset * 2
            mullion_w = 0.04
            pane_w = (glazed_w - mullion_w * (panes - 1)) / panes
            start = -glazed_w / 2 + pane_w / 2
            for i in range(panes):
                local_x = start + i * (pane_w + mullion_w)
                px = centre[0] + math.cos(opening_angle) * local_x
                py = centre[1] + math.sin(opening_angle) * local_x
                features.append(box(f"{name}-glass-{i}", (px, py, centre[2]),
                                    (pane_w, 0.02, glass_h), opening_angle, GLASS_MAT))
            for i in range(panes - 1):
                local_x = start + pane_w / 2 + i * (pane_w + mullion_w) + mullion_w / 2
                mx = centre[0] + math.cos(opening_angle) * local_x
                my = centre[1] + math.sin(opening_angle) * local_x
                features.append(box(f"{name}-mullion-{i}", (mx, my, centre[2]),
                                    (mullion_w, 0.06, glass_h), opening_angle, WINDOW_FRAME_MAT))
        elif opening["opening_type"] == "door":
            features.extend(add_door_leaf(f"{name}-door", wall, opening, cut_h, rooms))

    return {"body": obj, "features": features}


# ---------------------------------------------------- furniture normalisation

# Room shells inside staged .blend scenes. Many CGAxis assets are photographed
# in a room, so the file carries walls, a floor and a ceiling alongside the
# furniture. Joining those in drops a second room inside yours.
#
# Two earlier attempts at this failed in opposite directions, and the pair is
# instructive. A fixed 3 m threshold applied to every import ate a 3524 mm
# corner sofa as "architecture". Scoping it to files named "furniture set"
# then let every other staged scene keep its room, which is the fabric plane
# that filled the background of render 03.
#
# The threshold should not be absolute at all. What makes an object a shell is
# that it is far bigger than the thing being placed — so measure it against the
# footprint this model is going into. A 3.5 m sofa headed for a 2.6 m footprint
# is furniture; a 6 m wall is not.
SHELL_FACTOR = 2.0


def _object_extent(obj):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for corner in obj.bound_box:
        world = obj.matrix_world @ mathutils.Vector(corner)
        for axis in range(3):
            lo[axis] = min(lo[axis], world[axis])
            hi[axis] = max(hi[axis], world[axis])
    return [hi[a] - lo[a] for a in range(3)]


def import_model(filepath, divisor=1.0, target_mm=None):
    """Import a .blend, .glb or .fbx and join it into a single mesh object.

    Tracks object NAMES rather than object references: join() destroys the
    merged-away objects, and holding a Python reference to one and then
    touching it raises ReferenceError (StructRNA has been removed). Names stay
    valid because they are just strings, looked up again afterwards.

    `divisor` is the authoring-scale correction from the resolved catalogue.
    The Hub library holds three different scales — most assets at 2.54x from
    inches read as Blender units, some already at 1:1, a couple at 10x — so a
    model imported without its divisor is not slightly off, it is wrong by a
    factor of two and a half.
    """
    before = set(bpy.data.objects.keys())
    lowered = filepath.lower()
    if lowered.endswith(".blend"):
        # Append rather than open: the scene being built is ours, and the model
        # is a guest in it.
        with bpy.data.libraries.load(filepath, link=False) as (source, target):
            target.objects = list(source.objects)
        for obj in target.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.update()
    elif lowered.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=filepath)
    else:
        bpy.ops.import_scene.gltf(filepath=filepath)
    imported_names = set(bpy.data.objects.keys()) - before

    mesh_names = [n for n in imported_names if bpy.data.objects[n].type == "MESH"]

    # Discard the staged room before anything is joined or measured, judged
    # against the size of the thing actually being placed.
    if lowered.endswith(".blend") and divisor and target_mm:
        limit = (max(target_mm) / 1000.0) * SHELL_FACTOR
        kept = []
        for name in mesh_names:
            extent = [v / divisor for v in _object_extent(bpy.data.objects[name])]
            if max(extent) > limit:
                continue
            kept.append(name)
        if kept:
            for name in set(mesh_names) - set(kept):
                if name in bpy.data.objects:
                    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
            imported_names = imported_names - (set(mesh_names) - set(kept))
            mesh_names = kept
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

    if divisor and divisor != 1.0:
        obj.scale = (1.0 / divisor, 1.0 / divisor, 1.0 / divisor)
        bpy.context.view_layer.update()
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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


# Model facing, read off top-down renders of each asset (tmp/facing_sheet.py).
#
# This is the thing that should have been done first. Orientation was inferred
# from bounding boxes all day — first the catalogue footprint's aspect, then the
# model's own long axis — and a box cannot tell a desk's front from its back or
# which way an L-sofa opens. So rotation_deg from the annotation was landing on
# a model already pointing somewhere arbitrary, differently for every asset.
#
# Convention after the canonical long-axis-along-X turn: the BACK of the piece
# faces +Y. These are the extra degrees needed to get each model there.
MODEL_FACING_DEG = {
    # Back already +Y once the long axis is along X.
    "ecksofa": 0, "sofa_3sitzer": 0, "sofa_2sitzer": 0, "sofa_1sitzer": 0,
    "schreibtisch": 0, "schreibtisch_kind": 0,
    "waschtisch": 0, "handwaschbecken": 0, "doppelwaschtisch": 0,
    "spuele": 0, "waschmaschine": 0, "trockner": 0,
    "kleiderschrank": 0, "schrank_40": 0, "schrank_60": 0, "abstellschrank": 0,
    "couchtisch": 0, "essgruppe_6": 0, "hocker": 0, "fernseher": 0,

    # Head of the bed points -X: turn it three quarters to bring it to +Y.
    "doppelbett": 270, "einzelbett": 270,

    # Cistern side points -X.
    "wand_wc": 270,

    # Tap end points -Y.
    "badewanne": 180,

    # Corner pieces: the enclosed corner sits back-left, so a quarter turn puts
    # its solid sides against +Y and -X, which is how they are drawn.
    "eckbadewanne": 0, "dusche": 0, "dusche_gross": 0, "dusche_klein": 0,
}


# Assets whose CHIRALITY is opposite to the symbol Rainer drew.
#
# Measured, not inferred: the grey corner sofa's occupancy grid puts its chaise
# at the -X end with the back at +Y, and ecksofa.svg puts it at +X. That is a
# reflection. No rotation reproduces it, which is why every rotation-shaped fix
# failed — the corner kept landing away from the corner.
#
# A reflection is not a rotation: it does not also correct any quarter turn
# (Codex review, 2026-08-09 — an earlier version of this comment claimed it
# did; that claim was checked and is wrong).
#
# A separate, tested-and-reverted idea lived here: reproducing the Simplifier
# canvas's drawSymbolArt quarter-turn (added when a symbol's SVG viewBox
# disagrees with its footprint's portrait/landscape) inside this renderer too.
# Tried on doppelbett; it turned a correct render (rotation_deg alone) into a
# wrong one (Rainer confirmed by eye). Root cause, confirmed by a second Codex
# review: MODEL_FACING_DEG below was already tuned, by observation, to the
# SAME canonical +Y-back orientation the transposed canvas art represents —
# adding the canvas turn on top double-applies that correction. The canvas
# transpose is real but it is a 2D-icon-display fix, not a fact about which
# way the 3D model should face; do not reintroduce it here.
# 2026-08-10, settled by RAINER HIMSELF from the 8-orientation contact
# sheet (tmp/sofa-picker.png): Nr. 7 = mirrored, 180 total. With facing 0
# and his annotated rotation_deg 180 that means the mirror is IN. Two
# agent attempts to judge this from renders both failed in opposite
# directions — orientation calls on chiral furniture go to Rainer via
# contact sheet from now on, never by eyeballing a perspective render.
MODEL_MIRROR_Y = {"ecksofa"}

# Per-LABEL orientation overrides, because one asset key resolves to a
# DIFFERENT mesh per style. Each entry is a Rainer contact-sheet pick.
MODEL_ORIENT_BY_LABEL = {
    # tmp/violet-picker.png, pick Nr. 1 (n0): no mirror, total 0 —
    # annotated rotation 180 means facing must be 180.
    "Violet Corner Sofa 14": {"mirror": False, "facing": 180},
}
# Flip test against the drawing: DMH_MIRROR_OFF=<ids> removes assets from
# the mirror set for one render; DMH_MIRROR_ON=<ids> adds them.
if os.environ.get("DMH_MIRROR_OFF"):
    MODEL_MIRROR_Y = MODEL_MIRROR_Y - set(os.environ["DMH_MIRROR_OFF"].split(","))
if os.environ.get("DMH_MIRROR_ON"):
    MODEL_MIRROR_Y = MODEL_MIRROR_Y | set(os.environ["DMH_MIRROR_ON"].split(","))


def mirror_in_y(obj):
    """Reflect the mesh through y=0 and fix the normals.

    Applied to the MESH, not the object: instances are created from proto.data,
    so an object-level -1 scale never reaches the render.
    """
    obj.scale = (1.0, -1.0, 1.0)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.flip_normals()


def align_to_footprint(obj, target_mm=None):
    """Turn the model so its LONG axis runs along local X. Nothing else.

    The previous version compared the model's aspect to the catalogue
    footprint's and turned it when they disagreed. That made the catalogue the
    authority on which way a thing faces, and the catalogue is often stale — the
    desk footprint still said 970 x 1140 (portrait) while a real desk is
    1800 x 800 (landscape), so every desk was rotated 90 degrees away from the
    way Rainer had drawn it.

    Orientation belongs to the annotation. The model just needs a consistent
    starting position so that rotation_deg means the same thing for every asset,
    whichever way its modeller happened to build it. Long axis along X is that
    convention.
    """
    _, _, dimensions = local_dimensions(obj)
    if dimensions.x <= 1e-6 or dimensions.y <= 1e-6:
        return
    if dimensions.x >= dimensions.y:
        return
    obj.rotation_euler[2] += math.radians(90)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)


# Furniture bigger than this is not furniture, it is a staged room that
# came along with the model.
PLAUSIBLE_FURNITURE_M = 4.0


def scale_to_verified(obj, verified_size_mm):
    """Scale a model to its OWN verified real-world size. True if applied.

    Scaling to the catalogue footprint made everything the wrong size, because
    the footprint is a nominal figure for that kind of furniture while the model
    is whatever the modeller actually built. A real 2200 mm dining set forced
    into an 1800 mm footprint came out at 1511 mm, and every piece was wrong the
    same way.

    Matching the longest dimension to the verified longest also repairs a bad
    scale divisor on import, since the result is pinned to a measurement rather
    than to whatever units the file happened to use.
    """
    if not verified_size_mm or max(verified_size_mm) <= 0:
        return False
    longest_m = max(verified_size_mm) * MM
    if longest_m > PLAUSIBLE_FURNITURE_M:
        return False

    _, _, dimensions = local_dimensions(obj)
    if max(dimensions) <= 1e-6:
        return False
    factor = longest_m / max(dimensions)
    obj.scale = (factor, factor, factor)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rest_on_floor(obj)
    return True


def fit_within_bbox(obj, target_mm):
    """Scale uniformly so the model fits its annotated footprint.

    normalise_to_bbox forces all three axes to the target, which distorts
    anything whose proportions differ from the symbol — and they always differ,
    because a symbol carries a nominal footprint while a real model is whatever
    the modeller made. A three-seater forced into a 2600 x 2000 corner-sofa box
    becomes a stretched slab.

    Fitting uniformly keeps the object honest. It may not fill the whole
    footprint, which is the correct outcome: the library has no corner sofa, and
    a smaller sofa placed truthfully beats a wrong one inflated to fit.
    """
    # local_dimensions returns (mins, maxs, size) — three vectors, not one.
    # Zipping the target against the whole tuple divided millimetres by the
    # `mins` vector and produced a meaningless scale factor, which is how a
    # corner sofa came to be 138 metres long. Three separate root-cause guesses
    # missed it because they were all aimed downstream of here.
    _, _, dimensions = local_dimensions(obj)
    target = [target_mm["width_mm"] * MM, target_mm["depth_mm"] * MM,
              target_mm["height_mm"] * MM]
    # Scale from the LONGEST dimension, not the tightest.
    #
    # Taking the minimum of the three factors made every model fit inside its
    # box and therefore come out systematically small — a real 2200 mm dining
    # set shrank to 1511 mm, which is what Rainer saw across the bed, the sofa
    # and the table alike.
    if max(dimensions) <= 1e-6 or max(target) <= 0:
        return
    factor = max(target) / max(dimensions)
    obj.scale = (factor, factor, factor)
    bpy.context.view_layer.update()

    # Bake it into the mesh. Instances are created from proto.data — the mesh
    # datablock — which carries no object scale, so a factor left on the
    # prototype object is silently dropped and every instance renders at native
    # size. That is why a model kept appearing many times too large however the
    # fit was computed: the fit was correct and simply never reached the render.
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rest_on_floor(obj)


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

# Diagnostic: DMH_HIDE_FEATURES=1 hides the cut-exempt opening features
# (frames, glazing, door leaves) to attribute cap-level artifacts to either
# the wall body or the features. DMH_HIDE_WALLS=1 renders without any walls, to distinguish
# "furniture failed to instance" from "furniture is occluded by a wall".
hide_walls = os.environ.get("DMH_HIDE_WALLS") == "1"
hide_features = os.environ.get("DMH_HIDE_FEATURES") == "1"

# Dollhouse cutaway by a TILTED clipping plane.
#
# The first version hid whole near-side exterior walls. That works, but it
# throws away the front of the house entirely and the result reads as a model
# with a side missing rather than a doll's house.
#
# Rainer asked for the reference-image treatment instead: one plane sloping
# from 500 mm at the front to 2000 mm at the back. The near rooms are opened
# right down to a low kerb you see over, while the far wall stays tall enough
# to enclose the picture and catch light. Everything is cut by the same plane,
# so the slice reads as deliberate rather than as per-wall decisions.
#
# Door and window openings are exempt. Their frames, glazing and leaves stand
# at full height through the cut, which is what keeps a doorway legible once
# the wall around it is only knee-high.
CUT_HEIGHT_FRONT_MM = 500
CUT_HEIGHT_BACK_MM = 2000
# DMH_FLAT_CUT=<mm> overrides both with one uniform height: boss-reference
# style flat caps, and the diagnostic that isolated the junction "notches"
# (they are the saddle where two SLOPING caps intersect, not bad geometry).
if os.environ.get("DMH_FLAT_CUT"):
    CUT_HEIGHT_FRONT_MM = CUT_HEIGHT_BACK_MM = int(os.environ["DMH_FLAT_CUT"])

building_points = [p for room in floor["rooms"] for p in room["polygon_mm"]]
building_centre = (
    sum(p[0] for p in building_points) / len(building_points),
    sum(p[1] for p in building_points) / len(building_points),
)
# Horizontal component of the camera direction, matching the camera set up
# further down. Larger projection = nearer the viewer = cut lower.
CAMERA_DIR_XY = (1.0, -1.0)
_len = math.hypot(*CAMERA_DIR_XY)
CAMERA_DIR_XY = (CAMERA_DIR_XY[0] / _len, CAMERA_DIR_XY[1] / _len)


def _camera_axis_position(point_mm):
    return ((point_mm[0] - building_centre[0]) * CAMERA_DIR_XY[0]
            + (point_mm[1] - building_centre[1]) * CAMERA_DIR_XY[1]) * MM


_axis = [_camera_axis_position(p) for p in building_points]
AXIS_MIN, AXIS_MAX = min(_axis), max(_axis)
_axis_span = max(AXIS_MAX - AXIS_MIN, 0.001)
CUT_SLOPE = (CUT_HEIGHT_FRONT_MM - CUT_HEIGHT_BACK_MM) * MM / _axis_span


def cut_plane_height(axis_position):
    """Height of the slicing plane at a distance along the camera axis."""
    return CUT_HEIGHT_BACK_MM * MM + CUT_SLOPE * (axis_position - AXIS_MIN)


def build_cut_solid():
    """A slab occupying everything ABOVE the tilted plane, to subtract."""
    ux, uy = CAMERA_DIR_XY
    vx, vy = -uy, ux
    reach = max(_axis_span * 4.0, 40.0)
    cx = building_centre[0] * MM
    cy = building_centre[1] * MM

    vertices = []
    for s, t in ((-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)):
        vertices.append((cx + ux * s + vx * t, cy + uy * s + vy * t, cut_plane_height(s)))
    for s, t in ((-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)):
        vertices.append((cx + ux * s + vx * t, cy + uy * s + vy * t, cut_plane_height(s) + 30.0))

    faces = [(0, 3, 2, 1), (4, 5, 6, 7),
             (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new("cut-solid")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    solid = bpy.data.objects.new("cut-solid", mesh)
    collection("Staging").objects.link(solid)
    solid.hide_render = True
    solid.hide_viewport = True
    return solid


def apply_cut(target, solid):
    modifier = target.modifiers.new("dollhouse-cut", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = solid
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def snap_wall_endpoints(walls, tolerance_mm=150):
    """Merge wall endpoints that are close but not exactly coincident.

    Found by measurement, not assumed: a visible notch at a junction near
    the top room traced to 4 walls whose endpoints cluster near the same
    point but differ by up to 120mm (10782.8 / 10845.8 / 10871.7 / 10902.8
    on one axis) -- not a single shared corner. Likely each room's
    boundary was traced independently in the annotator, so a "shared"
    wall between two rooms ends up drawn twice, slightly differently, each
    time. Clustering endpoints within `tolerance_mm` and snapping them to
    the cluster's centroid closes that gap without needing to know which
    room owns which wall.
    """
    points = []
    for w in walls:
        points.append(("start_mm", w))
        points.append(("end_mm", w))

    n = len(points)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        xi, yi = points[i][1][points[i][0]]
        for j in range(i + 1, n):
            xj, yj = points[j][1][points[j][0]]
            if math.hypot(xi - xj, yi - yj) <= tolerance_mm:
                union(i, j)

    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)

    moved = 0
    for members in clusters.values():
        if len(members) < 2:
            continue
        xs = [points[i][1][points[i][0]][0] for i in members]
        ys = [points[i][1][points[i][0]][1] for i in members]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        for i in members:
            key, w = points[i]
            if w[key][0] != cx or w[key][1] != cy:
                moved += 1
            w[key] = [cx, cy]
    print(f"[dollhouse] wall endpoints snapped {moved} (within {tolerance_mm}mm)")


snap_wall_endpoints(floor["walls"])

cut_solid = build_cut_solid()

cut_count = 0
sliced_walls = 0
exempt_features = 0
wall_bodies = []
for index, wall in enumerate(floor["walls"]):
    wall_openings = openings_by_wall.get(wall.get("id"), [])
    built = wall_object(f"wall-{index}", wall, wall_openings, wall_height,
                        floor["rooms"], floor["walls"])
    cut_count += len(wall_openings)
    if not built:
        continue

    if hide_walls:
        built["body"].hide_render = True
        for item in built["features"]:
            item.hide_render = True
        continue

    wall_bodies.append(built["body"])
    exempt_features += len(built["features"])
    if hide_features:
        for item in built["features"]:
            item.hide_render = True

# Walls were separate overlapping boxes, so every T- and cross-junction
# showed the intersecting wall poking through the cap as a plus-shaped bump
# or a stub (confirmed on render at the kitchen/living corner and the
# living/Diele T). A boolean UNION merges them into one continuous body
# with a single flat cap — interior overlap faces disappear, which no
# per-wall extension tuning can achieve. Union BEFORE the dollhouse cut so
# the tilted slice sees one solid, not thirty.
# Per-wall slicing is the DEFAULT again. The 30-step EXACT union chain
# silently DESTROYED whole wall stretches (proved by A/B render
# tmp/union-wall-test2.png: the Buero window sits in a full wall without
# the union, in a void with it — Rainer spotted it, the vertex probe was
# fooled by leftover fragments). The junction-bump fixes live in the
# pairing + axis-projected extensions, NOT in the union, so nothing is
# lost. DMH_UNION=1 re-enables the chain for future experiments.
if wall_bodies and os.environ.get("DMH_UNION") != "1":
    for body in wall_bodies:
        bpy.ops.object.select_all(action="DESELECT")
        apply_cut(body, cut_solid)
    sliced_walls = len(wall_bodies)
    wall_bodies = []

if wall_bodies:
    merged = wall_bodies[0]
    for other in wall_bodies[1:]:
        modifier = merged.modifiers.new("wall-union", "BOOLEAN")
        modifier.operation = "UNION"
        modifier.solver = "EXACT"
        modifier.object = other
        bpy.context.view_layer.objects.active = merged
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(other, do_unlink=True)
    # 30 chained EXACT unions leave degenerate slivers and duplicate
    # vertices along every formerly-coincident face — and the FINAL boolean
    # (the tilted dollhouse cut) then fails locally around the dirtiest
    # junctions, leaving full-height towers exactly there (the plus-shaped
    # bumps: same failure family as the window-cutter coplanarity bug).
    # Clean the merged mesh before asking one more boolean of it.
    bpy.context.view_layer.objects.active = merged
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.dissolve_degenerate(threshold=0.001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    apply_cut(merged, cut_solid)
    sliced_walls = len(wall_bodies)

# ------------------------------------------------- procedurally built pieces
#
# Some things are not in the model library and never will be. Of 153 bathroom
# models in the converted library not one is taller than 1400 mm — the CGAxis
# sets are fixtures, not enclosures — so there is no shower cabin to find. A
# tray with two glass panels is three boxes and reads better than a wrong
# model. The same goes for a television panel and a towel radiator.
#
# Kitchen runs and islands are different again: they are not objects at all but
# annotated geometry, drawn as a path or a rectangle, so they are built to the
# shape Rainer drew rather than fetched from anywhere.

def _towards_centre(a, b, distance):
    """Perpendicular offset from a segment, pointing into the ROOM.

    A counter run is drawn ON the wall it stands against, so a box centred on
    that line would sit half inside the plaster. It has to move inward, and
    inward is whichever side the middle of the room is on.

    This used to measure against the whole BUILDING's centroid. In an
    L-shaped or multi-wing plan that point can sit in a different room
    entirely, or off to one side of the actual kitchen -- confirmed here:
    the kitchen run in bungalow_040_66 was landing away from its wall
    because the building's overall centre didn't agree with the kitchen's
    own. Falls back to the building centroid only if the run's midpoint
    isn't inside any known room (shouldn't happen for a real placement, but
    a silent KeyError on `floor` at import time would be worse than a
    documented fallback).
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

    room = room_at(mid, floor["rooms"])  # `mid` is already metres, matching point_in_polygon
    if room:
        pts = room["polygon_mm"]
        target = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    else:
        target = building_centre

    towards = ((target[0] * MM - mid[0]) * nx + (target[1] * MM - mid[1]) * ny)
    sign = 1.0 if towards > 0 else -1.0
    return nx * distance * sign, ny * distance * sign


def _snap_segment_to_walls(a, b, depth_m):
    """Fitted-kitchen rule (Rainer: 'wir sagten snap to walls'): a counter
    segment drawn NEAR a wall goes flush against it — back face on the
    wall face — and its ends extend to touching side walls, so no crumb
    gap survives. Free-standing segments (no wall within 600mm) stay
    exactly where they were drawn."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    if length < 0.05:
        return a, b
    ux, uy = (bx - ax) / length, (by - ay) / length
    seg_angle = math.atan2(uy, ux)
    mid_mm = ((ax + bx) / 2 / MM, (ay + by) / 2 / MM)

    best = None
    for wall in floor["walls"]:
        sx, sy = wall["start_mm"]
        ex, ey = wall["end_mm"]
        seg_sq = (ex - sx) ** 2 + (ey - sy) ** 2
        if not seg_sq:
            continue
        wall_angle = math.atan2(ey - sy, ex - sx)
        diff = abs((seg_angle - wall_angle + math.pi / 2) % math.pi - math.pi / 2)
        if diff > math.radians(20):
            continue
        t = max(0.0, min(1.0, ((mid_mm[0] - sx) * (ex - sx) + (mid_mm[1] - sy) * (ey - sy)) / seg_sq))
        px, py = sx + t * (ex - sx), sy + t * (ey - sy)
        dist = math.hypot(mid_mm[0] - px, mid_mm[1] - py)
        face = dist - wall["thickness_mm"] / 2
        if face > 600:
            continue
        if best is None or face < best[0]:
            direction = ((px - mid_mm[0]) / dist, (py - mid_mm[1]) / dist)
            best = (face, direction)
    if best is not None:
        face, direction = best
        if os.environ.get("DMH_DEBUG_SNAP"):
            print(f"[snap] seg mid={mid_mm[0]:.0f},{mid_mm[1]:.0f} "
                  f"face={face:.0f}mm dir={direction[0]:.2f},{direction[1]:.2f}")
        # Drawn line = FRONT edge? No: the drawn line is the wall-side
        # edge (the offset code pushes the body inward by depth/2), so
        # the line itself must land ON the wall face.
        shift_m = face * MM
        if abs(shift_m) > 0.002:
            ax += direction[0] * shift_m
            ay += direction[1] * shift_m
            bx += direction[0] * shift_m
            by += direction[1] * shift_m

    # End extension: reach a roughly perpendicular wall within 450mm.
    def extend(px_m, py_m, out_dir):
        best_reach = None
        for wall in floor["walls"]:
            sx, sy = wall["start_mm"]
            ex, ey = wall["end_mm"]
            seg_len = math.hypot(ex - sx, ey - sy)
            if not seg_len:
                continue
            wall_angle = math.atan2(ey - sy, ex - sx)
            diff = abs((seg_angle - wall_angle + math.pi / 2) % math.pi - math.pi / 2)
            if diff < math.radians(65):
                continue
            nx, ny = -(ey - sy) / seg_len, (ex - sx) / seg_len
            side = ((px_m / MM - sx) * nx + (py_m / MM - sy) * ny)
            approach = -(out_dir[0] * nx + out_dir[1] * ny)
            if abs(approach) < 0.3:
                continue
            if approach < 0:
                nx, ny, side, approach = -nx, -ny, -side, -approach
            reach = (side - wall["thickness_mm"] / 2) / approach
            if reach < -50 or reach > 450:
                continue
            if best_reach is None or reach < best_reach:
                best_reach = reach
        if best_reach is None or best_reach <= 2:
            return px_m, py_m
        return px_m + out_dir[0] * best_reach * MM, py_m + out_dir[1] * best_reach * MM

    ax, ay = extend(ax, ay, (-ux, -uy))
    bx, by = extend(bx, by, (ux, uy))
    wall_dir = best[1] if best is not None else None
    return (ax, ay), (bx, by), wall_dir


def build_path_run(name, item, material, worktop):
    """A counter run or a Vorwandinstallation, following the drawn path."""
    points = [(q[0] * MM, q[1] * MM) for q in item["points_mm"]]
    depth = item["depth_mm"] * MM
    height = item["height_mm"] * MM
    built = []
    for index in range(len(points) - 1):
        a, b = points[index], points[index + 1]
        snapped_wall_dir = None
        if item.get("type") == "counter":
            a, b, snapped_wall_dir = _snap_segment_to_walls(a, b, depth)
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length < 0.05:
            continue
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        if snapped_wall_dir is not None:
            # The snapped line sits exactly ON the room boundary, where
            # room_at() can land in the NEIGHBOUR room and flip the body
            # to the wrong side (it did: the run vanished into the Diele).
            # The correct side is simply AWAY from the snapped wall.
            ox = -snapped_wall_dir[0] * depth / 2
            oy = -snapped_wall_dir[1] * depth / 2
            if item.get("type") == "counter":
                # Remember which way the fitted kitchen faces: the tall
                # oven unit at the end of the run must face the SAME way.
                KITCHEN_RUN_FRONTS.append((-snapped_wall_dir[0],
                                           -snapped_wall_dir[1]))
        else:
            ox, oy = _towards_centre(a, b, depth / 2)
        centre = ((a[0] + b[0]) / 2 + ox, (a[1] + b[1]) / 2 + oy, height / 2)
        built.append(box(name + "-" + str(index), centre, (length, depth, height),
                         angle, material, into="Furniture"))
        if worktop:
            built.append(box(name + "-top-" + str(index),
                             (centre[0], centre[1], height + 0.02),
                             (length, depth * 1.03, 0.04), angle, worktop,
                             into="Furniture"))
    return built


def build_rect(name, item, material, worktop):
    """An island: the dragged rectangle, at counter height."""
    points = [(q[0] * MM, q[1] * MM) for q in item["points_mm"]]
    xs = [q[0] for q in points]
    ys = [q[1] for q in points]
    width, depth = max(xs) - min(xs), max(ys) - min(ys)
    if width < 0.1 or depth < 0.1:
        return []
    height = item["height_mm"] * MM
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, height / 2)
    built = [box(name, centre, (width, depth, height), 0.0, material, into="Furniture")]
    if worktop:
        built.append(box(name + "-top", (centre[0], centre[1], height + 0.02),
                         (width * 1.04, depth * 1.04, 0.04), 0.0, worktop,
                         into="Furniture"))
    return built


def build_shower(name, item):
    """Tray plus two glass panels. No enclosure exists in the library."""
    bbox = item["target_bbox_mm"]
    width, depth = bbox["width_mm"] * MM, bbox["depth_mm"] * MM
    x, y = item["position_mm"][0] * MM, item["position_mm"][1] * MM
    angle = math.radians(item.get("rotation_deg", 0))
    built = [box(name + "-tray", (x, y, 0.04), (width, depth, 0.08), angle,
                 GRANITE_MAT, into="Furniture")]
    height = 2.0
    for axis, extent in ((0, width), (1, depth)):
        offset = (depth if axis == 0 else width) / 2
        local_x = 0.0 if axis == 0 else offset
        local_y = offset if axis == 0 else 0.0
        dx = math.cos(angle) * local_x - math.sin(angle) * local_y
        dy = math.sin(angle) * local_x + math.cos(angle) * local_y
        dimensions = (extent, 0.012, height) if axis == 0 else (0.012, extent, height)
        built.append(box(name + "-glass-" + str(axis), (x + dx, y + dy, height / 2),
                         dimensions, angle, GLASS_MAT, into="Furniture"))
    return built


FLUSH_TYPES = ("oven_housing", "fridge", "washer", "wardrobe", "wall_panel")


def _nearest_wall_direction(centre_xy_m, max_gap_mm=900):
    """Unit direction from a point toward the nearest wall face, or None."""
    cx_mm, cy_mm = centre_xy_m[0] / MM, centre_xy_m[1] / MM
    best = None
    for wall in floor["walls"]:
        sx, sy = wall["start_mm"]
        ex, ey = wall["end_mm"]
        seg_sq = (ex - sx) ** 2 + (ey - sy) ** 2
        if not seg_sq:
            continue
        t = max(0.0, min(1.0, ((cx_mm - sx) * (ex - sx) + (cy_mm - sy) * (ey - sy)) / seg_sq))
        px, py = sx + t * (ex - sx), sy + t * (ey - sy)
        dist = math.hypot(cx_mm - px, cy_mm - py)
        if dist <= 1 or dist > max_gap_mm:
            continue
        if best is None or dist < best[0]:
            best = (dist, ((px - cx_mm) / dist, (py - cy_mm) / dist))
    return best[1] if best else None


def _snap_flush(centre_xy_m, depth_m, max_gap_mm=450):
    """Shift a fitted item so its back face touches the nearest wall face.

    A fitted kitchen has no air between tall units and the wall (Rainer:
    'die Küche ist immer noch nicht ohne Lücken'). Gaps appear when the
    annotated footprint is deeper than the catalogue depth the box is
    built with — the centre stays, the faces shrink. Snapping the back
    face to the nearest wall face within 450mm closes exactly that, and
    never moves anything drawn free-standing in the middle of a room."""
    cx_mm, cy_mm = centre_xy_m[0] / MM, centre_xy_m[1] / MM
    best = None
    for wall in floor["walls"]:
        sx, sy = wall["start_mm"]
        ex, ey = wall["end_mm"]
        seg_sq = (ex - sx) ** 2 + (ey - sy) ** 2
        if not seg_sq:
            continue
        t = max(0.0, min(1.0, ((cx_mm - sx) * (ex - sx) + (cy_mm - sy) * (ey - sy)) / seg_sq))
        px, py = sx + t * (ex - sx), sy + t * (ey - sy)
        dist = math.hypot(cx_mm - px, cy_mm - py)
        face = dist - wall["thickness_mm"] / 2
        if face <= 0 or face > max_gap_mm:
            continue
        if best is None or face < best[0]:
            direction = ((px - cx_mm) / dist, (py - cy_mm) / dist)
            best = (face, direction)
    if best is None:
        return centre_xy_m, None
    face, direction = best
    shift_mm = face - (depth_m / MM) / 2
    if shift_mm <= 2:
        return centre_xy_m, direction
    return ((centre_xy_m[0] + direction[0] * shift_mm * MM,
             centre_xy_m[1] + direction[1] * shift_mm * MM), direction)


def build_box(name, item, material):
    """A plain carcass at the annotated size.

    The fallback for anything with no usable model — wardrobes, cupboards,
    lowboards, hall units. Rainer's rule: rectilinear furniture is a scaled cube
    with a sensible finish, and only organic shapes need real geometry.

    This case was missing entirely: the plan builder emitted build="box" and the
    renderer had no branch for it, so every one of them silently placed nothing
    and the bedrooms came out empty.
    """
    bbox = item["target_bbox_mm"]
    width = (bbox.get("width_mm") or 600) * MM
    depth = (bbox.get("depth_mm") or 600) * MM
    height = (bbox.get("height_mm") or 800) * MM
    mount = item.get("height_mm", 0) * MM
    z = mount if mount else height / 2
    angle = math.radians(item.get("rotation_deg", 0))
    cx, cy = item["position_mm"][0] * MM, item["position_mm"][1] * MM
    back_direction = None
    if item.get("type") in FLUSH_TYPES:
        (cx, cy), back_direction = _snap_flush((cx, cy), depth)
    pieces = [box(name, (cx, cy, z), (width, depth, height), angle,
                  material, into="Furniture")]

    # The tall oven housing gets the Built-in Double Oven — but the
    # counter run that defines the kitchen's facing may not be built yet
    # (same placement-order trap as the sink cutout), so the actual
    # embedding runs AFTER the placement loop via OVEN_QUEUE.
    if item.get("type") == "oven_housing":
        # back_direction (the housing's OWN snap direction, discarded until
        # now) is the only reliable facing — the counter run's front can
        # belong to a different wall on an L-shaped kitchen, which is
        # exactly what pointed the oven at the aisle instead of the
        # cabinet's real open side.
        OVEN_QUEUE.append((cx, cy, width, depth, angle, back_direction))

    # A featureless slab at wardrobe size reads as a construction error, not
    # as furniture (confirmed on render: every carcass looked like a blank
    # monolith). Door gaps are what make cabinetry read as cabinetry at
    # dollhouse distance: thin dark vertical reveals splitting the tall face
    # into ~600 mm doors, on BOTH long faces since which one faces the room
    # depends on the item's rotation and the back is hidden inside the wall
    # zone anyway. Storage types only — a washer or TV panel has its own look.
    if item.get("type") in ("wardrobe", "dressing_wardrobe", "storage_shelving",
                            "sideboard", "tv_unit", "coat_rack") and height > 0.35:
        gap_mat = furniture_material("office_chair")  # metal-matte-black
        doors = max(2, round((width / MM) / 600))
        sin_a, cos_a = math.sin(angle), math.cos(angle)
        for d in range(1, doors):
            along = -width / 2 + width * d / doors
            for side in (-1.0, 1.0):
                off_x = along * cos_a - side * (depth / 2) * sin_a
                off_y = along * sin_a + side * (depth / 2) * cos_a
                pieces.append(box(f"{name}-gap-{d}-{int(side)}",
                                  (cx + off_x, cy + off_y, z),
                                  (0.012, 0.006, height * 0.92), angle,
                                  gap_mat, into="Furniture"))
    return pieces


def build_plant(name, item):
    """A potted plant placeholder: terracotta pot + layered green foliage.

    Deliberately simple geometry — the ComfyUI polish pass turns a green
    blob with the right silhouette into a plausible plant (Rainer's plan
    for filling large empty areas). Real botany models are not worth their
    polygon count at dollhouse distance."""
    pot_mat = flat(f"{name}-pot", (0.70, 0.42, 0.30), roughness=0.8)
    leaf_mat = flat(f"{name}-leaf", (0.23, 0.42, 0.20), roughness=0.9)
    cx, cy = item["position_mm"][0] * MM, item["position_mm"][1] * MM
    bbox = item.get("target_bbox_mm") or {}
    width = (bbox.get("width_mm") or 450) * MM
    total_h = (bbox.get("height_mm") or 1300) * MM
    pot_h = total_h * 0.25
    pieces = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=width * 0.32,
                                        depth=pot_h,
                                        location=(cx, cy, pot_h / 2))
    pot = bpy.context.active_object
    pot.name = f"{name}-pot"
    pot.data.materials.append(pot_mat)
    for coll in list(pot.users_collection):
        coll.objects.unlink(pot)
    collection("Furniture").objects.link(pot)
    pieces.append(pot)
    import random
    rng = random.Random(hash(name) & 0xFFFF)
    for i in range(5):
        fz = pot_h + (total_h - pot_h) * (0.25 + 0.16 * i)
        radius = width * (0.55 - 0.07 * i) * (0.9 + rng.random() * 0.3)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius,
                                              location=(cx + (rng.random() - 0.5) * width * 0.2,
                                                        cy + (rng.random() - 0.5) * width * 0.2,
                                                        fz))
        blob = bpy.context.active_object
        blob.name = f"{name}-leaf-{i}"
        blob.scale = (1.0, 1.0, 0.55)
        blob.data.materials.append(leaf_mat)
        for coll in list(blob.users_collection):
            coll.objects.unlink(blob)
        collection("Furniture").objects.link(blob)
        pieces.append(blob)
    return pieces


def build_panel(name, item, material, thickness_m):
    """A flat wall-hung panel: television, towel radiator, hob."""
    bbox = item["target_bbox_mm"]
    width = bbox["width_mm"] * MM
    height = bbox["height_mm"] * MM
    mount = item.get("height_mm", 0) * MM
    z = mount if mount else height / 2
    return [box(name, (item["position_mm"][0] * MM, item["position_mm"][1] * MM, z),
                (width, thickness_m, height), math.radians(item.get("rotation_deg", 0)),
                material, into="Furniture")]


prototypes = {}
placed = 0
built_procedurally = 0
failed = []

sink_cut_queue = []
KITCHEN_RUN_FRONTS = []
OVEN_QUEUE = []
for item in floor["placements"]:
    asset_id = item["asset_id"]

    kind = item.get("build")
    # The plan already resolved a real sink model for `spuele` (Kitchen Sink
    # 24.blend, preserve_materials true) -- but it also carries build="hob"
    # (the same generic label kochfeld uses), which was routing it through
    # the plain-box fallback and throwing the real model away. Confirmed
    # visually: it rendered as a flat grey slab with no basin, not a sink.
    # Only skip the procedural branch for this one case; kochfeld (the
    # actual hob, no real model resolved) still needs it.
    has_real_model = item["type"] == "sink" and item.get("mesh_path")
    if kind and not has_real_model:
        material = furniture_material(item["type"])
        if kind == "path":
            pieces = build_path_run(asset_id + "-" + str(placed), item, material,
                                    GRANITE_MAT if item["type"] == "counter" else None)
        elif kind == "rect":
            pieces = build_rect(asset_id + "-" + str(placed), item, material, GRANITE_MAT)
        elif kind == "shower":
            pieces = build_shower(asset_id + "-" + str(placed), item)
        elif kind == "tv":
            pieces = build_panel(asset_id + "-" + str(placed), item, TV_MAT, 0.06)
        elif kind == "radiator":
            pieces = build_panel(asset_id + "-" + str(placed), item, material, 0.08)
        elif kind == "hob":
            # Was build_panel with a fixed 40mm thickness -- correct for a
            # wall-mounted TV or radiator, wrong for a hob or sink sitting
            # flat on a counter: it collapsed the item's real depth (558mm /
            # 517mm) down to 40mm, rendering as an almost-invisible sliver.
            # Confirmed by inspecting the actual scene object, not guessed:
            # dims came back (0.941, 0.04, 0.05)m -- the depth axis was the
            # one being thrown away. build_box uses the full footprint and
            # the item's own mount height.
            #
            # That mount height (900mm / 880mm) is the CABINET height, not
            # the usable surface -- build_rect/build_path_run sit a 40mm-
            # thick worktop slab ON TOP of the cabinet, so a hob mounted at
            # exactly cabinet height is centred 25mm inside that slab, not
            # resting on it. Confirmed on the kitchen island: the hob object
            # existed (hide_render False, correct dims) but was invisible in
            # every render, buried in the worktop mesh. +40mm clears it.
            #
            # Both a sink and a hob route through this same "hob" build kind
            # (a plan-generation label, not a real distinction) -- but a dark
            # glass hob and a dark sink both sitting on the now-matte-black
            # counter (this session's own earlier fix) made the sink
            # disappear entirely. Sink gets steel; hob keeps dark glass.
            hob_material = furniture_material("sink") if item["type"] == "sink" else TV_MAT
            # +40 clears the worktop slab; build_box's z is the object's
            # CENTRE, so also clear half its own thickness or the object
            # still sinks halfway into the worktop from above. Verified by
            # measurement, not assumed: first pass (+40 only) put kochfeld's
            # z-range at 0.915-0.965m against the worktop's own 0.9-0.94m --
            # still a 25mm overlap.
            own_height_mm = (item.get("target_bbox_mm") or {}).get("height_mm", 0)
            on_worktop = dict(item, **{"height_mm": item.get("height_mm", 0) + 40 + own_height_mm / 2})
            pieces = build_box(asset_id + "-" + str(placed), on_worktop, hob_material)
            if item["type"] == "hob" and pieces:
                # Induction zone rings: four thin light rings in a 2x2 grid
                # on the glass — without them the hob read as a blank slab
                # (Rainer). Geometry, not texture: survives every finish.
                ring_mat = flat("hob-ring", (0.55, 0.55, 0.58), roughness=0.4)
                hob_obj = pieces[0]
                bpy.context.view_layer.update()
                hw, hd = hob_obj.dimensions.x, hob_obj.dimensions.y
                top_z = hob_obj.location.z + hob_obj.dimensions.z / 2 + 0.001
                a = hob_obj.rotation_euler.z
                cos_a, sin_a = math.cos(a), math.sin(a)
                radius = min(hw, hd) * 0.16
                for ix in (-1, 1):
                    for iy in (-1, 1):
                        lx, ly = ix * hw * 0.22, iy * hd * 0.22
                        wx = hob_obj.location.x + lx * cos_a - ly * sin_a
                        wy = hob_obj.location.y + lx * sin_a + ly * cos_a
                        bpy.ops.mesh.primitive_torus_add(
                            major_radius=radius, minor_radius=0.004,
                            major_segments=32, minor_segments=6,
                            location=(wx, wy, top_z))
                        ring = bpy.context.active_object
                        ring.name = f"{asset_id}-ring-{placed}-{ix}-{iy}"
                        ring.scale = (1, 1, 0.25)
                        ring.data.materials.append(ring_mat)
                        for coll in list(ring.users_collection):
                            coll.objects.unlink(ring)
                        collection("Furniture").objects.link(ring)
                        pieces.append(ring)
        elif kind == "plant":
            pieces = build_plant(asset_id + "-" + str(placed), item)
        elif kind == "box":
            pieces = build_box(asset_id + "-" + str(placed), item, material)
        else:
            print(f"[dollhouse] WARNING no builder for build={kind!r} ({asset_id})")
            pieces = []
        if pieces:
            built_procedurally += 1
            placed += 1
        continue

    if not item.get("mesh_path"):
        failed.append(asset_id)
        continue

    if asset_id not in prototypes:
        bbox = item.get("target_bbox_mm") or {}
        target_mm = [bbox.get("width_mm") or 0, bbox.get("depth_mm") or 0,
                     bbox.get("height_mm") or 0]
        obj = import_model(item["mesh_path"], item.get("scale_divisor", 1.0),
                           target_mm if max(target_mm) else None)
        if obj is None:
            failed.append(asset_id)
            prototypes[asset_id] = None
            continue

        if item.get("preserve_native_scale"):
            # Library models are authored at true size and carry their own
            # materials. Rescaling would distort them and overwriting their
            # materials would throw away the reason to use them at all.
            rest_on_floor(obj)
        elif item.get("size_mismatch"):
            # Flagged by the plan builder as too far from its footprint to fit
            # without looking wrong. Drop the model; the box built for it in
            # the procedural branch stands in.
            bpy.data.objects.remove(obj, do_unlink=True)
            prototypes[asset_id] = None
            failed.append(asset_id)
            continue
        elif item.get("preserve_materials"):
            # Dropping the fit entirely and trusting each model's verified size
            # was tried and put a corner sofa back at 138 m: that .blend holds
            # something enormous which the cataloguing pass silently skipped, so
            # its recorded divisor was never right. Until every asset's true
            # size is trustworthy this fit stays, as the backstop that keeps a
            # bad divisor merely inaccurate rather than catastrophic.
            align_to_footprint(obj)
            # Orientation is per MODEL, not per asset key: the modern and
            # classic picks for one symbol are different meshes with
            # different chirality. Rainer settled each via contact sheet:
            # grey modern ecksofa = Nr. 7 (mirror, facing 0), Violet
            # Corner Sofa 14 = Nr. 1 (no mirror, facing 180, since his
            # annotated rotation of 180 must land on 0 total).
            orient = MODEL_ORIENT_BY_LABEL.get(item.get("model_label") or "")
            mirror_this = (orient["mirror"] if orient
                           else asset_id in MODEL_MIRROR_Y)
            if mirror_this:
                mirror_in_y(obj)
                print(f"[dollhouse] mirrored      {asset_id} (asset chirality)")
            facing = (orient["facing"] if orient
                      else MODEL_FACING_DEG.get(asset_id, 0))
            if facing:
                obj.rotation_euler[2] += math.radians(facing)
                bpy.context.view_layer.update()
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            # Annotation beats heuristic. A footprint measured on the plan is
            # the authority; the model's verified size is only the fallback for
            # symbols nobody has measured yet.
            if item.get("footprint_measured"):
                fit_within_bbox(obj, item["target_bbox_mm"])
            elif not scale_to_verified(obj, item.get("verified_size_mm")):
                fit_within_bbox(obj, item["target_bbox_mm"])
            accent_key = (item.get("model_label")
                          if item.get("model_label") in ACCENT_OVERRIDE
                          else asset_id)
            if accent_key in ACCENT_OVERRIDE:
                obj.data.materials.clear()
                obj.data.materials.append(accent_material(accent_key))
        else:
            normalise_to_bbox(obj, item["target_bbox_mm"])
            obj.data.materials.clear()
            obj.data.materials.append(furniture_material(item["type"]))

        obj.name = f"proto-{asset_id}"
        place_in(obj, "Prototypes")
        obj.hide_render = True
        obj.hide_viewport = True
        prototypes[asset_id] = obj

    proto = prototypes[asset_id]
    if proto is None:
        continue

    instance = bpy.data.objects.new(f"{asset_id}-{placed}", proto.data)
    collection("Furniture").objects.link(instance)
    pending_sink_cut = None

    # `height_mm` is a MOUNT height — where the centre of a wall-mounted item
    # sits — but prototypes are re-origined with their base at z=0. Placing a
    # 1600mm mirror with its base at 1400mm put its top at 3000mm, a full
    # 600mm above a 2400mm wall, which is why mirrors appeared to float in
    # mid-air. Offset by half the item's height so the centre lands on the
    # mount instead.
    mount_mm = item.get("height_mm", 0)
    if mount_mm:
        # Was `item["target_bbox_mm"]["height_mm"]` -- the ANNOTATED target,
        # not the prototype's real height. Holds only when fit_within_bbox
        # happened to scale height to match the target exactly, which it
        # doesn't: it scales uniformly by the LONGEST axis only, so a real
        # model whose proportions differ from the annotation keeps its own
        # true height. Confirmed broken on `spuele` once it started using
        # its real resolved model instead of a procedural box: target height
        # was 200mm, real height came out 504mm, and the old formula sank
        # the sink halfway through the cabinet (z-range 0.528-1.032m against
        # a worktop at 0.9-0.94m) instead of resting on the worktop.
        # proto.dimensions.z is the prototype's actual evaluated height,
        # correct regardless of how it was scaled.
        z = mount_mm * MM - proto.dimensions.z / 2

        # Countertop fixtures aren't "centred at a mount height" the way a
        # mirror is -- `height_mm` here is the cabinet-top reference (same
        # role kochfeld's mount plays in the procedural hob/sink branch,
        # which needed +40mm worktop clearance + half the fixture's own
        # height to rest ON the worktop rather than centre through it). A
        # sink using its real model goes through this generic path instead,
        # and needs the same correction: base of the fixture at the
        # worktop's top, not the fixture centred on the cabinet height.
        if item["type"] == "sink":
            # The prototype's ORIGIN is its base (re-origined earlier), and
            # this instance carries no rotation, so instance.location.z IS
            # the base position directly -- no half-height term here. (First
            # pass added +proto.dimensions.z/2, which would have floated the
            # sink a further half-height above the worktop -- caught before
            # rendering, not after.)
            worktop_top_mm = mount_mm + 40
            if asset_id == "spuele":
                # Drop-in KITCHEN sink sits IN the counter: body sunk so
                # rim + faucet rise above the worktop; the cutout is
                # queued until AFTER the whole placement loop, because the
                # counter run is often built later than the sink that
                # sits in it (proven: 0 '-top-' objects existed at this
                # sink's placement time). Bathroom basins (same type)
                # stay ON their vanity tops, unrotated.
                z = (worktop_top_mm - 55) * MM
                pending_sink_cut = (max(proto.dimensions.x, 0.2),
                                    max(proto.dimensions.y, 0.2),
                                    worktop_top_mm)
            else:
                z = worktop_top_mm * MM
    else:
        z = 0.0

    px, py = item["position_mm"]
    if asset_id in POSITION_OVERRIDE:
        dx, dy = POSITION_OVERRIDE[asset_id]
        px, py = px + dx, py + dy
    instance.location = (
        px * MM,
        py * MM,
        z,
    )
    # ROTATION_OVERRIDE: `sofa_1sitzer`'s stored rotation_deg (315) was
    # checked twice tonight -- it's genuinely what the annotation says, and
    # the render was confirmed to reproduce it exactly (Codex, second
    # review). Rainer has now said three times, including this session,
    # that it's still wrong. Overriding at the render-plan level, not
    # touching the Simplifier annotation file -- that stays his to correct
    # at the source. 0 degrees matches "upright, arms left/right, back at
    # top" as measured against the source drawing earlier this session.
    rotation_env = os.environ.get("DMH_ROT_" + asset_id.upper())
    if rotation_env is not None:
        rotation_deg = float(rotation_env)
    else:
        rotation_deg = ROTATION_OVERRIDE.get(asset_id, item.get("rotation_deg", 0.0))
    instance.rotation_euler[2] = math.radians(rotation_deg)

    if pending_sink_cut is not None:
        sink_w, sink_d, worktop_top_mm = pending_sink_cut
        # Faucet belongs at the WALL side of a counter sink (Rainer).
        instance.rotation_euler[2] = math.radians(rotation_deg + 180)
        sink_cut_queue.append((instance.location.x, instance.location.y,
                               sink_w, sink_d, worktop_top_mm,
                               instance.rotation_euler.z, placed))
    placed += 1

# Built-in double ovens, AFTER the loop so the kitchen run's facing is
# known (fitted-kitchen rule: the tall unit fronts like its counter run).
oven_path = (r"E:/_models_hub/_extracted/Built_in_Double_Oven_BLEND"
             r"/Built in Double Oven.blend")
for cx, cy, width, depth, angle, own_back_direction in OVEN_QUEUE:
    if not os.path.exists(oven_path):
        break
    if own_back_direction is not None:
        fx, fy = -own_back_direction[0], -own_back_direction[1]
    elif KITCHEN_RUN_FRONTS:
        fx, fy = KITCHEN_RUN_FRONTS[0]
    else:
        direction = _nearest_wall_direction((cx, cy))
        if direction is None:
            continue
        fx, fy = -direction[0], -direction[1]
    oven = import_model(oven_path, 1.0, [560, 550, 880])
    if oven is None:
        continue
    scale = min(1.0,
                (width * 0.9) / max(oven.dimensions.x, 1e-6),
                (depth * 0.95) / max(oven.dimensions.y, 1e-6))
    oven.scale = (scale, scale, scale)
    oven.location = (cx, cy, 0.60)
    oven.rotation_euler = (0, 0, math.atan2(fy, fx) + math.pi / 2)
    bpy.context.view_layer.update()
    # Exact flush, measured: foremost bbox corner along the front axis
    # lands 5mm proud of the cabinet front.
    front_plane = cx * fx + cy * fy + depth / 2
    corners = [oven.matrix_world @ mathutils.Vector(c) for c in oven.bound_box]
    foremost = max(c.x * fx + c.y * fy for c in corners)
    # 50mm proud. History: 5mm made the dark glass vanish optically into
    # the dark cabinet, 25mm was still "sticking out too far" by eye
    # according to Rainer AND simultaneously not far enough — he hand-
    # repositioned it +28mm further out in the exported .blend (measured:
    # 8.719 -> 8.747m along the facing axis). 25+28=53, rounded to a
    # clean 50mm.
    shift = foremost - (front_plane + 0.050)
    oven.location.x -= fx * shift
    oven.location.y -= fy * shift
    for coll in list(oven.users_collection):
        coll.objects.unlink(oven)
    collection("Furniture").objects.link(oven)
    print(f"[dollhouse] oven embedded   front=({fx:.1f},{fy:.1f})")

# Kitchen-sink cutouts, AFTER every placement exists (the counter run is
# often built later in the loop than the sink that sits in it).
if sink_cut_queue:
    bpy.context.view_layer.update()
    for sx_m, sy_m, sink_w, sink_d, worktop_top_mm, rot_z, index in sink_cut_queue:
        for candidate in bpy.data.objects:
            if candidate.type != "MESH" or "-top-" not in candidate.name:
                continue
            local = candidate.matrix_world.inverted() @ mathutils.Vector(
                (sx_m, sy_m, worktop_top_mm * MM))
            lo = [min(v[i] for v in candidate.bound_box) for i in range(2)]
            hi = [max(v[i] for v in candidate.bound_box) for i in range(2)]
            if not (lo[0] - 0.1 <= local.x <= hi[0] + 0.1
                    and lo[1] - 0.1 <= local.y <= hi[1] + 0.1):
                continue
            cutter = box(f"sink-cut-{index}",
                         (sx_m, sy_m, worktop_top_mm * MM - 0.02),
                         # 78%: tight enough that the sink body fills the
                         # opening completely — at 88% a sliver of the black
                         # carcass showed through around the basin.
                         (sink_w * 0.78, sink_d * 0.78, 0.25), rot_z, None)
            cut_opening(candidate, cutter)
            print(f"[dollhouse] sink cutout    {candidate.name}")
            # Rainer's own fix (hand-edited in the exported .blend, folded
            # back into the generator): the CORPUS box directly under the
            # worktop still had its own solid top face right below the
            # cutout, reading as a flat surface inside the sink instead of
            # an open cabinet interior. Deleting that one face (not a
            # boolean — the corpus stays a solid box everywhere else, it's
            # hidden under the worktop anyway except exactly at this hole)
            # is simpler than the steel-liner-plate patch it replaces.
            corpus_name = candidate.name.replace("-top-", "-", 1)
            corpus = bpy.data.objects.get(corpus_name)
            if corpus is not None and corpus.type == "MESH":
                import bmesh
                bm = bmesh.new()
                bm.from_mesh(corpus.data)
                bm.faces.ensure_lookup_table()
                top_faces = [f for f in bm.faces if f.normal.z > 0.9]
                bmesh.ops.delete(bm, geom=top_faces, context="FACES")
                bm.to_mesh(corpus.data)
                bm.free()
                corpus.data.update()
                print(f"[dollhouse] sink corpus opened  {corpus_name}")
            break
        else:
            print(f"[dollhouse] sink cutout    NO WORKTOP at {sx_m:.2f},{sy_m:.2f}")

# ---------------------------------------------------------------- underlay
#
# Lay the original drawing under the model at true scale and look straight
# down. Everything verified so far has been internal consistency — the geometry
# checked against the data it came from — which is precisely how a corner sofa
# stayed 138 m through three confident fixes. The source drawing is the one
# reference outside the pipeline, so overlaying on it is the only check that can
# catch a wall in the wrong place or a room the wrong size.
#
#   DMH_UNDERLAY=<image>  put the drawing on the floor
#   DMH_TOPVIEW=1         orthographic plan view, to compare against it

def add_underlay(path, floor_plan):
    """Floor plane carrying the source drawing, mapped to annotation space.

    The Simplifier's scale is metres across the image WIDTH, so the drawing
    spans width_mm in x, and height_mm = width_mm * (pixel height / pixel
    width) in y. Normalized y is flipped when the plan is built, so the image
    has to be flipped back to line up.
    """
    scale = floor_plan.get("scale_metres_per_x_unit")
    if not scale or not os.path.exists(path):
        return None

    image = bpy.data.images.load(path)
    pixel_w, pixel_h = image.size
    if not pixel_w or not pixel_h:
        return None

    width_m = scale
    height_m = width_m * (pixel_h / float(pixel_w))

    bpy.ops.mesh.primitive_plane_add(size=1.0,
                                     location=(width_m / 2, height_m / 2, -0.005))
    plane = bpy.context.active_object
    plane.name = "source-underlay"
    plane.scale = (width_m, height_m, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    material = bpy.data.materials.new("source-underlay")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    mapping = nodes.new("ShaderNodeMapping")
    coords = nodes.new("ShaderNodeTexCoord")
    # No flip. The plan builder maps image row 0 to the TOP of world y, and
    # Blender's UV v=1 is already the top row of an image, so the two
    # conventions cancel. Flipping "to match" put the bathroom at the wrong end
    # of the house.
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    links.new(coords.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        links.new(texture.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 1.0
    plane.data.materials.append(material)
    place_in(plane, "Staging")
    return plane


underlay_path = os.environ.get("DMH_UNDERLAY")
if underlay_path:
    if add_underlay(underlay_path, floor):
        print(f"[dollhouse] underlay       {os.path.basename(underlay_path)}")
        # The floor plates would hide it, and the cut walls are what we are
        # checking, so drop the plates for the comparison.
        for obj in list(bpy.context.scene.objects):
            if obj.name.startswith("floor-"):
                obj.hide_render = True

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
collection("Staging").objects.link(camera)

# Steeper than the first attempt so full-height walls don't hide the rooms
# behind them.
if os.environ.get("DMH_TOPVIEW") == "1":
    # Straight down, framing the whole drawing rather than the building, so the
    # model and the source line up in the same picture.
    camera_data.ortho_scale = span * 1.9
    camera.location = (centre.x, centre.y, span * 3.0)
    camera.rotation_euler = (0.0, 0.0, 0.0)
else:
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
collection("Staging").objects.link(sun)
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
# DMH_WALLS_ONLY=1: hide every render object except the wall bodies, for
# unambiguous attribution of cap-level artifacts. Must run BEFORE the
# render call below — appended-at-EOF diagnostics execute after the PNG is
# already written and silently do nothing.
if os.environ.get("DMH_WALLS_ONLY") == "1":
    for _obj in bpy.context.scene.objects:
        if _obj.type == "MESH" and not _obj.name.startswith("wall-0"):
            _obj.hide_render = True

# A white ground plane under the model. Rainer reported "missing" walls at
# the Büro — probed the merged mesh: all three walls EXIST (26-33 vertices
# on each segment); their brightly lit exterior faces simply vanish into
# the equally bright backdrop. The boss-reference renders solve this with a
# soft drop shadow around the house — same trick here: the plane catches
# the sun shadow, so white walls read against shadowed ground, not void.
if os.environ.get("DMH_NO_GROUND") != "1":
    ground_size = max(20.0, span * 4.0)
    ground_mesh = bpy.data.meshes.new("ground-mesh")
    half = ground_size / 2
    ground_mesh.from_pydata(
        [(centre.x - half, centre.y - half, -0.02),
         (centre.x + half, centre.y - half, -0.02),
         (centre.x + half, centre.y + half, -0.02),
         (centre.x - half, centre.y + half, -0.02)], [], [[0, 1, 2, 3]])
    ground_mesh.update()
    ground = bpy.data.objects.new("ground", ground_mesh)
    collection("Staging").objects.link(ground)
    ground.data.materials.append(flat("ground-white", (0.92, 0.92, 0.92), roughness=1.0))

scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.abspath(out_path)


print(f"[dollhouse] floor           {floor['name']}")
print(f"[dollhouse] rooms           {len(floor['rooms'])}")
print(f"[dollhouse] walls           {len(floor['walls'])} at {wall_height}mm")
print(f"[dollhouse] openings cut    {cut_count}")
print(f"[dollhouse] walls sliced    {sliced_walls} by the tilted plane "
      f"({CUT_HEIGHT_FRONT_MM}mm front -> {CUT_HEIGHT_BACK_MM}mm back)")
print(f"[dollhouse] cut-exempt      {exempt_features} frames, glazing and door leaves")
print(f"[dollhouse] built in-scene  {built_procedurally} (showers, counters, panels)")
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

# --------------------------------------------- depth + edge passes (Stage 5)
# The ComfyUI polish pass needs a true-geometry depth map (depth ControlNet)
# and a clean edge map. The 5.0 compositor File Output node ignores
# per-item PNG formats headless and only emits one multilayer EXR, so the
# compositor route was abandoned (verified on a minimal graph). Instead: a
# SECOND cheap render with every material overridden by a camera-depth
# emission shader (no lights involved, few samples), then a numpy Sobel on
# that depth for the edge map. Written as <out>-depth.png / <out>-edge.png.
# DMH_NO_PASSES=1 skips.
if os.environ.get("DMH_NO_PASSES") != "1":
    base = os.path.splitext(os.path.abspath(out_path))[0]

    depth_mat = bpy.data.materials.new("depth-emission")
    depth_mat.use_nodes = True
    nodes = depth_mat.node_tree.nodes
    nodes.clear()
    cam_data = nodes.new("ShaderNodeCameraData")
    map_range = nodes.new("ShaderNodeMapRange")
    # Normalize raw view depth into 0..1 with numpy afterwards; here just
    # scale into a safe sub-1 band so the PNG doesn't clip: the camera sits
    # about 2.2 spans from the far corner.
    map_range.inputs["From Min"].default_value = 0.0
    map_range.inputs["From Max"].default_value = span * 3.0
    map_range.inputs["To Min"].default_value = 1.0   # near = bright
    map_range.inputs["To Max"].default_value = 0.0
    emission = nodes.new("ShaderNodeEmission")
    output = nodes.new("ShaderNodeOutputMaterial")
    links = depth_mat.node_tree.links
    links.new(cam_data.outputs["View Z Depth"], map_range.inputs["Value"])
    links.new(map_range.outputs["Result"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    overridden = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        overridden.append((obj, list(obj.data.materials)))
        obj.data.materials.clear()
        obj.data.materials.append(depth_mat)

    world = bpy.context.scene.world
    old_world_nodes = world.use_nodes if world else None
    if world:
        world.use_nodes = False
        world.color = (0.0, 0.0, 0.0)
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.0
    try:
        scene.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    scene.render.filepath = base + "-depth.png"
    bpy.ops.render.render(write_still=True)

    # Restore is unnecessary (the process exits) but cheap and keeps any
    # later in-process diagnostics honest.
    for obj, mats in overridden:
        obj.data.materials.clear()
        for m in mats:
            obj.data.materials.append(m)
    if world and old_world_nodes is not None:
        world.use_nodes = old_world_nodes

    try:
        import numpy as np
        img = bpy.data.images.load(base + "-depth.png")
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        grey = px[:, :, 0]
        # The raw map only spans a narrow band of the safe 0..1 scale.
        # Stretch the FOREGROUND (anything that isn't the flat background
        # value) to full range — ControlNet depth wants full-contrast
        # relative depth, and the Sobel below inherits the contrast.
        background = grey[0, 0]
        fg = np.abs(grey - background) > 0.02
        # Low-sample dither speckle survives any threshold as isolated
        # pixels; a single erosion pass keeps only pixels with a foreground
        # neighbourhood, then one dilation restores the true silhouette.
        core = fg.copy()
        core[1:, :] &= fg[:-1, :]; core[:-1, :] &= fg[1:, :]
        core[:, 1:] &= fg[:, :-1]; core[:, :-1] &= fg[:, 1:]
        grown = core.copy()
        grown[1:, :] |= core[:-1, :]; grown[:-1, :] |= core[1:, :]
        grown[:, 1:] |= core[:, :-1]; grown[:, :-1] |= core[:, 1:]
        fg = grown
        if fg.any():
            lo = np.percentile(grey[fg], 1.0)
            hi = np.percentile(grey[fg], 99.0)
            if hi > lo:
                grey = np.clip((grey - lo) / (hi - lo), 0.0, 1.0)
                grey[~fg] = 0.0
        px[:, :, 0] = px[:, :, 1] = px[:, :, 2] = grey
        img.pixels = px.ravel().tolist()
        img.filepath_raw = base + "-depth.png"
        img.file_format = "PNG"
        img.save()
        gx = np.zeros_like(grey); gy = np.zeros_like(grey)
        gx[:, 1:-1] = grey[:, 2:] - grey[:, :-2]
        gy[1:-1, :] = grey[2:, :] - grey[:-2, :]
        mag = np.sqrt(gx ** 2 + gy ** 2)
        top = np.percentile(mag, 99.5) or 1.0
        mag = np.clip(mag / top, 0.0, 1.0)
        out = np.zeros((h, w, 4), dtype=np.float32)
        out[:, :, 0] = out[:, :, 1] = out[:, :, 2] = mag
        out[:, :, 3] = 1.0
        img.pixels = out.ravel().tolist()
        img.filepath_raw = base + "-edge.png"
        img.file_format = "PNG"
        img.save()
        print(f"[dollhouse] passes          {base}-depth.png / -edge.png")
    except Exception as error:  # noqa: BLE001
        print(f"[dollhouse] edge pass FAILED: {error}")

# ------------------------------------------------------------ image manifest
# Every render leaves a <out>.manifest.json next to it: what plan, which
# style and finish set (with the RESOLVED palette values), which files
# belong together, and a composed description. This is the record the
# searchable catalog ingests (masterplan Phase 5) and the recipe the
# ComfyUI batch runner reads to generate further colour-palette variants
# automatically — Rainer's request 2026-08-11.
def _rgb255(rgb):
    return [round(c * 255) for c in rgb[:3]]

finish_name = os.environ.get("DMH_FINISH", "modern-a")
kitchen_rgb = _rgb255(FINISHES[FINISH["kitchen"]][0])
sofa_rgb = _rgb255(FINISHES[FINISH["sofa"]][0])
manifest = {
    "schema": "dmh-render-manifest-v1",
    "created": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    "plan_source": plan.get("source"),
    "source_geometry_hash": plan.get("source_geometry_hash"),
    "furniture_style": plan.get("style"),
    "finish_set": finish_name,
    "palette": {
        "wall_rgb": _rgb255(FINISH["wall"]),
        "floor": "wood" if not FINISH["floor_tint"] else "wood-tinted",
        "floor_tint_rgb": (_rgb255(FINISH["floor_tint"])
                           if FINISH["floor_tint"] else None),
        "floor_tint_factor": FINISH["floor_tint_factor"],
        "kitchen_finish": FINISH["kitchen"],
        "kitchen_rgb": kitchen_rgb,
        "upholstery_finish": FINISH["sofa"],
        "upholstery_rgb": sofa_rgb,
    },
    "image_type": ("plan_overlay" if os.environ.get("DMH_TOPVIEW") == "1"
                   else "interior_dollhouse"),
    "files": {
        "color": os.path.basename(out_path),
        "depth": (os.path.basename(os.path.splitext(out_path)[0] + "-depth.png")
                  if os.environ.get("DMH_NO_PASSES") != "1" else None),
        "edge": (os.path.basename(os.path.splitext(out_path)[0] + "-edge.png")
                 if os.environ.get("DMH_NO_PASSES") != "1" else None),
    },
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "furniture_count": placed,
    "description": (
        f"{plan.get('style', 'modern')} interior, finish {finish_name}: "
        f"{'dark-tinted' if FINISH['floor_tint'] else 'light oak'} wood floor, "
        f"{FINISH['kitchen'].replace('-', ' ')} kitchen fronts, "
        f"{FINISH['sofa'].replace('-', ' ')} upholstery, "
        f"wall tone RGB {tuple(_rgb255(FINISH['wall']))}"
    ),
    "polish": None,  # filled in by the ComfyUI runner when it polishes this image
}
with open(os.path.splitext(os.path.abspath(out_path))[0] + ".manifest.json",
          "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=1)
print(f"[dollhouse] manifest        {os.path.basename(out_path)}.manifest.json")

# Scene inventory, largest first. Three root-cause guesses at an oversized
# object all failed to change the image, which meant the thing was not on the
# path being guessed about. Measuring names it in one run.
if os.environ.get("DMH_INVENTORY") == "1":
    sizes = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        lo = [math.inf] * 3
        hi = [-math.inf] * 3
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])
        extent = [round(hi[a] - lo[a], 2) for a in range(3)]
        collections = ",".join(c.name for c in obj.users_collection)
        sizes.append((max(extent), obj.name, extent, collections, obj.hide_render))
    sizes.sort(reverse=True)
    for longest, name, extent, collections, hidden in sizes[:14]:
        print(f"[inventory] {longest:9.2f}m {name[:38]:38} {extent} "
              f"[{collections}]{' HIDDEN' if hidden else ''}")

print(f"[dollhouse] wrote           {scene.render.filepath}")

# ---------------------------------------------------------------- probe
# DMH_DUMP_AT="x_mm,y_mm" prints every render-visible object whose XY
# bounding box contains that point, just before rendering. Diagnostic only.
if os.environ.get("DMH_DUMP_AT"):
    qx, qy = [float(v) * MM for v in os.environ["DMH_DUMP_AT"].split(",")]
    print(f"[probe] objects covering ({qx:.2f}, {qy:.2f}) m:")
    import mathutils
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        lox = min(c.x for c in corners); hix = max(c.x for c in corners)
        loy = min(c.y for c in corners); hiy = max(c.y for c in corners)
        loz = min(c.z for c in corners); hiz = max(c.z for c in corners)
        if lox - 0.05 <= qx <= hix + 0.05 and loy - 0.05 <= qy <= hiy + 0.05:
            mat = obj.data.materials[0].name if obj.data.materials else "none"
            print(f"[probe]   {obj.name:32} z {loz:.2f}..{hiz:.2f}  mat={mat}")

# DMH_DUMP_TALL=<z_m> lists every render-visible mesh whose top exceeds z_m.
if os.environ.get("DMH_DUMP_TALL"):
    limit = float(os.environ["DMH_DUMP_TALL"])
    import mathutils
    print(f"[tall] objects reaching above {limit} m:")
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        hiz = max(c.z for c in corners)
        if hiz > limit:
            lox = min(c.x for c in corners); hix = max(c.x for c in corners)
            loy = min(c.y for c in corners); hiy = max(c.y for c in corners)
            mat = obj.data.materials[0].name if obj.data.materials else "none"
            print(f"[tall]   {obj.name:32} top {hiz:.2f}  xy ({lox:.1f}..{hix:.1f}, {loy:.1f}..{hiy:.1f})  mat={mat}")
# DMH_PROBE_SEGMENT="x1,y1,x2,y2;..." (mm): counts merged-wall vertices
# within 300mm of each segment, to tell "wall lost in boolean" apart from
# "wall present but hard to see". Runs post-render, print-only.
if os.environ.get("DMH_PROBE_SEGMENT"):
    merged_obj = bpy.context.scene.objects.get("wall-0")
    if merged_obj:
        mesh = merged_obj.data
        for spec in os.environ["DMH_PROBE_SEGMENT"].split(";"):
            x1, y1, x2, y2 = [float(v) * MM for v in spec.split(",")]
            ux, uy = x2 - x1, y2 - y1
            seg_len_sq = ux * ux + uy * uy or 1.0
            count = 0
            for vertex in mesh.vertices:
                world = merged_obj.matrix_world @ vertex.co
                wx, wy = world.x, world.y
                t = max(0.0, min(1.0, ((wx - x1) * ux + (wy - y1) * uy) / seg_len_sq))
                px, py = x1 + t * ux, y1 + t * uy
                if ((wx - px) ** 2 + (wy - py) ** 2) ** 0.5 <= 0.3:
                    count += 1
            print(f"[seg-probe] ({spec}): {count} vertices within 300mm")

# DMH_SAVE_BLEND=<path>: save the fully-built scene as a real .blend file
# for interactive inspection — Rainer orbiting it himself in Blender's own
# viewport, real lighting, real navigation, beats any more scripted camera
# guesses on this session's evidence.
if os.environ.get("DMH_SAVE_BLEND"):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.environ["DMH_SAVE_BLEND"]))
    print(f"[dollhouse] saved .blend    {os.environ['DMH_SAVE_BLEND']}")
