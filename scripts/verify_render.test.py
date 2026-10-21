"""Tests for verify_render.py's cross-checks.

check_opening_counts counted door/window elements across the WHOLE project and
compared that total against EACH floor's plan count. Single-floor projects
(bungalow_040_66, the reference) passed by accident; every multi-floor project
failed with a mismatch that was pure arithmetic — onehalfstorey_020's 12
ground + 11 upper openings are exactly the 23 the annotation holds, and it was
reported as "mismatch of 11" and "mismatch of 12", excluding both styles from
the handoff.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_render", HERE / "verify_render.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opening(floor_level, kind="window"):
    return {"type": kind, "floor_level": floor_level,
            "points": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}]}


class OpeningCountTests(unittest.TestCase):
    def setUp(self):
        self.verifier = load_verifier()
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "annotations.json"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, elements):
        self.path.write_text(json.dumps({"elements": elements}), encoding="utf-8")
        return str(self.path)

    def plan(self, ground, upper):
        return {"floors": [
            {"id": "groundfloor", "name": "groundfloor", "level": "groundfloor",
             "openings": [{}] * ground},
            {"id": "upperfloor", "name": "upperfloor", "level": "upperfloor",
             "openings": [{}] * upper},
        ]}

    def test_each_floor_is_checked_against_its_own_openings(self):
        annotations = self.write([opening("groundfloor")] * 12 + [opening("upperfloor")] * 11)
        self.assertEqual(self.verifier.check_opening_counts(self.plan(12, 11), annotations), [])

    def test_a_floor_that_really_lost_an_opening_still_fails(self):
        annotations = self.write([opening("groundfloor")] * 12 + [opening("upperfloor")] * 11)
        failures = self.verifier.check_opening_counts(self.plan(12, 9), annotations)
        self.assertEqual(len(failures), 1)
        self.assertIn("upperfloor", failures[0])
        self.assertIn("mismatch of 2", failures[0])

    def test_single_floor_project_behaviour_is_unchanged(self):
        annotations = self.write([opening("groundfloor")] * 5)
        plan = {"floors": [{"id": "groundfloor", "name": "groundfloor",
                            "level": "groundfloor", "openings": [{}] * 5}]}
        self.assertEqual(self.verifier.check_opening_counts(plan, annotations), [])

    def test_excluded_openings_still_count_towards_the_floor_total(self):
        annotations = self.write([opening("groundfloor")] * 12 + [opening("upperfloor")] * 11)
        plan = self.plan(10, 11)
        plan["floors"][0]["openings_in_excluded_rooms"] = [{}, {}]
        self.assertEqual(self.verifier.check_opening_counts(plan, annotations), [])

    def test_elements_without_a_floor_are_not_silently_ignored(self):
        """An element with no floor_level belongs to no floor and would vanish
        from every per-floor comparison — it has to surface somewhere."""
        annotations = self.write([opening("groundfloor")] * 12 + [opening("upperfloor")] * 11
                                 + [{"type": "window", "points": []}])
        failures = self.verifier.check_opening_counts(self.plan(12, 11), annotations)
        self.assertTrue(any("no floor_level" in failure for failure in failures), failures)

    def test_a_plan_that_invents_openings_on_an_empty_floor_fails(self):
        """Zero annotated openings on a floor is a real number, not "no data" —
        a plan showing windows there has invented them."""
        annotations = self.write([opening("groundfloor")] * 12)
        failures = self.verifier.check_opening_counts(self.plan(12, 3), annotations)
        self.assertEqual(len(failures), 1, failures)
        self.assertIn("upperfloor", failures[0])

    def test_missing_annotations_path_is_skipped_not_failed(self):
        self.assertEqual(self.verifier.check_opening_counts(self.plan(1, 1), None),
                         ["skipped (no --annotations given)"])


if __name__ == "__main__":
    unittest.main()
