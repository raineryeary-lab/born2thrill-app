"""Staffelgeschoss (STAFFELGESCHOSS-001).

Rainer, 2026-11-01, twostorey_xvit: ueber dem OG ein kleineres Geschoss mit
Dachterrasse, rundherum Kies und eine durchgehende Bruestung. Nur Flachdach.
"""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.gettempdir())


def lade(name, datei):
    spec = importlib.util.spec_from_file_location(name, HERE / datei)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


staffel = lade("staffel", "staffel.py")
dachboden = lade("dachboden", "dachboden.py")
treppe_zugang = lade("treppe_zugang", "treppe_zugang.py")


def wand(a, b, dicke=240):
    return {"start_mm": list(a), "end_mm": list(b), "thickness_mm": dicke, "wall_type": "exterior"}


def viereck(x0, y0, x1, y1):
    return [wand((x0, y0), (x1, y0)), wand((x1, y0), (x1, y1)),
            wand((x1, y1), (x0, y1)), wand((x0, y1), (x0, y0))]


def haus():
    """OG 7 x 12 m, Staffel 5 x 7 m buendig an der Ostseite und an der Suedseite."""
    return [
        {"level": "groundfloor", "walls": viereck(0, 0, 7000, 12000)},
        {"level": "upperfloor", "walls": viereck(0, 0, 7000, 12000)},
        {"level": "staffelgeschoss", "walls": viereck(2000, 0, 7000, 7000),
         "dachterrassen": [[[2000, 7000], [7000, 7000], [7000, 12000], [2000, 12000]]]},
    ]


class Reihenfolge(unittest.TestCase):
    def test_staffel_liegt_ueber_dem_og(self):
        self.assertEqual(dachboden.geschoss_reihenfolge({"staffelgeschoss", "groundfloor", "upperfloor"}),
                         ["groundfloor", "upperfloor", "staffelgeschoss"])

    def test_staffel_ist_ein_geschoss(self):
        self.assertIn("staffelgeschoss", dachboden.geschoss_ebenen({"groundfloor", "upperfloor", "staffelgeschoss"}))

    def test_treppenmeldung_nennt_sg(self):
        text = treppe_zugang.stair_access_message(
            {"ende": "antritt", "level": "staffelgeschoss", "raeume": [], "wall_id": "w"})
        self.assertIn("im SG", text)


class Umriss(unittest.TestCase):
    def test_vier_waende_ergeben_vier_ecken(self):
        ecken = staffel.umriss(viereck(0, 0, 7000, 12000))
        self.assertEqual(len(ecken), 4)
        self.assertEqual({tuple(e) for e in ecken}, {(0, 0), (7000, 0), (7000, 12000), (0, 12000)})

    def test_waende_in_beliebiger_richtung(self):
        w = viereck(0, 0, 7000, 12000)
        w[1]["start_mm"], w[1]["end_mm"] = w[1]["end_mm"], w[1]["start_mm"]
        w = [w[2], w[0], w[3], w[1]]
        self.assertEqual(len(staffel.umriss(w)), 4)

    def test_offener_zug_faellt_auf_die_huellbox(self):
        ecken = staffel.umriss(viereck(0, 0, 7000, 12000)[:3])
        self.assertEqual({tuple(e) for e in ecken}, {(0, 0), (7000, 0), (7000, 12000), (0, 12000)})


class Attika(unittest.TestCase):
    def test_nicht_dort_wo_die_staffelwand_steht(self):
        stuecke = staffel.attika_stuecke(viereck(0, 0, 7000, 12000), viereck(2000, 0, 7000, 7000))
        # Ostseite: nur noch y 7000..12000. Suedseite: nur x 0..2000.
        ost = [s for s in stuecke if s["start_mm"][0] == 7000 and s["end_mm"][0] == 7000]
        self.assertEqual(len(ost), 1)
        self.assertEqual(sorted((ost[0]["start_mm"][1], ost[0]["end_mm"][1])), [7000, 12000])
        sued = [s for s in stuecke if s["start_mm"][1] == 0 and s["end_mm"][1] == 0]
        self.assertEqual(len(sued), 1)
        self.assertEqual(sorted((sued[0]["start_mm"][0], sued[0]["end_mm"][0])), [0, 2000])

    def test_freie_waende_ganz(self):
        stuecke = staffel.attika_stuecke(viereck(0, 0, 7000, 12000), viereck(2000, 0, 7000, 7000))
        self.assertTrue(any(sorted((s["start_mm"][1], s["end_mm"][1])) == [0, 12000]
                            and s["start_mm"][0] == 0 for s in stuecke))

    def test_mitten_zurueckgesetzt_laeuft_alles_durch(self):
        stuecke = staffel.attika_stuecke(viereck(0, 0, 7000, 12000), viereck(1500, 1500, 5500, 8000))
        self.assertEqual(len(stuecke), 4)

    def test_kurze_reste_entfallen(self):
        stuecke = staffel.attika_stuecke([wand((0, 0), (5100, 0))], [wand((0, 0), (5000, 0))])
        self.assertEqual(stuecke, [])


class PlanFeld(unittest.TestCase):
    def test_feld(self):
        feld = staffel.plan_feld(haus())
        self.assertEqual(len(feld["umriss_unten_mm"]), 4)
        self.assertEqual(len(feld["terrassen_mm"]), 1)
        self.assertEqual(len(feld["attika"]), 4)

    def test_ohne_staffel_kein_feld(self):
        self.assertIsNone(staffel.plan_feld(haus()[:2]))

    def test_staffel_allein_kein_feld(self):
        self.assertIsNone(staffel.plan_feld(haus()[2:]))

    def test_staffel_nur_als_oberstes(self):
        self.assertIsNone(staffel.plan_feld(list(reversed(haus()))))


class Kies(unittest.TestCase):
    def test_nicht_unter_der_staffel(self):
        unten = [[0, 0], [7000, 0], [7000, 12000], [0, 12000]]
        oben = [[2000, 0], [7000, 0], [7000, 7000], [2000, 7000]]
        felder = staffel.kies_felder(unten, oben)
        flaeche = sum((f[1][0] - f[0][0]) * (f[2][1] - f[1][1]) for f in felder)
        self.assertEqual(flaeche, 7000 * 12000 - 5000 * 7000)

    def test_im_plan_feld(self):
        self.assertTrue(staffel.plan_feld(haus())["kies_felder_mm"])

    def test_geschossbild_nutzt_die_felder_und_die_windung(self):
        quelle = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
        self.assertIn('STAFFEL.get("kies_felder_mm")', quelle)
        self.assertIn('_winding_nach_unten(_feld)', quelle)


class Daecher(unittest.TestCase):
    def test_nur_flachdach(self):
        run_project = lade("run_project_staffel", "run_project.py")
        with tempfile.TemporaryDirectory() as ordner:
            pfad = os.path.join(ordner, "plan.json")
            with open(pfad, "w", encoding="utf-8") as handle:
                json.dump({"staffelgeschoss": staffel.plan_feld(haus()), "floors": []}, handle)
            self.assertEqual(run_project.roof_types_for_plan(pfad), ("flachdach",))


class Kuerzel(unittest.TestCase):
    def test_codex_auftrag_kennt_sg(self):
        quelle = (HERE / "make-codex-job.py").read_text(encoding="utf-8")
        self.assertIn('"staffelgeschoss": "sg"', quelle)


if __name__ == "__main__":
    unittest.main()
