"""Exterior areas must be registered from the floor they were drawn on.

Rainer, 2026-09-21, twostorey_053: "why is the terasse going through the house
there is a missmatch in the tabs."

Both builder paths (annotation plan and corrected-revision plan) put EVERY
exterior area through the ground floor's Frame and never read `floor_level`.
An area drawn on the upper floor's image therefore landed in 3D off by scale
AND offset -- as soon as the annotator started saving the field (it dropped it
before 2026-09-21, so nothing was affected yet)."""
import importlib.util
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "build-simplifier-render-plan.py"))
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)

# ground: marks (0.2,0.2)/(0.8,0.8); upper: (0.1,0.1)/(0.5,0.9)
#   upper -> ground:  xg = 1.5 xu + 0.05      yg = 0.75 yu + 0.125
MARKS = {
    "groundfloor": [{"x": 0.2, "y": 0.2}, {"x": 0.8, "y": 0.8}],
    "upperfloor": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.9}],
}
AX, BX, AY, BY = 1.5, 0.05, 0.75, 0.125
GROUND_AREA = [{"x": 0.3, "y": 0.1}, {"x": 0.7, "y": 0.1}, {"x": 0.7, "y": 0.15}, {"x": 0.3, "y": 0.15}]


def to_upper(points):
    """The same area as it would be drawn on the upper floor's image."""
    return [{"x": (p["x"] - BX) / AX, "y": (p["y"] - BY) / AY} for p in points]


def annotations(**extra):
    data = {
        "floor_scale": {"groundfloor": 10.0},
        "floor_alignment": MARKS,
        "annotation_space": {"aspect": 1.0},          # image_size -> 1000 x 1000
        "annotations": [{
            "floor_level": "groundfloor", "label": "Wohnen",
            "points": [{"x": 0.2, "y": 0.2}, {"x": 0.8, "y": 0.2},
                       {"x": 0.8, "y": 0.8}, {"x": 0.2, "y": 0.8}],
        }],
        "exterior_areas": [],
    }
    data.update(extra)
    return data


def area(points, **extra):
    return {"id": "a1", "type": "terrasse", "points": points, **extra}


def close(test, got, want, delta=0.11):     # Frame.point rounds to 0.1 mm
    test.assertEqual(len(got), len(want))
    for g, w in zip(got, want):
        test.assertAlmostEqual(g[0], w[0], delta=delta)
        test.assertAlmostEqual(g[1], w[1], delta=delta)


class GroundPointsTests(unittest.TestCase):
    def points(self, flaeche, ann=None):
        return plan_builder.exterior_area_ground_points(flaeche, ann or annotations(), "groundfloor")

    def test_legacy_area_without_floor_is_ground_native(self):
        got, warum = self.points(area(GROUND_AREA))
        self.assertEqual(got, GROUND_AREA)
        self.assertIsNone(warum)

    def test_ground_area_is_untouched(self):
        got, _ = self.points(area(GROUND_AREA, floor_level="groundfloor"))
        self.assertEqual(got, GROUND_AREA)

    def test_upper_native_area_is_registered_onto_the_ground_floor(self):
        got, warum = self.points(area(to_upper(GROUND_AREA), floor_level="upperfloor"))
        self.assertIsNone(warum)
        for g, w in zip(got, GROUND_AREA):
            self.assertAlmostEqual(g["x"], w["x"], places=9)
            self.assertAlmostEqual(g["y"], w["y"], places=9)

    def test_points_outside_the_image_are_not_clamped(self):
        weit_draussen = [{"x": -0.4, "y": 1.3}, {"x": 0.2, "y": 1.3}, {"x": 0.2, "y": 1.6}]
        got, _ = self.points(area(weit_draussen, floor_level="upperfloor"))
        self.assertAlmostEqual(got[0]["x"], AX * -0.4 + BX, places=9)      # -0.55
        self.assertAlmostEqual(got[0]["y"], AY * 1.3 + BY, places=9)       #  1.1
        self.assertLess(got[0]["x"], 0.0)
        self.assertGreater(got[0]["y"], 1.0)

    def test_missing_alignment_is_reported(self):
        ann = annotations(floor_alignment={"groundfloor": MARKS["groundfloor"]})
        got, warum = self.points(area(GROUND_AREA, floor_level="upperfloor"), ann)
        self.assertIsNone(got)
        self.assertIn("upperfloor", warum)
        self.assertIn("Ausrichtung", warum)

    def test_marks_on_different_diagonals_are_reported_not_mirrored(self):
        # upper marked NE / SW, ground marked NW / SE: the builder's nearest
        # pairing would return a negative scale (a mirror image).
        ann = annotations(floor_alignment={
            "groundfloor": MARKS["groundfloor"],
            "upperfloor": [{"x": 0.5, "y": 0.1}, {"x": 0.1, "y": 0.9}],
        })
        got, warum = self.points(area(GROUND_AREA, floor_level="upperfloor"), ann)
        self.assertIsNone(got)
        self.assertTrue(warum)


