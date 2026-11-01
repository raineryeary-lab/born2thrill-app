"""_distance_point_to_segment(), the shared point-to-segment distance helper
add_door_leaf() uses for BOTH its furniture-collision check and its new
door-vs-door collision check (hits_other_leaf).

render-furnished-dollhouse.py imports bpy and only runs inside Blender, so
it cannot be imported here directly. `_distance_point_to_segment` is pure
math with no bpy dependency, so this pulls its ACTUAL source out of the real
file via ast (never a hand-copied duplicate that could drift) and execs just
that one function in an isolated namespace.

The higher-level door-vs-door collision behaviour (hits_other_leaf, the
rehinge/close fallback, PLACED_DOOR_LEAVES) is exercised by the real
pipeline instead -- those are closures over wall/opening/rooms/the module
global `floor`, not standalone functions, and this script's own render
scripts are all built to run wholesale under Blender, not import in
isolation. See plans/front-door-material-and-door-collision-v1.md, "Tests
and verification commands", for the bungalow_039 run that is the regression
proof for the reported bug (four real door pairs 858-1475mm apart).
"""

import ast
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "render-furnished-dollhouse.py"


def load_distance_point_to_segment():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "_distance_point_to_segment")
    namespace = {"math": math}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["_distance_point_to_segment"]



