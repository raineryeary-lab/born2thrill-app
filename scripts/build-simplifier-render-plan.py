# Build a furnished render plan directly from Simplifier annotations.
#
# WHY THIS EXISTS, AND WHAT IT IS NOT
#
# The approved pipeline is: Simplifier annotations -> canonical JSON -> render.
# Canonical JSON is the single geometry source for anything delivered, and
# scripts/build-furnished-render-plan.mjs is the builder that path uses.
#
# bungalow_040_66 has no canonical document — it is `training_ready`, not
# promoted — and promoting it is the whole generator process, not a step. So
# this script exists to get a PICTURE out of hand-annotated data for review.
# It is a proof path, exactly like scripts/render-furnished-dollhouse.py which
# it feeds:
#
#   * it never writes canonical geometry
#   * it never computes or touches geometry_hash
#   * nothing it produces may be delivered, published or emailed
#
# The output carries `source: "simplifier_annotations_proof"` so an image built
# this way can always be told apart from one built from approved geometry.
#
# WHAT IT DOES
#
# Reads projects/<id>/annotations.json and turns it into the same
# dmh-furnished-render-plan-proof-v1 schema the Blender script already
# consumes:
#
#   rooms      <- annotation polygons, German labels mapped to material kinds
#   walls      <- room polygon edges; an edge shared by two rooms is interior,
#                 an edge belonging to one room is exterior
#   openings   <- door/window/opening elements, matched to their nearest wall
#   placements <- Rainer's hand-placed Ausstattung symbols, which is the whole
#                 point: furniture that was annotated rather than guessed
#
# Usage:
#   python scripts/build-simplifier-render-plan.py <project_id> <style> <out.json>

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SIMPLIFIER = os.path.join(os.path.dirname(REPO), "floorplan-simplifier")
SHORTLIST = os.path.join(REPO, "tmp", "symbol-model-shortlist.json")
PICKS = os.path.join(REPO, "data", "symbol-model-picks.json")
# A placed symbol records type, position and rotation and nothing else — that
# separation is deliberate, so a symbol never carries a size that could drift
# from the catalogue. The footprint therefore has to be looked up.
FOOTPRINTS = os.path.join(SIMPLIFIER, "symbol_footprints.json")

# German room label -> the material kind the renderer understands. Longest and
# most specific first: "Elternbad" must reach `sanitary` on "bad", not
# `sleeping` on "eltern", which is the same precedence bug that once classed a
# bathroom as a bedroom in the Simplifier.
ROOM_KINDS = [
    ("duschbad", "sanitary"), ("kinderbad", "sanitary"), ("elternbad", "sanitary"),
    ("gästebad", "sanitary"), ("gaestebad", "sanitary"), ("tageslichtbad", "sanitary"),
    ("badezimmer", "sanitary"), ("du-wc", "sanitary"), ("dusch", "sanitary"),
    ("bad", "sanitary"), ("gäste-wc", "sanitary"), ("gaeste-wc", "sanitary"),
    ("wc", "sanitary"),
    ("hwr", "service"), ("htr", "service"), ("hauswirtschaft", "service"),
    ("technik", "service"), ("waschküche", "service"),
    ("diele", "circulation"), ("flur", "circulation"), ("windfang", "circulation"),
    ("treppe", "circulation"),
    ("ankleide", "storage"), ("abstell", "storage"), ("speis", "storage"),
    ("keller", "storage"), ("garderobe", "storage"),
    ("küche", "living"), ("kueche", "living"), ("essen", "living"),
    ("wohnen", "living"), ("wohnzimmer", "living"),
    ("schlafen", "sleeping"), ("eltern", "sleeping"), ("kind", "sleeping"),
    ("gast", "sleeping"), ("büro", "sleeping"), ("arbeiten", "sleeping"),
]

# Spaces that are not interior rooms. A carport has no floor finish and no
# furniture, and including it stretches the camera framing over dead ground.
EXCLUDED_ROOMS = ("carport", "garage", "terrasse", "balkon", "loggia")

