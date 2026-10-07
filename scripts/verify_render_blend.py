"""Rainer's rules, checked against the BUILT SCENE instead of the log.

Why this exists: `verify_render.py` checked the rules by reading lines the
renderer prints about itself. On 2026-08-17 that let a missing Treppenloch
pass twice -- the renderer booleaned the floor slab, the boolean silently cut
nothing, the log said "cut through 5 floor slabs", and the check believed it.
Rainer had to say "still no treppenloch" after being told it was done, twice.

A rule that trusts the thing it is checking is not a rule. These read the
.blend.

Usage:
  blender --background --python scripts/verify_render_blend.py -- \
      <scene.blend> <plan.json> [--floor floor-1]

Exit code 0 = all checks passed, 1 = at least one failed.
"""
import json
import re
import math
import sys

import bpy
import mathutils

MM = 0.001


def argv():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("usage: ... -- <scene.blend> <plan.json> [--floor <id>]")
    floor_id = None
    if "--floor" in args:
        floor_id = args[args.index("--floor") + 1]
    return args[0], args[1], floor_id


def world_box(obj):
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    return ([min(c[i] for c in corners) for i in range(3)],
            [max(c[i] for c in corners) for i in range(3)])


def meshes(prefix):
    return [o for o in bpy.data.objects
            if o.type == "MESH" and o.name.startswith(prefix)
            and len(o.data.vertices) and not o.hide_render]


def check_treppenloch(plan, floor, is_lowest):
    """R3. Nothing horizontal may seal the stair core on a storey above the
    flight -- not a floor slab and not the GROUND PLANE.

    The ground plane sits 20mm under the floor and sealed the Loch even after
    the slabs were opened: you looked through the opening at a flat white
    plane (Rainer, 2026-08-18). It is checked here with the slabs.

    Tested FACE BY FACE, deliberately. A bounding-box test cannot see a hole
    -- the four strips of an opened plane still have the bbox of the whole
    plane -- and a bbox test is exactly what missed this the first time.
    """
    core = plan.get("shared_stair_core") or {}
    polygon = core.get("polygon_mm") or []
    if is_lowest or len(polygon) < 3:
        return []
    x0, x1 = min(p[0] for p in polygon) * MM, max(p[0] for p in polygon) * MM
    y0, y1 = min(p[1] for p in polygon) * MM, max(p[1] for p in polygon) * MM
    occluders = [o for o in bpy.data.objects
                 if o.type == "MESH" and len(o.data.vertices) and not o.hide_render
                 and (o.name.startswith("floor-") or o.name == "ground")]
    covered = []
    for obj in occluders:
        for face in obj.data.polygons:
            if abs(face.normal.z) < 0.9:
                continue
            corners = [obj.matrix_world @ obj.data.vertices[v].co for v in face.vertices]
            lo = [min(c[i] for c in corners) for i in range(2)]
            hi = [max(c[i] for c in corners) for i in range(2)]
            # Strict overlap, not touching: a strip that ENDS on the hole's
            # edge is correct, not a covering.
            eps = 1e-4
            if lo[0] < x1 - eps and hi[0] > x0 + eps                     and lo[1] < y1 - eps and hi[1] > y0 + eps:
                covered.append(f"{obj.name} face x={lo[0]:.2f}..{hi[0]:.2f} "
                               f"y={lo[1]:.2f}..{hi[1]:.2f}")
                break
    if covered:
        return [f"{len(covered)} surface(s) seal the Treppenloch: " + "; ".join(covered[:3])]
    return []


