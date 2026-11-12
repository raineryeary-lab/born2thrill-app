"""Luftraum: eine durchgehende Wand nur am offenen Stueck aufschneiden.

Plan luftraum-mischwand-teilen-v1. Rainer, 2026-10-22, onehalfstorey_vv1:
"the Luftraum has no railing even though it is in the editor". wall-2 lief
an Luftraum UND Bad entlang (Raeume {Bad, Luftraum, Flur}) und blieb deshalb
ganz stehen -- das Gelaender fand eine Wand laengs und baute 0 Stuecke.
"""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.mkdtemp())


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_simplifier_render_plan", HERE / "build-simplifier-render-plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rechteck(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


ROOMS = [
    {"id": "lr", "name": "Luftraum", "kind": "luftraum", "polygon_mm": rechteck(4500, 5300, 8000, 7800)},
    {"id": "bad", "name": "Bad", "kind": "sanitary", "polygon_mm": rechteck(4500, 7800, 8000, 11000)},
    {"id": "flur", "name": "Flur", "kind": "circulation", "polygon_mm": rechteck(2000, 5300, 4500, 11000)},
]
MISCH = {"id": "wall-2", "start_mm": [4500.0, 5300.0], "end_mm": [4500.0, 11000.0],
         "thickness_mm": 115, "wall_type": "interior", "rooms": ["bad", "lr", "flur"]}
LR_BAD = {"id": "wall-1", "start_mm": [4500.0, 7800.0], "end_mm": [8000.0, 7800.0],
          "thickness_mm": 115, "wall_type": "interior", "rooms": ["lr", "bad"]}


class Mischwand(unittest.TestCase):
    def setUp(self):
        self.b = load_builder()

    def test_offenes_stueck_am_luftraum(self):
        st = self.b.offene_wandstuecke(ROOMS, [MISCH, LR_BAD])
        self.assertEqual(list(st), ["wall-2"])
        (t0, t1), = st["wall-2"]
        self.assertAlmostEqual(t0, 0.0, places=3)
        self.assertAlmostEqual(t1, 2500 / 5700, places=3)

    def test_wand_zum_bad_bleibt(self):
        self.assertNotIn("wall-1", self.b.offene_wandstuecke(ROOMS, [MISCH, LR_BAD]))

    def test_teilen_und_oeffnungen_umhaengen(self):
        st = self.b.offene_wandstuecke(ROOMS, [MISCH])
        oeff = [{"id": "durchgang", "wall_id": "wall-2", "position": 0.2, "width_mm": 2556.0},
                {"id": "badtuer", "wall_id": "wall-2", "position": 0.75, "width_mm": 856.0}]
        waende, oeffnungen, weg = self.b.waende_teilen([MISCH], oeff, st)
        self.assertEqual(len(waende), 1)
        rest = waende[0]
        self.assertNotEqual(rest["id"], "wall-2")
        self.assertAlmostEqual(rest["start_mm"][1], 7800.0, places=0)
        self.assertAlmostEqual(rest["end_mm"][1], 11000.0, places=0)
        self.assertEqual(weg, ["durchgang"])
        tuer, = oeffnungen
        self.assertEqual(tuer["wall_id"], rest["id"])
        # y der Tuer bleibt: 5300 + 0.75 * 5700 = 9575
        y = rest["start_mm"][1] + tuer["position"] * (rest["end_mm"][1] - rest["start_mm"][1])
        self.assertAlmostEqual(y, 9575.0, places=0)

    def test_plan_ruft_es_auf(self):
        quelle = (HERE / "build-simplifier-render-plan.py").read_text(encoding="utf-8")
        self.assertIn("offene_wandstuecke(rooms, walls)", quelle)
        self.assertIn("waende_teilen(", quelle)


if __name__ == "__main__":
    unittest.main()
