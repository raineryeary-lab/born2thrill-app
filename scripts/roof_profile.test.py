import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roof_profile as rp  # noqa: E402


def edge_use(faces):
    edges = {}
    for face in faces:
        for i, a in enumerate(face):
            b = face[(i + 1) % len(face)]
            edges.setdefault((a, b), 0)
            edges[(a, b)] += 1
    return edges


def projected_up_area(verts, faces):
    """Horizontal area covered by faces whose normal points up."""
    total = 0.0
    for face in faces:
        pts = [verts[i] for i in face]
        nx, ny, nz = rp._newell(pts)
        if nz > 1e-9:
            total += nz / 2.0
    return total


def signed_volume(verts, faces):
    """Positive when every face points outward (fan-triangulated)."""
    total = 0.0
    for face in faces:
        v0 = verts[face[0]]
        for k in range(1, len(face) - 1):
            v1, v2 = verts[face[k]], verts[face[k + 1]]
            cross = (v1[1] * v2[2] - v1[2] * v2[1],
                     v1[2] * v2[0] - v1[0] * v2[2],
                     v1[0] * v2[1] - v1[1] * v2[0])
            total += (v0[0] * cross[0] + v0[1] * cross[1] + v0[2] * cross[2]) / 6.0
    return total


class SanitizeTests(unittest.TestCase):
    def test_garbage_gives_none(self):
        self.assertIsNone(rp.sanitize_profile(None, 10000))
        self.assertIsNone(rp.sanitize_profile({"form": "walmdach", "points": [{}]}, 10000))
        self.assertIsNone(rp.sanitize_profile({"form": "satteldach", "points": []}, 10000))

    def test_nan_and_strings_do_not_raise(self):
        out = rp.sanitize_profile({"form": "satteldach",
                                   "points": [{"u": "x", "h_mm": float("nan")}]}, 10000)
        self.assertEqual(out["points"][0]["u"], 0.5)
        self.assertGreaterEqual(out["points"][0]["h_mm"], rp.H_MIN_MM)

    def test_ridge_kept_inside_footprint_with_margin(self):
        out = rp.sanitize_profile({"form": "satteldach",
                                   "points": [{"u": 0.0, "h_mm": 1000}]}, 10000)
        self.assertEqual(out["points"][0]["u"], rp.U_MIN)
        out = rp.sanitize_profile({"form": "satteldach",
                                   "points": [{"u": 5, "h_mm": 1000}]}, 10000)
        self.assertEqual(out["points"][0]["u"], rp.U_MAX)

    def test_slope_capped(self):
        out = rp.sanitize_profile({"form": "satteldach",
                                   "points": [{"u": 0.5, "h_mm": 99999}]}, 10000)
        self.assertLessEqual(out["points"][0]["h_mm"], rp.MAX_SLOPE * 5000)
        self.assertLessEqual(out["points"][0]["h_mm"], rp.H_MAX_MM)

    def test_doppelpult_points_get_ordered_and_vertical_step_snaps(self):
        out = rp.sanitize_profile({"form": "doppelpultdach", "points": [
            {"u": 0.6, "h_mm": 2000}, {"u": 0.605, "h_mm": 1000}]}, 10000)
        self.assertEqual(out["points"][0]["u"], out["points"][1]["u"])

    def test_doppelpult_step_limited(self):
        out = rp.sanitize_profile({"form": "doppelpultdach", "points": [
            {"u": 0.5, "h_mm": 500}, {"u": 0.5, "h_mm": 6000}]}, 20000)
        self.assertLessEqual(out["points"][1]["h_mm"] - out["points"][0]["h_mm"],
                             rp.STEP_MAX_MM)

    def test_idempotent(self):
        p = rp.default_profile("doppelpultdach", 10600)
        self.assertEqual(rp.sanitize_profile(p, 10600), p)

    def test_defaults_are_five_degrees(self):
        # 10.6 m span: gable rise = 5.3 m * tan(5 deg) = 0.4637 m
        p = rp.default_profile("satteldach", 10600)
        self.assertAlmostEqual(p["points"][0]["h_mm"], 464, delta=1)


class ResolveTests(unittest.TestCase):
    def test_every_built_form_always_gets_a_profile(self):
        for form in rp.FORMS:
            got = rp.resolve_profile(None, form, 10000)
            self.assertEqual(got["form"], form)
            self.assertEqual(got, rp.default_profile(form, 10000))

    def test_a_saved_profile_wins_over_the_default(self):
        saved = {"satteldach": {"form": "satteldach", "points": [{"u": 0.3, "h_mm": 1800}]}}
        got = rp.resolve_profile(saved, "satteldach", 10000)
        self.assertEqual(got["points"][0]["u"], 0.3)

    def test_each_form_only_takes_its_own_profile(self):
        profiles = {"doppelpultdach": {"form": "doppelpultdach",
                                       "points": [{"u": 0.5, "h_mm": 900}, {"u": 0.5, "h_mm": 1800}]}}
        self.assertEqual(rp.resolve_profile(profiles, "satteldach", 10000),
                         rp.default_profile("satteldach", 10000))
        self.assertEqual(rp.resolve_profile(profiles, "doppelpultdach", 10000)["points"][1]["h_mm"], 1800)

    def test_a_profile_filed_under_the_wrong_key_is_ignored(self):
        wrong = {"satteldach": rp.default_profile("pultdach", 10000)}
        self.assertEqual(rp.resolve_profile(wrong, "satteldach", 10000),
                         rp.default_profile("satteldach", 10000))

    def test_flachdach_and_walmdach_are_not_built_here(self):
        for kind in ("flachdach", "walmdach"):
            self.assertIsNone(rp.resolve_profile({}, kind, 10000))


class TwoWingSharedProfileTests(unittest.TestCase):
    """render-exterior.py's Satteldach-auf-L-Grundriss-Pfad (roof_wings.py)
    ruft resolve_profile() zweimal mit DEMSELBEN gespeicherten Profil aber
    ZWEI unterschiedlichen (Fluegel-)Spannweiten auf -- Rainer, 2026-09-22,
    nachdem die erste Fassung immer den 5-Grad-Standard gebaut hat, egal was
    gespeichert war: "no i want it fixed, this is BS". Diese Tests pinnen
    genau dieses zweifache Aufloesen fest, nicht nur den Einzelfall."""

    def test_the_same_saved_profile_resolves_on_two_different_spans(self):
        saved = {"satteldach": {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 5000}]}}
        wide = rp.resolve_profile(saved, "satteldach", 12890)   # wing_a-artige Spannweite
        narrow = rp.resolve_profile(saved, "satteldach", 4750)  # wing_b-artige Spannweite
        # Auf der breiten Spanne passt die volle gespeicherte Firsthoehe
        # (5000mm < 1.5 * halbe Spanne, kein Deckel noetig).
        self.assertEqual(wide["points"][0]["h_mm"], 5000)
        # Auf der schmalen Spanne wird exakt derselbe, bestehende Deckel aus
        # sanitize_profile() angewendet (MAX_SLOPE * halbe Spanne) -- kein
        # neuer Sonderfall fuer Fluegel, derselbe Mechanismus wie ueberall.
        self.assertEqual(narrow["points"][0]["h_mm"],
                         round(rp.MAX_SLOPE * 0.5 * 4750))
        self.assertLess(narrow["points"][0]["h_mm"], wide["points"][0]["h_mm"])

    def test_a_span_too_narrow_for_any_saved_height_still_returns_a_sound_roof(self):
        saved = {"satteldach": {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 5000}]}}
        got = rp.resolve_profile(saved, "satteldach", 1200)
        self.assertGreaterEqual(got["points"][0]["h_mm"], rp.H_MIN_MM)
        self.assertLessEqual(got["points"][0]["h_mm"], rp.MAX_SLOPE * 0.5 * 1200)

    def test_an_off_centre_saved_ridge_keeps_its_u_on_both_wings(self):
        # u ist bereits spannweiten-unabhaengig (Bruchteil 0..1) -- ein
        # aussermittiger First bleibt auf beiden Fluegeln an derselben
        # relativen Stelle, nur die Hoehe wird pro Spanne neu gedeckelt.
        saved = {"satteldach": {"form": "satteldach", "points": [{"u": 0.3, "h_mm": 900}]}}
        wide = rp.resolve_profile(saved, "satteldach", 12890)
        narrow = rp.resolve_profile(saved, "satteldach", 4750)
        self.assertEqual(wide["points"][0]["u"], 0.3)
        self.assertEqual(narrow["points"][0]["u"], 0.3)


class HasVerticalStepTests(unittest.TestCase):
    def test_doppelpultdach_with_equal_u_has_a_step(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]}
        self.assertTrue(rp.has_vertical_step(prof))

    def test_a_flat_topped_doppelpultdach_has_no_step(self):
        # two DIFFERENT u -- a sloped plateau, not a vertical jump.
        prof = {"form": "doppelpultdach", "points": [{"u": 0.35, "h_mm": 1500}, {"u": 0.65, "h_mm": 1500}]}
        self.assertFalse(rp.has_vertical_step(prof))

    def test_satteldach_and_pultdach_never_have_a_step(self):
        self.assertFalse(rp.has_vertical_step(rp.default_profile("satteldach", 9000)))
        self.assertFalse(rp.has_vertical_step(rp.default_profile("pultdach", 9000)))

    def test_none_and_empty_are_false_not_a_crash(self):
        self.assertFalse(rp.has_vertical_step(None))
        self.assertFalse(rp.has_vertical_step({"form": "satteldach", "points": []}))


class SoftenVerticalStepsTests(unittest.TestCase):
    """Rainer, still on Doppelpultdach: "you are back to the 2
    doppelpultdach roofs" -- a DIFFERENT bug than the wing-overlap spike:
    a height field cannot sample a true zero-width vertical jump
    consistently, wherever it falls (not just at wing overlaps). Widening
    it into a short, continuous ramp before it ever reaches
    heightfield_roof_mesh() removes the ambiguity."""

    def test_widens_a_true_vertical_step_by_the_requested_run(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]}
        out = rp.soften_vertical_steps(prof, span_mm=9000, min_run_mm=300)
        self.assertAlmostEqual(out["points"][0]["u"], 0.39, places=6)
        self.assertAlmostEqual(out["points"][1]["u"], 0.39 + 300 / 9000, places=6)
        # heights untouched -- only u moves.
        self.assertEqual(out["points"][0]["h_mm"], 2150)
        self.assertEqual(out["points"][1]["h_mm"], 1200)

    def test_a_profile_without_a_step_is_unchanged(self):
        prof = rp.default_profile("satteldach", 9000)
        out = rp.soften_vertical_steps(prof, span_mm=9000, min_run_mm=300)
        self.assertEqual(out, prof)

    def test_a_flat_topped_doppelpultdach_is_unchanged(self):
        # two DIFFERENT u already -- a sloped plateau, nothing to widen.
        prof = {"form": "doppelpultdach", "points": [{"u": 0.35, "h_mm": 1500}, {"u": 0.65, "h_mm": 1500}]}
        out = rp.soften_vertical_steps(prof, span_mm=9000, min_run_mm=300)
        self.assertEqual(out, prof)

    def test_never_pushes_u_past_u_max(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.9, "h_mm": 2150}, {"u": 0.9, "h_mm": 1200}]}
        out = rp.soften_vertical_steps(prof, span_mm=1000, min_run_mm=500)
        self.assertLessEqual(out["points"][1]["u"], rp.U_MAX)

    def test_a_zero_span_is_a_safe_no_op_not_a_crash(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]}
        out = rp.soften_vertical_steps(prof, span_mm=0, min_run_mm=300)
        self.assertEqual(out["points"][0]["u"], out["points"][1]["u"])

    def test_result_no_longer_reads_as_having_a_step(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]}
        out = rp.soften_vertical_steps(prof, span_mm=9000, min_run_mm=300)
        self.assertFalse(rp.has_vertical_step(out))


