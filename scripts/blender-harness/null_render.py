#!/usr/bin/env python3
"""PHASE 1 -- der Nullrender: rendern und dabei nichts veraendern.

Oeffnet die .blend, schreibt die Invarianten VOR dem Rendern, rendert mit den
Einstellungen der Datei, schreibt die Invarianten DANACH und speichert die
Szene NICHT. Wer hier etwas verschiebt, faellt in `verify_invariants.py` auf.

Kein Styling, kein Objekttausch, keine Materialaenderung, kein Licht: das ist
der Nullpunkt, gegen den jede spaetere Aenderung gemessen wird. Solange der
Nullrender nicht sauber ist, ist jede Aussage ueber ein spaeteres Bild
wertlos.

Aufruf (Windows):

    "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" ^
        --background "<szene.blend>" ^
        --python null_render.py -- <ausgabeordner> [codex-job.json]

Schreibt in den Ausgabeordner:

    invariants_vorher.json
    null-render.png
    invariants_nachher.json

Nichts davon gehoert in den Lieferordner. Der Ausgabeordner ist bewusst ein
eigener (`renders/harness`), damit ein Zwischenstand gar nicht erst in die
Naehe der Lieferung kommt.
"""

import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
if HIER not in sys.path:
    sys.path.insert(0, HIER)

import export_invariants  # noqa: E402  -- eine Wahrheit, nicht zwei


def main():
    try:
        import bpy
    except ImportError:
        sys.exit("Dieses Skript laeuft nur in Blender:\n"
                 '  blender.exe --background "<szene.blend>" '
                 "--python null_render.py -- <ausgabeordner> [codex-job.json]")
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argumente:
        sys.exit("Ausgabeordner fehlt.")
    ordner = os.path.abspath(argumente[0])
    job_pfad = argumente[1] if len(argumente) > 1 else None
    os.makedirs(ordner, exist_ok=True)

    job = None
    if job_pfad and os.path.exists(job_pfad):
        with open(job_pfad, encoding="utf-8") as datei:
            job = json.load(datei)

    def schreibe(name):
        daten = export_invariants.sammle(bpy)
        if job:
            daten["marker"] = export_invariants.marker_zuordnen(daten, job)
            daten["stueckzahlen"] = export_invariants.stueckzahlen_pruefen(daten, job)
        pfad = os.path.join(ordner, name)
        with open(pfad, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=1, sort_keys=True)
        return pfad

    vorher = schreibe("invariants_vorher.json")
    print("NULL vorher   %s" % vorher)

    ziel = os.path.join(ordner, "null-render.png")
    szene = bpy.context.scene
    # Die Einstellungen der Datei bleiben, wie sie sind -- auch Aufloesung und
    # Engine. Ein Harness, der "nur schnell" etwas umstellt, misst nicht mehr
    # dieselbe Szene.
    szene.render.filepath = ziel
    bpy.ops.render.render(write_still=True)
    print("NULL bild     %s" % ziel)

    nachher = schreibe("invariants_nachher.json")
    print("NULL nachher  %s" % nachher)
    # Ausdruecklich NICHT speichern: die .blend bleibt, wie sie ist.
    print("NULL fertig -- die .blend wurde nicht gespeichert")


if __name__ == "__main__":
    main()
