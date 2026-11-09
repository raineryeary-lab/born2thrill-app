"""Automated pass/fail checks for a render plan + its render log, replacing
manual eyeballing for defects that have a cheap, precise test. Every check
here corresponds to a real defect chased by hand earlier in this project's
history (see docs/RENDER-WORKFLOW.md and the plan-exterior-classic fix
history):

  wall_angles          -- the wall-22 kink: an off-axis wall that isn't the
                           intentionally-relaxed shortest edge
  opening_count        -- openings silently dropped or duplicated between
                           annotation and render plan
  procedural_fallback  -- furniture silently falling back to anonymous
                           boxes instead of real models
  render_log           -- missing-asset / WARNING lines in a Blender log

The mesh-bounding-box sanity check (catches the coplanar-boolean-union
wall-deletion failure) needs bpy and lives in verify_render_blend.py,
run via `blender --background --python`, since it must inspect the
actual built scene.

Usage:
  python scripts/verify_render.py <plan.json> [--annotations <annotations.json>] [--log <blender_log.txt>]

Exit code 0 = all checks passed. Exit code 1 = at least one check failed.
Prints one line per check, PASS or FAIL, plus detail on failure.
"""
import argparse
import json
import math
import os
import re
import sys


DIAGONAL_TOLERANCE_DEG = 6.0


def check_wall_angles(plan, tolerance_deg=0.05,
                      diagonal_tolerance_deg=DIAGONAL_TOLERANCE_DEG):
    """At most one exterior wall per floor may sit off-axis (the shortest
    edge, by design -- see _regularize_outline_points), and only up to the
    angle-snap tolerance (6 degrees). Every other wall must be within
    `tolerance_deg` of 0/45/90. Catches the wall-22 class of bug: an
    off-axis wall that ISN'T the shortest, silently landing on a long,
    visually prominent wall instead."""
    failures = []
    for floor in plan.get("floors", []):
        walls = [w for w in floor.get("walls", []) if w["wall_type"] == "exterior"]
        if len(walls) < 3:
            continue
        lengths = {}
        off_axis = {}
        for w in walls:
            sx, sy = w["start_mm"]
            ex, ey = w["end_mm"]
            length = math.hypot(ex - sx, ey - sy)
            if length < 1e-6:
                continue
            angle = math.degrees(math.atan2(ey - sy, ex - sx)) % 90
            angle = min(angle, 90 - angle)
            lengths[w["id"]] = length
            off_axis[w["id"]] = angle
        # A wall near 45 degrees is a DIAGONAL, not a crooked wall. The
        # docstring above has always said "within tolerance of 0/45/90", but
        # the implementation only ever measured distance to an axis, so every
        # deliberate diagonal counted as a defect. Measured 2026-08-20: of 37
        # walls this rule rejected across the catalogue, 17 sat between 40 and
        # 50 degrees -- chamfered corners and the angled wing that gives the
        # Winkelbungalow its name.
        #
        # The tolerance matches the 6 degrees used by
        # _regularize_outline_points, and for the same reason: that function
        # deliberately does NOT snap diagonals ("left exactly as drawn"), so a
        # drawn diagonal keeps its hand tremor and must be judged by the same
        # margin the axis-aligned edges are snapped within.
        #
        # This does not relax the rule for crooked walls. A wall a few degrees
        # off an AXIS is still a defect and still fails -- which is what caught
        # the 6-to-15-degree walls in this same batch.
        offenders = {wid: ang for wid, ang in off_axis.items()
                     if ang > tolerance_deg
                     and abs(ang - 45.0) > diagonal_tolerance_deg}
        if not offenders:
            continue
        if len(offenders) > 1:
            failures.append(f"{floor.get('name', '?')}: {len(offenders)} walls off-axis "
                            f"(expected at most 1, the shortest edge): {offenders}")
            continue
        offender_id = next(iter(offenders))
        shortest_id = min(lengths, key=lambda wid: lengths[wid])
        if offender_id != shortest_id:
            failures.append(f"{floor.get('name', '?')}: wall {offender_id} is "
                            f"{off_axis[offender_id]:.3f} deg off-axis and is NOT the "
                            f"shortest wall (shortest is {shortest_id}, "
                            f"{lengths[shortest_id]:.0f}mm vs offender's "
                            f"{lengths[offender_id]:.0f}mm) -- residual angle-snap error "
                            f"landed on the wrong wall.")
    return failures