class ScaleProfileToSpanTests(unittest.TestCase):
    """render-exterior.py loest das gespeicherte Profil einmal gegen die
    Spannweite des GANZEN Daches auf (das, was der Dach-Tab-Editor zeigt),
    dann ueberträgt `scale_profile_to_span()` es auf jeden Fluegel. Rainer,
    2026-09-22, zum ersten (falschen) Versuch -- dieselbe absolute Hoehe auf
    jedem Fluegel: "i dont understand ... 2 flat roofs on top of each
    other". Diese Tests pinnen fest, dass die NEIGUNG (nicht die absolute
    Hoehe) erhalten bleibt."""

    def test_the_pitch_stays_the_same_on_a_narrower_wing(self):
        design = rp.resolve_profile(
            {"satteldach": {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1550}]}},
            "satteldach", 11800)
        design_pitch = design["points"][0]["h_mm"] / (design["points"][0]["u"] * 11800)

        narrow = rp.scale_profile_to_span(design, 11800, 2790)
        narrow_pitch = narrow["points"][0]["h_mm"] / (narrow["points"][0]["u"] * 2790)
        # sanitize_profile() rundet h_mm auf ganze mm -- auf einer sehr
        # kurzen Spanne (2,79 m) macht das eine winzige Winkelabweichung,
        # kein Rundungsfehler im eigentlichen Skalierungsschritt.
        self.assertAlmostEqual(narrow_pitch, design_pitch, places=3)
        # Nicht dieselbe absolute Hoehe -- das war genau der Fehler.
        self.assertLess(narrow["points"][0]["h_mm"], design["points"][0]["h_mm"])

    def test_a_wider_wing_than_the_design_span_scales_up_not_down(self):
        design = {"form": "pultdach", "points": [{"u": 1.0, "h_mm": 500}]}
        wider = rp.scale_profile_to_span(design, 5000, 10000)
        self.assertAlmostEqual(wider["points"][0]["h_mm"], 1000, delta=1)

    def test_the_same_span_in_and_out_is_a_no_op(self):
        design = rp.default_profile("doppelpultdach", 9000)
        same = rp.scale_profile_to_span(design, 9000, 9000)
        self.assertEqual(same, design)

    def test_u_never_changes_only_height(self):
        design = {"form": "doppelpultdach",
                  "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]}
        scaled = rp.scale_profile_to_span(design, 12890, 2790)
        self.assertEqual([p["u"] for p in scaled["points"]], [0.39, 0.39])

    def test_still_clamped_against_the_wings_own_bounds_afterwards(self):
        # Ein absurd hoher Design-First auf eine winzige Fluegel-Spanne
        # projiziert muss trotz gleicher Neigung noch innerhalb der
        # bestehenden Grenzen landen (sanitize_profile() laeuft danach).
        design = {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 5900}]}
        tiny = rp.scale_profile_to_span(design, 12000, 1300)
        self.assertLessEqual(tiny["points"][0]["h_mm"], rp.H_MAX_MM)
        self.assertGreaterEqual(tiny["points"][0]["h_mm"], rp.H_MIN_MM)

    def test_a_zero_or_missing_design_span_returns_the_profile_unchanged(self):
        design = rp.default_profile("satteldach", 8000)
        self.assertEqual(rp.scale_profile_to_span(design, 0, 5000), design)
        self.assertEqual(rp.scale_profile_to_span(None, 8000, 5000), None)


class PultdachTests(unittest.TestCase):
    def test_edge_snaps_to_left_or_right(self):
        for u, want in ((0.9, 1.0), (0.5, 1.0), (0.2, 0.0), (-3, 0.0)):
            out = rp.sanitize_profile({"form": "pultdach", "points": [{"u": u, "h_mm": 1000}]}, 10000)
            self.assertEqual(out["points"][0]["u"], want)

    def test_default_matches_todays_pultdach_rise(self):
        p = rp.default_profile("pultdach", 10500)          # span * tan(5 deg) = 0.9187 m
        self.assertAlmostEqual(p["points"][0]["h_mm"], 918.7, delta=1)

    def test_slope_capped_over_the_full_span(self):
        out = rp.sanitize_profile({"form": "pultdach", "points": [{"u": 1, "h_mm": 99999}]}, 4000)
        self.assertLessEqual(out["points"][0]["h_mm"], rp.MAX_SLOPE * 4000)

    def test_roof_is_one_sheet_the_wall_is_separate(self):
        for u in (0.0, 1.0):
            prof = rp.sanitize_profile({"form": "pultdach", "points": [{"u": u, "h_mm": 1200}]}, 10000)
            verts, faces, facade = rp.profile_mesh(0, 12, 0, 10, 2.75, prof)
            self.assertEqual(len(faces), 1)                # just the slope: paper laid over the house
            self.assertEqual(facade, [])


class RoofSheetTests(unittest.TestCase):
    CASES = {
        "gable centred": {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]},
        "gable off-centre": {"form": "satteldach", "points": [{"u": 0.3, "h_mm": 1200}]},
        "versetzt": {"form": "doppelpultdach", "points": [
            {"u": 0.5, "h_mm": 1000}, {"u": 0.5, "h_mm": 2000}]},
        "versetzt stepping down": {"form": "doppelpultdach", "points": [
            {"u": 0.5, "h_mm": 2000}, {"u": 0.5, "h_mm": 1000}]},
        "flat top": {"form": "doppelpultdach", "points": [
            {"u": 0.35, "h_mm": 1500}, {"u": 0.65, "h_mm": 1500}]},
        "pult high right": {"form": "pultdach", "points": [{"u": 1.0, "h_mm": 1300}]},
        "pult high left": {"form": "pultdach", "points": [{"u": 0.0, "h_mm": 1300}]},
    }
    DIMS = ((0, 12, 0, 9), (0, 9, 0, 12))

    def build(self, name, dims=(0, 12, 0, 9), z=2.75):
        span_mm = min(dims[1] - dims[0], dims[3] - dims[2]) * 1000
        prof = rp.sanitize_profile(self.CASES[name], span_mm)
        return prof, rp.profile_mesh(dims[0], dims[1], dims[2], dims[3], z, prof)

    def test_no_directed_edge_used_twice(self):
        for name in self.CASES:
            for dims in self.DIMS:
                _, (verts, faces, _) = self.build(name, dims)
                for edge, count in edge_use(faces).items():
                    self.assertEqual(count, 1, "%s %s edge %s" % (name, dims, edge))

    def test_roof_sheet_covers_the_whole_roof_outline_no_gaps(self):
        for name in self.CASES:
            for dims in self.DIMS:
                _, (verts, faces, _) = self.build(name, dims)
                area = (dims[1] - dims[0]) * (dims[3] - dims[2])
                self.assertAlmostEqual(projected_up_area(verts, faces), area, places=6,
                                       msg="%s %s" % (name, dims))

    def test_faces_point_away_from_the_house(self):
        for name in self.CASES:
            _, (verts, faces, _) = self.build(name)
            for face in faces:
                nx, ny, nz = rp._newell([verts[i] for i in face])
                cx = sum(verts[i][0] for i in face) / len(face)
                cy = sum(verts[i][1] for i in face) / len(face)
                if abs(nz) > 1e-9 and abs(nx) + abs(ny) < 1e-9:
                    self.assertGreater(nz, 0, name)             # slopes and flats face up
                elif abs(nz) < 1e-9:
                    self.assertGreaterEqual((cx - 6.0) * nx + (cy - 4.5) * ny, -1e-9, name)

    def test_eaves_stay_at_wall_top(self):
        for name in self.CASES:
            _, (verts, _, _) = self.build(name, z=2.75)
            low = [v for v in verts if abs(v[2] - 2.75) < 1e-9]
            self.assertEqual(len(low), 4, name)

    def test_no_degenerate_faces(self):
        for name in self.CASES:
            _, (verts, faces, _) = self.build(name)
            for face in faces:
                nx, ny, nz = rp._newell([verts[i] for i in face])
                self.assertGreater((nx * nx + ny * ny + nz * nz) ** 0.5, 1e-6, name)

    def test_gable_is_a_folded_sheet_of_two_faces(self):
        _, (verts, faces, facade) = self.build("gable centred")
        self.assertEqual((len(verts), len(faces), facade), (6, 2, []))

    def test_versetzt_keeps_its_vertical_plaster_step(self):
        _, (verts, faces, facade) = self.build("versetzt")
        self.assertEqual(len(faces), 3)                        # two slopes and the step
        self.assertEqual(len(facade), 1)
        self.assertAlmostEqual(rp._newell([verts[j] for j in faces[facade[0]]])[2], 0.0, places=9)


