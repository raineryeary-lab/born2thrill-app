"""Eine leere Gelaender-Wahl heisst "kein Gelaender" (gelaender-leere-wahl-v1).

Rainer, 2026-10-22, onehalfstorey_vv2: alle Treppenloch-Gelaender im Zeichner
abgeschaltet (loch_railing_sides = []), gebaut wurden trotzdem 7 automatische.
"""
import ast
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERER = HERE / "render-furnished-dollhouse.py"


def load():
    tree = ast.parse(RENDERER.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "manuelle_gelaenderseiten"]
    if not nodes:
        raise AssertionError("manuelle_gelaenderseiten fehlt")
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(RENDERER), "exec"), ns)
    return ns["manuelle_gelaenderseiten"]


KANTEN = {"0-left", "0-right", "1-left", "1-right", "start", "end"}


class LeereWahl(unittest.TestCase):
    def setUp(self):
        self.f = load()

    def test_nichts_gesetzt_automatisch(self):
        self.assertIsNone(self.f(None, KANTEN))

    def test_leer_heisst_kein_gelaender(self):
        self.assertEqual(self.f([], KANTEN), [])

    def test_altes_format_automatisch(self):
        self.assertIsNone(self.f(["north", "west"], KANTEN))

    def test_gueltige_wahl_bleibt(self):
        self.assertEqual(self.f(["0-left", "end"], KANTEN), ["0-left", "end"])

    def test_naht(self):
        self.assertIn("manuelle_gelaenderseiten(manual_sides", RENDERER.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
