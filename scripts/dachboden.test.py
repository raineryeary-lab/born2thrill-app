"""Bungalow mit Dachboden als Ausbaureserve (dachboden-ausbaureserve-v1).

Rainer, 2026-10-23, bungalow_generationat: "this one doesn't have a 2 geschoss
but just an attic with dachschraegen no walls as ausbaureserve". Die Ebene
`attic` ist kein Geschoss: nichts darauf wird gebaut, ihre Fenster werden
Giebelfenster, das Dach ist das steile Satteldach direkt auf dem Erdgeschoss.
"""
import copy
import importlib.util
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade(name, datei):
    spec = importlib.util.spec_from_file_location(name, HERE / datei)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def beispiel():
    return {
        "floor_scale": {"groundfloor": 13.0, "attic": 13.0},
        "annotations": [
            {"id": "w", "floor_level": "groundfloor", "room_ids": ["wohnen"], "points": []},
            {"id": "d", "floor_level": "attic", "room_ids": ["luftraum"], "points": []},
            {"id": "a", "floor_level": "attic", "room_ids": ["abstell"], "points": []},
        ],
        "elements": [
            {"id": "f1", "type": "window", "floor_level": "groundfloor", "points": []},
            {"id": "s0", "type": "stairs", "floor_level": "groundfloor", "points": []},
            {"id": "s1", "type": "stairs", "floor_level": "attic", "points": []},
            {"id": "g1", "type": "window", "floor_level": "attic", "window_type": "bodentief",
             "sill_height_mm": 0, "points": [{"x": 0.10, "y": 0.42}, {"x": 0.10, "y": 0.52}]},
            {"id": "g2", "type": "window", "floor_level": "attic", "window_type": "bodentief",
             "sill_height_mm": 0, "points": [{"x": 0.92, "y": 0.43}, {"x": 0.92, "y": 0.51}]},
        ],
        "roof_type_modern": "flachdach",
    }


class AbspaltenTests(unittest.TestCase):
    def setUp(self):
        self.mod = lade("dachboden", "dachboden.py")

    def test_attic_ist_danach_kein_geschoss_mehr(self):
        a = beispiel()
        self.assertTrue(self.mod.abspalten(a))
        self.assertEqual({x["floor_level"] for x in a["annotations"]}, {"groundfloor"})
        self.assertEqual({x["floor_level"] for x in a["elements"]}, {"groundfloor"})

    def test_die_treppe_des_erdgeschosses_bleibt_die_einzige(self):
        a = beispiel()
        self.mod.abspalten(a)
        self.assertEqual([e["id"] for e in a["elements"] if e["type"] == "stairs"], ["s0"])

    def test_fenster_werden_giebelfenster(self):
        a = beispiel()
        self.mod.abspalten(a)
        self.assertEqual([f["id"] for f in a["_dachboden"]["fenster"]], ["g1", "g2"])
        self.assertEqual(a["_dachboden"]["level"], "attic")

    def test_beide_stile_satteldach(self):
        a = beispiel()
        self.mod.abspalten(a)
        self.assertEqual(a["roof_type_modern"], "satteldach")
        self.assertEqual(a["roof_type_classic"], "satteldach")
        self.assertEqual(a["roof_type_modern_herkunft"], "dachboden")

    def test_haus_ohne_attic_bleibt_wie_es_ist(self):
        a = beispiel()
        a["annotations"] = [x for x in a["annotations"] if x["floor_level"] != "attic"]
        a["elements"] = [x for x in a["elements"] if x["floor_level"] != "attic"]
        vorher = copy.deepcopy(a)
        self.assertFalse(self.mod.abspalten(a))
        self.assertEqual(a, vorher)

    def test_nur_attic_ohne_erdgeschoss_wird_nicht_abgespalten(self):
        a = {"annotations": [{"floor_level": "attic", "points": []}], "elements": []}
        self.assertFalse(self.mod.abspalten(a))


class FensterHoeheTests(unittest.TestCase):
    def setUp(self):
        self.mod = lade("dachboden", "dachboden.py")

    def test_mitten_im_giebel_volle_hoehe(self):
        # Giebel 8 m breit, 40 Grad: Mitte hat 4 m * tan40 = 3,36 m Platz
        self.assertAlmostEqual(self.mod.fenster_hoehe(4.0, 1.0, 0.0, 8.0, 40.0, 2.1), 2.1)

    def test_am_rand_auf_die_dachschraege_gekuerzt(self):
        h = self.mod.fenster_hoehe(1.5, 1.0, 0.0, 8.0, 40.0, 2.1)
        self.assertAlmostEqual(h, 1.0 * math.tan(math.radians(40.0)) - self.mod.RAND_M, places=6)

    def test_zu_nah_an_der_traufe_kein_fenster(self):
        self.assertIsNone(self.mod.fenster_hoehe(0.6, 1.0, 0.0, 8.0, 40.0, 2.1))


