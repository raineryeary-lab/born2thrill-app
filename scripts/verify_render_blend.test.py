"""R9 misst, WIE VIEL vor dem Treppenaustritt steht -- nicht, ob sich etwas beruehrt.

Rainer, 2026-08-28: `onehalfstorey_020` liess sich nicht mehr bauen. Gemessen
in der Szene:

    Austrittszone von stair-step-15   x 6.12 .. 7.12   y 7.335 .. 8.135
    loch-rail-west                    x 6.10 .. 6.15   y 3.13  .. 7.38

Das Gelaender laeuft LAENGS der Treppe an ihrer Westseite -- das, woran man
sich beim Hochgehen festhaelt. Nur seine letzten 45mm ragen in die Zone, und
quer zur Gehrichtung sind das 30mm einer 1000mm breiten Stufe: 3 %. Die alte
Fassung der Regel fragte nur "beruehrt sich etwas?" und liess das Haus
durchfallen.

Der Fall, fuer den die Regel am 2026-08-23 gebaut wurde, war ein anderer:
auf `onehalfstorey_029` stand `loch-rail-west` QUER ueber dem Austritt, ueber
die volle Breite. Diese Tests halten beide Faelle fest, damit die Lockerung
den urspruenglichen Defekt nicht mit durchlaesst.

`verify_render_blend.py` laeuft sonst in Blender. Fuer die reinen
Rechenfunktionen wird `bpy` durch eine Attrappe ersetzt -- getestet wird
Geometrie, nicht Blender.
"""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module():
    """Das Modul ohne Blender laden.

    Es ruft am Ende `main()` auf, was ohne Szene sofort aussteigt; deshalb
    wird die Datei bis zu diesem Aufruf ausgefuehrt und der Rest verworfen.
    """
    for name in ("bpy", "mathutils"):
        if name not in sys.modules:
            attrappe = types.ModuleType(name)
            if name == "bpy":
                attrappe.data = types.SimpleNamespace(objects=[])
                attrappe.context = types.SimpleNamespace(scene=None)
            sys.modules[name] = attrappe
    quelle = (HERE / "verify_render_blend.py").read_text(encoding="utf-8")
    quelle = quelle.replace("\nmain()", "\n# main() -- im Test nicht aufrufen")
    modul = types.ModuleType("verify_render_blend")
    modul.__file__ = str(HERE / "verify_render_blend.py")
    exec(compile(quelle, str(HERE / "verify_render_blend.py"), "exec"), modul.__dict__)
    return modul