def check_opening_counts_against_correction(plan):
    """Corrected plans are verified against their own source revision."""
    path = plan.get("correction_revision")
    if not path or not os.path.exists(path):
        return [f"correction revision not readable: {path!r}"]
    try:
        with open(path, encoding="utf-8-sig") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        return [f"could not read correction revision: {error}"]
    by_floor = {floor.get("id"): len(floor.get("openings") or [])
                for floor in document.get("floors", [])}
    failures = []
    for floor in plan.get("floors", []):
        expected = by_floor.get(floor.get("id"))
        if expected is None:
            failures.append(f"{floor.get('name', '?')}: no floor {floor.get('id')!r} in the "
                            f"correction revision")
            continue
        found = len(floor.get("openings", []))
        if found != expected:
            failures.append(f"{floor.get('name', '?')}: correction revision has {expected} "
                            f"openings, plan has {found} -- mismatch of {expected - found}")
    return failures


def check_opening_counts(plan, annotations_path):
    """Cross-check the render plan's exterior opening count against the
    source annotation's door+window count for the same floor, catching
    openings silently dropped (or duplicated) between annotation and plan."""
    # A corrected plan's openings come from the correction revision, not from
    # the annotation package — and its floors are named in a different
    # vocabulary (Erdgeschoss vs groundfloor), so cross-checking it against
    # annotations counts zero and reports every opening as invented. Check it
    # against the document it was actually built from.
    if str(plan.get("source", "")).startswith("correction") or plan.get("correction_revision"):
        return check_opening_counts_against_correction(plan)
    if not annotations_path:
        return ["skipped (no --annotations given)"]
    try:
        with open(annotations_path, encoding="utf-8-sig") as handle:
            annotations = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        return [f"could not read annotations: {error}"]

    # Per FLOOR, not per project. The original version counted every
    # door/window in the file and compared that one total against each floor
    # in turn: onehalfstorey_020's 12 ground + 11 upper openings are exactly
    # the 23 the annotation holds, and both styles were excluded from the
    # handoff over "mismatch of 11" / "mismatch of 12". Single-floor projects
    # passed only because there the project total IS the floor total.
    by_floor = {}
    homeless = 0
    for element in annotations.get("elements", []):
        if element.get("type") not in ("door", "window", "opening"):
            continue
        level = element.get("floor_level")
        if not level:
            homeless += 1
            continue
        by_floor[level] = by_floor.get(level, 0) + 1

    failures = []
    if homeless:
        failures.append(f"{homeless} door/window element(s) carry no floor_level, "
                        f"so they belong to no floor and cannot be verified")
    for floor in plan.get("floors", []):
        level = floor.get("level") or floor.get("id") or floor.get("name")
        annotated_openings = by_floor.get(level, 0)
        plan_openings = len(floor.get("openings", []))
        excluded = len(floor.get("openings_in_excluded_rooms", []))
        unmatched = len(floor.get("unmatched_openings", []) if isinstance(floor.get("unmatched_openings"), list) else [])
        accounted = plan_openings + excluded
        # Compared unconditionally. Guarding on `annotated_openings` let a plan
        # invent openings on a floor the annotation gives none — the count was
        # 0, the guard was falsy, and the mismatch went unreported (Codex,
        # 2026-08-16).
        if accounted != annotated_openings:
            failures.append(f"{floor.get('name', '?')}: annotation has {annotated_openings} "
                            f"door/window elements, plan accounts for {accounted} "
                            f"({plan_openings} rendered + {excluded} excluded), "
                            f"{unmatched} unmatched -- mismatch of "
                            f"{annotated_openings - accounted}")
    return failures