def load_laufplan_stufen():
    """Die echte Funktion aus dem Renderer, ohne bpy -- wie oben."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "laufplan_stufen")
    namespace = {"math": math}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["laufplan_stufen"]


laufplan_stufen = load_laufplan_stufen()


class DistancePointToSegmentTests(unittest.TestCase):
    def setUp(self):
        self.distance = load_distance_point_to_segment()

    def test_point_directly_above_segment_midpoint(self):
        d = self.distance(0.5, 1.0, 0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d, 1.0)

    def test_point_beyond_segment_end_clamps_to_the_endpoint(self):
        d = self.distance(2.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d, 1.0)

    def test_point_on_the_segment_is_zero(self):
        d = self.distance(0.5, 0.0, 0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d, 0.0)

    def test_degenerate_zero_length_segment_is_plain_point_distance(self):
        d = self.distance(3.0, 4.0, 0.0, 0.0, 0.0, 0.0)
        self.assertAlmostEqual(d, 5.0)




def lade_dict(name):
    """Ein Modul-Dict aus der echten Datei ziehen -- ohne bpy zu importieren."""
    baum = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for knoten in baum.body:
        if (isinstance(knoten, ast.Assign)
                and any(isinstance(z, ast.Name) and z.id == name for z in knoten.targets)):
            return ast.literal_eval(knoten.value)
    raise AssertionError(f"{name} nicht gefunden")


class EsszimmerstuhlFacingTests(unittest.TestCase):
    """Das Stuhlmodell schaut nach -Y und braucht die halbe Drehung.

    Rainer, 2026-08-25, zweimal: die Stuehle sitzen verkehrt. Nachgerechnet am
    Bauplan von bungalow_039 zeigen alle sechs Platzierungen bereits zum Tisch
    (Skalarprodukt 0.90-1.00), die Platzierung ist also in Ordnung -- bleibt
    das Modell. Der Eintrag war zwischendurch entfernt, weil ich die
    Sitzrichtung aus einer Isometrie abgelesen hatte; davor warnt der
    Kommentar bei ROTATION_OVERRIDE ausdruecklich.
    """

    @classmethod
    def setUpClass(cls):
        cls.facing = lade_dict("MODEL_FACING_DEG")
        cls.override = lade_dict("ROTATION_OVERRIDE")

    def test_beide_stuhlschluessel_sind_um_180_kanonisiert(self):
        for schluessel in ("essgruppe_stuhl", "esszimmerstuhl"):
            self.assertEqual(self.facing.get(schluessel), 180)

    def test_die_drehung_steht_nicht_in_der_platzierung(self):
        for schluessel in ("essgruppe_stuhl", "esszimmerstuhl"):
            self.assertNotIn(schluessel, self.override,
                             "Modellfehler gehoeren in MODEL_FACING_DEG")


class BettFacingTests(unittest.TestCase):
    """Rainer, 2026-08-25: "the double bed has to be rotated 90 degrees
    counterclockwise to your symbol".

    270 + 90 gegen den Uhrzeigersinn = 360, also 0. Das Einzelbett ist ein
    ANDERES Modell und bleibt unangetastet, bis es jemand am Bild geprueft hat.
    """

    @classmethod
    def setUpClass(cls):
        cls.facing = lade_dict("MODEL_FACING_DEG")

    def test_doppelbett_braucht_keine_korrektur_mehr(self):
        self.assertEqual(self.facing.get("doppelbett"), 0)

    def test_einzelbett_bleibt_wie_es_war(self):
        self.assertEqual(self.facing.get("einzelbett"), 270)

def lade_funktion(name, umgebung=None):
    """Eine reine Funktion aus der echten Datei ziehen -- ohne bpy."""
    baum = ast.parse(SOURCE.read_text(encoding="utf-8"))
    knoten = next(n for n in baum.body
                  if isinstance(n, ast.FunctionDef) and n.name == name)
    namensraum = dict(umgebung or {})
    exec(compile(ast.Module(body=[knoten], type_ignores=[]), str(SOURCE), "exec"),
         namensraum)
    return namensraum[name]


class BodenplatteNachUntenTests(unittest.TestCase):
    """plans/bodenplatte-nach-unten-v1.md.

    polygon_object extrudiert gegen die Flaechennormale. Im Uhrzeigersinn
    gezeichnete Raeume bekamen dadurch eine Platte, die NACH OBEN waechst --
    in Blender gemessen: Boden 0..220, Badewanne 0..580, Duschwanne 0..120.
    Jedes Moebel stand 220mm zu tief.
    """

    @classmethod
    def setUpClass(cls):
        # staticmethod: sonst wuerde self als erstes Argument mitgehen.
        cls.dreh = staticmethod(lade_funktion("_winding_nach_unten"))

    @staticmethod
    def _flaeche(punkte):
        s = 0.0
        for i in range(len(punkte)):
            x1, y1 = punkte[i]
            x2, y2 = punkte[(i + 1) % len(punkte)]
            s += x1 * y2 - x2 * y1
        return s / 2

    def test_im_uhrzeigersinn_wird_gedreht(self):
        # So laufen die Raeume von bungalow_039: negative Flaeche.
        quadrat = [[0, 0], [0, 1000], [1000, 1000], [1000, 0]]
        self.assertLess(self._flaeche(quadrat), 0)
        self.assertGreater(self._flaeche(self.dreh(quadrat)), 0)

    def test_gegen_den_uhrzeigersinn_bleibt(self):
        quadrat = [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]
        self.assertGreater(self._flaeche(quadrat), 0)
        self.assertEqual(self.dreh(quadrat), quadrat)

    def test_beide_richtungen_ergeben_dieselbe_umlaufrichtung(self):
        # Der eigentliche Punkt: onehalfstorey_029 hatte in EINEM Geschoss
        # beide Varianten nebeneinander, also Boeden auf zwei Hoehen.
        a = [[0, 0], [0, 1000], [1000, 1000], [1000, 0]]
        b = list(reversed(a))
        self.assertGreater(self._flaeche(self.dreh(a)), 0)
        self.assertGreater(self._flaeche(self.dreh(b)), 0)

    def test_ein_l_foermiger_raum_wird_auch_gedreht(self):
        ell = [[0, 0], [0, 2000], [1000, 2000], [1000, 1000], [2000, 1000], [2000, 0]]
        self.assertLess(self._flaeche(ell), 0)
        self.assertGreater(self._flaeche(self.dreh(ell)), 0)


class LaufplanTest(unittest.TestCase):
    """Ein Podest darf keine Stufe fressen.

    onehalfstorey_029, am 2026-09-01 nachgemessen. Der Verifier meldete
    "R9_stair_access: top tread stair-step-13 finishes at 2271mm but this
    storey's floor is at 2620mm". 2620 - 2271 = 349 mm = genau zwei
    Steigungen, und die Treppe hat zwei Podeste.

    Die Zahlen aus plan-modern.json:

        Lauflinie      5277 mm
        Podeste        2 x 900 mm  bei 1518..2418 und 2836..3736
        Flugstrecke    3477 mm
        gebraucht      15 Steigungen (2620 / 174,67)
        gebaut         13 -- 11 Stufen und 2 Podeste, Ende bei 5073 mm

    Der alte Laufplan lief mit festem Auftritt die Linie entlang und nahm ein
    Podest, sobald die NAECHSTE Stufe hineingeragt haette. Die angefangene
    Stufe davor fiel dabei weg: 1518 / 267,5 = 5,68 Stufen, gelegt wurden 5,
    die restlichen 181 mm verschluckte das Podest. Zwei Podeste, zwei
    verlorene Steigungen -- und die Treppe endete 349 mm unter dem Boden, auf
    dem sie ankommt.

    Denselben Fehler hatte der Annotator beim Zeichnen der Stufenkanten
    (`auftrittsStellen`, 2026-08-31: "the stairs are off again even if they
    did look normal in the architecture view"). Dort ist er behoben, hier
    nicht -- gezeichnet wurde seitdem richtig und gebaut weiter falsch.

    Richtig ist: jedes Flugstueck bekommt eine GANZE Zahl Stufen, und die
    Summe aus Stufen und Podesten ist die Zahl der Steigungen, die das
    Geschoss braucht.
    """

    # Genau der Fall von onehalfstorey_029.
    LAUF = 5277.2
    ZONEN = [(1518.4, 2418.4), (2836.0, 3736.0)]
    STEIGUNGEN = 15

    def test_die_Treppe_bekommt_alle_Steigungen(self):
        plan = laufplan_stufen(self.LAUF, self.ZONEN, self.STEIGUNGEN)
        self.assertEqual(len(plan), self.STEIGUNGEN,
                         "%d statt %d Steigungen" % (len(plan), self.STEIGUNGEN))

    def test_jedes_Podest_ist_genau_eine_Steigung(self):
        plan = laufplan_stufen(self.LAUF, self.ZONEN, self.STEIGUNGEN)
        podeste = [e for e in plan if e["art"] == "podest"]
        self.assertEqual(len(podeste), len(self.ZONEN))
        for e, (von, bis) in zip(podeste, self.ZONEN):
            self.assertAlmostEqual(e["start"], von, places=3)
            self.assertAlmostEqual(e["ende"], bis, places=3)

    def test_die_Lauflinie_wird_ganz_verbraucht(self):
        plan = laufplan_stufen(self.LAUF, self.ZONEN, self.STEIGUNGEN)
        self.assertAlmostEqual(plan[0]["start"], 0.0, places=3)
        self.assertAlmostEqual(plan[-1]["ende"], self.LAUF, places=3)

    def test_die_Elemente_stossen_lueckenlos_aneinander(self):
        plan = laufplan_stufen(self.LAUF, self.ZONEN, self.STEIGUNGEN)
        for vorher, nachher in zip(plan, plan[1:]):
            self.assertAlmostEqual(vorher["ende"], nachher["start"], places=3)

    def test_eine_gerade_Treppe_ohne_Podest_bleibt_wie_sie_war(self):
        plan = laufplan_stufen(4200.0, [], 15)
        self.assertEqual(len(plan), 15)
        self.assertTrue(all(e["art"] == "stufe" for e in plan))
        for e in plan:
            self.assertAlmostEqual(e["ende"] - e["start"], 280.0, places=3)

    def test_der_Auftritt_bleibt_innerhalb_eines_Flugs_gleich(self):
        # DIN 18065: in einem Lauf sind alle Auftritte gleich. Zwischen zwei
        # Fluegen darf er sich unterscheiden -- die Stuecke sind verschieden
        # lang und muessen eine ganze Zahl Stufen tragen.
        plan = laufplan_stufen(self.LAUF, self.ZONEN, self.STEIGUNGEN)
        flug, fluege = [], []
        for e in plan:
            if e["art"] == "podest":
                if flug: fluege.append(flug)
                flug = []
            else:
                flug.append(e["ende"] - e["start"])
        if flug: fluege.append(flug)
        for f in fluege:
            self.assertAlmostEqual(max(f), min(f), places=3)

    def test_zu_kurze_Lauflinie_meldet_sich_statt_zu_schummeln(self):
        # Passt die Zahl nicht auf die gezeichnete Linie, kommt heraus, was
        # passt -- der Aufrufer sieht es an der Laenge und schreibt es in die
        # Treppennotiz. Erfunden wird nichts.
        plan = laufplan_stufen(600.0, [], 15)
        self.assertLess(len(plan), 15)

    def test_ohne_Steigungen_gibt_es_keinen_Plan(self):
        self.assertEqual(laufplan_stufen(5000.0, [], 0), [])


def load_worktop_rest():
    """Die Arbeitsplatten-Regel aus der echten Datei (ast, nie nachgebaut)."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    wanted = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ("WORKTOP_THICKNESS_MM", "ON_WORKTOP_TYPES")
                for t in node.targets):
            wanted.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == "worktop_rest_mm":
            wanted.append(node)
    namespace = {}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["worktop_rest_mm"], namespace


