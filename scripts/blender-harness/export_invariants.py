#!/usr/bin/env python3
"""PHASE 0 -- die Wahrheit aus der .blend, maschinenlesbar.

Rainer, 2026-09-02: der Weg ueber das Bildmodell ist aufgehoben. Moebel
werden deterministisch in Blender gestaltet oder durch CGAxis-Modelle
ersetzt; Architektur, Kamera und Schnittebene bleiben unveraendert, und
Mittelpunkt, Fussabdruck, Ausrichtung und Anzahl jedes Ausgangsobjekts sind
verbindlich.

Verbindlich heisst: nachpruefbar. Dieses Skript schreibt auf, was in der
Datei steht, BEVOR irgendjemand sie anfasst -- jede Transformationsmatrix,
jede Abmessung, jeden Mesh-Fingerabdruck, die Kamera und die
Render-Sichtbarkeit. `verify_invariants.py` vergleicht spaeter dagegen.

Ohne diese Datei ist "das Moebel steht noch richtig" eine Meinung. Am
2026-09-01 hat genau das vier Runden gekostet.

Aufruf (Windows):

    "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" ^
        --background "<szene.blend>" ^
        --python export_invariants.py -- <ziel.json> [codex-job.json]

Ohne Blender laeuft nichts: das Skript liest `bpy`. Liegt `codex-job.json`
daneben, werden zusaetzlich die 43 Marker ihren Objekten zugeordnet und die
Stueckzahlen geprueft.
"""

import hashlib
import json
import os
import sys

# Objektstaemme, die zur Gebaeudehuelle gehoeren. Deckungsgleich mit
# KEIN_MOEBEL in make-codex-job.py -- dieselbe Grenze, damit Auftrag und
# Harness dasselbe "Moebel" meinen.
ARCHITEKTUR = ("wall", "floor", "roof", "cut", "ground", "proto", "sockel",
               "ceiling", "loch", "window", "door", "stair", "coping",
               "foundation", "site", "raumlicht")


def ist_architektur(name):
    """Traegt dieses Objekt die Gebaeudehuelle?

    Tuerblaetter heissen `wall-<n>-door` und sind damit ueber `wall` schon
    erfasst. Ein Moebel, das faelschlich hier landet, waere schlimmer als
    umgekehrt: es duerfte dann unbemerkt veraendert werden.
    """
    n = (name or "").lower()
    return any(n.startswith(a) or ("-%s" % a) in n for a in ARCHITEKTUR)


def _matrix(m):
    return [[round(v, 6) for v in zeile] for zeile in m]


def _mesh_fingerabdruck(objekt):
    """Ein Hash ueber Ecken und Flaechen -- veraenderte Geometrie faellt auf.

    Gerundet auf Mikrometer: Blender rechnet in float, und ein Speichern
    allein darf nicht schon eine Abweichung erzeugen.
    """
    daten = getattr(objekt, "data", None)
    if daten is None or not hasattr(daten, "vertices"):
        return None
    h = hashlib.sha256()
    h.update(b"v")
    for v in daten.vertices:
        h.update(("%.6f,%.6f,%.6f;" % (v.co.x, v.co.y, v.co.z)).encode())
    h.update(b"p")
    for p in daten.polygons:
        h.update((",".join(str(i) for i in p.vertices) + ";").encode())
    return h.hexdigest()


