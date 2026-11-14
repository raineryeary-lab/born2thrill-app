"""loch-im-flur-v1: ein Treppenloch, das INNERHALB des Flurs gezeichnet ist,
bekommt keine Aussenwaende, und die Fassade daneben bleibt geschlossen.

Rainer, 2026-11-09, twostorey_025: "the 3d walls upstairs are broken".
Geometrie wie dort: Flur 0..6000 x 0..1800, Loch am Fassadenende 4000..6000,
Bad darunter, Fassade bei x = 6000.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "plan_builder", os.path.join(HERE, "build-simplifier-render-plan.py"))
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)


def box(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


ROOMS = [
    {"id": "flur", "name": "Flur", "kind": "circulation", "polygon_mm": box(0, 0, 6000, 1800)},
    {"id": "loch", "name": "Treppenöffnung", "kind": "treppenoeffnung", "polygon_mm": box(4000, 0, 6000, 1800)},
    {"id": "bad", "name": "Bad", "kind": "sanitary", "polygon_mm": box(0, -3000, 6000, 0)},
]


class LochImFlur(unittest.TestCase):
    def setUp(self):
        self.walls = pb.build_walls(ROOMS)

    def test_keine_aussenwand_mitten_im_flur(self):
        for w in self.walls:
            if w["wall_type"] != "exterior":
                continue
            xs = (w["start_mm"][0], w["end_mm"][0])
            self.assertFalse(all(500 < x < 5500 for x in xs) and abs(xs[0] - xs[1]) < 1,
                             f"Aussenwand im Flur: {w}")

    def test_lochkante_zum_flur_ist_innenwand_und_damit_gelaender(self):
        innen = [w for w in self.walls if w["wall_type"] == "interior"
                 and set(w["rooms"]) == {"flur", "loch"}]
        self.assertTrue(innen, self.walls)
        rooms = [dict(r) for r in ROOMS]
        offen = pb.offene_deckenloch_waende(rooms, self.walls)
        self.assertTrue({w["id"] for w in innen} <= offen)

    def test_fassade_neben_dem_loch_ist_aussenwand(self):
        fassade = [w for w in self.walls if w["wall_type"] == "exterior"
                   and abs(w["start_mm"][0] - w["end_mm"][0]) < 1 and w["start_mm"][0] > 5900
                   and min(w["start_mm"][1], w["end_mm"][1]) < 900 < max(w["start_mm"][1], w["end_mm"][1])]
        self.assertTrue(fassade, self.walls)

    def test_flur_bad_nur_eine_wand(self):
        zwischen = [w for w in self.walls if abs(w["start_mm"][1] - w["end_mm"][1]) < 1
                    and -300 < w["start_mm"][1] < 300 and w["wall_type"] == "exterior"]
        self.assertEqual(zwischen, [])


if __name__ == "__main__":
    unittest.main()
