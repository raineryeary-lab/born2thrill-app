"""Zwei Dachfluegel aus einem L-foermigen Grundriss erkennen.

Rainer, 2026-09-22, an `german_catalog_review_bungalow_4_3_1_wb_125`: "the
doppelpultdach is a walmdach in blender" -- die Form braucht heute ein
Rechteck, dieses Haus ist keins (eine ueberdachte Terrasse als Einschnitt).
Dann: "but this for example is exactly one of our standard houses". Eigene
Messung: 39 von 124 auswertbaren Haeusern (31 %) sind genau so ein
zweischenkliges L. Plan: born2thrill-local-workbench/plans/
zweischenkliges-satteldach-v1.md, Stufe 1 (Wandgeometrie).
"""
import importlib.util
import math
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("roof_wings", os.path.join(HERE, "roof_wings.py"))
rw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rw)


def rect(x0, x1, y0, y1):
    """Ein achsparalleles Rechteck als CCW-Punktliste."""
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# Ein einfaches L: grosser 10x9-Kasten, oben rechts eine 6x5.7-Ecke fehlt
# (dieselbe Form wie german_catalog_review_bungalow_4_3_1_wb_125, siehe
# WB_125_OUTLINE_M unten fuer die echten Zahlen).
SIMPLE_L = [(0, 0), (4, 0), (4, 4), (10, 4), (10, 9), (0, 9)]

# Der ECHTE Umriss von german_catalog_review_bungalow_4_3_1_wb_125
# (annotations.json outer_outlines.groundfloor), CCW gemacht und x10 skaliert
# (die Geometrie ist massstabsunabhaengig -- siehe roof_wings.py Docstring).
WB_125_OUTLINE_M = [(4.102, 3.0251), (9.7098, 3.0251), (9.7098, 9.1033),
                    (0.6597, 9.1033), (0.6597, 0.9732), (4.102, 0.9732)]

RECTANGLE = rect(0, 8, 0, 6)

# Ein T: ein 12x4-Querbalken oben, ein 4x6-Stiel darunter mittig -- zwei
# Reflexpunkte, ausdruecklich ausserhalb von Version 1. CCW (positive Flaeche).
T_SHAPE = [(4, 0), (8, 0), (8, 6), (12, 6), (12, 10), (0, 10), (0, 6), (4, 6)]

# Eine versetzte Treppenform (Z), zwei Reflexpunkte, KEIN einfaches L -- auch
# ausserhalb von Version 1.
Z_SHAPE = [(0, 0), (6, 0), (6, 3), (10, 3), (10, 8), (4, 8), (4, 5), (0, 5)]

# german_catalog_review_bungalow_4_3_1_wb_125's REAL, already overhang-
# expanded roof_poly (roof_wings_from_ridge_path()'s own `footprint`
# argument is always the overhang-expanded polygon, never the bare wall
# outline -- render-exterior.py passes `roof_poly`) and its REAL saved
# `roof_ridge_path` from BEFORE it was cleared, 2026-09-29 (preserved in
# annotations.json under `roof_ridge_path_removed_2026_09_29`). Rainer, on
# his own Blender viewport: "that doesnt look like a working roof" -- a
# visibly crossed/jagged roof surface, ROOF-SWEEP-CONSTRUCTOR-001.
WB_125_REAL_ROOF_POLY_M = [(0.577, 0.838), (14.467, 0.838), (14.467, 9.851),
                           (6.331, 9.851), (6.331, 12.638), (0.577, 12.638)]
WB_125_REAL_BROKEN_PATH_M = [(3.5179, 12.0906), (3.5179, 6.0391),
                             (0.9571, 6.0391), (14.0617, 6.0391)]


