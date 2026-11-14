#!/usr/bin/env python3
"""Bestehende Moebeldateien einmalig in den Bau-Anzeigeraum umrechnen.

    python moebel-migrieren.py bungalow_036
    python moebel-migrieren.py --alle
    python moebel-migrieren.py --alle --probe     nur rechnen, nichts schreiben

WARUM. Bis zum 2026-08-21 zeigte der Moebel-Editor den Korrektur-Kandidaten
(/generate), gebaut wurde aber die Frame-Geometrie des Annotationswegs --
zwei verschieden gerechnete Haeuser unter demselben Koordinatenraum-Namen.
Ergebnis: jedes gesetzte Moebel stand im Bau spiegelverkehrt und verschoben
(Waschmaschine im HWR gesetzt -> im Schlafzimmer gerendert, Bett auf Granit).

Die Zuordnung laeuft RAUMWEISE, nicht ueber eine globale Transformation --
eine solche gibt es zwischen den beiden Haeusern nicht (nicht-uniforme
Faktoren je Achse, gemessen 1.123 vs 1.249 auf onehalfstorey_020):

    1. In welchem Kandidaten-Raum steht das Moebel? (Punkt-in-Polygon,
       sonst naechster Raum)
    2. Wo relativ zur Raum-Box? (fx, fy in 0..1)
    3. Derselbe relative Punkt in der Box DESSELBEN Raums der Bau-Geometrie
       (Zuordnung ueber Annotations-Id, sonst ueber den Namen).

Drehungen bleiben stehen: beide Raeume sind y-nach-unten, gespiegelt wird
nichts. Die alte Datei bleibt als .vor-migration-<datum> liegen.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
# Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein Skript,
# das ohne gesetzte Variable still auf den alten C:-Nachbarordner
# zurueckfiele, wuerde unbemerkt gegen veraltete Daten arbeiten -- exakt
# der root-merge-Fehler vom 18.08., nur seitenverkehrt. Gleiches Muster wie
# build-simplifier-render-plan.py.workbench_data_root().
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
            "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)
NEUER_RAUM = "render-geometry-mm-y-down-v1"
ALTER_RAUM = "correction-document-mm-svg-y-down-v1"


def kandidat_geometrie(plan):
    """Die Geometrie, auf der die alten Moebel gesetzt wurden (/generate)."""
    url = ("http://localhost:3000/api/floorplan-workbench/generate"
           "?reference=%s&transform=identity" % plan)
    with urllib.request.urlopen(url, timeout=120) as antwort:
        daten = json.load(antwort)
    if not daten.get("candidate"):
        raise SystemExit("%s: /generate liefert keinen Kandidaten (%s)"
                         % (plan, daten.get("error")))
    return daten["candidate"]["floors"]


def bau_geometrie(plan):
    """Die Geometrie, die gebaut wird, im Anzeige-Raum (y nach unten)."""
    out = os.path.join(DATA, "corrections", plan, "tmp", "migration-geometrie.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    befehl = [sys.executable, os.path.join(HERE, "build-simplifier-render-plan.py"),
              "--geometry-only", plan, out]
    lauf = subprocess.run(befehl, capture_output=True, text=True, errors="replace")
    if lauf.returncode != 0:
        raise SystemExit("%s: geometry-only fehlgeschlagen: %s"
                         % (plan, (lauf.stdout + lauf.stderr)[-300:]))
    with open(out, encoding="utf-8-sig") as handle:
        daten = json.load(handle)
    os.remove(out)
    if daten.get("coordinate_space") != NEUER_RAUM:
        raise SystemExit("geometry-only liefert %r statt %r -- Skriptstand pruefen"
                         % (daten.get("coordinate_space"), NEUER_RAUM))
    return daten["floors"]


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def drin(pt, poly):
    x, y = pt
    innen = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            innen = not innen
        j = i
    return innen


def raum_von(pt, raeume, schluessel):
    for r in raeume:
        if drin(pt, r[schluessel]):
            return r
    # sonst: naechstgelegene Raum-Box
    def abstand(r):
        x0, y0, x1, y1 = bbox(r[schluessel])
        dx = max(x0 - pt[0], 0, pt[0] - x1)
        dy = max(y0 - pt[1], 0, pt[1] - y1)
        return (dx * dx + dy * dy) ** 0.5
    return min(raeume, key=abstand)


def uebertrage(pt, quelle, quell_schluessel, ziel, ziel_schluessel):
    qx0, qy0, qx1, qy1 = bbox(quelle[quell_schluessel])
    zx0, zy0, zx1, zy1 = bbox(ziel[ziel_schluessel])
    fx = (pt[0] - qx0) / (qx1 - qx0) if qx1 > qx0 else 0.5
    fy = (pt[1] - qy0) / (qy1 - qy0) if qy1 > qy0 else 0.5
    fx = max(0.0, min(1.0, fx))
    fy = max(0.0, min(1.0, fy))
    return [round(zx0 + fx * (zx1 - zx0), 1), round(zy0 + fy * (zy1 - zy0), 1)]


def ziel_raum(quell, bau_raeume):
    for r in bau_raeume:
        if r.get("id") and r["id"] == quell.get("id"):
            return r
    name = (quell.get("name") or "").strip().lower()
    for r in bau_raeume:
        if (r.get("name") or "").strip().lower() == name:
            return r
    return None


def migriere(plan, probe=False):
    ordner = os.path.join(DATA, "corrections", plan, "furniture")
    if not os.path.isdir(ordner):
        return "keine Moebeldateien"
    dateien = sorted(n for n in os.listdir(ordner) if n.endswith(".json"))
    if not dateien:
        return "keine Moebeldateien"

    kandidat = kandidat_geometrie(plan)
    bau = bau_geometrie(plan)
    stempel = datetime.date.today().isoformat()

    saetze = []
    for name in dateien:
        pfad = os.path.join(ordner, name)
        with open(pfad, encoding="utf-8-sig") as handle:
            doc = json.load(handle)
        if doc.get("coordinate_space") == NEUER_RAUM:
            saetze.append("%s: schon migriert" % name)
            continue
        if doc.get("coordinate_space") != ALTER_RAUM:
            saetze.append("%s: unbekannter Raum %r -- uebersprungen"
                          % (name, doc.get("coordinate_space")))
            continue

        index = int(name.split("-")[1].split(".")[0])
        if index >= len(kandidat) or index >= len(bau):
            saetze.append("%s: Geschoss %d fehlt in einer der Geometrien" % (name, index))
            continue
        k_raeume = kandidat[index]["rooms"]
        b_raeume = bau[index]["rooms"]

        verloren = []
        for symbol in doc.get("symbols") or []:
            punkte = ([symbol["position_mm"]] if symbol.get("position_mm")
                      else list(symbol.get("points_mm") or []))
            neu = []
            for pt in punkte:
                quelle = raum_von(pt, k_raeume, "polygon")
                ziel = ziel_raum(quelle, b_raeume)
                if ziel is None:
                    verloren.append("%s (%s: Raum %r ohne Entsprechung)"
                                    % (symbol.get("symbol"), name, quelle.get("name")))
                    break
                neu.append(uebertrage(pt, quelle, "polygon", ziel, "polygon_mm"))
            else:
                if symbol.get("position_mm"):
                    symbol["position_mm"] = neu[0]
                else:
                    symbol["points_mm"] = neu

        if verloren:
            saetze.append("%s: NICHT geschrieben -- %s" % (name, "; ".join(verloren)))
            continue

        doc["coordinate_space"] = NEUER_RAUM
        doc["migriert_am"] = datetime.datetime.now().isoformat(timespec="seconds")
        doc["migration"] = ("raumweise aus %s (Korrektur-Kandidat), Spiegelfehler "
                           "vom 2026-08-21" % ALTER_RAUM)
        if probe:
            saetze.append("%s: wuerde %d Symbole umrechnen" % (name, len(doc.get("symbols") or [])))
            continue
        os.replace(pfad, pfad + ".vor-migration-" + stempel)
        with open(pfad + ".tmp", "w", encoding="utf-8") as handle:
            json.dump(doc, handle, indent=2, ensure_ascii=False)
        os.replace(pfad + ".tmp", pfad)
        saetze.append("%s: %d Symbole migriert" % (name, len(doc.get("symbols") or [])))
    return "; ".join(saetze)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plaene", nargs="*")
    parser.add_argument("--alle", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()

    plaene = args.plaene
    if args.alle:
        wurzel = os.path.join(DATA, "corrections")
        plaene = sorted(n for n in os.listdir(wurzel)
                        if os.path.isdir(os.path.join(wurzel, n, "furniture")))
    if not plaene:
        sys.exit("Welches Haus? Oder --alle")

    for plan in plaene:
        try:
            print("%-24s %s" % (plan, migriere(plan, probe=args.probe)))
        except SystemExit as fehler:
            print("%-24s FEHLER: %s" % (plan, fehler))
    return 0


if __name__ == "__main__":
    sys.exit(main())
