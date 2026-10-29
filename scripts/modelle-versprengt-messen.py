"""Misst, welche Modelle versprengte Teile mitbringen.

Rainer, 2026-09-03, beim Ausrichtungs-Kontaktbogen: "es sieht so aus als
wuerde ein Kissen weit weg liegen", "Gestell weit verschoben", "Modell ist
gesprengt" -- drei von sechs Modellen.

Das ist mehr als ein Schoenheitsfehler. `import_model` fuegt alle Meshes einer
Datei zu EINEM Objekt zusammen; ein Kissen, das im Quellmodell zehn Meter
neben dem Sofa liegt, reist mit und landet irgendwo im Raum. Ausserdem
verschiebt es den Mittelpunkt: der Renderer setzt das Moebel auf seinen
Marker, aber der Mittelpunkt liegt nicht mehr im Moebel.

Gemessen wird der Abstand jedes Teils vom SCHWERPUNKT der Masse, gewichtet
nach Volumen -- ein grosses Teil zieht den Schwerpunkt, ein Kissen nicht.

Aufruf:
    blender --background --factory-startup --python
            scripts/modelle-versprengt-messen.py -- <symbol> [<symbol> ...]
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
VARIANTEN = ("modern", "classic", "warm", "dark", "scandi")

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


def teil_mass(obj):
    ecken = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    xs = [p.x for p in ecken]
    ys = [p.y for p in ecken]
    zs = [p.z for p in ecken]
    mitte = mathutils.Vector(((min(xs) + max(xs)) / 2,
                              (min(ys) + max(ys)) / 2,
                              (min(zs) + max(zs)) / 2))
    volumen = max((max(xs) - min(xs)), 1e-6) * max((max(ys) - min(ys)), 1e-6) \
        * max((max(zs) - min(zs)), 1e-6)
    return mitte, volumen


picks = json.load(open(PICKS, encoding="utf-8"))["picks"]
gesehen = set()
befunde = []
for symbol in symbole:
    eintrag = picks.get(symbol) or {}
    for variante in VARIANTEN:
        modell = eintrag.get(variante)
        if not modell or modell["path"] in gesehen or not os.path.exists(modell["path"]):
            continue
        gesehen.add(modell["path"])
        meshes = lade(modell["path"], modell.get("divisor") or 1.0)
        if len(meshes) < 2:
            continue
        teile = [teil_mass(o) + (o.name,) for o in meshes]
        gesamt = sum(v for _m, v, _n in teile)
        schwer = mathutils.Vector((0, 0, 0))
        for mitte, vol, _n in teile:
            schwer += mitte * (vol / gesamt)
        # Der Kern ist das groesste Teil; sein Halbmesser ist der Massstab.
        kern = max(teile, key=lambda t: t[1])
        kern_r = kern[1] ** (1.0 / 3.0)
        weit = [(name, (mitte - schwer).length)
                for mitte, _vol, name in teile
                if (mitte - schwer).length > max(kern_r * 1.5, 1.2)]
        if weit:
            befunde.append({
                "modell": modell["label"],
                "pfad": modell["path"],
                "teile": len(meshes),
                "versprengt": [{"teil": n, "abstand_m": round(d, 2)} for n, d in
                               sorted(weit, key=lambda x: -x[1])],
            })
            print("[versprengt] %-44s %d von %d Teilen, bis %.1f m entfernt"
                  % (modell["label"][:44], len(weit), len(meshes),
                     max(d for _n, d in weit)))
        else:
            print("[sauber]     %-44s %d Teile" % (modell["label"][:44], len(meshes)))

json.dump(befunde, open(os.path.join(REPO, "tmp", "modelle-versprengt.json"),
                        "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[messen] %d Modelle mit versprengten Teilen" % len(befunde))
