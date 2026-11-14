"""Hausgroesse aus dem Aussenumriss, drei Klassen (umriss-groesse-drei-klassen-v1).

Rainer, 2026-11-07: "use the Aussenumriss from each floor, add everything up
... we just have to divide it into three parts". Ein Geschoss ohne eigenen
Umriss nimmt den gezeichneten (wie outlineForFloor()); Staffelgeschoss nie.
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
    spec = importlib.util.spec_from_file_location("kmatrix_umriss", HERE / "konfigurator-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def raum(ebene):
    return {"id": "r" + ebene, "label": "Kind", "floor_level": ebene,
            "points": [{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}, {"x": 0.3, "y": 0.3}, {"x": 0.1, "y": 0.3}]}


# 0.5 x 0.5 normiert, 20 m je Einheit, Seitenverhaeltnis 1 -> 10 x 10 m = 100 m2
QUADRAT = [{"x": 0.0, "y": 0.0}, {"x": 0.5, "y": 0.0}, {"x": 0.5, "y": 0.5}, {"x": 0.0, "y": 0.5}]


class MatrixUmriss(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.tmp = tempfile.TemporaryDirectory()
        self.m.PROJECTS = self.tmp.name
        self.ordner = Path(self.tmp.name) / "twostorey_test"
        self.ordner.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def werte(self, annotationen):
        annotationen.setdefault("annotation_space", {"aspect": 1.0})
        (self.ordner / "annotations.json").write_text(json.dumps(annotationen), encoding="utf-8")
        (self.ordner / "gebaeudemass.json").write_text(json.dumps(
            {"floor_scale": {"groundfloor": 20.0, "upperfloor": 20.0, "staffelgeschoss": 20.0}}), encoding="utf-8")
        return self.m.haus_werte("twostorey_test")

    def test_zwei_geschosse_je_eigener_umriss(self):
        w = self.werte({"annotations": [raum("groundfloor"), raum("upperfloor")],
                        "outer_outlines": {"groundfloor": QUADRAT, "upperfloor": QUADRAT}})
        self.assertEqual(w["umriss_m2"], 200)
        self.assertEqual(w["umriss_fehlt"], "")

    def test_og_ohne_umriss_nimmt_den_eg_umriss(self):
        w = self.werte({"annotations": [raum("groundfloor"), raum("upperfloor")],
                        "outer_outlines": {"groundfloor": QUADRAT}})
        self.assertEqual(w["umriss_m2"], 200)

    def test_alter_einzelner_umriss(self):
        w = self.werte({"annotations": [raum("groundfloor"), raum("upperfloor")],
                        "outer_outline": QUADRAT, "outer_outline_floor": "groundfloor"})
        self.assertEqual(w["umriss_m2"], 200)

    def test_staffelgeschoss_wird_nicht_kopiert(self):
        w = self.werte({"annotations": [raum("groundfloor"), raum("staffelgeschoss")],
                        "outer_outlines": {"groundfloor": QUADRAT}})
        self.assertIsNone(w["umriss_m2"])
        self.assertIn("staffelgeschoss", w["umriss_fehlt"])

    def test_ohne_umriss_markiert(self):
        w = self.werte({"annotations": [raum("groundfloor")]})
        self.assertIsNone(w["umriss_m2"])
        self.assertEqual(w["umriss_fehlt"], "kein Außenumriss")

    def test_winziger_umriss_zaehlt_als_fehlend(self):
        # bungalow_040_17, 2026-11-07: ein aus Versehen gezogenes 1 x 8 px Rechteck
        winzig = [{"x": 0.7, "y": 0.5}, {"x": 0.701, "y": 0.5}, {"x": 0.701, "y": 0.508}, {"x": 0.7, "y": 0.508}]
        w = self.werte({"annotations": [raum("groundfloor")], "outer_outlines": {"groundfloor": winzig}})
        self.assertIsNone(w["umriss_m2"])
        self.assertIn("zu klein", w["umriss_fehlt"])

    def test_klassen(self):
        grenzen = [150, 220]
        self.assertEqual(self.m.groessenklasse(120, grenzen), 1)
        self.assertEqual(self.m.groessenklasse(150, grenzen), 2)
        self.assertEqual(self.m.groessenklasse(260, grenzen), 3)
        self.assertIsNone(self.m.groessenklasse(None, grenzen))

    def test_drittel_vorschlag(self):
        self.assertEqual(self.m.drittel_grenzen([100, 110, 120, 200, 210, 220, 300, 310, 320]), [200, 300])


if __name__ == "__main__":
    unittest.main()
