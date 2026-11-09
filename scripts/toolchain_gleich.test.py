"""run_project.py stempelt den Toolchain-Fingerabdruck, batch-build.py prueft
ihn. Beide Listen muessen gleich sein -- sonst gilt jeder Bau sofort als
veraltet oder nie (DG-MIT-KNIESTOCK-001: Hilfsmodule fehlten im Abdruck)."""
import ast
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def skripte(datei):
    baum = ast.parse((HERE / datei).read_text(encoding="utf-8"))
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.For) and isinstance(knoten.target, ast.Name) and knoten.target.id == "script":
            if isinstance(knoten.iter, ast.Tuple):
                return [e.value for e in knoten.iter.elts]
    return None


class ToolchainGleich(unittest.TestCase):
    def test_beide_listen_gleich(self):
        self.assertEqual(skripte("run_project.py"), skripte("batch-build.py"))

    def test_hilfsmodule_drin(self):
        for m in ("anderthalb.py", "dachboden.py", "roof_profile.py"):
            self.assertIn(m, skripte("run_project.py"))


if __name__ == "__main__":
    unittest.main()
