"""Kontaktbogen zur Ausrichtung: jedes Modell von OBEN, mit Nordpfeil.

Warum von oben und nicht aus der Dollhouse-Perspektive
------------------------------------------------------
Im Renderer steht bei ROTATION_OVERRIDE die Warnung "Never eyeball chair
facing from a perspective render -- sheet only", und Rainer hat sie zweimal
ausgesprochen. Am 2026-08-25 wurde die Sitzrichtung eines Schalensessels aus
einer Isometrie abgelesen und war falsch. Eine Draufsicht ohne Perspektive
laesst sich dagegen eindeutig lesen.

Was der Bogen zeigt
-------------------
Je Modell ein Bild von senkrecht oben, das Modell ungedreht in seiner eigenen
lokalen Lage. Der Pfeil zeigt nach +y, also dorthin, wohin der Renderer die
Vorderseite VERMUTET. Steht das Moebel anders herum, ist der noetige Wert
abzulesen: Vorderseite nach oben = 0, nach links = 90, nach unten = 180,
nach rechts = 270. Der Wert gehoert nach MODEL_ORIENT_BY_LABEL.

Aufruf
------
    blender --background --python scripts/ausrichtungs-kontaktbogen.py --
            <symbol> [<symbol> ...] <ausgabeordner>
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
VARIANTEN = ("warm", "dark", "scandi", "classic")

args = sys.argv[sys.argv.index("--") + 1:]
symbole, ziel = args[:-1], args[-1]
os.makedirs(ziel, exist_ok=True)


def leere_szene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    szene = bpy.context.scene
    szene.render.engine = os.environ.get("BOGEN_ENGINE", "BLENDER_EEVEE")
    szene.render.resolution_x = 520
    szene.render.resolution_y = 520
    szene.render.film_transparent = False
    welt = bpy.data.worlds.new("bogen")
    welt.use_nodes = True
    # Mittelgrauer Grund, nicht weiss: ein weisses Ledersofa und ein weisses
    # Bett waren auf hellem Grund praktisch unsichtbar, und ein Bogen, auf dem
    # man nichts sieht, ist keine Entscheidungsgrundlage.
    welt.node_tree.nodes["Background"].inputs[0].default_value = (0.28, 0.30, 0.33, 1)
    welt.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    szene.world = welt
    return szene


def lade(pfad, divisor):
    vorher = set(bpy.data.objects.keys())
    if pfad.lower().endswith(".blend"):
        with bpy.data.libraries.load(pfad, link=False) as (quelle, ziel_lib):
            ziel_lib.objects = list(quelle.objects)
        for obj in ziel_lib.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
    elif pfad.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=pfad)
    else:
        bpy.ops.import_scene.gltf(filepath=pfad)
    bpy.context.view_layer.update()
    neu = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - vorher
           if bpy.data.objects[n].type == "MESH"]
    if not neu:
        return None
    # Nur die WURZELN skalieren, und MULTIPLIZIEREN statt ueberschreiben.
    #
    # Der erste Entwurf setzte `obj.scale = 1/divisor` auf jedes Objekt. Das
    # warf die Eigenskalierung des Modells weg und skalierte Kinder doppelt.
    # Gemessen am 2026-09-03: "White Leather Bed" kam mit einer Spanne von
    # 687 m heraus, "Wooden Bed with Black-Orange Bedclothes" mit 858 m --
    # das Bett war ein Subpixel-Punkt, und die Zelle sah leer aus. Vorher
    # hatte ich Kamerahoehe und Sichtbarkeit verdaechtigt; beides war falsch.
    familie = set(neu)
    for obj in neu:
        obj.hide_render = False
        obj.hide_viewport = False
        if obj.parent in familie:
            continue                   # das Elternteil bringt die Skalierung mit
        obj.scale = tuple(c / divisor for c in obj.scale)
    bpy.context.view_layer.update()
    return neu


def rahmen(objekte):
    """Groesster waagerechter Halbmesser, fuer die Kamera."""
    punkte = []
    for obj in objekte:
        for ecke in obj.bound_box:
            welt = obj.matrix_world @ mathutils.Vector(ecke)
            punkte.append(welt)
    if not punkte:
        return 1.0, (0.0, 0.0)
    xs = [p.x for p in punkte]
    ys = [p.y for p in punkte]
    zs = [p.z for p in punkte]
    mitte = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    return max(max(xs) - min(xs), max(ys) - min(ys)), mitte, max(zs)


def nordpfeil(mitte, oberkante, spanne):
    """Ein flacher, selbstleuchtender Pfeil nach +y -- die Richtung, die der
    Renderer als Vorderseite VERMUTET. Ohne ihn ist die Kamera-Draufsicht nur
    ein Foto des Modells, keine Aussage darueber, wohin 0 Grad zeigt (Rainer,
    2026-09-04: "there are no arrows how can i say anything about
    orientation"). Selbstleuchtend, damit er unter jeder Beleuchtung sichtbar
    bleibt, nicht nur wenn die Sonne guenstig steht."""
    laenge = max(spanne * 0.45, 0.3)
    breite = laenge * 0.18
    kopf = laenge * 0.32
    z = oberkante + spanne * 0.01
    cx, cy = mitte
    verts = [
        (cx - breite / 2, cy, z), (cx + breite / 2, cy, z),
        (cx + breite / 2, cy + laenge - kopf, z),
        (cx + breite * 1.6, cy + laenge - kopf, z),
        (cx, cy + laenge, z),
        (cx - breite * 1.6, cy + laenge - kopf, z),
        (cx - breite / 2, cy + laenge - kopf, z),
    ]
    faces = [tuple(range(len(verts)))]
    mesh = bpy.data.meshes.new("nordpfeil")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("nordpfeil", mesh)
    bpy.context.scene.collection.objects.link(obj)
    material = bpy.data.materials.new("nordpfeil-material")
    material.use_nodes = True
    emission = material.node_tree.nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (1.0, 0.35, 0.0, 1.0)
    emission.inputs["Strength"].default_value = 2.0
    material.node_tree.links.new(
        emission.outputs["Emission"],
        material.node_tree.nodes["Material Output"].inputs["Surface"])
    obj.data.materials.append(material)
    return obj


picks = json.load(open(PICKS, encoding="utf-8"))["picks"]
geschrieben = []
for symbol in symbole:
    eintrag = picks.get(symbol) or {}
    for variante in VARIANTEN:
        modell = eintrag.get(variante)
        if not modell or not os.path.exists(modell["path"]):
            print("[bogen] fehlt        %s / %s" % (symbol, variante))
            continue
        leere_szene()
        objekte = lade(modell["path"], modell.get("divisor") or 1.0)
        if not objekte:
            print("[bogen] leer         %s / %s" % (symbol, variante))
            continue
        spanne, mitte, oberkante = rahmen(objekte)
        print("[bogen] mass         %s / %-8s %d Meshes, Spanne %.2f m, Mitte %.2f/%.2f, oben %.2f"
              % (symbol, variante, len(objekte), spanne, mitte[0], mitte[1], oberkante))
        spanne = max(spanne, 0.5)

        kamera_daten = bpy.data.cameras.new("oben")
        kamera_daten.type = "ORTHO"
        kamera_daten.ortho_scale = spanne * 1.35
        kamera = bpy.data.objects.new("oben", kamera_daten)
        # UEBER dem Modell, nicht auf einer festen Hoehe. Zwei Betten kamen
        # leer heraus, weil ihre Geometrie hoch ueber null liegt und die
        # Kamera daran vorbeisah.
        kamera.location = (mitte[0], mitte[1], oberkante + spanne * 3)
        kamera.rotation_euler = (0.0, 0.0, 0.0)
        bpy.context.scene.collection.objects.link(kamera)
        bpy.context.scene.camera = kamera

        licht_daten = bpy.data.lights.new("sonne", type="SUN")
        licht_daten.energy = 3.0
        licht = bpy.data.objects.new("sonne", licht_daten)
        licht.rotation_euler = (math.radians(35), 0.0, math.radians(35))
        bpy.context.scene.collection.objects.link(licht)

        nordpfeil(mitte, oberkante, spanne)

        aus = os.path.join(ziel, "%s__%s.png" % (symbol, variante))
        bpy.context.scene.render.filepath = aus
        bpy.ops.render.render(write_still=True)
        geschrieben.append((symbol, variante, modell["label"], aus))
        print("[bogen] gerendert    %s / %-8s %s" % (symbol, variante, modell["label"]))

print("[bogen] fertig %d Bilder" % len(geschrieben))
json.dump([{"symbol": s, "variante": v, "label": l, "bild": b}
           for s, v, l, b in geschrieben],
          open(os.path.join(ziel, "bogen.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
