#!/usr/bin/env python3
"""PHASE 1 -- beweisen, dass der Harness nichts angefasst hat.

Vergleicht zwei `invariants.json` Objekt fuer Objekt: Transformationsmatrix,
Abmessungen, Mesh-Fingerabdruck, Sichtbarkeit, Kamera und Render-Einstellungen.
Jede Abweichung ist ein Fehler; das Skript endet dann mit Code 1.

Rainer, 2026-09-02: "Beweisen, dass der Harness nichts verschiebt, dreht,
skaliert, entfernt oder hinzufuegt." Genau das steht hier, und nichts sonst --
gerechnet wird ohne Blender, damit die Pruefung nicht von dem Programm
abhaengt, das sie pruefen soll.

    python verify_invariants.py <vorher.json> <nachher.json> [--toleranz-mm 0.001]

PASS  Code 0, "OK"        -- keine einzige Abweichung
FAIL  Code 1, Liste       -- mit Objektname und Zahl, nicht "irgendwas anders"
"""

import argparse
import json
import sys


def _lade(pfad):
    with open(pfad, encoding="utf-8") as datei:
        return json.load(datei)


def matrix_abweichung_mm(a, b):
    """Groesste Abweichung zweier 4x4-Matrizen, Translation in Millimetern.

    Die ersten drei Spalten sind Rotation und Skalierung (dimensionslos), die
    vierte ist die Verschiebung in Metern. Beides in EINER Zahl auszudruecken
    waere Unsinn, also kommen zwei heraus.
    """
    dreh = 0.0
    verschiebung_mm = 0.0
    for i in range(3):
        for j in range(3):
            dreh = max(dreh, abs(a[i][j] - b[i][j]))
        verschiebung_mm = max(verschiebung_mm, abs(a[i][3] - b[i][3]) * 1000.0)
    return dreh, verschiebung_mm


def vergleiche(vorher, nachher, toleranz_mm=0.001, toleranz_dreh=1e-6):
    """Alle Abweichungen als Liste von Saetzen. Leer heisst bestanden."""
    fehler = []

    for feld in ("aufloesung", "engine", "film_transparent", "frame"):
        a = (vorher.get("szene") or {}).get(feld)
        b = (nachher.get("szene") or {}).get(feld)
        if a != b:
            fehler.append("Szene %s: vorher %r, nachher %r" % (feld, a, b))

    ka, kb = vorher.get("kamera"), nachher.get("kamera")
    if bool(ka) != bool(kb):
        fehler.append("Kamera: vorher %s, nachher %s"
                      % ("vorhanden" if ka else "keine", "vorhanden" if kb else "keine"))
    elif ka:
        dreh, weg = matrix_abweichung_mm(ka["matrix_world"], kb["matrix_world"])
        if weg > toleranz_mm or dreh > toleranz_dreh:
            fehler.append("Kamera bewegt: %.4f mm, Drehung %.2e" % (weg, dreh))
        for feld in ("typ", "lens", "ortho_scale", "shift_x", "shift_y",
                     "clip_start", "clip_end", "sensor_width", "sensor_fit"):
            if ka.get(feld) != kb.get(feld):
                fehler.append("Kamera %s: vorher %r, nachher %r"
                              % (feld, ka.get(feld), kb.get(feld)))

    oa, ob = vorher.get("objekte") or {}, nachher.get("objekte") or {}
    for name in sorted(set(oa) - set(ob)):
        fehler.append("ENTFERNT: %s" % name)
    for name in sorted(set(ob) - set(oa)):
        fehler.append("HINZUGEFUEGT: %s" % name)

    for name in sorted(set(oa) & set(ob)):
        a, b = oa[name], ob[name]
        if a["typ"] != b["typ"]:
            fehler.append("%s: Typ %s -> %s" % (name, a["typ"], b["typ"]))
            continue
        dreh, weg = matrix_abweichung_mm(a["matrix_world"], b["matrix_world"])
        if weg > toleranz_mm:
            fehler.append("%s verschoben um %.4f mm" % (name, weg))
        if dreh > toleranz_dreh:
            fehler.append("%s gedreht oder skaliert (%.2e)" % (name, dreh))
        for i, achse in enumerate("xyz"):
            da = a["dimensionen_mm"][i] - b["dimensionen_mm"][i]
            if abs(da) > toleranz_mm:
                fehler.append("%s Abmessung %s: %.3f -> %.3f mm"
                              % (name, achse, a["dimensionen_mm"][i],
                                 b["dimensionen_mm"][i]))
        if a.get("mesh") != b.get("mesh"):
            fehler.append("%s: Mesh veraendert" % name)
        if a.get("sichtbar_render") != b.get("sichtbar_render"):
            fehler.append("%s: Render-Sichtbarkeit %s -> %s"
                          % (name, a.get("sichtbar_render"), b.get("sichtbar_render")))
        if a.get("parent") != b.get("parent"):
            fehler.append("%s: Parent %r -> %r" % (name, a.get("parent"), b.get("parent")))
        if a.get("materialien") != b.get("materialien"):
            fehler.append("%s: Materialien %r -> %r"
                          % (name, a.get("materialien"), b.get("materialien")))
    return fehler


def main():
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("vorher")
    zerleger.add_argument("nachher")
    zerleger.add_argument("--toleranz-mm", type=float, default=0.001,
                          help="erlaubte Verschiebung in mm (Standard 0,001)")
    args = zerleger.parse_args()

    fehler = vergleiche(_lade(args.vorher), _lade(args.nachher), args.toleranz_mm)
    if not fehler:
        print("OK -- keine Abweichung zwischen %s und %s"
              % (args.vorher, args.nachher))
        return 0
    print("FEHLGESCHLAGEN -- %d Abweichung(en):" % len(fehler))
    for f in fehler[:200]:
        print("  " + f)
    if len(fehler) > 200:
        print("  ... (%d weitere)" % (len(fehler) - 200))
    return 1


if __name__ == "__main__":
    sys.exit(main())