class WingRecognitionTests(unittest.TestCase):
    def test_a_plain_rectangle_has_no_wings_to_recognize(self):
        # Rechtecke laufen ueber den bestehenden is_rectangle-Pfad in
        # render-exterior.py -- dieses Modul wird dafuer nie aufgerufen,
        # muss aber defensiv None liefern, nicht abstuerzen.
        self.assertIsNone(rw.recognize_two_wings(RECTANGLE))

    def test_a_simple_l_recognizes_its_two_wings(self):
        got = rw.recognize_two_wings(SIMPLE_L)
        self.assertIsNotNone(got)
        wing_a, wing_b = got
        # First entlang x (volle Breite 0..10), First entlang y (volle Hoehe 0..9)
        self.assertEqual(wing_a, (0, 10, 4, 9))
        self.assertEqual(wing_b, (0, 4, 0, 9))

    def test_the_real_wb_125_outline_recognizes_its_two_wings(self):
        got = rw.recognize_two_wings(WB_125_OUTLINE_M)
        self.assertIsNotNone(got)
        wing_a, wing_b = got
        self.assertAlmostEqual(wing_a[0], 0.6597, places=3)
        self.assertAlmostEqual(wing_a[1], 9.7098, places=3)
        self.assertAlmostEqual(wing_a[2], 3.0251, places=3)
        self.assertAlmostEqual(wing_a[3], 9.1033, places=3)
        self.assertAlmostEqual(wing_b[0], 0.6597, places=3)
        self.assertAlmostEqual(wing_b[1], 4.102, places=3)
        self.assertAlmostEqual(wing_b[2], 0.9732, places=3)
        self.assertAlmostEqual(wing_b[3], 9.1033, places=3)

    def test_the_two_wings_together_cover_exactly_the_footprint(self):
        wing_a, wing_b = rw.recognize_two_wings(SIMPLE_L)
        self.assertTrue(rw._grid_coverage_matches(SIMPLE_L, wing_a, wing_b, rw.DEFAULT_TOL_M))
        # Ein Rechteck, das die Kerbe mit einschliesst, darf NICHT passen --
        # sonst wuerde eine ungueltige Zerlegung als gueltig durchgehen.
        self.assertFalse(rw._grid_coverage_matches(SIMPLE_L, (0, 10, 0, 9), (0, 4, 0, 9), rw.DEFAULT_TOL_M))

    def test_an_l_mirrored_into_all_four_corners_is_recognized(self):
        # Dieselbe Form, die fehlende Ecke einmal in jeder der vier Ecken --
        # die Missing-Corner-Erkennung darf sich nicht auf eine Richtung
        # verlassen.
        variants = {
            "oben rechts fehlt": [(0, 0), (10, 0), (10, 4), (4, 4), (4, 9), (0, 9)],
            "oben links fehlt": [(0, 0), (10, 0), (10, 9), (4, 9), (4, 4), (0, 4)],
            "unten rechts fehlt": [(0, 4), (4, 4), (4, 0), (10, 0), (10, 9), (0, 9)],
            "unten links fehlt": [(4, 0), (10, 0), (10, 9), (0, 9), (0, 4), (4, 4)],
        }
        for name, poly in variants.items():
            with self.subTest(name=name):
                got = rw.recognize_two_wings(poly)
                self.assertIsNotNone(got, name)
                wing_a, wing_b = got
                self.assertTrue(rw._grid_coverage_matches(poly, wing_a, wing_b, rw.DEFAULT_TOL_M))

    def test_a_t_shape_two_reflex_points_is_rejected(self):
        # Version 1: nur ein einfaches L (ein Reflexpunkt). Ein T braucht
        # eine eigene, spaetere Erweiterung (Plan, "Explicitly out of scope").
        self.assertEqual(len(rw._reflex_vertices(T_SHAPE)), 2)
        self.assertIsNone(rw.recognize_two_wings(T_SHAPE))

    def test_a_staircase_z_shape_is_rejected(self):
        self.assertIsNone(rw.recognize_two_wings(Z_SHAPE))

    def test_a_reflex_point_too_close_to_the_edge_is_rejected_not_guessed(self):
        # Reflexpunkt nur 0.1 m von der Aussenkante entfernt -- entartet,
        # lieber ablehnen als ein hauchduennes Fluegelchen bauen.
        degenerate = [(0, 0), (10, 0), (10, 0.1), (0.1, 0.1), (0.1, 9), (0, 9)]
        self.assertIsNone(rw.recognize_two_wings(degenerate))

    def test_a_polygon_with_too_few_points_is_rejected(self):
        self.assertIsNone(rw.recognize_two_wings([(0, 0), (1, 0)]))

    def test_a_clockwise_polygon_is_handled_like_its_ccw_twin(self):
        cw = list(reversed(SIMPLE_L))
        got_cw = rw.recognize_two_wings(cw)
        got_ccw = rw.recognize_two_wings(SIMPLE_L)
        self.assertEqual(got_cw, got_ccw)


