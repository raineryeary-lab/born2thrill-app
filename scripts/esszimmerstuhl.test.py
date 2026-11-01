"""Einzelner Esszimmerstuhl bekommt das Modell der Essgruppen-Stuehle (esszimmerstuhl-modell-v1).

Rainer, 2026-10-23, onehalfstorey_046: go.py stoppte an
"R5_appliance_finishes ... dining_chair" -- vier einzelne Esszimmerstuehle am
runden Tisch hatten kein Modell und wurden als Kasten gebaut.
"""
import importlib.util
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", r"E:\born2thrill-local-workbench-data")


def lade(name, datei):
    spec = importlib.util.spec_from_file_location(name, HERE / datei)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class EsszimmerstuhlTests(unittest.TestCase):
    def setUp(self):
        self.plan = lade("bsrp", "build-simplifier-render-plan.py")

    def test_beide_stile_haben_ein_modell(self):
        for stil in ("modern", "classic"):
            picks = self.plan.load_model_picks(stil)
            self.assertIn("esszimmerstuhl", picks, stil)
            self.assertEqual(picks["esszimmerstuhl"]["path"], picks["essgruppe_stuhl"]["path"], stil)

    def test_die_regel_des_pruefers_bleibt(self):
        verify = lade("verify_render", "verify_render.py")
        kasten = {"floors": [{"placements": [{"build": "box", "type": "dining_chair"}]}]}
        self.assertTrue(verify.check_finish_coverage(kasten))


if __name__ == "__main__":
    unittest.main()
