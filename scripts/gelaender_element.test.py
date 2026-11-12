"""Gelaender-Element: von Hand gezeichnet wie die Trennwand.

Plan: plans/gelaender-element-v1.md.
Rainer, 2026-11-07: "i need to have a railing element like the trennwand,
the treppenloch combine with the should work" -- und "Yes, build it" auf:
ein gezeichnetes Gelaender auf einer Treppenloch-Kante ersetzt dort das
automatische und trifft es an den Ecken.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gelaender_gezeichnet as gg  # noqa: E402


def load_plan_builder():
    spec = importlib.util.spec_from_file_location(
        "build_simplifier_render_plan", HERE / "build-simplifier-render-plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Rahmen:
    """1 Bildeinheit = 10 000 mm, y nicht gespiegelt -- reicht fuer den Test."""
    def point(self, p):
        return (p["x"] * 10000.0, p["y"] * 10000.0)


class PlanBuilder(unittest.TestCase):
    def test_gezeichnetes_gelaender_wird_ein_stueck_in_mm(self):
        bp = load_plan_builder()
        ann = {"elements": [
            {"type": "railing", "floor_level": "upperfloor",
             "points": [{"x": 0.1, "y": 0.2}, {"x": 0.4, "y": 0.2}]},
            {"type": "railing", "floor_level": "groundfloor",
             "points": [{"x": 0.1, "y": 0.2}, {"x": 0.4, "y": 0.2}]},
            {"type": "partition", "floor_level": "upperfloor",
             "points": [{"x": 0.1, "y": 0.5}, {"x": 0.4, "y": 0.5}]},
        ]}
        stuecke = bp.railing_segments(ann, "upperfloor", Rahmen())
        self.assertEqual(len(stuecke), 1)
        self.assertEqual(stuecke[0]["start_mm"], (1000.0, 2000.0))
        self.assertEqual(stuecke[0]["end_mm"], (4000.0, 2000.0))

    def test_gelaender_ist_keine_wand(self):
        bp = load_plan_builder()
        ann = {"elements": [{"type": "railing", "floor_level": "upperfloor",
                             "points": [{"x": 0.1, "y": 0.2}, {"x": 0.4, "y": 0.2}]}]}
        self.assertEqual(bp.partition_walls(ann, "upperfloor", Rahmen()), [])


class Zusammenspiel(unittest.TestCase):
    def test_gelaender_auf_der_kante_deckt_sie_ab(self):
        # Kante 0..4000 mm auf y=0; gezeichnet 1000..3000, 80 mm daneben.
        weg = gg.abdeckung((0, 0), (4000, 0), [{"start_mm": (1000, 80), "end_mm": (3000, 80)}])
        self.assertEqual(len(weg), 1)
        self.assertAlmostEqual(weg[0][0], 0.25)
        self.assertAlmostEqual(weg[0][1], 0.75)

    def test_weit_weg_oder_quer_deckt_nichts(self):
        self.assertEqual(gg.abdeckung((0, 0), (4000, 0),
                                      [{"start_mm": (1000, 600), "end_mm": (3000, 600)}]), [])
        self.assertEqual(gg.abdeckung((0, 0), (4000, 0),
                                      [{"start_mm": (2000, -1000), "end_mm": (2000, 1000)}]), [])

    def test_ohne_intervalle_schneidet_heraus(self):
        self.assertEqual(gg.ohne_intervalle([(0.0, 1.0)], [(0.25, 0.75)]),
                         [(0.0, 0.25), (0.75, 1.0)])
        self.assertEqual(gg.ohne_intervalle([(0.0, 1.0)], [(0.0, 1.0)]), [])

    def test_ende_nah_an_lochecke_rastet_ein(self):
        st = gg.einrasten([{"start_mm": (90, 100), "end_mm": (3000, 100)}], [(0, 0), (4000, 0)])
        self.assertEqual(st[0]["start_mm"], (0, 0))
        self.assertEqual(st[0]["end_mm"], (3000, 100))


class Dollhouse(unittest.TestCase):
    def test_dollhouse_baut_und_verrechnet(self):
        q = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
        self.assertIn("import gelaender_gezeichnet", q)
        self.assertIn('floor.get("railings")', q)
        self.assertIn("gelaender-gezeichnet-", q)
        # Treppenloch (Treppenkern) UND Luftraum/Treppenoeffnung nehmen das
        # gezeichnete Stueck aus der Automatik.
        self.assertGreaterEqual(q.count("gelaender_gezeichnet.abdeckung("), 2)


class Pruefung(unittest.TestCase):
    def test_verify_kennt_gezeichnete_gelaender(self):
        q = (HERE / "verify_render_blend.py").read_text(encoding="utf-8")
        r2 = q[q.index("def check_gelaender("):q.index("def _xy_quad(")]
        self.assertIn('meshes("gelaender-gezeichnet")', r2)
        # Auch ein gezeichnetes Gelaender darf nicht quer ueber den Austritt.
        self.assertIn('meshes("loch-rail") + meshes("gelaender-gezeichnet")', q)


if __name__ == "__main__":
    unittest.main()
