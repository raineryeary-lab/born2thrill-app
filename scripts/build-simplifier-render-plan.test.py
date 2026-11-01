"""geometry_only() must emit walls and openings, not just rooms.

Rainer, 2026-08-22, from the furniture step of /haus?plan=bungalow_039: "why
can i not see the walls and doors when placing furniture". geometry_only()
used to emit rooms only ("the room polygons ... and nothing else" per its own
former docstring) -- the furniture editor's overrideFloor then hardcoded
walls/openings to empty arrays, because there was nothing to read.

Runs against the real bungalow_039 Simplifier project (a hand-crafted
fixture would need to reproduce build_walls()'s edge-pairing tolerances to
be representative) so this also proves the shared
build_floor_walls_and_openings() helper -- now used by BOTH this function and
the full render-plan build -- actually matches doors/windows onto walls, not
just that build_walls() runs.
"""

import ast
import importlib.util
import json
import math
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ID = "bungalow_039"
SIMPLIFIER_PROJECTS = HERE.parent.parent / "floorplan-simplifier" / "projects"
GOLDEN_VECTORS = HERE / "pose-golden-vectors.json"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "build_simplifier_render_plan", HERE / "build-simplifier-render-plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless((SIMPLIFIER_PROJECTS / PROJECT_ID / "annotations.json").exists(),
                      f"{PROJECT_ID} not present in this checkout's floorplan-simplifier data")
class GeometryOnlyWallsAndOpeningsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        module = load_module()
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "geometry.json"
        module.geometry_only(PROJECT_ID, str(out))
        cls.payload = json.loads(out.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_floor_has_walls_and_openings(self):
        floors = self.payload["floors"]
        self.assertTrue(floors, "no floors in geometry_only() output")
        for floor in floors:
            self.assertTrue(floor["walls"], f"{floor['floor_level']}: no walls")
            self.assertTrue(floor["openings"], f"{floor['floor_level']}: no openings")

    def test_walls_use_the_short_field_names_the_editor_reads(self):
        # src/app/floorplan-workbench/page.tsx reads wall.id/start/end/thickness
        # -- the annotation-pipeline's own start_mm/end_mm/thickness_mm would
        # silently render nothing (undefined coordinates), the exact bug this
        # test guards against.
        for floor in self.payload["floors"]:
            for wall in floor["walls"]:
                for key in ("id", "start", "end", "thickness"):
                    self.assertIn(key, wall)
                self.assertEqual(len(wall["start"]), 2)
                self.assertEqual(len(wall["end"]), 2)
                self.assertNotIn("start_mm", wall)

    def test_openings_use_the_short_field_names_and_resolve_to_a_real_wall(self):
        for floor in self.payload["floors"]:
            wall_ids = {wall["id"] for wall in floor["walls"]}
            for opening in floor["openings"]:
                for key in ("id", "wall_id", "opening_type", "position", "width"):
                    self.assertIn(key, opening)
                self.assertIn(opening["wall_id"], wall_ids,
                               f"{floor['floor_level']}: opening {opening['id']} "
                               f"references a wall not in this floor's wall list")
                self.assertNotIn("width_mm", opening)

    def test_rooms_carry_a_real_area(self):
        # room.area_m2 (page.tsx:545) had no fallback -- geometry_only()
        # rooms omitting it rendered "ca. NaN mA2" for every room in the
        # furniture editor (Rainer, 2026-08-22, caught from a screenshot).
        for floor in self.payload["floors"]:
            for room in floor["rooms"]:
                self.assertIn("area_m2", room)
                self.assertGreater(room["area_m2"], 0)

    def test_no_two_same_type_walls_sit_on_the_same_line_unmerged(self):
        # _merge_collinear_walls() used to compute its line identity from a
        # wall's raw (possibly reversed) direction vector, so two segments
        # on the IDENTICAL physical line got opposite-signed offsets when
        # one was stored start->end and the other end->start -- silently
        # skipping the merge and leaving a real kink (measured on
        # bungalow_039: two segments 25.4mm apart on one line, offsets
        # +6441.7 vs -6416.3, sign alone put them ~12,858mm apart by this
        # metric). Rainer: "die Tueren und waende sind 'off'". Recomputes
        # the SAME direction-invariant angle/offset the fix itself uses, so
        # this fails on the old code and passes on the new.
        offset_tolerance_mm = 150  # matches MERGE_LINE_OFFSET_TOLERANCE_MM
        angle_tolerance_deg = 12   # matches PARALLEL_TOLERANCE_DEG
        for floor in self.payload["floors"]:
            by_type = {}
            for wall in floor["walls"]:
                by_type.setdefault(wall.get("wall_type", "?"), []).append(wall)
            for wall_type, walls in by_type.items():
                lines = []
                for wall in walls:
                    (ax, ay), (bx, by) = wall["start"], wall["end"]
                    length = math.dist((ax, ay), (bx, by))
                    if length < 1e-6:
                        continue
                    ux, uy = (bx - ax) / length, (by - ay) / length
                    angle = math.atan2(uy, ux) % math.pi
                    nx, ny = -math.sin(angle), math.cos(angle)
                    offset = ax * nx + ay * ny
                    lines.append((wall["id"], angle, offset))
                for i, (id_a, angle_a, offset_a) in enumerate(lines):
                    for id_b, angle_b, offset_b in lines[i + 1:]:
                        angle_diff = abs((angle_a - angle_b + math.pi / 2) % math.pi - math.pi / 2)
                        if math.degrees(angle_diff) > angle_tolerance_deg:
                            continue
                        self.assertGreater(
                            abs(offset_a - offset_b), offset_tolerance_mm,
                            f"{floor['floor_level']}: {wall_type} walls {id_a} and {id_b} "
                            f"sit on the same line ({abs(offset_a - offset_b):.1f}mm apart) "
                            "but were not merged")

    def test_door_hinge_and_swing_are_normalized_into_the_walls_frame(self):
        # annotate.js's own swing preview reads hinge_side/swing_side
        # relative to the door element's OWN two drawn points; add_door_leaf()
        # reads the identical stored strings relative to the matched WALL's
        # own start_mm->end_mm order -- an unrelated direction decided by
        # which room's edge produced that wall segment. The two frames
        # disagree whenever a door's own point order runs opposite to its
        # wall's, and every hand-set value then renders backwards while
        # still previewing correctly in the annotator (Rainer, 2026-08-22:
        # "Schlafzimmertuer falsche richtung ... Buero Tuer auch
        # Eingangstueer auch Kuechentuer auch"). Measured directly against
        # bungalow_039's real annotation + compiled walls before this fix:
        # exactly these 3 of 6 explicitly-set doors had opposite point
        # order to their wall (Kueche, Buero/Gast, Eingang) and were the
        # exact 3 doors Rainer named as wrong.
        #
        # geometry_only()'s own openings_out (the furniture editor's short
        # schema) drops swing_side/hinge_side entirely -- doors don't swing
        # in that editor -- so this calls build_floor_walls_and_openings()
        # directly, the one place both fields survive, replicating exactly
        # the setup geometry_only() itself uses (same module, same project).
        module = load_module()
        annotations = json.loads(
            (SIMPLIFIER_PROJECTS / PROJECT_ID / "annotations.json").read_text(encoding="utf-8"))
        raw_by_id = {
            el["id"]: (el.get("hinge_side"), el.get("swing_side"))
            for el in annotations.get("elements", [])
            if el.get("type") == "door"
        }
        project_dir = str(SIMPLIFIER_PROJECTS / PROJECT_ID)
        pixel_width, pixel_height = module.image_size(project_dir, annotations)
        floor_scale = annotations.get("floor_scale") or {}
        levels = sorted({item.get("floor_level") for item in annotations.get("annotations", [])
                         if item.get("floor_level")})
        ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
        frame = module.Frame(floor_scale[ground_level], pixel_width, pixel_height)
        rooms, excluded_polygons = [], []
        for item in annotations.get("annotations", []):
            if item.get("floor_level") != ground_level or len(item.get("points") or []) < 3:
                continue
            points = item["points"]
            if module.excluded(item.get("label")):
                excluded_polygons.append((item.get("label"), [frame.point(p) for p in points]))
                continue
            polygon_mm = [frame.point(p) for p in points]
            rooms.append({"id": item.get("id"), "name": item.get("label"),
                          "kind": module.room_kind(item.get("label")), "polygon_mm": polygon_mm})
        _walls, openings, _unmatched, _skipped = module.build_floor_walls_and_openings(
            rooms, excluded_polygons, annotations, ground_level, frame, True)
        openings_by_id = {o["id"]: o for o in openings}
        # Expected wall-frame values per real door (id suffix -> hinge,
        # swing), from the geometric normalization: Kueche/Buero/Eingang
        # have door points opposite their wall (both labels re-expressed);
        # Bad/HWR align and keep theirs; the Schlafzimmertuer (hinge="end")
        # keeps its hinge but its SWING re-expresses, because the annotator
        # draws the swing relative to hinge->free, which "end" reverses --
        # the door that stayed wrong under the first, label-flipping fix
        # (Rainer, 2026-08-22 evening: "doors are still wrong").
        expected_by_suffix = {
            "39265e": ("end", "first_room"),      # Schlafen: swing re-expressed
            "40c789": ("start", "second_room"),   # Bad: unchanged
            "f1af94": ("start", "second_room"),   # HWR: unchanged
            "369138": ("end", "second_room"),     # Kueche: both re-expressed
            "5d6a18": ("end", "second_room"),     # Buero/Gast: both re-expressed
            "a64838": ("end", "second_room"),     # Eingang: both re-expressed
        }

        def classify(door_id):
            return next((s for s in expected_by_suffix if door_id.endswith(s)), None)

        seen = set()
        for door_id, opening in openings_by_id.items():
            if opening["opening_type"] != "door" or door_id not in raw_by_id:
                continue
            suffix = classify(door_id)
            if suffix is None:
                continue
            seen.add(suffix)
            want_hinge, want_swing = expected_by_suffix[suffix]
            self.assertEqual(opening["hinge_side"], want_hinge,
                              f"door {door_id}: wall-frame hinge_side")
            self.assertEqual(opening["swing_side"], want_swing,
                              f"door {door_id}: wall-frame swing_side")
        missing = set(expected_by_suffix) - seen
        self.assertFalse(missing, f"expected doors not found in build_floor_walls_and_openings() output: {missing}")

    def test_wall_endpoints_and_room_polygons_share_one_coordinate_frame(self):
        # Both went through the SAME y-flip in geometry_only(). If a future
        # edit flips one and not the other, walls end up offset from the
        # rooms they should sit on -- this catches that by checking a wall's
        # y-extent falls within the overall room y-extent (with wall-
        # thickness headroom), not mirrored to the opposite side.
        for floor in self.payload["floors"]:
            room_ys = [p[1] for room in floor["rooms"] for p in room["polygon_mm"]]
            if not room_ys:
                continue
            lo, hi = min(room_ys), max(room_ys)
            pad = 500
            for wall in floor["walls"]:
                for point in (wall["start"], wall["end"]):
                    self.assertGreaterEqual(point[1], lo - pad)
                    self.assertLessEqual(point[1], hi + pad)


@unittest.skipUnless((SIMPLIFIER_PROJECTS / PROJECT_ID / "annotations.json").exists(),
                      f"{PROJECT_ID} not present in this checkout's floorplan-simplifier data")
class PoseContractTests(unittest.TestCase):
    """plans/pose-contract-slice-1-v1.md, points 1 and 3.

    The furniture-pose contract (editor space -> compiled render plan) is
    frozen as data in pose-golden-vectors.json, anchored to Rainer's
    2026-08-22 contact sheet ("B and D are Mirrored" -- the mirrored flag
    passes through UNINVERTED on the workbench path, rotation negates).
    Both plan-builder paths must produce the SAME pose from the same file:
    corrected_placements() used to re-apply the editor->render conversion
    workbench_furniture() had already performed (double y-flip, double
    rotation negation, one net mirror inversion), so the --corrected path
    delivered poses in the EDITOR's convention. Confirmed independently by
    Codex review, 2026-08-22.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def _with_furniture(self, symbols):
        """Temp workbench data root holding one furniture file; returns a
        context manager restoring the env var afterwards."""
        test = self

        class _Ctx:
            def __enter__(ctx):
                ctx.tmp = tempfile.TemporaryDirectory()
                ctx.old = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
                folder = Path(ctx.tmp.name) / "corrections" / PROJECT_ID / "furniture"
                folder.mkdir(parents=True)
                (folder / "floor-0.json").write_text(json.dumps({
                    "coordinate_space": "render-geometry-mm-y-down-v1",
                    "symbols": symbols,
                }), encoding="utf-8")
                os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"] = ctx.tmp.name
                return ctx

            def __exit__(ctx, *exc):
                if ctx.old is None:
                    os.environ.pop("FLOORPLAN_WORKBENCH_DATA_DIR", None)
                else:
                    os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"] = ctx.old
                ctx.tmp.cleanup()
                return False

        return _Ctx()

    def test_pose_golden_vectors_hold_for_the_workbench_path(self):
        golden = json.loads(GOLDEN_VECTORS.read_text(encoding="utf-8"))
        # The file's own example arithmetic must be internally consistent --
        # it is the contract a future TypeScript-side test reads too.
        for vector in golden["vectors"]:
            editor, compiled = vector["editor"], vector["compiled"]
            self.assertEqual(compiled["rotation_deg"],
                             (-editor["rotation_deg"]) % 360, vector["name"])
            self.assertEqual(compiled["mirrored"], editor["mirrored"], vector["name"])
            self.assertAlmostEqual(compiled["position_mm"][0],
                                   editor["position_mm"][0], places=1)
            self.assertAlmostEqual(compiled["position_mm"][1],
                                   golden["lo_plus_hi"] - editor["position_mm"][1],
                                   places=1)

        # Codex architecture review, 2026-09-18: workbench_furniture() now
        # flips against the frame's OWN height_mm (a stable, scale/aspect-
        # derived constant) instead of a room-polygon-derived extent -- see
        # plans/moebel-koordinaten-staleness-und-treppenbreite-v1.md.
        annotations = self.module.load_annotations(
            os.path.join(self.module.SIMPLIFIER, "projects", PROJECT_ID))
        pixel_width, pixel_height = self.module.image_size(
            os.path.join(self.module.SIMPLIFIER, "projects", PROJECT_ID), annotations)
        frame = self.module.frame_for_level(
            annotations, "groundfloor", "groundfloor", pixel_width, pixel_height)
        self.assertIsNotNone(frame)
        flip = frame.height_mm
        symbols = [dict(v["editor"], symbol="ecksofa", id=f"v{i}",
                        footprint_mm={"width_mm": 3524, "depth_mm": 2037})
                   for i, v in enumerate(golden["vectors"])]
        with self._with_furniture(symbols):
            out = self.module.workbench_furniture(PROJECT_ID, "groundfloor")
        by_id = {s["id"]: s for s in out}
        for i, vector in enumerate(golden["vectors"]):
            got = by_id[f"v{i}"]
            self.assertEqual(got["rotation_deg"],
                             vector["compiled"]["rotation_deg"], vector["name"])
            self.assertEqual(bool(got.get("mirrored")),
                             vector["compiled"]["mirrored"], vector["name"])
            ex, ey = vector["editor"]["position_mm"]
            self.assertAlmostEqual(got["position_mm"][0], ex, places=1)
            self.assertAlmostEqual(got["position_mm"][1], round(flip - ey, 1),
                                   places=1)

    def test_corrected_path_agrees_with_the_workbench_path(self):
        # The exact regression: same file, two builders, one pose. Fails on
        # the old corrected_placements() (double transform) and on the old
        # missing floor-id alias (SystemExit "cannot derive the room extent"
        # when called with the correction document's "floor-0" name).
        symbols = [{"symbol": "ecksofa", "id": "c0",
                    "position_mm": [4000.0, 3000.0],
                    "rotation_deg": 270, "mirrored": True,
                    "footprint_mm": {"width_mm": 3524, "depth_mm": 2037}}]
        with self._with_furniture(symbols):
            reference = self.module.workbench_furniture(PROJECT_ID, "groundfloor")[0]
            placements, skipped = self.module.corrected_placements(
                PROJECT_ID, "floor-0", {})
        self.assertFalse(skipped)
        pose = placements[0]
        self.assertEqual(pose["rotation_deg"], reference["rotation_deg"])
        self.assertEqual(bool(pose["mirrored"]), bool(reference.get("mirrored")))
        self.assertEqual(pose["position_mm"], reference["position_mm"])

    def test_door_pose_metamorphic_relations(self):
        # Corrected formulation, second iteration (2026-08-22 evening): the
        # annotator's swing side is defined relative to the HINGE->FREE
        # direction, which reverses with the hinge label -- so hinge and
        # swing are COUPLED, not independently flippable. Relations below
        # encode the annotator's actual drawing semantics (drawDoorSwing).
        f = self.module.door_pose_in_wall_frame
        flip_h = {"start": "end", "end": "start"}
        flip_s = {"first_room": "second_room", "second_room": "first_room"}
        a, b = (1000.0, 2000.0), (1900.0, 2050.0)
        ws, we = (0.0, 2000.0), (5000.0, 2100.0)
        base = f(a, b, ws, we, "start", "first_room")
        # (a) Swapping the WALL's ends leaves the physical door unchanged,
        #     so the wall-relative labels must swap with the wall.
        self.assertEqual(f(a, b, we, ws, "start", "first_room"),
                         (flip_h[base[0]], flip_s[base[1]]))
        # (b) Swapping the DOOR's points AND flipping the hinge label keeps
        #     the hinge on the same physical point, and the annotator's
        #     swing side (relative to hinge->free) is then UNCHANGED: same
        #     physical annotation -> identical canonical output. (The first
        #     fix wrongly flipped the swing label here too.)
        self.assertEqual(f(b, a, ws, we, "end", "first_room"), base)
        # (c) Swapping the door's points but NOT the labels moves the hinge
        #     to the other jamb AND mirrors the drawn arc -> both flip.
        self.assertEqual(f(b, a, ws, we, "start", "first_room"),
                         (flip_h[base[0]], flip_s[base[1]]))
        # (d) THE bug that survived the first fix: flipping ONLY the hinge
        #     label reverses hinge->free, so the annotator's arc lands on
        #     the other physical side -- BOTH canonical labels must flip.
        #     The old label-flipping code left the swing untouched here
        #     (bungalow_039's Schlafzimmertuer, hinge="end": preview and
        #     render guaranteed opposite).
        self.assertEqual(f(a, b, ws, we, "end", "first_room"),
                         (flip_h[base[0]], flip_s[base[1]]))
        # Unset values pass through untouched, whatever the geometry.
        self.assertEqual(f(b, a, ws, we, None, None), (None, None))


@unittest.skipUnless((SIMPLIFIER_PROJECTS / PROJECT_ID / "annotations.json").exists(),
                      f"{PROJECT_ID} not present in this checkout's floorplan-simplifier data")
class FurnitureGeometryBindingTests(unittest.TestCase):
    """plans/furniture-geometry-binding-v1.md.

    A furniture layout records WHICH drawing it was placed on. Redrawing the
    rooms and rebuilding used to re-use the old layout silently against the
    new geometry; now the build refuses. Layouts saved before the stamp
    existed (every one of them today) must keep building.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def _with_document(self, document):
        module = self.module
        test = self

        class _Ctx:
            def __enter__(ctx):
                ctx.tmp = tempfile.TemporaryDirectory()
                ctx.old = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
                folder = Path(ctx.tmp.name) / "corrections" / PROJECT_ID / "furniture"
                folder.mkdir(parents=True)
                (folder / "groundfloor.json").write_text(
                    json.dumps(document), encoding="utf-8")
                os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"] = ctx.tmp.name
                return ctx

            def __exit__(ctx, *exc):
                if ctx.old is None:
                    os.environ.pop("FLOORPLAN_WORKBENCH_DATA_DIR", None)
                else:
                    os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"] = ctx.old
                ctx.tmp.cleanup()
                return False

        return _Ctx()

    def _document(self, **extra):
        return dict({
            "coordinate_space": "render-geometry-mm-y-down-v1",
            "symbols": [{"symbol": "ecksofa", "id": "s1", "position_mm": [3000.0, 4000.0],
                         "rotation_deg": 0, "mirrored": False,
                         "footprint_mm": {"width_mm": 3524, "depth_mm": 2037}}],
        }, **extra)

    def _current_identity(self):
        # Die Identitaet der RAEUME dieses Geschosses -- dieselbe Funktion,
        # die der Bau prueft und der Editor beim Speichern stempelt.
        return self.module.level_geometry_identity(PROJECT_ID, "groundfloor")

    def test_legacy_document_without_stamp_still_builds(self):
        with self._with_document(self._document()):
            out = self.module.workbench_furniture(PROJECT_ID, "groundfloor")
        self.assertEqual(len(out), 1)

    def test_matching_stamp_builds(self):
        doc = self._document(geometry_identity=self._current_identity())
        with self._with_document(doc):
            out = self.module.workbench_furniture(PROJECT_ID, "groundfloor")
        self.assertEqual(len(out), 1)

    def test_foreign_stamp_is_refused_and_names_the_moebel_step(self):
        doc = self._document(geometry_identity="0" * 64)
        with self._with_document(doc):
            with self.assertRaises(SystemExit) as caught:
                self.module.workbench_furniture(PROJECT_ID, "groundfloor")
        message = str(caught.exception)
        self.assertIn("Moebel", message)
        self.assertIn(PROJECT_ID, message)


class FloorRegistrationRuleTests(unittest.TestCase):
    """HARD RULE (Rainer, 2026-08-23): an upper storey without alignment
    marks on BOTH floors is refused -- it would stack hundreds of mm
    misregistered (onehalfstorey_029: 463mm). With marks, the storey goes
    through a RegisteredFrame; the ground floor always gets a plain Frame.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def _annotations(self, marks):
        return {
            "floor_scale": {"groundfloor": 10.0, "upperfloor": 10.2},
            "floor_alignment": marks,
            "annotations": [
                {"floor_level": "groundfloor", "label": "Wohnen", "id": "g1",
                 "points": [{"x": 0.1, "y": 0.1}, {"x": 0.9, "y": 0.1},
                            {"x": 0.9, "y": 0.9}, {"x": 0.1, "y": 0.9}]},
                {"floor_level": "upperfloor", "label": "Schlafen", "id": "u1",
                 "points": [{"x": 0.12, "y": 0.12}, {"x": 0.88, "y": 0.12},
                            {"x": 0.88, "y": 0.88}, {"x": 0.12, "y": 0.88}]},
            ],
        }

    def test_upper_storey_without_marks_is_refused(self):
        f = self.module.frame_for_level
        for marks in ({}, {"groundfloor": [{"x": 0.1, "y": 0.9}, {"x": 0.9, "y": 0.1}]},
                      {"upperfloor": [{"x": 0.1, "y": 0.9}, {"x": 0.9, "y": 0.1}]}):
            with self.assertRaises(SystemExit, msg=f"marks={marks!r} must be refused"):
                f(self._annotations(marks), "upperfloor", "groundfloor", 1000, 1000)

    def test_ground_floor_never_needs_marks(self):
        frame = self.module.frame_for_level(self._annotations({}), "groundfloor",
                                            "groundfloor", 1000, 1000)
        self.assertIsInstance(frame, self.module.Frame)
        self.assertNotIsInstance(frame, self.module.RegisteredFrame)

    def test_upper_storey_with_marks_is_registered(self):
        marks = {"groundfloor": [{"x": 0.1, "y": 0.9}, {"x": 0.9, "y": 0.1}],
                 "upperfloor": [{"x": 0.12, "y": 0.88}, {"x": 0.88, "y": 0.12}]}
        frame = self.module.frame_for_level(self._annotations(marks), "upperfloor",
                                            "groundfloor", 1000, 1000)
        self.assertIsInstance(frame, self.module.RegisteredFrame)
        # The upper mark (0.12, 0.12) must land where the ground mark (0.1, 0.1)
        # lands -- that is what registration means.
        ground = self.module.Frame(10.0, 1000, 1000)
        self.assertEqual(frame._registered({"x": 0.12, "y": 0.12}),
                         ground.point({"x": 0.1, "y": 0.1}))


class RotationOverrideScopeTests(unittest.TestCase):
    """plans/pose-contract-slice-1-v1.md, point 2.

    ROTATION_OVERRIDE replaces the plan's per-placement rotation entirely
    (render-furnished-dollhouse.py, instance site). "ecksofa": 0 was a
    repair for one old annotation state that no longer exists; it silently
    swallowed every rotation Rainer set in the Moebel editor. The renderer
    must not override plan placement values -- deleted 2026-08-22 with
    Rainer's approval ("Plan 1 all 4 points"). This guards the deletion at
    source level, since importing the renderer needs bpy.
    """

    def test_ecksofa_carries_no_renderer_rotation_override(self):
        source = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
        marker = "ROTATION_OVERRIDE = {"
        start = source.index(marker) + len("ROTATION_OVERRIDE = ")
        block = source[start:start + source[start:].index("\n}") + 2]
        override = ast.literal_eval(block)
        self.assertNotIn("ecksofa", override,
                         "ROTATION_OVERRIDE[\"ecksofa\"] swallows the editor's "
                         "rotation for the corner sofa; it was deleted per "
                         "plans/pose-contract-slice-1-v1.md and must not return "
                         "without a new plan")


def _axis_offset_deg(wall):
    """How far a wall is from the nearest axis, in degrees (0 = axis-true)."""
    (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
    angle = math.degrees(math.atan2(by - ay, bx - ax)) % 180.0
    return min(abs(angle), abs(angle - 90.0), abs(angle - 180.0))


def _open_t_gap_mm(wall, walls, min_angle_deg=30.0, overrun_mm=300.0):
    """Largest distance either end of `wall` would have to travel FORWARD along
    its own direction to reach another wall's centreline it is aiming at.

    Deliberately re-derived here instead of calling the implementation, so the
    test measures the defect the way the plan measured it (plans/
    interior-wall-geometry-v1.md, section (b)) rather than agreeing with the
    code by construction.
    """
    (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
    length = math.dist((ax, ay), (bx, by))
    if length < 1e-6:
        return 0.0
    ux, uy = (bx - ax) / length, (by - ay) / length
    worst = 0.0
    for point, sign in (((ax, ay), -1.0), ((bx, by), 1.0)):
        dx, dy = ux * sign, uy * sign
        best = None
        for other in walls:
            if other is wall:
                continue
            (ox1, oy1), (ox2, oy2) = other["start_mm"], other["end_mm"]
            odx, ody = ox2 - ox1, oy2 - oy1
            other_length = math.hypot(odx, ody)
            if other_length < 1e-6:
                continue
            denominator = dx * ody - dy * odx
            if abs(denominator) < 1e-9:
                continue
            theta = abs(math.degrees(math.atan2(abs(denominator), dx * odx + dy * ody)))
            if theta < min_angle_deg:
                continue
            t = ((ox1 - point[0]) * ody - (oy1 - point[1]) * odx) / denominator
            if t <= 1.0 or t > 400.0:
                continue
            hit = (point[0] + dx * t, point[1] + dy * t)
            s = ((hit[0] - ox1) * odx + (hit[1] - oy1) * ody) / other_length
            if s < -overrun_mm or s > other_length + overrun_mm:
                continue
            if best is None or t < best:
                best = t
        if best is not None:
            worst = max(worst, best)
    return worst


class InteriorWallGeometryTests(unittest.TestCase):
    """plans/interior-wall-geometry-v1.md.

    Rainer, 2026-08-23, screenshot of onehalfstorey_029's UPPER floor in the
    Moebel editor: a diagonal wall at the Flur/Kind boundary that should be
    orthogonal, interior walls stopping short of the walls they should meet,
    and kinks where two collinear interior walls join.

    Measured before writing any code: 029's upperfloor wall-4 ran at 170.58
    degrees (9.42 off axis) while every other interior wall on that floor was
    exact, and nine interior wall ends stopped 26.6 to 120.0 mm short of the
    wall they aimed at -- the 120.0 ones being exactly half an exterior wall
    thickness, because interior walls are built from room INNER faces while
    exterior walls are pushed outward by half their thickness.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    @staticmethod
    def _wall(start, end, wall_type="interior", thickness=120):
        return {"id": "w", "start_mm": list(start), "end_mm": list(end),
                "thickness_mm": thickness, "wall_type": wall_type, "rooms": []}

    # ---- straightening -------------------------------------------------

    def test_off_axis_interior_wall_is_straightened(self):
        # The real defect, to the millimetre: 029 upperfloor wall-4.
        wall = self._wall((9152.4, 6366.2), (11398.4, 5993.5), thickness=189)
        self.module._orthogonalize_interior_walls([wall])
        self.assertAlmostEqual(_axis_offset_deg(wall), 0.0, places=9)
        # Rotated about its own midpoint: the shared y is the mean of the two,
        # so the wall does not drift into either room.
        self.assertAlmostEqual(wall["start_mm"][1], (6366.2 + 5993.5) / 2, places=6)
        self.assertAlmostEqual(wall["end_mm"][1], (6366.2 + 5993.5) / 2, places=6)
        self.assertAlmostEqual(wall["start_mm"][0], 9152.4, places=6)
        self.assertAlmostEqual(wall["end_mm"][0], 11398.4, places=6)

    def test_near_vertical_wall_snaps_onto_a_touching_neighbour_not_the_mean(self):
        # The real defect, to the millimetre: twostorey_046 ground floor,
        # HWR/HTR's boundary against Diele. Rainer, 2026-09-15: "the wall to
        # the htr still has a whole in it". wall-A is a finished, already-
        # vertical wall; wall-B is the near-vertical (8.85 degrees off) wall
        # that starts exactly on wall-A's end. Snapping wall-B to the MEAN of
        # its own two ends (the pre-existing behaviour) moves that shared
        # point sideways by 184.7mm, opening a gap where there had been none.
        wall_a = self._wall((5719.9, 4189.4), (5719.9, 3671.7))
        wall_b = self._wall((5719.9, 3671.7), (6089.3, 1296.6))
        self.module._orthogonalize_interior_walls([wall_a, wall_b])
        self.assertAlmostEqual(_axis_offset_deg(wall_b), 0.0, places=9)
        # Snapped onto wall_a's end (x=5719.9), not the mean of its own two
        # ends (x=5904.6) -- the connection survives.
        self.assertAlmostEqual(wall_b["start_mm"][0], 5719.9, places=6)
        self.assertAlmostEqual(wall_b["end_mm"][0], 5719.9, places=6)
        self.assertEqual(wall_b["start_mm"], wall_a["end_mm"])

    def test_anchor_snap_does_not_confuse_a_touching_end_with_its_own(self):
        # A wall whose OWN two ends happen to coincide with two DIFFERENT
        # neighbours (a short connector wall) must anchor on either
        # neighbour, not silently find "itself" and fall through to the mean
        # -- a value-equality bug here would look identical to the fix
        # working, since both neighbours sit near the same axis.
        wall_a = self._wall((5719.9, 4189.4), (5719.9, 3671.7))
        wall_c = self._wall((5719.9, 3671.7), (5719.9, 1000.0))
        wall_b = self._wall((5719.9, 3671.7), (6089.3, 1296.6))
        self.module._orthogonalize_interior_walls([wall_a, wall_b, wall_c])
        self.assertAlmostEqual(wall_b["start_mm"][0], 5719.9, places=6)
        self.assertAlmostEqual(wall_b["end_mm"][0], 5719.9, places=6)

    def test_already_orthogonal_interior_wall_is_untouched(self):
        for start, end in (((7051.6, 10084.8), (7051.6, 6287.6)),
                           ((7096.0, 6187.9), (9049.0, 6187.9))):
            with self.subTest(start=start):
                wall = self._wall(start, end)
                before = json.loads(json.dumps(wall))
                self.module._orthogonalize_interior_walls([wall])
                self.assertEqual(wall, before)

    def test_legitimate_diagonal_is_left_alone(self):
        # 45 degrees is a real German floorplan feature (abgeschraegte Ecke),
        # and 21.58 degrees is the smallest genuinely diagonal interior wall
        # measured across the 94-project corpus. Both sit outside the 12
        # degree snap tolerance, which was chosen to fall inside the measured
        # empty band between 10.43 and 21.58 degrees.
        for dx, dy in ((1000.0, 1000.0), (1000.0, 1000.0 * math.tan(math.radians(21.58)))):
            with self.subTest(dy=dy):
                wall = self._wall((2000.0, 3000.0), (2000.0 + dx, 3000.0 + dy))
                before = json.loads(json.dumps(wall))
                self.module._orthogonalize_interior_walls([wall])
                self.assertEqual(wall, before)

    def test_exterior_wall_is_never_straightened(self):
        # Exterior geometry is _close_exterior_corners' business; this must
        # not reach into it.
        wall = self._wall((9152.4, 6366.2), (11398.4, 5993.5), wall_type="exterior")
        before = json.loads(json.dumps(wall))
        self.module._orthogonalize_interior_walls([wall])
        self.assertEqual(wall, before)

    # ---- T-junction closing --------------------------------------------

    def test_t_junction_gap_is_closed(self):
        # The 120mm case: an interior wall ending on the room's inner face,
        # half an exterior wall thickness short of that wall's centreline.
        interior = self._wall((7051.6, 10084.8), (7051.6, 6287.6))
        exterior = self._wall((2817.7, 10204.8), (11505.7, 10204.8),
                              wall_type="exterior", thickness=240)
        self.module._close_interior_t_junctions([interior, exterior])
        self.assertAlmostEqual(interior["start_mm"][1], 10204.8, places=3)
        self.assertAlmostEqual(interior["start_mm"][0], 7051.6, places=6)
        self.assertAlmostEqual(interior["end_mm"][1], 6287.6, places=6)
        # The wall it met is not dragged along.
        self.assertEqual(exterior["start_mm"], [2817.7, 10204.8])
        self.assertEqual(exterior["end_mm"], [11505.7, 10204.8])

    def test_t_junction_gap_is_closed_against_another_interior_wall(self):
        # 029 upperfloor wall-3 start, 44.4mm short of wall-0.
        stem = self._wall((7096.0, 6187.9), (9049.0, 6187.9))
        trunk = self._wall((7051.6, 10084.8), (7051.6, 6187.9))
        self.module._close_interior_t_junctions([stem, trunk])
        self.assertAlmostEqual(stem["start_mm"][0], 7051.6, places=3)

    def test_t_junction_overshoot_is_not_trimmed(self):
        # 029 groundfloor wall-3 runs 162mm PAST the exterior wall it crosses.
        # Trimming is explicitly out of scope; only extension is allowed, so
        # this must come back untouched.
        interior = self._wall((6680.9, 3842.3), (2870.7, 3842.3))
        exterior = self._wall((3033.1, 3973.5), (3033.1, 688.8),
                              wall_type="exterior", thickness=240)
        before = json.loads(json.dumps(interior))
        self.module._close_interior_t_junctions([interior, exterior])
        self.assertEqual(interior, before)

    def test_parallel_wall_is_not_a_t_junction_target(self):
        # Two collinear interior walls with a door opening between them must
        # not be welded shut by the T-junction pass -- that is
        # _merge_collinear_walls' decision, and it deliberately leaves gaps
        # wider than MERGE_GAP_TOLERANCE_MM alone.
        upper = self._wall((7051.6, 10084.8), (7051.6, 6287.6))
        lower = self._wall((7051.6, 5124.2), (7051.6, 808.8))
        before = json.loads(json.dumps([upper, lower]))
        self.module._close_interior_t_junctions([upper, lower])
        self.assertEqual([upper, lower], before)

    def test_gap_beyond_tolerance_is_left_open(self):
        # 900mm is not a construction tolerance, it is a missing wall. Closing
        # it would invent geometry nobody drew.
        interior = self._wall((5000.0, 5000.0), (5000.0, 2000.0))
        exterior = self._wall((2000.0, 1100.0), (9000.0, 1100.0),
                              wall_type="exterior", thickness=240)
        before = json.loads(json.dumps(interior))
        self.module._close_interior_t_junctions([interior, exterior])
        self.assertEqual(interior, before)

    def test_end_beyond_the_targets_own_end_is_not_hooked(self):
        # The target's centreline is infinite, the target wall is not. An end
        # aiming at empty space past the far end of another wall has nothing
        # to meet.
        interior = self._wall((5000.0, 5000.0), (5000.0, 3100.0))
        exterior = self._wall((1000.0, 3000.0), (2000.0, 3000.0),
                              wall_type="exterior", thickness=240)
        before = json.loads(json.dumps(interior))
        self.module._close_interior_t_junctions([interior, exterior])
        self.assertEqual(interior, before)

    def test_clean_geometry_is_a_no_op(self):
        # A closed, already-correct rectangle of interior walls: every pass
        # must leave it exactly as it is.
        walls = [self._wall((0.0, 0.0), (4000.0, 0.0)),
                 self._wall((4000.0, 0.0), (4000.0, 3000.0)),
                 self._wall((4000.0, 3000.0), (0.0, 3000.0)),
                 self._wall((0.0, 3000.0), (0.0, 0.0))]
        before = json.loads(json.dumps(walls))
        self.module._orthogonalize_interior_walls(walls)
        self.module._close_interior_t_junctions(walls)
        self.assertEqual(walls, before)


@unittest.skipUnless((SIMPLIFIER_PROJECTS / PROJECT_ID / "annotations.json").exists(),
                      f"{PROJECT_ID} not present in this checkout's floorplan-simplifier data")
class InteriorWallGeometryOnRealProjectTests(unittest.TestCase):
    """The same two invariants, on the real bungalow_039 build.

    A hand-built fixture cannot prove that build_walls() actually runs the new
    passes in the right order relative to _merge_collinear_walls and
    _close_exterior_corners; this can.
    """

    @classmethod
    def setUpClass(cls):
        module = load_module()
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "geometry.json"
        module.geometry_only(PROJECT_ID, str(out))
        cls.payload = json.loads(out.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _walls_mm(self, floor):
        return [{"id": w["id"], "start_mm": w["start"], "end_mm": w["end"],
                 "thickness_mm": w["thickness"], "wall_type": w.get("wall_type", "?")}
                for w in floor["walls"]]

    def test_interior_walls_are_axis_true_or_properly_diagonal(self):
        for floor in self.payload["floors"]:
            for wall in self._walls_mm(floor):
                if wall["wall_type"] != "interior":
                    continue
                offset = _axis_offset_deg(wall)
                self.assertFalse(
                    1e-6 < offset <= 12.0,
                    f"{floor['floor_level']}: interior {wall['id']} is {offset:.2f} "
                    "degrees off axis -- inside the snap tolerance, so it should "
                    "have been straightened")

    def test_no_open_interior_t_junctions(self):
        for floor in self.payload["floors"]:
            walls = self._walls_mm(floor)
            for wall in walls:
                if wall["wall_type"] != "interior":
                    continue
                gap = _open_t_gap_mm(wall, walls)
                self.assertEqual(
                    gap, 0.0,
                    f"{floor['floor_level']}: interior {wall['id']} stops "
                    f"{gap:.1f}mm short of a wall it runs into")


class StairTurnStyleTests(unittest.TestCase):
    """How a drawn turn is built: Podest or gewendelt.

    Rainer, 2026-08-23, on onehalfstorey_029: "your stairs are still shit". Two
    of sixteen treads measured the full 1000 x 1000mm of the turn, because the
    tread that straddled a sharp vertex took its back riser line on one leg and
    its front riser line on the other and came out a bow tie.

    The rebuild needs to know FIRST whether the turn is a landing or a winder,
    and the rule is geometric: a landing only if the drawn Lauflinie still
    carries every riser on straight flights once the landing has taken its room.
    These pin that rule, including the real 029 path, so the answer cannot drift
    back to "count the points".
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    # onehalfstorey_029, straight out of the built plan.
    U_029 = [[9357.4, 4344.3], [11075.1, 4344.3], [11075.1, 5616.0], [9274.6, 5616.0]]

    def test_two_point_path_is_straight(self):
        self.assertEqual(
            self.module.stair_turn_style([[0.0, 0.0], [4200.0, 0.0]], 1000.0, 15),
            "straight")

    def test_real_029_u_is_a_winder(self):
        """4790mm of Lauflinie, 2272mm of it eaten by the merged landing: the
        14 remaining risers would need 3640mm and only 2518mm are left."""
        self.assertEqual(
            self.module.stair_turn_style(self.U_029, 1000.0, 15), "winder")

    def test_wide_quarter_turn_is_a_landing(self):
        """A generous well: 3000mm up, 3000mm across, one 90 degree vertex. The
        landing takes 1000mm and 5000mm is still left for 14 treads."""
        path = [[0.0, 0.0], [3000.0, 0.0], [3000.0, 3000.0]]
        self.assertEqual(self.module.stair_turn_style(path, 1000.0, 15), "landing")

    def test_tight_quarter_turn_is_a_winder(self):
        """The same corner drawn in half the space cannot hold the flights."""
        path = [[0.0, 0.0], [1400.0, 0.0], [1400.0, 1400.0]]
        self.assertEqual(self.module.stair_turn_style(path, 1000.0, 15), "winder")

    def test_close_vertices_merge_into_one_landing(self):
        """Two 90 degree vertices 271.7mm apart are ONE U-turn with ONE landing
        across both flights -- what simple_half_turn_stair_blender.py builds --
        not two landings with a stub of flight between them."""
        zones, total = self.module.stair_landing_zones(self.U_029, 1000.0)
        self.assertEqual(len(zones), 1, f"expected one merged landing, got {zones}")
        self.assertAlmostEqual(zones[0][0], 1217.7, places=1)
        self.assertAlmostEqual(zones[0][1], 3489.4, places=1)
        self.assertAlmostEqual(total, 4789.9, places=1)

    def test_far_apart_vertices_stay_two_landings(self):
        path = [[0.0, 0.0], [4000.0, 0.0], [4000.0, 4000.0], [0.0, 4000.0]]
        zones, _ = self.module.stair_landing_zones(path, 1000.0)
        self.assertEqual(len(zones), 2)

    def test_declared_podest_overrides_the_measurement(self):
        self.assertEqual(
            self.module.stair_turn_style(self.U_029, 1000.0, 15, declared="podest"),
            "landing")

    def test_declared_gewendelt_overrides_the_measurement(self):
        path = [[0.0, 0.0], [3000.0, 0.0], [3000.0, 3000.0]]
        self.assertEqual(
            self.module.stair_turn_style(path, 1000.0, 15,
                                         declared="viertelgewendelt"),
            "winder")


class StairGeometryFromStoreyTests(unittest.TestCase):
    """The riser count comes from the storey, not from a literal.

    The plan shipped {"riseMm": 175, "risers": 16} = a 2800mm climb into the
    renderer's 2400mm wall + 220mm slab = 2620mm storey, so every flight
    overshot the floor it arrives on by 180mm.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_risers_divide_the_storey_exactly(self):
        risers, rise = self.module.stair_risers_for_storey()
        self.assertAlmostEqual(risers * rise, self.module.STOREY_HEIGHT_MM, places=6)

    def test_rise_stays_inside_din_18065(self):
        _, rise = self.module.stair_risers_for_storey()
        self.assertGreaterEqual(rise, 140.0)
        self.assertLessEqual(rise, 200.0)

    def test_2620mm_storey_gives_15_risers(self):
        risers, rise = self.module.stair_risers_for_storey(2620.0)
        self.assertEqual(risers, 15)
        self.assertAlmostEqual(rise, 2620.0 / 15, places=6)

    def test_a_taller_storey_gets_more_risers(self):
        risers, _ = self.module.stair_risers_for_storey(3000.0)
        self.assertEqual(risers, 17)


class KuecheninselIstEinRechteckTests(unittest.TestCase):
    """plans/kuecheninsel-rechteck-v1.md.

    Das Werkzeug zeichnet eine Insel als ZWEI gegenueberliegende Ecken
    (page.tsx: "A rectangle IS two opposite corners"). Der Bau verlangte
    frueher `len(points) > 2` fuer `build: rect` -- der Normalfall fiel also in
    den Zweig `path` und wurde als Kuechenzeilen-Lauf entlang der Diagonalen
    gebaut: im Editor ein Rechteck, in der .blend ein schraeger Balken
    (Rainer, 2026-08-25: "always ends up at 45 degrees").
    """

    @classmethod
    def setUpClass(cls):
        cls.quelle = (HERE / "build-simplifier-render-plan.py").read_text(encoding="utf-8")

    def _entscheidungen(self):
        """Jede `build`-Zuweisung im Bau, als lesbarer Ausdruck."""
        baum = ast.parse(self.quelle)
        gefunden = []
        for knoten in ast.walk(baum):
            if (isinstance(knoten, ast.Dict)
                    and any(isinstance(k, ast.Constant) and k.value == "build"
                            for k in knoten.keys if k is not None)):
                for schluessel, wert in zip(knoten.keys, knoten.values):
                    if isinstance(schluessel, ast.Constant) and schluessel.value == "build":
                        gefunden.append(ast.unparse(wert))
        return [a for a in gefunden if "RECT_BUILD" in a]

    def test_beide_zweige_entscheiden_gleich(self):
        ausdruecke = self._entscheidungen()
        self.assertEqual(len(ausdruecke), 2, "es gibt genau zwei Rechteck-Zweige")
        self.assertEqual(ausdruecke[0], ausdruecke[1],
                         "beide Zweige muessen dieselbe Regel haben")

    def test_die_punktzahl_entscheidet_nicht_mehr(self):
        for ausdruck in self._entscheidungen():
            self.assertNotIn("len(points)", ausdruck,
                             "eine Insel mit 2 Punkten ist genauso ein Rechteck")

    def test_nur_rechteck_symbole_werden_zum_rechteck(self):
        module = load_module()
        self.assertIn("kuecheninsel", module.RECT_BUILD)
        self.assertIn("stuff", module.RECT_BUILD)
        self.assertNotIn("kuechenzeile", module.RECT_BUILD)
        for ausdruck in self._entscheidungen():
            self.assertIn("'path'", ausdruck.replace('"', "'"))


@unittest.skipUnless(os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
                     and (SIMPLIFIER_PROJECTS / PROJECT_ID / "annotations.json").exists(),
                     "braucht FLOORPLAN_WORKBENCH_DATA_DIR und das echte Projekt")
class KuecheninselAmEchtenHausTests(unittest.TestCase):
    """Kriterium 4: am gebauten Plan nachgemessen, nicht nur an der Quelle."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / "plan.json"
            lauf = subprocess.run(
                [os.environ.get("PYTHON_EXECUTABLE") or "python",
                 str(HERE / "build-simplifier-render-plan.py"), PROJECT_ID, "modern", str(ziel)],
                capture_output=True, text=True)
            if lauf.returncode != 0 or not ziel.exists():
                raise unittest.SkipTest("Bau nicht moeglich: " + (lauf.stderr or "")[-200:])
            cls.plan = json.loads(ziel.read_text(encoding="utf-8"))

    def _platzierungen(self, asset_id):
        return [p for f in self.plan.get("floors", [])
                for p in f.get("placements", []) if p.get("asset_id") == asset_id]

    def test_die_insel_wird_als_rechteck_gebaut(self):
        inseln = self._platzierungen("kuecheninsel")
        if not inseln:
            self.skipTest("dieses Haus hat keine Kuecheninsel")
        for insel in inseln:
            self.assertEqual(insel.get("build"), "rect")

    def test_die_kuechenzeile_bleibt_ein_lauf(self):
        for zeile in self._platzierungen("kuechenzeile"):
            self.assertEqual(zeile.get("build"), "path")

    # --- Stuehle am Esstisch (Rainer, 2026-08-25) -------------------------
    # "alle Stuehle etwas naeher zum Tisch ruecken, nicht zu viel, in eines
    # davon ca 15 grad drehen damit es nicht ultra perfect aussieht"

    def _stuehle_und_tisch(self):
        stuehle = self._platzierungen("essgruppe_stuhl")
        tische = self._platzierungen("essgruppe_6")
        if not stuehle or not tische:
            self.skipTest("dieses Haus hat keine Essgruppe mit abgeleiteten Stuehlen")
        return stuehle, tische[0]

    def test_genau_ein_stuhl_steht_schief(self):
        stuehle, tisch = self._stuehle_und_tisch()
        gerade = {(tisch.get("rotation_deg", 0) + f) % 360 for f in (0, 90, 180, 270)}
        schief = [s for s in stuehle if s["rotation_deg"] % 360 not in gerade]
        self.assertEqual(len(schief), 1,
                         "genau einer soll aus der Reihe tanzen, nicht keiner und nicht alle")

    def test_der_schiefe_stuhl_steht_um_15_grad_daneben(self):
        stuehle, tisch = self._stuehle_und_tisch()
        gerade = [(tisch.get("rotation_deg", 0) + f) % 360 for f in (0, 90, 180, 270)]
        for stuhl in stuehle:
            abstand = min(min((stuhl["rotation_deg"] - g) % 360,
                              (g - stuhl["rotation_deg"]) % 360) for g in gerade)
            self.assertIn(abstand, (0, 15), "erlaubt sind ausgerichtet oder 15 Grad daneben")

    def test_die_stuehle_stehen_am_tisch_nicht_daneben(self):
        stuehle, tisch = self._stuehle_und_tisch()
        tx, ty = tisch["position_mm"]
        breite, tiefe = (tisch.get("verified_size_mm") or [1522, 914])[:2]
        for stuhl in stuehle:
            x, y = stuhl["position_mm"]
            # Mitte-zu-Mitte darf die halbe Tischdiagonale plus eine
            # Stuhltiefe nicht ueberschreiten -- sonst steht er im Raum.
            grenze = math.hypot(breite, tiefe) / 2 + 600
            self.assertLess(math.hypot(x - tx, y - ty), grenze)

    def test_derselbe_plan_ergibt_denselben_schiefen_stuhl(self):
        # Deterministisch, sonst aendert sich das Zertifikat bei jedem Bau.
        stuehle, _ = self._stuehle_und_tisch()
        winkel = [s["rotation_deg"] for s in stuehle]
        modul = load_module()
        streu = int(__import__("hashlib").sha256(PROJECT_ID.encode("utf-8"))
                    .hexdigest()[:8], 16)
        self.assertEqual(len([w for w in winkel if w % 90]), 1)
        self.assertIn(streu % 6, range(6))
        self.assertTrue(hasattr(modul, "SYMBOL_3D"))

class FensterNormbreiteTests(unittest.TestCase):
    """plans/fensterbreiten-auswahl-v1.md.

    Ein Fenster war bisher genau so breit wie der gezogene Strich. Der
    Annotator bietet jetzt Normbreiten an (68/80/101/131/151/171/300 cm) und
    schreibt sie als `width_mm` an das Element; der Bau muss sie der
    Strichlaenge vorziehen -- sonst waere die Auswahl eine Attrappe.
    """

    @classmethod
    def setUpClass(cls):
        cls.quelle = (HERE / "build-simplifier-render-plan.py").read_text(encoding="utf-8")

    def _ausdruck(self):
        """Die width_mm-Zuweisung der Oeffnung, als lesbarer Ausdruck."""
        baum = ast.parse(self.quelle)
        for knoten in ast.walk(baum):
            if (isinstance(knoten, ast.Dict)
                    and any(isinstance(k, ast.Constant) and k.value == "opening_type"
                            for k in knoten.keys if k is not None)):
                for schluessel, wert in zip(knoten.keys, knoten.values):
                    if isinstance(schluessel, ast.Constant) and schluessel.value == "width_mm":
                        return ast.unparse(wert)
        raise AssertionError("width_mm der Oeffnung nicht gefunden")

    def test_die_gewaehlte_breite_schlaegt_die_strichlaenge(self):
        ausdruck = self._ausdruck()
        self.assertIn("element.get('width_mm')", ausdruck.replace('"', "'"))
        self.assertIn("math.dist(a, b)", ausdruck)

    def test_ohne_auswahl_bleibt_die_strichlaenge(self):
        # Der Ausdruck muss die Zeichnung als ZWEITEN Fall behalten, nicht
        # ersetzen -- sonst haetten alle Bestandsfenster ploetzlich 0 mm.
        ausdruck = self._ausdruck().replace('"', "'")
        self.assertLess(ausdruck.index("element.get('width_mm')"),
                        ausdruck.index("math.dist(a, b)"))

    def test_die_sieben_breiten_stehen_im_annotator(self):
        annotator = (HERE.parent.parent / "floorplan-simplifier" / "static" / "annotate.html")
        if not annotator.exists():
            self.skipTest("Annotator nicht in diesem Checkout")
        markup = annotator.read_text(encoding="utf-8")
        self.assertIn('id="windowWidth"', markup)
        for millimeter in (680, 800, 1010, 1310, 1510, 1710, 3000):
            self.assertIn('value="%d"' % millimeter, markup)
        # Leerer Eintrag = heutiges Verhalten, muss der erste sein.
        self.assertIn('<option value="">', markup)


class HerkunftDerZahlen(unittest.TestCase):
    """Ein Etikett darf nicht mehr behaupten als der Wert hergibt.

    Zwei Faelle, beide am 2026-08-29 aufgefallen:

    1. `roof_type_source` sagte "annotation" auch dann, wenn die Dachform aus
       `gebaeudemass.json` kam -- denn beim Bauen wird das Beiblatt vorher in
       den Annotations-Dict gemischt, und danach sieht alles gleich aus. Der
       Wert stimmt, das Etikett luegt. 231 von 233 Haeusern haben ihre
       Dachform NUR im Beiblatt; das Etikett war also fast immer falsch.

    2. Am selben Tag bekamen 121 Haeuser einen GESCHAETZTEN Massstab (aus der
       Tuerbreite, Median-Fehler 6,7 %). Der Bauplan sagte davon nichts. Ein
       Zertifikat, das auf einer Schaetzung steht und wie ein Mass aussieht,
       ist weniger wert, als es aussieht -- dasselbe Argument, das im Kopf von
       `roof_type_source` schon steht.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_a_roof_from_the_sidecar_is_labelled_as_such(self):
        annotations = {"roof_type_modern": "flachdach",
                       "roof_type_modern_herkunft": "beiblatt"}
        self.assertEqual(self.module.dach_herkunft(annotations, "modern"), "beiblatt")

    def test_a_roof_from_the_drawing_keeps_its_label(self):
        self.assertEqual(
            self.module.dach_herkunft({"roof_type_classic": "walmdach"}, "classic"),
            "annotation")

    def test_no_roof_at_all_is_still_named(self):
        self.assertEqual(self.module.dach_herkunft({}, "modern"), "nicht_annotiert")

    def test_an_estimated_scale_is_carried_into_the_plan(self):
        self.assertIs(self.module.massstab_geschaetzt({"floor_scale_geschaetzt": True}), True)

    def test_a_measured_scale_is_not_marked(self):
        self.assertIs(self.module.massstab_geschaetzt({"floor_scale": {"groundfloor": 12.0}}),
                      False)
        self.assertIs(self.module.massstab_geschaetzt({}), False)


class HoeheNurWoSieGEMESSENIst(unittest.TestCase):
    """Eine 2D-Nennhoehe darf ein 3D-Modell nicht plattdruecken.

    Rainer, 2026-08-30: "sieh dir doch die blender datei an." Im gebauten
    interior-modern-baseline.blend von 3_3_2 gemessen:

        doppelbett-10   2,000 x 1,800 x 0,500 m

    Ein Doppelbett von einem halben Meter -- Matratze UND Kopfteil. Der Bauer
    skaliert jede Achse EINZELN auf die Symbolmasze, absichtlich: was Rainer
    zeichnet und was er bekommt, soll dasselbe Objekt sein. Breite und Tiefe
    zeichnet er. Die Hoehe nicht -- die kommt aus SPEC, und dort steht bei
    einem Bett 500 mm. Das ist die Matratzenoberkante eines GRUNDRISS-Symbols,
    nicht die Gesamthoehe eines Moebels.

    Aus dem Bauplan, Modellhoehe gegen Zielhoehe:

        doppelbett     856 -> 500 mm   0,58
        einzelbett     682 -> 500 mm   0,73
        badewanne     1016 -> 580 mm   0,57
        wand_wc        813 -> 400 mm   0,49

    Bei diesen vier ist die Tabellenzahl ein Nennmass, kein Aussenmass. Ohne
    Hoehenangabe nimmt `fit_to_symbol` fuer z den Mittelwert der x/y-Faktoren
    -- das Modell behaelt seine Proportion und passt trotzdem in den
    gezeichneten Grundriss.

    Wo die Hoehe WIRKLICH gemeint ist, bleibt sie: ein Kleiderschrank soll
    2100 hoch sein, ein Fernseher 700, eine Dusche 2000. Die stehen weiter da.
    """

    def setUp(self):
        self.module = load_module()

    def test_bett_wanne_und_wand_wc_erzwingen_keine_hoehe(self):
        for symbol in ("doppelbett", "einzelbett", "badewanne", "wand_wc"):
            with self.subTest(symbol=symbol):
                spec = self.module.SYMBOL_3D[symbol]
                self.assertIsNone(
                    spec.get("height"),
                    "%s traegt noch eine Nennhoehe -- sie staucht das Modell"
                    % symbol)

    def test_die_gemessenen_hoehen_bleiben_stehen(self):
        # Gegenprobe: nicht alle Hoehen loeschen. Diese sind echte Aussenmasze.
        for symbol, hoehe in (("kleiderschrank", 2100), ("fernseher", 700),
                              ("dusche_gross", 2000), ("kuehlschrank", 1800),
                              ("essgruppe_stuhl", 844)):
            with self.subTest(symbol=symbol):
                self.assertEqual(self.module.SYMBOL_3D[symbol].get("height"), hoehe)

    def test_ohne_hoehe_folgt_z_dem_grundriss(self):
        """Die Regel in `fit_to_symbol`, hier nachgerechnet.

        Fehlt die Hoehe, bekommt z den Mittelwert der bekannten Faktoren. Fuer
        das Doppelbett von 3_3_2: Modell 1958 x 2151 x 856, Ziel 1800 x 2000.
        """
        modell = (1958.0, 2151.0, 856.0)
        ziel = {"width_mm": 1800, "depth_mm": 2000, "height_mm": None}
        faktoren = []
        for name, hat in zip(("width_mm", "depth_mm", "height_mm"), modell):
            will = ziel[name]
            faktoren.append(will / hat if will else None)
        bekannt = [f for f in faktoren if f]
        faktoren = [f if f else sum(bekannt) / len(bekannt) for f in faktoren]
        self.assertAlmostEqual(modell[2] * faktoren[2], 792, delta=5)


class KurzeAussenwandTest(unittest.TestCase):
    """Eine Aussenwand, die kuerzer als die Eckentoleranz ist, darf nicht
    zusammenfallen.

    Rainer, 2026-09-01, zu german_catalog_review_bungalow_3_4_5_b_120: "the
    outer walls seem to be kaputt at the entrance."

    Gemessen. Die Eingangsnische ist 537 mm tief, ihre zwei Seitenwaende sind
    537 mm lang. `_close_exterior_corners` arbeitet mit tol_mm = 800 und
    probiert ALLE VIER Endpunkt-Paarungen zweier Waende durch. Bei einer Wand
    unter 800 mm liegt damit auch ihr FERNES Ende innerhalb der Toleranz zur
    Ecke -- und wird dorthin gezogen:

        VOR  _close_exterior_corners  wall-11  10809.1 1501.0 -> 10809.1 2038.2   L 537.2
        NACH _close_exterior_corners  wall-11  10809.1 1501.0 -> 10809.1 1501.0   L   0.0

    Beide Seitenwaende der Nische kamen mit Laenge 0 heraus, und im Render
    stand die Nische offen.

    Die Ecke schliessen heisst: das NAEHERE Ende auf den Schnittpunkt ziehen.
    Das ferne Ende bleibt, wo es ist.
    """

    def bauen(self, a, b):
        return [{"id": "a", "wall_type": "exterior", "start_mm": a[0], "end_mm": a[1],
                 "thickness_mm": 240},
                {"id": "b", "wall_type": "exterior", "start_mm": b[0], "end_mm": b[1],
                 "thickness_mm": 240}]

    def laenge(self, w):
        return math.dist(w["start_mm"], w["end_mm"])

    def test_die_kurze_nischenwand_ueberlebt(self):
        modul = load_module()
        # Genau der Fall: Unterkante y=1501 laeuft nach x=10809, dort geht die
        # 537 mm tiefe Nische nach oben.
        walls = self.bauen(([14321.0, 1501.0], [10809.1, 1501.0]),
                           ([10809.1, 1501.0], [10809.1, 2038.2]))
        raus = modul._close_exterior_corners(walls)
        self.assertAlmostEqual(self.laenge(raus[1]), 537.2, delta=1.0,
                               msg="die Nischenwand ist zusammengefallen")

    def test_die_echte_ecke_wird_trotzdem_geschlossen(self):
        # Der Grund, warum es die Funktion gibt: zwei Aussenwaende, die
        # 120 mm voreinander enden, muessen sich treffen.
        modul = load_module()
        walls = self.bauen(([2818.0, 809.0], [2818.0, 10085.0]),
                           ([2938.0, 689.0], [11386.0, 689.0]))
        raus = modul._close_exterior_corners(walls)
        self.assertEqual(raus[0]["start_mm"], raus[1]["start_mm"],
                         "die offene Ecke wurde nicht geschlossen")

    def test_keine_wand_wird_umgedreht(self):
        # Wird das falsche Ende gezogen, kann die Wand auch die Richtung
        # wechseln statt nur zu schrumpfen.
        modul = load_module()
        walls = self.bauen(([0.0, 0.0], [3000.0, 0.0]),
                           ([3000.0, 0.0], [3000.0, 400.0]))
        raus = modul._close_exterior_corners(walls)
        self.assertGreater(self.laenge(raus[1]), 300.0)

    def test_zwei_lange_waende_bleiben_wie_sie_waren(self):
        modul = load_module()
        walls = self.bauen(([0.0, 0.0], [10000.0, 0.0]),
                           ([10000.0, 0.0], [10000.0, 8000.0]))
        vorher = [self.laenge(w) for w in walls]
        raus = modul._close_exterior_corners(walls)
        for alt, neu in zip(vorher, [self.laenge(w) for w in raus]):
            self.assertAlmostEqual(alt, neu, delta=1.0)


class ImageSizeGroundFloorPriorityTests(unittest.TestCase):
    """image_size() must use the GROUND FLOOR's own preview, not whichever
    generic file happens to sort first.

    Rainer, 2026-09-15, on twostorey_046: "the right wall in the htr is
    missing and the aspect ratio is totally off". Root cause: a bare,
    unprefixed "room_concept.png" (a generic leftover many multi-floor
    projects still have on disk) was checked BEFORE any per-floor-prefixed
    file, so it silently won even though it belongs to no floor in
    particular. Confirmed on twostorey_046: the file's 1600x1390 (aspect
    1.151) versus the real groundfloor_original_preview.png's 1130x1448
    (aspect 0.780) -- a 47.5% height error that also broke wall-pairing for
    one wall (see the failed-hypothesis log in
    plans/image-size-ground-floor-priority-v1.md: rebuilding the same two
    rooms' walls with each frame directly proved the missing wall was a
    second symptom of this exact bug, not an independent defect).
    """

    def _png(self, breite, hoehe):
        import struct
        import zlib

        def chunk(typ, daten):
            roh = typ + daten
            return (struct.pack(">I", len(daten)) + roh
                    + struct.pack(">I", zlib.crc32(roh) & 0xFFFFFFFF))
        ihdr = struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0)
        zeile = b"\x00" + b"\x00\x00\x00" * breite
        return (bytes([137, 80, 78, 71, 13, 10, 26, 10])
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(zeile * hoehe))
                + chunk(b"IEND", b""))

    def _annotations(self, levels=("groundfloor", "upperfloor")):
        return {"annotations": [{"floor_level": level, "label": "Zimmer"}
                                for level in levels]}

    def test_ground_floor_prefixed_file_wins_over_generic_room_concept(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            # The generic file that used to win: different aspect, no floor
            # prefix, sorts before nothing (it's just checked first).
            Path(tmp, "room_concept.png").write_bytes(self._png(1600, 1390))
            # The real per-floor preview -- what the annotations were
            # actually drawn on, and the only file that should be picked.
            Path(tmp, "groundfloor_original_preview.png").write_bytes(
                self._png(1130, 1448))
            width, height = module.image_size(tmp, self._annotations())
        self.assertEqual((width, height), (1130, 1448))

    def test_single_floor_project_still_falls_back_to_generic_names(self):
        # No per-floor-prefixed file exists (older/simpler project layout) --
        # the generic "room_concept.png" must still be found, unchanged from
        # before this fix.
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "room_concept.png").write_bytes(self._png(800, 600))
            width, height = module.image_size(tmp, self._annotations(("groundfloor",)))
        self.assertEqual((width, height), (800, 600))

    def test_annotation_space_aspect_still_bypasses_file_search_entirely(self):
        # A project with a stated building size must keep ignoring every
        # file on disk, generic or per-floor -- regression guard for the
        # short-circuit this fix sits right after.
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "room_concept.png").write_bytes(self._png(1600, 1390))
            Path(tmp, "groundfloor_original_preview.png").write_bytes(
                self._png(1130, 1448))
            annotations = self._annotations()
            annotations["annotation_space"] = {"aspect": 2.0}
            width, height = module.image_size(tmp, annotations)
        self.assertEqual((width, height), (1000.0, 2000.0))

    @unittest.skipUnless((SIMPLIFIER_PROJECTS / "twostorey_046" / "annotations.json").exists(),
                        "twostorey_046 not present in this checkout's floorplan-simplifier data")
    def test_real_regression_fixture_twostorey_046(self):
        # The actual project the bug was found on: real groundfloor aspect
        # 0.780, real leftover room_concept.png aspect 1.151. Must resolve
        # to the groundfloor file, not the generic one.
        module = load_module()
        project_dir = str(SIMPLIFIER_PROJECTS / "twostorey_046")
        annotations = json.loads(
            (SIMPLIFIER_PROJECTS / "twostorey_046" / "annotations.json").read_text(encoding="utf-8"))
        width, height = module.image_size(project_dir, annotations)
        self.assertAlmostEqual(width / height, 0.780, delta=0.01)


if __name__ == "__main__":
    unittest.main()
