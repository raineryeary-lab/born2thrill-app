"""Treppe nach oben im mittleren Geschoss (TREPPE-AUFWAERTS-001).

Rainer, 2026-11-01, twostorey_xvit und other_xvitv1: bei drei Geschossen zeigte
das mittlere nur den Lauf nach unten, die Treppe ins Geschoss darueber fehlte.
"""
import ast
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUELLE = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")


def laden():
    baum = ast.parse(QUELLE)
    knoten = [n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name == "treppenlaeufe"]
    ns = {}
    exec(compile(ast.Module(body=knoten, type_ignores=[]), "treppenlaeufe", "exec"), ns)
    return ns["treppenlaeufe"]


class Laeufe(unittest.TestCase):
    def setUp(self):
        self.f = laden()

    def test_unterstes_geschoss_nur_nach_oben(self):
        self.assertEqual(self.f(0, 3, 2.6), [(0.0, "stair-")])

    def test_mittleres_geschoss_hat_beide(self):
        self.assertEqual(self.f(1, 3, 2.6), [(0.0, "stairauf-"), (-2.6, "stair-")])

    def test_oberstes_geschoss_nur_nach_unten(self):
        self.assertEqual(self.f(2, 3, 2.6), [(-2.6, "stair-")])

    def test_zwei_geschosse_wie_bisher(self):
        self.assertEqual(self.f(0, 2, 2.6), [(0.0, "stair-")])
        self.assertEqual(self.f(1, 2, 2.6), [(-2.6, "stair-")])

    def test_der_untere_lauf_kommt_zuletzt(self):
        # top_step_front steuert den Austritt und muss vom Lauf nach unten stammen.
        self.assertEqual(self.f(1, 4, 2.6)[-1][1], "stair-")


class OhneAustritt(unittest.TestCase):
    def setUp(self):
        baum = ast.parse(QUELLE)
        knoten = [n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name == "ohne_austritt"]
        ns = {}
        exec(compile(ast.Module(body=knoten, type_ignores=[]), "ohne_austritt", "exec"), ns)
        self.f = ns["ohne_austritt"]

    def test_nur_der_austritt_bleibt_offen(self):
        stuecke = self.f([(0.0, 1.0)], (0, 0), (0, 2400), ((0, 1400), (0, 2400)))
        self.assertEqual(len(stuecke), 1)
        self.assertAlmostEqual(stuecke[0][1], 1400 / 2400)

    def test_austritt_in_der_mitte_teilt(self):
        self.assertEqual(len(self.f([(0.0, 1.0)], (0, 0), (0, 3000), ((0, 1000), (0, 2000)))), 2)


class KeinHandlaufErsatz(unittest.TestCase):
    def test_ohne_wahl_ist_das_loch_automatisch(self):
        self.assertNotIn('manual_sides = stair_core.get("railing_sides")', QUELLE)


class Naht(unittest.TestCase):
    def test_der_bau_ruft_es_auf(self):
        self.assertIn('treppenlaeufe(floor_index, len(plan["floors"]), risers * rise)', QUELLE)

    def test_antritt_bleibt_offen(self):
        self.assertIn('side == "start" and _hoch_weiter', QUELLE)


if __name__ == "__main__":
    unittest.main()