class NahtTests(unittest.TestCase):
    def test_load_annotations_spaltet_ab(self):
        quelle = (HERE / "build-simplifier-render-plan.py").read_text(encoding="utf-8")
        start = quelle.index("def load_annotations(")
        koerper = quelle[start:quelle.index("\ndef ", start + 10)]
        self.assertIn("dachboden.abspalten(annotations)", koerper)

    def test_der_plan_traegt_die_giebelfenster(self):
        quelle = (HERE / "build-simplifier-render-plan.py").read_text(encoding="utf-8")
        self.assertIn('"dachboden": dachboden_plan(', quelle)

    def test_der_renderer_baut_sie(self):
        quelle = (HERE / "render-exterior.py").read_text(encoding="utf-8")
        self.assertIn('plan.get("dachboden")', quelle)
        self.assertIn("dachboden.fenster_hoehe(", quelle)

    def test_nur_ein_satteldach_wird_geliefert(self):
        import json
        import tempfile
        run = lade("run_project", "run_project.py")
        with tempfile.TemporaryDirectory() as tmp:
            pfad = Path(tmp) / "plan.json"
            pfad.write_text(json.dumps({"plan_id": "bungalow_x", "dachboden": {"giebelfenster": []}}),
                            encoding="utf-8")
            self.assertEqual(run.roof_types_for_plan(str(pfad)), ("satteldach",))


class GeschosseTests(unittest.TestCase):
    """go.py zaehlte die Ebene attic als Geschoss: Bau mit --floors 0,1, ein
    "upper"-Innenbild, das es nicht gibt, und "the rule says 3" (2026-10-23)."""

    def setUp(self):
        self.mod = lade("dachboden", "dachboden.py")

    def test_attic_zaehlt_nicht_als_geschoss(self):
        self.assertEqual(self.mod.geschoss_ebenen({"groundfloor", "attic"}), ["groundfloor"])

    def test_andere_haeuser_unveraendert(self):
        self.assertEqual(self.mod.geschoss_ebenen({"groundfloor", "upperfloor"}),
                         ["groundfloor", "upperfloor"])
        self.assertEqual(self.mod.geschoss_ebenen({"attic"}), ["attic"])

    def test_go_zaehlt_damit(self):
        quelle = (HERE / "go.py").read_text(encoding="utf-8")
        start = quelle.index("def storeys(")
        koerper = quelle[start:quelle.index("\ndef ", start + 10)]
        self.assertIn("dachboden.geschoss_ebenen(", koerper)


class WohnDachgeschossTests(unittest.TestCase):
    """DG-MIT-KNIESTOCK-001 (Rainer, 2026-10-24, other_vito: EG + OG + DG mit
    Kniestock und Dachschraegen). Ein Dachgeschoss mit Wohnraeumen ist ein
    Geschoss, kein Dachboden -- nur Luftraum/Abstell/Speicher (GenerationAt)
    ist Ausbaureserve.
    """

    def setUp(self):
        self.mod = lade("dachboden", "dachboden.py")

    def mit_dg(self, ids, og=True):
        a = beispiel()
        a["annotations"] = [x for x in a["annotations"] if x["floor_level"] != "attic"]
        if og:
            a["annotations"].append({"id": "o", "floor_level": "upperfloor", "room_ids": ["kind"], "points": []})
        for i, rid in enumerate(ids):
            a["annotations"].append({"id": "d%d" % i, "floor_level": "attic", "room_ids": [rid], "points": []})
        return a

    def test_dg_mit_hobbyraum_und_og_wird_nicht_abgespalten(self):
        a = self.mit_dg(["hobby", "hobby", "flur"])
        self.assertFalse(self.mod.abspalten(a))
        self.assertIn("attic", {x["floor_level"] for x in a["annotations"]})

    def test_dg_mit_kinderzimmern_ohne_og_wird_nicht_abgespalten(self):
        # 1,5-Geschosser aus dem Katalog: EG + DG mit Kind/Eltern/Bad
        self.assertFalse(self.mod.abspalten(self.mit_dg(["kind", "eltern", "bad", "flur"], og=False)))

    def test_nur_luftraum_und_abstell_bleibt_ausbaureserve(self):
        self.assertTrue(self.mod.abspalten(self.mit_dg(["luftraum", "abstell"], og=False)))

    def test_reihenfolge_dg_zuletzt(self):
        self.assertEqual(self.mod.geschoss_reihenfolge({"attic", "groundfloor", "upperfloor"}),
                         ["groundfloor", "upperfloor", "attic"])
        self.assertEqual(self.mod.geschoss_reihenfolge({"upperfloor", "groundfloor", "basement"}),
                         ["basement", "groundfloor", "upperfloor"])

    def test_eg_og_reihenfolge_wie_bisher(self):
        for ebenen in ({"groundfloor"}, {"groundfloor", "upperfloor"}, {"basement", "groundfloor"}):
            self.assertEqual(self.mod.geschoss_reihenfolge(ebenen), sorted(ebenen))

    def test_geschosse_zaehlen_das_wohn_dg_mit(self):
        a = self.mit_dg(["hobby", "flur"])
        self.assertEqual(self.mod.geschoss_ebenen({"groundfloor", "upperfloor", "attic"}, a["annotations"]),
                         ["groundfloor", "upperfloor", "attic"])


if __name__ == "__main__":
    unittest.main()
