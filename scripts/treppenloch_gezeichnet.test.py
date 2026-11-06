"""Treppenloch selbst zeichnen: a Treppenoeffnung area is the hole.

Plan: plans/treppenloch-selbst-zeichnen-v1.md.

Rainer, 2026-10-20: "we need a checkbox 'Treppenloch selbst zeichnen' and
then be able to draw the Gelaender" -- and then: "those walls where the
stairs are have to align, otherwise we have floors peeking out in the
middle of the walls, so somehow we need a snap in there".

The renderer functions are pulled out of the real files via ast (no bpy),
for both renderers; the plan-builder helper is imported from its module.
"""

import ast
import importlib.util
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERERS = (HERE / "render-furnished-dollhouse.py", HERE / "render-persp-test.py")
NAMES = ("_clip_halfplane", "_polygon_area_mm2", "stair_hole_quads", "slab_minus_hole",
         "konvexe_teile", "lochkanten_einrasten", "deckenloch_auto_kanten",
         "versatz_zur_wand_unten", "_wandflaeche_zum_loch", "austritt_abstand_zur_kante")


def load_renderer(source):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    missing = set(NAMES) - {n.name for n in nodes}
    if missing:
        raise AssertionError(f"{source.name}: missing {sorted(missing)}")
    namespace = {"math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


def load_plan_builder():
    spec = importlib.util.spec_from_file_location(
        "build_simplifier_render_plan", HERE / "build-simplifier-render-plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def area(polygon):
    return abs(sum(polygon[k][0] * polygon[(k + 1) % len(polygon)][1]
                   - polygon[(k + 1) % len(polygon)][0] * polygon[k][1]
                   for k in range(len(polygon)))) / 2.0


def inside(point, polygon):
    x, y = point
    hit = False
    for i in range(len(polygon)):
        x1, y1 = polygon[i - 1]
        x2, y2 = polygon[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def wall(wid, a, b, t=240):
    return {"id": wid, "start_mm": list(a), "end_mm": list(b), "thickness_mm": t}


ROOM = [[0.0, 0.0], [8000.0, 0.0], [8000.0, 6000.0], [0.0, 6000.0]]


class Gezeichnet:
    source = None

    def setUp(self):
        self.ns = load_renderer(self.source)

    # --- the drawn hole is cut out of other rooms' floors, concave too ------
    def test_l_foermiges_loch_aus_dem_flur(self):
        hole = [[2000.0, 1000.0], [5000.0, 1000.0], [5000.0, 2000.0],
                [3000.0, 2000.0], [3000.0, 4000.0], [2000.0, 4000.0]]
        teile = self.ns["konvexe_teile"](hole)
        self.assertAlmostEqual(sum(area(t) for t in teile), area(hole), delta=1.0)
        pieces = self.ns["slab_minus_hole"](ROOM, teile)
        self.assertAlmostEqual(sum(map(area, pieces)), area(ROOM) - area(hole), delta=1.0)
        self.assertTrue(any(inside((4000.0, 3000.0), p) for p in pieces),
                        "the inner corner of the L is floor")
        self.assertFalse(any(inside((2500.0, 3000.0), p) for p in pieces))

    # --- automatic railing edges: every edge except the Austritt ------------
    def test_austritt_bleibt_offen(self):
        hole = [[2000.0, 1000.0], [4000.0, 1000.0], [4000.0, 4000.0], [2000.0, 4000.0]]
        # stair arrives across the top edge (y = 4000), x 2100..3000
        kanten = self.ns["deckenloch_auto_kanten"](hole, ((2100.0, 4000.0), (3000.0, 4000.0)))
        self.assertEqual(sorted(kanten), [0, 1, 3])

    def test_austritt_mitten_im_loch_wird_gemessen(self):
        # twostorey_059 scratch build: the drawn hole ran 450 mm past the
        # Austritt -- the stair then ends in front of air and every edge
        # (rightly) has a railing. The distance is what the warning reports.
        hole = [[4053.0, 5818.0], [6451.0, 5818.0], [6451.0, 2205.0], [4053.0, 2205.0]]
        austritt = ((5999.0, 5828.0), (5999.0, 4928.0))
        self.assertAlmostEqual(self.ns["austritt_abstand_zur_kante"](hole, austritt), 452.0, delta=0.5)
        on_edge = [[4053.0, 5818.0], [5999.0, 5818.0], [5999.0, 2205.0], [4053.0, 2205.0]]
        self.assertAlmostEqual(self.ns["austritt_abstand_zur_kante"](on_edge, austritt), 0.0, delta=0.5)

    def test_ohne_austritt_alle_kanten(self):
        hole = [[0.0, 0.0], [1000.0, 0.0], [1000.0, 1000.0], [0.0, 1000.0]]
        self.assertEqual(sorted(self.ns["deckenloch_auto_kanten"](hole, None)), [0, 1, 2, 3])

    # --- snap: hole edges onto the wall face on the hole side ---------------
    def test_kante_40mm_vor_der_wand_rastet_auf_die_flaeche(self):
        # wall centre x = 1000, 240 thick -> face towards the hole at x = 1120
        walls = [wall("w1", (1000, -500), (1000, 6000))]
        hole = [[1160.0, 1000.0], [3000.0, 1000.0], [3000.0, 4000.0], [1160.0, 4000.0]]
        neu, log = self.ns["lochkanten_einrasten"](hole, walls)
        xs = sorted({round(p[0], 3) for p in neu})
        self.assertEqual(xs, [1120.0, 3000.0])
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0][1], "w1")
        self.assertAlmostEqual(abs(log[0][2]), 40.0, delta=0.01)

    def test_kante_in_der_wand_bleibt(self):
        # Revised by amendment A1 (2026-10-20): moving an edge from inside the
        # wall zone to the face lays slab over the stair (twostorey_059, the
        # stair drawn 59 mm into the wall -> verifier R3 failed). Only widen.
        walls = [wall("w1", (1000, -500), (1000, 6000))]
        hole = [[1080.0, 1000.0], [3000.0, 1000.0], [3000.0, 4000.0], [1080.0, 4000.0]]
        neu, log = self.ns["lochkanten_einrasten"](hole, walls)
        self.assertEqual(sorted({round(p[0], 3) for p in neu}), [1080.0, 3000.0])
        self.assertEqual(log, [])

    def test_zu_weit_oder_zu_schraeg_rastet_nicht(self):
        walls = [wall("w1", (1000, -500), (1000, 6000))]
        far = [[1300.0, 1000.0], [3000.0, 1000.0], [3000.0, 4000.0], [1300.0, 4000.0]]
        neu, log = self.ns["lochkanten_einrasten"](far, walls)
        self.assertEqual(log, [])
        self.assertEqual(neu, far)
        # 30 degrees off the wall: no snap
        steep = [[1160.0, 1000.0], [3000.0, 1000.0], [3000.0, 4000.0],
                 [1160.0 + 3000.0 * math.tan(math.radians(30)), 4000.0]]
        _, log = self.ns["lochkanten_einrasten"](steep, walls)
        self.assertNotIn(3, [k for k, _, _ in log])

    def test_ecke_zwei_waende(self):
        walls = [wall("w1", (1000, -500), (1000, 6000)), wall("w2", (-500, 1000), (6000, 1000))]
        hole = [[1150.0, 1150.0], [3000.0, 1150.0], [3000.0, 4000.0], [1150.0, 4000.0]]
        neu, log = self.ns["lochkanten_einrasten"](hole, walls)
        self.assertIn([1120.0, 1120.0], [[round(p[0], 3), round(p[1], 3)] for p in neu])
        self.assertEqual(sorted(w for _, w, _ in log), ["w1", "w2"])

    # --- the stairwell wall below must sit under the one above --------------
    def test_versatz_zur_wand_unten(self):
        face = ((1120.0, 1000.0), (1120.0, 4000.0))
        below = [wall("u1", (1060, -500), (1060, 6000))]
        self.assertAlmostEqual(self.ns["versatz_zur_wand_unten"](face, below), 60.0, delta=0.01)
        self.assertAlmostEqual(self.ns["versatz_zur_wand_unten"](
            face, [wall("u1", (1000, -500), (1000, 6000))]), 0.0, delta=0.01)
        self.assertIsNone(self.ns["versatz_zur_wand_unten"](face, []))


class FurnishedDollhouse(Gezeichnet, unittest.TestCase):
    source = RENDERERS[0]


class PerspTest(Gezeichnet, unittest.TestCase):
    source = RENDERERS[1]


class PlanBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_plan_builder()

    def test_deckenloch_art(self):
        art = self.mod.deckenloch_art
        self.assertEqual(art("Treppenöffnung", ["treppenoeffnung"]), "treppenoeffnung")
        self.assertEqual(art("Treppenoeffnung", None), "treppenoeffnung")
        self.assertEqual(art("Luftraum", ["luftraum"]), "luftraum")
        self.assertIsNone(art("Treppe", ["treppe"]))
        self.assertIsNone(art("Flur", ["flur"]))

    def test_offene_waende_nur_zum_flur(self):
        rooms = [{"id": "loch", "kind": "treppenoeffnung", "name": "Treppenöffnung"},
                 {"id": "flur", "kind": "circulation", "name": "Flur"},
                 {"id": "bad", "kind": "wet", "name": "Bad"}]
        walls = [{"id": "w-flur", "wall_type": "interior", "rooms": ["loch", "flur"]},
                 {"id": "w-bad", "wall_type": "interior", "rooms": ["loch", "bad"]},
                 {"id": "w-aussen", "wall_type": "exterior", "rooms": ["loch"]}]
        self.assertEqual(self.mod.offene_deckenloch_waende(rooms, walls), {"w-flur"})


if __name__ == "__main__":
    unittest.main()