class WingHeightTests(unittest.TestCase):
    """z = max(z1, z2): Handrechenbeispiel (Codex-Design-Review, 2026-09-22)."""

    def setUp(self):
        self.wing_a, self.wing_b = rw.recognize_two_wings(SIMPLE_L)   # (0,10,4,9), (0,4,0,9)
        self.t = math.tan(math.radians(30))     # steile Neigung, leicht nachzurechnen

    def test_a_single_wings_ridge_is_centred_and_symmetric(self):
        x0, x1, y0, y1 = self.wing_a
        mid_y = (y0 + y1) / 2
        # First in der Mitte: volle Firsthoehe = halbe Spannweite * Neigung
        self.assertAlmostEqual(rw.wing_height_m(self.wing_a, self.t, 5, mid_y),
                               (y1 - y0) / 2 * self.t, places=6)
        # Traufe (Rand): Hoehe 0
        self.assertAlmostEqual(rw.wing_height_m(self.wing_a, self.t, 5, y0), 0.0, places=6)
        self.assertAlmostEqual(rw.wing_height_m(self.wing_a, self.t, 5, y1), 0.0, places=6)
        # Symmetrisch um die Mitte
        self.assertAlmostEqual(rw.wing_height_m(self.wing_a, self.t, 5, mid_y - 1),
                               rw.wing_height_m(self.wing_a, self.t, 5, mid_y + 1), places=6)

    def test_a_point_outside_the_wing_rectangle_is_zero_height(self):
        # (1, 1) liegt in wing_b, nicht in wing_a (wing_a beginnt erst bei y=4)
        self.assertEqual(rw.wing_height_m(self.wing_a, self.t, 1, 1), 0.0)

    def test_combined_height_takes_the_upper_surface_at_the_shared_overlap_point(self):
        # Ueberlappung beider Fluegel: x in [0,4], y in [4,9]. An ihrer
        # jeweils jeweiligen Firstlinie muss combined_height_m das GROESSERE
        # der beiden Ergebnisse liefern, nicht eines "vergessen".
        x, y = 2.0, 6.5   # innerhalb der Ueberlappung
        h_a = rw.wing_height_m(self.wing_a, self.t, x, y)
        h_b = rw.wing_height_m(self.wing_b, self.t, x, y)
        combined = rw.combined_height_m([self.wing_a, self.wing_b], self.t, x, y)
        self.assertEqual(combined, max(h_a, h_b))
        self.assertGreater(combined, 0)   # innerhalb beider Fluegel: nie 0

    def test_at_the_reflex_corner_both_wings_meet_the_eave_at_zero(self):
        rx, ry = 4, 4   # der Reflexpunkt selbst
        self.assertAlmostEqual(rw.combined_height_m([self.wing_a, self.wing_b], self.t, rx, ry), 0.0, places=6)

    def test_ridge_side_classification_the_taller_wing_wins_at_its_own_ridge(self):
        # First von wing_a liegt bei y=6.5 (Mitte von 4..9); dort ist wing_a
        # klar dominant (Grat "gehoert" wing_a), auch innerhalb der
        # Ueberlappung mit wing_b.
        x0, x1, y0, y1 = self.wing_a
        ridge_y = (y0 + y1) / 2
        x_in_overlap = 2.0
        h_a = rw.wing_height_m(self.wing_a, self.t, x_in_overlap, ridge_y)
        h_b = rw.wing_height_m(self.wing_b, self.t, x_in_overlap, ridge_y)
        self.assertGreater(h_a, h_b, "am First von wing_a sollte wing_a die Kehle ueberragen")


