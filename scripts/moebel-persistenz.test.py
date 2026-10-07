"""Das Mass ist richtig -- der freie Input ist es nicht.

Rainer, 2026-09-01: "find out why stuff like that happens". Codex hat
geantwortet, jedes Innenbild sei eine eigene Stichprobe eines Bildmodells;
Objekte verschwinden dabei, und kein Auftragstext kann das verhindern.

Diese Tests halten fest, was daraufhin an
german_catalog_review_bungalow_3_4_2_b_120 gemessen wurde:

    Baseline gegen sich selbst              43 Objekte, alle 1,00
    dusche-3 kuenstlich uebermalt           0,35, Nachbarn 1,00
    freie Lieferung, dusche-3 FEHLT         1,16
    freie Lieferung, schreibtisch-20 FEHLT  1,06 und 1,26

Das Werkzeug erkennt ein entferntes Moebel also zuverlaessig, SOLANGE die
zwei Bilder ueberhaupt zueinander passen. Gegen ein frei erzeugtes Bild
versagt es, und zwar nicht knapp: wo die Dusche fehlt, stehen Fliesen und
eine Topfpflanze -- mehr Kanten als der graue Rohbau, nicht weniger.

Genau das ist der Beleg fuer Codex' Diagnose. Das Werkzeug wird brauchbar,
sobald der Low-Denoise-Pass (0,22) steht.
"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def lade():
    spec = importlib.util.spec_from_file_location(
        "moebel_persistenz", HERE / "moebel-persistenz.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def wuerfel(x, y, breite, hoehe):
    """Acht Ecken wie `umriss_px` sie liefert, hier als flacher Quader."""
    return [[x, y], [x + breite, y], [x + breite, y + hoehe], [x, y + hoehe],
            [x, y], [x + breite, y], [x + breite, y + hoehe], [x, y + hoehe]]


class KastenTest(unittest.TestCase):

    def test_das_rechteck_umschliesst_alle_acht_ecken(self):
        modul = lade()
        self.assertEqual(modul.kasten(wuerfel(100, 200, 50, 30)),
                         (100, 200, 150, 230))

    def test_ohne_umriss_gibt_es_kein_rechteck(self):
        modul = lade()
        self.assertIsNone(modul.kasten(None))
        self.assertIsNone(modul.kasten([]))


class PersistenzTest(unittest.TestCase):
    """Gemessen an einem gebauten Bildpaar, nicht an Zufallsrauschen."""

    def bilder(self, tmp):
        from PIL import Image, ImageDraw
        basis = Image.new("RGB", (400, 300), (210, 210, 208))
        z = ImageDraw.Draw(basis)
        # Zwei "Moebel": Kaesten mit Fugen, also mit Kanten.
        for x0 in (40, 240):
            z.rectangle((x0, 80, x0 + 100, 200), fill=(150, 120, 90))
            for i in range(1, 4):
                z.line((x0, 80 + i * 30, x0 + 100, 80 + i * 30), fill=(90, 70, 50), width=2)
        a = os.path.join(tmp, "basis.png")
        basis.save(a)
        # Dasselbe Bild, aber das linke Moebel uebermalt.
        ohne = basis.copy()
        ImageDraw.Draw(ohne).rectangle((40, 80, 140, 200), fill=(210, 210, 208))
        b = os.path.join(tmp, "ohne.png")
        ohne.save(b)
        return a, b

    def marker(self):
        return [{"name": "links", "umriss_px": wuerfel(40, 80, 100, 120)},
                {"name": "rechts", "umriss_px": wuerfel(240, 80, 100, 120)}]

    def test_baseline_gegen_sich_selbst_ist_ueberall_eins(self):
        # Der Nullpunkt: ohne Aenderung darf nichts anschlagen. An 3_4_2
        # gemessen: 43 von 43 Objekten exakt 1,00.
        modul = lade()
        with tempfile.TemporaryDirectory() as tmp:
            a, _ = self.bilder(tmp)
            raus = modul.persistenz(a, a, self.marker())
            for name, (_, _, v) in raus.items():
                self.assertAlmostEqual(v, 1.0, places=6, msg=name)

    def test_ein_entferntes_moebel_faellt_deutlich_ab(self):
        modul = lade()
        with tempfile.TemporaryDirectory() as tmp:
            a, b = self.bilder(tmp)
            raus = modul.persistenz(a, b, self.marker())
            self.assertLess(raus["links"][2], 0.5,
                            "das uebermalte Moebel wurde nicht erkannt")

    def test_der_nachbar_bleibt_unberuehrt(self):
        # Sonst meldet das Werkzeug bei jeder Aenderung das halbe Haus.
        modul = lade()
        with tempfile.TemporaryDirectory() as tmp:
            a, b = self.bilder(tmp)
            raus = modul.persistenz(a, b, self.marker())
            self.assertAlmostEqual(raus["rechts"][2], 1.0, places=6)

    def test_verschiedene_bildgroessen_geben_kein_ergebnis(self):
        # Ohne gleiche Masze zeigt derselbe Pixel nicht dieselbe Stelle.
        from PIL import Image
        modul = lade()
        with tempfile.TemporaryDirectory() as tmp:
            a, _ = self.bilder(tmp)
            klein = os.path.join(tmp, "klein.png")
            Image.open(a).resize((200, 150)).save(klein)
            self.assertIsNone(modul.persistenz(a, klein, self.marker()))


if __name__ == "__main__":
    unittest.main()
