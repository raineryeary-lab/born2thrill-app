"""anderthalb.py -- 1,5-Geschosser. Plan: plans/anderthalbgeschosser-dach-v1.md."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anderthalb as a  # noqa: E402

# onehalfstorey_044, gemessen 2026-10-20: 9,79 x 9,25 m, First laengs x.
BBOX = (1.387, 11.179, 2.098, 11.348)


class Grundregeln(unittest.TestCase):
    def test_nur_anderthalb(self):
        self.assertTrue(a.ist_anderthalb({"plan_id": "onehalfstorey_044"}))
        self.assertTrue(a.ist_anderthalb({"house_type": "1.5-storey", "plan_id": "x"}))
        self.assertFalse(a.ist_anderthalb({"plan_id": "twostorey_059", "house_type": "2-storey"}))
        self.assertFalse(a.ist_anderthalb({"plan_id": "bungalow_007"}))

    def test_traufe_ein_meter_ueber_dem_og(self):
        self.assertAlmostEqual(a.traufhoehe(2.75), 3.75)

    def test_traufseiten(self):
        self.assertEqual(a.traufseiten(BBOX, "satteldach"), ["north", "south"])
        self.assertEqual(a.traufseiten(BBOX, "satteldach", along_x=False), ["east", "west"])
        self.assertEqual(a.traufseiten(BBOX, "walmdach"), ["north", "east", "south", "west"])

    def test_seite_von_wand(self):
        self.assertEqual(a.seite_von_wand((1.387, 11.348), (11.179, 11.348), BBOX), "north")
        self.assertEqual(a.seite_von_wand((1.387, 2.098), (1.387, 11.348), BBOX), "west")


class Giebel(unittest.TestCase):
    def test_044_balkontueren_nord_und_fenster_sued(self):
        # zwei 2,10-m-Tueren im Norden, ein Fenster im Sueden; dazu der
        # gezeichnete Ziergiebel Nord -- die Oeffnungen bestimmen.
        oeff = [("north", 5.0, 1.0, 2.1), ("north", 6.6, 1.0, 2.1),
                ("south", 6.0, 1.2, 2.25), ("west", 6.0, 1.2, 2.25)]
        g = a.giebel(BBOX, "satteldach", oeff, [("ziergiebel", "north")])
        nord = [x for x in g if x["seite"] == "north"]
        sued = [x for x in g if x["seite"] == "south"]
        self.assertEqual(len(nord), 1)                  # beide Tueren: ein Giebel
        self.assertAlmostEqual(nord[0]["lo"], 4.0)
        self.assertAlmostEqual(nord[0]["hi"], 7.6)
        self.assertEqual(len(sued), 1)
        self.assertAlmostEqual(sued[0]["hi"] - sued[0]["lo"], 2.5)   # Mindestbreite
        self.assertFalse(any(x["seite"] == "west" for x in g))       # Giebelseite

    def test_ohne_oeffnungen_quergiebel_drittel(self):
        g = a.giebel(BBOX, "satteldach", [], [("quergiebel", "south")])
        self.assertEqual(len(g), 1)
        self.assertAlmostEqual(g[0]["hi"] - g[0]["lo"], (BBOX[1] - BBOX[0]) / 3)
        self.assertAlmostEqual((g[0]["hi"] + g[0]["lo"]) / 2, (BBOX[0] + BBOX[1]) / 2)

    def test_ohne_oeffnungen_ziergiebel_zwei_meter(self):
        g = a.giebel(BBOX, "satteldach", [], [("ziergiebel", "north")])
        self.assertAlmostEqual(g[0]["hi"] - g[0]["lo"], 2.0)

    def test_niedrige_oeffnung_braucht_keinen(self):
        self.assertEqual(a.giebel(BBOX, "satteldach", [("north", 5.0, 0.6, 0.9)], []), [])

    def test_weit_auseinander_zwei_giebel(self):
        g = a.giebel(BBOX, "satteldach", [("north", 3.0, 1.0, 2.1), ("north", 9.0, 1.0, 2.1)], [])
        self.assertEqual(len(g), 2)

    def test_zwerchmasse(self):
        m = a.zwerch_masse(4.0, 7.6, traufe_z=3.75, wand_oben_z=5.50)
        t = math.tan(math.radians(40))
        self.assertAlmostEqual(m["first_z"], 5.50 + 1.8 * t)
        self.assertAlmostEqual(m["tiefe_traufe"], 1.75 / t)
        self.assertAlmostEqual(m["tiefe_first"], (m["first_z"] - 3.75) / t)



class Zwerchkubus(unittest.TestCase):
    """Plan anderthalb-zwerchkubus-modern-v1: moderne Variante, Kasten mit Flachdach."""

    def test_kubusmasse(self):
        m = a.kubus_masse(4.0, 7.6, traufe_z=3.75, wand_oben_z=5.50)
        t = math.tan(math.radians(40))
        self.assertAlmostEqual(m["dach_z"], 5.50 + a.ATTIKA_M)
        self.assertAlmostEqual(a.ATTIKA_M, 0.30)
        self.assertAlmostEqual(m["tiefe_wand"], 1.75 / t)
        self.assertAlmostEqual(m["tiefe_dach"], (5.80 - 3.75) / t)

    def test_dachform_und_zwerch(self):
        self.assertEqual(a.dachform_und_zwerch("satteldach-kubus"), ("satteldach", "kubus"))
        self.assertEqual(a.dachform_und_zwerch("satteldach"), ("satteldach", "giebel"))
        self.assertEqual(a.dachform_und_zwerch(" Walmdach "), ("walmdach", "giebel"))

    def test_renderer_nutzt_es(self):
        # Die Naht: render-exterior.py muss EXT_ROOF_TYPE hierueber lesen.
        quelle = (Path(__file__).resolve().parent / "render-exterior.py").read_text(encoding="utf-8")
        self.assertIn("anderthalb.dachform_und_zwerch(", quelle)
        self.assertIn("anderthalb.kubus_masse(", quelle)


class UeberDachPrisma(unittest.TestCase):
    """onehalfstorey_045, 2026-10-21: First Nord-Sued, die Giebelwaende blieben
    im Westen bis 8,7 m stehen -- der Schnittkoerper kreuzte sich selbst
    (Oberkante 13,7 m unter dem Ende seiner Dachlinie bei 15,3 m)."""

    def test_umriss_kreuzt_sich_nicht(self):
        t = math.tan(math.radians(40))
        for tief in (5.0, 13.76, 30.0):
            q = a.ueber_dach_profil(3.75, tief, 8.69, t)
            (s0, z0), (s1, z1), (s2, z2), (s3, z3) = q
            self.assertEqual((s0, s1, s2, s3), (-3.0, tief, tief, -3.0))
            self.assertGreater(z2, z1, "Oberkante unter dem Dachlinien-Ende: Umriss kreuzt sich")
            self.assertEqual(z2, z3)
            self.assertAlmostEqual(z1, 3.75 + tief * t)

    def test_renderer_nutzt_es(self):
        quelle = (Path(__file__).resolve().parent / "render-exterior.py").read_text(encoding="utf-8")
        self.assertIn("anderthalb.ueber_dach_profil(", quelle)


# onehalfstorey_vm2, Obergeschoss (Wandmitten, m): Hauptkoerper + Erker Ost.
VM2 = [((1.7772, 11.8254), (10.9167, 11.8254)), ((10.9167, 11.8254), (10.9167, 8.2352)),
       ((10.9167, 4.5209), (10.9167, 1.0254)), ((10.9167, 8.2352), (11.7372, 8.2352)),
       ((11.7372, 8.2352), (11.7372, 4.5209)), ((11.7372, 4.5209), (10.9167, 4.5209)),
       ((10.9167, 1.0254), (1.7772, 1.0254)), ((1.7772, 1.0254), (1.7772, 11.8254))]


class Erker(unittest.TestCase):
    """anderthalb-erker-zwerch-v1 (Rainer 2026-10-22: vm2 "the generated roof is totally off")."""

    def test_vm2_hauptkoerper_und_erker(self):
        bbox, erker = a.rechteck_mit_erkern(VM2)
        for ist, soll in zip(bbox, (1.777, 10.917, 1.025, 11.825)):
            self.assertAlmostEqual(ist, soll, places=2)
        self.assertEqual(len(erker), 1)
        e = erker[0]
        self.assertEqual(e["seite"], "east")
        self.assertAlmostEqual(e["lo"], 4.521, places=2)
        self.assertAlmostEqual(e["hi"], 8.235, places=2)
        self.assertAlmostEqual(e["tiefe"], 0.82, places=2)

    def test_rechteck_ohne_erker(self):
        r = [((0, 0), (10, 0)), ((10, 0), (10, 8)), ((10, 8), (0, 8)), ((0, 8), (0, 0))]
        bbox, erker = a.rechteck_mit_erkern(r)
        self.assertEqual(bbox, (0, 10, 0, 8))
        self.assertEqual(erker, [])

    def test_l_form_ist_kein_erker(self):
        # zweiter Fluegel 4 m tief: kein Erker
        l = [((0, 0), (10, 0)), ((10, 0), (10, 12)), ((10, 12), (6, 12)), ((6, 12), (6, 8)),
             ((6, 8), (0, 8)), ((0, 8), (0, 0))]
        self.assertIsNone(a.rechteck_mit_erkern(l))

    def test_gezogen_auf_der_erkerfront(self):
        bbox, erker = a.rechteck_mit_erkern(VM2)
        g = a.giebel(bbox, "satteldach", [], [], along_x=False,
                     gezeichnet=[((11.6172, 8.4855), (11.6172, 4.3944))], erker=erker)
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0]["seite"], "east")
        self.assertAlmostEqual(g[0]["vor"], 0.82, places=2)
        # Front ist die Erkerfront: nicht breiter als der Erker
        self.assertAlmostEqual(g[0]["lo"], 4.521, places=2)
        self.assertAlmostEqual(g[0]["hi"], 8.235, places=2)

    def test_automatik_erker_auf_traufseite(self):
        bbox, erker = a.rechteck_mit_erkern(VM2)
        g = a.giebel(bbox, "satteldach", [], [], along_x=False, erker=erker)
        ost = [x for x in g if x["seite"] == "east"]
        self.assertEqual(len(ost), 1)
        self.assertAlmostEqual(ost[0]["lo"], 4.521, places=2)
        self.assertAlmostEqual(ost[0]["hi"], 8.235, places=2)
        self.assertAlmostEqual(ost[0]["vor"], 0.82, places=2)

    def test_ohne_erker_vor_null(self):
        g = a.giebel(BBOX, "satteldach", [("north", 5.0, 1.0, 2.1)], [])
        self.assertEqual(g[0]["vor"], 0.0)

    def test_seitenprofil_ohne_erker_wie_bisher(self):
        self.assertEqual(a.zwerch_seitenprofil(0.02, 0.0, 2.75, 3.75, 2.0, 5.5),
                         [(-0.02, 3.70), (2.05, 5.5), (-0.02, 5.5)])

    def test_seitenprofil_mit_erker_ab_boden(self):
        q = a.zwerch_seitenprofil(0.94, 0.82, 2.75, 3.75, 2.0, 5.5)
        self.assertEqual(q[0], (-0.94, 2.75))
        self.assertEqual(q[-1], (-0.94, 5.5))
        self.assertIn((-0.02, 2.75), q)

    def test_renderer_nutzt_es(self):
        quelle = (Path(__file__).resolve().parent / "render-exterior.py").read_text(encoding="utf-8")
        self.assertIn("anderthalb.rechteck_mit_erkern(", quelle)
        self.assertIn("erker=AH_ERKER", quelle)


class Dachschraege(unittest.TestCase):
    """dollhouse-dachschraege-v1 (Rainer 2026-10-22: "why are the walls so chopped off?" -> "Slope like the roof")."""

    def test_keil_nordtraufe(self):
        t = math.tan(math.radians(40))
        verts, faces = a.dachschraege_keil("north", (0.0, 10.0, 0.0, 8.0), 2.0, 6.0, boden_z=0.0, tief=3.0)
        self.assertEqual(len(verts), 8)
        self.assertEqual({v[0] for v in verts}, {2.0, 6.0})
        # Die Dachlinie: an der Wandlinie (y=8) 1,0 m, nach innen steigend
        unten = sorted({(round(v[1], 6), round(v[2], 6)) for v in verts if v[2] < 5.0})
        (y_a, z_a), (y_b, z_b) = unten
        steigung = (z_a - z_b) / (y_b - y_a)
        self.assertAlmostEqual(steigung, t, places=6)
        z_an_wand = z_b + (y_b - 8.0) * t
        self.assertAlmostEqual(z_an_wand, 1.0, places=6)
        self.assertEqual(len(faces), 6)

    def test_keil_ost_x_konstant_entlang_y(self):
        verts, _ = a.dachschraege_keil("east", (0.0, 10.0, 0.0, 8.0), 1.0, 5.0, boden_z=0.0, tief=12.0)
        self.assertEqual({v[1] for v in verts}, {1.0, 5.0})

    def test_dollhouse_nutzt_es(self):
        quelle = (Path(__file__).resolve().parent / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
        self.assertIn("dachschraege_keil(", quelle)
        self.assertIn("gezeichnet=", quelle)
        self.assertIn("erker=", quelle)

class DachgeschossUeberObergeschossTests(unittest.TestCase):
    """DG-MIT-KNIESTOCK-001: EG + OG + DG (other_vito) -- das DG sitzt mit
    Kniestock unter dem Dach wie das Obergeschoss eines 1,5-Geschossers."""

    def test_dg_als_oberstes_geschoss_ist_anderthalb(self):
        plan = {"plan_id": "other_vito", "house_type": "other",
                "floors": [{"level": "groundfloor"}, {"level": "upperfloor"}, {"level": "attic"}]}
        self.assertTrue(a.ist_anderthalb(plan))

    def test_zweigeschosser_ohne_dg_bleibt_wie_er_ist(self):
        plan = {"plan_id": "twostorey_053", "house_type": "twostorey",
                "floors": [{"level": "groundfloor"}, {"level": "upperfloor"}]}
        self.assertFalse(a.ist_anderthalb(plan))


class EckErkerTests(unittest.TestCase):
    """DG-MIT-KNIESTOCK-001, other_vito: der Vorsprung laeuft bis an die
    Hausecke (eine Seitenwand, die andere buendig mit der Giebelwand)."""

    W = [((1.673, 12.066), (8.501, 12.066)), ((8.501, 12.066), (8.501, 1.600)),
         ((8.501, 1.600), (5.142, 1.600)), ((5.142, 1.600), (5.142, 0.860)),
         ((5.142, 0.860), (1.673, 0.860)), ((1.673, 0.860), (1.673, 12.066))]

    def test_eck_erker_wird_erkannt(self):
        r = a.rechteck_mit_erkern(self.W)
        self.assertIsNotNone(r)
        (x0, x1, y0, y1), erker = r
        self.assertAlmostEqual(y0, 1.600, places=3)
        self.assertEqual(len(erker), 1)
        e = erker[0]
        self.assertEqual(e["seite"], "south")
        self.assertAlmostEqual(e["tiefe"], 0.74, places=2)
        self.assertAlmostEqual(e["lo"], 1.673, places=3)
        self.assertAlmostEqual(e["hi"], 5.142, places=3)

    def test_reines_rechteck_bleibt_rechteck(self):
        R = [((0, 0), (8, 0)), ((8, 0), (8, 10)), ((8, 10), (0, 10)), ((0, 10), (0, 0))]
        self.assertEqual(a.rechteck_mit_erkern(R), ((0, 8, 0, 10), []))


class KeilRichtungTests(unittest.TestCase):
    """Die Dachschraegen-Keile muessen fuer ALLE vier Seiten nach aussen zeigen.

    other_vito, 2026-10-24: "the kniestock is missing". Nord- und West-Keil
    waren gespiegelt und damit innen-aussen verkehrt -- der Boolean schnitt
    dort nichts, die Traufwand blieb voll hoch. Betraf jeden 1,5-Geschosser
    auf einer Traufseite.
    """

    def volumen(self, v, f):
        s = 0.0
        for face in f:
            p = [v[i] for i in face]
            for i in range(1, len(p) - 1):
                a0, b, c = p[0], p[i], p[i + 1]
                s += (a0[0] * (b[1] * c[2] - b[2] * c[1]) - a0[1] * (b[0] * c[2] - b[2] * c[0])
                      + a0[2] * (b[0] * c[1] - b[1] * c[0]))
        return s / 6

    def test_alle_seiten_haben_positives_volumen(self):
        bb = (1.673, 8.501, 1.6, 12.066)
        for seite in ("north", "south", "east", "west"):
            lo, hi = (bb[0] - 2, bb[1] + 2) if seite in ("north", "south") else (bb[2] - 2, bb[3] + 2)
            v, f = a.dachschraege_keil(seite, bb, lo, hi)
            self.assertGreater(self.volumen(v, f), 0, seite)


class EckErkerOhneQuergiebelTests(unittest.TestCase):
    """other_vito, 2026-10-24: "why is there a quergiebel on this thing?" --
    ein Erker an der Hausecke bekommt KEINEN Zwerchgiebel; das Hauptdach
    laeuft in seiner Neigung darueber weiter (Kniestock dort niedriger)."""

    W = EckErkerTests.W

    def test_eck_erker_ist_markiert(self):
        (_, erker) = a.rechteck_mit_erkern(self.W)
        self.assertTrue(erker[0].get("ecke"))

    def test_eck_erker_bekommt_keinen_zwerch(self):
        bb, erker = a.rechteck_mit_erkern(self.W)
        self.assertEqual(a.giebel(bb, "satteldach", [], [], along_x=True, erker=erker), [])

    def test_erker_in_der_mitte_behaelt_seinen_zwerch(self):
        bb = (0.0, 10.0, 0.0, 8.0)
        erker = [{"seite": "south", "lo": 3.0, "hi": 6.0, "tiefe": 0.8}]
        g = a.giebel(bb, "satteldach", [], [], along_x=True, erker=erker)
        self.assertEqual(len(g), 1)


if __name__ == "__main__":
    unittest.main()