# Height in mm for each symbol, the dimension a 2D footprint cannot carry, plus
# the finish category the renderer uses when a model has no materials of its
# own. Mount height is the CENTRE of a wall-hung item.
SYMBOL_3D = {
    "badewanne":         {"height": 580,  "type": "bathtub"},
    "eckbadewanne":      {"height": 580,  "type": "bathtub"},
    "dusche":            {"height": 2000, "type": "shower", "build": "shower"},
    "dusche_gross":      {"height": 2000, "type": "shower", "build": "shower"},
    "dusche_klein":      {"height": 2000, "type": "shower", "build": "shower"},
    "wand_wc":           {"height": 400,  "type": "toilet", "mount": 660},
    # mount is the item CENTRE. The resolved Toilet Bowl model is 820mm
    # tall (probed z-range, includes the flush plate), so centre 660 puts
    # its underside at 250mm -- wall-hung with visible air. 200 sat it on
    # the floor (Rainer 2026-08-11); 480 still only left 70mm.
    "waschtisch":        {"height": 200,  "type": "sink",   "mount": 850},
    "doppelwaschtisch":  {"height": 200,  "type": "sink",   "mount": 850},
    "handwaschbecken":   {"height": 200,  "type": "sink",   "mount": 850},
    "badheizkoerper":    {"height": 1200, "type": "radiator", "mount": 900, "build": "radiator"},
    "vorwandinstallation": {"height": 1500, "type": "wall_panel", "depth": 150},
    "kuechenzeile":      {"height": 900,  "type": "counter", "depth": 600},
    "kuecheninsel":      {"height": 900,  "type": "counter", "depth": 900},
    "kuehlschrank":      {"height": 1800, "type": "fridge"},
    "hochschrank_herd":  {"height": 2100, "type": "oven_housing"},
    "kochfeld":          {"height": 50,   "type": "hob",  "mount": 900, "build": "hob"},
    "spuele":            {"height": 200,  "type": "sink", "mount": 880, "build": "hob"},
    "waschmaschine":     {"height": 850,  "type": "washer"},
    "trockner":          {"height": 850,  "type": "washer"},
    "ecksofa":           {"height": 800,  "type": "sofa"},
    "sofa_3sitzer":      {"height": 800,  "type": "sofa"},
    "sofa_2sitzer":      {"height": 800,  "type": "sofa"},
    "sofa_1sitzer":      {"height": 800,  "type": "armchair"},
    "hocker":            {"height": 450,  "type": "stool"},
    "couchtisch":        {"height": 400,  "type": "coffee_table"},
    "lowboard":          {"height": 500,  "type": "sideboard"},
    "sideboard":         {"height": 800,  "type": "sideboard"},
    "fernseher":         {"height": 700,  "type": "tv", "mount": 1100, "build": "tv"},
    "essgruppe_6":       {"height": 750,  "type": "dining_set"},
    "playstation_gruppe": {"height": 750, "type": "dining_set"},
    "doppelbett":        {"height": 500,  "type": "bed"},
    "einzelbett":        {"height": 500,  "type": "bed"},
    "kleiderschrank":    {"height": 2100, "type": "wardrobe"},
    "schrank_60":        {"height": 2100, "type": "wardrobe"},
    "schrank_40":        {"height": 2100, "type": "wardrobe"},
    "abstellschrank":    {"height": 2100, "type": "wardrobe"},
    "schreibtisch":      {"height": 750,  "type": "desk"},
    "schreibtisch_kind": {"height": 720,  "type": "desk"},
    "garderobe":         {"height": 1900, "type": "wardrobe"},
    "schreibtischstuhl": {"height": 1200, "type": "office_chair"},
    "essgruppe_stuhl":   {"height": 844,  "type": "dining_chair"},
    "pflanze":           {"height": 1300, "type": "plant", "build": "plant"},
}

DEFAULT_WALL_THICKNESS_MM = 240
INTERIOR_WALL_THICKNESS_MM = 115


def room_kind(label):
    lowered = (label or "").lower()
    for needle, kind in ROOM_KINDS:
        if needle in lowered:
            return kind
    return "living"


def excluded(label):
    lowered = (label or "").lower()
    return any(needle in lowered for needle in EXCLUDED_ROOMS)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def image_size(project_dir):
    """Pixel size of the preview the annotations were drawn on.

    Normalized y is measured against image HEIGHT, so without the aspect ratio
    every plan comes out squashed along one axis — the same unit mix-up that
    made symbols render 81.5 % too shallow in the annotation UI.
    """
    for name in ("original_preview.png", "room_concept.png"):
        candidate = os.path.join(project_dir, name)
        if not os.path.exists(candidate):
            continue
        with open(candidate, "rb") as handle:
            head = handle.read(33)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            width = int.from_bytes(head[16:20], "big")
            height = int.from_bytes(head[20:24], "big")
            if width and height:
                return width, height
    raise SystemExit("could not read preview image size")


