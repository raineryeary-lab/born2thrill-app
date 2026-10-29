"""1,5-Geschosser: nur das Satteldach. Plan: plans/anderthalb-eine-dachform-v1.md.

Rainer, 2026-10-20: "we dont need the 4 roof forms just the one with the 1,5
story houses".
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# run_project.py verweigert ohne Datenordner -- ein leerer Tempordner genuegt,
# getestet wird nur die Dachformwahl.
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.mkdtemp())


def lade(name, datei):
    spec = importlib.util.spec_from_file_location(name, HERE / datei)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run_project = lade("run_project_t", "run_project.py")
dachform = lade("dachform_t", "dachform.py")


def planfile(**felder):
    fd, pfad = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as h:
        json.dump(felder, h)
    return pfad


class Dachformen(unittest.TestCase):
    def test_anderthalb_nur_satteldach(self):
        self.assertEqual(run_project.roof_types_for_plan(
            planfile(plan_id="onehalfstorey_044", house_type="1.5-storey")),
            # anderthalb-zwerchkubus-modern-v1 (Rainer 2026-10-21: "2: classic + modern")
            ("satteldach", "satteldach-kubus"))

    def test_zweigeschosser_vier(self):
        self.assertEqual(run_project.roof_types_for_plan(
            planfile(plan_id="twostorey_059", house_type="2-storey")),
            ("flachdach", "walmdach", "satteldach", "pultdach"))

    def test_versetztes_pult_bleibt_fuer_andere(self):
        self.assertEqual(run_project.roof_types_for_plan(
            planfile(plan_id="bungalow_007", roof_fourth="doppelpultdach")),
            ("flachdach", "walmdach", "satteldach", "doppelpultdach"))

    def test_standard_dachform(self):
        self.assertEqual(dachform.standard_fuer("onehalfstorey_044"), ("satteldach", "satteldach"))
        self.assertEqual(dachform.standard_fuer("twostorey_059"),
                         (dachform.STANDARD_MODERN, dachform.STANDARD_CLASSIC))


if __name__ == "__main__":
    unittest.main()
