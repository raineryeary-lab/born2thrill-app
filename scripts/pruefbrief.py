#!/usr/bin/env python3
"""Der Prüfbrief zu einer Lieferung: was drin sein muss, und wo.

Rainer, 2026-09-01: "codex hat keine schlechte Arbeit geleistet, nur muessen
wir die Fehler minimieren wo moeglich damit wir einen Fluss hinbekommen."

Der Fluss scheitert nicht an der Qualitaet, sondern an den RUNDEN. Bei
german_catalog_review_bungalow_3_4_2_b_120 ging die Beanstandung dreimal
raus, weil stueckweise geprueft wurde: erst die Stuehle, dann der Klotz, dann
die fehlende Dusche. Jede Runde kostet einen halben Tag.

Vier Bilder gleichzeitig pruefen geht -- vier Augenpaare parallel, je eines
je Bild. Die brauchen alle denselben Zettel: was laut .blend im Bild stehen
muss, wie viele es sind und an welchem Pixel. Genau den schreibt dieses
Skript, damit die Pruefung in Sekunden startet statt in einer
Viertelstunde Handarbeit.

    python pruefbrief.py <plan> [lieferordner]

Ohne Lieferordner wird der juengste Codex-Ordner genommen. Heraus kommt der
Pfad des Briefs; die Bilder stehen mit darin.

Was der Brief NICHT kann: die Bilder ansehen. Das bleibt Sache dessen, der
ihn bekommt. Codex, 2026-09-01, zu dem was auch mit Masken nicht garantiert
bleibt: "Kontaktpunkte, Kollisionen, Tueren, Treppen, Gelaender und
Moeblierung muessen visuell geprueft werden."
"""

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt.")
DATA = os.path.abspath(_konfiguriert)


def _make_codex_job():
    """`stueckzahlen` kommt aus dem Generator -- eine Wahrheit, nicht zwei."""
    spec = importlib.util.spec_from_file_location(
        "make_codex_job", os.path.join(HERE, "make-codex-job.py"))
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def juengster_ordner(renders):
    """Der neueste Codex-Lieferordner, oder None.

    go-baseline zaehlt nicht: das ist der Rohbau-Nachweis, keine Lieferung.
    """
    if not os.path.isdir(renders):
        return None
    codex = [e for e in os.listdir(renders)
             if e.startswith("codex-") and os.path.isdir(os.path.join(renders, e))]
    if not codex:
        return None
    return max(codex, key=lambda e: os.path.getmtime(os.path.join(renders, e)))


def bilder_im_ordner(job, ordner):
    """Die Innenbilder der Lieferung, in der Reihenfolge des Auftrags."""
    innen = [e["filename_hint"] for e in job.get("required_outputs", [])
             if e.get("kind") == "interior"]
    da = sorted(os.listdir(ordner)) if os.path.isdir(ordner) else []
    namen = []
    for hint in innen:
        stamm = os.path.splitext(hint)[0]
        treffer = [f for f in da if f.startswith(stamm)]
        if treffer:
            namen.append(treffer[0])
    return namen


def brief(job, ordner, stueckzahlen):
    """Der Text: Stueckzahlen, Marker, Bilderliste."""
    zeilen = ["SOLL-LISTE aus der .blend -- so viele Stuecke stehen wirklich drin.",
              ""]
    for z in stueckzahlen:
        if z.startswith("- "):
            zeilen.append(z.replace("`", "").replace("**", ""))
    karten = job.get("object_map") or []
    karten = karten if isinstance(karten, list) else [karten]
    marker = (karten[0].get("markers") if karten else []) or []
    bild = (karten[0].get("image") if karten else None) or [0, 0]
    zeilen += ["",
               "MARKER -- Pixel im %dx%d-Bild, Mitte des Objekts, dazu die "
               "Masse aus der .blend." % (bild[0], bild[1]),
               "Der Punkt ist der SCHWERPUNKT: bei niedrigen Moebeln liegt er "
               "optisch auf der",
               "Tischplatte oder daneben. Das ist kein Fehler.", ""]
    for e in sorted(marker, key=lambda x: x["name"]):
        mm = e.get("masse_mm")
        zeilen.append("  %-24s px %4d,%4d  %s"
                      % (e["name"], e["px"][0], e["px"][1],
                         ("%d x %d x %d mm" % tuple(mm)) if mm else ""))
    zeilen += ["", "BILDER in %s:" % ordner, ""]
    for name in bilder_im_ordner(job, ordner):
        zeilen.append("  " + os.path.join(ordner, name))
    return "\n".join(zeilen) + "\n"


def main():
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("plan")
    zerleger.add_argument("ordner", nargs="?")
    zerleger.add_argument("--nach", help="wohin der Brief geschrieben wird")
    args = zerleger.parse_args()

    renders = os.path.join(DATA, "corrections", args.plan, "renders")
    pfad = os.path.join(renders, "go-baseline", "codex-job.json")
    if not os.path.exists(pfad):
        sys.exit("Kein Auftrag fuer %s -- erst 'An Codex'." % args.plan)
    with open(pfad, encoding="utf-8") as datei:
        job = json.load(datei)

    ordner = args.ordner or juengster_ordner(renders)
    if not ordner:
        sys.exit("Keine Codex-Lieferung unter %s." % renders)
    if not os.path.isabs(ordner):
        ordner = os.path.join(renders, ordner)

    text = brief(job, ordner, _make_codex_job().stueckzahlen(job.get("objects") or {}))
    ziel = args.nach or os.path.join(ordner, "PRUEFBRIEF.txt")
    with open(ziel, "w", encoding="utf-8") as datei:
        datei.write(text)
    print(ziel)


if __name__ == "__main__":
    main()