class WallExtensionTests(unittest.TestCase):
    """The wall from the wall tops up to the roof, on the house's own planes."""
    OV, T, Z = 0.5, 0.24, 2.75

    def walls(self, name, dims=(0, 12, 0, 9)):
        span_mm = min(dims[1] - dims[0], dims[3] - dims[2]) * 1000
        prof = rp.sanitize_profile(RoofSheetTests.CASES[name], span_mm)
        return prof, rp.wall_extension(dims[0], dims[1], dims[2], dims[3], self.Z, self.OV, prof, self.T)

    def test_every_prism_is_closed_and_faces_outward(self):
        for name in RoofSheetTests.CASES:
            for dims in RoofSheetTests.DIMS:
                _, prisms = self.walls(name, dims)
                self.assertGreaterEqual(len(prisms), 2, name)
                for verts, faces in prisms:
                    use = edge_use(faces)
                    for (a, b), count in use.items():
                        self.assertEqual(count, 1, "%s directed edge reused" % name)
                        self.assertIn((b, a), use, "%s open edge" % name)
                    self.assertGreater(signed_volume(verts, faces), 1e-6, "%s inside-out" % name)

    def test_walls_stand_on_the_house_walls_not_at_the_overhang_edge(self):
        # Rainer, 2026-09-22: "i dont understand ... 2 flat roofs on top of
        # each other" -- traced to the gable wall standing `overhang` inside
        # the roof (correct, that's the verge) with NOTHING closing the
        # underside of that pocket, so you could see clean through it. Fix:
        # wall_extension() now ALSO returns a verge-soffit prism per gable
        # end that reaches all the way to the true roof edge on EVERY side
        # (along the ridge axis AND across, into the eave corners -- a
        # first version only closed the ridge-axis side and Rainer still
        # saw a sliver of sky at the corner). The load-bearing wall itself
        # still stands inset -- some prism must still have a vertex there.
        for name in RoofSheetTests.CASES:
            _, prisms = self.walls(name)
            xs = [v[0] for verts, _ in prisms for v in verts]
            ys = [v[1] for verts, _ in prisms for v in verts]
            # ridge along x (12 x 9): the wall itself still sits OV inside
            # the roof (half a wall thick around the plane) -- SOME prism
            # (the real gable wall, thickness T) still has a vertex there.
            self.assertTrue(any(abs(v[0] - (0 + self.OV - self.T / 2)) < 1e-9
                                for verts, _ in prisms for v in verts), name)
            # But nothing is left open out to the true roof edge any more,
            # on any side -- the soffit closes it flush with the whole
            # roof silhouette (x=0/12 AND y=0/9, the eave corners too).
            self.assertAlmostEqual(min(xs), 0.0, places=9, msg=name)
            self.assertAlmostEqual(max(xs), 12.0, places=9, msg=name)
            self.assertAlmostEqual(min(ys), 0.0, places=9, msg=name)
            self.assertAlmostEqual(max(ys), 9.0, places=9, msg=name)

    def test_walls_start_at_the_wall_top_and_never_poke_through_the_roof(self):
        for name in RoofSheetTests.CASES:
            prof, prisms = self.walls(name)
            section = rp._section(prof, 9.0)
            for verts, _ in prisms:
                self.assertAlmostEqual(min(v[2] for v in verts), self.Z, places=9, msg=name)
                for x, y, z in verts:
                    roof = self.Z + rp._height_at(section, y)
                    # a versetzt step has two heights at one position: allow the higher
                    step_top = max(self.Z + h for c, h in section if abs(c - y) < 1e-6) \
                        if any(abs(c - y) < 1e-6 for c, _ in section) else roof
                    self.assertLessEqual(z, max(roof, step_top) + 1e-9, "%s pokes through the roof" % name)

    def test_the_soffit_closes_the_overhang_pocket_with_no_gap(self):
        # The soffit spans exactly [true roof edge, wall centreline] -- its
        # inner ring reaches a0+overhang, PAST the wall's own near face
        # (a0+overhang-T/2), so it overlaps into the wall rather than
        # falling short of it: no sliver left open either side.
        for name in RoofSheetTests.CASES:
            _, prisms = self.walls(name)
            soffit_xs = sorted({round(v[0], 9) for verts, _ in prisms for v in verts
                                if abs(max(vv[0] for vv in verts) - min(vv[0] for vv in verts) - self.OV) < 1e-9})
            self.assertIn(0.0, soffit_xs, name)              # reaches the true roof edge
            self.assertIn(12.0, soffit_xs, name)
            self.assertIn(round(self.OV, 9), soffit_xs, name)          # reaches the wall centreline
            self.assertIn(round(12 - self.OV, 9), soffit_xs, name)

    def test_no_overhang_means_no_soffit_prism_and_no_crash(self):
        # overhang=0: the wall itself sits centred exactly on the roof
        # edge, so it alone (no separate soffit needed or built) already
        # pokes out by half its own thickness -- same as before this fix.
        prof = rp.sanitize_profile(RoofSheetTests.CASES["gable centred"], 9000)
        prisms = rp.wall_extension(0, 12, 0, 9, self.Z, 0.0, prof, self.T)
        xs = [v[0] for verts, _ in prisms for v in verts]
        self.assertAlmostEqual(min(xs), -self.T / 2, places=9)
        self.assertAlmostEqual(max(xs), 12 + self.T / 2, places=9)

    def test_gable_apex_reaches_the_ridge_with_no_gap(self):
        # ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP-2, 2026-10-01: a real
        # steep-pitch render showed a visible hole right at the gable's own
        # tip -- every OTHER point still tucks `sink` into the roof slab
        # (hidden under the overhang there), but the profile's own PEAK now
        # reaches the true ridge height exactly, no gap at all, closing the
        # one point `sink` can't hide behind anything.
        prof, prisms = self.walls("gable centred")
        apex = max(v[2] for verts, _ in prisms for v in verts)
        self.assertAlmostEqual(apex - self.Z, 1.5, delta=0.01)

    def test_pultdach_high_side_is_walled_up_to_the_roof(self):
        prof, prisms = self.walls("pult high right")
        section = rp._section(prof, 9.0)
        # The verge soffit now reaches the TRUE roof edge (y=9.0, the eave
        # corner) -- for a Pultdach whose high edge sits exactly at u=1,
        # that true edge is the roof's own tallest point. ROOF-RIDGE-PATH-
        # TOOL-001-FOLLOWUP-2, 2026-09-27: the soffit itself is no longer
        # simply the OVERALL tallest prism -- it now carries its own extra
        # margin (`extra_sink`, `boundary_polygon()`'s own docstring: a
        # real camera-ray comparison against a built render showed it
        # otherwise sitting in front of -- visible through -- the roof's
        # own SOLIDIFY surface on a steep slope) on top of which OTHER,
        # unrelated prisms (the long wall along the eave, unaffected by
        # this margin) can legitimately come out taller. Identify the
        # ridge-axis-end verge soffits directly -- narrow (`overhang`
        # wide) along the ridge axis (X here), spanning the FULL cross-
        # section width (Y, 0..9) -- rather than assuming whichever prism
        # is tallest overall is the soffit.
        soffits = [p for p in prisms
                   if abs(max(v[0] for v in p[0]) - min(v[0] for v in p[0]) - self.OV) < 1e-6
                   and max(v[1] for v in p[0]) - min(v[1] for v in p[0]) > 1.0]
        self.assertTrue(soffits, "the ridge-axis ends need their own verge soffits")
        tallest = max(v[2] for p in soffits for v in p[0]) - self.Z
        # ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP-2, 2026-10-01: this pultdach's
        # own peak sits exactly at the true eave corner (y=9.0, u=1) -- the
        # same "no `sink` at the profile's own peak" fix as the gable apex
        # test above applies here too, so only `extra_sink` (the soffit's
        # own separate margin) is left subtracted.
        # ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP-2, 2026-10-01: this profile's
        # own peak sits exactly at cross=9.0 (u=1) -- both `sink` and
        # `extra_sink` are now zero there (the wall and the soffit must
        # meet flush at the one point they share, not leave a visible step
        # between a sunk soffit and an un-sunk wall right at the peak).
        self.assertAlmostEqual(tallest, rp._height_at(section, 9.0), places=6)
        # the long wall itself, tucked under the lowest point of the roof across its thickness
        long_walls = [p for p in prisms
                      if max(v[0] for v in p[0]) - min(v[0] for v in p[0]) > 1.0     # runs along the ridge
                      and max(v[1] for v in p[0]) > 9.0 - self.OV - 1e-6]
        self.assertTrue(long_walls, "the high side needs its own wall along the eave")
        inner = 9.0 - self.OV - self.T / 2
        self.assertAlmostEqual(max(v[2] for v in long_walls[0][0]) - self.Z,
                               rp._height_at(section, inner) - 0.05, places=6)

    def test_a_tiny_building_gets_no_walls_instead_of_bad_ones(self):
        prof = rp.default_profile("satteldach", 900)
        self.assertEqual(rp.wall_extension(0, 3, 0, 1.2, 2.75, 0.5, prof, 0.24), [])

    def test_real_ends_false_skips_that_ends_gable_wall_and_soffit(self):
        # Rainer, 2026-09-24, german_catalog_review_bungalow_4_3_1_wb_125's
        # Versetztes Pultdach on an L: the wing carrying the FULL
        # cross-section has only ONE true outer gable -- its other ridge-axis
        # end is the internal reflex line, where a full-profile end-wall
        # would poke into the narrower wing's own territory. real_ends lets
        # the caller skip that end's ordinary wall/soffit (a separate,
        # truncated call covers it correctly instead).
        prof, prisms_both = self.walls("gable centred")
        prisms_a1_only = rp.wall_extension(0, 12, 0, 9, self.Z, self.OV, prof, self.T,
                                           real_ends=(False, True))
        prisms_a0_only = rp.wall_extension(0, 12, 0, 9, self.Z, self.OV, prof, self.T,
                                           real_ends=(True, False))
        # Fewer prisms than building both ends (each end contributes an
        # end-wall + a soffit -- both dropped when that end isn't real).
        self.assertLess(len(prisms_a1_only), len(prisms_both))
        self.assertLess(len(prisms_a0_only), len(prisms_both))
        # No prism reaches all the way to the a0 (x=0) roof edge when a0 is
        # not real, and none reaches the a1 (x=12) edge when a1 is not real
        # -- the long "high side" walls (which run the whole ridge
        # regardless of real_ends, by design) still stop short of the true
        # edge, at overhang/2 in from it, same as any prism that isn't the
        # dropped gable/soffit.
        xs_a1_only = [v[0] for verts, _ in prisms_a1_only for v in verts]
        xs_a0_only = [v[0] for verts, _ in prisms_a0_only for v in verts]
        self.assertGreater(min(xs_a1_only), 0.0)
        self.assertLess(max(xs_a0_only), 12.0)
        # The real end is unaffected: still reaches its true roof edge.
        self.assertAlmostEqual(max(xs_a1_only), 12.0, places=9)
        self.assertAlmostEqual(min(xs_a0_only), 0.0, places=9)

    def test_real_ends_default_is_unchanged_behaviour(self):
        prof = rp.sanitize_profile(RoofSheetTests.CASES["gable centred"], 9000)
        default = rp.wall_extension(0, 12, 0, 9, self.Z, self.OV, prof, self.T)
        explicit = rp.wall_extension(0, 12, 0, 9, self.Z, self.OV, prof, self.T,
                                     real_ends=(True, True))
        self.assertEqual(len(default), len(explicit))


class EndWallAndSoffitTests(unittest.TestCase):
    """Just ONE gable end-wall + its soffit -- no long "high side" walls.

    Rainer, 2026-09-24, german_catalog_review_bungalow_4_3_1_wb_125's
    Versetztes Pultdach: wall_extension(), even with real_ends suppressing
    the unwanted end, still built its OWN pair of long walls running the
    WHOLE ridge-axis range of whatever rectangle it's given -- wrong for a
    small notch-edge sliver whose "own" ridge-axis range is mostly the wide
    wing's already-built territory. end_wall_and_soffit() is the fix: only
    the requested end's wall + soffit, nothing that runs the ridge length.
    """
    OV, T, Z = 0.5, 0.24, 2.75

    def test_returns_only_a_wall_and_a_soffit_no_long_walls(self):
        prof = rp.sanitize_profile({"form": "pultdach", "points": [{"u": 0, "h_mm": 1200}]}, 9000)
        prisms = rp.end_wall_and_soffit(0, 12, 0, 9, self.Z, self.OV, prof, self.T, "a0")
        self.assertEqual(len(prisms), 2)  # one end-wall, one soffit -- never a long wall

    def test_no_prism_extends_past_the_ridge_axis_end_plus_overhang(self):
        # A long wall (the bug this replaces) would run the WHOLE a0..a1
        # ridge-axis range; a single end's wall + soffit must stay within a
        # sliver near that one end.
        prof = rp.sanitize_profile({"form": "pultdach", "points": [{"u": 0, "h_mm": 1200}]}, 9000)
        prisms = rp.end_wall_and_soffit(0, 12, 0, 9, self.Z, self.OV, prof, self.T, "a0")
        xs = [v[0] for verts, _ in prisms for v in verts]
        self.assertLessEqual(max(xs), self.OV + self.T / 2 + 1e-9)

    def test_a1_end_builds_near_the_far_edge_instead(self):
        prof = rp.sanitize_profile({"form": "pultdach", "points": [{"u": 1, "h_mm": 1200}]}, 9000)
        prisms = rp.end_wall_and_soffit(0, 12, 0, 9, self.Z, self.OV, prof, self.T, "a1")
        xs = [v[0] for verts, _ in prisms for v in verts]
        self.assertGreaterEqual(min(xs), 12 - self.OV - self.T / 2 - 1e-9)

    def test_no_overhang_still_returns_just_the_wall(self):
        prof = rp.sanitize_profile({"form": "pultdach", "points": [{"u": 0, "h_mm": 1200}]}, 9000)
        prisms = rp.end_wall_and_soffit(0, 12, 0, 9, self.Z, 0.0, prof, self.T, "a0")
        self.assertEqual(len(prisms), 1)  # no soffit needed when there is no overhang

    def test_too_narrow_a_cross_span_gets_no_wall_instead_of_a_bad_one(self):
        prof = rp.default_profile("pultdach", 900)
        self.assertEqual(
            rp.end_wall_and_soffit(0, 3, 0, 1.2, self.Z, 0.5, prof, self.T, "a0"), [])


