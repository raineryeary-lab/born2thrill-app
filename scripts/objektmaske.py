"""Pixelgenaue Maske je Objekt aus einer fertigen .blend.

Wozu: eine maskierte Bearbeitung aendert nur, was innerhalb der Maske liegt.
Position, Drehung und Anzahl koennen sich dabei nicht verschieben, weil
ausserhalb kein Pixel geschrieben wird. Die Maske wird hier GEMESSEN -- sie
ist die Silhouette, die der Renderer selbst erzeugt hat, nicht eine gemalte
Auswahl.

Nebenbei beantwortet derselbe Durchgang die Frage, die `marker_check` bisher
als Selbstauskunft stellen musste: ein Objekt mit null Pixeln im Bild ist
verdeckt, egal was die Szene enthaelt.

Verfahren: KEIN Compositor. Der Object-Index-Pass haengt in Blender 5 an einer
anderen Stelle als in 4, und ein Dateiausgabe-Knoten hat dort kein
`base_path` mehr -- zwei API-Fallen fuer eine Information, die sich einfacher
holen laesst. Stattdessen Workbench mit flacher Beleuchtung und Objektfarbe:
jedes Objekt bekommt eine eindeutige Farbe, das Bild wird danach ausgezaehlt.
Das laeuft in jeder Version und ist in einem Bild fertig.

Aufruf:
    blender --background <datei.blend> --python scripts/objektmaske.py --
            <ausgabeordner>
"""

import json
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
ziel = args[0]
os.makedirs(ziel, exist_ok=True)

szene = bpy.context.scene
objekte = [o for o in szene.objects if o.type == "MESH" and o.visible_get()]

# Optionaler Filter auf Objekt-Staemme (erstes Namenssegment, "-" getrennt),
# fuer Aufrufer, die nur eine kleine Objektgruppe brauchen -- zum Beispiel
# schuetze-garderobe.py, das nur "garderobe" will. Ein Haus mit vielen
# Moebeln hat leicht ueber 250 sichtbare Meshes (twostorey_045's Obergeschoss:
# 301), weit mehr als die Farbkodierung traegt; ungefiltert waere die Maske
# fuer solche Haeuser gar nicht baubar, obwohl die gesuchten paar Objekte
# das Limit nie beruehren. Unveraendertes Verhalten, wenn die Variable fehlt.
_nur_staemme = os.environ.get("OBJEKTMASKE_NUR_STAMM", "").strip()
if _nur_staemme:
    _erlaubt = {s.strip() for s in _nur_staemme.split(",") if s.strip()}
    objekte = [o for o in objekte if o.name.split("-")[0] in _erlaubt]

if len(objekte) > 250:
    raise SystemExit("mehr als 250 sichtbare Meshes -- die Farbkodierung "
                     "traegt nur bis 250")

def nach_linear(wert):
    """sRGB-Zielwert in den linearen Wert umrechnen, den Blender erwartet.

    `obj.color` ist LINEAR, das PNG wird sRGB-kodiert. Ohne Umrechnung kam
    aus dem gewuenschten Wert 28 im Bild eine 94 heraus, und weil die
    sRGB-Kurve unten steil ist, fielen benachbarte Nummern auf denselben
    Ausgabewert: 205 Objekte ergaben nur 157 verschiedene Werte. Genau die
    Sorte stiller Fehler, die eine Maske unbrauchbar macht.
    """
    if wert <= 0.04045:
        return wert / 12.92
    return ((wert + 0.055) / 1.055) ** 2.4


zuordnung = {}
for nummer, obj in enumerate(objekte, start=1):
    # Der Wert wird spaeter aus dem roten Kanal zurueckgelesen. 0 bleibt frei
    # fuer den Hintergrund.
    obj.color = (nach_linear(nummer / 255.0), 0.0, 0.0, 1.0)
    zuordnung[nummer] = obj.name

szene.render.engine = "BLENDER_WORKBENCH"
schattierung = szene.display.shading
schattierung.light = "FLAT"
schattierung.color_type = "OBJECT"
schattierung.show_object_outline = False
schattierung.show_specular_highlight = False
szene.display.render_aa = "OFF"          # keine Kantenglaettung: sonst
                                         # entstehen Mischfarben an den
                                         # Raendern, die zu keinem Objekt
                                         # gehoeren
szene.view_settings.view_transform = "Standard"
szene.view_settings.look = "None"
szene.view_settings.exposure = 0.0
szene.view_settings.gamma = 1.0
szene.render.film_transparent = False
# Workbench nimmt NICHT world.color, sondern seine eigene Hintergrundfarbe.
# Ohne diese Zeile kam der Hintergrund als mittleres Grau heraus, dessen roter
# Kanal zufaellig 28 traf -- und 28 war das Ecksofa. Die Maske "ecksofa-28"
# umfasste daraufhin 39 Prozent des Bildes: alles ausserhalb des Hauses.
schattierung.background_type = "VIEWPORT"
schattierung.background_color = (0.0, 0.0, 0.0)
# Dithering streut den Wert um plus/minus eins und erfindet damit Objekte,
# die es nicht gibt.
szene.render.dither_intensity = 0.0

aus = os.path.join(ziel, "objektindex.png")
szene.render.filepath = aus
szene.render.image_settings.file_format = "PNG"
szene.render.image_settings.color_mode = "RGB"
szene.render.image_settings.color_depth = "8"
bpy.ops.render.render(write_still=True)

json.dump({str(k): v for k, v in zuordnung.items()},
          open(os.path.join(ziel, "objektindex.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("[maske] %d Objekte kodiert -> %s" % (len(objekte), aus))
