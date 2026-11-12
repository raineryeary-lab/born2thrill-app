"""Preisrechner im Annotator (plans/annotator-preisrechner-v1.md).

Rainer, 2026-11-07: "cant you build another price calculator in the anotater?"
vorschau(plan, d) rechnet wie die Matrix, aber aus der ungespeicherten Zeichnung.
"""
import copy
import importlib.machinery
import importlib.util
import json
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = "bungalow_2_familienhaus"


def lade(datei="konfigurator-matrix.py", name="kmatrix_vorschau"):
    os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", r"E:\born2thrill-local-workbench-data")
    loader = importlib.machinery.SourceFileLoader(name, str(HERE / datei))
    spec = importlib.util.spec_from_loader(name, loader)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Vorschau(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.m.einstellungen_laden()
        self.d = json.loads((Path(self.m.PROJECTS) / PLAN / "annotations.json").read_text(encoding="utf-8"))

    def test_gespeicherte_zeichnung_gleich_matrix(self):
        gespeichert = self.m.haus_werte(PLAN)
        v = self.m.vorschau(PLAN, copy.deepcopy(self.d))
        self.assertEqual(v["qm"], gespeichert["qm"])
        self.assertEqual(v["zimmer"], gespeichert["zimmer"])
        self.assertEqual(v["volumen_m3"], gespeichert["volumen_m3"])
        self.assertEqual(v["haustyp"], gespeichert["haustyp"])
        self.assertEqual(v["preise"][0]["preis"], round(gespeichert["qm"] * float(self.m.EINST["preis_pro_m2"])))

    def test_ungespeicherte_aenderung_zaehlt(self):
        d = copy.deepcopy(self.d)
        zimmer = [a for a in d["annotations"] if self.m.ist_zimmer(a.get("label"))
                  and "wohnen" not in a["label"].lower()]
        d["annotations"].remove(zimmer[0])
        v = self.m.vorschau(PLAN, d)
        voll = self.m.vorschau(PLAN, copy.deepcopy(self.d))
        self.assertLess(v["qm"], voll["qm"])

    def test_wohneinheiten_aus_zeichnung(self):
        d = copy.deepcopy(self.d)
        d["wohneinheiten"] = 1
        self.assertNotEqual(self.m.vorschau(PLAN, d)["haustyp"], "zfh")
        d["wohneinheiten"] = 2
        self.assertEqual(self.m.vorschau(PLAN, d)["haustyp"], "zfh")

    def test_budgetspalte(self):
        self.assertEqual(self.m.budgetspalte(449_999), "bis 450.000 €")
        self.assertEqual(self.m.budgetspalte(450_000), "450.000–600.000 €")
        self.assertEqual(self.m.budgetspalte(600_000), "über 600.000 €")

    def test_ohne_raeume(self):
        self.assertIn("fehlt", self.m.vorschau(PLAN, {"annotations": []}))

    @unittest.skipUnless((HERE / "konfigurator-matrix.py.before-preisrechner").exists(), "keine Sicherung")
    def test_alle_haeuser_wie_vorher(self):
        alt = lade("konfigurator-matrix.py.before-preisrechner", "kmatrix_alt")
        for plan in sorted(os.listdir(self.m.PROJECTS)):
            if plan.startswith("_") or not (Path(self.m.PROJECTS) / plan).is_dir():
                continue
            self.assertEqual(self.m.haus_werte(plan), alt.haus_werte(plan), plan)


if __name__ == "__main__":
    unittest.main()