class Frame:
    """Normalized annotation space -> millimetres, y flipped.

    Image y grows downward; a floorplan in 3D wants y growing north, otherwise
    every plan renders mirrored and every door swings the wrong way.
    """

    def __init__(self, scale_metres_per_x_unit, pixel_width, pixel_height):
        self.width_mm = scale_metres_per_x_unit * 1000.0
        self.height_mm = self.width_mm * (pixel_height / float(pixel_width))

    def point(self, position):
        return [round(position["x"] * self.width_mm, 1),
                round((1.0 - position["y"]) * self.height_mm, 1)]

    def xy(self, x, y):
        return self.point({"x": x, "y": y})


def polygon_area(points):
    total = 0.0
    for index, (x, y) in enumerate(points):
        nx, ny = points[(index + 1) % len(points)]
        total += x * ny - nx * y
    return abs(total) / 2.0


def _edges_of(rooms):
    """Every room boundary edge, with the room's centroid so "outward" is known."""
    out = []
    for room in rooms:
        points = room["polygon_mm"]
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            if math.dist(start, end) < 150:
                continue
            out.append({"room": room["id"], "a": list(start), "b": list(end),
                        "centroid": (cx, cy)})
    return out


def _overlap(edge_a, edge_b):
    """Portion of edge_a that faces edge_b, as two points, or None.

    Rooms are annotated as their INNER boundary, so two rooms either side of a
    partition never share an edge — they have parallel edges about a wall
    thickness apart. The first version of this looked for shared edges and
    found none, which is why every one of the 40 walls came out exterior. What
    actually identifies an interior wall is a pair of near-parallel edges,
    close together, whose lengths overlap.
    """
    ax, ay = edge_a["a"]
    bx, by = edge_a["b"]
    length = math.dist((ax, ay), (bx, by))
    if length < 150:
        return None
    ux, uy = (bx - ax) / length, (by - ay) / length

    # Project the other edge onto this one and keep the overlapping stretch.
    ts = []
    for point in (edge_b["a"], edge_b["b"]):
        ts.append((point[0] - ax) * ux + (point[1] - ay) * uy)
    low, high = max(0.0, min(ts)), min(length, max(ts))
    if high - low < 400:
        return None
    return ((ax + ux * low, ay + uy * low), (ax + ux * high, ay + uy * high))


def _perpendicular_gap(edge_a, edge_b):
    ax, ay = edge_a["a"]
    bx, by = edge_a["b"]
    length = math.dist((ax, ay), (bx, by))
    ux, uy = (bx - ax) / length, (by - ay) / length
    nx, ny = -uy, ux
    gaps = [abs((point[0] - ax) * nx + (point[1] - ay) * ny) for point in (edge_b["a"], edge_b["b"])]
    return sum(gaps) / 2.0


# How far apart two room boundaries may be and still be one partition rather
# than two rooms with a cupboard between them. German interior walls run
# 100-150 mm plus plaster; 400 mm is generous without being absurd.
MAX_PARTITION_GAP_MM = 400
PARALLEL_TOLERANCE_DEG = 12