class MainPathTests(unittest.TestCase):
    def convert(self, flaechen, **extra):
        ann = annotations(exterior_areas=flaechen, **extra)
        return plan_builder.plan_exterior_areas(ann, ann["floor_scale"], 1000.0, 1000.0)

    def test_upper_native_exterior_matches_ground_equivalent(self):
        aus_eg = self.convert([area(GROUND_AREA)])
        aus_og = self.convert([area(to_upper(GROUND_AREA), floor_level="upperfloor")])
        close(self, aus_og[0]["points_mm"], aus_eg[0]["points_mm"])
        self.assertEqual(aus_og[0]["type"], "terrasse")

    def test_the_old_behaviour_would_have_missed_by_a_lot(self):
        # Ground truth for the size of the bug: raw upper coordinates through
        # the ground frame are far from where the same area lands ground-side.
        aus_eg = self.convert([area(GROUND_AREA)])
        roh = plan_builder.Frame(10.0, 1000.0, 1000.0).point(to_upper(GROUND_AREA)[0])
        self.assertGreater(abs(roh[0] - aus_eg[0]["points_mm"][0][0]), 500)

    def test_exterior_registration_does_not_snap(self):
        # A point 300 mm from a wall must stay where it is; RegisteredFrame's
        # snapping is wall geometry, not site dressing.
        nah_an_der_wand = [{"x": 0.203, "y": 0.5}, {"x": 0.4, "y": 0.5}, {"x": 0.4, "y": 0.6}]
        aus_og = self.convert([area(to_upper(nah_an_der_wand), floor_level="upperfloor")])
        want = [plan_builder.Frame(10.0, 1000.0, 1000.0).point(p) for p in nah_an_der_wand]
        close(self, aus_og[0]["points_mm"], want)

    def test_missing_alignment_skips_the_area_and_says_so(self):
        ann = annotations(floor_alignment={"groundfloor": MARKS["groundfloor"]},
                          exterior_areas=[area(GROUND_AREA), area(GROUND_AREA, id="b", floor_level="upperfloor")])
        import contextlib
        import io
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            out = plan_builder.plan_exterior_areas(ann, ann["floor_scale"], 1000.0, 1000.0)
        self.assertEqual([a["id"] for a in out], ["a1"])
        self.assertIn("Aussenflaeche", buffer.getvalue())
        self.assertIn("upperfloor", buffer.getvalue())

    def test_no_floor_scale_gives_nothing(self):
        ann = annotations(exterior_areas=[area(GROUND_AREA)])
        self.assertEqual(plan_builder.plan_exterior_areas(ann, {}, 1000.0, 1000.0), [])


class CorrectedPathTests(unittest.TestCase):
    """annotation_exterior_areas() maps onto the CORRECTED footprint."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = plan_builder.SIMPLIFIER
        plan_builder.SIMPLIFIER = self.tmp.name

    def tearDown(self):
        plan_builder.SIMPLIFIER = self.old
        self.tmp.cleanup()

    def run_path(self, flaechen):
        folder = os.path.join(self.tmp.name, "projects", "p1")
        os.makedirs(folder, exist_ok=True)
        ann = annotations(exterior_areas=flaechen)
        with open(os.path.join(folder, "annotations.json"), "w", encoding="utf-8") as handle:
            json.dump(ann, handle)
        frame = plan_builder.Frame(10.0, 1000.0, 1000.0)
        rooms = [{"polygon_mm": [frame.point(p) for p in ann["annotations"][0]["points"]]}]
        return plan_builder.annotation_exterior_areas("p1", rooms)

    def test_corrected_path_registers_upper_native_areas(self):
        aus_eg = self.run_path([area(GROUND_AREA)])
        aus_og = self.run_path([area(to_upper(GROUND_AREA), floor_level="upperfloor")])
        self.assertEqual(len(aus_og), 1)
        close(self, aus_og[0]["points_mm"], aus_eg[0]["points_mm"])

    def test_corrected_fit_follows_registration(self):
        # Corrected footprint 2 % larger and shifted: the registered area must
        # ride through the SAME fit as the ground-native one.
        folder = os.path.join(self.tmp.name, "projects", "p1")
        os.makedirs(folder, exist_ok=True)
        ann = annotations(exterior_areas=[area(to_upper(GROUND_AREA), floor_level="upperfloor")])
        with open(os.path.join(folder, "annotations.json"), "w", encoding="utf-8") as handle:
            json.dump(ann, handle)
        rooms = [{"polygon_mm": [[1000, 1000], [9000, 1000], [9000, 9000], [1000, 9000]]}]
        out = plan_builder.annotation_exterior_areas("p1", rooms)
        # source footprint 2000..8000 -> target 1000..9000: scale 1.3333
        frame = plan_builder.Frame(10.0, 1000.0, 1000.0)
        want = []
        for p in GROUND_AREA:
            x, y = frame.point(p)
            want.append([(x - 2000) * (8000 / 6000) + 1000, (y - 2000) * (8000 / 6000) + 1000])
        close(self, out[0]["points_mm"], want, delta=0.3)


if __name__ == "__main__":
    unittest.main()
