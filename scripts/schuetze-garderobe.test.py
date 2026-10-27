"""Die reinen Bausteine von schuetze-garderobe.py, ohne Blender.

objektmaske.py selbst (der Blender-Lauf) wird hier nicht getestet -- dafuer
braucht es eine echte .blend. Getestet wird alles, was danach passiert:
Maske aus dem Objektindex bauen, skalieren, Mittelpunkt messen, komponieren,
und den marker_check richtig fortschreiben.
"""

import importlib.util
import os
import unittest
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def load_module():
    spec = importlib.util.spec_from_file_location(
        "schuetze_garderobe", HERE / "schuetze-garderobe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def objektindex_bild(breite, hoehe, felder):
    """Ein synthetisches Objektindex-Bild: felder = [(x0,y0,x1,y1,nummer), ...]."""
    bild = Image.new("RGB", (breite, hoehe), (0, 0, 0))
    pixel = bild.load()
    for x0, y0, x1, y1, nummer in felder:
        for y in range(y0, y1):
            for x in range(x0, x1):
                pixel[x, y] = (nummer, 0, 0)
    return bild


class StammTest(unittest.TestCase):
    def test_erstes_segment(self):
        modul = load_module()
        self.assertEqual(modul.stamm("garderobe-23"), "garderobe")
        self.assertEqual(modul.stamm("garderobe-bench"), "garderobe")
        self.assertEqual(modul.stamm("stuff-9"), "stuff")
        self.assertEqual(modul.stamm(None), "")


class GarderobeNummernTest(unittest.TestCase):
    def test_nur_garderobe_stamm(self):
        modul = load_module()
        zuordnung = {"1": "garderobe-23", "2": "garderobe-bench",
                    "3": "stuff-9", "4": "badewanne-14"}
        self.assertEqual(modul.garderobe_nummern(zuordnung), {1, 2})

    def test_leer_ohne_treffer(self):
        modul = load_module()
        self.assertEqual(
            modul.garderobe_nummern({"1": "stuff-9", "2": "badewanne-14"}), set())


class MaskeTest(unittest.TestCase):
    def test_maske_markiert_nur_genannte_nummern(self):
        modul = load_module()
        bild = objektindex_bild(10, 10, [(0, 0, 4, 4, 5), (6, 6, 10, 10, 7)])
        maske = modul.maske_fuer_nummern(bild, {5})
        pixel = maske.load()
        self.assertEqual(pixel[1, 1], 255)
        self.assertEqual(pixel[7, 7], 0)
        self.assertEqual(pixel[9, 0], 0)

    def test_ohne_nummern_leere_maske(self):
        modul = load_module()
        bild = objektindex_bild(5, 5, [(0, 0, 5, 5, 3)])
        maske = modul.maske_fuer_nummern(bild, set())
        holen = getattr(maske, "get_flattened_data", None) or maske.getdata
        self.assertEqual(list(holen()), [0] * 25)


class MittelpunktTest(unittest.TestCase):
    def test_mittelpunkt_eines_rechtecks(self):
        modul = load_module()
        bild = objektindex_bild(10, 10, [(2, 2, 6, 6, 1)])
        maske = modul.maske_fuer_nummern(bild, {1})
        cx, cy = modul.centroid_of_mask(maske)
        # Rechteck x=2..5, y=2..5 -> Mitte bei 3.5, 3.5
        self.assertAlmostEqual(cx, 3.5, delta=0.1)
        self.assertAlmostEqual(cy, 3.5, delta=0.1)

    def test_leere_maske_gibt_none(self):
        modul = load_module()
        maske = Image.new("L", (10, 10), 0)
        self.assertIsNone(modul.centroid_of_mask(maske))


class SkalierenTest(unittest.TestCase):
    def test_skaliert_auf_zielgroesse(self):
        modul = load_module()
        maske = Image.new("L", (10, 10), 255)
        skaliert = modul.skaliere_maske(maske, (20, 30))
        self.assertEqual(skaliert.size, (20, 30))

    def test_gleiche_groesse_bleibt_unveraendert(self):
        modul = load_module()
        maske = Image.new("L", (10, 10), 255)
        self.assertIs(modul.skaliere_maske(maske, (10, 10)), maske)


class KompositTest(unittest.TestCase):
    def test_maske_entscheidet_welches_bild_gewinnt(self):
        modul = load_module()
        basis = Image.new("RGB", (4, 4), (255, 0, 0))
        ziel = Image.new("RGB", (4, 4), (0, 255, 0))
        maske = Image.new("L", (4, 4), 0)
        pixel = maske.load()
        pixel[0, 0] = 255
        ergebnis = modul.komposit(basis, ziel, maske)
        self.assertEqual(ergebnis.getpixel((0, 0)), (255, 0, 0))
        self.assertEqual(ergebnis.getpixel((3, 3)), (0, 255, 0))


class MarkerCheckTest(unittest.TestCase):
    def _katalog(self):
        return [
            {"n": 9, "name": "garderobe-23", "status": "ersetzt"},
            {"n": 10, "name": "garderobe-bench", "status": "ersetzt"},
            {"n": 26, "name": "stuff-9", "status": "ersetzt"},
            {"n": 1, "name": "badewanne-14", "status": "sichtbar", "bei": [10, 10]},
        ]

    def test_aktualisiert_nur_garderobe(self):
        modul = load_module()
        ergebnis = modul.aktualisiere_marker_check(self._katalog(), (100.0, 200.0))
        nach_name = {e["name"]: e for e in ergebnis}
        self.assertEqual(nach_name["garderobe-23"]["status"], "sichtbar")
        self.assertEqual(nach_name["garderobe-23"]["bei"], [100.0, 200.0])
        self.assertEqual(nach_name["garderobe-bench"]["status"], "sichtbar")
        # stuff und andere Staemme bleiben unangetastet
        self.assertEqual(nach_name["stuff-9"], {"n": 26, "name": "stuff-9",
                                                "status": "ersetzt"})
        self.assertEqual(nach_name["badewanne-14"]["bei"], [10, 10])

    def test_ohne_mittelpunkt_bleibt_alles_gleich(self):
        modul = load_module()
        original = self._katalog()
        ergebnis = modul.aktualisiere_marker_check(original, None)
        self.assertEqual(ergebnis, original)

    def test_original_liste_wird_nicht_veraendert(self):
        modul = load_module()
        original = self._katalog()
        modul.aktualisiere_marker_check(original, (5.0, 5.0))
        self.assertEqual(original[0]["status"], "ersetzt")


class BereitsKorrektTest(unittest.TestCase):
    def test_schon_sichtbar_und_nah_dran_ist_korrekt(self):
        modul = load_module()
        katalog = [{"n": 9, "name": "garderobe-23", "status": "sichtbar",
                   "bei": [100.0, 200.0]}]
        self.assertTrue(modul.bereits_korrekt(katalog, (105.0, 198.0)))

    def test_ersetzt_ist_nicht_korrekt(self):
        modul = load_module()
        katalog = [{"n": 9, "name": "garderobe-23", "status": "ersetzt"}]
        self.assertFalse(modul.bereits_korrekt(katalog, (100.0, 200.0)))

    def test_sichtbar_aber_weit_weg_ist_nicht_korrekt(self):
        modul = load_module()
        katalog = [{"n": 9, "name": "garderobe-23", "status": "sichtbar",
                   "bei": [500.0, 500.0]}]
        self.assertFalse(modul.bereits_korrekt(katalog, (100.0, 200.0)))

    def test_kein_garderobe_marker_ist_immer_korrekt(self):
        modul = load_module()
        katalog = [{"n": 1, "name": "badewanne-14", "status": "ersetzt"}]
        self.assertTrue(modul.bereits_korrekt(katalog, (100.0, 200.0)))

    def test_ohne_mittelpunkt_ist_immer_korrekt(self):
        modul = load_module()
        katalog = [{"n": 9, "name": "garderobe-23", "status": "ersetzt"}]
        self.assertTrue(modul.bereits_korrekt(katalog, None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
