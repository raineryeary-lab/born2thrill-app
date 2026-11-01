"""Explicit facade must survive overlapping Flur/Luftraum room edges."""
import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def builder():
    spec = importlib.util.spec_from_file_location("outline_merge_builder", HERE / "build-simplifier-render-plan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rect(a, b, c, d):
    return [[a, b], [c, b], [c, d], [a, d]]


def wall(name, x, y0, y1, kind):
    return {"id": name, "start_mm": [x, y0], "end_mm": [x, y1],
            "thickness_mm": 240 if kind == "exterior" else 120,
            "wall_type": kind, "rooms": [] if kind == "exterior" else ["flur", "void"]}


def segment(w):
    return tuple(sorted(tuple(round(v, 3) for v in p) for p in (w["start_mm"], w["end_mm"])))


OUTLINE = [[0, 0], [9000, 0], [9000, 4000], [10000, 4000],
           [10000, 7500], [9000, 7500], [9000, 11000], [0, 11000]]
ROOMS = [
    {"id": "flur", "name": "Flur", "kind": "circulation", "polygon_mm": rect(5500, 4000, 9880, 7380)},
    {"id": "void", "name": "Luftraum", "kind": "luftraum", "polygon_mm": rect(8500, 5000, 9880, 7380)},
    {"id": "bath", "name": "Bad", "kind": "sanitary", "polygon_mm": rect(5500, 7500, 8880, 10880)},
]


class ExplicitOutlineMerge(unittest.TestCase):
    def setUp(self):
        self.b = builder()

    def test_closed_outline_survives_overlapping_void_room_and_cleanup(self):
        original = self.b._outline_to_walls(OUTLINE)
        rooms_before = copy.deepcopy(ROOMS)
        walls = self.b.build_walls(ROOMS, OUTLINE, outline_edge_tolerance_mm=420)
        removed = self.b.offene_deckenloch_waende(ROOMS, walls)
        kept = [w for w in walls if w["id"] not in removed]
        self.assertEqual({segment(w) for w in original},
                         {segment(w) for w in kept if w["wall_type"] == "exterior"})
        self.assertEqual(ROOMS, rooms_before)
        self.assertTrue(removed, "Real internal void boundaries must still open")
        self.assertTrue(any(w["wall_type"] == "interior" and "bath" in w["rooms"] for w in kept))

    def test_authoritative_exterior_preserved_in_both_input_orders(self):
        outside = wall("outside", 100, 0, 5000, "exterior")
        inside = wall("inside", 0, 0, 5000, "interior")
        for order in ([inside, outside], [outside, inside]):
            with self.subTest(order=[w["id"] for w in order]):
                snapshot = copy.deepcopy(order)
                out = self.b._merge_overlapping_parallel_walls(order, [], preserve_outline=True)
                self.assertEqual(len(out), 1)
                self.assertEqual(out[0], outside)
                self.assertEqual(order, snapshot)

    def test_partial_overlap_preserves_exact_interior_remnants(self):
        outside = wall("outside", 100, 1000, 4000, "exterior")
        inside = wall("inside", 0, 0, 5000, "interior")
        for order in ([inside, outside], [outside, inside]):
            out = self.b._merge_overlapping_parallel_walls(order, [], preserve_outline=True)
            self.assertIn(outside, out)
            interior = [w for w in out if w["wall_type"] == "interior"]
            self.assertEqual({segment(w) for w in interior},
                             {((0, 0), (0, 1000)), ((0, 4000), (0, 5000))})

    def test_real_interior_partition_not_near_outline_unchanged(self):
        inside = wall("inside", 2000, 0, 5000, "interior")
        outside = wall("outside", 0, 0, 5000, "exterior")
        self.assertEqual(self.b._merge_overlapping_parallel_walls(
            [inside, outside], [], preserve_outline=True), [inside, outside])

    def test_window_still_matches_same_explicit_facade_after_cleanup(self):
        walls = self.b.build_walls(ROOMS, OUTLINE, outline_edge_tolerance_mm=420)
        removed = self.b.offene_deckenloch_waende(ROOMS, walls)
        walls = [w for w in walls if w["id"] not in removed]
        match = self.b.nearest_wall(walls, [9880, 5500], [9880, 6200])
        self.assertIsNotNone(match)
        distance, host, _ = match
        self.assertAlmostEqual(distance, 0)
        self.assertEqual(host["wall_type"], "exterior")
        self.assertEqual(segment(host), ((9880, 4120), (9880, 7380)))


if __name__ == "__main__":
    unittest.main()