def quad(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


class BlockierteBreite(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        # Die echte Zone von onehalfstorey_020, stair-step-15.
        # Gehrichtung nach Norden, also Querachse = X.
        self.zone = quad(6.12, 7.335, 7.12, 8.135)
        self.nx, self.ny = -1.0, 0.0
        self.breite = 1.00

    def messe(self, hindernis):
        return self.mod._blockierte_breite(self.zone, hindernis, self.nx, self.ny,
                                           self.breite)

    def test_a_side_rail_that_only_grazes_the_zone_is_not_an_obstruction(self):
        """onehalfstorey_020: 30mm einer 1000mm-Stufe, das sind 3 %.

        Genau dieses Gelaender haelt man beim Aussteigen fest.
        """
        anteil = self.messe(quad(6.10, 3.13, 6.15, 7.38))
        self.assertAlmostEqual(anteil, 0.03, places=2)
        self.assertLess(anteil, 0.25)

    def test_a_rail_across_the_exit_is_an_obstruction(self):
        """onehalfstorey_029: quer ueber die volle Breite, 100 %."""
        anteil = self.messe(quad(6.12, 7.35, 7.12, 7.40))
        self.assertGreater(anteil, 0.9)

    def test_half_the_width_still_fails(self):
        """Auch eine halbe Sperre ist eine Sperre.

        Die Grenze liegt bei 25 %, nicht bei "fast alles" -- sonst waere eine
        Absperrung ueber die halbe Stufe erlaubt.
        """
        self.assertGreater(self.messe(quad(6.12, 7.35, 6.62, 7.40)), 0.25)

    def test_something_outside_the_zone_blocks_nothing(self):
        self.assertEqual(self.messe(quad(3.00, 1.00, 4.00, 2.00)), 0.0)

    def test_a_rail_that_stops_short_of_the_zone_blocks_nothing(self):
        """Endet das Gelaender vor der Zone, ist nichts zu messen."""
        self.assertEqual(self.messe(quad(6.10, 3.13, 6.15, 7.20)), 0.0)


class ClipVerhalten(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_the_clip_of_two_disjoint_shapes_is_empty(self):
        self.assertEqual(len(self.mod._convex_clip(quad(0, 0, 1, 1), quad(5, 5, 6, 6))), 0)

    def test_the_clip_keeps_the_shared_rectangle(self):
        stueck = self.mod._convex_clip(quad(0, 0, 2, 2), quad(1, 1, 3, 3))
        xs = [p[0] for p in stueck]
        ys = [p[1] for p in stueck]
        self.assertAlmostEqual(min(xs), 1.0)
        self.assertAlmostEqual(max(xs), 2.0)
        self.assertAlmostEqual(min(ys), 1.0)
        self.assertAlmostEqual(max(ys), 2.0)

    def test_the_old_area_helper_still_agrees_with_the_clip(self):
        """`_convex_overlap_area` traegt Regel c (Stufenueberlappung).

        Sie bleibt unveraendert in Gebrauch, also muss sie zum neuen
        Clipping passen.
        """
        flaeche = self.mod._convex_overlap_area(quad(0, 0, 2, 2), quad(1, 1, 3, 3))
        self.assertAlmostEqual(flaeche, 1.0, places=6)




class ProzedualGebautesTraegtAuchSeinenStempel(unittest.TestCase):
    """R0 darf ein Moebel nicht am Symbol eines anderen messen.

    Rainer, 2026-08-30, an `bungalow_001`:

        Verifier R0_symbol_sizes: kleiderschrank-10:
        footprint 1400x800 vs symbol 3000x700

    Im gebauten Blend nachgemessen -- nicht geraten:

        kleiderschrank-10   Cube.126    1400x800x2100   Stempel: KEINER
        kleiderschrank-19   Mesh.039    3000x700x2100   Stempel: 3000x700

    Instanz 10 ist ein prozedural gebauter Kasten. Der Bauweg
    (`build_box` und Geschwister) setzt `symbol_w_mm` nicht -- den setzt nur
    der Prototyp-Weg. `check_symbol_sizes()` faellt ohne Stempel auf
    `wanted[asset_id]` zurueck, und dort steht die ZULETZT gesehene
    Platzierung desselben Assets: 3000x700.

    Das ist genau der Fehler, den der Stempel 2026-08-22 beheben sollte
    (onehalfstorey_029) -- er wurde nur auf einem der beiden Wege eingebaut.

    Rainer dazu: "kleiderschränke gibt es nicht in EINEM maß, die möbel sind
    nur symbole die einen bestimmten bereich verdecken können." Genau deshalb
    muss jede Instanz an IHRER eigenen Groesse gemessen werden.
    """

    def test_der_bauweg_stempelt(self):
        quelle = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
        zweig = quelle[quelle.index('elif kind == "box":'):]
        zweig = zweig[:zweig.index("if not item.get(\"mesh_path\")")]
        self.assertIn("symbol_w_mm", zweig)
        self.assertIn("symbol_d_mm", zweig)

    def test_der_prototypweg_stempelt_weiterhin(self):
        quelle = (HERE / "render-furnished-dollhouse.py").read_text(encoding="utf-8")
        self.assertIn('instance["symbol_w_mm"]', quelle)

    def test_ohne_stempel_misst_der_verifier_am_falschen(self):
        """Die Rueckfallzeile ist der Grund -- sie bleibt, aber sie darf nicht
        mehr greifen, wo ein Stempel haette stehen koennen."""
        quelle = (HERE / "verify_render_blend.py").read_text(encoding="utf-8")
        self.assertIn('body.get("symbol_w_mm")', quelle)


if __name__ == "__main__":
    unittest.main(verbosity=2)