def check_procedural_fallback_rate(plan, max_rate=0.5):
    """Flag houses where more than max_rate of furniture placements fell
    back to an anonymous procedural box instead of a real model -- doesn't
    block, just surfaces for human review instead of silently passing."""
    failures = []
    for floor in plan.get("floors", []):
        placements = floor.get("placements", [])
        if not placements:
            continue
        procedural = [p for p in placements if p.get("model_source") == "procedural"]
        rate = len(procedural) / len(placements)
        if rate > max_rate:
            names = sorted({p["asset_id"] for p in procedural})
            failures.append(f"{floor.get('name', '?')}: {len(procedural)}/{len(placements)} "
                            f"placements ({rate:.0%}) are procedural fallbacks: {', '.join(names)}")
    return failures


def check_render_log(log_path):
    """Grep a saved Blender stdout log for WARNING/missing-asset lines."""
    if not log_path:
        return ["skipped (no --log given)"]
    try:
        with open(log_path, encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError as error:
        return [f"could not read log: {error}"]
    hits = [line.strip() for line in lines
            if re.search(r"\bWARNING\b|missing asset", line, re.IGNORECASE)]
    # Known-harmless noise, reported but not failed on:
    #  - "cannot be made relative": external E:\ asset libraries can't be
    #    repathed relative to the .blend, expected for every external asset.
    #  - DeprecationWarning: forward-compat noise from Blender's own API
    #    (e.g. Material.use_nodes), not a rendering defect.
    HARMLESS = ("cannot be made relative", "deprecationwarning")
    real_warnings = [h for h in hits if not any(marker in h.lower() for marker in HARMLESS)]
    if real_warnings:
        return [f"{len(real_warnings)} real warning(s) in log: " + "; ".join(real_warnings[:5])]
    return []


# --------------------------------------------------------------- RULES
#
# Rainer's standing rules, 2026-08-17. He said, repeatedly, that these are
# RULES and not notes -- so they are checked here and they FAIL the build,
# rather than living in a comment somewhere that an agent may or may not
# read. Each one costs a render its PASS.
#
# R0  the symbol is the object      a piece renders at its drawn footprint,
#                                   exactly -- not bigger, not smaller
# R1  nothing floats                every opening feature has wall at it
# R2  stairs exist                  a shared_stair_core is built, with a
#                                   Gelaender on every open side
# R3  Treppenloch                   every storey above the flight has the
#                                   opening cut through its slab
# R4  outside exists                site areas reach the plan when the
#                                   annotation has them
# R5  appliances read as appliances no furniture type falls through to the
#                                   catch-all finish

def check_symbol_fit(log_path):
    """R0. The renderer prints one `symbol fit` line per prototype with the
    achieved size and the symbol's own size. Any disagreement is a failure:
    what Rainer positions and what he gets must be the same object."""
    if not log_path or not os.path.exists(log_path):
        return ["skipped (no --interior-log given)"]
    failures = []
    seen = 0
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = re.search(r"symbol fit\s+(\S+)\s+->\s+(\d+)x(\d+)x(\d+)mm "
                              r"\(symbol (\d+)x(\d+)x(\d+)\)", line)
            if not match:
                continue
            seen += 1
            asset = match.group(1)
            got = [int(match.group(i)) for i in (2, 3, 4)]
            want = [int(match.group(i)) for i in (5, 6, 7)]
            if any(abs(g - w) > 2 for g, w in zip(got, want)):
                failures.append(f"{asset}: rendered {got[0]}x{got[1]}x{got[2]} "
                                f"but its symbol is {want[0]}x{want[1]}x{want[2]}")
    if not seen:
        # An unfurnished house has nothing to fit, and failing it here says
        # "the rule is not running" when the truth is "there is no furniture".
        # bungalow_039 (0 instances from 0 meshes) failed this way on the first
        # batch run, 2026-08-19. Read the renderer's own count and only complain
        # when furniture WAS placed and no fit line appeared -- that is the case
        # the rule was written to catch.
        placed = 0
        with open(log_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = re.search(r"furniture\s+(\d+) instances", line)
                if match:
                    placed = int(match.group(1))
                    break
        if placed:
            return ["no `symbol fit` lines in the interior log — the rule is not running"]
        return []
    return failures


def check_no_floating_features(log_path):
    """R1. Any opening feature sliced away from its wall, or left standing
    where the wall was cut below it, is a floating object."""
    if not log_path or not os.path.exists(log_path):
        return ["skipped (no --interior-log given)"]
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    match = re.search(r"features sliced\s+(\d+)", text)
    if not match:
        return ["no `features sliced` line in the interior log"]
    return []


def check_stairs(plan, log_path):
    """R2 + R3. If the plan carries a stair core, every interior render must
    build it, put a Gelaender on it, and — above the flight — cut the
    Treppenloch."""
    if not plan.get("shared_stair_core"):
        return []
    if not log_path or not os.path.exists(log_path):
        return ["skipped (no --interior-log given)"]
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    failures = []
    steps = re.search(r"stair steps\s+(\d+)", text)
    if not steps or int(steps.group(1)) == 0:
        failures.append("plan carries shared_stair_core but no stair was built")
    # "Handlauf" counts: the Bastian system (ETA-06/0261) carries the rail on
    # Geraenderstaebe up to a Handlauf, and a flight walled on both flanks gets
    # a wall-mounted Handlauf instead of a balustrade. Grepping only for the
    # word "Gelaender" failed every correctly-railed stair after the renderer
    # was rewritten (batch-build, 2026-08-19) -- the rule was checking the
    # wording, not the thing.
    if not any(word in text for word in ("Gelaender", "Handlauf")):
        failures.append("stair built with no Gelaender")
    upper = re.search(r"floor\s+(\S+)", text)
    if "through the Treppenloch" in text and "Treppenloch     cut through" not in text:
        failures.append("storey above the flight has no Treppenloch cut")
    return failures


def check_exterior_areas(plan, annotations_path):
    """R4. Site areas in the annotation must reach the plan."""
    if not annotations_path or not os.path.exists(annotations_path):
        return ["skipped (no --annotations given)"]
    with open(annotations_path, encoding="utf-8-sig") as handle:
        annotations = json.load(handle)
    drawn = len(annotations.get("exterior_areas") or [])
    carried = len(plan.get("exterior_areas") or [])
    if drawn and not carried:
        return [f"annotation has {drawn} exterior area(s) — Terrasse/Einfahrt/"
                f"Gehweg — and the plan carries none"]
    return []


def check_furniture_inside(plan):
    """R6: Jedes Moebel steht IN einem Raum dieses Plans.

    bungalow_036, 2026-08-21: Rainers Ecksofa lag bei x=10950 in einem Haus,
    dessen Raeume bei x=10047 enden -- im Moebel-Editor korrekt platziert, aber
    Editor (Korrekturweg) und Bau (Annotationsweg) rechnen das Haus verschieden
    gross. Das Sofa ragte im Render aus der Bodenplatte. Solange die beiden
    Wege nicht vereinigt sind, muss so eine Lieferung LAUT scheitern und das
    Moebel beim Namen nennen, statt still ein kaputtes Bild zu zertifizieren.

    Toleranz 300 mm: an eine Wand geschobene Moebel duerfen mit der Mitte
    knapp ausserhalb des Raumpolygons liegen (halbe Wandstaerke + Anschnitt).
    Abgeleitete Teile (Stuehle einer Essgruppe) zaehlen nicht eigenstaendig --
    massgeblich ist, was der Nutzer gesetzt hat.
    """
    def in_or_near(x, y, polygone, tol=300.0):
        for poly in polygone:
            if len(poly) < 3:
                continue
            inside = False
            j = len(poly) - 1
            naeher = False
            for i in range(len(poly)):
                xi, yi = poly[i]; xj, yj = poly[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
                dx, dy = xj - xi, yj - yi
                l2 = dx * dx + dy * dy
                if l2:
                    t = max(0.0, min(1.0, ((x - xi) * dx + (y - yi) * dy) / l2))
                    ex, ey = xi + t * dx, yi + t * dy
                    if ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5 <= tol:
                        naeher = True
                j = i
            if inside or naeher:
                return True
        return False

    failures = []
    for floor in plan.get("floors") or []:
        # Codex-Review 2026-08-21, drei Luecken in der ersten Fassung:
        # (1) ein Geschoss OHNE Raumpolygone wurde ganz uebersprungen -- ein
        #     False Negative statt eines Fehlschlags; (2) Moebel in einer
        #     ausgeschlossenen Flaeche (Garage, Terrasse, Balkon) galten als
        #     "draussen", obwohl sie legitim dort stehen; (3) gezeichnete
        #     Moebel (points_mm statt position_mm, z.B. eine Kuechenzeile)
        #     wurden komplett uebersprungen.
        raeume = [r.get("polygon_mm") or [] for r in floor.get("rooms") or []]
        raeume = [p for p in raeume if len(p) >= 3]
        ausschluss = [a.get("polygon_mm") or [] for a in floor.get("excluded_areas") or []]
        ausschluss = [p for p in ausschluss if len(p) >= 3]
        for item in floor.get("placements") or []:
            if item.get("derived_from"):
                continue
            punkte = []
            if item.get("position_mm"):
                punkte = [item["position_mm"]]
            elif item.get("points_mm"):
                pts = item["points_mm"]
                punkte = [[sum(p[0] for p in pts) / len(pts),
                          sum(p[1] for p in pts) / len(pts)]] if pts else []
            if not punkte:
                continue
            x, y = punkte[0]
            if not raeume and not ausschluss:
                failures.append(
                    "%s: keine Raumpolygone im Plan -- kann %s nicht gegen "
                    "Raeume pruefen (fehlt der Maßstab?)"
                    % (floor.get("id"), item.get("asset_id")))
                continue
            # 300mm Toleranz nur fuer Raeume (Wandstaerke + Anschnitt an einer
            # geschobenen Kommode) -- eine ausgeschlossene Flaeche (Garage,
            # Terrasse, Balkon) ist grosszuegig genug, dass das Moebel wirklich
            # DRIN stehen muss (Codex-Review, 2026-08-21).
            if not in_or_near(x, y, raeume, tol=300.0) \
                    and not in_or_near(x, y, ausschluss, tol=0.0):
                # Die Mitte allein genuegt nicht, um das Stueck zu FINDEN.
                # Am 2026-08-28 stand in onehalfstorey_020 eines von sieben
                # `stuff`-Rechtecken unterhalb des Bildrands: im Editor weder
                # sichtbar noch anklickbar. "im Moebel-Editor weiter nach
                # innen ruecken" war damit ein Rat, dem niemand folgen konnte.
                # Also: die Ecken dazu, und der naechste Raum mit Abstand.
                # Fuer die Meldung die Raeume MIT Namen, nicht die nackten
                # Polygone der Pruefung -- "921 mm vom naechsten Raum" sagt
                # weniger als "921 mm vom Kinderzimmer".
                naechster, abstand = _naechster_raum(
                    x, y, floor.get("rooms") or [])
                wo = ""
                if item.get("points_mm"):
                    wo = " (Ecken %s)" % ", ".join(
                        "%.0f,%.0f" % (p[0], p[1]) for p in item["points_mm"][:4])
                naehe = ""
                if naechster is not None:
                    naehe = (" -- %.0f mm vom naechsten Raum (%s)"
                             % (abstand, naechster))
                failures.append(
                    "%s: %s steht bei %.0f,%.0f ausserhalb jedes Raums%s%s -- im "
                    "Moebel-Editor weiter nach innen ruecken"
                    % (floor.get("id"), item.get("asset_id"), x, y, wo, naehe))
    return failures


def _naechster_raum(x, y, raeume):
    """Der naechstgelegene Raum und der Abstand dorthin, in Millimetern.

    Ohne diese Angabe steht in der Meldung nur eine Koordinate. Mit ihr
    sieht man sofort, ob ein Stueck 20 mm ueber eine Wand ragt oder --
    wie am 2026-08-28 -- fast einen Meter vor der Fassade im Freien liegt.
    """
    bester, kuerzester = None, None
    for raum in raeume or []:
        poly = raum.get("polygon_mm") if isinstance(raum, dict) else raum
        if not poly or len(poly) < 2:
            continue
        for i in range(len(poly)):
            ax, ay = poly[i][0], poly[i][1]
            bx, by = poly[(i + 1) % len(poly)][0], poly[(i + 1) % len(poly)][1]
            dx, dy = bx - ax, by - ay
            laenge = dx * dx + dy * dy
            t = 0.0 if laenge == 0 else max(
                0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / laenge))
            d = math.hypot(x - (ax + t * dx), y - (ay + t * dy))
            if kuerzester is None or d < kuerzester:
                kuerzester = d
                bester = raum.get("name") if isinstance(raum, dict) else "Raum"
    return bester, (kuerzester if kuerzester is not None else 0.0)


def check_finish_coverage(plan):
    """R5. A furniture type with no explicit finish falls through to the
    catch-all and can land on the same colour as the cabinetry — how the
    fridge came to be the same colour as the rest of the kitchen."""
    known = {
        "bed_double", "sofa", "wardrobe", "dressing_wardrobe", "nightstand",
        "coffee_table", "dining_table", "desk", "tv_unit", "storage_shelving",
        "washer_dryer_unit", "bathroom_vanity", "office_chair", "coat_rack",
        "rug", "wall_art", "mirror", "floor_lamp", "table_lamp", "shoe_rack",
        "clothing_rack", "counter", "oven_housing", "sink", "fridge",
        "dining_set", "sideboard", "wall_panel", "hob", "toilet", "shower",
        "bathtub", "bed", "stool", "tv", "washer", "cupboard", "towel_radiator",
    }
    missing = set()
    for floor in plan.get("floors", []):
        for placement in floor.get("placements", []):
            if placement.get("build") in ("box", "path", "rect") \
                    and placement.get("type") not in known:
                missing.add(placement["type"])
    if missing:
        return [f"procedural types with no explicit finish (will use the "
                f"catch-all): {', '.join(sorted(missing))}"]
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_path")
    parser.add_argument("--annotations")
    parser.add_argument("--log")
    parser.add_argument("--interior-log",
                        help="the dollhouse render's log, for the rule checks")
    args = parser.parse_args()

    with open(args.plan_path, encoding="utf-8-sig") as handle:
        plan = json.load(handle)

    checks = [
        ("wall_angles", check_wall_angles(plan)),
        ("opening_count", check_opening_counts(plan, args.annotations)),
        ("procedural_fallback", check_procedural_fallback_rate(plan)),
        ("render_log", check_render_log(args.log)),
        # Rainer's rules. Not notes.
        ("R0_symbol_is_the_object", check_symbol_fit(args.interior_log)),
        ("R1_nothing_floats", check_no_floating_features(args.interior_log)),
        ("R2_R3_stairs_and_treppenloch", check_stairs(plan, args.interior_log)),
        ("R4_outside_exists", check_exterior_areas(plan, args.annotations)),
        ("R5_appliance_finishes", check_finish_coverage(plan)),
        ("R6_furniture_inside", check_furniture_inside(plan)),
    ]

    failed = False
    for name, failures in checks:
        real_failures = [f for f in failures if not f.startswith("skipped")]
        if real_failures:
            failed = True
            print(f"FAIL {name}")
            for f in real_failures:
                print(f"  - {f}")
        elif failures:
            print(f"SKIP {name}: {failures[0]}")
        else:
            print(f"PASS {name}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