def check_stair_built(plan, is_lowest):
    """R2. A plan carrying a stair core must produce steps, and they must
    stand on the right side of this storey's floor."""
    core = plan.get("shared_stair_core") or {}
    if not core.get("polygon_mm"):
        return []
    steps = meshes("stair-step-")
    if not steps:
        return ["plan carries shared_stair_core but the scene has no stair steps"]
    # Measured against THIS STOREY'S floor, not world zero. Once the upper
    # storey was raised to its real elevation (2620mm) the old world-zero
    # test failed a perfectly good scene: the stair descends 2450mm below the
    # storey floor, which is 170mm ABOVE world zero. A check that assumes the
    # storey sits on the ground stops being a check the moment the house is
    # assembled.
    slabs = meshes("floor-")
    storey_floor = max((world_box(o)[1][2] for o in slabs), default=0.0)
    tops = [world_box(s)[1][2] for s in steps]
    bases = [world_box(s)[0][2] for s in steps]
    if is_lowest and max(tops) <= storey_floor + 0.01:
        return ["stair steps do not rise above this floor"]
    if not is_lowest and min(bases) > storey_floor - 0.5:
        return [f"stair on the upper storey does not descend through the Loch "
                f"(lowest step {min(bases) * 1000:.0f}mm vs floor "
                f"{storey_floor * 1000:.0f}mm)"]
    return []


def check_gelaender(plan):
    """R2. A stair needs a Gelaender; an open Treppenloch needs one round it."""
    core = plan.get("shared_stair_core") or {}
    if not core.get("polygon_mm"):
        return []
    # "stair-handlauf" is the wall-mounted case: a flight walled on both flanks
    # gets a handrail instead of a balustrade. It counts.
    if meshes("stair-rail") or meshes("loch-rail") or meshes("stair-handlauf"):
        return []
    return ["stair built with no Gelaender anywhere in the scene"]


def _xy_quad(obj):
    """This object's footprint as an axis-aligned quad in world XY."""
    lo, hi = world_box(obj)
    return [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]


def _tread_polygon(obj):
    """The tread's own outline in world XY, not its bounding box.

    A bounding box cannot tell a tapered winder from a bow tie: the bow-tie
    treads that started this rule (stair-step-7 and -11 on onehalfstorey_029,
    2026-08-23) measured 1000 x 1000mm exactly BECAUSE their bbox was the whole
    turn. The lowest horizontal face is the tread's real shape.
    """
    faces = [f for f in obj.data.polygons if f.normal.z > 0.9]
    if not faces:
        return _xy_quad(obj)
    face = max(faces, key=lambda f: f.area)
    return [tuple((obj.matrix_world @ obj.data.vertices[v].co)[:2]) for v in face.vertices]


def _polygon_area(poly):
    if len(poly) < 3:
        return 0.0
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
                   - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2.0


def _convex_clip(subject, clip):
    """`subject` clipped to the convex polygon `clip` (Sutherland-Hodgman).

    Returns the intersection polygon, so a caller can measure it in whatever
    direction matters -- area alone cannot tell a rail lying ACROSS the exit
    from one running ALONGSIDE it.
    """
    def signed_area(poly):
        return sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
                   - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly))) / 2.0

    if len(subject) < 3 or len(clip) < 3:
        return []
    if signed_area(clip) < 0:
        clip = clip[::-1]
    output = list(subject)
    for i in range(len(clip)):
        ax, ay = clip[i]
        bx, by = clip[(i + 1) % len(clip)]
        if not output:
            return []
        eingang, output = output, []
        for j in range(len(eingang)):
            cur = eingang[j]
            prev = eingang[j - 1]
            def innen(p):
                return (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) >= -1e-12
            def schnitt(p, q):
                x1, y1 = p
                x2, y2 = q
                d = ((bx - ax) * (y1 - y2) - (by - ay) * (x1 - x2))
                if abs(d) < 1e-15:
                    return q
                s = ((bx - ax) * (y1 - ay) - (by - ay) * (x1 - ax)) / d
                return (x1 + s * (x2 - x1), y1 + s * (y2 - y1))
            if innen(cur):
                if not innen(prev):
                    output.append(schnitt(prev, cur))
                output.append(cur)
            elif innen(prev):
                output.append(schnitt(prev, cur))
    return output


