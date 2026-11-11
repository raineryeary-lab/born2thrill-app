"""Kleine Zimmer zaehlen voll und werden zur Pruefung gelistet (kleine-zimmer-v1).

Rainer, 2026-11-07, auf "Raeume unter 10 m2 als ganze Zimmer zaehlen?": "yes but
mark them as green and let me review them". 6 Haeuser mit 2,5 Zimmern tauchten
unter keinem Filter auf.
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
    spec = importlib.util.spec_from_file_location("kmatrix_klein", HERE / "konfigurator-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def quadrat(label, x, seite):
    return {"id": label + str(x), "label": label, "floor_level": "groundfloor",
            "points": [{"x": x, "y": 0.0}, {"x": x + seite, "y": 0.0},
                       {"x": x + seite, "y": seite}, {"x": x, "y": seite}]}


class KleineZimmer(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.tmp = tempfile.TemporaryDirectory()
        self.m.PROJECTS = self.tmp.name
        ordner = Path(self.tmp.name) / "bungalow_test"
        ordner.mkdir()
        # 20 m je Bildeinheit: 0,15 -> 3 m -> 9 m2; 0,2 -> 4 m -> 16 m2
        ann = {"annotations": [quadrat("Büro", 0.0, 0.15), quadrat("Kind", 0.3, 0.2),
                               quadrat("Bad", 0.6, 0.1)],
               "annotation_space": {"aspect": 1.0}}
        (ordner / "annotations.json").write_text(json.dumps(ann), encoding="utf-8")
        (ordner / "gebaeudemass.json").write_text(json.dumps({"floor_scale": {"groundfloor": 20.0}}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_kleines_zimmer_zaehlt_voll_und_steht_in_der_liste(self):
        w = self.m.haus_werte("bungalow_test")
        self.assertEqual(w["zimmer"], 2)                      # Büro 9 m2 + Kind 16 m2, Bad nicht
        self.assertEqual(w["kleine_zimmer"], "Büro 9,0 m²")

    def test_angezeigte_10_0_ist_nicht_klein(self):
        # bungalow_037, Rainer 2026-11-07 "fixed": Büro auf 9,99 m2 gezogen, angezeigt
        # "10,0 m²" -- darf nicht mehr als klein gelistet werden.
        ordner = Path(self.tmp.name) / "bungalow_grenze"
        ordner.mkdir()
        seite = (9.996 ** 0.5) / 20
        ann = {"annotations": [quadrat("Büro", 0.0, seite)], "annotation_space": {"aspect": 1.0}}
        (ordner / "annotations.json").write_text(json.dumps(ann), encoding="utf-8")
        (ordner / "gebaeudemass.json").write_text(json.dumps({"floor_scale": {"groundfloor": 20.0}}), encoding="utf-8")
        self.assertEqual(self.m.haus_werte("bungalow_grenze")["kleine_zimmer"], "")

    def test_standard_ohne_halbe_zimmer(self):
        self.assertEqual(self.m.STANDARD["halbes_zimmer_unter_m2"], 0)
        self.assertEqual(self.m.STANDARD["kleines_zimmer_pruefen_unter_m2"], 10)

    def test_csv_spalte_am_ende(self):
        q = (HERE / "konfigurator-matrix.py").read_text(encoding="utf-8")
        self.assertIn('"kleine_zimmer"]', q)
        self.assertIn('" · ".join(sorted(kleine))', q)   # kein ";" im Feld, das ist der CSV-Trenner


if __name__ == "__main__":
    unittest.main()