class AxisContractTests(unittest.TestCase):
    """The contract the Dach-tab reference (dach-referenz.js) now relies on:
    the ridge runs along the LONGER side, a tie goes to "along x", and u=0 is
    the wall at the SMALLER world coordinate. Rainer, 2026-09-22: "we have to
    add some kind of referance to the Dach Tab to place the roofs correctly."
    Codex-Review (read-only) traced this exact chain; these tests pin it down
    so a future change to _axes()/profile_mesh() cannot silently invert it
    without the client's reference going wrong too."""

    def test_ridge_runs_along_the_longer_side(self):
        self.assertEqual(rp._axes(0, 12, 0, 8)[0], True)     # width 12 >= depth 8
        self.assertEqual(rp._axes(0, 8, 0, 12)[0], False)

    def test_a_tie_goes_to_along_x(self):
        # roof_profile.py: `along_x = width >= depth` -- equality wins for x.
        self.assertEqual(rp._axes(0, 10, 0, 10)[0], True)

    def test_u_zero_is_the_smaller_world_y_when_along_x(self):
        along_x, span, _, c0 = rp._axes(0, 12, 2, 10)
        self.assertTrue(along_x)
        self.assertEqual(c0, 2)          # the smaller of the two world y values
        self.assertEqual(span, 8)        # depth

        # The satteldach ridge (u=0.3) must land at world y = c0 + 0.3*span.
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.3, "h_mm": 900}]}, 8000)
        verts, _, _ = rp.profile_mesh(0, 12, 2, 10, 2.75, prof)
        ridge = [v for v in verts if abs(v[2] - (2.75 + 0.9)) < 1e-6]
        self.assertTrue(ridge)
        for v in ridge:
            self.assertAlmostEqual(v[1], 2 + 0.3 * 8, places=6)

    def test_u_zero_is_the_smaller_world_x_when_along_y(self):
        along_x, span, _, c0 = rp._axes(0, 8, 0, 12)   # depth 12 > width 8: ridge along y
        self.assertFalse(along_x)
        self.assertEqual(c0, 0)          # the smaller of the two world x values
        self.assertEqual(span, 8)        # width

        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.3, "h_mm": 900}]}, 8000)
        verts, _, _ = rp.profile_mesh(0, 8, 0, 12, 2.75, prof)
        ridge = [v for v in verts if abs(v[2] - (2.75 + 0.9)) < 1e-6]
        self.assertTrue(ridge)
        for v in ridge:
            self.assertAlmostEqual(v[0], 0 + 0.3 * 8, places=6)


class AxisOverrideTests(unittest.TestCase):
    """Rainer, 2026-09-22: "also mybe have a possibility to rotate the roof
    90 degrees" -- confirmed with "und die Dachdrehung?" Codex-Design-Review
    (read-only) recommended a keyword-only `along_x` override on _axes(),
    profile_mesh() and wall_extension(): None keeps today's automatic rule
    exactly (AxisContractTests above must keep passing unmodified), an
    explicit True/False forces that axis regardless of width/depth."""

    def test_automatic_mode_is_unchanged_by_the_new_parameter(self):
        self.assertEqual(rp._axes(0, 12, 0, 8), rp._axes(0, 12, 0, 8, along_x=None))

    def test_forced_axis_selects_cross_span_interval_and_origin(self):
        # width 12 >= depth 8 would automatically pick along_x=True (span=8,
        # the depth); forcing False must select the OTHER span/origin pair.
        along_x, span, (a0, a1), c0 = rp._axes(0, 12, 2, 10, along_x=False)
        self.assertFalse(along_x)
        self.assertEqual(span, 12)       # width, not depth
        self.assertEqual(c0, 0)          # the smaller world x
        self.assertEqual((a0, a1), (2, 10))

    def test_explicit_false_overrides_a_wide_rectangle(self):
        self.assertEqual(rp._axes(0, 20, 0, 5, along_x=False)[0], False)

    def test_explicit_true_overrides_a_tall_rectangle(self):
        self.assertEqual(rp._axes(0, 5, 0, 20, along_x=True)[0], True)

    def test_a_square_can_be_forced_onto_y(self):
        # automatic: a tie goes to along_x (True); forced False must win anyway.
        self.assertEqual(rp._axes(0, 10, 0, 10)[0], True)
        self.assertEqual(rp._axes(0, 10, 0, 10, along_x=False)[0], False)

    def test_forced_mesh_and_wall_extension_share_the_forced_axis(self):
        # An off-centre satteldach ridge, forced onto y although width>=depth
        # would automatically pick x -- both the sheet and the walls must
        # place it on the SAME (forced) axis, not disagree with each other.
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.3, "h_mm": 900}]}, 8000)
        verts, _, _ = rp.profile_mesh(0, 12, 2, 10, 2.75, prof, along_x=False)
        ridge = [v for v in verts if abs(v[2] - (2.75 + 0.9)) < 1e-6]
        self.assertTrue(ridge)
        for v in ridge:
            self.assertAlmostEqual(v[0], 0 + 0.3 * 12, places=6)   # width is now the span
        walls = rp.wall_extension(0, 12, 2, 10, 2.75, 0.5, prof, 0.24, along_x=False)
        self.assertTrue(walls)
        # end-wall prisms are thin slabs (0.24m thick) CENTRED on the a0/a1
        # ends of the FORCED axis (y here: a0+overhang=2.5, a1-overhang=9.5).
        a_values = [v[1] for verts_, _ in walls for v in verts_]
        self.assertTrue(any(abs(a - 2.5) < 0.13 for a in a_values))
        self.assertTrue(any(abs(a - 9.5) < 0.13 for a in a_values))

    def test_resolve_profile_clamps_against_the_forced_span(self):
        # A profile tuned for a short (4 m) span clamps its slope (MAX_SLOPE *
        # 0.5 * 4000 = 3000mm cap, below the requested 3500); the SAME u/h on
        # a forced long (12 m) span (cap 9000mm) survives unclamped.
        saved = {"satteldach": {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 3500}]}}
        short = rp.resolve_profile(saved, "satteldach", 4000)
        long = rp.resolve_profile(saved, "satteldach", 12000)
        self.assertEqual(short["points"][0]["h_mm"], 3000)    # clamped
        self.assertEqual(long["points"][0]["h_mm"], 3500)     # unclamped

    def test_a_profile_survives_a_rotate_and_rotate_back_round_trip(self):
        saved = {"satteldach": {"form": "satteldach", "points": [{"u": 0.35, "h_mm": 1100}]}}
        span_before = 8000
        span_after_rotate = 12000
        # Rotating does not touch the SAVED dict at all -- only what span it
        # is resolved against when built/displayed.
        rp.resolve_profile(saved, "satteldach", span_after_rotate)
        back = rp.resolve_profile(saved, "satteldach", span_before)
        self.assertEqual(back["points"][0]["u"], 0.35)
        self.assertEqual(back["points"][0]["h_mm"], 1100)


class WingHeightAtTests(unittest.TestCase):
    """wing_height_at()/combined_height_at(): the per-point sampling that
    replaces the boolean union for a multi-wing roof."""

    def test_outside_the_wing_rectangle_is_none(self):
        wing = (0, 12, 0, 9)
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 9000)
        self.assertIsNone(rp.wing_height_at(-1, 4, wing, prof))
        self.assertIsNone(rp.wing_height_at(13, 4, wing, prof))
        self.assertIsNone(rp.wing_height_at(6, -1, wing, prof))
        self.assertIsNone(rp.wing_height_at(6, 10, wing, prof))

    def test_at_the_eave_is_zero_at_the_ridge_is_the_saved_height(self):
        wing = (0, 12, 0, 9)     # wider than deep -> ridge along x, cross = y
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 9000)
        self.assertAlmostEqual(rp.wing_height_at(6, 0, wing, prof), 0.0, places=6)
        self.assertAlmostEqual(rp.wing_height_at(6, 9, wing, prof), 0.0, places=6)
        self.assertAlmostEqual(rp.wing_height_at(6, 4.5, wing, prof), 1.5, places=6)
        # Constant along the ridge axis (x) at a fixed cross-position (y).
        self.assertAlmostEqual(rp.wing_height_at(0.5, 4.5, wing, prof),
                               rp.wing_height_at(11.5, 4.5, wing, prof), places=6)

    def test_a_tall_narrow_wing_uses_x_as_the_cross_axis(self):
        wing = (0, 4, 0, 12)    # deeper than wide -> ridge along y, cross = x
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 900}]}, 4000)
        self.assertAlmostEqual(rp.wing_height_at(2, 6, wing, prof), 0.9, places=6)
        self.assertAlmostEqual(rp.wing_height_at(0, 6, wing, prof), 0.0, places=6)     # eave (cross=x=0)
        # Constant along the ridge axis (y) at a fixed cross-position (x).
        self.assertAlmostEqual(rp.wing_height_at(2, 0.5, wing, prof),
                               rp.wing_height_at(2, 11.5, wing, prof), places=6)

    def test_combined_height_takes_the_taller_wing_in_the_overlap(self):
        wing_a = (0, 12, 4, 9)      # SIMPLE_L-style wings (see roof_wings.test.py)
        wing_b = (0, 4, 0, 9)
        prof_a = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 5000)
        prof_b = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 900}]}, 4000)
        x, y = 2.0, 6.5   # inside both rectangles
        h_a = rp.wing_height_at(x, y, wing_a, prof_a)
        h_b = rp.wing_height_at(x, y, wing_b, prof_b)
        self.assertEqual(rp.combined_height_at(x, y, [wing_a, wing_b], [prof_a, prof_b]), max(h_a, h_b))

    def test_a_point_outside_every_wing_is_none(self):
        wing_a = (0, 12, 4, 9)
        wing_b = (0, 4, 0, 9)
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 5000)
        self.assertIsNone(rp.combined_height_at(8, 2, [wing_a, wing_b], [prof, prof]))

    def test_along_x_override_forces_the_axis_even_against_auto_detection(self):
        # Codex second-opinion review, 2026-09-24, WB_125's Versetztes
        # Pultdach: wing_height_at() always auto-detected its OWN ridge
        # axis (the longer side), ignoring any `roof_axis_override` the
        # caller had already forced for the whole roof -- a real,
        # confirmed bug (this house's own "full" wing, wider than deep,
        # auto-detected along_x=True while the roof's forced axis was
        # False, sampling its height against the wrong span entirely).
        # This wing is wider than deep (12 x 9) -> auto-detects along_x=True.
        wing = (0, 12, 0, 9)
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 12000)
        # Forced along_x=False: cross axis is x (span=12), not the
        # auto-detected y (span=9) -- a different height at the same point.
        forced = rp.wing_height_at(3, 4, wing, prof, along_x=False)
        auto = rp.wing_height_at(3, 4, wing, prof)
        self.assertNotAlmostEqual(forced, auto, places=3)
        # Forced False -> ridge along y, cross = x: constant along y at fixed x.
        self.assertAlmostEqual(
            rp.wing_height_at(3, 0.5, wing, prof, along_x=False),
            rp.wing_height_at(3, 8.5, wing, prof, along_x=False), places=6)

    def test_combined_height_at_forwards_along_x_to_every_wing(self):
        # x=8 falls outside wing_b's own x-range (0..4), isolating wing_a's
        # own along_x behaviour in the combined result.
        wing_a = (0, 12, 4, 9)      # wider than deep -> auto-detects along_x=True
        wing_b = (0, 4, 0, 9)
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 12000)
        forced = rp.combined_height_at(8, 6.5, [wing_a, wing_b], [prof, prof], along_x=False)
        auto = rp.combined_height_at(8, 6.5, [wing_a, wing_b], [prof, prof])
        self.assertNotAlmostEqual(forced, auto, places=3)

    def test_combined_height_at_accepts_a_per_wing_axis_list(self):
        # Rainer, 2026-09-26, PER-WING-AXIS-OVERRIDE-001: two wings of an
        # L pitching in genuinely DIFFERENT directions at the same time --
        # a single shared along_x value can never express this, no matter
        # what it's set to (that's the whole point of the feature).
        wing_a = (0, 12, 4, 9)
        wing_b = (0, 4, 0, 9)
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 12000)
        # x=8 is only within wing_a; forcing wing_a's OWN axis to False
        # (ridge along y) must change ITS height there, independent of
        # whatever wing_b's own (here irrelevant) list entry says.
        per_wing_true = rp.combined_height_at(8, 6.5, [wing_a, wing_b], [prof, prof], along_x=[True, True])
        per_wing_mixed = rp.combined_height_at(8, 6.5, [wing_a, wing_b], [prof, prof], along_x=[False, True])
        self.assertNotAlmostEqual(per_wing_true, per_wing_mixed, places=3)
        # A per-wing list of all-True must match today's scalar True --
        # the list form is a strict generalisation, not a different rule.
        scalar_true = rp.combined_height_at(8, 6.5, [wing_a, wing_b], [prof, prof], along_x=True)
        self.assertAlmostEqual(per_wing_true, scalar_true, places=6)


