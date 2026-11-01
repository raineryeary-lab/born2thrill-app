"""BAU-SCHNELLER-001 Runde 2: ein gescheiterter Zusatz-Pass beendet den Render.

Codex, 2026-10-28: scheiterte der ID-Masken-Pass, druckte
render-furnished-dollhouse.py nur "id mask FAILED", liess Masken-Material und
schwarze Welt in der Szene -- und speicherte sie trotzdem als .blend, die dann
zertifiziert wurde. Mit drei Blender-Prozessen gleichzeitig wird ein voller
GPU-Speicher wahrscheinlicher.

Echter Blender-Lauf (je ~1 min), darum eigene Datei. Braucht einen fertig
gebauten Plan; Vorgabe bungalow_037 (PASS_FEHLER_PLAN ueberschreibt).
"""
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", r"E:\born2thrill-local-workbench-data")
PLAN = os.environ.get("PASS_FEHLER_PLAN") or os.path.join(
    DATA, "corrections", "bungalow_037", "renders", "go-baseline", "plan-modern.json")


def render(ordner, **env):
    png = os.path.join(ordner, "interior-test-baseline.png")
    blend = os.path.join(ordner, "interior-test-baseline.blend")
    umgebung = dict(os.environ, DMH_SAVE_BLEND=blend, DMH_FINISH="modern-a", DMH_FLOOR="0", **env)
    # Wie run_project.py: ein Python-Fehler ist ein Fehler.
    lauf = subprocess.run([BLENDER, "--background", "--python-exit-code", "1", "--python",
                           os.path.join(HERE, "render-furnished-dollhouse.py"), "--", PLAN, png],
                          capture_output=True, text=True, env=umgebung, timeout=900)
    return lauf.returncode, lauf.stdout + lauf.stderr, blend


@unittest.skipUnless(os.path.exists(BLENDER) and os.path.exists(PLAN), "Blender oder Plan fehlt")
class PassFehlerBeendetDenRender(unittest.TestCase):
    def test_id_maske_scheitert_nichts_wird_gespeichert(self):
        with tempfile.TemporaryDirectory() as ordner:
            code, aus, blend = render(ordner, DMH_TESTFEHLER="idmask")
            self.assertNotEqual(code, 0, aus[-2000:])
            self.assertIn("FEHLER id mask", aus)
            self.assertFalse(os.path.exists(blend), "gescheiterte Szene wurde gespeichert")

    def test_tiefen_pass_scheitert_nichts_wird_gespeichert(self):
        with tempfile.TemporaryDirectory() as ordner:
            code, aus, blend = render(ordner, DMH_TESTFEHLER="depth")
            self.assertNotEqual(code, 0, aus[-2000:])
            self.assertFalse(os.path.exists(blend), "gescheiterte Szene wurde gespeichert")

    def test_ohne_fehler_wird_gespeichert(self):
        with tempfile.TemporaryDirectory() as ordner:
            code, aus, blend = render(ordner)
            self.assertEqual(code, 0, aus[-2000:])
            self.assertTrue(os.path.exists(blend))
            self.assertIn("Meshes getauscht und wiederhergestellt", aus)


if __name__ == "__main__":
    unittest.main()
