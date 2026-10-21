"""Amendment A1 of treppenloch-selbst-zeichnen-v1 -- four fixes found on the
twostorey_059 build of 2026-10-20 (void probe of the 11:31 go-baseline .blend):

1. A Luftraum cuts its hole out of every overlapping floor (the Flur kept its
   floor under it; both Luftraum railings stood in open floor).
2. Railings run up to a wall they meet end-on; only a wall ALONGSIDE leaves a
   gap (one railing was 1212 of 1616 mm).
3. The wall snap only widens the hole, never lays slab over the stair.
4. Verifier R3 tests the real opening, not its bounding box.

Renderer and verifier import bpy, so the pure functions are pulled out of the
real files via ast (no copies).
"""

import ast
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERER = HERE / "render-furnished-dollhouse.py"
VERIFIER = HERE / "verify_render_blend.py"
RENDER_NAMES = ("_clip_halfplane", "_polygon_area_mm2", "stair_hole_quads", "slab_minus_hole",
                "konvexe_teile", "lochkanten_einrasten", "_wandflaeche_zum_loch",
                "deckenloch_teile", "gelaender_freie_stuecke")


def load(source, names, extra=None):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    missing = set(names) - {n.name for n in nodes}
    if missing:
        raise AssertionError(f"{source.name}: missing {sorted(missing)}")
    namespace = {"math": math, **(extra or {})}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


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


# twostorey_059, 11:28 plan: the Flur rectangle covers the whole stairwell and
# the Luftraum sits inside it.
FLUR = [[4269.0, 7139.0], [7395.0, 7139.0], [7395.0, 975.0], [4269.0, 975.0]]
LUFTRAUM = [[4288.0, 5032.0], [5904.0, 5032.0], [5904.0, 2155.0], [4288.0, 2155.0]]
STAIR = [[5602.7, 2194.9], [4033.9, 2194.9], [4033.9, 5828.0], [5999.0, 5828.0],
         [5999.0, 4928.0], [4933.9, 4928.0], [4933.9, 3094.9], [5602.7, 3094.9]]


