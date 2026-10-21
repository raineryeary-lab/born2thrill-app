"""T- and Z/S-shaped footprints (exactly two reflex vertices) as three (or,
for the simpler Z sub-family, two) roof wings -- see roof_wings_multi.py's
own module docstring for the full story of why this needed its own file
and its own construction rules per shape family.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rw = _load("roof_wings")
rwm = _load("roof_wings_multi")


def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# The SAME fixtures roof_wings.test.py already uses to assert the existing,
# one-reflex-only recognize_two_wings() correctly REJECTS these two shapes
# -- reused here (not redefined) so both files are provably talking about
# the same two real test shapes, not two different ones that happen to
# share a name.
T_SHAPE = [(4, 0), (8, 0), (8, 6), (12, 6), (12, 10), (0, 10), (0, 6), (4, 6)]
Z_SHAPE = [(0, 0), (6, 0), (6, 3), (10, 3), (10, 8), (4, 8), (4, 5), (0, 5)]

RECTANGLE = rect(0, 8, 0, 6)
SIMPLE_L = [(0, 0), (4, 0), (4, 4), (10, 4), (10, 9), (0, 9)]

# Codex's own illustrative three-wing Z/S example (design review,
# plans/TZ-WING-RECOGNITION-001-codex-review.md): a NARROW connector
# bridging two arms that do NOT themselves overlap -- geometrically
# distinct from Z_SHAPE above, which only needs two overlapping
# rectangles. Traced by hand into a boundary the same way T_SHAPE/Z_SHAPE
# already were, then confirmed against the exact-coverage check itself
# (see test_codex_three_wing_example_matches_its_own_band_description).
#   y:[4,6] -> x:[0,6]  (upper arm)
#   y:[2,4] -> x:[4,6]  (connector, narrow)
#   y:[0,2] -> x:[4,10] (lower arm)
Z_CONNECTOR_SHAPE = [(4, 0), (10, 0), (10, 2), (6, 2), (6, 6), (0, 6), (0, 4), (4, 4)]

# A U-shaped notch: a rectangle with a notch cut from the MIDDLE of one
# edge that does NOT reach through to the opposite edge -- two reflex
# vertices, like a T or Z, but genuinely neither (no stem reaches the far
# side, no diagonal offset). Must be explicitly rejected, not guessed at.
U_NOTCH_SHAPE = [(0, 0), (10, 0), (10, 10), (7, 10), (7, 4), (3, 4), (3, 10), (0, 10)]


def mirror_x(poly, width):
    return [(width - x, y) for x, y in poly]


def mirror_y(poly, height):
    return [(x, height - y) for x, y in poly]


def rotate_90(poly):
    """(x,y) -> (y,-x), then the caller shifts to keep coordinates >= 0."""
    pts = [(y, -x) for x, y in poly]
    min_x = min(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    return [(x - min_x, y - min_y) for x, y in pts]


class ArrangementCoverageTests(unittest.TestCase):
    """The exact (not sampled) coverage check this whole module leans on."""

    def test_two_wings_that_exactly_cover_the_l_pass(self):
        wing_a, wing_b = rw.recognize_two_wings(SIMPLE_L)
        self.assertTrue(rwm._arrangement_coverage_matches(SIMPLE_L, (wing_a, wing_b), rw.DEFAULT_TOL_M))

    def test_a_wing_set_that_over_covers_the_notch_fails(self):
        self.assertFalse(rwm._arrangement_coverage_matches(
            SIMPLE_L, ((0, 10, 0, 9), (0, 4, 0, 9)), rw.DEFAULT_TOL_M))

    def test_a_wing_set_that_under_covers_fails(self):
        # wing_b shrunk in y too, so its own y0..1 strip (x:[0,4]) is no
        # longer covered by EITHER wing -- a genuine hole, not papered over
        # by the other wing's own full extent (an earlier version of this
        # test only shrunk wing_a's x0, which wing_b's full x:[0,4] already
        # covered on its own -- not actually an under-coverage case at all).
        self.assertFalse(rwm._arrangement_coverage_matches(
            SIMPLE_L, ((2, 10, 4, 9), (0, 4, 1, 9)), rw.DEFAULT_TOL_M))


class TShapeTests(unittest.TestCase):
    def test_the_repositorys_own_t_fixture_is_recognized(self):
        # Same T_SHAPE roof_wings.test.py uses to prove recognize_two_wings()
        # (one-reflex-only) correctly rejects it.
        self.assertEqual(len(rw._reflex_vertices(T_SHAPE)), 2)
        self.assertIsNone(rw.recognize_two_wings(T_SHAPE))

        got = rwm.recognize_multi_wing(T_SHAPE)
        self.assertIsNotNone(got)
        self.assertEqual(got["shape"], "T")
        self.assertEqual(got["roles"], ("stem", "arm_1", "arm_2"))
        stem, arm_1, arm_2 = got["wings"]
        self.assertEqual(stem, (4, 8, 0, 10))
        self.assertEqual(arm_1, (0, 8, 6, 10))
        self.assertEqual(arm_2, (4, 12, 6, 10))
        # The junction graph: all three wings genuinely meet at the T's
        # crossing (Codex: "a T has a real three-way overlap").
        self.assertEqual(len(got["junctions"]), 3)

    def test_stem_up_instead_of_down(self):
        # T_SHAPE's own stem hangs DOWN from a bar at the top; mirror it
        # vertically so the stem points UP from a bar at the bottom --
        # the "which bbox edge is missing" logic must not have silently
        # assumed one direction.
        poly = mirror_y(T_SHAPE, 10)
        got = rwm.recognize_multi_wing(poly)
        self.assertIsNotNone(got)
        self.assertEqual(got["shape"], "T")

    def test_stem_sideways_left_and_right(self):
        # Rotate the whole T 90 degrees: bar runs vertically, stem pokes
        # out sideways -- exercises the shared_x (as opposed to shared_y)
        # branch of the construction.
        rotated = rotate_90(T_SHAPE)
        got = rwm.recognize_multi_wing(rotated)
        self.assertIsNotNone(got, rotated)
        self.assertEqual(got["shape"], "T")
        rotated_back = rotate_90(rotate_90(rotate_90(T_SHAPE)))
        got2 = rwm.recognize_multi_wing(rotated_back)
        self.assertIsNotNone(got2, rotated_back)
        self.assertEqual(got2["shape"], "T")

    def test_a_clockwise_t_is_handled_like_its_ccw_twin(self):
        cw = list(reversed(T_SHAPE))
        got_cw = rwm.recognize_multi_wing(cw)
        got_ccw = rwm.recognize_multi_wing(T_SHAPE)
        self.assertEqual(got_cw, got_ccw)


class ZShapeTests(unittest.TestCase):
    def test_the_repositorys_own_z_fixture_needs_only_two_wings(self):
        # Same Z_SHAPE roof_wings.test.py calls "eine versetzte
        # Treppenform (Z)" and uses to prove recognize_two_wings() rejects
        # it -- traced by hand (see roof_wings_multi.py's module docstring
        # discovery note) to actually be the SIMPLER two-overlapping-
        # rectangles family, not the three-wing connector family.
        self.assertEqual(len(rw._reflex_vertices(Z_SHAPE)), 2)
        self.assertIsNone(rw.recognize_two_wings(Z_SHAPE))

        got = rwm.recognize_multi_wing(Z_SHAPE)
        self.assertIsNotNone(got)
        self.assertEqual(got["shape"], "Z")
        self.assertEqual(len(got["wings"]), 2)
        self.assertEqual(got["roles"], ("rect_1", "rect_2"))
        rect_1, rect_2 = got["wings"]
        self.assertEqual(rect_1, (0, 6, 0, 5))
        self.assertEqual(rect_2, (4, 10, 3, 8))

    def test_codex_three_wing_example_needs_the_connector(self):
        self.assertEqual(len(rw._reflex_vertices(Z_CONNECTOR_SHAPE)), 2)
        got = rwm.recognize_multi_wing(Z_CONNECTOR_SHAPE)
        self.assertIsNotNone(got)
        self.assertEqual(got["shape"], "Z")
        self.assertEqual(len(got["wings"]), 3, got["wings"])
        self.assertEqual(got["roles"], ("connector", "arm_lo", "arm_hi"))
        # The connector must NOT itself span a full bbox axis -- that's
        # exactly what distinguishes it from the simpler two-wing family
        # (Codex: "the connector overlaps each arm, the arms do not
        # overlap each other").
        connector, arm_lo, arm_hi = got["wings"]

        def overlap_area(a, b):
            ax0, ax1, ay0, ay1 = a
            bx0, bx1, by0, by1 = b
            ox = max(0.0, min(ax1, bx1) - max(ax0, bx0))
            oy = max(0.0, min(ay1, by1) - max(ay0, by0))
            return ox * oy

        self.assertGreater(overlap_area(connector, arm_lo), 0)
        self.assertGreater(overlap_area(connector, arm_hi), 0)
        self.assertEqual(overlap_area(arm_lo, arm_hi), 0)

    def test_z_mirrored_into_the_other_diagonal(self):
        mirrored = mirror_x(Z_SHAPE, 10)
        got = rwm.recognize_multi_wing(mirrored)
        self.assertIsNotNone(got, mirrored)
        self.assertEqual(got["shape"], "Z")

    def test_z_connector_example_mirrored_and_rotated(self):
        for variant in (
            mirror_x(Z_CONNECTOR_SHAPE, 10),
            mirror_y(Z_CONNECTOR_SHAPE, 6),
            rotate_90(Z_CONNECTOR_SHAPE),
        ):
            with self.subTest(variant=variant):
                got = rwm.recognize_multi_wing(variant)
                self.assertIsNotNone(got, variant)
                self.assertEqual(got["shape"], "Z")

    def test_a_clockwise_z_is_handled_like_its_ccw_twin(self):
        cw = list(reversed(Z_SHAPE))
        got_cw = rwm.recognize_multi_wing(cw)
        got_ccw = rwm.recognize_multi_wing(Z_SHAPE)
        self.assertEqual(got_cw, got_ccw)


class RejectionTests(unittest.TestCase):
    """Two reflex vertices does not imply T or Z -- U-notches and
    staircases also qualify by reflex-count alone (Codex's own warning);
    they must be explicitly rejected, not forced into a wrong T/Z shape."""

    def test_a_u_shaped_notch_is_rejected(self):
        self.assertEqual(len(rw._reflex_vertices(U_NOTCH_SHAPE)), 2)
        self.assertIsNone(rwm.recognize_multi_wing(U_NOTCH_SHAPE))

    def test_a_plain_rectangle_has_nothing_to_recognize(self):
        self.assertIsNone(rwm.recognize_multi_wing(RECTANGLE))

    def test_a_simple_l_one_reflex_point_is_not_this_modules_job(self):
        # recognize_two_wings() already owns the one-reflex-vertex case;
        # this module must not also claim it.
        self.assertIsNone(rwm.recognize_multi_wing(SIMPLE_L))

    def test_a_reflex_point_too_close_to_the_edge_is_rejected_not_guessed(self):
        degenerate = [(4, 0), (8, 0), (8, 0.1), (12, 0.1), (12, 10), (0, 10), (0, 0.1), (4, 0.1)]
        self.assertIsNone(rwm.recognize_multi_wing(degenerate))

    def test_a_polygon_with_too_few_points_is_rejected(self):
        self.assertIsNone(rwm.recognize_multi_wing([(0, 0), (1, 0)]))

    def test_three_reflex_points_are_out_of_scope_and_rejected(self):
        # A plus/cross shape: four reflex vertices, well outside anything
        # reviewed or requested here.
        plus = [(4, 0), (6, 0), (6, 4), (10, 4), (10, 6), (6, 6),
                (6, 10), (4, 10), (4, 6), (0, 6), (0, 4), (4, 4)]
        self.assertIsNone(rwm.recognize_multi_wing(plus))


if __name__ == "__main__":
    unittest.main(verbosity=2)
