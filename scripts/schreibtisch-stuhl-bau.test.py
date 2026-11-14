"""Rainer, 2026-10-16: jeder Schreibtisch bekommt beim Bau seinen Stuhl,
ohne eigenes Symbol im Plan."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", HERE)
spec = importlib.util.spec_from_file_location("plan", os.path.join(HERE, "build-simplifier-render-plan.py"))
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


class StuhlTests(unittest.TestCase):
    def test_tisch_bekommt_stuhl_davor(self):
        tisch = {"id": "t1", "symbol": "schreibtisch", "position_mm": [1000, 1000],
                 "rotation_deg": 0, "footprint_mm": {"width_mm": 1600, "depth_mm": 800}}
        alle = plan.mit_schreibtischstuehlen([tisch])
        stuhl = [s for s in alle if s["symbol"] == "schreibtischstuhl"]
        self.assertEqual(len(stuhl), 1)
        self.assertEqual(stuhl[0]["position_mm"], [1000, 1555])   # 400 + 305 - 150
        self.assertEqual(stuhl[0]["rotation_deg"], 180)

    def test_gedrehter_kindertisch(self):
        tisch = {"id": "t2", "symbol": "schreibtisch_kind", "position_mm": [1000, 1000],
                 "rotation_deg": 90, "footprint_mm": {"width_mm": 1200, "depth_mm": 600}}
        stuhl = [s for s in plan.mit_schreibtischstuehlen([tisch]) if s["symbol"] == "schreibtischstuhl"][0]
        self.assertAlmostEqual(stuhl["position_mm"][0], 1000 - 455, places=1)
        self.assertAlmostEqual(stuhl["position_mm"][1], 1000, places=1)
        self.assertEqual(stuhl["rotation_deg"], 270)

    def test_vorhandener_stuhl_wird_nicht_verdoppelt(self):
        tisch = {"id": "t1", "symbol": "schreibtisch", "position_mm": [1000, 1000],
                 "rotation_deg": 0, "footprint_mm": {"width_mm": 1600, "depth_mm": 800}}
        hand = {"id": "s", "symbol": "schreibtischstuhl", "position_mm": [1100, 1500], "rotation_deg": 180}
        alle = plan.mit_schreibtischstuehlen([tisch, hand])
        self.assertEqual(sum(s["symbol"] == "schreibtischstuhl" for s in alle), 1)


if __name__ == "__main__":
    unittest.main()