def build_walls(rooms):
    """Interior walls from facing room boundaries, exterior from the rest.

    An interior wall is centred between the two room faces it separates. An
    exterior wall is pushed outward by half its thickness, because the room
    polygon is the inside face and a wall drawn centred on it would eat into
    the room.
    """
    edges = _edges_of(rooms)
    # An edge may face SEVERAL rooms along its length (a long HWR wall with
    # DU-WC on one span and the Flur on another). Exclusive one-shot pairing
    # (`used[j]`) let the first room consume the whole edge; the second
    # room's edge then found no partner and fell through to the exterior
    # branch -- a 240mm 'exterior' wall dead-ending in the middle of the
    # flat, which is exactly the fat junction stub seen on render (task
    # #12). So: an edge may partner once per FACING PAIR; only an edge that
    # never partnered at all becomes exterior. Each room's own edge pulls
    # in its own span, so a shared long edge ends up correctly split into
    # one thin wall per neighbour.
    partnered = [False] * len(edges)
    paired = set()
    # Per-edge list of (t0, t1) intervals along the edge that a pairing
    # actually covered. One pairing used to consume the WHOLE edge, so the
    # stretch of a long edge beyond its partner's overlap silently got NO
    # wall at all — confirmed on bungalow_040_66: the Gast/office east
    # edge paired with the Wohnen west edge over a partial span and the
    # remainder (the missing 'Wand D' Rainer pointed at) vanished.
    covered = [[] for _ in edges]
    walls = []

    def _interval_on(edge, span):
        ax, ay = edge["a"]
        bx, by = edge["b"]
        length = math.dist((ax, ay), (bx, by)) or 1.0
        ux, uy = (bx - ax) / length, (by - ay) / length
        ts = sorted(((p[0] - ax) * ux + (p[1] - ay) * uy) for p in span)
        return (max(0.0, ts[0]), min(length, ts[1]))

    for i, edge in enumerate(edges):
        angle = math.atan2(edge["b"][1] - edge["a"][1], edge["b"][0] - edge["a"][0])
        partner = None
        for j, other in enumerate(edges):
            if j == i or other["room"] == edge["room"] or (i, j) in paired:
                continue
            other_angle = math.atan2(other["b"][1] - other["a"][1], other["b"][0] - other["a"][0])
            difference = abs((angle - other_angle + math.pi / 2) % math.pi - math.pi / 2)
            if difference > math.radians(PARALLEL_TOLERANCE_DEG):
                continue
            gap = _perpendicular_gap(edge, other)
            if gap > MAX_PARTITION_GAP_MM or gap < 20:
                continue
            span = _overlap(edge, other)
            if span is None:
                continue
            if partner is None or gap < partner[0]:
                partner = (gap, j, span)

        if partner is not None:
            gap, j, span = partner
            partnered[i] = partnered[j] = True
            paired.add((i, j))
            paired.add((j, i))
            covered[i].append(_interval_on(edges[i], span))
            covered[j].append(_interval_on(edges[j], span))
            other = edges[j]
            # Centreline sits midway between the two faces.
            ax, ay = edge["a"]
            bx, by = edge["b"]
            length = math.dist((ax, ay), (bx, by))
            nx, ny = -(by - ay) / length, (bx - ax) / length
            towards = (other["a"][0] - ax) * nx + (other["a"][1] - ay) * ny
            shift = (gap / 2.0) * (1 if towards > 0 else -1)
            walls.append({
                "id": f"wall-{len(walls)}",
                "start_mm": [round(span[0][0] + nx * shift, 1), round(span[0][1] + ny * shift, 1)],
                "end_mm": [round(span[1][0] + nx * shift, 1), round(span[1][1] + ny * shift, 1)],
                "thickness_mm": round(gap),
                "wall_type": "interior",
                "rooms": sorted({edge["room"], other["room"]}),
            })

    for i, edge in enumerate(edges):
        ax, ay = edge["a"]
        bx, by = edge["b"]
        length = math.dist((ax, ay), (bx, by))
        # The UNCOVERED stretches of this edge (whole edge when it never
        # paired) each become an exterior wall — a partial pairing must
        # not delete the rest of the wall.
        gaps = []
        cursor = 0.0
        for t0, t1 in sorted(covered[i]):
            if t0 - cursor > 300:
                gaps.append((cursor, t0))
            cursor = max(cursor, t1)
        if length - cursor > 300:
            gaps.append((cursor, length))
        if not gaps:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        # Push away from the room, so the wall sits outside its inner face.
        inward = (edge["centroid"][0] - ax) * nx + (edge["centroid"][1] - ay) * ny
        shift = (DEFAULT_WALL_THICKNESS_MM / 2.0) * (-1 if inward > 0 else 1)
        for t0, t1 in gaps:
            walls.append({
                "id": f"wall-{len(walls)}",
                "start_mm": [round(ax + ux * t0 + nx * shift, 1),
                             round(ay + uy * t0 + ny * shift, 1)],
                "end_mm": [round(ax + ux * t1 + nx * shift, 1),
                           round(ay + uy * t1 + ny * shift, 1)],
                "thickness_mm": DEFAULT_WALL_THICKNESS_MM,
                "wall_type": "exterior",
                "rooms": [edge["room"]],
            })

    return walls


