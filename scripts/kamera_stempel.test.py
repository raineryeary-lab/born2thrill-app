"""Upper-floor camera: the stamp must describe the camera as SAVED.

Plan: plans/kamera-obergeschoss-stempel-v1.md. twostorey_059, 2026-10-20:
camera z 48.60 (stamp) -> 51.22 (file, 11:31) -> 53.84 (file, 11:54). The
stamp was written before the storey was lifted by 2.62 m, so every rebuilt
upper floor looked "moved by hand", was rescued and lifted once more.

render-furnished-dollhouse.py imports bpy; the pure functions come out of
the real file via ast.
"""

import ast
import json
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "render-furnished-dollhouse.py"
LIFT = 2.62


def load():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    names = ("kamera_von_hand", "kamera_vor_anhebung")
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    missing = set(names) - {n.name for n in nodes}
    if missing:
        raise AssertionError(f"missing {sorted(missing)}")
    ns = {"math": math, "json": json}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), ns)
    return ns


def kamera(loc, stempel_loc=None, rot=(33.403, 0.0, 45.0)):
    alt = {"loc": list(loc), "rot_deg": list(rot), "lens": 82.0, "typ": "PERSP"}
    alt["stempel"] = (json.dumps({"loc": list(stempel_loc), "rot_deg": list(rot)})
                      if stempel_loc is not None else None)
    return alt


class KameraStempel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load()

    def test_gebaute_kamera_ist_nicht_von_hand(self):
        # stamp written after the lift: file and stamp agree
        alt = kamera((24.9708, -14.1046, 51.2239), (24.9708, -14.1046, 51.2239))
        self.assertFalse(self.ns["kamera_von_hand"](alt, None, LIFT))

    def test_verschobene_kamera_ist_von_hand(self):
        alt = kamera((25.9708, -14.1046, 51.2239), (24.9708, -14.1046, 51.2239))
        self.assertTrue(self.ns["kamera_von_hand"](alt, None, LIFT))

    def test_alte_datei_ohne_stempel_auf_regelposition_plus_anhebung(self):
        regel = (24.9708, -14.1046, 48.6039)            # before the lift
        alt = kamera((24.9708, -14.1046, 48.6039 + LIFT))
        self.assertFalse(self.ns["kamera_von_hand"](alt, regel, LIFT))
        alt = kamera((20.0, -14.1046, 48.6039 + LIFT))
        self.assertTrue(self.ns["kamera_von_hand"](alt, regel, LIFT))

    def test_handkamera_bleibt_wo_sie_war(self):
        # saved (world) -> applied before the lift -> lifted: same place
        gespeichert = [24.9708, -14.1046, 51.2239]
        vorher = self.ns["kamera_vor_anhebung"](gespeichert, LIFT)
        nachher = [vorher[0], vorher[1], vorher[2] + LIFT]
        for a, b in zip(nachher, gespeichert):
            self.assertAlmostEqual(a, b, places=9)

    def test_erdgeschoss_unveraendert(self):
        self.assertEqual(self.ns["kamera_vor_anhebung"]([1.0, 2.0, 3.0], 0.0), [1.0, 2.0, 3.0])

    def test_stempel_kommt_nach_der_anhebung(self):
        text = SOURCE.read_text(encoding="utf-8")
        stempel = text.index('camera["zf_kamera"] = json.dumps(')
        anhebung = text.index("_obj.location.z += storey_base_z")
        self.assertGreater(stempel, anhebung,
                           "the stamp must record the camera after the storey lift")


if __name__ == "__main__":
    unittest.main()
