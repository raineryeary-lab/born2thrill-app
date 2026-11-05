"""3D-Vorschau (vorschau-3d-v1): Dachwahl und der Ausstieg vor dem Render."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("vorschau_3d", os.path.join(HERE, "vorschau-3d.py"))
vorschau = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vorschau)


class DachWahl(unittest.TestCase):
    def test_gewuenschtes_dach_wenn_vorhanden(self):
        self.assertEqual(vorschau.dach_waehlen("walmdach", ["flachdach", "walmdach"]), "walmdach")

    def test_sonst_das_erste_des_hauses(self):
        # Ein 1,5-Geschosser hat kein Flachdach -- nicht bauen, was es nicht gibt.
        self.assertEqual(vorschau.dach_waehlen("flachdach", ["satteldach", "satteldach-kubus"]),
                         "satteldach")
        self.assertEqual(vorschau.dach_waehlen("", ["flachdach"]), "flachdach")
        self.assertIsNone(vorschau.dach_waehlen("walmdach", []))


class AusstiegVorDemRender(unittest.TestCase):
    """Die GLB-Weiche muss VOR dem ersten Render stehen und danach aufhoeren."""

    def test_weiche_vor_render_und_ohne_dateien(self):
        quelle = open(os.path.join(HERE, "render-exterior.py"), encoding="utf-8").read()
        weiche = quelle.index('if os.environ.get("EXT_GLTF_OUT"):')
        self.assertLess(weiche, quelle.index("bpy.ops.render.render("))
        self.assertLess(weiche, quelle.index("bpy.ops.wm.save_as_mainfile("))
        block = quelle[weiche:quelle.index("for engine in", weiche)]
        self.assertIn("sys.exit(0)", block)
        self.assertIn("export_cameras=False", block)
        # Versteckte Asset-Vorlagen gehoeren nicht in die Vorschau (onehalfstorey_021).
        self.assertIn("use_visible=True", block)


if __name__ == "__main__":
    unittest.main()
