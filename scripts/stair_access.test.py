"""A stair must be reachable at both ends.

Rainer, 2026-10-17, twostorey_058: "you also have to set up a warning if a
staircase is not accessible please the last one had a wall blocking the
entrance". An interior wall ran straight across the foot of the flight, 52 mm
from the first step, with no door in it -- built, rendered, and nothing said so.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "treppe_zugang.py"))
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)

# straight flight from (6463, 9026) up to (6463, 4683), 900 mm wide -- 058's
CORE = {"path_mm": [[6463.2, 9026.2], [6463.2, 4682.9]], "usable_width_mm": 900.0}

SIDES = [  # the stair room's long walls, parallel to the flight: no problem
    {"id": "links", "start_mm": [5771.6, 4660.7], "end_mm": [5771.6, 9044.0],
     "thickness_mm": 120, "wall_type": "interior"},
    {"id": "rechts", "start_mm": [7089.8, 8973.9], "end_mm": [7089.8, 2742.6],
     "thickness_mm": 120, "wall_type": "interior"},
]
QUER = {"id": "quer", "start_mm": [5771.6, 8973.9], "end_mm": [7089.8, 8973.9],
        "thickness_mm": 115, "wall_type": "interior", "rooms": ["a", "b"]}


def floors(eg_walls, eg_openings=(), og_walls=(), og_openings=()):
    return [{"level": "groundfloor", "walls": list(eg_walls), "openings": list(eg_openings)},
            {"level": "upperfloor", "walls": list(og_walls), "openings": list(og_openings)}]


class StairAccessTests(unittest.TestCase):
    def blocked(self, plan_floors, core=CORE):
        return plan_builder.stair_access_blocked(core, plan_floors)

    def test_058_wall_across_the_foot_is_reported(self):
        got = self.blocked(floors(SIDES + [QUER]))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["ende"], "antritt")
        self.assertEqual(got[0]["level"], "groundfloor")
        self.assertEqual(got[0]["wall_id"], "quer")

    def test_side_walls_alone_are_fine(self):
        self.assertEqual(self.blocked(floors(SIDES)), [])

    def test_a_door_in_that_wall_makes_it_reachable(self):
        tuer = {"wall_id": "quer", "opening_type": "door", "position": 0.525,
                "width_mm": 900, "traversable": True}
        self.assertEqual(self.blocked(floors(SIDES + [QUER], [tuer])), [])

    def test_a_window_in_that_wall_does_not(self):
        fenster = {"wall_id": "quer", "opening_type": "window", "position": 0.525,
                   "width_mm": 900, "traversable": False}
        self.assertEqual(len(self.blocked(floors(SIDES + [QUER], [fenster]))), 1)

    def test_a_wall_well_clear_of_the_foot_is_fine(self):
        weit = dict(QUER, start_mm=[5771.6, 10200], end_mm=[7089.8, 10200])
        self.assertEqual(self.blocked(floors(SIDES + [weit])), [])

    def test_a_wall_across_the_top_exit_is_reported_on_the_upper_floor(self):
        oben = dict(QUER, id="oben", start_mm=[5771.6, 4400], end_mm=[7089.8, 4400])
        got = self.blocked(floors(SIDES, og_walls=[oben]))
        self.assertEqual([(g["ende"], g["level"], g["wall_id"]) for g in got],
                         [("austritt", "upperfloor", "oben")])

    def test_wall_only_partly_across_leaves_a_way_past(self):
        halb = dict(QUER, start_mm=[5771.6, 8973.9], end_mm=[6300, 8973.9])
        self.assertEqual(self.blocked(floors(SIDES + [halb])), [])

    def test_floors_are_ordered_by_level_not_list_position(self):
        # 1_5_1: floors come as [attic, groundfloor]; the foot is on the EG.
        eg, og = floors(SIDES + [QUER])
        og = dict(og, level="attic")
        got = self.blocked([og, eg])
        self.assertEqual([(g["ende"], g["level"]) for g in got], [("antritt", "groundfloor")])

    def test_no_stair_no_findings(self):
        self.assertEqual(self.blocked(floors(SIDES + [QUER]), core=None), [])
        self.assertEqual(self.blocked([], core=CORE), [])


if __name__ == "__main__":
    unittest.main()