class A1Renderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load(RENDERER, RENDER_NAMES)

    # 1 -- Luftraum cuts overlapping floors ---------------------------------
    def test_luftraum_schneidet_den_flur(self):
        rooms = [{"kind": "circulation", "polygon_mm": FLUR},
                 {"kind": "luftraum", "polygon_mm": LUFTRAUM}]
        teile = self.ns["deckenloch_teile"](self.ns["stair_hole_quads"](STAIR), rooms)
        pieces = self.ns["slab_minus_hole"](FLUR, teile)
        for point, what in (((5400.0, 4000.0), "Treppenauge unter dem Luftraum"),
                            ((4600.0, 3500.0), "Luftraum ueber dem Lauf")):
            self.assertFalse(any(inside(point, p) for p in pieces), f"{what} must be open")
        self.assertTrue(any(inside((6800.0, 4000.0), p) for p in pieces), "Flur beside stays floor")

    def test_gezeichnetes_loch_ersetzt_die_treppe_luftraum_bleibt(self):
        drawn = [[4300.0, 2300.0], [5000.0, 2300.0], [5000.0, 3000.0], [4300.0, 3000.0]]
        rooms = [{"kind": "treppenoeffnung", "polygon_mm": drawn},
                 {"kind": "luftraum", "polygon_mm": [[6000.0, 6000.0], [7000.0, 6000.0],
                                                      [7000.0, 7000.0], [6000.0, 7000.0]]}]
        teile = self.ns["deckenloch_teile"](self.ns["stair_hole_quads"](STAIR), rooms)
        total = sum(area(t) for t in teile)
        self.assertAlmostEqual(total, area(drawn) + 1000.0 * 1000.0, delta=1.0)

    # 2 -- railings run to the wall -----------------------------------------
    def test_gelaender_endet_an_der_wand_die_es_trifft(self):
        # railing along y = 2155 from x 4692 to 5904; a wall stands across its
        # west end (vertical wall at x = 4300, face at 4420)
        walls = [wall("w-quer", (4300, 1000), (4300, 6000))]
        stuecke = self.ns["gelaender_freie_stuecke"]((4420.0, 2155.0), (5904.0, 2155.0), walls)
        self.assertEqual(len(stuecke), 1)
        self.assertAlmostEqual(stuecke[0][0], 0.0, delta=1e-9)
        self.assertAlmostEqual(stuecke[0][1], 1.0, delta=1e-9)

    def test_gelaender_laengs_an_der_wand_entfaellt(self):
        walls = [wall("w-laengs", (4000, 2000), (6500, 2000))]   # face at y = 2120, 35 mm away
        self.assertEqual(self.ns["gelaender_freie_stuecke"]((4420.0, 2155.0), (5904.0, 2155.0), walls), [])

    def test_wand_nur_am_mittelstueck(self):
        walls = [wall("w-mitte", (5000, 2000), (5400, 2000))]
        stuecke = self.ns["gelaender_freie_stuecke"]((4400.0, 2155.0), (6400.0, 2155.0), walls)
        self.assertEqual(len(stuecke), 2)
        self.assertLess(stuecke[0][1], 0.31)        # stops before x = 5000
        self.assertGreater(stuecke[1][0], 0.49)     # resumes after x = 5400

    # 3 -- the snap only widens ---------------------------------------------
    def test_kante_in_der_wand_bleibt(self):
        # A1 revision of test_kante_in_der_wand_rastet_auch_auf_die_flaeche:
        # moving this edge to the face would lay slab over the stair.
        walls = [wall("w1", (1000, -500), (1000, 6000))]
        hole = [[1080.0, 1000.0], [3000.0, 1000.0], [3000.0, 4000.0], [1080.0, 4000.0]]
        neu, log = self.ns["lochkanten_einrasten"](hole, walls)
        self.assertEqual(neu, hole)
        self.assertEqual(log, [])

    def test_kante_vor_der_wand_rastet_weiter(self):
        walls = [wall("w1", (1000, -500), (1000, 6000))]
        hole = [[1160.0, 1000.0], [3000.0, 1000.0], [3000.0, 4000.0], [1160.0, 4000.0]]
        neu, log = self.ns["lochkanten_einrasten"](hole, walls)
        self.assertEqual(sorted({round(p[0], 3) for p in neu}), [1120.0, 3000.0])


class A1Verifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        helpers = load(RENDERER, ("_clip_halfplane", "_polygon_area_mm2", "stair_hole_quads",
                                  "konvexe_teile"))
        cls.ns = load(VERIFIER, ("ueberdeckung_mm2", "r3_loch_teile"), helpers)

    def test_treppenauge_ist_kein_verschluss(self):
        teile = self.ns["r3_loch_teile"]({"shared_stair_core": {"polygon_mm": STAIR}}, {"rooms": []})
        # a floor face over the Treppenauge of THIS stair, running on into the
        # Flur (like floor-...-0 of the 11:31 build, which had the stair at
        # x 4270.. -- coordinates of one stair, not mixed)
        auge = [[4933.9, 3094.9], [7390.0, 3094.9], [7390.0, 4928.0], [4933.9, 4928.0]]
        self.assertLess(self.ns["ueberdeckung_mm2"](auge, teile), 10000.0)

    def test_boden_ueber_dem_lauf_wird_gefunden(self):
        teile = self.ns["r3_loch_teile"]({"shared_stair_core": {"polygon_mm": STAIR}}, {"rooms": []})
        ueber_lauf = [[4100.0, 3200.0], [4800.0, 3200.0], [4800.0, 4000.0], [4100.0, 4000.0]]
        self.assertAlmostEqual(self.ns["ueberdeckung_mm2"](ueber_lauf, teile), 700.0 * 800.0, delta=1.0)

    def test_gezeichnetes_loch_gilt(self):
        drawn = [[4300.0, 2300.0], [5000.0, 2300.0], [5000.0, 3000.0], [4300.0, 3000.0]]
        teile = self.ns["r3_loch_teile"]({"shared_stair_core": {"polygon_mm": STAIR}},
                                         {"rooms": [{"kind": "treppenoeffnung", "polygon_mm": drawn}]})
        self.assertAlmostEqual(sum(area(t) for t in teile), area(drawn), delta=1.0)


if __name__ == "__main__":
    unittest.main()