def _blockierte_breite(zone, hindernis, nx, ny, breite):
    """Welcher Anteil der Stufenbreite steht wirklich zu?

    Beruehrung allein sagt nichts. Am 2026-08-28 fiel `onehalfstorey_020`
    durch, weil das SEITLICHE Gelaender der Treppe mit seinen letzten 45mm in
    die Zone ragte -- 30mm einer 1000mm breiten Stufe, also 3 %. Genau dieses
    Gelaender haelt man beim Aussteigen fest. Der Fall, fuer den die Regel
    gebaut wurde (onehalfstorey_029), lief quer ueber die volle Breite.

    Gemessen wird die Ausdehnung der Schnittflaeche QUER zur Gehrichtung,
    geteilt durch die Stufenbreite.
    """
    stueck = _convex_clip(hindernis, zone)
    if len(stueck) < 3 or breite <= 1e-9:
        return 0.0
    quer = [p[0] * nx + p[1] * ny for p in stueck]
    return (max(quer) - min(quer)) / breite


def _convex_overlap_area(subject, clip):
    """Area of subject clipped to the convex polygon `clip` (Sutherland-Hodgman).

    Treads are convex by construction (a quad between two riser lines), so this
    is exact for what it is used on.
    """
    def signed_area(poly):
        return sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
                   - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly))) / 2.0

    if len(subject) < 3 or len(clip) < 3:
        return 0.0
    if signed_area(clip) < 0:
        clip = clip[::-1]
    output = list(subject)
    for i in range(len(clip)):
        ax, ay = clip[i]
        bx, by = clip[(i + 1) % len(clip)]
        if not output:
            return 0.0
        current, output = output, []
        for index, point in enumerate(current):
            previous = current[index - 1]
            side_p = (bx - ax) * (point[1] - ay) - (by - ay) * (point[0] - ax)
            side_q = (bx - ax) * (previous[1] - ay) - (by - ay) * (previous[0] - ax)
            if (side_p >= 0) != (side_q >= 0):
                span = side_q - side_p
                if abs(span) > 1e-12:
                    t = side_q / span
                    output.append((previous[0] + (point[0] - previous[0]) * t,
                                   previous[1] + (point[1] - previous[1]) * t))
            if side_p >= 0:
                output.append(point)
    return abs(signed_area(output)) if len(output) >= 3 else 0.0


def _separated(a, b):
    """Separating-axis test for two convex polygons: True = no overlap."""
    for poly in (a, b):
        for i in range(len(poly)):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % len(poly)]
            nx, ny = -(by - ay), bx - ax
            length = math.hypot(nx, ny)
            if length < 1e-12:
                continue
            nx, ny = nx / length, ny / length
            pa = [p[0] * nx + p[1] * ny for p in a]
            pb = [p[0] * nx + p[1] * ny for p in b]
            if min(pa) > max(pb) + 1e-9 or min(pb) > max(pa) + 1e-9:
                return True
    return False


