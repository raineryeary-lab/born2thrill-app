"""Zimmer zaehlen (zimmer-zaehlung-v1). Rainer, 2026-11-07: "recheck this shit have
codex recheck it" -- Codex und Claude fanden: "Kinderbad" zaehlte als Zimmer (8 Haeuser),
ein kaputtes Label "BÃƒÂ¼ro" (doppelt falsch kodiertes "Büro") zaehlte nicht."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade():
    os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.gettempdir())
    spec = importlib.util.spec_from_file_location("kmatrix_zimmer", HERE / "konfigurator-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Zimmer(unittest.TestCase):
    def setUp(self):
        self.m = lade()

    def test_nassraeume_zaehlen_nie(self):
        for label in ("Kinderbad", "Elternbad", "Bad", "DU-WC", "WC", "Kind / Bad", "Gäste-WC"):
            self.assertFalse(self.m.ist_zimmer(label), label)

    def test_kaputtes_umlaut_label_wird_erkannt(self):
        self.assertTrue(self.m.ist_zimmer("BÃƒÂ¼ro"))
        self.assertTrue(self.m.ist_zimmer("BÃ¼ro"))

    def test_bisherige_zimmer_bleiben(self):
        for label in ("Kind", "Eltern / Schlafen", "Wohnen / Essen / Kochen", "Büro", "Gast", "Wohnen", "Zimmer"):
            self.assertTrue(self.m.ist_zimmer(label), label)
        for label in ("Flur", "Diele", "HWR / HTR", "Ankleide", "Speisekammer", "Kochen", "Luftraum"):
            self.assertFalse(self.m.ist_zimmer(label), label)


if __name__ == "__main__":
    unittest.main()
