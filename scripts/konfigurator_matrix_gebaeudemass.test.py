"""Konfigurator-Matrix liest die eingetippten Gebaeudemasse (matrix-gebaeudemass-v1).

"Gebaeudemasse eingeben" legt Seitenverhaeltnis und Massstab in
gebaeudemass.json ab. Die Matrix las nur annotations.json -- eingetippte
Masse kamen nie in die Website-Filter.
"""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade():
    os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.gettempdir())
    spec = importlib.util.spec_from_file_location("kmatrix", HERE / "konfigurator-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RAUM = {"id": "r1", "label": "Kind", "floor_level": "groundfloor",
        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}, {"x": 0.3, "y": 0.3}, {"x": 0.1, "y": 0.3}]}


class MatrixGebaeudemass(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.tmp = tempfile.TemporaryDirectory()
        self.m.PROJECTS = self.tmp.name
        self.ordner = Path(self.tmp.name) / "bungalow_test"
        self.ordner.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def schreibe(self, annotationen, sidecar):
        (self.ordner / "annotations.json").write_text(json.dumps(annotationen), encoding="utf-8")
        (self.ordner / "gebaeudemass.json").write_text(json.dumps(sidecar), encoding="utf-8")

    def test_seitenverhaeltnis_aus_gebaeudemass(self):
        self.schreibe({"annotations": [RAUM]},
                      {"floor_scale": {"groundfloor": 20.0}, "annotation_space": {"aspect": 0.5}})
        w = self.m.haus_werte("bungalow_test")
        self.assertNotIn("fehlt", w)
        # 0.2 x 0.2 normiert, 20 m je Einheit, Hoehe x 0.5 -> 4 m x 2 m = 8 m2
        self.assertEqual(w["qm"], 8)

    def test_zeichnung_gewinnt(self):
        self.schreibe({"annotations": [RAUM], "annotation_space": {"aspect": 1.0}},
                      {"floor_scale": {"groundfloor": 20.0}, "annotation_space": {"aspect": 0.5}})
        self.assertEqual(self.m.haus_werte("bungalow_test")["qm"], 16)

    def test_ohne_masse_fehlt_weiter(self):
        self.schreibe({"annotations": [RAUM]}, {"floor_scale": {"groundfloor": 20.0}})
        self.assertEqual(self.m.haus_werte("bungalow_test")["fehlt"], "kein Seitenverhaeltnis")


if __name__ == "__main__":
    unittest.main()
