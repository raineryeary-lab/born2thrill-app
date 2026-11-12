"""Satteldach: das Hauptdach laeuft ueber die Fluegel weiter (HAUPTDACH-VERLAENGERT-001).

Rainer, 2026-11-05, bungalow_040_47: "not each small segment gets its own roof
but the main roof extends in those areas". Seine .blend von 15:30: First in der
Mitte des Hauptkoerpers (x 8,28 m), beide Flaechen ueber die Fluegel verlaengert.
"""
import ast
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUELLE = (HERE / "render-exterior.py").read_text(encoding="utf-8")


def laden():
    baum = ast.parse(QUELLE)
    knoten = [n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name == "hauptdach_verlaengerbar"]
    ns = {}
    exec(compile(ast.Module(body=knoten, type_ignores=[]), "hauptdach_verlaengerbar", "exec"), ns)
    return ns["hauptdach_verlaengerbar"]


# bungalow_040_47 in Metern: Hauptkoerper und zwei Fluegel an den Stirnseiten.
HAUPT = (1.397, 15.157, 2.0, 10.34)
SUED = (1.397, 9.4, 1.008, 2.0)
NORD = (1.397, 9.4, 10.34, 13.388)


class Erkennen(unittest.TestCase):
    def setUp(self):
        self.f = laden()

    def test_bungalow_040_47(self):
        self.assertIs(self.f([HAUPT, SUED, NORD]), False)          # First laeuft in y

    def test_vorgabe_y_passt(self):
        self.assertIs(self.f([HAUPT, SUED, NORD], False), False)

    def test_vorgabe_x_passt_nicht(self):
        self.assertIsNone(self.f([HAUPT, SUED, NORD], True))

    def test_fluegel_an_der_langseite_nicht(self):
        seite = (15.157, 18.0, 4.0, 8.0)                            # haengt seitlich am Hauptkoerper
        self.assertIsNone(self.f([HAUPT, SUED, seite], False))

    def test_fluegel_breiter_als_der_hauptkoerper_nicht(self):
        breit = (0.0, 16.5, 10.34, 11.0)
        self.assertIsNone(self.f([HAUPT, SUED, breit], False))


class Naht(unittest.TestCase):
    def test_drei_teile_gehen_in_den_einfirst(self):
        self.assertIn("footprint and len(massing_rects) >= 2):", QUELLE)

    def test_einfirst_ruft_die_pruefung(self):
        self.assertIn("along_x = hauptdach_verlaengerbar(rects, along_x_vorgabe)", QUELLE)

    def test_first_in_der_mitte(self):
        self.assertIn("kanten = [(lo + hi) / 2.0]", QUELLE)


if __name__ == "__main__":
    unittest.main()
