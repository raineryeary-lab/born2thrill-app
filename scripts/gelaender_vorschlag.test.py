"""Treppenloch-Gelaender: der Austritt bleibt immer offen (gelaender-nur-gezeichnet-v1).

Rainer, 2026-11-07: "dont let me place a railing so that it doesnt interrupt
the stairs at the top". Gemessen: deckenloch_auto_kanten liess die
Austrittskante nur offen, wenn sie <= 150 mm vor dem Treppenende lag.
"""
import ast
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lade():
    src = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
    nodes = [n for n in ast.parse(src).body
             if isinstance(n, ast.FunctionDef) and n.name == "deckenloch_auto_kanten"]
    ns = {"math": math}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "x", "exec"), ns)
    return ns["deckenloch_auto_kanten"]


class Austritt(unittest.TestCase):
    def test_loch_400mm_ueber_das_treppenende_hinaus(self):
        auto = lade()
        hole = [[2000.0, 1000.0], [4000.0, 1000.0], [4000.0, 4400.0], [2000.0, 4400.0]]
        # Treppe kommt bei y = 4000 an, das Loch reicht bis 4400.
        self.assertEqual(sorted(auto(hole, ((2100.0, 4000.0), (3000.0, 4000.0)))), [0, 1, 3])

    def test_nur_parallele_kante_ist_austritt(self):
        auto = lade()
        hole = [[2000.0, 1000.0], [4000.0, 1000.0], [4000.0, 4000.0], [2000.0, 4000.0]]
        # Austritt quer zur x-Richtung bei x = 3900: Kante 1 (x = 4000) ist es.
        self.assertEqual(sorted(auto(hole, ((3900.0, 2000.0), (3900.0, 3000.0)))), [0, 2, 3])


if __name__ == "__main__":
    unittest.main()