def check_stair_access(plan, is_lowest):
    """R9. A stair you can actually get off, and treads that are treads.

    Rainer, 2026-08-23, on onehalfstorey_029's upper floor: "your stairs are
    still shit" and "there is a rail blocking the stairs". Both were true and
    every gate passed:

      - `loch-rail-west` was built along the FULL west edge of the Treppenloch
        (x 9.25, y 3.844..6.116), standing straight across the top of the
        flight. R2_gelaender only asked whether a Gelaender EXISTS.
      - `stair-step-7` and `stair-step-11` measured 1000 x 1000mm each: the
        treads that straddled the two 90-degree vertices came out
        self-intersecting and swallowed their neighbours. Nothing measured a
        tread against the tread next to it.

    Three clauses, all measured in the scene:
      a) no railing stands in the arrival zone ahead of the top tread,
      b) the top tread arrives level with this storey's floor,
      c) no two treads overlap in plan.
    """
    core = plan.get("shared_stair_core") or {}
    if not core.get("polygon_mm"):
        return []
    steps = meshes("stair-step-") + meshes("stair-podest-")
    if not steps:
        return []                      # R2_stair_built owns "there is no stair"
    failures = []
    steps = sorted(steps, key=lambda o: world_box(o)[1][2])

    # --- c) treads may not overlap one another -------------------------
    polygons = [(o.name, _tread_polygon(o)) for o in steps]
    for i in range(len(polygons)):
        name_a, poly_a = polygons[i]
        for j in range(i + 1, len(polygons)):
            name_b, poly_b = polygons[j]
            if _separated(poly_a, poly_b):
                continue
            overlap = _convex_overlap_area(poly_a, poly_b)
            smaller = min(_polygon_area(poly_a), _polygon_area(poly_b)) or 1e-9
            if overlap > 0.10 * smaller:
                failures.append(
                    f"{name_a} and {name_b} overlap in plan by "
                    f"{overlap / smaller * 100:.0f}% of the smaller tread "
                    f"({overlap:.3f} m2) -- that is not a flight of stairs")

    if is_lowest:
        # The lowest storey's flight is deliberately truncated at the dollhouse
        # cut plane, so it has no arrival and no top tread to reach.
        return failures

    top = steps[-1]
    top_lo, top_hi = world_box(top)

    # --- b) the top tread arrives level with the floor -----------------
    slabs = meshes("floor-")
    storey_floor = max((world_box(o)[1][2] for o in slabs), default=None)
    if storey_floor is not None:
        # The slab is 220mm thick and its walking face is its own top; rooms
        # whose polygon winds the other way put that face 220mm lower. Both are
        # a level arrival, a flight that stops half a storey down is not.
        if not (storey_floor - 0.24 <= top_hi[2] <= storey_floor + 0.02):
            failures.append(
                f"top tread {top.name} finishes at {top_hi[2] * 1000:.0f}mm but this "
                f"storey's floor is at {storey_floor * 1000:.0f}mm -- you cannot "
                f"step off the stair onto the floor")

    # --- a) nothing may stand in the way of the Austritt ---------------
    if len(steps) >= 2:
        prev_lo, prev_hi = world_box(steps[-2])
        cx, cy = (top_lo[0] + top_hi[0]) / 2, (top_lo[1] + top_hi[1]) / 2
        px, py = (prev_lo[0] + prev_hi[0]) / 2, (prev_lo[1] + prev_hi[1]) / 2
        dx, dy = cx - px, cy - py
        length = math.hypot(dx, dy)
        if length > 1e-6:
            ux, uy = dx / length, dy / length
            nx, ny = -uy, ux
            reach = 0.9
            span = max(top.dimensions.x, top.dimensions.y) / 2.0
            zone = [(cx + ux * t + nx * s, cy + uy * t + ny * s)
                    for t, s in ((0.10, -span), (reach, -span), (reach, span), (0.10, span))]
            # Beruehrung allein ist kein Hindernis. Gemessen wird, wie viel
            # der Stufenbreite zusteht: ein Gelaender QUER ueber den Austritt
            # nimmt sie fast ganz, das seitliche Gelaender der Treppe streift
            # sie mit dem Endpfosten. 25 % ist die Grenze -- darunter kommt man
            # heraus, darueber nicht.
            SPERRE = 0.25
            breite = 2.0 * span
            for rail in meshes("loch-rail"):
                anteil = _blockierte_breite(zone, _xy_quad(rail), nx, ny, breite)
                if anteil > SPERRE:
                    lo, hi = world_box(rail)
                    failures.append(
                        f"{rail.name} (x {lo[0]:.2f}..{hi[0]:.2f}, y {lo[1]:.2f}..{hi[1]:.2f}) "
                        f"blocks {anteil * 100:.0f}% of the arrival width of {top.name} "
                        f"-- the balustrade is built across the stair exit")
    return failures


