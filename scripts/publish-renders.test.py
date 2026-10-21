"""Der Rohbau geht nicht in den Kundenkatalog.

Rainer, 2026-09-01, zu german_catalog_review_bungalow_3_4_5_b_120: "es heisst
ich muss die bilder freigeben das sind aber keine Bilder."

Er hatte recht. Das Haus ist gebaut und zertifiziert, aber Codex hat noch nie
etwas geliefert -- unter `renders/` liegt nur `go-baseline`. Was das Hochladen
genommen haette:

    Hochladen wuerde nehmen:  ...\\renders\\go-baseline
       exterior-classic-baseline.png
       exterior-modern-baseline.png
       interior-modern-baseline.png

Drei graue Blender-Rohbauten, direkt in den Katalog. Genau das ist am
2026-08-26 schon einmal passiert, und bungalow_001s Bild id 80 steht bis
heute so drin.

Drei Loecher, alle drei hier abgedeckt:

  1. `collect()` schliesst `-depth`, `-edge` und `-mask` aus -- aber NICHT
     `-baseline`.
  2. `bilderordner()` in go.py nimmt `go-baseline`, wenn es keinen
     Codex-Ordner gibt (`kandidaten = codex or sorted(os.listdir(wurzel))`),
     obwohl der eigene Docstring sagt: "go-baseline ist der ROHBAU-Nachweis,
     nie die Lieferung."
  3. Der Aufrufer in `treibe()` faellt noch einmal darauf zurueck:
     `bilderordner(name) or os.path.join(..., "go-baseline")`.
"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def lade(dateiname, modulname):
    spec = importlib.util.spec_from_file_location(modulname, HERE / dateiname)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def leg_an(ordner, *namen):
    os.makedirs(ordner, exist_ok=True)
    for name in namen:
        with open(os.path.join(ordner, name), "wb") as datei:
            datei.write(b"x")
    return ordner


class RohbauNichtHochladenTest(unittest.TestCase):

    def test_baseline_bilder_werden_ausgeschlossen(self):
        modul = lade("publish-renders.py", "publish_renders")
        with tempfile.TemporaryDirectory() as tmp:
            leg_an(tmp, "01-exterior-classic.png",
                   "exterior-modern-baseline.png",
                   "interior-modern-baseline.png")
            self.assertEqual(modul.collect(tmp), ["01-exterior-classic.png"])

    def test_ein_ordner_mit_NUR_baselines_wird_abgelehnt(self):
        # Nicht "lade halt nichts hoch": wer hier stillschweigend
        # weitermacht, hat einen Katalogeintrag ohne Bilder.
        modul = lade("publish-renders.py", "publish_renders")
        with tempfile.TemporaryDirectory() as tmp:
            leg_an(tmp, "exterior-classic-baseline.png",
                   "interior-modern-baseline.png")
            with self.assertRaises(SystemExit):
                modul.collect(tmp)

    def test_die_technischen_paesse_bleiben_draussen(self):
        # Die bestehende Zusage darf dabei nicht verlorengehen.
        modul = lade("publish-renders.py", "publish_renders")
        with tempfile.TemporaryDirectory() as tmp:
            leg_an(tmp, "01-exterior-classic.png",
                   "01-exterior-classic-depth.png",
                   "01-exterior-classic-edge.png",
                   "01-exterior-classic-mask.png")
            self.assertEqual(modul.collect(tmp), ["01-exterior-classic.png"])


class BilderordnerTest(unittest.TestCase):

    def baue(self, wurzel, plan):
        return os.path.join(wurzel, "corrections", plan, "renders")

    def test_ohne_codex_lieferung_gibt_es_keinen_bilderordner(self):
        modul = lade("go.py", "go_modul")
        with tempfile.TemporaryDirectory() as tmp:
            modul.DATA = tmp
            renders = self.baue(tmp, "pruef_haus")
            leg_an(os.path.join(renders, "go-baseline"),
                   "exterior-modern-baseline.png")
            self.assertIsNone(modul.bilderordner("pruef_haus"),
                              "go-baseline ist der Rohbau-Nachweis, nie die "
                              "Lieferung")

    def test_eine_codex_lieferung_wird_genommen(self):
        modul = lade("go.py", "go_modul")
        with tempfile.TemporaryDirectory() as tmp:
            modul.DATA = tmp
            renders = self.baue(tmp, "pruef_haus")
            leg_an(os.path.join(renders, "go-baseline"),
                   "exterior-modern-baseline.png")
            ziel = leg_an(os.path.join(renders, "codex-pruef_haus-2026-09-01"),
                          "01-exterior-classic.png")
            self.assertEqual(modul.bilderordner("pruef_haus"), ziel)

    def test_ohne_renders_ordner_kommt_None(self):
        modul = lade("go.py", "go_modul")
        with tempfile.TemporaryDirectory() as tmp:
            modul.DATA = tmp
            self.assertIsNone(modul.bilderordner("gibt_es_nicht"))


if __name__ == "__main__":
    unittest.main()
