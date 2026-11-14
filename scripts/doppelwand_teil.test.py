"""Doppelwand: nur der ueberlappende Teil wird EINE Wand (doppelwand-nur-ueberlappung-v1).

Rainer, 2026-10-23, bungalow_tv1: Dach und Wand ueber der Terrasse. Die
Innenwand Wohnen/Schlafen und die Terrassen-Aussenwand des Wohnens
ueberlappten sich nur in der Ecke (203 mm). Zusammengefasst wurde trotzdem
die ganze Laenge beider -- und als Innenwand typisiert. Damit fehlte die
Terrassenfassade, der Aussenring war offen, Dach und Sockel fielen auf das
umschliessende Rechteck zurueck.
"""
import importlib.util
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module():
    os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", r"E:\born2thrill-local-workbench-data")
    spec = importlib.util.spec_from_file_location(
        "build_simplifier_render_plan", HERE / "build-simplifier-render-plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rechteck(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def y_spanne(w):
    ys = (w["start_mm"][1], w["end_mm"][1])
    return min(ys), max(ys)


class DoppelwandTeilTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        # bungalow_tv1, echte Werte (Spion auf dem Merge, 2026-10-23)
        self.raeume = [
            {"id": "wek", "polygon_mm": rechteck(2866, 6172, 8585, 15392)},
            {"id": "eltern", "polygon_mm": rechteck(8627, 6116, 12650, 10151)},
        ]
        self.innen = {"id": "wall-0", "start_mm": [8606, 10151], "end_mm": [8606, 6172],
                      "thickness_mm": 115, "wall_type": "interior", "rooms": ["eltern", "wek"]}
        self.aussen = {"id": "wall-10", "start_mm": [8498, 15210], "end_mm": [8498, 9948],
                       "thickness_mm": 240, "wall_type": "exterior", "rooms": ["wek"]}

    def test_terrassenfassade_bleibt_aussenwand(self):
        ergebnis = self.mod._merge_overlapping_parallel_walls(
            [self.innen, self.aussen], self.raeume)
        aussen = [w for w in ergebnis if w["wall_type"] == "exterior"]
        self.assertTrue(aussen, ergebnis)
        self.assertTrue(any(y_spanne(w)[1] >= 15200 and y_spanne(w)[0] <= 10400
                            for w in aussen), ergebnis)

    def test_keine_innenwand_ueber_die_raumkante_hinaus(self):
        ergebnis = self.mod._merge_overlapping_parallel_walls(
            [self.innen, self.aussen], self.raeume)
        for w in ergebnis:
            if w["wall_type"] == "interior":
                self.assertLessEqual(y_spanne(w)[1], 10151 + 250, w)

    def test_die_innenwand_bleibt_innenwand(self):
        ergebnis = self.mod._merge_overlapping_parallel_walls(
            [self.innen, self.aussen], self.raeume)
        self.assertTrue(any(w["wall_type"] == "interior" and y_spanne(w)[0] <= 6200
                            for w in ergebnis), ergebnis)

    def test_volle_ueberlappung_wie_bisher_eine_wand(self):
        a = {"id": "a", "start_mm": [0, 0], "end_mm": [0, 5000],
             "thickness_mm": 240, "wall_type": "exterior", "rooms": []}
        b = {"id": "b", "start_mm": [150, 0], "end_mm": [150, 5000],
             "thickness_mm": 240, "wall_type": "exterior", "rooms": []}
        ergebnis = self.mod._merge_overlapping_parallel_walls([a, b], [])
        self.assertEqual(len(ergebnis), 1)
        self.assertEqual(y_spanne(ergebnis[0]), (0, 5000))

    def test_kurzer_ueberstand_wird_kein_eigenes_stueck(self):
        a = {"id": "a", "start_mm": [0, 0], "end_mm": [0, 5000],
             "thickness_mm": 240, "wall_type": "exterior", "rooms": []}
        b = {"id": "b", "start_mm": [150, 120], "end_mm": [150, 5000],
             "thickness_mm": 240, "wall_type": "exterior", "rooms": []}
        ergebnis = self.mod._merge_overlapping_parallel_walls([a, b], [])
        self.assertEqual(len(ergebnis), 1)
        self.assertEqual(y_spanne(ergebnis[0]), (0, 5000))


if __name__ == "__main__":
    unittest.main()
