"""Trennwand in the render plan: a "partition" element becomes a full-height
interior wall (12 cm default), and a door drawn on it attaches to it like to
any other wall. Rainer, 2026-09-20."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "build-simplifier-render-plan.py"))
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)

FRAME = plan_builder.Frame(10.0, 1000, 1000)      # 10 m wide, 10 m tall, y flipped


def annotations(extra_elements=(), partition=None):
    elements = [dict(e) for e in extra_elements]
    partition = {"id": "p1", "type": "partition", "floor_level": "groundfloor",
                 "points": [{"x": 0.2, "y": 0.5}, {"x": 0.8, "y": 0.5}], **(partition or {})}
    elements.append(partition)
    return {"elements": elements, "annotations": []}


def build(ann, level="groundfloor"):
    return plan_builder.build_floor_walls_and_openings([], [], ann, level, FRAME, level)


class TrennwandTests(unittest.TestCase):
    def test_partition_element_becomes_one_interior_wall_of_120_mm(self):
        walls, openings, unmatched, _ = build(annotations())
        self.assertEqual(len(walls), 1)
        wall = walls[0]
        self.assertEqual(wall["wall_type"], "interior")
        self.assertEqual(wall["thickness_mm"], 120)
        ys = {round(wall["start_mm"][1]), round(wall["end_mm"][1])}
        self.assertEqual(ys, {5000})
        self.assertEqual(sorted((round(wall["start_mm"][0]), round(wall["end_mm"][0]))), [2000, 8000])

    def test_chosen_thickness_is_used(self):
        walls, *_ = build(annotations(partition={"thickness_mm": 175}))
        self.assertEqual(walls[0]["thickness_mm"], 175)

    def test_partition_on_another_floor_is_not_built_here(self):
        walls, *_ = build(annotations(partition={"floor_level": "upperfloor"}))
        self.assertEqual(walls, [])

    def test_a_door_on_the_trennwand_finds_its_wall(self):
        door = {"id": "d1", "type": "door", "floor_level": "groundfloor",
                "points": [{"x": 0.45, "y": 0.5}, {"x": 0.55, "y": 0.5}]}
        walls, openings, unmatched, _ = build(annotations([door]))
        self.assertEqual(len(unmatched), 0)
        self.assertEqual([o["opening_type"] for o in openings], ["door"])
        self.assertEqual(openings[0]["wall_id"], walls[0]["id"])

    def test_a_projekt_without_partitions_builds_exactly_as_before(self):
        walls, *_ = build({"elements": [], "annotations": []})
        self.assertEqual(walls, [])

    def test_a_zero_length_partition_is_ignored(self):
        dot = {"points": [{"x": 0.5, "y": 0.5}, {"x": 0.5, "y": 0.5}]}
        walls, *_ = build(annotations(partition=dot))
        self.assertEqual(walls, [])


if __name__ == "__main__":
    unittest.main()