class GableCapPolygonTests(unittest.TestCase):
    """Rainer, still on Doppelpultdach: "you are back to the 2
    doppelpultdach roofs" -- traced to SOLIDIFY's auto rim-fill choking
    on a non-convex gable outline (the step). render-exterior.py builds
    this polygon and triangulates it explicitly instead."""

    def test_starts_and_ends_at_the_eave_height_zero(self):
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 9000)
        pts = rp.gable_cap_polygon(0, 14, 0, 9, 2.75, prof, "a0")
        self.assertAlmostEqual(pts[0][2], 2.75, places=6)
        self.assertAlmostEqual(pts[-1][2], 2.75, places=6)

    def test_includes_both_step_heights_for_doppelpultdach(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 1642}, {"u": 0.39, "h_mm": 917}]}
        pts = rp.gable_cap_polygon(0, 14, 0, 9, 2.75, prof, "a0")
        zs_mm = [round((z - 2.75) * 1000) for _, _, z in pts]
        self.assertIn(1642, zs_mm)
        self.assertIn(917, zs_mm)

    def test_a0_and_a1_sit_at_the_two_true_gable_planes(self):
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 9000)
        pts_a0 = rp.gable_cap_polygon(0, 14, 0, 9, 2.75, prof, "a0")
        pts_a1 = rp.gable_cap_polygon(0, 14, 0, 9, 2.75, prof, "a1")
        self.assertTrue(all(x == 0 for x, y, z in pts_a0))       # ridge along x -> gables at x0/x1
        self.assertTrue(all(x == 14 for x, y, z in pts_a1))

    def test_matches_the_cross_section_used_by_the_roof_sheet_itself(self):
        # Same numbers wall_extension()/profile_mesh() would use -- no
        # separate source of truth to drift out of sync.
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 1642}, {"u": 0.39, "h_mm": 917}]}
        pts = rp.gable_cap_polygon(0.577, 14.467, 0.838, 9.851, 2.75, prof, "a1")
        section = rp._section(prof, 9.013)
        self.assertEqual(len(pts), len(section))
        for (x, y, z), (cross, height) in zip(pts, section):
            self.assertAlmostEqual(y, 0.838 + cross, places=6)
            self.assertAlmostEqual(z, 2.75 + height, places=6)


class GableCapPrismTests(unittest.TestCase):
    """The gable cap as its own solid prism -- Rainer, 2026-09-24, WB_125's
    Versetztes Pultdach: his own Blender screenshot showed real crossing
    facets from the tessellate-then-weld version of this cap (confirmed with
    a real bmesh.bvhtree overlap query; a Codex second opinion then
    confirmed this prism-based construction has no such defect in its own
    probes). Reuses `_prism()`, already proven throughout
    `wall_extension()` -- a genuinely separate, already-closed solid never
    needs merging into the roof sheet's own vertices, so there is nothing
    left for a weld pass to get wrong."""

    def test_is_closed_and_faces_outward(self):
        for form_profile in (
            {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]},
            {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 1642}, {"u": 0.39, "h_mm": 917}]},
            {"form": "doppelpultdach", "points": [{"u": 0.83, "h_mm": 2150}, {"u": 0.83, "h_mm": 1250}]},
        ):
            for end in ("a0", "a1"):
                verts, faces = rp.gable_cap_prism(0, 14, 0, 9, 2.75, form_profile, end, 0.22)
                use = edge_use(faces)
                for (a, b), count in use.items():
                    self.assertEqual(count, 1, "%s %s directed edge reused" % (form_profile["form"], end))
                    self.assertIn((b, a), use, "%s %s open edge" % (form_profile["form"], end))
                self.assertGreater(signed_volume(verts, faces), 1e-6,
                                   "%s %s inside-out or degenerate" % (form_profile["form"], end))

    def test_includes_both_step_heights_for_doppelpultdach(self):
        prof = {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 1642}, {"u": 0.39, "h_mm": 917}]}
        verts, _ = rp.gable_cap_prism(0, 14, 0, 9, 2.75, prof, "a0", 0.22)
        zs_mm = [round((v[2] - 2.75) * 1000) for v in verts]
        self.assertIn(1642, zs_mm)
        self.assertIn(917, zs_mm)

    def test_sits_flush_against_the_true_edge_extending_outward(self):
        # Rainer, 2026-09-24: an earlier version extended INWARD, which
        # z-fought with the roof sheet's own coplanar first row once
        # wing_height_at()'s axis fix made the sheet genuinely flat along
        # its own ridge axis there (see gable_cap_prism()'s own docstring).
        # Extending outward instead means it never shares any depth with
        # the sheet -- nothing left to fight over.
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 9000)
        verts_a0, _ = rp.gable_cap_prism(0, 14, 0, 9, 2.75, prof, "a0", 0.22)
        verts_a1, _ = rp.gable_cap_prism(0, 14, 0, 9, 2.75, prof, "a1", 0.22)
        xs_a0 = [v[0] for v in verts_a0]
        xs_a1 = [v[0] for v in verts_a1]
        # a0's INNER face is flush with the true edge (x=0); it extends
        # OUTWARD (negative x), never past x=0 into the roof's own territory.
        self.assertAlmostEqual(max(xs_a0), 0.0, places=9)
        self.assertLessEqual(max(xs_a0), 1e-9)
        self.assertAlmostEqual(min(xs_a1), 14.0, places=9)
        self.assertGreaterEqual(min(xs_a1), 14.0 - 1e-9)


