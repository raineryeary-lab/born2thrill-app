"""The stair band must not run through an exterior wall.

Rainer, 2026-09-21, twostorey_053: "stairs are not aligned why all of a sudden
again?" The drawn Lauflinie sat 250 mm too far to the right; the builder sweeps
the band symmetrically around it, so the 900 mm band ended 325 mm beyond the
wall's inner face and 85 mm outside the house -- and nothing said so."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "build-simplifier-render-plan.py"))
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)

# a 8 m x 12 m house, 240 mm exterior walls on the centreline rectangle
WALLS = [
    {"start_mm": [0, 0], "end_mm": [8000, 0], "thickness_mm": 240, "wall_type": "exterior"},
    {"start_mm": [8000, 0], "end_mm": [8000, 12000], "thickness_mm": 240, "wall_type": "exterior"},
    {"start_mm": [8000, 12000], "end_mm": [0, 12000], "thickness_mm": 240, "wall_type": "exterior"},
    {"start_mm": [0, 12000], "end_mm": [0, 0], "thickness_mm": 240, "wall_type": "exterior"},
    {"start_mm": [0, 6000], "end_mm": [8000, 6000], "thickness_mm": 120, "wall_type": "interior"},
]


def core(x_left, x_right, y_bottom=3000, y_top=5000):
    return {"polygon_mm": [[x_left, y_bottom], [x_right, y_bottom], [x_right, y_top], [x_left, y_top]]}


class StairWallOverlapTests(unittest.TestCase):
    def overlap(self, stair):
        return plan_builder.stair_wall_overlap(stair, WALLS)

    def test_a_stair_inside_the_house_reports_nothing(self):
        self.assertIsNone(self.overlap(core(4000, 6000)))

    def test_a_stair_exactly_at_the_inner_face_is_fine(self):
        # inner face of the right wall is at 8000 - 120
        self.assertIsNone(self.overlap(core(5000, 7880)))

    def test_a_stair_running_into_the_wall_reports_the_depth(self):
        got = self.overlap(core(5000, 8000))       # to the wall centreline: 120 mm into it
        self.assertAlmostEqual(got["in_wand_mm"], 120, delta=5)
        self.assertEqual(got["ausserhalb_mm"], 0)

    def test_twostorey_053_case_through_the_wall_and_out_the_other_side(self):
        got = self.overlap(core(5000, 8205))       # 205 mm past the centreline
        self.assertAlmostEqual(got["in_wand_mm"], 325, delta=5)
        self.assertAlmostEqual(got["ausserhalb_mm"], 85, delta=5)

    def test_small_overlaps_from_hand_drawing_are_tolerated(self):
        self.assertIsNone(self.overlap(core(5000, 7900)))      # 20 mm

    def test_interior_walls_are_ignored(self):
        self.assertIsNone(self.overlap(core(4000, 6000, 5900, 6100)))

    def test_no_stair_or_no_walls_gives_nothing(self):
        self.assertIsNone(plan_builder.stair_wall_overlap(None, WALLS))
        self.assertIsNone(plan_builder.stair_wall_overlap(core(1, 2), []))


if __name__ == "__main__":
    unittest.main()
