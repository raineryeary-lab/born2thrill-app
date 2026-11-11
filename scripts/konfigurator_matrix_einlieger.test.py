"""einliegerwohnung-v1: Zimmer zaehlt nur die Hauptwohnung, ELW-Zimmer extra.

Rainer, 2026-11-08: "Nein Hauptwohnung mit ELW in Klammern".
Rechnet an einem echten Haus (bungalow_001), dessen Zeichnung im Speicher
veraendert wird -- auf der Platte aendert sich nichts.
Aufruf: python konfigurator_matrix_einlieger.test.py
"""
import copy
import importlib.machinery
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", r"E:\born2thrill-local-workbench-data")
m = importlib.machinery.SourceFileLoader("matrix_elw", os.path.join(HERE, "konfigurator-matrix.py")).load_module()
PLAN = "bungalow_001"
DATEI = os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects", PLAN, "annotations.json")


def zeichnung():
    with open(DATEI, encoding="utf-8") as f:
        return json.load(f)


class Einlieger(unittest.TestCase):
    def test_elw_zimmer_zaehlen_extra(self):
        d = zeichnung()
        ohne = m.haus_werte(PLAN, copy.deepcopy(d))
        zimmer = [a for a in d["annotations"] if m.ist_zimmer(a.get("label"))
                  and "wohnen" not in (a.get("label") or "").lower()]
        self.assertGreaterEqual(len(zimmer), 2, "Testhaus braucht 2 Zimmer")
        for a in zimmer[:2]:
            a["einlieger"] = True
        d["einliegerwohnung"] = True
        mit = m.haus_werte(PLAN, d)
        self.assertTrue(mit["elw"])
        self.assertGreater(mit["zimmer_elw"], 0)
        self.assertEqual(mit["zimmer"] + mit["zimmer_elw"], ohne["zimmer"])

    def test_ohne_elw_wie_bisher(self):
        w = m.haus_werte(PLAN, zeichnung())
        self.assertNotIn("zimmer_elw", w)
        self.assertNotIn("elw", w)


if __name__ == "__main__":
    unittest.main()