class HeightfieldRoofMeshTests(unittest.TestCase):
    """The height-field roof sheet itself -- built once per multi-wing
    roof, never via a 3D boolean. Rainer, 2026-09-22, on the boolean
    version: "3 roofs in one a satteldach aand 2 doppelpult 90 degrees
    from each other" / "i dont want a walmdach instead of the
    doppelpultdach" -- these tests pin down the property that failed
    there: a single, non-self-overlapping sheet, for the SAME stepped
    doppelpultdach profile that broke the union."""

    WING_A = (0, 10, 4, 9)     # the SIMPLE_L fixture from roof_wings.test.py
    WING_B = (0, 4, 0, 9)

    def profiles(self, form):
        if form == "doppelpultdach":
            prof_a = rp.sanitize_profile(
                {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]},
                5000)
            prof_b = rp.sanitize_profile(
                {"form": "doppelpultdach", "points": [{"u": 0.39, "h_mm": 2150}, {"u": 0.39, "h_mm": 1200}]},
                4000)
            return prof_a, prof_b
        prof_a = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 5000)
        prof_b = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 900}]}, 4000)
        return prof_a, prof_b

    def test_the_sheet_is_a_single_non_self_overlapping_surface(self):
        # THE core regression test: every directed edge used at most once,
        # for the exact profile shape (doppelpultdach's step) that broke
        # the boolean union.
        for form in ("satteldach", "doppelpultdach"):
            prof_a, prof_b = self.profiles(form)
            verts, faces = rp.heightfield_roof_mesh(
                [self.WING_A, self.WING_B], [prof_a, prof_b], z_eave=2.75, step=0.5)
            use = edge_use(faces)
            for edge, count in use.items():
                self.assertEqual(count, 1, "%s: edge %s reused (self-overlap)" % (form, edge))

    def test_the_outer_boundary_lands_exactly_on_the_true_perimeter(self):
        prof_a, prof_b = self.profiles("satteldach")
        verts, faces = rp.heightfield_roof_mesh(
            [self.WING_A, self.WING_B], [prof_a, prof_b], z_eave=2.75, step=0.33)
        xs = {round(v[0], 6) for v in verts}
        ys = {round(v[1], 6) for v in verts}
        self.assertIn(0.0, xs)
        self.assertIn(10.0, xs)      # max x across both wings
        self.assertIn(0.0, ys)
        self.assertIn(9.0, ys)

    def test_covers_the_full_l_shape_no_missing_cells(self):
        prof_a, prof_b = self.profiles("satteldach")
        verts, faces = rp.heightfield_roof_mesh(
            [self.WING_A, self.WING_B], [prof_a, prof_b], z_eave=0.0, step=0.5)
        area = 0.0
        for a, b, c in faces:
            (x1, y1, _), (x2, y2, _), (x3, y3, _) = verts[a], verts[b], verts[c]
            area += abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2.0
        # SIMPLE_L area = 10*5 (wing_a) + 4*9 (wing_b) - 4*5 (overlap) = 50+36-20 = 66
        self.assertAlmostEqual(area, 66.0, delta=0.5)

    def test_a_vertex_height_matches_combined_height_at(self):
        prof_a, prof_b = self.profiles("doppelpultdach")
        verts, faces = rp.heightfield_roof_mesh(
            [self.WING_A, self.WING_B], [prof_a, prof_b], z_eave=2.75, step=0.5)
        for x, y, z in verts:
            expect = rp.combined_height_at(x, y, [self.WING_A, self.WING_B], [prof_a, prof_b])
            if expect is not None:
                self.assertAlmostEqual(z, 2.75 + expect, places=6)

    def test_height_wings_overrides_which_rectangles_the_height_is_sampled_from(self):
        # Rainer, 2026-09-22, still on Doppelpultdach after the self-
        # overlap fix: "i dont want a walmdach instead of the
        # doppelpultdach" -- the remaining break was wing_b's own flat
        # ridge (constant along y, its full/spanning axis in SIMPLE_L)
        # poking through wing_a's much-lower near-eave area (y close to
        # 4, wing_a's own u=0). Clipping wing_b's height-only rectangle
        # near the reflex point (roof_wings.clip_wing_to_valley()) and
        # passing it as `height_wings` should let wing_a's own low value
        # win there instead, with NO change to what the mesh covers.
        import roof_wings as rw
        prof_a = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 5000)
        prof_b = rp.sanitize_profile(
            {"form": "doppelpultdach", "points": [{"u": 0.3, "h_mm": 1800}, {"u": 0.3, "h_mm": 1200}]},
            4000)
        wings = [self.WING_A, self.WING_B]
        probe_x, probe_y = 1.2, 5.1     # inside wing_a's own eave, well past the margin from ry

        unclipped = rp.combined_height_at(probe_x, probe_y, wings, [prof_a, prof_b])
        self.assertGreater(unclipped, 1.0, "sanity: the spike is really there before clipping")

        rx, ry = rw.reflex_point(*wings)
        clipped_b = rw.clip_wing_to_valley(self.WING_B, self.WING_A, rx, ry, margin=0.5)
        height_wings = [self.WING_A, clipped_b]

        verts_default, faces_default = rp.heightfield_roof_mesh(
            wings, [prof_a, prof_b], z_eave=0.0, step=0.5)
        verts_clipped, faces_clipped = rp.heightfield_roof_mesh(
            wings, [prof_a, prof_b], z_eave=0.0, step=0.5, height_wings=height_wings)

        # Coverage (which (x,y) cells exist) is identical either way --
        # only the sampled HEIGHTS differ, which can flip a cell's
        # diagonal-split choice, so compare (x,y) footprints, not the
        # exact face/diagonal list.
        self.assertEqual(len(faces_default), len(faces_clipped))
        self.assertEqual({(round(x, 6), round(y, 6)) for x, y, _ in verts_default},
                         {(round(x, 6), round(y, 6)) for x, y, _ in verts_clipped})
        self.assertEqual(len(verts_default), len(verts_clipped))

        # The specific spike point is now much lower (wing_a's own low
        # near-eave value, not wing_b's step height). Look each mesh's
        # own nearest vertex up by (x,y) -- vertex COMPACTION can index
        # the two meshes differently even over the same (x,y) footprint.
        def nearest_z(verts):
            v = min(verts, key=lambda v: (v[0] - probe_x) ** 2 + (v[1] - probe_y) ** 2)
            return v[2]
        self.assertLess(nearest_z(verts_clipped), nearest_z(verts_default) - 0.5)

        # No holes introduced: every vertex still has SOME height (the
        # bigger, unclipped wing_a always covers the shared zone).
        for x, y, z in verts_clipped:
            self.assertIsNotNone(rp.combined_height_at(x, y, height_wings, [prof_a, prof_b]))

    def test_faces_point_up_before_solidify(self):
        prof_a, prof_b = self.profiles("satteldach")
        verts, faces = rp.heightfield_roof_mesh(
            [self.WING_A, self.WING_B], [prof_a, prof_b], z_eave=2.75, step=0.5)
        for face in faces:
            nx, ny, nz = rp._newell([verts[i] for i in face])
            self.assertGreaterEqual(nz, -1e-9, "face normal points downward")

    def test_a_single_wing_reduces_to_a_plain_rectangle_roof(self):
        prof = rp.sanitize_profile({"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}, 9000)
        verts, faces = rp.heightfield_roof_mesh([(0, 12, 0, 9)], [prof], z_eave=0.0, step=0.5)
        self.assertAlmostEqual(max(v[2] for v in verts), 1.5, places=6)
        self.assertAlmostEqual(min(v[2] for v in verts), 0.0, places=6)

    def test_no_loose_vertices_outside_the_l_shapes_missing_corner(self):
        # Rainer's real Blender build showed 541 disconnected "islands" for
        # one continuous roof sheet -- traced to loose, face-less grid
        # vertices (the corner cut off the bounding box to make the L)
        # confusing SOLIDIFY's rim-fill. Every returned vertex must be used
        # by at least one face.
        for form in ("satteldach", "doppelpultdach"):
            prof_a, prof_b = self.profiles(form)
            verts, faces = rp.heightfield_roof_mesh(
                [self.WING_A, self.WING_B], [prof_a, prof_b], z_eave=2.75, step=0.5)
            used = {i for face in faces for i in face}
            self.assertEqual(used, set(range(len(verts))), form)


class WallExtensionCombinedHeightTests(unittest.TestCase):
    """PER-WING-AXIS-OVERRIDE-001-FOLLOWUP, 2026-09-27: a real WB_125 render
    with wingA ridge along X / wingB ridge along Y (perpendicular -- the
    NORMAL look of any L-shaped gable roof, confirmed by Rainer as the
    intended shape) showed a torn gap at the wings' shared boundary.
    Codex read-only review + a hand-worked example (reproduced here)
    traced it to `wall_extension()`'s long-wall height coming from ONLY
    the `dominant` wing's own section, never checking whether the
    (correctly suppressed, so as not to double-build) OTHER wing's
    rectangle still covers that exact stretch with a genuinely taller
    roof. `all_wings`/`all_profiles`/`all_along_x` fix this; `None`
    (every other test in this file) must stay byte-identical."""

    # Mirrors the exact numbers from the Codex review's own synthetic
    # reproduction: wingA spans the full building width with its ridge
    # along X; wingB spans the full building depth (narrower in X) with
    # its ridge along Y. Both share the true south edge (y=0) -- a TIED
    # boundary, resolved by `dominant` (wingA, the bigger-by-area wing).
    WING_A = (0.0, 12.0, 0.0, 4.0)     # 12m x 4m, ridge along X
    WING_B = (0.0, 4.0, 0.0, 10.0)     # 4m x 10m, ridge along Y
    Z = 2.75
    OV = 0.3
    T = 0.24

    @staticmethod
    def _centred_gable(span_mm):
        return rp.sanitize_profile(
            {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 2000}]}, span_mm)

    def test_without_all_wings_the_old_underfill_is_reproduced(self):
        # Establishes the FAILURE this fix closes, so a future regression
        # in the opposite direction (silently reverting to own-wing-only
        # height) is caught by THIS test going back to passing, not by
        # only the new behaviour ever being checked.
        prof_a = self._centred_gable((self.WING_A[1] - self.WING_A[0]) * 1000)
        prof_b = self._centred_gable((self.WING_B[3] - self.WING_B[2]) * 1000)
        prisms = rp.wall_extension(
            *self.WING_A, self.Z, self.OV, prof_a, self.T,
            along_x=True, other_wing=self.WING_B, dominant=True)
        # South long wall: y close to 0, running along x (a long run).
        south_walls = [p for p in prisms
                       if max(v[0] for v in p[0]) - min(v[0] for v in p[0]) > 1.0
                       and max(v[1] for v in p[0]) < 1.0]
        self.assertTrue(south_walls, "wingA's own south long wall should still be built")
        tallest = max(v[2] for p in south_walls for v in p[0]) - self.Z
        # wingA's OWN height near its eave (cross close to overhang) is low
        # -- nowhere near wingB's true 2m ridge peak that also covers this
        # stretch. This is the confirmed defect: a real gap of well over
        # 1m between this wall's top and the true combined roof.
        self.assertLess(tallest, 1.0)

    def test_with_all_wings_the_south_wall_reaches_the_true_combined_height(self):
        prof_a = self._centred_gable((self.WING_A[1] - self.WING_A[0]) * 1000)
        prof_b = self._centred_gable((self.WING_B[3] - self.WING_B[2]) * 1000)
        prisms = rp.wall_extension(
            *self.WING_A, self.Z, self.OV, prof_a, self.T,
            along_x=True, other_wing=self.WING_B, dominant=True,
            all_wings=[self.WING_A, self.WING_B], all_profiles=[prof_a, prof_b],
            all_along_x=[True, False])
        # `ROOF-SWEEP-CONSTRUCTOR-001`, 2026-09-29: the south wall is now
        # built as several smaller ramp segments (dense safety sampling
        # against a real ~0.4m undershoot found on WB_125), not one single
        # long prism -- filter by position only (y near the south eave),
        # not by any one prism's own x-span, and aggregate the tallest
        # point across all of them.
        south_walls = [p for p in prisms if max(v[1] for v in p[0]) < 1.0]
        self.assertTrue(south_walls, "wingA's own south long wall should still be built")
        tallest = max(v[2] for p in south_walls for v in p[0]) - self.Z
        # wingB's own ridge (2m, centred on its 4m width -- x=2, well
        # within wingA's x-range too) is the true combined height along
        # most of this stretch, and x=2 IS one of wingB's own saved
        # profile breakpoints -- the fix splits and samples exactly there,
        # so this must be an exact match (within float tolerance), not
        # just "closer than before".
        self.assertAlmostEqual(tallest, 2.0 - 0.05, places=6)

    def test_a_shorter_wing_forced_to_the_same_axis_gets_a_step_closure(self):
        # `ROOF-SWEEP-CONSTRUCTOR-001`, 2026-09-29, Rainer: "if there are
        # height differences then you just treat it like a giebel" -- the
        # real WB_125 bug this reproduces: BOTH wings forced to the SAME
        # ridge axis (the automatic default when no per-wing override/drawn
        # path exists), so the SHORTER wing's own end sits well inside the
        # TALLER wing's own footprint -- `exposed_ranges()` correctly calls
        # that sub-range "internal" (no ordinary gable belongs there), but
        # the shorter wing's own roof is genuinely taller than the taller
        # wing reaches at that exact point, leaving an unsupported cliff in
        # a real hero-camera render. wingA (short, 1m peak) sits centred at
        # y=2 -- inside wingB's own y-range (0-10) -- while wingB (tall, 3m
        # peak, centred at y=5) is the one being built here; wingB's OWN
        # end wall at a=3.7 must therefore get an EXTRA step prism closing
        # the gap over wingA's own y-range, floating (not starting at the
        # ground), unlike an ordinary gable.
        wing_a = (0.0, 12.0, 0.0, 4.0)
        wing_b = (0.0, 4.0, 0.0, 10.0)
        prof_a = rp.sanitize_profile(
            {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1000}]}, 4000)
        prof_b = rp.sanitize_profile(
            {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 3000}]}, 10000)
        prisms = rp.wall_extension(
            *wing_b, self.Z, self.OV, prof_b, self.T,
            along_x=True, other_wing=wing_a, dominant=False,
            all_wings=[wing_a, wing_b], all_profiles=[prof_a, prof_b], all_along_x=[True, True])
        # A step prism at wingB's a1 end (x=3.7), spanning wingA's own
        # y-range (0.3-3.7, overhang-inset), floating well above wall-top.
        steps = [p for p in prisms
                 if abs(max(v[0] for v in p[0]) - 3.82) < 0.05
                 and min(v[2] for v in p[0]) > self.Z + 0.05]
        self.assertTrue(steps, "expected a floating step-closure prism at wingB's a1 end")
        self.assertGreater(min(v[2] for p in steps for v in p[0]), self.Z,
                           "step must float above wall-top, not start at the ground like an ordinary gable")

    def test_all_wings_none_is_byte_identical_to_every_existing_caller(self):
        # The regression-safety net for every OTHER test in this file and
        # every real single-wing/whole-house-axis-agrees caller in
        # render-exterior.py: omitting the new parameters must change
        # NOTHING.
        prof = rp.sanitize_profile(RoofSheetTests.CASES["gable centred"], 9000)
        a = rp.wall_extension(0, 12, 0, 9, self.Z, self.OV, prof, self.T)
        b = rp.wall_extension(0, 12, 0, 9, self.Z, self.OV, prof, self.T,
                              all_wings=None, all_profiles=None, all_along_x=None)
        self.assertEqual(a, b)


