"""GLAS-SCHIEBETUER-001: the panel layout of the glass sliding wall.

Rainer, 2026-10-18: "one of the doors has to be half open to show that it is
a sliding door". `schiebefluegel` is pure math; pulled out of the real
renderer via ast like render-furnished-dollhouse.test.py does."""
import ast
import importlib.util
import math
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "render-furnished-dollhouse.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "schiebefluegel")
ns = {"math": math}
for k in tree.body:   # die Konstanten, die die Funktion liest, aus derselben Datei
    if isinstance(k, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith("SCHIEBE_") for t in k.targets):
        exec(compile(ast.Module(body=[k], type_ignores=[]), str(SOURCE), "exec"), ns)
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ns)
schiebefluegel = ns["schiebefluegel"]

spec = importlib.util.spec_from_file_location("plan_builder", HERE / "build-simplifier-render-plan.py")
plan_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_builder)


class Fluegel(unittest.TestCase):
    def test_panel_count(self):
        for n in (1, 2, 3):
            self.assertEqual(len(schiebefluegel(2.4, n)), n)

    def test_bad_count_is_two(self):
        self.assertEqual(len(schiebefluegel(2.4, 9)), 2)

    def test_exactly_one_panel_is_half_open(self):
        for n in (1, 2, 3):
            offen = [f for f in schiebefluegel(2.4, n) if f["offen"]]
            self.assertEqual(len(offen), 1, n)
            f = offen[0]
            self.assertAlmostEqual(abs(f["mitte"] - f["mitte_zu"]), f["breite"] / 2, places=6)

    def test_closed_panels_cover_the_whole_run(self):
        for n in (1, 2, 3):
            fl = schiebefluegel(2.4, n)
            links = min(f["mitte_zu"] - f["breite"] / 2 for f in fl)
            rechts = max(f["mitte_zu"] + f["breite"] / 2 for f in fl)
            self.assertAlmostEqual(links, -1.2, places=6)
            self.assertAlmostEqual(rechts, 1.2, places=6)

    def test_neighbours_run_on_different_tracks(self):
        fl = schiebefluegel(3.0, 3)
        self.assertNotEqual(fl[0]["spur"], fl[1]["spur"])
        self.assertNotEqual(fl[1]["spur"], fl[2]["spur"])

    def test_open_panel_stays_inside_the_run_when_there_is_a_neighbour(self):
        for n in (2, 3):
            f = [f for f in schiebefluegel(2.4, n) if f["offen"]][0]
            self.assertGreaterEqual(f["mitte"] - f["breite"] / 2, -1.2 - 1e-9)
            self.assertLessEqual(f["mitte"] + f["breite"] / 2, 1.2 + 1e-9)


class Schwebetueren(unittest.TestCase):
    """Rainer, 2026-11-01: "dont add the leiste on the floor thses would be
    schwebetueren". Die Fluegel haengen oben, am Boden liegt nichts."""

    def setUp(self):
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_glass_closet")
        self.quelle = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), fn)

    def test_nur_oben_eine_schiene(self):
        self.assertIn('"schiene-oben"', self.quelle)
        self.assertNotIn('"schiene-unten"', self.quelle)

    def test_kein_fluegelprofil_am_boden(self):
        self.assertNotIn('rahmen-{k}-u', self.quelle)


class Plan(unittest.TestCase):
    def test_symbol_is_specified_for_3d(self):
        spec = plan_builder.SYMBOL_3D["glasschiebetuer"]
        self.assertEqual(spec["type"], "glass_closet")
        self.assertEqual(spec["build"], "glass_closet")


if __name__ == "__main__":
    unittest.main()
