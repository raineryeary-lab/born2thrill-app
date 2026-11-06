"""lochgelaender-wand-v1: the automatic Treppenloch railing leaves the edges
open that a wall guards, and the eye between two flights.

onehalfstorey_021, 2026-11-03: the wall check got metres against walls in mm,
found nothing, and a railing stood inside the outer wall. Geometry below is
that house's OG from plan-modern.json (go-baseline).
"""

import ast
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERER = HERE / "render-furnished-dollhouse.py"
NAMES = ("_clip_halfplane", "_polygon_area_mm2", "stair_hole_quads",
         "gelaender_freie_stuecke", "lochkante_luecken")


def load():
    tree = ast.parse(RENDERER.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    missing = set(NAMES) - {n.name for n in nodes}
    if missing:
        raise AssertionError(f"missing {sorted(missing)}")
    ns = {"math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(RENDERER), "exec"), ns)
    return ns


R = load()


def wall(wid, a, b, t):
    return {"id": wid, "start_mm": list(a), "end_mm": list(b), "thickness_mm": t}


WALLS = [
    wall("wall-0", (1096, 5305), (5463, 5305), 120),
    wall("wall-1", (5463, 699), (5463, 3605), 120),
    wall("wall-2", (5463, 5305), (5463, 9522), 120),
    wall("wall-5", (6901, 3605), (1096, 3605), 120),
    wall("wall-9", (1096, 699), (1096, 9522), 240),
]
BAND = [[3644, 3366], [1205, 3366], [1205, 5198], [3644, 5198],
        [3644, 4298], [2105, 4298], [2105, 4266], [3644, 4266]]
LOCH = R["stair_hole_quads"](BAND)


def gebaut_mm(a, b):
    """Built length of the automatic railing along a->b, in mm."""
    span = math.hypot(b[0] - a[0], b[1] - a[1])
    offen = sum(t1 - t0 for t0, t1 in R["lochkante_luecken"](a, b, WALLS, LOCH))
    return span * (1 - offen)


class Onehalfstorey021(unittest.TestCase):
    def test_loch_ist_geschnitten(self):
        self.assertTrue(LOCH)

    def test_kante_an_der_aussenwand_bleibt_offen(self):
        # loch-rail-1-right stood at x 1,18-1,23 m, inside wall-9.
        self.assertLess(gebaut_mm((1205, 3366), (1205, 5198)), 1)

    def test_kanten_an_innenwaenden_bleiben_offen(self):
        self.assertLess(gebaut_mm((1205, 3366), (3644, 3366)), 1)   # 170 mm vor wall-5
        self.assertLess(gebaut_mm((1205, 5198), (3644, 5198)), 1)   # 40 mm vor wall-0

    def test_treppenauge_bekommt_kein_gelaender(self):
        self.assertLess(gebaut_mm((2105, 4266), (3644, 4266)), 1)
        self.assertLess(gebaut_mm((2105, 4298), (3644, 4298)), 1)

    def test_freie_flurkante_wird_ganz_gebaut(self):
        # The Antritt end faces the Flur, no wall alongside: full railing.
        self.assertGreater(gebaut_mm((3644, 3366), (3644, 4266)), 850)


class Grundfall(unittest.TestCase):
    def test_gerade_treppe_ohne_wand(self):
        band = [[0, 0], [3000, 0], [3000, 1000], [0, 1000]]
        loch = R["stair_hole_quads"](band)
        luecken = R["lochkante_luecken"]((0, 0), (3000, 0), [], loch)
        self.assertEqual(luecken, [])

    def test_wand_nur_an_einem_ende(self):
        # A wall alongside the first metre only: open there, built after.
        w = [wall("w", (0, -200), (1000, -200), 120)]
        band = [[0, 0], [3000, 0], [3000, 1000], [0, 1000]]
        luecken = R["lochkante_luecken"]((0, 0), (3000, 0), w, R["stair_hole_quads"](band))
        self.assertEqual(len(luecken), 1)
        t0, t1 = luecken[0]
        self.assertEqual(t0, 0.0)
        self.assertAlmostEqual(t1 * 3000, 1000, delta=60)


if __name__ == "__main__":
    unittest.main()
