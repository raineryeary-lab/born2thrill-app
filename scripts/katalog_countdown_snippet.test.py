"""Countdown ueber dem Grundriss-Katalog (plans/katalog-countdown-v1.md).

Rainer, 2026-11-07: "could you add this list to the grundrisskatalog? towards
the top so i can countdown?"
"""
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade():
    spec = importlib.util.spec_from_file_location("katalog_countdown", HERE / "katalog-countdown-snippet.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


HAEUSER = [
    {"plan": "a", "state": "fertig", "catalogue_images": 9},
    {"plan": "b", "state": "fertig_update", "catalogue_images": 9},
    {"plan": "c", "state": "ausrichtung_noetig", "catalogue_images": 1},
    {"plan": "d", "state": "baubereit", "catalogue_images": 0},
    {"plan": "e", "state": "bau_veraltet", "catalogue_images": 0},
    # nur das Grundrissbild hochgeladen: es fehlen die Codex-Bilder, nicht die Freigabe
    {"plan": "f", "state": "bilder_freigeben", "catalogue_images": 1},
    {"plan": "g", "state": "bilder_freigeben", "catalogue_images": 10},
]


class Countdown(unittest.TestCase):
    def setUp(self):
        self.m = lade()
        self.d = self.m.zaehlen(HAEUSER, grundriss_bilder={"c", "f"})

    def test_zahlen(self):
        self.assertEqual((self.d["fertig"], self.d["gesamt"], self.d["offen"]), (2, 7, 5))

    def test_schritte_in_reihenfolge_und_mit_namen(self):
        schritte = [(s["titel"], s["plaene"]) for s in self.d["schritte"]]
        titel = [t for t, _ in schritte]
        self.assertEqual(titel, ["Geschosse ausrichten (Annotator)", "Bauen",
                                 "Codex-Bilder fehlen", "Bilder freigeben"])
        self.assertEqual(dict(schritte)["Bauen"], ["d", "e"])
        self.assertEqual(dict(schritte)["Codex-Bilder fehlen"], ["f"])
        self.assertEqual(dict(schritte)["Bilder freigeben"], ["g"])

    def test_nur_fuer_eingeloggte_bearbeiter(self):
        php = self.m.php(self.d, "2026-11-07 16:00")
        self.assertIn("current_user_can( 'edit_posts' )", php)
        self.assertIn("grundriss_katalog", php)
        for verboten in ("\\", "`", "${"):
            self.assertNotIn(verboten, php)


if __name__ == "__main__":
    unittest.main()
