"""Haustyp in der Matrix: die gezeichneten Geschosse schlagen den gespeicherten Typ.

Rainer, 2026-11-07, zu bungalow_034 (EG + OG) und bungalow_generationat (EG + DG),
beide in data.json als "bungalow" gespeichert: "Both are EFH". Ein Haus mit
Ober- oder Dachgeschoss ist im Konfigurator nie ein Bungalow. data.json bleibt
unberuehrt (es steuert Bau und Katalog).
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
    spec = importlib.util.spec_from_file_location("kmatrix_haustyp", HERE / "konfigurator-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def raum(ebene):
    return {"id": "r" + ebene, "label": "Kind", "floor_level": ebene,
            "points": [{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}, {"x": 0.3, "y": 0.3}]}


class Haustyp(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.tmp = tempfile.TemporaryDirectory()
        self.m.PROJECTS = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def haus(self, name, ebenen, house_type="bungalow", elemente=(), wohneinheiten=None):
        ordner = Path(self.tmp.name) / name
        ordner.mkdir()
        ann = {"annotations": [raum(e) for e in ebenen], "elements": list(elemente)}
        if wohneinheiten:
            ann["wohneinheiten"] = wohneinheiten
        (ordner / "annotations.json").write_text(json.dumps(ann), encoding="utf-8")
        (ordner / "data.json").write_text(json.dumps({"house_type": house_type}), encoding="utf-8")
        return name

    def test_bungalow_mit_obergeschoss_ist_efh(self):
        self.assertEqual(self.m.haustyp(self.haus("bungalow_034", ["groundfloor", "upperfloor"])), "efh")

    def test_bungalow_mit_dachgeschoss_ist_efh(self):
        self.assertEqual(self.m.haustyp(self.haus("bungalow_generationat", ["groundfloor", "attic"])), "efh")

    def test_bungalow_mit_treppe_ist_efh(self):
        # Rainer, 2026-11-07: "if there are stairs its not a bungalow"
        treppe = {"type": "stairs", "floor_level": "groundfloor", "points": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}]}
        self.assertEqual(self.m.haustyp(self.haus("bungalow_009", ["groundfloor"], elemente=[treppe])), "efh")

    def test_wohneinheiten_zfh_und_mfh(self):
        # wohneinheiten-zfh-mfh-v1 (Rainer, 2026-11-07)
        self.assertEqual(self.m.haustyp(self.haus("twostorey_a", ["groundfloor", "upperfloor"], "2-storey",
                                                  wohneinheiten=2)), "zfh")
        self.assertEqual(self.m.haustyp(self.haus("twostorey_b", ["groundfloor", "upperfloor"], "2-storey",
                                                  wohneinheiten=4)), "mfh")
        self.assertEqual(self.m.haustyp(self.haus("twostorey_c", ["groundfloor", "upperfloor"], "2-storey")), "efh")

    def test_echter_bungalow_bleibt(self):
        self.assertEqual(self.m.haustyp(self.haus("bungalow_001", ["groundfloor"])), "bungalow")

    def test_hanghaus_mit_untergeschoss_ist_efh(self):
        self.assertEqual(self.m.haustyp(self.haus("twostorey_060", ["basement", "groundfloor"], "twostorey")), "efh")


if __name__ == "__main__":
    unittest.main()
