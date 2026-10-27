"""Die Ausrichtung eines Moebels messen statt sie zu erfragen.

Rainer, 2026-09-03: "ich kann nicht stundenlang das Zeug drehen und
positionieren und dir sagen dass es falsch ist und du machst es wieder
falsch."

Er hat recht, und die vier Modellsaetze von heute haben es schlimmer gemacht:
viermal so viele Modelle heisst viermal so viele Ausrichtungen, die jemand
von Hand pruefen muesste. Das skaliert nicht.

DAS SIGNAL: die Rueckseite ist die HOHE Seite.

- Ein Bett hat ein Kopfteil; das Fussende ist niedrig.
- Ein Sofa hat eine Lehne; die Sitzflaeche davor ist niedrig.
- Ein Schrank hat keine solche Asymmetrie -- fuer den gilt weiter
  derive_front_axis im Renderer (flachere Seite = Ruecken).

Gemessen wird das Hoehenprofil laengs jeder der vier waagerechten
Richtungen: das Modell in Streifen schneiden, je Streifen die groesste Hoehe
nehmen, und schauen, zu welcher Seite die Hoehe abfaellt. Die hohe Seite ist
hinten, die gegenueberliegende ist vorn.

Pruefung: Rainer hat am 2026-09-03 sechs Modelle von Hand beurteilt. Die
Rechnung wird gegen diese sechs gehalten. Trifft sie sie nicht, taugt sie
nicht -- dann steht es hier und wird nicht benutzt.

Aufruf:
    blender --background --factory-startup --python
            scripts/ausrichtung-messen.py -- <symbol> [<symbol> ...]
"""

import json
import math
import os
import sys

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PICKS = os.path.join(REPO, "data", "symbol-model-picks.json")
VARIANTEN = ("warm", "dark", "scandi", "classic", "modern")

# Was Rainer am 2026-09-03 an der Draufsicht entschieden hat. Die Rechnung
# muss diese sechs treffen, sonst ist sie wertlos.
RAINERS_URTEIL = {
    "cgaxis_3_seat_orange_sofa_blender": 180,
    "Grey Sofa with Pillows": 180,
    "White Sofa 07": 0,
    "Grey Sofa with Wooden Frame": 180,
    "Tall Bed with Shelves (9606)": 180,
    "Grey Bed with Grid Pattern": 0,
}

symbole = sys.argv[sys.argv.index("--") + 1:]


def lade(pfad, divisor):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if pfad.lower().endswith(".blend"):
        with bpy.data.libraries.load(pfad, link=False) as (quelle, ziel):
            ziel.objects = list(quelle.objects)
        for obj in ziel.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
    elif pfad.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=pfad)
    else:
        bpy.ops.import_scene.gltf(filepath=pfad)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    familie = set(meshes)
    for obj in meshes:
        if obj.parent in familie:
            continue
        obj.scale = tuple(c / divisor for c in obj.scale)
    bpy.context.view_layer.update()
    return meshes


def punkte(meshes, hoechstens=40000):
    """Eckpunkte in Weltkoordinaten, ausgeduennt."""
    alle = []
    for obj in meshes:
        m = obj.matrix_world
        ecken = obj.data.vertices
        schritt = max(1, len(ecken) // max(1, hoechstens // max(1, len(meshes))))
        for i in range(0, len(ecken), schritt):
            alle.append(m @ ecken[i].co)
    return alle


def hohe_seite(pkt):
    """In welche waagerechte Richtung die hohe Seite des Moebels liegt.

    Das Moebel wird laengs beider waagerechter Achsen in zehn Streifen
    geteilt; je Streifen zaehlt die groesste Hoehe. Der Vergleich der
    beiden Enden sagt, wo es hoch ist. Die staerkere der beiden Achsen
    gewinnt -- bei einem Bett ist das die Laengsachse (Kopfteil), bei einem
    Sofa die Tiefenachse (Lehne).
    """
    xs = [p.x for p in pkt]
    ys = [p.y for p in pkt]
    zs = [p.z for p in pkt]
    z0 = min(zs)
    ergebnis = {}
    for achse, werte in (("x", xs), ("y", ys)):
        lo, hi = min(werte), max(werte)
        if hi - lo < 1e-6:
            continue
        streifen = [[] for _ in range(10)]
        for p, w in zip(pkt, werte):
            k = min(9, int((w - lo) / (hi - lo) * 10))
            streifen[k].append(p.z - z0)
        hoehen = [max(s) if s else 0.0 for s in streifen]
        vorne = sum(hoehen[:3]) / 3.0      # niedriges Ende
        hinten = sum(hoehen[7:]) / 3.0
        ergebnis[achse] = (hinten - vorne, max(hoehen))
    if not ergebnis:
        return None, 0.0
    achse = max(ergebnis, key=lambda a: abs(ergebnis[a][0]))
    unterschied, hoch = ergebnis[achse]
    if hoch <= 0 or abs(unterschied) / hoch < 0.12:
        return None, abs(unterschied) / max(hoch, 1e-6)
    # Die hohe Seite ist HINTEN, vorne ist die andere.
    if achse == "y":
        front = (0.0, -1.0) if unterschied > 0 else (0.0, 1.0)
    else:
        front = (-1.0, 0.0) if unterschied > 0 else (1.0, 0.0)
    grad = round((math.degrees(math.atan2(-front[0], front[1])) + 360) % 360) % 360
    return grad, abs(unterschied) / hoch


picks = json.load(open(PICKS, encoding="utf-8"))["picks"]
gesehen, treffer, geprueft = set(), 0, 0
for symbol in symbole:
    eintrag = picks.get(symbol) or {}
    for variante in VARIANTEN:
        modell = eintrag.get(variante)
        if not modell or modell["path"] in gesehen or not os.path.exists(modell["path"]):
            continue
        gesehen.add(modell["path"])
        meshes = lade(modell["path"], modell.get("divisor") or 1.0)
        if not meshes:
            continue
        grad, staerke = hohe_seite(punkte(meshes))
        urteil = RAINERS_URTEIL.get(modell["label"])
        marke = ""
        if urteil is not None:
            geprueft += 1
            if grad == urteil:
                treffer += 1
                marke = "  TRIFFT (Rainer: %d)" % urteil
            else:
                marke = "  DANEBEN (Rainer: %d)" % urteil
        print("[messen] %-44s %s  Staerke %.2f%s"
              % (modell["label"][:44],
                 "unklar" if grad is None else "%3d Grad" % grad,
                 staerke, marke))

if geprueft:
    print("[messen] %d von %d gegen Rainers Urteil richtig" % (treffer, geprueft))