class ArbeitsplattenAuflage(unittest.TestCase):
    """Das Kochfeld liegt AUF der Arbeitsplatte, nicht in ihr.

    Rainer, 2026-09-21: "the kochfeld has to be higher it is always covered up
    by the kuecheninsel." Das Kochfeld nimmt das echte Modell "Induction Hob 3"
    (908 x 520 x 19 mm). Auf diesem Modellweg wurde es mit der Mitte auf die
    Schrankhoehe (900 mm) gesetzt -- die Arbeitsplatte der Insel liegt aber
    900..940 mm. Das Kochfeld (890..910 mm) steckte ganz darin. Nur die Spuele
    bekam die Korrektur; der prozedurale Kochfeld-Zweig hatte sie auch
    (+40 mm), der Modellzweig nicht."""

    def test_ein_kochfeld_auf_900_liegt_auf_940(self):
        worktop_rest_mm, _ = load_worktop_rest()
        self.assertEqual(worktop_rest_mm("hob", 900), 940)

    def test_die_spuele_bleibt_wie_sie_war(self):
        worktop_rest_mm, _ = load_worktop_rest()
        self.assertEqual(worktop_rest_mm("sink", 880), 920)

    def test_das_kochfeld_ragt_ueber_die_platte(self):
        worktop_rest_mm, _ = load_worktop_rest()
        boden = worktop_rest_mm("hob", 900)
        # "Induction Hob 3": 19 mm hoch. Vorher: Mitte 900 -> Oberseite 909,5.
        self.assertGreater(boden + 19, 940)
        self.assertLess(900 + 19 / 2, 940, "die alte Rechnung: Oberseite unter der Platte")

    def test_andere_moebel_bekommen_keine_auflage(self):
        worktop_rest_mm, _ = load_worktop_rest()
        for art in ("counter", "fridge", "sofa", "storage_shelving", "oven_housing"):
            with self.subTest(art=art):
                self.assertIsNone(worktop_rest_mm(art, 900))

    def test_ohne_schrankhoehe_gibt_es_keine_auflage(self):
        worktop_rest_mm, _ = load_worktop_rest()
        self.assertIsNone(worktop_rest_mm("hob", 0))
        self.assertIsNone(worktop_rest_mm("hob", None))

    def test_der_modellweg_benutzt_die_regel(self):
        quelle = SOURCE.read_text(encoding="utf-8")
        modellweg = quelle[quelle.index("mount_mm = item.get(\"height_mm\", 0)"):]
        modellweg = modellweg[:modellweg.index("px, py = item[\"position_mm\"]")]
        self.assertIn('worktop_rest_mm(item["type"], mount_mm)', modellweg)


if __name__ == "__main__":
    unittest.main()
