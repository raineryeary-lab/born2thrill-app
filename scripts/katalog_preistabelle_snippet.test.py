"""Preistabelle auf dem Grundriss-Katalog (plans/katalog-preistabelle-v1.md).

Rainer, 2026-11-07: "that one i need" ... "on the grundrisskatalog site".
"""
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade():
    spec = importlib.util.spec_from_file_location("katalog_preistabelle", HERE / "katalog-preistabelle-snippet.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ZEILEN = [
    {"plan": "bungalow_001", "haustyp": "bungalow", "zimmer": "3.0", "wohnflaeche_m2": "120", "preis_eur": "360000", "volumen_m3": "314"},
    {"plan": "onehalfstorey_002", "haustyp": "efh", "zimmer": "4.5", "wohnflaeche_m2": "150", "preis_eur": "450000", "volumen_m3": ""},
    {"plan": "twostorey_2_familien", "haustyp": "zfh", "zimmer": "6.0", "wohnflaeche_m2": "213", "preis_eur": "639000", "volumen_m3": "558"},
    {"plan": "ohne_flaeche", "haustyp": "efh", "zimmer": "4", "wohnflaeche_m2": "", "preis_eur": ""},
]


class Preistabelle(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.m.geschosse = lambda plan: set()
        self.d = self.m.daten(ZEILEN)

    def test_hausart_und_satztyp(self):
        self.assertEqual(self.d, [["Bungalow", "B", 3.0, 120.0, 360000, 314],
                                  ["Einfamilienhaus", "A", 4.5, 150.0, 450000, 0],
                                  ["Zweifamilienhaus", "Z", 6.0, 213.0, 639000, 558]])

    def test_nur_fuer_bearbeiter_und_editor_tauglich(self):
        php = self.m.php(self.d, "2026-11-07 16:30")
        self.assertIn("current_user_can( 'edit_posts' )", php)
        self.assertIn("grundriss_katalog", php)
        self.assertIn("Zweifamilienhaus", php)
        # Rainer, 2026-11-07: "could you actually put a price behind that" -- EUR/m2 am Faktor
        self.assertIn("m² Wohnfläche", php)
        self.assertIn("function qm(", php)
        # Rainer, 2026-11-07: "make a second slider with the volume please"
        self.assertIn("€ je m³", php)
        self.assertIn('data-modus="m3"', php)
        for verboten in ("\\", "`", "${"):
            self.assertNotIn(verboten, php)


if __name__ == "__main__":
    unittest.main()