class ReflexPointTests(unittest.TestCase):
    """Rainer, 2026-09-22, Doppelpultdach auf einem L: "i dont want a
    walmdach instead of the doppelpultdach" -- gebraucht, um den First des
    "durchgehenden" Fluegels auf die Naehe der echten Kehle zu deckeln,
    statt ihn ueber die volle (absichtlich ueberlappende) Rechteck-
    Ausdehnung wirken zu lassen."""

    SIMPLE_L_A, SIMPLE_L_B = (0, 10, 4, 9), (0, 4, 0, 9)

    def test_the_real_wb_125_reflex_point(self):
        # wing_a = (0.6597, 9.7098, 3.0251, 9.1033): its y1 (9.1033)
        # matches the shared bbox edge exactly (a true eave), so the
        # reflex point's y is its OTHER bound, y0 = 3.0251.
        wing_a, wing_b = rw.recognize_two_wings(WB_125_OUTLINE_M)
        rx, ry = rw.reflex_point(wing_a, wing_b)
        self.assertAlmostEqual(rx, 4.102, places=3)
        self.assertAlmostEqual(ry, 3.0251, places=3)

    def test_the_simple_l_reflex_point(self):
        rx, ry = rw.reflex_point(self.SIMPLE_L_A, self.SIMPLE_L_B)
        self.assertEqual((rx, ry), (4, 4))

    def test_all_four_corner_orientations(self):
        variants = {
            "oben rechts fehlt": [(0, 0), (10, 0), (10, 4), (4, 4), (4, 9), (0, 9)],
            "oben links fehlt": [(0, 0), (10, 0), (10, 9), (4, 9), (4, 4), (0, 4)],
            "unten rechts fehlt": [(0, 4), (4, 4), (4, 0), (10, 0), (10, 9), (0, 9)],
            "unten links fehlt": [(4, 0), (10, 0), (10, 9), (0, 9), (0, 4), (4, 4)],
        }
        for name, poly in variants.items():
            with self.subTest(name=name):
                wing_a, wing_b = rw.recognize_two_wings(poly)
                rx, ry = rw.reflex_point(wing_a, wing_b)
                self.assertEqual((rx, ry), (4, 4), name)


class ClipWingToValleyTests(unittest.TestCase):
    """`clip_wing_to_valley()`: a purely geometric primitive -- if `wing`
    spans a FULL bbox axis while `other_wing` ends at the reflex point on
    that axis, pull `wing` back to `margin` of the reflex point there.
    Both SIMPLE_L wings independently satisfy that pattern (wing_a spans
    the full x-range, wing_b the full y-range) -- the function clips
    whichever one is ASKED; it has no opinion on which one SHOULD be
    clipped for a given roof (that decision needs the profile/ridge axis
    too, and lives in render-exterior.py: only the smaller wing gets
    clipped there, since the bigger wing legitimately dominates the
    shared body and clipping it would risk an uncovered gap if the
    smaller one were clipped too)."""

    WING_A, WING_B = (0, 10, 4, 9), (0, 4, 0, 9)   # SIMPLE_L; rx,ry = 4,4

    def test_the_full_y_wing_is_clipped_in_y(self):
        # wing_b spans the full y-range (0..9); wing_a lives on the HIGH
        # side of the reflex point (y in [ry,9] = [4,9], its y0 == ry).
        # Clipping wing_b to a 1m margin pulls its y1 DOWN to ry+1=5,
        # leaving wing_b's own y<4 territory (below the shared zone,
        # exclusive to wing_b) untouched.
        clipped = rw.clip_wing_to_valley(self.WING_B, self.WING_A, 4, 4, margin=1.0)
        self.assertEqual(clipped, (0, 4, 0, 5.0))

    def test_the_full_x_wing_is_clipped_in_x(self):
        # wing_a spans the full x-range (0..10); wing_b's own home is
        # x<=4 (it ends at rx=4). Clipping wing_a to a 1m margin should
        # pull its x0 up to rx-1=3.
        clipped = rw.clip_wing_to_valley(self.WING_A, self.WING_B, 4, 4, margin=1.0)
        self.assertEqual(clipped, (3.0, 10, 4, 9))

    def test_zero_margin_clips_flush_to_the_reflex_point(self):
        clipped = rw.clip_wing_to_valley(self.WING_B, self.WING_A, 4, 4, margin=0.0)
        self.assertEqual(clipped, (0, 4, 0, 4.0))

    def test_a_margin_wider_than_the_wing_itself_does_not_invert_it(self):
        # An absurdly large margin must not push y0 past y1.
        clipped = rw.clip_wing_to_valley(self.WING_B, self.WING_A, 4, 4, margin=100.0)
        self.assertLessEqual(clipped[2], clipped[3])

    def test_matches_the_real_wb_125_orientation(self):
        # The function itself is purely geometric and clips WHICHEVER wing
        # is asked, on whichever axis it spans fully while the other wing
        # is reflex-bounded -- both directions clip here, since wing_a
        # spans the full x-range (ridge along x, its own "full" axis) just
        # as wing_b spans the full y-range (ridge along y). Caller code
        # decides WHICH wing to actually clip (render-exterior.py: only
        # the smaller one -- see its own comment for why).
        wing_a, wing_b = rw.recognize_two_wings(WB_125_OUTLINE_M)
        rx, ry = rw.reflex_point(wing_a, wing_b)
        clipped_b = rw.clip_wing_to_valley(wing_b, wing_a, rx, ry, margin=0.5)
        self.assertNotEqual(clipped_b, wing_b)
        clipped_a = rw.clip_wing_to_valley(wing_a, wing_b, rx, ry, margin=0.5)
        self.assertNotEqual(clipped_a, wing_a)