def point_in_polygon(point, polygon, tolerance_mm=300):
    """Inside the polygon, or within tolerance of its boundary — openings sit
    ON a room's edge, so their midpoint can land just outside the polygon."""
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    if inside:
        return True
    for i in range(len(polygon)):
        sx, sy = polygon[i]
        ex, ey = polygon[(i + 1) % len(polygon)]
        length_squared = (ex - sx) ** 2 + (ey - sy) ** 2
        if not length_squared:
            continue
        t = max(0.0, min(1.0, ((x - sx) * (ex - sx) + (y - sy) * (ey - sy)) / length_squared))
        if math.dist(point, (sx + t * (ex - sx), sy + t * (ey - sy))) <= tolerance_mm:
            return True
    return False


def nearest_wall(walls, a, b):
    """The wall an opening belongs to: closest by midpoint, and roughly parallel.

    Angle matters. A door drawn across a corner sits near two walls, and
    attaching it to the perpendicular one puts it through the return.
    """
    midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    best = None
    for wall in walls:
        sx, sy = wall["start_mm"]
        ex, ey = wall["end_mm"]
        wall_angle = math.atan2(ey - sy, ex - sx)
        difference = abs((angle - wall_angle + math.pi / 2) % math.pi - math.pi / 2)
        if difference > math.radians(25):
            continue
        length_squared = (ex - sx) ** 2 + (ey - sy) ** 2
        if not length_squared:
            continue
        t = ((midpoint[0] - sx) * (ex - sx) + (midpoint[1] - sy) * (ey - sy)) / length_squared
        t = max(0.0, min(1.0, t))
        distance = math.dist(midpoint, (sx + t * (ex - sx), sy + t * (ey - sy)))
        if best is None or distance < best[0]:
            best = (distance, wall, t)
    return best


def load_model_picks(style="modern"):
    """Resolved Hub models for each symbol key, with their scale divisor.

    Types come from the assets' own names and sizes were verified by
    scripts/resolve-hub-scales.py, so nothing here is inferred from a
    measurement — which is what went wrong every time today. The old
    size-match shortlist is deliberately NOT consulted: it ranked models
    against a library whose measurements the FBX conversion had corrupted.
    """
    if not os.path.exists(PICKS):
        return {}
    raw = load_json(PICKS).get("picks", {})
    resolved = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        chosen = entry.get(style) or entry.get("modern")
        if not isinstance(chosen, dict) or not chosen.get("path"):
            continue
        resolved[key] = {
            "path": chosen["path"],
            "divisor": chosen.get("divisor", 1.0),
            "size_mm": chosen.get("size_mm"),
            "label": chosen.get("label"),
            "source": "hub_resolved",
        }
    return resolved


# How far a model's real footprint may sit from the annotated one before a box
# serves better. A real model squeezed to a third of its size looks worse than
# a plain box at the right size — the stretched-sofa mistake in reverse.
#
# Crude on purpose. Nobody measures a marketing render; it only has to avoid
# looking obviously wrong.
# 0.45 was slightly too tight: a 400 mm basin against a 600 mm symbol misses by
# 49 % and got replaced by a box, when the real basin would have looked better.
# Nobody measures a marketing render, so err towards the real model.
FOOTPRINT_TOLERANCE = 0.6


def footprint_mismatch(model, footprint):
    """True when the model is too far off the drawn footprint to use."""
    size = model.get("size_mm")
    if not size or not footprint.get("width_mm"):
        return False
    want = sorted([footprint["width_mm"], footprint["depth_mm"]], reverse=True)
    got = sorted(size[:2], reverse=True)
    for a, b in zip(got, want):
        if b <= 0:
            continue
        if abs(a - b) / float(b) > FOOTPRINT_TOLERANCE:
            return True
    return False