class MeshHeightAtTests(unittest.TestCase):
    """`ROOF-SWEEP-CONSTRUCTOR-001`, 2026-09-29: Codex's read-only design
    review reproduced a real, measured mismatch between `heightfield_roof_
    mesh()`'s own built triangle mesh and `combined_height_at()`'s analytic
    value at the same point -- a grid cell straddling the "which wing wins"
    crease picks one diagonal and triangulates flat across it, which is not
    always where that crease actually falls. `mesh_height_at()` reads the
    real mesh directly so a caller (namely `wall_extension()`) can use it
    as the sole authority instead of trusting the analytic function to
    match geometry it didn't actually build."""

    # Codex's own synthetic reproduction, verbatim: an L, wingA's ridge
    # along X (u=0.4, 1700mm), wingB's ridge along Y (u=0.6, 1300mm).
    WINGS = [(0, 10, 0, 4), (0, 4, 0, 10)]
    PROFILES = [
        {"form": "satteldach", "points": [{"u": 0.4, "h_mm": 1700}]},
        {"form": "satteldach", "points": [{"u": 0.6, "h_mm": 1300}]},
    ]

    def test_reproduces_codexs_measured_98_5mm_mismatch(self):
        # Codex's read-only design review reproduced a real, measured
        # mismatch between `heightfield_roof_mesh()`'s own built triangle
        # mesh and `combined_height_at()`'s analytic value at the same
        # point -- a grid cell straddling the "which wing wins" crease
        # picks one diagonal and triangulates flat across it, which is not
        # always where that crease actually falls. This test pins down the
        # exact, confirmed mismatch as a known, currently-unfixed property
        # of the wing-rectangle/height-field architecture (the attempted
        # exact-crease fix for this was tried and reverted the same day --
        # see ROOF-SWEEP-CONSTRUCTOR-001.md's own Progress log -- broke on
        # WB_125's real geometry despite passing this synthetic case).
        verts, faces = rp.heightfield_roof_mesh(self.WINGS, self.PROFILES, 0.0, step=0.3)
        x, y = 3.737374, 0.202020
        mesh_z = rp.mesh_height_at(verts, faces, x, y)
        analytic_z = rp.combined_height_at(x, y, self.WINGS, self.PROFILES)
        self.assertAlmostEqual(mesh_z, 0.313131, places=5)
        self.assertAlmostEqual(analytic_z, 0.214646, places=5)
        self.assertGreater(mesh_z - analytic_z, 0.09)   # the real, measured ~98.5mm gap

    def test_matches_the_analytic_function_away_from_any_crease(self):
        # Deep inside a single wing, far from any boundary or the other
        # wing's own overlap, both functions must agree closely -- this
        # mismatch is specifically a crease/boundary artefact, not a
        # general disagreement between the two representations.
        verts, faces = rp.heightfield_roof_mesh(self.WINGS, self.PROFILES, 0.0, step=0.3)
        x, y = 7.0, 2.0
        mesh_z = rp.mesh_height_at(verts, faces, x, y)
        analytic_z = rp.combined_height_at(x, y, self.WINGS, self.PROFILES)
        self.assertAlmostEqual(mesh_z, analytic_z, delta=0.02)

    def test_a_point_outside_every_triangle_returns_none(self):
        verts, faces = rp.heightfield_roof_mesh(self.WINGS, self.PROFILES, 0.0, step=0.3)
        self.assertIsNone(rp.mesh_height_at(verts, faces, 50.0, 50.0))


class WallExtensionRoofMeshTests(unittest.TestCase):
    """`wall_extension(roof_mesh=...)`: the wall must agree with the actual
    built roof mesh, not the analytic function that can disagree with it
    right at a wing-boundary crease (see `MeshHeightAtTests` above)."""

    WING_A = WallExtensionCombinedHeightTests.WING_A
    WING_B = WallExtensionCombinedHeightTests.WING_B
    Z = WallExtensionCombinedHeightTests.Z
    OV = WallExtensionCombinedHeightTests.OV
    T = WallExtensionCombinedHeightTests.T

    def _south_wall_tallest(self, prisms):
        # Position-only filter (not x-span) -- see the identical note in
        # `WallExtensionCombinedHeightTests` above: dense safety sampling
        # now splits the south wall into several smaller prisms.
        south_walls = [p for p in prisms if max(v[1] for v in p[0]) < 1.0]
        self.assertTrue(south_walls, "wingA's own south long wall should still be built")
        return max(v[2] for p in south_walls for v in p[0]) - self.Z

    def test_roof_mesh_none_is_byte_identical_to_the_analytic_only_path(self):
        prof_a = WallExtensionCombinedHeightTests._centred_gable(
            (self.WING_A[1] - self.WING_A[0]) * 1000)
        prof_b = WallExtensionCombinedHeightTests._centred_gable(
            (self.WING_B[3] - self.WING_B[2]) * 1000)
        common = dict(along_x=True, other_wing=self.WING_B, dominant=True,
                      all_wings=[self.WING_A, self.WING_B], all_profiles=[prof_a, prof_b],
                      all_along_x=[True, False])
        a = rp.wall_extension(*self.WING_A, self.Z, self.OV, prof_a, self.T, **common)
        b = rp.wall_extension(*self.WING_A, self.Z, self.OV, prof_a, self.T,
                              roof_mesh=None, **common)
        self.assertEqual(a, b)

    def test_roof_mesh_given_matches_the_actual_mesh_not_the_analytic_value(self):
        prof_a = WallExtensionCombinedHeightTests._centred_gable(
            (self.WING_A[1] - self.WING_A[0]) * 1000)
        prof_b = WallExtensionCombinedHeightTests._centred_gable(
            (self.WING_B[3] - self.WING_B[2]) * 1000)
        verts, faces = rp.heightfield_roof_mesh(
            [self.WING_A, self.WING_B], [prof_a, prof_b], self.Z, step=0.3,
            along_x=[True, False])
        prisms = rp.wall_extension(
            *self.WING_A, self.Z, self.OV, prof_a, self.T,
            along_x=True, other_wing=self.WING_B, dominant=True,
            all_wings=[self.WING_A, self.WING_B], all_profiles=[prof_a, prof_b],
            all_along_x=[True, False], roof_mesh=(verts, faces))
        tallest = self._south_wall_tallest(prisms)
        # Sample the same mesh directly at wingB's own ridge breakpoint
        # (x=2, the point the analytic-only test above already checks) --
        # the wall's height must match THIS, not a re-derivation of the
        # analytic formula, proving it actually queried the mesh.
        expected = rp.mesh_height_at(verts, faces, 2.0, 0.0 + self.OV) - self.Z - 0.05
        self.assertAlmostEqual(tallest, expected, places=5)


class DepthToMatchHeightTests(unittest.TestCase):
    """`_depth_to_match_height()` -- ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP-2,
    2026-09-30 (Rainer: "the bottom part of the smaller roof should stop
    when it hits the larger roof, the top part can go further"): how far
    into a wing's own rising slope, walking in from a given end, its own
    height first reaches some target -- the building block chevron_roof_
    construction() uses for a smaller wing's own per-point junction depth."""

    SECTION = [(0.0, 0.0), (5.0, 2.0), (10.0, 0.0)]        # a centred ridge

    def test_height_zero_is_always_zero_depth(self):
        self.assertEqual(rp._depth_to_match_height(self.SECTION, 10.0, True, 0.0), 0.0)
        self.assertEqual(rp._depth_to_match_height(self.SECTION, 10.0, False, 0.0), 0.0)

    def test_from_the_zero_end_walks_past_the_crossing_not_up_to_it(self):
        # ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP-3, 2026-10-01: stopping
        # exactly where the bigger wing's height first reaches the target
        # only makes them EQUAL there -- the smaller wing's own (constant)
        # height is still visible above the bigger wing's for the entire
        # stretch before it. The real crossing is at distance 2.5 (height 1
        # reached halfway up the 0..5 rising run); this must go PAST that,
        # not stop at it.
        self.assertGreater(rp._depth_to_match_height(self.SECTION, 10.0, True, 1.0), 2.5)
        self.assertAlmostEqual(rp._depth_to_match_height(self.SECTION, 10.0, True, 1.0), 5.0)
        # the ridge's own crossing (distance 5.0) would double to 10.0 --
        # ROOF-RIDGE-PER-FORM-001 follow-up, 2026-10-04 (Rainer: "fix it"):
        # was 10.0, which carried the smaller ridge over the bigger wing's
        # ridge and out of its back slope (3_5_1_b_145). Capped at the
        # bigger wing's own ridge now.
        self.assertAlmostEqual(rp._depth_to_match_height(self.SECTION, 10.0, True, 2.0), 5.0)

    def test_from_the_span_end_mirrors_the_walk(self):
        # a centred ridge is symmetric, so walking in from either end gives
        # the same depths for the same target heights.
        self.assertAlmostEqual(rp._depth_to_match_height(self.SECTION, 10.0, False, 1.0), 5.0)
        # was 10.0 before the 2026-10-04 ridge cap, see above.
        self.assertAlmostEqual(rp._depth_to_match_height(self.SECTION, 10.0, False, 2.0), 5.0)

    def test_an_off_centre_ridge_gives_different_depths_from_each_end(self):
        section = [(0.0, 0.0), (3.0, 3.0), (10.0, 0.0)]
        # was 6.0 / 10.0 before the 2026-10-04 ridge cap: both ran past the
        # ridge (at 3.0 from the zero end, 7.0 from the far end).
        self.assertAlmostEqual(rp._depth_to_match_height(section, 10.0, True, 3.0), 3.0)
        self.assertAlmostEqual(rp._depth_to_match_height(section, 10.0, False, 3.0), 7.0)

    def test_never_runs_past_the_bigger_wings_own_ridge(self):
        # ROOF-RIDGE-PER-FORM-001 follow-up, 2026-10-04: crossing at 2.0
        # doubles to 4.0, but the ridge is at 3.0 -- past it the bigger roof
        # falls away again and the smaller ridge would poke out.
        section = [(0.0, 0.0), (3.0, 3.0), (10.0, 0.0)]
        self.assertAlmostEqual(rp._depth_to_match_height(section, 10.0, True, 2.0), 3.0)
        # a lower target whose doubled depth stays short of the ridge is unchanged
        self.assertAlmostEqual(rp._depth_to_match_height(section, 10.0, True, 1.0), 2.0)

    def test_a_target_taller_than_the_section_ever_reaches_goes_all_the_way_through(self):
        # An unusual, steeper-branch-than-body case: extend at least all
        # the way through rather than come up short and leave a real gap.
        self.assertAlmostEqual(rp._depth_to_match_height(self.SECTION, 10.0, True, 99.0), 10.0)