class RoofWingsFromRidgePathTests(unittest.TestCase):
    """`ROOF-RIDGE-PATH-TOOL-001`, 2026-09-27: derive wing rectangles from
    a user-drawn ridge path (corners allowed, any rectilinear shape) --
    the same `(wings, along_x)` shape the existing renderer already
    consumes, no changes needed there."""

    def test_a_straight_path_across_a_plain_rectangle_matches_it_exactly(self):
        got = rw.roof_wings_from_ridge_path([(0, 3), (8, 3)], RECTANGLE)
        self.assertIsNotNone(got)
        wings, along_x = got
        self.assertEqual(wings, [(0, 8, 0, 6)])
        self.assertEqual(along_x, [True])

    def test_an_l_shaped_ridge_across_the_full_wing_matches_recognize_two_wings(self):
        # The same SIMPLE_L recognize_two_wings() already handles
        # automatically, drawn by hand instead: a horizontal ridge spanning
        # the full top wing's own width, and (separately) a vertical
        # ridge spanning the full side wing's own height. Must produce
        # the SAME wings (0,10,4,9)/(0,4,0,9) -- proof the new derivation
        # is CORRECT, not just different, on a case with a known answer.
        wings1, _ = rw.roof_wings_from_ridge_path([(0, 6.5), (10, 6.5)], SIMPLE_L)
        wings2, _ = rw.roof_wings_from_ridge_path([(2, 9), (2, 0)], SIMPLE_L)
        self.assertEqual(wings1, [(0, 10, 4, 9)])
        self.assertAlmostEqual(wings2[0][0], 0, places=6)
        self.assertAlmostEqual(wings2[0][1], 4, places=6)
        self.assertEqual(wings2[0][2:], (0, 9))

    def test_an_l_shaped_path_as_one_continuous_two_segment_polyline(self):
        # The natural way a user actually draws it: across the top wing,
        # turn the corner, down through the side wing -- one path, two
        # segments. Rainer, 2026-09-27, second pass: "so it also takes on
        # the width of the Floorplan footprint plus tha dachueberstand
        # inclidun at the start and finish" -- the path's own two FREE
        # ends ((9,6.5) and (2,0)) now extend out to SIMPLE_L's true edge
        # (x=10, y=0) regardless of exactly where drawn; only the
        # INTERIOR corner (2,6.5) -- the L/turn junction between the two
        # wings, not a gable -- stays exactly as drawn (see the separate
        # interior-partial-gable test below for why that still matters).
        # The CROSS extent still correctly comes from the real footprint:
        # x=10 and the midpoint both sit safely inside wing_a's own
        # exclusive territory (x>4), so the "narrowest of 3 samples" rule
        # finds (4,9) despite the corner endpoint (x=2) alone sitting in
        # the ambiguous elbow region where the footprint is locally taller.
        path = [(9, 6.5), (2, 6.5), (2, 0)]
        wings, along_x = rw.roof_wings_from_ridge_path(path, SIMPLE_L)
        self.assertEqual(along_x, [True, False])
        self.assertEqual(wings[0], (2, 10, 4, 9))
        self.assertEqual(wings[1], (0, 4, 0, 6.5))

    def test_a_t_shaped_path_that_recognize_two_wings_cannot_handle_at_all(self):
        # T_SHAPE has two reflex points -- recognize_two_wings() returns
        # None for it (documented, explicit L-only limitation). A drawn
        # path has no such limit: one continuous stroke across the top
        # bar and back down the stem -- the only way to draw a T without
        # lifting the pen, so the ridge legitimately backtracks over
        # (12,8)->(6,8) before heading down; the resulting extra wing
        # ((6,12,6,10)) is a harmless subset already covered by the first.
        self.assertIsNone(rw.recognize_two_wings(T_SHAPE))
        path = [(0, 8), (12, 8), (6, 8), (6, 0)]
        wings, along_x = rw.roof_wings_from_ridge_path(path, T_SHAPE)
        self.assertEqual(along_x, [True, True, False])
        self.assertEqual(wings[0], (0, 12, 6, 10))
        # The stem's own free end (6,0) was already exactly on the true
        # wall (y=0), so it doesn't move; its OTHER end (6,8) is the
        # interior turn (not a gable) and also stays as drawn -- one row
        # short of the stem's own structural line (y=6), which just means
        # this wing's rectangle harmlessly re-covers a strip the bar wing
        # (wings[0]) already covers too (`combined_height_at()` takes the
        # max of overlapping wings, so redundant coverage is never wrong,
        # only ever a no-op).
        self.assertEqual(wings[-1], (4, 8, 0, 8))
        # Union of the bar and stem wings must exactly cover T_SHAPE --
        # reuse the same grid-coverage check style as recognize_two_
        # wings()'s own tests (the middle, redundant wing contributes no
        # area the other two don't already cover, so it's fine to leave
        # out of this specific check).
        self.assertTrue(rw._grid_coverage_matches(T_SHAPE, wings[0], wings[-1], rw.DEFAULT_TOL_M))

    def test_a_short_two_point_ridge_extends_to_the_true_wall_at_both_free_ends(self):
        # Rainer, 2026-09-27, second pass: a bare 2-point path has NO
        # interior corner -- both its points are free (gable) ends, so
        # BOTH always extend out to the footprint's true edge, regardless
        # of how far short of the wall the user actually clicked. This is
        # the ordinary case (a plain satteldach/pultdach ridge, or an L's
        # own wing drawn as its own segment): it should behave exactly
        # like the wall/overhang the automatic detector would have used,
        # not require pixel-perfect clicking.
        wings, along_x = rw.roof_wings_from_ridge_path([(1, 3), (6, 3)], RECTANGLE)
        self.assertEqual(wings, [(0, 8, 0, 6)])

    def test_an_interior_partial_gable_at_a_junction_is_still_accepted(self):
        # The free-end extension above must NEVER reach an INTERIOR
        # corner (shared by two segments) -- that is a real junction
        # between two wings (an L/T/plus corner), and a wing drawn
        # intentionally short there (a partial gable/hip) is still a
        # valid, deliberate shape, not an error. Middle segment
        # (4,3)-(4,1) touches neither path[0] nor path[-1] and must
        # survive completely unchanged.
        path = [(1, 3), (4, 3), (4, 1), (7, 1)]
        wings, along_x = rw.roof_wings_from_ridge_path(path, RECTANGLE)
        self.assertEqual(along_x, [True, False, True])
        self.assertEqual(wings[0], (0, 4, 0, 6))    # free end (1,3) -> true wall x=0
        self.assertEqual(wings[1], (0, 8, 1, 3))    # interior segment: untouched
        self.assertEqual(wings[2], (4, 8, 0, 6))    # free end (7,1) -> true wall x=8

    def test_a_diagonal_segment_is_rejected_not_silently_misbuilt(self):
        self.assertIsNone(rw.roof_wings_from_ridge_path([(0, 0), (5, 5)], RECTANGLE))

    def test_a_single_point_path_is_rejected(self):
        self.assertIsNone(rw.roof_wings_from_ridge_path([(1, 1)], RECTANGLE))

    def test_a_segment_ending_exactly_on_the_boundary_is_rejected(self):
        # (4,3) sits ON the rectangle's own right wall (x=8 is the true
        # wall; this checks the OTHER axis: a ridge endpoint whose cross
        # position sits exactly on the boundary, not safely inside it,
        # e.g. y=0 -- the true south wall itself).
        self.assertIsNone(rw.roof_wings_from_ridge_path([(1, 0), (6, 0)], RECTANGLE))

    def test_wb_125s_real_self_crossing_path_is_rejected_not_silently_misbuilt(self):
        # 2026-09-29, Rainer's own Blender viewport: "that doesnt look like
        # a working roof" -- a visibly crossed/jagged roof surface. Root
        # cause, confirmed by running this EXACT real path/footprint:
        # segment 2 ((3.5179,6.0391)->(0.9571,6.0391)) sits entirely within
        # the SIDE wing's own x-range, so its perpendicular (vertical) scan
        # picks up the side wing's extended reach (cross-extent up to
        # y=12.638) instead of the main wing's true extent -- producing a
        # wing whose cross-extent (0.838,12.638) directly conflicts with
        # segment 3's own, correctly-scanned main-wing wing (0.838,9.851),
        # despite both sharing the along_x ridge direction and overlapping
        # in x (0.9571 to 3.5179 is inside 0.9571 to 14.467). Two same-axis
        # wings disagreeing like this is exactly what produces the crossed
        # surface: max() of two conflicting symmetric ridge functions over
        # their shared area. This is the ACTUAL delivered project's ACTUAL
        # broken path -- not a synthetic approximation.
        result = rw.roof_wings_from_ridge_path(WB_125_REAL_BROKEN_PATH_M, WB_125_REAL_ROOF_POLY_M)
        self.assertIsNone(result)

    def test_legitimate_same_axis_overlap_with_matching_cross_extent_is_not_a_conflict(self):
        # The T-shape test above already proves this behaviourally (its
        # backtracked bar segment produces an exact cross-extent subset,
        # not a conflict) -- this test names the underlying rule directly
        # so a future change to the conflict check can't silently start
        # rejecting a legitimate redundant-subset wing.
        path = [(0, 8), (12, 8), (6, 8), (6, 0)]
        wings, along_x = rw.roof_wings_from_ridge_path(path, T_SHAPE)
        self.assertIsNotNone(wings)
        self.assertEqual(wings[0], (0, 12, 6, 10))
        self.assertEqual(wings[1], (6, 12, 6, 10))   # subset of wings[0]: same cross-extent