def main():
    if len(sys.argv) < 4:
        raise SystemExit("usage: build-simplifier-render-plan.py <project_id> <style> <out.json>")
    project_id, style, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    annotations = load_json(os.path.join(project_dir, "annotations.json"))
    pixel_width, pixel_height = image_size(project_dir)

    floor_scale = annotations.get("floor_scale") or {}
    floors_out = []
    models = load_model_picks(style)
    footprints = load_json(FOOTPRINTS)

    levels = sorted({item.get("floor_level") for item in annotations.get("annotations", [])
                     if item.get("floor_level")})
    for level in levels:
        scale = floor_scale.get(level)
        if not scale:
            raise SystemExit(f"{level} has no calibrated scale — set it in the Simplifier first")
        frame = Frame(scale, pixel_width, pixel_height)

        rooms = []
        excluded_polygons = []
        for item in annotations.get("annotations", []):
            if item.get("floor_level") != level:
                continue
            points = item.get("points") or []
            if len(points) < 3:
                continue
            if excluded(item.get("label")):
                excluded_polygons.append((item.get("label"), [frame.point(p) for p in points]))
                continue
            polygon = [frame.point(p) for p in points]
            rooms.append({
                "id": item.get("id") or f"room-{len(rooms)}",
                "name": item.get("label") or "Raum",
                "kind": room_kind(item.get("label")),
                "polygon_mm": polygon,
                "area_m2": round(polygon_area(polygon) / 1e6, 2),
            })

        walls = build_walls(rooms)

        openings = []
        unmatched = []
        skipped_excluded = []
        for element in annotations.get("elements", []):
            if element.get("floor_level") != level:
                continue
            kind = element.get("type")
            if kind not in ("door", "window", "opening"):
                continue
            points = element.get("points") or []
            if len(points) < 2:
                continue
            a, b = frame.point(points[0]), frame.point(points[1])
            match = nearest_wall(walls, a, b)
            if match is None or match[0] > 1200:
                midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                host = next((label for label, poly in excluded_polygons
                             if point_in_polygon(midpoint, poly)), None)
                if host:
                    skipped_excluded.append((element.get("id"), host))
                else:
                    unmatched.append(element.get("id"))
                continue
            _, wall, t = match

            # Window type is annotated now, so the sill comes from the plan
            # instead of a blanket 900 mm. A bodentiefes Fenster starts at the
            # floor; a Brüstungsfenster does not.
            window_type = element.get("window_type")
            if kind == "window":
                sill = element.get("sill_height_mm")
                if sill is None:
                    sill = 0 if window_type == "bodentief" else 900
                height = 2100 - sill if window_type == "bodentief" else 1350
            else:
                sill, height = 0, 2010

            openings.append({
                "id": element.get("id") or f"opening-{len(openings)}",
                "wall_id": wall["id"],
                "opening_type": kind,
                "position": round(t, 4),
                "width_mm": round(math.dist(a, b), 1),
                "height_mm": height,
                "sill_height_mm": sill,
                "traversable": kind != "window",
                "window_type": window_type,
                "panes": element.get("panes"),
                "swing_side": element.get("swing_side"),
                "hinge_side": element.get("hinge_side"),
                "role": element.get("role"),
                "connects": wall.get("rooms", []),
            })

        placements = []
        skipped = []
        for symbol in annotations.get("symbols", []):
            if symbol.get("floor_level") != level:
                continue
            key = symbol.get("symbol")
            spec = SYMBOL_3D.get(key)
            if not spec:
                skipped.append({"symbol": key, "reason": "no 3D specification"})
                continue

            # Path and rectangle symbols carry BOTH `points` and a centre
            # `position`. The points are the real geometry — a kitchen run is
            # its path, not a dot — so they win. Testing `position` first sent
            # every Kuechenzeile down the stamp branch and lost it.
            points = symbol.get("points") or []
            position = None if points else symbol.get("position")
            if points:
                placements.append({
                    "asset_id": key,
                    "type": spec["type"],
                    "build": "rect" if len(points) > 2 and key == "kuecheninsel" else "path",
                    "points_mm": [frame.point(p) for p in points],
                    # The catalogue depth for this symbol. Falling back to a blanket
                    # 600 built every Vorwandinstallation four times too deep.
                    "depth_mm": symbol.get("depth_mm") or spec.get("depth", 600),
                    "height_mm": spec["height"],
                    "source": "simplifier_annotations_proof",
                })
                continue
            if not position:
                skipped.append({"symbol": key, "reason": "no position"})
                continue

            # A footprint measured on the plan by dragging the symbol's
            # corners beats the catalogue's nominal size. The annotator was
            # looking at the actual drawing; the catalogue is a general figure
            # for that kind of furniture, and using it is what made every piece
            # come out undersized.
            measured = symbol.get("footprint_mm") or {}
            footprint = measured if measured.get("width_mm") else (footprints.get(key) or {})
            if not footprint.get("width_mm"):
                skipped.append({"symbol": key, "reason": "no footprint in the catalogue"})
                continue
            model = models.get(key)
            build = spec.get("build")
            if not model and not build:
                build = "box"

            # The gate exists to stop a wildly wrong model being squeezed into
            # a nominal catalogue footprint. It must never fire against a
            # footprint Rainer measured on the plan: that comparison is between
            # two things that are both correct, and rejecting the model turned
            # every carefully measured symbol into a plain box.
            measured_here = bool(measured.get("width_mm"))
            mismatch = (bool(model) and not measured_here
                        and footprint_mismatch(model, footprint))
            if mismatch and not build:
                # No model worth using and nothing procedural defined, so build
                # it as a plain box at the annotated size.
                build = "box"

            placements.append({
                "asset_id": key,
                "type": spec["type"],
                "mesh_path": model["path"] if model and not mismatch else None,
                "model_source": (model["source"] if model and not mismatch
                                 else "procedural"),
                "model_label": model.get("label") if model else None,
                "scale_divisor": model.get("divisor", 1.0) if model else 1.0,
                # The model's own verified real-world size, from
                # resolve-hub-scales.py. The renderer scales to THIS rather than
                # to the catalogue footprint, so a real 2200 mm dining set stays
                # 2200 mm instead of being squeezed into a nominal 1800.
                "verified_size_mm": model.get("size_mm") if model else None,
                "size_mismatch": mismatch,
                # Measured by dragging the symbol's corners on the plan. When
                # present it OUTRANKS the model's own verified size: Rainer was
                # looking at this drawing, the model's dimensions describe some
                # other piece of furniture.
                "footprint_measured": bool(measured.get("width_mm")),
                "build": build,
                "position_mm": frame.point(position),
                "rotation_deg": symbol.get("rotation_deg", 0),
                "mirrored": bool(symbol.get("mirrored")),
                "target_bbox_mm": {
                    "width_mm": footprint.get("width_mm"),
                    "depth_mm": footprint.get("depth_mm"),
                    "height_mm": spec["height"],
                },
                "height_mm": spec.get("mount", 0),
                # Library models carry their own materials, which is the entire
                # reason to prefer them over generated meshes. Scale them to the
                # annotated footprint, but never overwrite what they came with.
                # An item with a `build` kind is routed through a procedural
                # builder by the renderer and its mesh is never imported, so
                # claiming preserve_materials there made the plan lie about
                # which path the item takes. The one exception the renderer
                # actually honours is the sink (`spuele`), which imports its
                # real model despite carrying build="hob".
                "preserve_materials": bool(model) and (
                    not build or spec["type"] == "sink"),
                "wall_snapped": bool(symbol.get("wall_snapped")),
                "source": "simplifier_annotations_proof",
            })

        # A desk without a chair reads as unfinished (defect #4). If Rainer
        # annotated no schreibtischstuhl, derive one: offset from the desk
        # toward its room's centre (convention-free — no guess about which
        # local axis is 'front'), turned to face the desk. Presentation-only,
        # like all furnishing; never geometry.
        has_chair = any(p["asset_id"] == "schreibtischstuhl" for p in placements)
        chair_model = models.get("schreibtischstuhl")
        if not has_chair and chair_model:
            for desk in [p for p in placements if p["asset_id"].startswith("schreibtisch")]:
                dx, dy = desk["position_mm"]
                room = next((r for r in rooms if point_in_polygon((dx, dy), r["polygon_mm"], 0)), None)
                if not room:
                    continue
                pts = room["polygon_mm"]
                centroid = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
                vx, vy = centroid[0] - dx, centroid[1] - dy
                norm = math.hypot(vx, vy) or 1.0
                offset = (desk["target_bbox_mm"].get("depth_mm") or 800) / 2 + 350
                cx, cy = dx + vx / norm * offset, dy + vy / norm * offset
                facing = (math.degrees(math.atan2(-vx, vy)) + 180.0) % 360.0
                placements.append({
                    "asset_id": "schreibtischstuhl",
                    "type": "office_chair",
                    "mesh_path": chair_model["path"],
                    "model_source": chair_model["source"],
                    "model_label": chair_model.get("label"),
                    "scale_divisor": chair_model.get("divisor", 1.0),
                    "verified_size_mm": chair_model.get("size_mm"),
                    "size_mismatch": False,
                    "footprint_measured": False,
                    "build": None,
                    "position_mm": [round(cx, 1), round(cy, 1)],
                    "rotation_deg": round(facing, 1),
                    "mirrored": False,
                    "target_bbox_mm": {"width_mm": 650, "depth_mm": 650,
                                       "height_mm": 1200},
                    "height_mm": 0,
                    "preserve_materials": True,
                    "wall_snapped": False,
                    "derived_from": desk["asset_id"],
                    "source": "simplifier_annotations_proof",
                })

        # The modern dining pick is a TABLE-ONLY model (the old set model was
        # a black blob and got swapped on Rainer's request); six chairs are
        # derived around it: two per long side, one per end, each turned to
        # face the table. Only when the resolved pick is a bare table —
        # a set model (classic) brings its own chairs.
        chair_model = models.get("essgruppe_stuhl")
        if chair_model:
            for table in [p for p in placements
                          if p["asset_id"] == "essgruppe_6"
                          and "table" in (p.get("model_label") or "").lower()
                          and "set" not in (p.get("model_label") or "").lower()]:
                tx, ty = table["position_mm"]
                theta = math.radians(table.get("rotation_deg", 0))
                cos_t, sin_t = math.cos(theta), math.sin(theta)
                half_w = (table["verified_size_mm"] or [1522, 914])[0] / 2
                half_d = (table["verified_size_mm"] or [1522, 914])[1] / 2
                chair_half = 297
                side_y = half_d + 40 + chair_half
                end_x = half_w + 40 + chair_half
                locals_deg = [(-half_w / 2, side_y, 180), (half_w / 2, side_y, 180),
                              (-half_w / 2, -side_y, 0), (half_w / 2, -side_y, 0),
                              (end_x, 0, 90), (-end_x, 0, 270)]
                for lx, ly, face in locals_deg:
                    wx = tx + lx * cos_t - ly * sin_t
                    wy = ty + lx * sin_t + ly * cos_t
                    placements.append({
                        "asset_id": "essgruppe_stuhl",
                        "type": "dining_chair",
                        "mesh_path": chair_model["path"],
                        "model_source": chair_model["source"],
                        "model_label": chair_model.get("label"),
                        "scale_divisor": chair_model.get("divisor", 1.0),
                        "verified_size_mm": chair_model.get("size_mm"),
                        "size_mismatch": False,
                        "footprint_measured": False,
                        "build": None,
                        "position_mm": [round(wx, 1), round(wy, 1)],
                        "rotation_deg": (table.get("rotation_deg", 0) + face) % 360,
                        "mirrored": False,
                        "target_bbox_mm": {"width_mm": 563, "depth_mm": 593,
                                           "height_mm": 844},
                        "height_mm": 0,
                        "preserve_materials": True,
                        "wall_snapped": False,
                        "derived_from": "essgruppe_6",
                        "source": "simplifier_annotations_proof",
                    })

        floors_out.append({
            "id": level,
            "name": level,
            "level": level,
            "scale_metres_per_x_unit": scale,
            "rooms": rooms,
            "walls": walls,
            "openings": openings,
            "placements": placements,
            "unplaced": skipped,
            "skipped_rooms": [],
            "unmatched_openings": unmatched,
            "openings_in_excluded_rooms": [
                {"id": oid, "room": label} for oid, label in skipped_excluded],
        })

    out = {
        "schema": "dmh-furnished-render-plan-proof-v1",
        "plan_id": project_id,
        # No canonical document exists for this plan, so there is no geometry
        # hash to quote. Saying so explicitly is the point: an image built this
        # way is for review and cannot be delivered.
        "source_geometry_hash": None,
        "source": "simplifier_annotations_proof",
        "not_for_delivery": True,
        "style": style,
        "floors": floors_out,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1)

    for floor in floors_out:
        print(f"[plan] {floor['name']}: {len(floor['rooms'])} rooms, {len(floor['walls'])} walls "
              f"({sum(1 for w in floor['walls'] if w['wall_type'] == 'exterior')} exterior), "
              f"{len(floor['openings'])} openings, {len(floor['placements'])} furniture")
        if floor["unmatched_openings"]:
            print(f"[plan]   {len(floor['unmatched_openings'])} openings matched no wall")
        for entry in floor.get("openings_in_excluded_rooms", []):
            print(f"[plan]   opening {entry['id']} sits in excluded room "
                  f"'{entry['room']}' — intentionally not rendered")
        for item in floor["unplaced"]:
            print(f"[plan]   skipped {item['symbol']}: {item['reason']}")
        procedural = [p["asset_id"] for p in floor["placements"] if p.get("model_source") == "procedural"]
        if procedural:
            print(f"[plan]   built procedurally: {', '.join(sorted(set(procedural)))}")
    print(f"[plan] wrote {out_path}")


if __name__ == "__main__":
    main()
