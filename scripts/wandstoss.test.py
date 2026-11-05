"""Wandstoesse an der Fassade (CODEX-EXPORT-001 F1-F3).

twostorey_053/058: Innenwaende endeten auf der Aussenkante und standen mit +10
mm (gerendertes Geschoss) bzw. +60 mm (EG-Sockel) aus der Fassade -- senkrechte
Striche und Rippen auf dem Putz. Zwischen Innenwaenden bleibt +10 (gegen
koplanare Flaechen), an der Fassade nicht.
"""
import ast
import math
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "render-furnished-dollhouse.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_end_extension_mm")
ns = {"math": math}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ns)
ext = ns["_end_extension_mm"]

AUSSEN_A = {"start_mm": [0, 0], "end_mm": [10000, 0], "thickness_mm": 240, "wall_type": "exterior"}
AUSSEN_B = {"start_mm": [0, 0], "end_mm": [0, 8000], "thickness_mm": 240, "wall_type": "exterior"}


def innen(a, b, t=115):
    return {"start_mm": list(a), "end_mm": list(b), "thickness_mm": t, "wall_type": "interior"}


class Wandstoss(unittest.TestCase):
    def test_inner_wall_ending_on_the_outer_face_is_pulled_back_inside(self):
        w = innen((5000, 3000), (5000, -120))
        self.assertAlmostEqual(ext(w["end_mm"], (0, -1), w, [AUSSEN_A, w]), -10.0)

    def test_inner_wall_ending_on_the_inner_face_reaches_10mm_short_of_the_facade(self):
        w = innen((5000, 3000), (5000, 120))
        self.assertAlmostEqual(ext(w["end_mm"], (0, -1), w, [AUSSEN_A, w]), 230.0)

    def test_exterior_corner_is_exactly_flush(self):
        self.assertAlmostEqual(ext(AUSSEN_A["start_mm"], (-1, 0), AUSSEN_A, [AUSSEN_A, AUSSEN_B]), 120.0)

    def test_inner_to_inner_keeps_the_10mm_overshoot(self):
        d = innen((3000, 5000), (7000, 5000))
        c = innen((5000, 3000), (5000, 5000))
        self.assertAlmostEqual(ext(c["end_mm"], (0, 1), c, [c, d]), 57.5 + 10)


if __name__ == "__main__":
    unittest.main()
