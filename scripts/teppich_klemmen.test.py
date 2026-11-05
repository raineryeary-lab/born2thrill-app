"""Tests fuer teppich_klemmen.py -- Teppiche nie unter einer Wand.

    python scripts/teppich_klemmen.test.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teppich_klemmen import von_waenden_weg, wand_streifen  # noqa: E402


def wand(sx, sy, ex, ey, dicke):
    return {"start_mm": [sx, sy], "end_mm": [ex, ey], "thickness_mm": dicke}


# bungalow_040_36, Erdgeschoss, die Aussenwaende um den Wohnbereich
# (render_geometry, 2026-10-09). Raumkante x = 14890 / y = 1520 / x = 9934 --
# AUSSENSEITE, nicht Wandmitte.
WAENDE = [
    wand(10054, 5130, 10054, 1640, 240),
    wand(10054, 1640, 14770, 1640, 240),
    wand(14770, 1640, 14770, 12060, 240),
    wand(4569, 8262, 14890, 8262, 120),
    wand(3627, 8972, 4569, 8262, 120),   # schraeg -- uebersprungen
]


def innen(r, streifen):
    x0, y0 = r[0] - r[2] / 2, r[1] - r[3] / 2
    x1, y1 = r[0] + r[2] / 2, r[1] + r[3] / 2
    e = 1e-6
    return not any(x0 < s[2] - e and s[0] < x1 - e and y0 < s[3] - e and s[1] < y1 - e for s in streifen)


class TeppichKlemmen(unittest.TestCase):
    def test_der_gemeldete_fall_kommt_von_der_aussenwand_weg(self):
        streifen = wand_streifen(WAENDE)
        # Was der alte Code baute: 200 mm vor der Raumkante 14890 -> bis 14,69 m.
        tx, ty, b, t = 13.13, 3.37, 3.12, 3.30
        self.assertFalse(innen((tx, ty, b, t), streifen), "Ausgangslage muss die Wand treffen")
        neu = von_waenden_weg(tx, ty, b, t, streifen)
        self.assertTrue(innen(neu, streifen))
        # Rechte Kante vor der Innenseite (14,77 - 0,12) minus Abstand.
        self.assertLessEqual(neu[0] + neu[2] / 2, 14.77 - 0.12 - 0.05 + 1e-9)

    def test_ein_freier_teppich_bleibt_unveraendert(self):
        streifen = wand_streifen(WAENDE)
        self.assertEqual(von_waenden_weg(12.0, 4.5, 2.0, 2.0, streifen), (12.0, 4.5, 2.0, 2.0))

    def test_es_wird_die_billigste_kante_gekuerzt(self):
        # Wand rechts schneidet 0,1 m hinein: rechts kuerzen, nicht links.
        streifen = [(4.95, -10, 5.2, 10)]
        tx, ty, b, t = von_waenden_weg(4.0, 0.0, 2.0, 2.0, streifen)
        self.assertAlmostEqual(tx - b / 2, 3.0)
        self.assertAlmostEqual(tx + b / 2, 4.95)
        self.assertAlmostEqual(t, 2.0)

    def test_schraege_waende_werden_uebersprungen(self):
        self.assertEqual(len(wand_streifen([wand(0, 0, 1000, 1000, 120)])), 0)

    def test_ganz_ueberdeckt_heisst_weg(self):
        self.assertEqual(von_waenden_weg(0, 0, 1, 1, [(-5, -5, 5, 5)])[2], 0.0)


if __name__ == "__main__":
    unittest.main()
