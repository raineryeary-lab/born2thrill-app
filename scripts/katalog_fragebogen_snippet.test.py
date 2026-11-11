"""Katalog-Filter nur nach Fragebogen + Name (katalog-filter-fragebogen-v2).

Rainer, 2026-11-07: "can you redo the grundriss catalog so that the filters on
the top just have me filter according to the questionaire + the name?"
Snippet 9 bleibt unberuehrt; Snippet 10 blendet dessen Filterzeile aus und
setzt Name, Budget, Hausart, Zimmer, Gaeste-WC an ihre Stelle.
"""
import csv
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade():
    os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.gettempdir())
    spec = importlib.util.spec_from_file_location("katalog_snippet", HERE / "katalog-fragebogen-snippet.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Snippet(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        with open(t / "matrix.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["plan", "haustyp", "zimmer", "preis_eur", "budget", "gaeste_wc_dusche"])
            w.writerow(["bungalow_007", "efh", "5.0", "561000", "passt", "ja"])
            w.writerow(["bungalow_001", "bungalow", "3.5", "300000", "zu guenstig", "nein"])
        (t / "projects" / "bungalow_007").mkdir(parents=True)
        (t / "projects" / "bungalow_007" / "anzeigename.json").write_text(
            json.dumps({"anzeigename": "2-Geschosser am Hang (BAH)"}), encoding="utf-8")
        self.m.PROJECTS = str(t / "projects")
        self.daten = self.m.werte(str(t / "matrix.csv"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_daten_mit_anzeigename(self):
        self.assertEqual(self.daten["bungalow_007"], ["efh", 5, 561000, 1, "2-Geschosser am Hang (BAH)", 1])
        self.assertEqual(self.daten["bungalow_001"], ["bungalow", 3, 300000, 0, "", 1])

    def test_js_filtert_nach_fragebogen_und_name(self):
        js = self.m.JS
        for feld in ('data-fb="name"', 'data-fb="budget"', 'data-fb="art"', 'data-fb="zi"', 'data-fb="du"'):
            self.assertIn(feld, js)
        self.assertIn("bis 450.000", js)
        self.assertNotIn('data-fb="an"', js)          # kein Haekchen mehr: Filter gelten immer
        # Rainer, 2026-11-07: "5 und mehr Zimmer" statt nur 5 (die Daten sind bei 5 gedeckelt)
        self.assertIn(">5 und mehr Zimmer<", js)

    def test_zfh_ohne_massstab_trotzdem_unter_hausart(self):
        # Rainer, 2026-11-07: "WHY ARE MY 2 FAMILIENHAEUSER NOT BEING SHOWN" --
        # ohne Massstab fehlt die Matrixzeile; die Hausart kennt die Zeichnung trotzdem.
        ordner = Path(self.m.PROJECTS) / "other_zfh"
        ordner.mkdir()
        (ordner / "annotations.json").write_text(json.dumps({"wohneinheiten": 2, "annotations": []}),
                                                 encoding="utf-8")
        (Path(self.m.PROJECTS) / "other_efh").mkdir()
        (Path(self.m.PROJECTS) / "other_efh" / "annotations.json").write_text('{"annotations": []}',
                                                                              encoding="utf-8")
        daten = self.m.ohne_matrix_nach_wohneinheiten(self.daten)
        self.assertEqual(daten["other_zfh"], ["zfh", 0, 0, 0, "", 2])
        self.assertNotIn("other_efh", daten)
        self.assertEqual(daten["bungalow_007"][0], "efh")

    def test_mehrfamilienhaus_nach_wohnungen(self):
        # wohneinheiten-zfh-mfh-v1: "By number of flats"
        js = self.m.JS
        self.assertIn('<option value="mfh">Mehrfamilienhaus</option>', js)
        self.assertIn("Wohnungen", js)

    def test_grundriss_karte_heisst_offen(self):
        # katalog-grundriss-bild-v1: nur das Grundriss-Bild -> nicht "gerendert"
        js = self.m.JS
        self.assertIn("-grundriss", js)
        self.assertIn("'.gk-state'", js)
        self.assertIn("'offen'", js)

    def test_alte_filter_von_snippet_9_ausgeblendet(self):
        self.assertIn(".gk-search > .gk-row:not(.gk-fb)", self.m.CSS)
        self.assertIn(".gk-search > .gk-tags", self.m.CSS)


if __name__ == "__main__":
    unittest.main()