class ChevronRoofConstructionTests(unittest.TestCase):
    """`ROOF-SWEEP-CONSTRUCTOR-001`, 2026-09-29 (Rainer: "you make the [roof]
    same width as the footprint and then close the holes after that you add
    the dachueberstand"): each wing built independently at its TRUE
    footprint extent, no height field, no max() reconciliation. Uses
    WB_125's own real numbers (the house that drove this whole
    investigation), not a synthetic fixture."""

    Z_EAVE = 2.75
    WALL_T = 0.24
    OV = 0.5
    # true, non-overlapping footprint (no overhang) -- main body + north extension
    WING_A = (1.077, 13.967, 1.338, 9.351)     # ridge along X
    WING_B = (1.077, 5.831, 9.351, 12.138)     # ridge along Y
    BASE_PROFILE = {"form": "satteldach", "points": [{"u": 0.4, "h_mm": 2250}]}

    def _profiles(self):
        span_a_mm = (self.WING_A[3] - self.WING_A[2]) * 1000
        span_b_mm = (self.WING_B[1] - self.WING_B[0]) * 1000
        prof = rp.sanitize_profile(self.BASE_PROFILE, 5000)
        return (rp.scale_profile_to_span(prof, 5000, span_a_mm),
               rp.scale_profile_to_span(prof, 5000, span_b_mm))

    def _build(self, overhang):
        prof_a, prof_b = self._profiles()
        return rp.chevron_roof_construction(
            [self.WING_A, self.WING_B], [prof_a, prof_b], [True, False],
            self.Z_EAVE, overhang, self.WALL_T)

    def test_same_axis_junction_is_refused_not_guessed(self):
        # Two wings sharing an edge with the SAME ridge axis is the harder
        # "real overlap/valley" case this function explicitly declines,
        # per its own docstring -- proven by two COLINEAR same-axis wings
        # (an extension in the same direction, gable to gable).
        wing_a = (0.0, 10.0, 0.0, 5.0)
        wing_b = (10.0, 16.0, 0.0, 5.0)     # shares the x=10 edge, BOTH along_x
        prof = rp.sanitize_profile(self.BASE_PROFILE, 5000)
        result = rp.chevron_roof_construction(
            [wing_a, wing_b], [prof, prof], [True, True], self.Z_EAVE, self.OV, self.WALL_T)
        self.assertIsNone(result)

    def test_the_junction_seam_matches_exactly_zero_tolerance(self):
        (roof_verts, roof_faces), prisms = self._build(0.0)
        # Chevron A's own north edge (the true junction, y=9.351) must sit
        # EXACTLY at z_eave (height 0) -- not approximately. Chevron A is
        # built FIRST, so its own verts are the first 6 in the combined
        # list -- must filter to those specifically, not chevron B's own
        # vertices at the SAME y (its south GABLE ring, whose peak is
        # legitimately non-zero; only its own edges are 0, checked by the
        # exact-height-match test that drove this whole construction).
        chevron_a_verts = roof_verts[:6]
        at_junction = [v for v in chevron_a_verts if abs(v[1] - 9.351) < 1e-9]
        self.assertTrue(at_junction)
        for v in at_junction:
            self.assertAlmostEqual(v[2], self.Z_EAVE, places=9)

    def test_no_self_intersection_in_the_roof_surface(self):
        # The exact structural property that eliminated WB_125's real,
        # confirmed self-intersections this session: every triangle/face of
        # the roof surface belongs to exactly one wing's own independent,
        # ordinary profile_mesh() -- there is no shared grid for two
        # surfaces to cross inside. Checked here by construction: each
        # wing's own verts/faces are contiguous, non-overlapping index
        # ranges (profile_mesh() never mixes vertices across wings).
        (roof_verts, roof_faces), _ = self._build(self.OV)
        # 2 wings, each profile_mesh() call contributes exactly 6 verts / 2 faces
        # (a single-ridge satteldach section has 3 points per ring x 2 rings).
        self.assertEqual(len(roof_verts), 12)
        self.assertEqual(len(roof_faces), 4)

    def test_overhang_extends_on_every_side_including_shared_ones(self):
        # ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP, 2026-09-30 (Rainer, on the
        # BIGGER wing's own side of a junction specifically: chevron A here
        # is the bigger wing, so its own shared north side still keeps the
        # plain overhang, exactly like any of its other, genuinely free
        # sides -- it never needs to extend deep, since chevron B (the
        # smaller wing) already covers that ground from its own side; see
        # the next two tests for chevron B's own, much deeper extension).
        (roof_verts, _), _ = self._build(self.OV)
        xs = sorted({round(v[0], 6) for v in roof_verts})
        ys = sorted({round(v[1], 6) for v in roof_verts})
        self.assertIn(round(1.077 - self.OV, 6), xs)
        self.assertIn(round(13.967 + self.OV, 6), xs)
        self.assertIn(round(1.338 - self.OV, 6), ys)
        self.assertIn(round(9.351 + self.OV, 6), ys)   # chevron A's own plain overhang, unchanged

    def test_smaller_wings_eave_points_stop_exactly_at_the_true_junction_edge(self):
        # ROOF-SWEEP-CONSTRUCTOR-001-FOLLOWUP-2, 2026-09-30 (Rainer,
        # refining the previous flat-depth version: "the bottom part of the
        # smaller roof should stop when it hits the larger roof, the top
        # part can go further"): chevron B's own EAVE points (height 0)
        # must sit exactly at the true junction edge (y=9.351) -- the
        # bigger wing is ALSO at height 0 there, so they already touch,
        # zero extra depth needed.
        (roof_verts, _), _ = self._build(self.OV)
        chevron_b_verts = roof_verts[6:]     # chevron B is built second
        eave_ys = {round(v[1], 6) for v in chevron_b_verts if abs(v[2] - self.Z_EAVE) < 1e-9}
        self.assertIn(9.351, eave_ys)

    def test_smaller_wings_ridge_extends_exactly_as_far_as_it_takes_not_a_flat_depth(self):
        # The ridge point (the tallest cross position) is a genuinely
        # DIFFERENT, much deeper extension than the eaves above -- computed
        # via the same `_depth_to_match_height()` the real code calls, so
        # this pins down the WIRING (right wing, right section, right end)
        # rather than re-deriving the geometry by hand.
        (roof_verts, _), _ = self._build(self.OV)
        chevron_b_verts = roof_verts[6:]
        ys = sorted({round(v[1], 6) for v in chevron_b_verts})
        prof_a, prof_b = self._profiles()
        _, o_true_span, _, _ = rp._axes(*self.WING_A, along_x=True)
        o_true_section = rp._section(prof_a, o_true_span)
        b_true_section = rp._section(prof_b, self.WING_B[1] - self.WING_B[0])
        ridge_h = max(h for _, h in b_true_section)
        expected_depth = rp._depth_to_match_height(o_true_section, o_true_span, False, ridge_h)
        expected_y = round(self.WING_B[2] - expected_depth, 6)
        self.assertAlmostEqual(min(ys), expected_y, places=6)
        self.assertGreater(expected_depth, self.OV)          # much deeper than a plain overhang
        self.assertLess(expected_depth, self.WING_A[3] - self.WING_A[2])  # short of a full crossing

    def test_bigger_wing_at_the_same_junction_keeps_only_the_plain_overhang(self):
        # The mirror check: chevron A (the bigger wing) must NOT also reach
        # deep into chevron B at this same junction -- only the smaller
        # wing extends; the bigger one is unaffected, unchanged from a
        # plain overhang on that side (already asserted loosely by the
        # previous test; pinned down exactly here).
        (roof_verts, _), _ = self._build(self.OV)
        chevron_a_verts = roof_verts[:6]
        ys = sorted({round(v[1], 6) for v in chevron_a_verts})
        self.assertAlmostEqual(min(ys), self.WING_A[2] - self.OV, places=6)
        self.assertAlmostEqual(max(ys), self.WING_A[3] + self.OV, places=6)

    def test_shared_junction_gable_stays_at_the_true_footprint_not_uniformly_expanded(self):
        # The WALLS are unaffected by the roof surface's own overlap above:
        # `wall_extension()`'s existing overhang-inset math always lands on
        # the TRUE footprint edge regardless of how far the roof rectangle
        # handed to it extends, and the junction gable (built separately,
        # from the wing's own true x0/x1/y0/y1, never the extended roof
        # rect) stays centred exactly on y=9.351 -- not naively pushed out
        # to y=8.851, which would float it over chevron A's own roof
        # mid-slope instead of the real wall corner.
        _, prisms = self._build(self.OV)
        self.assertGreater(len(prisms), 0)
        gable_prisms = [(verts, faces) for verts, faces in prisms
                        if max(v[1] for v in verts) - min(v[1] for v in verts) < 0.5
                        and min(v[1] for v in verts) < 9.4 and max(v[1] for v in verts) > 9.2]
        self.assertTrue(gable_prisms, "the junction gable should be findable near y=9.351")
        for verts, _ in gable_prisms:
            centre_y = (min(v[1] for v in verts) + max(v[1] for v in verts)) / 2.0
            self.assertAlmostEqual(centre_y, 9.351, places=6)
            base_z = min(v[2] for v in verts)
            self.assertAlmostEqual(base_z, self.Z_EAVE, places=6)


class VersetztesPultdachGableTests(unittest.TestCase):
    """Rainer, 2026-10-02, Blender screenshot of a Versetztes Pultdach: the
    gable wall climbed to the LOWER side of the vertical step and ran straight
    down, leaving an open 0.9 m triangle under the high slab ("the hole is
    not completely closed"). `_height_at()` is single-valued and skips
    vertical segments, so the step was dropped when the wall's top line was
    sampled."""

    # The real profile that failed: eave -> 0.816 m at mid-span -> straight up
    # to 1.716 m -> back down to the other eave.
    PROFILE = {"form": "doppelpultdach",
               "points": [{"u": 0.5, "h_mm": 816}, {"u": 0.5, "h_mm": 1716}]}
    Z = 5.5

    def _gable_tops(self, prisms):
        # every prism vertex at the south gable plane, as (x, z above eave)
        out = []
        for verts, _faces in prisms:
            ys = {round(v[1], 3) for v in verts}
            if max(ys) - min(ys) < 0.5:          # a gable prism, not a long wall
                out.append(sorted({(round(v[0], 3), round(v[2] - self.Z, 3)) for v in verts}))
        return out

    def test_the_gable_wall_reaches_the_high_side_of_the_step(self):
        prisms = rp.wall_extension(0.0, 8.0, 0.0, 12.0, self.Z, 0.5, self.PROFILE, 0.24,
                                   along_x=False, build_soffit=False)
        gables = self._gable_tops(prisms)
        self.assertTrue(gables, "no gable wall found")
        for pts in gables:
            heights_at_step = sorted(z for x, z in pts if abs(x - 4.0) < 1e-3)
            self.assertIn(0.816, heights_at_step)
            self.assertIn(1.716, heights_at_step)

    def test_a_profile_without_a_step_is_unchanged(self):
        flat = {"form": "satteldach", "points": [{"u": 0.5, "h_mm": 1500}]}
        prisms = rp.wall_extension(0.0, 8.0, 0.0, 12.0, self.Z, 0.5, flat, 0.24,
                                   along_x=False, build_soffit=False)
        for pts in self._gable_tops(prisms):
            self.assertEqual(sorted({z for x, z in pts if abs(x - 4.0) < 1e-3}), [1.5])

    def test_the_single_gable_closure_also_follows_the_step(self):
        prisms = rp.end_wall_and_soffit(0.0, 8.0, 0.0, 12.0, self.Z, 0.0, self.PROFILE, 0.24,
                                        "a0", along_x=False)
        tops = {round(v[2] - self.Z, 3) for verts, _f in prisms for v in verts
                if abs(v[0] - 4.0) < 1e-3}
        self.assertIn(1.716, tops)
        self.assertIn(0.816, tops)


if __name__ == "__main__":
    unittest.main()
