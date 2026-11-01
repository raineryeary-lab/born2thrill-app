"""Generierte Modelle: die gemessene Front muss auf -Y landen.

CODEX-EXPORT-001, Punkt 2. derive_front_axis drehte die gemessene Front auf
+Y. Die Bau-Konvention ist aber Ruecken +Y, Front -Y (MODEL_FACING_DEG: "Back
already +Y"; build_playstation; die Moebeldatei wird beim Planbau gespiegelt).
Folge: kleiderschrank-4/5 (twostorey_053) und -2/-5 (058) standen mit den
Tueren zur Wand.
"""
import ast
import math
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "render-furnished-dollhouse.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "drehung_front_auf_minus_y")
ns = {"math": math}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ns)
drehung = ns["drehung_front_auf_minus_y"]
node2 = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "front_vektor")
exec(compile(ast.Module(body=[node2], type_ignores=[]), str(SOURCE), "exec"), ns)
front_vektor = ns["front_vektor"]


def gedreht(vektor, grad):
    r = math.radians(grad)
    return (round(vektor[0] * math.cos(r) - vektor[1] * math.sin(r), 6),
            round(vektor[0] * math.sin(r) + vektor[1] * math.cos(r), 6))


class FrontAufMinusY(unittest.TestCase):
    def test_every_measured_front_ends_on_minus_y(self):
        for front in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.assertEqual(gedreht(front, drehung(front)), (0.0, -1.0), front)

    def test_front_already_on_minus_y_is_not_turned(self):
        self.assertEqual(drehung((0, -1)), 0)



class FrontStempel(unittest.TestCase):
    """Jedes gestempelte Moebel traegt seine Front in Weltrichtung (fp_front).

    Die Objekt-Drehung in Blender enthaelt die Modell-Korrekturen
    (MODEL_FACING_DEG); die Front des SYMBOLS ist lokal -Y, gedreht um die
    Plan-Drehung.
    """

    def test_rotation_0_faces_minus_y(self):
        self.assertEqual(front_vektor(0), (0.0, -1.0))

    def test_rotation_90_faces_plus_x(self):
        self.assertEqual(front_vektor(90), (1.0, 0.0))

    def test_rotation_180_faces_plus_y(self):
        self.assertEqual(front_vektor(180), (0.0, 1.0))

    def test_rotation_270_faces_minus_x(self):
        self.assertEqual(front_vektor(270), (-1.0, 0.0))


if __name__ == "__main__":
    unittest.main()
