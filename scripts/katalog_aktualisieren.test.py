"""katalog-automatisch-v1 (Rainer, 2026-11-07: "this has to go automatically")."""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("katalog_aktualisieren", os.path.join(HERE, "katalog-aktualisieren.py"))
ka = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ka)


class KatalogAktualisieren(unittest.TestCase):
    def test_snippet_code_ohne_php_marke(self):
        self.assertEqual(ka.snippet_code("<?php\n/** x */\nadd_action();\n"), "/** x */\nadd_action();")
        self.assertEqual(ka.snippet_code("/** x */\r\nadd_action();"), "/** x */\nadd_action();")

    def test_zeitstempel_ist_keine_aenderung(self):
        self.assertEqual(ka.ohne_stand("Stand 2026-11-07 16:30: 270"), ka.ohne_stand("Stand 2026-11-07 19:21: 270"))
        self.assertNotEqual(ka.ohne_stand("Stand 2026-11-07 16:30: 270"), ka.ohne_stand("Stand 2026-11-07 19:21: 271"))

    def test_nur_fehlende_und_nie_cubicasa(self):
        self.assertEqual(ka.fehlende_plaene(["a", "b", "cubicasa_review_1"], {"a"}), ["b"])

    def test_nie_freigabe_oder_mail(self):
        quelle = open(os.path.join(HERE, "katalog-aktualisieren.py"), encoding="utf-8").read()
        for verboten in ("/freigabe", "release(", '"send"', "approved\":"):
            self.assertNotIn(verboten, quelle)


if __name__ == "__main__":
    unittest.main()
