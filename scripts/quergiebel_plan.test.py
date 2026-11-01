"""Gezogene Quergiebel: Plan und Renderer-Regel (quergiebel-ziehen-v1)."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.mkdtemp())
import anderthalb as a  # noqa: E402


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_simplifier_render_plan", HERE / "build-simplifier-render-plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BBOX = (1.387, 11.179, 2.098, 11.348)


class PlanBauer(unittest.TestCase):
    def test_quergiebel_in_metern(self):
        b = load_builder()
        frame = b.Frame(10.0, 1000, 1000)          # 10 m je Einheit, y gespiegelt
        ann = {"elements": [
            {"type": "quergiebel", "floor_level": "upperfloor",
             "points": [{"x": 0.3, "y": 0.1}, {"x": 0.62, "y": 0.1}]},
            {"type": "quergiebel", "floor_level": "groundfloor",
             "points": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}]},
            {"type": "window", "floor_level": "upperfloor",
             "points": [{"x": 0.4, "y": 0.1}, {"x": 0.5, "y": 0.1}]},
        ]}
        qg = b.quergiebel_m(ann, "upperfloor", frame)
        self.assertEqual(len(qg), 1)
        self.assertAlmostEqual(qg[0]["a"]["x"], 3.0)
        self.assertAlmostEqual(qg[0]["b"]["x"], 6.2)
        self.assertAlmostEqual(qg[0]["a"]["y"], 9.0)

    def test_plan_traegt_es(self):
        quelle = (HERE / "build-simplifier-render-plan.py").read_text(encoding="utf-8")
        self.assertIn('"quergiebel": quergiebel_m(', quelle)


class Renderregel(unittest.TestCase):
    def test_gezeichnet_ersetzt_automatik(self):
        oeff = [("north", 5.0, 1.0, 2.1), ("south", 6.0, 1.2, 2.25)]
        g = a.giebel(BBOX, "satteldach", oeff, [],
                     gezeichnet=[((3.0, 11.348), (8.0, 11.348))])
        self.assertEqual(len(g), 1, g)
        self.assertEqual(g[0]["seite"], "north")
        self.assertAlmostEqual(g[0]["lo"], 3.0)
        self.assertAlmostEqual(g[0]["hi"], 8.0)
        self.assertEqual(g[0]["grund"], "gezogen")

    def test_richtung_egal_und_schmal_erlaubt(self):
        g = a.giebel(BBOX, "satteldach", [], [], gezeichnet=[((6.0, 2.1), (5.0, 2.1))])
        self.assertEqual(g[0]["seite"], "south")
        self.assertAlmostEqual(g[0]["lo"], 5.0)
        self.assertAlmostEqual(g[0]["hi"], 6.0)

    def test_ohne_gezeichnete_wie_bisher(self):
        oeff = [("north", 5.0, 1.0, 2.1), ("north", 6.6, 1.0, 2.1)]
        self.assertEqual(a.giebel(BBOX, "satteldach", oeff, [], gezeichnet=[]),
                         a.giebel(BBOX, "satteldach", oeff, []))

    def test_renderer_gibt_sie_weiter(self):
        quelle = (HERE / "render-exterior.py").read_text(encoding="utf-8")
        self.assertIn("gezeichnet=", quelle)
        self.assertIn('plan.get("quergiebel")', quelle)


if __name__ == "__main__":
    unittest.main()
