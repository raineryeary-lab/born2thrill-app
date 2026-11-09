"""Sauna/Fitness/Hobby im Bau und im Codex-Auftrag (sauna-fitness-hobby-v1)."""
import ast
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", tempfile.mkdtemp())


def load(name, datei):
    spec = importlib.util.spec_from_file_location(name, HERE / datei)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class CodexTexte(unittest.TestCase):
    def setUp(self):
        self.job = load("make_codex_job", "make-codex-job.py")

    def test_stuff_inhalt(self):
        self.assertIn("Laufband", self.job.stuff_inhalt("Fitness"))
        self.assertIn("Werkbank", self.job.stuff_inhalt("Hobbyraum"))
        self.assertIn("Liegen", self.job.stuff_inhalt("Sauna / Wellness"))

    def test_saunakabine_rolle(self):
        rolle = self.job.NENNENSWERT.get("saunakabine", "")
        self.assertIn("Saunakabine", rolle)
        self.assertIn("(ersetzen)", rolle)


class Bau(unittest.TestCase):
    def test_saunakabine_als_quader(self):
        b = load("build_simplifier_render_plan", "build-simplifier-render-plan.py")
        self.assertIn("saunakabine", b.RECT_BUILD)
        self.assertEqual(b.SYMBOL_3D["saunakabine"]["height"], 2100)


if __name__ == "__main__":
    unittest.main()
