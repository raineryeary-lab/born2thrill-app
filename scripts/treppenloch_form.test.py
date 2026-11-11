"""The Treppenloch is the stair's own outline, not its bounding rectangle.

Plan: plans/treppenloch-folgt-treppenform-v1.md.

Measured on twostorey_059 (2026-10-20): the upper floor was cut open over the
whole 1965 x 3633 mm rectangle around a U stair. The Treppenauge between the
flights (about 1.07 x 1.83 m) and a notch beside the start were void, three
railings stood in the middle of that void, and the hallway edge of it had no
railing at all.

render-furnished-dollhouse.py imports bpy, so -- as in
render-furnished-dollhouse.test.py -- the REAL functions are pulled out of
the file via ast and executed without Blender. The same checks run against
render-persp-test.py, which is kept in step.
"""

import ast
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERERS = (HERE / "render-furnished-dollhouse.py", HERE / "render-persp-test.py")
NAMES = ("_clip_halfplane", "_polygon_area_mm2", "stair_hole_quads", "slab_minus_hole")

# shared_stair_core.polygon_mm of twostorey_059, exactly as in its plan-modern.json.
U_POLY = [[5602.7, 2194.9], [4033.9, 2194.9], [4033.9, 5828.0], [5999.0, 5828.0],
          [5999.0, 4928.0], [4933.9, 4928.0], [4933.9, 3094.9], [5602.7, 3094.9]]
# Its six manually chosen loch railings (loch_railing_sides).
U_RAILS = ["1-left", "0-left", "2-right", "2-left", "start", "0-right"]

ROOM = [[3000.0, 1000.0], [8000.0, 1000.0], [8000.0, 7000.0], [3000.0, 7000.0]]


def load(source):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    missing = set(NAMES) - {n.name for n in nodes}
    if missing:
        raise AssertionError(f"{source.name}: missing {sorted(missing)}")
    namespace = {"math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


def inside(point, polygon):
    """Strict-ish point-in-polygon (ray casting)."""
    x, y = point
    hit = False
    for i in range(len(polygon)):
        x1, y1 = polygon[i - 1]
        x2, y2 = polygon[i]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
    return hit


def area(polygon):
    return abs(sum(polygon[k][0] * polygon[(k + 1) % len(polygon)][1]
                   - polygon[(k + 1) % len(polygon)][0] * polygon[k][1]
                   for k in range(len(polygon)))) / 2.0


def rail_edges(poly):
    """Same split as the renderer's loch-rail code and annotate.js."""
    n = len(poly) // 2
    left, right = poly[:n], list(reversed(poly[n:]))
    edges = {}
    for i in range(n - 1):
        edges[f"{i}-left"] = (right[i], right[i + 1])
        edges[f"{i}-right"] = (left[i], left[i + 1])
    edges["start"] = (left[0], right[0])
    edges["end"] = (left[-1], right[-1])
    return edges


class TreppenlochForm:
    source = None

    def setUp(self):
        ns = load(self.source)
        self.quads = ns["stair_hole_quads"]
        self.cut = ns["slab_minus_hole"]

    def pieces(self, room, poly):
        quads = self.quads(poly)
        self.assertIsNotNone(quads)
        return self.cut(room, quads)

    # 1 -- straight stair: unchanged, the polygon IS the rectangle.
    def test_gerade_treppe_rechteck_wie_bisher(self):
        rect = [[4000.0, 2000.0], [4000.0, 5000.0], [4900.0, 5000.0], [4900.0, 2000.0]]
        pieces = self.pieces(ROOM, rect)
        self.assertAlmostEqual(sum(map(area, pieces)), area(ROOM) - 900.0 * 3000.0, delta=1.0)

    # 2 -- L stair: the empty corner of the bounding box stays floor.
    def test_l_treppe_ecke_bleibt_boden(self):
        l_poly = [[4000.0, 2000.0], [4000.0, 5900.0], [6900.0, 5900.0],
                  [6900.0, 5000.0], [4900.0, 5000.0], [4900.0, 2000.0]]
        pieces = self.pieces(ROOM, l_poly)
        self.assertAlmostEqual(sum(map(area, pieces)), area(ROOM) - area(l_poly), delta=1.0)
        self.assertTrue(any(inside((6000.0, 3000.0), p) for p in pieces),
                        "corner beside the turn must be floor")

    # 3 -- U stair (twostorey_059): Treppenauge and notch are floor.
    def test_u_treppe_treppenauge_und_kerbe_sind_boden(self):
        pieces = self.pieces(ROOM, U_POLY)
        self.assertAlmostEqual(sum(map(area, pieces)), area(ROOM) - area(U_POLY), delta=1.0)
        for point, what in (((5400.0, 4000.0), "Treppenauge"), ((5800.0, 2600.0), "Kerbe")):
            self.assertTrue(any(inside(point, p) for p in pieces), f"{what} must be floor")

    # 4 -- nothing lies over the stair itself.
    def test_kein_boden_ueber_der_treppe(self):
        pieces = self.pieces(ROOM, U_POLY)
        for x in range(4050, 6000, 50):
            for y in range(2210, 5820, 50):
                point = (x + 0.5, y + 0.5)
                if inside(point, U_POLY):
                    self.assertFalse(any(inside(point, p) for p in pieces),
                                     f"floor over the stair at {point}")

    # 5 -- an outline that is not a swept band is refused, so the caller
    #      falls back to the bounding box (never "no hole").
    def test_unbekannte_form_gibt_none(self):
        self.assertIsNone(self.quads([[0, 0], [1000, 0], [500, 800]]))
        self.assertIsNone(self.quads([]))

    # 5b -- a diagonal flight: quads are not axis-aligned, cut is still exact.
    def test_schraege_treppe(self):
        poly = [[4000.0, 2000.0], [6000.0, 4000.0], [6636.4, 3363.6], [4636.4, 1363.6]]
        pieces = self.pieces(ROOM, poly)
        self.assertAlmostEqual(sum(map(area, pieces)), area(ROOM) - area(poly), delta=1.0)

    # 6 -- every chosen railing has floor on its outer side, along its length.
    def test_jedes_gelaender_steht_auf_boden(self):
        pieces = self.pieces(ROOM, U_POLY)
        edges = rail_edges(U_POLY)
        for name in U_RAILS:
            (ax, ay), (bx, by) = edges[name]
            length = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / length, (bx - ax) / length
            for k in range(1, int(length // 100)):
                t = k * 100.0 / length
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                a = (px + nx * 50, py + ny * 50)
                b = (px - nx * 50, py - ny * 50)
                outer = b if inside(a, U_POLY) else a
                self.assertTrue(any(inside(outer, p) for p in pieces),
                                f"railing {name} borders a void at {outer}")


class FurnishedDollhouse(TreppenlochForm, unittest.TestCase):
    source = RENDERERS[0]


class PerspTest(TreppenlochForm, unittest.TestCase):
    source = RENDERERS[1]


if __name__ == "__main__":
    unittest.main()
