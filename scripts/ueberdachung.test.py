"""Ueberdachte Terrasse und Balkon, Plan UEBERDACHUNG-001.

Rainer, 2026-10-31: "it has to be the floor above it extended or the roof above
it extended". Geprueft wird die reine Geometrie ohne Blender.
"""
import importlib.util
import math
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ueberdachung", os.path.join(HERE, "ueberdachung.py"))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

# Hauswand von (0,0) nach (10000,0), die Terrasse liegt davor (y < 0).
WAND = [((0, 0), (10000, 0))]
TERRASSE = [(2000, 0), (6000, 0), (6000, -3000), (2000, -3000)]


def abstand(p, seg):
    (ax, ay), (bx, by) = seg
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def flaeche(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
                   for i in range(len(p)))) / 2


class Feld(unittest.TestCase):
    def test_nur_true_wird_weitergereicht(self):
        self.assertEqual(u.feld({"ueberdacht": True}), {"ueberdacht": True})
        self.assertEqual(u.feld({"ueberdacht": False}), {})
        self.assertEqual(u.feld({}), {})


class WasDeckt(unittest.TestCase):
    FLOORS = [{"level": "groundfloor", "balconies": []},
              {"level": "upperfloor", "balconies": [{"id": "b", "polygon_mm": TERRASSE, "ueberdacht": True}]}]

    def test_balkon_oben_bekommt_das_dach(self):
        f = u.flaechen({"exterior_areas": []}, self.FLOORS)
        self.assertEqual([(x["art"], x["ebene"], x["traeger"]) for x in f], [("balkon", 1, "dach")])

    def test_terrasse_unter_geschoss_bekommt_die_decke(self):
        plan = {"exterior_areas": [{"id": "t", "type": "terrasse", "level": "groundfloor",
                                    "points_mm": TERRASSE, "ueberdacht": True}]}
        f = [x for x in u.flaechen(plan, self.FLOORS) if x["art"] == "terrasse"]
        self.assertEqual(f[0]["traeger"], "decke")

    def test_bungalow_terrasse_bekommt_das_dach(self):
        plan = {"exterior_areas": [{"id": "t", "type": "terrasse", "points_mm": TERRASSE, "ueberdacht": True}]}
        f = u.flaechen(plan, [{"level": "groundfloor"}])
        self.assertEqual(f[0]["traeger"], "dach")

    def test_ohne_haekchen_nichts(self):
        plan = {"exterior_areas": [{"id": "t", "type": "terrasse", "points_mm": TERRASSE}]}
        self.assertEqual(u.flaechen(plan, [{"level": "groundfloor"}]), [])


class Dachgrundriss(unittest.TestCase):
    HAUS = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]

    def test_balkon_wird_teil_des_dachs(self):
        p = u.vereinigt(self.HAUS, [[(2.0, 10.0), (8.0, 10.0), (8.0, 12.0), (2.0, 12.0)]])
        self.assertAlmostEqual(flaeche(p), 112.0)
        self.assertEqual(len(p), 8)

    def test_luecke_zur_wand_wird_gefangen(self):
        p = u.vereinigt(self.HAUS, [[(2.0, 10.2), (8.0, 10.2), (8.0, 12.0), (2.0, 12.0)]])
        self.assertAlmostEqual(flaeche(p), 112.0)

    def test_terrasse_ueber_die_ganze_seite(self):
        p = u.vereinigt(self.HAUS, [[(0.0, 10.0), (10.0, 10.0), (10.0, 13.0), (0.0, 13.0)]])
        self.assertEqual(len(p), 4)
        self.assertAlmostEqual(flaeche(p), 130.0)

    def test_kleiner_versatz_in_der_zeichnung_verschwindet(self):
        p = u.vereinigt(self.HAUS, [[(0.0, 10.0), (5.0, 10.0), (5.0, 13.0), (5.07, 13.0),
                                     (5.07, 13.07), (0.0, 13.07)]])
        self.assertLessEqual(len(p), 6)

    def test_gegen_den_uhrzeigersinn(self):
        p = u.vereinigt(self.HAUS, [[(2.0, 10.0), (8.0, 10.0), (8.0, 12.0), (2.0, 12.0)]])
        self.assertGreater(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
                               for i in range(len(p))), 0)


class Pfosten(unittest.TestCase):
    def test_keine_pfosten_an_der_fassade(self):
        for p in u.pfosten(TERRASSE, WAND):
            self.assertGreater(abstand(p, WAND[0]), 300, p)

    def test_aeussere_ecken_haben_pfosten(self):
        stuetzen = u.pfosten(TERRASSE, WAND)
        for ecke in [(6000, -3000), (2000, -3000)]:
            self.assertLessEqual(min(math.dist(p, ecke) for p in stuetzen), 200, ecke)

    def test_nur_die_ecken_bei_normaler_breite(self):
        # Rainer, 2026-10-31: "too manyposts".
        breit = [(0, 0), (7800, 0), (7800, -2000), (0, -2000)]
        self.assertEqual(len(u.pfosten(breit, [((0, 0), (7800, 0))])), 2)

    def test_lange_kante_bekommt_eine_mittelstuetze(self):
        lang = [(0, 0), (12000, 0), (12000, -2000), (0, -2000)]
        self.assertEqual(len(u.pfosten(lang, [((0, 0), (12000, 0))])), 3)

    def test_kleiner_versatz_macht_keine_zusatzstuetze(self):
        mit_versatz = [(0, 0), (8000, 0), (8000, -3000), (5000, -3000), (5000, -3070), (0, -3070)]
        self.assertEqual(len(u.pfosten(mit_versatz, [((0, 0), (8000, 0))])), 2)

    def test_frei_stehende_flaeche_hat_alle_vier_ecken(self):
        frei = [(0, 0), (3000, 0), (3000, 3000), (0, 3000)]
        stuetzen = u.pfosten(frei, [])
        for ecke in frei:
            self.assertLessEqual(min(math.dist(p, ecke) for p in stuetzen), 200, ecke)

    def test_l_form_innenecke_ohne_pfosten(self):
        l_form = [(0, 0), (6000, 0), (6000, -2000), (3000, -2000), (3000, -4000), (0, -4000)]
        self.assertGreater(min(math.dist(p, (3000, -2000)) for p in u.pfosten(l_form, WAND)), 150)

    def test_flaeche_ueber_die_wand_hinaus(self):
        kurz = [((0, 0), (3000, 0))]
        flaeche_ = [(1000, 0), (6000, 0), (6000, -3000), (1000, -3000)]
        stuetzen = u.pfosten(flaeche_, kurz)
        for p in stuetzen:
            self.assertGreater(abstand(p, kurz[0]), 300, p)
        self.assertLessEqual(min(math.dist(p, (6000, 0)) for p in stuetzen), 200)

    def test_drehsinn_der_zeichnung_ist_egal(self):
        self.assertEqual(len(u.pfosten(list(reversed(TERRASSE)), WAND)), len(u.pfosten(TERRASSE, WAND)))


if __name__ == "__main__":
    unittest.main()
