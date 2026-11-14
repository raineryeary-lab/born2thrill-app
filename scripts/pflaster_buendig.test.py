"""Aussenflaechen liegen buendig im Rasen (pflaster-buendig-v1).

Rainer, 2026-10-22: "huge slabs of stuff" -- Terrasse, Gehweg und Einfahrt
schwebten 16 cm ueber dem Rasen (Rasen -0,16 m, Flaechen 0 m, ohne Seiten).
"""
import ast
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERER = HERE / "render-exterior.py"


def load():
    tree = ast.parse(RENDERER.read_text(encoding="utf-8"))
    keep = [n for n in tree.body
            if (isinstance(n, ast.FunctionDef) and n.name == "flaechen_z")
            or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("AREA_STACK_Z", "RASEN_Z")
                                                  for t in n.targets))]
    ns = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(RENDERER), "exec"), ns)
    return ns


class Buendig(unittest.TestCase):
    def setUp(self):
        self.ns = load()

    def test_eben_terrasse_knapp_ueber_rasen(self):
        self.assertAlmostEqual(self.ns["flaechen_z"]("terrasse", "eben", 0.0), -0.16 + 0.016)

    def test_eben_garten(self):
        self.assertAlmostEqual(self.ns["flaechen_z"]("garten", "eben", 0.0), -0.16 + 0.001)

    def test_hang_unveraendert(self):
        self.assertAlmostEqual(self.ns["flaechen_z"]("gehweg", "hang", 1.2), 1.2 + 0.011)

    def test_naht(self):
        self.assertIn("flaechen_z(area[\"type\"]", RENDERER.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
