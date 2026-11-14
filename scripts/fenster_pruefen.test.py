"""Tests fuer fenster-pruefen.py (fenster-pruefen-v1, REGELN 40)."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("fp", os.path.join(HERE, "fenster-pruefen.py"))
fp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fp)

RAUM = [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]          # 16 m² -> 2 m² Fenster noetig
WAND = {"id": "w", "start": [0, 0], "end": [4000, 0], "thickness": 240}


def geschoss(level, fenster, name="Kind"):
    return {"floor_level": level, "walls": [WAND],
            "rooms": [{"id": "r-" + level, "name": name, "polygon_mm": RAUM, "area_m2": 16.0}],
            "openings": [{"id": f"{level}-{i}", "wall_id": "w", "opening_type": "window",
                          "position": pos, "width": breite} for i, (pos, breite) in enumerate(fenster)]}


class Licht(unittest.TestCase):
    def test_zu_wenig_fenster_wird_gemeldet(self):
        # 1010 x 1350 = 1,36 m² < 2 m²
        r = fp.pruefe({"floors": [geschoss("groundfloor", [(0.5, 1010)])]}, {"elements": []})
        self.assertEqual(len(r["licht"]), 1)
        self.assertEqual(r["licht"][0]["soll_m2"], 2.0)

    def test_genug_fenster_ist_ok(self):
        r = fp.pruefe({"floors": [geschoss("groundfloor", [(0.5, 1510)])]}, {"elements": []})
        self.assertEqual(r["licht"], [])

    def test_bodentief_zaehlt_hoeher(self):
        el = {"elements": [{"id": "groundfloor-0", "window_type": "bodentief"}]}
        # 1010 x 2100 = 2,12 m²
        r = fp.pruefe({"floors": [geschoss("groundfloor", [(0.5, 1010)])]}, el)
        self.assertEqual(r["licht"], [])

    def test_bad_und_kinderbad_brauchen_kein_licht(self):
        for name in ("Bad", "Kinderbad", "Flur"):
            r = fp.pruefe({"floors": [geschoss("groundfloor", [], name)]}, {"elements": []})
            self.assertEqual(r["licht"], [], name)


class Flucht(unittest.TestCase):
    def pruefe(self, unten, oben):
        geo = {"floors": [geschoss("groundfloor", [unten]), geschoss("upperfloor", [oben])]}
        return fp.pruefe(geo, {"elements": []})["flucht"]

    def test_genau_mittig_ist_ok(self):
        self.assertEqual(self.pruefe((0.5, 1000), (0.5, 1500)), [])

    def test_kante_buendig_ist_ok(self):
        # unten 1500..2500, oben 1500..2100 -> linke Kante gleich
        self.assertEqual(self.pruefe((0.5, 1000), (0.45, 600)), [])

    def test_fast_fluchtend_wird_gemeldet(self):
        z = self.pruefe((0.5, 1000), (0.53, 1000))      # 120 mm daneben
        self.assertEqual(len(z), 1)
        self.assertEqual(z[0]["daneben_mm"], 120)

    def test_weit_daneben_ist_absicht(self):
        self.assertEqual(self.pruefe((0.25, 800), (0.75, 800)), [])


if __name__ == "__main__":
    unittest.main()
