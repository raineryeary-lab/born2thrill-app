"""Der Prüfbrief muss alles tragen, was vier parallele Prüfer brauchen.

Rainer, 2026-09-01: "nur muessen wir die Fehler minimieren wo moeglich damit
wir einen Fluss hinbekommen."

Der Fluss scheitert an den Runden, nicht an der Qualitaet. Bei
german_catalog_review_bungalow_3_4_2_b_120 ging die Beanstandung DREIMAL
raus, weil stueckweise geprueft wurde. Vier Bilder gleichzeitig zu pruefen
geht -- die Pruefer brauchen nur alle denselben Zettel.
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def lade():
    spec = importlib.util.spec_from_file_location(
        "pruefbrief", HERE / "pruefbrief.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


JOB = {
    "objects": {"doppelbett": ["doppelbett-1"],
                "essgruppe_6": ["essgruppe_6-27"],
                "essgruppe_stuhl": ["essgruppe_stuhl-%d" % n for n in range(30, 36)]},
    "object_map": [{
        "file": "OBJEKTKARTE-interior-modern-baseline.png",
        "image": [2000, 1500],
        "markers": [
            {"name": "doppelbett-1", "px": [603, 808],
             "masse_mm": [1800, 2000, 792], "umriss_px": [[1, 2]] * 8},
            {"name": "essgruppe_6-27", "px": [999, 344]},
        ],
    }],
    "required_outputs": [
        {"kind": "exterior", "filename_hint": "01-exterior-classic.png"},
        {"kind": "interior", "filename_hint": "03-floorplan-warm-modern.png"},
        {"kind": "interior", "filename_hint": "04-floorplan-dark-modern.png"},
    ],
}


class BriefTest(unittest.TestCase):

    def brief(self, ordner):
        modul = lade()
        mcj = modul._make_codex_job()
        return modul.brief(JOB, ordner, mcj.stueckzahlen(JOB["objects"]))

    def test_die_stueckzahlen_stehen_drin(self):
        # Ohne sie kann niemand zaehlen, und genau das Zaehlen ist die Aufgabe.
        text = self.brief("egal")
        self.assertIn("doppelbett", text)
        self.assertIn("6 Stuehle", text)

    def test_die_marker_stehen_mit_pixel_und_massen_drin(self):
        text = self.brief("egal")
        self.assertIn("603", text)
        self.assertIn("808", text)
        self.assertIn("1800 x 2000 x 792 mm", text)

    def test_die_schwerpunkt_falle_wird_erklaert(self):
        # Ich habe selbst zweimal ein Moebel falsch beurteilt, weil der
        # Markerpunkt optisch auf der Tischplatte lag.
        self.assertIn("SCHWERPUNKT", self.brief("egal"))

    def test_nur_die_INNENbilder_kommen_in_die_liste(self):
        # Die zwei Aussenansichten werden nicht Raum fuer Raum geprueft.
        with tempfile.TemporaryDirectory() as tmp:
            for n in ("01-exterior-classic-review.png",
                      "03-floorplan-warm-modern-review.png",
                      "04-floorplan-dark-modern-review.png"):
                open(os.path.join(tmp, n), "wb").write(b"x")
            text = self.brief(tmp)
            self.assertIn("03-floorplan-warm-modern-review.png", text)
            self.assertIn("04-floorplan-dark-modern-review.png", text)
            self.assertNotIn("01-exterior-classic", text)

    def test_die_review_endung_wird_gefunden(self):
        # Codex liefert als Zwischenstand mit "-review" im Namen.
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "03-floorplan-warm-modern-review.png"), "wb").write(b"x")
            self.assertIn("-review.png", self.brief(tmp))


class JuengsterOrdnerTest(unittest.TestCase):

    def test_go_baseline_ist_keine_lieferung(self):
        # Der Rohbau-Nachweis darf nie als Lieferung durchgehen -- so kamen
        # am 2026-08-26 graue Kloetze in den Kundenkatalog.
        modul = lade()
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "go-baseline"))
            self.assertIsNone(modul.juengster_ordner(tmp))

    def test_der_neueste_codex_ordner_gewinnt(self):
        modul = lade()
        with tempfile.TemporaryDirectory() as tmp:
            alt = os.path.join(tmp, "codex-haus-2026-08-30")
            neu = os.path.join(tmp, "codex-haus-2026-09-01")
            os.makedirs(alt)
            os.makedirs(neu)
            os.utime(alt, (1000, 1000))
            os.utime(neu, (2000, 2000))
            self.assertEqual(modul.juengster_ordner(tmp), "codex-haus-2026-09-01")

    def test_ohne_renders_ordner_kommt_None(self):
        modul = lade()
        self.assertIsNone(modul.juengster_ordner("/gibt/es/nicht"))


if __name__ == "__main__":
    unittest.main()
