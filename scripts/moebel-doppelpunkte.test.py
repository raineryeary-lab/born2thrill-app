"""Doppelpunkte aus gespeicherten Moebellaeufen ziehen -- aber nur die harmlosen.

Rainer, 2026-08-28: "when i doubleclick to end the creation many times there
are 2 points created at the end", und auf die Frage, ob ein Durchlauf die
bestehenden bereinigen soll: "what ever you think is better".

Beim Nachsehen zerfiel der Befund in zwei Sorten:

1. Ein Pfad (`vorwandinstallation`, `kuechenzeile`), dessen letzter Punkt den
   vorletzten wiederholt. Die Strecke dazwischen ist null lang; sie zu
   entfernen aendert die Form NICHT. 13 Faelle.

2. Ein Rechteck (`kuecheninsel`), dessen zwei Eckpunkte zusammenfallen:
   `onehalfstorey_020` hat eine Kuecheninsel von 0 x 0 mm, `onehalfstorey_029`
   eine von 0 x 50 mm. Das ist kein Doppelpunkt, das ist eine kaputte
   Platzierung -- und sie zu "bereinigen" liesse einen einzelnen Punkt
   zurueck. 4 Faelle.

Der Bereiniger fasst nur die erste Sorte an. Die zweite wird gemeldet: sie
gehoert neu gezeichnet oder geloescht, und das ist eine Entscheidung ueber
Geometrie in Haeusern, deren Lieferung angenommen ist.
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def load():
    spec = importlib.util.spec_from_file_location(
        "moebel_doppelpunkte", HERE / "moebel-doppelpunkte.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class Entdoppeln(unittest.TestCase):
    def setUp(self):
        self.mod = load()

    def test_a_repeated_last_point_is_dropped(self):
        """Der echte Fall aus `german_catalog_review_bungalow_3_2_5_b_100_1`."""
        lauf = [[4200, 8550], [4300, 9250], [6900, 9400], [6800, 7250], [6800, 7250]]
        self.assertEqual(self.mod.entdoppelt(lauf), lauf[:4])

    def test_a_point_a_few_millimetres_off_is_NOT_dropped(self):
        """Der Durchlauf faehrt ueber gespeicherte Haeuser -- da zaehlt Beweis.

        `onehalfstorey_020`: [[4352, 8271], [4352, 10790], [4299, 10790]] --
        die letzten beiden liegen 53 mm auseinander. Sie zu verschmelzen
        kuerzte den Lauf wirklich um 53 mm; das ist eine Geometrieaenderung,
        keine Bereinigung. Der erste Trockenlauf ist genau daran haengen
        geblieben, an einem 50-mm-Fall in
        `german_catalog_review_bungalow_3_1_2_b_85`.

        Der Editor darf beim Anlegen grosszuegiger sein: dort ist noch nichts
        gespeichert.
        """
        lauf = [[4352, 8271], [4352, 10790], [4299, 10790]]
        self.assertEqual(self.mod.entdoppelt(lauf), lauf)
        self.assertEqual(self.mod.befund({"symbol": "vorwandinstallation",
                                          "points_mm": lauf}), "knapp")

    def test_a_deliberate_short_leg_survives(self):
        """200 mm sind eine gezeichnete Strecke, kein Zittern."""
        lauf = [[0, 0], [200, 0], [200, 900]]
        self.assertEqual(self.mod.entdoppelt(lauf), lauf)

    def test_a_clean_run_is_returned_unchanged(self):
        lauf = [[1200, 800], [4300, 840], [4300, 3100]]
        self.assertEqual(self.mod.entdoppelt(lauf), lauf)

    def test_the_shape_is_provably_unchanged(self):
        """Der ganze Grund, warum das gefahrlos ist.

        Die Streckenlaenge des Laufs bleibt gleich -- eine Strecke der Laenge
        null traegt nichts bei.
        """
        lauf = [[4200, 8550], [4300, 9250], [6900, 9400], [6800, 7250], [6800, 7250]]
        self.assertAlmostEqual(self.mod.laenge(lauf),
                               self.mod.laenge(self.mod.entdoppelt(lauf)), places=6)


class WasNichtAngefasstWird(unittest.TestCase):
    def setUp(self):
        self.mod = load()

    def test_a_degenerate_rectangle_is_reported_not_cleaned(self):
        """`onehalfstorey_020`: eine Kuecheninsel von 0 x 0 mm."""
        eintrag = {"symbol": "kuecheninsel",
                   "points_mm": [[9180.4, 5353.9], [9180.4, 5353.9]]}
        self.assertEqual(self.mod.befund(eintrag), "entartet")

    def test_an_almost_degenerate_rectangle_is_reported_as_knapp(self):
        """`onehalfstorey_029`: 0 x 50 mm ist auch keine Insel.

        Sie faellt unter `knapp`, nicht unter `entartet` -- die zwei Ecken
        liegen 50 mm auseinander, nicht aufeinander. Angefasst wird sie so
        oder so nicht.
        """
        eintrag = {"symbol": "kuecheninsel",
                   "points_mm": [[2750, 4150], [2750, 4100]]}
        self.assertEqual(self.mod.befund(eintrag), "knapp")

    def test_a_real_rectangle_is_left_alone(self):
        eintrag = {"symbol": "kuecheninsel",
                   "points_mm": [[2000, 3000], [3600, 4000]]}
        self.assertEqual(self.mod.befund(eintrag), "sauber")

    def test_a_path_with_a_duplicate_is_cleanable(self):
        eintrag = {"symbol": "kuechenzeile",
                   "points_mm": [[0, 0], [1000, 0], [1000, 0]]}
        self.assertEqual(self.mod.befund(eintrag), "zu_bereinigen")

    def test_a_stamp_is_none_of_this(self):
        self.assertEqual(self.mod.befund({"symbol": "kuehlschrank",
                                          "position_mm": [1, 2]}), "sauber")


class DateiSchreiben(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.pfad = os.path.join(self.tmp.name, "floor-0.json")
        self.inhalt = {
            "schema": "zf-moebel-v1",
            "symbols": [
                {"id": "a", "symbol": "kuechenzeile",
                 "points_mm": [[0, 0], [1000, 0], [1000, 0]]},
                {"id": "b", "symbol": "kuecheninsel",
                 "points_mm": [[500, 500], [500, 500]]},
                {"id": "c", "symbol": "kuehlschrank", "position_mm": [10, 20]},
            ],
        }
        with open(self.pfad, "w", encoding="utf-8") as datei:
            json.dump(self.inhalt, datei)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_dry_run_writes_nothing(self):
        vorher = open(self.pfad, encoding="utf-8").read()
        self.mod.bereinige_datei(self.pfad, schreiben=False)
        self.assertEqual(open(self.pfad, encoding="utf-8").read(), vorher)

    def test_writing_drops_the_duplicate_and_keeps_the_rest(self):
        self.mod.bereinige_datei(self.pfad, schreiben=True)
        with open(self.pfad, encoding="utf-8") as datei:
            neu = json.load(datei)  # noqa: F841 -- unten benutzt
        symbole = {s["id"]: s for s in neu["symbols"]}
        self.assertEqual(symbole["a"]["points_mm"], [[0, 0], [1000, 0]])
        self.assertEqual(symbole["b"]["points_mm"], [[500, 500], [500, 500]])
        self.assertEqual(symbole["c"]["position_mm"], [10, 20])

    def test_writing_leaves_a_backup(self):
        """Ohne Sicherung faehrt hier niemand ueber fremde Daten."""
        self.mod.bereinige_datei(self.pfad, schreiben=True)
        self.assertTrue(os.path.exists(self.pfad + ".vor-entdoppeln"))

    def test_a_file_without_duplicates_is_not_rewritten(self):
        self.mod.bereinige_datei(self.pfad, schreiben=True)
        os.remove(self.pfad + ".vor-entdoppeln")
        self.mod.bereinige_datei(self.pfad, schreiben=True)
        self.assertFalse(os.path.exists(self.pfad + ".vor-entdoppeln"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