def check_symbol_sizes(plan, floor):
    """R0. Every placed piece measures its symbol, in the scene."""
    wanted = {}
    for placement in floor.get("placements", []):
        bbox = placement.get("target_bbox_mm") or {}
        if bbox.get("width_mm") and placement.get("mesh_path"):
            wanted[placement["asset_id"]] = bbox
    failures = []
    for asset_id, bbox in wanted.items():
        # Two ways this check was wrong before it was right, both recorded so
        # they don't come back:
        #   - it unioned every INSTANCE of an asset, so three wardrobes 1070
        #     wide standing apart measured 3170;
        #   - it used the WORLD bounding box, which grows when an object is
        #     rotated: a 610mm chair at 45 degrees measured 863.
        # So: one instance at a time, and obj.dimensions (local, scaled, not
        # rotation-inflated).
        pattern = re.compile(rf"^{re.escape(asset_id)}-(\d+)(?:-|$)")
        instances = {}
        for obj in bpy.data.objects:
            match = pattern.match(obj.name)
            if obj.type != "MESH" or not match or not len(obj.data.vertices):
                continue
            instances.setdefault(match.group(1), []).append(obj)
        for index, parts in sorted(instances.items()):
            # The body of the piece, not its trim: largest footprint wins.
            body = max(parts, key=lambda o: o.dimensions.x * o.dimensions.y)
            # Per-INSTANCE expectation where the renderer stamped one:
            # `wanted` is keyed by asset_id, so three wardrobes with three
            # different measured footprints used to be checked against
            # whichever placement happened to come last (onehalfstorey_029,
            # 2026-08-22). The stamp names THIS instance's own symbol.
            if body.get("symbol_w_mm"):
                want = [float(body["symbol_w_mm"]), float(body.get("symbol_d_mm") or 0)]
            else:
                want = [bbox.get("width_mm") or 0, bbox.get("depth_mm") or 0]
            got = [body.dimensions.x / MM, body.dimensions.y / MM]
            if abs(max(got) - max(want)) > 3 or abs(min(got) - min(want)) > 3:
                failures.append(f"{asset_id}-{index}: footprint {got[0]:.0f}x{got[1]:.0f} "
                                f"vs symbol {want[0]:.0f}x{want[1]:.0f}")
    return failures