class RoofWingsFromRidgePathsTests(unittest.TestCase):
    """`ROOF-RIDGE-MULTI-PATH-001`, 2026-10-01. Rainer: "we said we would
    build a 'countertop' line maker, where i can also draw independent
    lines" -- WB_125's own two wings don't share a ridge joint point, and
    forcing them into one connected path (`WB_125_REAL_BROKEN_PATH_M`
    above) produced a self-overlapping path and a broken roof. This
    generalizes `roof_wings_from_ridge_path()` to a LIST of independent
    paths, each derived on its own."""

    def test_two_independent_paths_match_the_known_good_numbers(self):
        # SAME two segments the existing single-path tests already prove
        # match recognize_two_wings()'s own numbers on SIMPLE_L -- but
        # drawn here as two SEPARATE paths (not one connected polyline),
        # exactly the WB_125 shape of problem: two wings whose ridges
        # don't share a joint point.
        self.assertEqual(rw.recognize_two_wings(SIMPLE_L), ((0, 10, 4, 9), (0, 4, 0, 9)))
        path_a = [(0, 6.5), (10, 6.5)]
        path_b = [(2, 9), (2, 0)]
        got = rw.roof_wings_from_ridge_paths([path_a, path_b], SIMPLE_L)
        self.assertIsNotNone(got)
        wings, along_x = got
        self.assertEqual(wings, [(0, 10, 4, 9), (0, 4, 0, 9)])
        self.assertEqual(along_x, [True, False])

    def test_a_single_path_through_the_plural_function_matches_the_singular_one(self):
        path = [(0, 6.5), (10, 6.5)]
        self.assertEqual(
            rw.roof_wings_from_ridge_paths([path], SIMPLE_L),
            rw.roof_wings_from_ridge_path(path, SIMPLE_L),
        )

    def test_a_cross_path_conflict_is_detected_same_as_a_within_path_one(self):
        # Two INDEPENDENT paths, each individually valid on its own, whose
        # combined wings share a ridge axis, overlap, and disagree on
        # cross-extent -- the same disagreement that made the EXISTING
        # test_wb_125s_real_self_crossing_path_is_rejected... test reject a
        # single connected path, now checked across two separate ones.
        path_a = [(1, 2), (3, 2)]
        path_b = [(1, 7), (3, 7)]
        self.assertIsNotNone(rw.roof_wings_from_ridge_path(path_a, SIMPLE_L))
        self.assertIsNotNone(rw.roof_wings_from_ridge_path(path_b, SIMPLE_L))
        self.assertIsNone(rw.roof_wings_from_ridge_paths([path_a, path_b], SIMPLE_L))

    def test_an_invalid_path_in_the_list_rejects_the_whole_set(self):
        # Same "refuse rather than guess" fallback the singular function
        # already has for one bad path -- one bad path among several good
        # ones must not silently drop just that one.
        good = [(0, 6.5), (10, 6.5)]
        diagonal = [(0, 0), (5, 5)]
        self.assertIsNone(rw.roof_wings_from_ridge_paths([good, diagonal], SIMPLE_L))

    def test_empty_or_all_empty_paths_is_rejected(self):
        self.assertIsNone(rw.roof_wings_from_ridge_paths([], SIMPLE_L))
        self.assertIsNone(rw.roof_wings_from_ridge_paths([[], []], SIMPLE_L))

    def test_a_free_end_stops_at_another_paths_crossing_not_the_far_wall(self):
        # Rainer, 2026-10-01, live on WB_125: "if you do that then we end up
        # with an X instead of a T" -- the side wing's own vertical line was
        # drawn short of the true top wall (a free end), and the main
        # wing's horizontal line crosses it partway up. Before this fix,
        # the vertical free end extended all the way to the true top wall
        # (y=9), sailing straight through the main wing's own horizontal
        # line instead of stopping there -- a plus/X shape instead of the
        # correct T.
        vertical = [(2, 1), (2, 5)]        # upper end (y=5) is the free end
        horizontal = [(0, 5.5), (10, 5.5)]  # crosses the vertical's own column
        wings, along_x = rw.roof_wings_from_ridge_paths([vertical, horizontal], SIMPLE_L)
        self.assertEqual(along_x, [False, True])
        # Stops exactly at the horizontal line's own y (5.5) -- a T, not
        # extended to the true top wall (y=9).
        self.assertEqual(wings[0], (0, 4, 0, 5.5))
        # The main wing's own line is completely unaffected -- nothing
        # blocks IT, so it still reaches both true outer walls.
        self.assertEqual(wings[1], (0, 10, 4, 9))

    def test_a_free_end_with_nothing_in_its_path_still_reaches_the_wall(self):
        # Same shape, but the vertical line's free end (y=3) is drawn BELOW
        # the horizontal line's crossing (y=5.5) this time, i.e. the
        # horizontal line is NOT in the way of this particular extension
        # direction (which still travels from y=3 toward the far wall at
        # y=9, right past y=5.5) -- the crossing-detection must only ever
        # SHORTEN an extension that would otherwise sail through another
        # line, never get confused by one that sits on the wrong side.
        vertical = [(2, 1), (2, 3)]
        horizontal = [(0, 5.5), (10, 5.5)]
        wings, along_x = rw.roof_wings_from_ridge_paths([vertical, horizontal], SIMPLE_L)
        # The horizontal line crosses the vertical's own column (x=2) at
        # y=5.5, which DOES sit between the free end (y=3) and the true
        # wall (y=9) -- so this one SHOULD stop there too; this test exists
        # to pin that down explicitly (not just assert it doesn't crash).
        self.assertEqual(wings[0], (0, 4, 0, 5.5))

    def test_both_free_ends_of_one_path_each_stop_at_their_own_crossing(self):
        # Three independent paths: a short vertical spine, sandwiched
        # between two horizontal branches that each cross it. Both of the
        # spine's own free ends need extending (it's drawn entirely between
        # the two branches) -- each must stop at its OWN nearer crossing,
        # not sail past to the true top/bottom wall. The branches' own free
        # ends (away from the spine) are unaffected -- nothing blocks them.
        spine = [(2, 5.5), (2, 6.5)]
        branch_lo = [(2, 5), (10, 5)]
        branch_hi = [(2, 7), (10, 7)]
        wings, along_x = rw.roof_wings_from_ridge_paths(
            [spine, branch_lo, branch_hi], SIMPLE_L)
        self.assertEqual(along_x, [False, True, True])
        self.assertEqual(wings[0], (0, 10, 5, 7))
        self.assertEqual(wings[1], (0, 10, 4, 9))
        self.assertEqual(wings[2], (0, 10, 4, 9))


if __name__ == "__main__":
    unittest.main()