def sammle(bpy):
    """Alles, was ein spaeterer Lauf nicht veraendert haben darf."""
    szene = bpy.context.scene
    kamera = szene.camera
    quelldatei = bpy.data.filepath
    datei_hash = None
    if quelldatei and os.path.isfile(quelldatei):
        h = hashlib.sha256()
        with open(quelldatei, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        datei_hash = h.hexdigest()
    raus = {
        "schema": "zf-scene-snapshot-v1",
        "blender": bpy.app.version_string,
        "datei": quelldatei,
        "source_blend_sha256": datei_hash,
        "szene": {
            "name": szene.name,
            "aufloesung": [szene.render.resolution_x, szene.render.resolution_y,
                           szene.render.resolution_percentage],
            "engine": szene.render.engine,
            "film_transparent": bool(szene.render.film_transparent),
            "frame": szene.frame_current,
            # Der Nullrender vom 2026-09-02 war deutlich heller als der
            # gelieferte Baseline-Render (mittlere Helligkeit 183 gegen 165),
            # bei identischer Geometrie. Ursache: der Depth-Pass in
            # render-furnished-dollhouse.py setzt view_transform auf
            # "Standard", exposure auf 0 und die Samples auf 8 -- und stellt
            # das vor DMH_SAVE_BLEND nicht zurueck. Die gelieferte .blend
            # traegt damit die Einstellungen des DEPTH-Passes. Ohne diese
            # Felder faellt das keinem Vergleich auf.
            "view_transform": getattr(szene.view_settings, "view_transform", None),
            "look": getattr(szene.view_settings, "look", None),
            "exposure": round(getattr(szene.view_settings, "exposure", 0.0), 6),
            "gamma": round(getattr(szene.view_settings, "gamma", 1.0), 6),
            "samples": getattr(getattr(szene, "eevee", None), "taa_render_samples", None),
        },
        "kamera": None,
        "objekte": {},
    }
    if kamera is not None:
        d = kamera.data
        raus["kamera"] = {
            "name": kamera.name,
            "matrix_world": _matrix(kamera.matrix_world),
            "typ": d.type,
            "lens": round(getattr(d, "lens", 0.0), 6),
            "ortho_scale": round(getattr(d, "ortho_scale", 0.0), 6),
            "shift_x": round(d.shift_x, 6),
            "shift_y": round(d.shift_y, 6),
            "clip_start": round(d.clip_start, 6),
            "clip_end": round(d.clip_end, 6),
            "sensor_width": round(getattr(d, "sensor_width", 0.0), 6),
            "sensor_fit": getattr(d, "sensor_fit", ""),
        }
    for o in sorted(bpy.data.objects, key=lambda x: x.name):
        eintrag = {
            "typ": o.type,
            "matrix_world": _matrix(o.matrix_world),
            "dimensionen_mm": [round(v * 1000.0, 3) for v in o.dimensions],
            "sichtbar_render": not o.hide_render,
            "sichtbar_viewport": not o.hide_viewport,
            "parent": o.parent.name if o.parent else None,
            "architektur": ist_architektur(o.name),
            "materialien": [s.material.name for s in o.material_slots if s.material],
        }
        if o.type == "MESH":
            eintrag["mesh"] = _mesh_fingerabdruck(o)
            eintrag["ecken"] = len(o.data.vertices)
            eintrag["flaechen"] = len(o.data.polygons)
        raus["objekte"][o.name] = eintrag
    raus["summary"] = {
        "object_count": len(raus["objekte"]),
        "mesh_count": sum(1 for item in raus["objekte"].values()
                          if item["typ"] == "MESH"),
        "architecture_mesh_count": sum(1 for item in raus["objekte"].values()
                                       if item["typ"] == "MESH" and item["architektur"]),
        "furniture_mesh_count": sum(1 for item in raus["objekte"].values()
                                    if item["typ"] == "MESH" and not item["architektur"]),
        "opening_objects": sorted(name for name in raus["objekte"]
                                  if "door" in name.lower() or "window" in name.lower()),
    }
    return raus


def marker_zuordnen(invarianten, job):
    """Die Marker des Auftrags auf die Blender-Objekte abbilden.

    Der Markername IST der Objektname (`_marker_liste` benutzt `_bauteil`),
    also ist die Zuordnung exakt und nicht geraten. Was nicht zugeordnet
    werden kann, wird gemeldet statt stillschweigend weggelassen.
    """
    karten = job.get("object_map") or []
    karten = karten if isinstance(karten, list) else [karten]
    marker = [m for k in karten for m in (k.get("markers") or [])]
    # Ein Marker steht fuer ein MOEBELSTUECK, nicht fuer ein Netz. Am
    # 2026-09-02 kamen fuenf Marker als "fehlt in der .blend" heraus --
    # `doppelwaschtisch-6` besteht dort aus `-6-l` und `-6-r`, `dusche-3` aus
    # vierzehn Teilen, `kuechenzeile-0` aus acht. Der Name ist der Praefix.
    alle = sorted(invarianten["objekte"])
    zuordnung, ohne_objekt = {}, []
    for m in marker:
        name = m.get("name")
        teile = ([name] if name in invarianten["objekte"]
                 else [n for n in alle
                       if n.startswith(name + "-") or n.startswith(name + ".")])
        if teile:
            zuordnung[str(m.get("n"))] = {
                "objekt": name,
                "meshes": teile,
                "rolle": m.get("rolle"),
                "px": m.get("px"),
                "masse_mm": m.get("masse_mm"),
                "drehung_grad": m.get("drehung_grad"),
            }
        else:
            ohne_objekt.append({"n": m.get("n"), "name": name})
    return {"marker_gesamt": len(marker), "zugeordnet": zuordnung,
            "ohne_blender_objekt": ohne_objekt}


def stueckzahlen_pruefen(invarianten, job):
    """Die Sorten aus dem Auftrag gegen die Objekte in der Datei zaehlen.

    Gezaehlt wird das MOEBELSTUECK, nicht das Netz: `kleiderschrank-14` und
    `kleiderschrank-14-gap-1--1` sind ein Schrank. Dieselbe Regel wie in
    `stueckzahlen()` -- sonst zaehlt der Harness anders als der Auftrag, und
    beide haetten recht.
    """
    def bauteil(name):
        teile = name.split("-")
        return "-".join(teile[:2]) if len(teile) > 1 else name

    ist = {}
    for name, e in invarianten["objekte"].items():
        if e["typ"] != "MESH":
            continue
        # Tuerblaetter heissen `wall-<n>-door` und laufen sonst als
        # Architektur. Der Auftrag zaehlt sie als `tuer` -- beide haben
        # recht, also muss der Harness die Bruecke schlagen.
        if name.endswith("-door"):
            ist.setdefault("tuer", set()).add(name)
            continue
        if e["architektur"]:
            continue
        stamm = name.split("-")[0]
        ist.setdefault(stamm, set()).add(bauteil(name))
    soll = {}
    for stamm, namen in (job.get("objects") or {}).items():
        soll[stamm] = len({bauteil(n) for n in namen})
    zeilen, abweichungen = {}, []
    for stamm in sorted(set(soll) | set(ist)):
        s = soll.get(stamm)
        i = len(ist.get(stamm, ()))
        zeilen[stamm] = {"auftrag": s, "blend": i}
        if s is not None and s != i:
            abweichungen.append("%s: Auftrag %s, .blend %d" % (stamm, s, i))
    return {"je_sorte": zeilen, "abweichungen": abweichungen}


def main():
    try:
        import bpy
    except ImportError:
        sys.exit("Dieses Skript laeuft nur in Blender:\n"
                 '  blender.exe --background "<szene.blend>" '
                 "--python export_invariants.py -- <ziel.json> [codex-job.json]")
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argumente:
        sys.exit("Ziel-JSON fehlt.")
    ziel = argumente[0]
    job_pfad = argumente[1] if len(argumente) > 1 else None

    raus = sammle(bpy)
    if job_pfad and os.path.exists(job_pfad):
        with open(job_pfad, encoding="utf-8") as datei:
            job = json.load(datei)
        raus["marker"] = marker_zuordnen(raus, job)
        raus["stueckzahlen"] = stueckzahlen_pruefen(raus, job)
        raus["auftrag"] = {
            "plan_id": job.get("plan_id"),
            "job_id": job.get("job_id"),
            "nachweis_mesh_objekte": (job.get("nachweis") or {}).get("mesh_objekte"),
            "annotation_hash": (job.get("source") or {}).get("annotation_hash"),
        }
    os.makedirs(os.path.dirname(os.path.abspath(ziel)) or ".", exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as datei:
        json.dump(raus, datei, ensure_ascii=False, indent=1, sort_keys=True)

    meshes = sum(1 for e in raus["objekte"].values() if e["typ"] == "MESH")
    moebel = sum(1 for e in raus["objekte"].values()
                 if e["typ"] == "MESH" and not e["architektur"])
    print("INVARIANTS %s" % ziel)
    print("  Objekte gesamt %d, MESH %d, davon Moebel %d, Architektur %d"
          % (len(raus["objekte"]), meshes, moebel, meshes - moebel))
    if raus.get("marker"):
        m = raus["marker"]
        print("  Marker %d zugeordnet, %d ohne Blender-Objekt"
              % (len(m["zugeordnet"]), len(m["ohne_blender_objekt"])))
        for x in m["ohne_blender_objekt"]:
            print("    ! Marker %s -> %s fehlt in der .blend" % (x["n"], x["name"]))
    if raus.get("stueckzahlen"):
        for a in raus["stueckzahlen"]["abweichungen"]:
            print("    ! Stueckzahl %s" % a)
    nachweis = (raus.get("auftrag") or {}).get("nachweis_mesh_objekte")
    if nachweis is not None and nachweis != meshes:
        print("    ! Nachweis im Auftrag %s, in der Datei %d" % (nachweis, meshes))


if __name__ == "__main__":
    main()