def check_opening_heights(plan, floor):
    """R8. Opening features stand at their intended heights, measured in
    the scene.

    On 2026-08-22 the dollhouse cutaway plane sliced 7 of 8 windows and two
    door leaves through the middle on bungalow_039, and every gate passed
    -- Rainer found it by opening the .blend himself ("fesnter sind fast
    ueberall geschnitten"). This is that day's ad-hoc Z-extent probe made
    permanent, with component-specific expectations rather than a naive
    "everything is full-height" (a frame HEAD is only profile-tall, glazing
    is inset, heights clamp to the wall) -- per the Codex-reviewed design
    in plans/pose-contract-slice-1-v1.md.

    Two directions, both needed:
      - every found jamb/leaf/glazing matches SOME expected opening span on
        its wall (catches truncation -- the actual bug class), and
      - every door/window opening HAS its jambs, its leaf or its glazing at
        the expected span (catches features deleted or never built).
    Passages (opening_type "opening") are frameless by design and exempt.
    """
    WALL_HEIGHT_MM = 2400.0   # the renderer's wall_height constant
    GLASS_INSET_M = 0.015     # the renderer's glass_inset
    TOL = 0.03                # 30mm: boolean/profile tolerance
    failures = []
    walls = floor.get("walls") or []
    openings_by_wall = {}
    for opening in floor.get("openings") or []:
        openings_by_wall.setdefault(opening.get("wall_id"), []).append(opening)

    # The renderer raises a whole storey when assembling; expectations are
    # relative to this storey's own base. Anchored on the WALL BODIES'
    # lowest z, not the floor slab: the slab's top sits 220mm ABOVE the
    # wall feet in a standard build (measured on bungalow_039 -- using it
    # shifted every expectation by exactly that and failed a correct
    # scene), while wall bodies stand on the storey base by construction.
    body_pattern = re.compile(r"^wall-\d+(\.\d+)?$")
    bodies = [o for o in bpy.data.objects
              if o.type == "MESH" and len(o.data.vertices) and not o.hide_render
              and body_pattern.match(o.name)]
    base = min((world_box(o)[0][2] for o in bodies), default=0.0)
    if abs(base) < 0.005:
        base = 0.0

    def z_span(obj):
        lo, hi = world_box(obj)
        return lo[2] - base, hi[2] - base

    def near(got, want):
        return abs(got[0] - want[0]) <= TOL and abs(got[1] - want[1]) <= TOL

    for index, wall in enumerate(walls):
        # The renderer names objects by ENUMERATE index over floor["walls"],
        # not by wall["id"] -- map by position. Prefixes end with a literal
        # separator so wall-1 never matches wall-11.
        spans = []
        for opening in openings_by_wall.get(wall.get("id"), []):
            sill = opening.get("sill_height_mm") or 0
            height = opening.get("height_mm") or 0
            available = WALL_HEIGHT_MM - sill
            if available <= 0 or height <= 0:
                continue
            top = sill + min(height, available)
            spans.append((sill * MM, top * MM, opening))

        jambs = meshes(f"wall-{index}-frame-jamb")
        leaves = [o for o in bpy.data.objects
                  if o.type == "MESH" and len(o.data.vertices) and not o.hide_render
                  and (o.name == f"wall-{index}-door"
                       or o.name.startswith(f"wall-{index}-door."))]
        glazing = meshes(f"wall-{index}-glass-") + meshes(f"wall-{index}-mullion-")

        door_spans = [(s, t) for s, t, o in spans if o.get("opening_type") == "door"]
        window_spans = [(s + GLASS_INSET_M, t - GLASS_INSET_M)
                        for s, t, o in spans if o.get("opening_type") == "window"]
        all_spans = [(s, t) for s, t, _ in spans]

        for obj, expected, label in (
                [(o, all_spans, "jamb") for o in jambs]
                + [(o, door_spans, "door leaf") for o in leaves]
                + [(o, window_spans, "glazing") for o in glazing]):
            got = z_span(obj)
            if not any(near(got, want) for want in expected):
                wanted = ", ".join(f"{w[0] * 1000:.0f}-{w[1] * 1000:.0f}" for w in expected) or "none"
                failures.append(
                    f"{obj.name}: {label} spans {got[0] * 1000:.0f}-{got[1] * 1000:.0f}mm, "
                    f"matches no opening on this wall (expected: {wanted}mm)")

        for s, t, opening in spans:
            kind = opening.get("opening_type")
            if kind not in ("door", "window"):
                continue
            oid = opening.get("id")
            if sum(1 for o in jambs if near(z_span(o), (s, t))) < 2:
                failures.append(f"{wall.get('id')}: {kind} {oid} is missing its jambs "
                                f"at {s * 1000:.0f}-{t * 1000:.0f}mm")
            if kind == "door" and not any(near(z_span(o), (s, t)) for o in leaves):
                failures.append(f"{wall.get('id')}: door {oid} has no leaf "
                                f"at {s * 1000:.0f}-{t * 1000:.0f}mm")
            if kind == "window":
                want = (s + GLASS_INSET_M, t - GLASS_INSET_M)
                if not any(near(z_span(o), want) for o in glazing):
                    failures.append(f"{wall.get('id')}: window {oid} has no glazing "
                                    f"at {want[0] * 1000:.0f}-{want[1] * 1000:.0f}mm")
    return failures


def main():
    blend_path, plan_path, floor_id = argv()
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    with open(plan_path, encoding="utf-8-sig") as handle:
        plan = json.load(handle)

    floors = plan.get("floors") or []
    scene_floor = bpy.context.scene.get("floor_id") or (floor_id or "")
    floor = next((f for f in floors if f.get("id") == scene_floor), floors[0] if floors else {})
    is_lowest = bool(floors) and floor is floors[0]
    print(f"[verify-blend] {blend_path}")
    print(f"[verify-blend] storey {floor.get('id')} "
          f"({'lowest' if is_lowest else 'above the flight'})")

    checks = [
        ("R0_symbol_sizes", check_symbol_sizes(plan, floor)),
        ("R2_stair_built", check_stair_built(plan, is_lowest)),
        ("R2_gelaender", check_gelaender(plan)),
        ("R3_treppenloch", check_treppenloch(plan, floor, is_lowest)),
        ("R8_opening_heights", check_opening_heights(plan, floor)),
        ("R9_stair_access", check_stair_access(plan, is_lowest)),
    ]
    failed = False
    for name, failures in checks:
        if failures:
            failed = True
            print(f"FAIL {name}")
            for line in failures:
                print(f"  - {line}")
        else:
            print(f"PASS {name}")
    sys.exit(1 if failed else 0)


main()
