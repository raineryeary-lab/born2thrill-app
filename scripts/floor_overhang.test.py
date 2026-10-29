"""An upper storey must not stick out past (or fall short of) the ground floor
without anybody being told.

Rainer, 2026-09-21, twostorey_053: "the floors are not lined up." The upper
floor's north wall stood 353 mm beyond the ground floor's. RegisteredFrame snaps
outer faces onto the ground floor's within SNAP_MM = 350, so 353 mm was kept "as
drawn (a real setback)" -- and nothing in the build said so; it showed up only in
Blender. The builder cannot tell an intended overhang from a hand-drawing error,
so it says "check", it does not move anything."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "build-simplifier-render-plan.py"))
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)


def box(x0, y0, x1, y1, thickness=240):
    return [
        {"start_mm": [x0, y0], "end_mm": [x1, y0], "thickness_mm": thickness, "wall_type": "exterior"},
        {"start_mm": [x1, y0], "end_mm": [x1, y1], "thickness_mm": thickness, "wall_type": "exterior"},
        {"start_mm": [x1, y1], "end_mm": [x0, y1], "thickness_mm": thickness, "wall_type": "exterior"},
        {"start_mm": [x0, y1], "end_mm": [x0, y0], "thickness_mm": thickness, "wall_type": "exterior"},
        {"start_mm": [x0, (y0 + y1) / 2], "end_mm": [x1, (y0 + y1) / 2], "thickness_mm": 120, "wall_type": "interior"},
    ]


def floors(upper_walls, ground_walls=None):
    return [
        {"level": "groundfloor", "walls": ground_walls or box(2008.5, 1395.4, 10268.5, 13035.4)},
        {"level": "upperfloor", "walls": upper_walls},
    ]


class FloorOverhangTests(unittest.TestCase):
    def report(self, upper_walls, **kwargs):
        return plan_builder.floor_overhang(floors(upper_walls), **kwargs)

    def test_flush_floors_report_nothing(self):
        self.assertEqual(self.report(box(2008.5, 1395.4, 10268.5, 13035.4)), [])

    def test_twostorey_053_north_wall_353_mm_out(self):
        got = self.report(box(2008.5, 1395.4, 10268.5, 13388.0))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["level"], "upperfloor")
        self.assertEqual(got[0]["side"], "north")
        self.assertAlmostEqual(got[0]["delta_mm"], 352.6, delta=1)

    def test_a_setback_is_reported_with_a_negative_delta(self):
        got = self.report(box(2008.5 + 400, 1395.4, 10268.5, 13035.4))
        self.assertEqual([(g["side"], round(g["delta_mm"])) for g in got], [("west", -400)])

    def test_hand_drawing_noise_is_tolerated(self):
        self.assertEqual(self.report(box(2008.5, 1395.4, 10268.5, 13035.4 + 200)), [])

    def test_outer_faces_are_compared_not_centrelines(self):
        # same centrelines, 120 mm walls upstairs: outer faces differ by 60 mm
        self.assertEqual(self.report(box(2008.5, 1395.4, 10268.5, 13035.4, thickness=120)), [])

    def test_a_wall_of_different_thickness_is_measured_at_its_outer_face(self):
        # centreline 400 further out, wall 120 thinner: outer face = +400 - 120 + 60 = +340
        got = self.report(box(2008.5, 1395.4, 10268.5, 13035.4 + 400, thickness=120))
        self.assertEqual([(g["side"], round(g["delta_mm"])) for g in got], [("north", 340)])

    def test_several_sides_are_all_listed(self):
        got = self.report(box(2008.5 - 300, 1395.4 - 300, 10268.5, 13035.4))
        self.assertEqual(sorted(g["side"] for g in got), ["south", "west"])

    def test_no_ground_floor_or_no_exterior_walls_gives_nothing(self):
        self.assertEqual(plan_builder.floor_overhang([{"level": "upperfloor", "walls": box(0, 0, 1, 1)}]), [])
        self.assertEqual(plan_builder.floor_overhang(floors([w for w in box(0, 0, 9000, 9000) if w["wall_type"] != "exterior"])), [])
        self.assertEqual(plan_builder.floor_overhang([]), [])

    def test_the_threshold_can_be_tightened(self):
        got = self.report(box(2008.5, 1395.4, 10268.5, 13035.4 + 200), threshold_mm=100)
        self.assertEqual(got[0]["side"], "north")


class FloorOverhangMessageTests(unittest.TestCase):
    def test_message_names_side_and_size_and_says_check_not_wrong(self):
        text = plan_builder.floor_overhang_message(
            {"level": "upperfloor", "side": "north", "delta_mm": 352.6})
        self.assertIn("upperfloor", text)
        self.assertIn("Norden", text)
        self.assertIn("353", text)
        self.assertIn("Pruefen", text)

    def test_a_setback_says_zurueck(self):
        text = plan_builder.floor_overhang_message(
            {"level": "upperfloor", "side": "west", "delta_mm": -400})
        self.assertIn("Westen", text)
        self.assertIn("zurueck", text)


if __name__ == "__main__":
    unittest.main()
