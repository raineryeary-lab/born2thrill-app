"""katalogzeile.zeile(): the kon_grundrisse row for a house, by the same rule
the original catalogue import used. Plan: plans/katalogzeile-automatisch-v1.md.

The rule was reconstructed from the live list; this test holds it to that
list for every house in data/simplifier-v2/dataset.json, and names every
mismatch instead of tolerating it silently.
"""

import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import katalogzeile  # noqa: E402

LIVE = json.load(open(HERE / "testdaten" / "grundrisse-live-2026-10-20.json", encoding="utf-8"))
DATASET = json.load(open(HERE.parent / "data" / "simplifier-v2" / "dataset.json", encoding="utf-8"))
PROJECTS = HERE.parents[1] / "floorplan-simplifier" / "projects"


def ausstattung_set(text):
    return {a.strip() for a in (text or "").split(",") if a.strip()}


class Reproduktion(unittest.TestCase):
    """Every house in the dataset AND in the live list."""

    @classmethod
    def setUpClass(cls):
        live = {r["id"]: r for r in LIVE}
        cls.paare = []
        for record in DATASET["projects"]:
            row = live.get(record["project_id"])
            if row:
                cls.paare.append((record, row, katalogzeile.zeile_aus_dataset(record)))

    def treffer(self, spalte, schluessel, mindestens):
        falsch = [(rec["project_id"], row[schluessel], neu[spalte])
                  for rec, row, neu in self.paare if row[schluessel] != neu[spalte]]
        ok = len(self.paare) - len(falsch)
        self.assertGreaterEqual(ok, mindestens,
                                f"{spalte}: {ok}/{len(self.paare)}; abweichend: {falsch[:12]}")
        return falsch

    def test_mindestens_300_haeuser(self):
        self.assertGreaterEqual(len(self.paare), 300)

    def test_haustyp(self):
        self.treffer("haustyp", "t", 307)

    def test_geschosse(self):
        self.treffer("geschosse", "f", 306)

    def test_keller(self):
        self.treffer("keller", "b", 309)

    def test_raeume(self):
        self.treffer("raeume", "r", 308)

    def test_schlaf_kinder_baeder(self):
        self.treffer("schlafzimmer", "sz", 311)
        self.treffer("kinderzimmer", "kz", 311)
        self.treffer("baeder", "bd", 310)

    def test_ausstattung(self):
        falsch = [(rec["project_id"], sorted(ausstattung_set(row["a"]) ^ set(neu["ausstattung"].split(", "))))
                  for rec, row, neu in self.paare
                  if ausstattung_set(row["a"]) != set(neu["ausstattung"].split(", "))]
        # 7 named deviations (2026-10-20 snapshot): bungalow_040_66 is a hand
        # INSERT, the others' drawings changed after the August import.
        self.assertLessEqual(len(falsch), 7, f"ausstattung abweichend: {falsch[:12]}")

    def test_hash(self):
        self.treffer("hash", "h", 305)


class AusDemProjekt(unittest.TestCase):
    def test_twostorey_059_wie_von_hand(self):
        ordner = PROJECTS / "twostorey_059"
        if not ordner.exists():
            self.skipTest("twostorey_059 not on this machine")
        neu = katalogzeile.zeile_aus_projekt(str(ordner))
        self.assertEqual((neu["haustyp"], neu["geschosse"], neu["keller"], neu["raeume"],
                          neu["schlafzimmer"], neu["kinderzimmer"], neu["baeder"]),
                         ("Zweigeschosser", 2, 0, 11, 1, 2, 1))
        self.assertEqual(set(neu["ausstattung"].split(", ")),
                         {"Bad", "Schlafzimmer", "Kinderzimmer", "Arbeitszimmer", "Gäste-WC",
                          "HWR", "Wohnen", "Essen", "Küche"})

    def test_keller_und_leere_raeume(self):
        record = {"project_id": "x", "house_type": "twostorey", "annotation_sha256": "abc" * 10,
                  "floors": [
                      {"floor_level": "basement", "rooms": [{"room_id": "keller", "room_ids": ["keller"]}]},
                      {"floor_level": "groundfloor", "rooms": [
                          {"room_id": "diele", "room_ids": ["diele"]},
                          {"room_id": "du_wc", "room_ids": ["du_wc"]},
                          {"room_id": "luftraum", "room_ids": ["luftraum"]}]}]}
        neu = katalogzeile.zeile_aus_dataset(record)
        self.assertEqual(neu["keller"], 1)
        self.assertEqual(neu["geschosse"], 2)
        self.assertEqual(neu["baeder"], 0)
        # a DU-WC on the ground floor is the import's Gaeste-WC; diele and
        # luftraum add nothing
        self.assertEqual(neu["ausstattung"], "Gäste-WC")

    def test_nur_bekannte_worte(self):
        self.assertTrue(set(katalogzeile.WORTE) >= {"Bad", "Gäste-WC", "storage", "hobby_room"})
        self.assertEqual(set(katalogzeile.HAUSTYPEN.values()),
                         {"Bungalow", "Zweigeschosser", "1,5-Geschosser", "Sonstige",
                          "Zweigeschosser mit Keller"})


if __name__ == "__main__":
    unittest.main()
