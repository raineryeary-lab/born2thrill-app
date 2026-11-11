"""Umbauter Raum je Haus (plans/umbauter-raum-volumen-v1.md).

Rainer, 2026-11-07: "und wenn du nach Volumen statt Flaeche machst" ...
"make a second slider with the volume please".
Volles Geschoss = Umriss x 2,62 m; Dachgeschoss / oberes Geschoss eines
1,5-Geschossers = Umriss x nutzbare Hoehe unter dem Dach (Kniestock 1,0 m,
40 Grad, gedeckelt bei 2,62 m). Das Dach selbst zaehlt nicht (4 Dachformen).
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
    spec = importlib.util.spec_from_file_location("kmatrix_volumen", HERE / "konfigurator-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def raum(ebene):
    return {"id": "r" + ebene, "label": "Kind", "floor_level": ebene,
            "points": [{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}, {"x": 0.3, "y": 0.3}, {"x": 0.1, "y": 0.3}]}


# 0.5 x 0.5 normiert, 20 m je Einheit -> 10 x 10 m
QUADRAT = [{"x": 0.0, "y": 0.0}, {"x": 0.5, "y": 0.0}, {"x": 0.5, "y": 0.5}, {"x": 0.0, "y": 0.5}]
# 0.5 x 0.4 -> 10 x 8 m
RECHTECK = [{"x": 0.0, "y": 0.0}, {"x": 0.5, "y": 0.0}, {"x": 0.5, "y": 0.4}, {"x": 0.0, "y": 0.4}]


class Volumen(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.tmp = tempfile.TemporaryDirectory()
        self.m.PROJECTS = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def werte(self, plan, annotationen):
        ordner = Path(self.tmp.name) / plan
        ordner.mkdir()
        annotationen.setdefault("annotation_space", {"aspect": 1.0})
        (ordner / "annotations.json").write_text(json.dumps(annotationen), encoding="utf-8")
        (ordner / "gebaeudemass.json").write_text(json.dumps(
            {"floor_scale": {"groundfloor": 20.0, "upperfloor": 20.0, "attic": 20.0}}), encoding="utf-8")
        return self.m.haus_werte(plan)

    def test_nutzhoehe_unter_dem_dach(self):
        self.assertAlmostEqual(self.m.nutzhoehe_dach(8.0), 2.23, delta=0.01)
        self.assertAlmostEqual(self.m.nutzhoehe_dach(3.0), 1.63, delta=0.02)   # erreicht 2,62 nie
        self.assertLess(self.m.nutzhoehe_dach(30.0), 2.62)

    def test_bungalow(self):
        w = self.werte("bungalow_test", {"annotations": [raum("groundfloor")],
                                         "outer_outlines": {"groundfloor": QUADRAT}})
        self.assertEqual(w["volumen_m3"], 262)

    def test_zweigeschosser_og_ohne_eigenen_umriss(self):
        w = self.werte("twostorey_test", {"annotations": [raum("groundfloor"), raum("upperfloor")],
                                          "outer_outlines": {"groundfloor": QUADRAT}})
        self.assertEqual(w["volumen_m3"], 524)

    def test_anderthalb_oben_unter_dem_dach(self):
        w = self.werte("onehalfstorey_test", {"annotations": [raum("groundfloor"), raum("upperfloor")],
                                              "outer_outlines": {"groundfloor": RECHTECK}})
        self.assertAlmostEqual(w["volumen_m3"], 80 * 2.62 + 80 * self.m.nutzhoehe_dach(8.0), delta=1)

    def test_dachgeschoss_attic(self):
        w = self.werte("twostorey_attic", {"annotations": [raum("groundfloor"), raum("attic")],
                                           "outer_outlines": {"groundfloor": QUADRAT}})
        self.assertAlmostEqual(w["volumen_m3"], 262 + 100 * self.m.nutzhoehe_dach(10.0), delta=1)

    def test_ohne_umriss_kein_volumen(self):
        w = self.werte("bungalow_leer", {"annotations": [raum("groundfloor")]})
        self.assertIsNone(w["volumen_m3"])


if __name__ == "__main__":
    unittest.main()
