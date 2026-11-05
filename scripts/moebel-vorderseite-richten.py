"""Dreht gespeicherte Moebel so, dass ihre Vorderseite von der Wand weg zeigt.

Warum es diesen Lauf gibt
-------------------------
`snapStampToWalls` hat das Vorzeichen der Wandnormalen richtig bestimmt, aber
die Richtung der WAND als `rotation_deg` zurueckgegeben statt die der Normalen
(behoben am 2026-09-03). Zwei Raeume links und rechts derselben Wand bekamen
dieselbe Drehung, also stand die Haelfte falsch herum. Die Reparatur wirkt nur
beim naechsten Setzen; der Bestand behaelt seine alte Drehung.

Gemessen ueber die 19 Moebeldateien: von 244 wandnahen Stuecken zeigten 47 mit
der Vorderseite in die Wand.

Warum NICHT alle davon gerichtet werden
---------------------------------------
"Rueckseite an der Wand" gilt nicht fuer jedes Moebel:

- Eine Badewanne liegt mit der LANGEN Seite an der Wand; ihre Vorderseite ist
  das Armaturenende und zeigt die Wand ENTLANG, nicht von ihr weg. Sie
  wegzudrehen waere ein neuer Fehler, kein behobener.
- Ein Schreibtischstuhl schaut zum Schreibtisch, nicht in den Raum.
- Ein Schreibtisch steht oft mit der Front zur Wand, weil davor gesessen wird.

Deshalb richtet dieser Lauf nur die Typen, bei denen der Ruecken
definitionsgemaess an der Wand liegt: Schraenke, Geraete, Sanitaerobjekte an
der Wand. Alles andere wird gezaehlt und gemeldet, aber nicht angefasst -- im
Editor faellt es jetzt ohnehin auf, weil jedes Moebel einen Pfeil hat.

Aufruf
------
    python scripts/moebel-vorderseite-richten.py            # nur messen
    python scripts/moebel-vorderseite-richten.py --schreiben

Vor jedem Schreiben wird die Datei als <name>.vor-vorderseite-<datum>.json
danebengelegt.
"""

import collections
import glob
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Typen, bei denen die Rueckseite definitionsgemaess an der Wand liegt.
AN_DIE_WAND = {
    "kleiderschrank", "garderobe", "lowboard", "sideboard",
    "abstellschrank", "schrank_40", "schrank_60",
    "kuehlschrank", "hochschrank_herd", "kochfeld", "spuele",
    "waschmaschine", "trockner",
    "wand_wc", "handwaschbecken", "doppelwaschtisch", "waschtisch",
    "badheizkoerper", "fernseher",
}

# Wie weit ein Stueck von einer Wand entfernt sein darf, um noch als
# "steht an dieser Wand" zu gelten. Grosszuegig: die Tiefe der meisten
# Schraenke liegt unter 700 mm, und die Position ist der Mittelpunkt.
REICHWEITE_MM = 900

# Ab welchem Skalarprodukt eine Vorderseite eindeutig zur Wand zeigt. Zwischen
# -0,5 und +0,5 steht das Stueck quer zur Wand; das ist keine Fehlstellung,
# die dieser Lauf beheben koennte, sondern eine Absicht.
EINDEUTIG = 0.5


def workbench_data_root():
    root = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
    if not root:
        raise SystemExit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt")
    return root


def naechste_kante(point, rooms):
    """Die naechste Raumkante zu diesem Punkt -- dieselbe Suche wie im Editor."""
    best = None
    for room in rooms or []:
        poly = room.get("polygon") or room.get("polygon_mm") or []
        for index in range(len(poly)):
            a, b = poly[index], poly[(index + 1) % len(poly)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            laenge = dx * dx + dy * dy
            if not laenge:
                continue
            t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / laenge
            t = max(0.0, min(1.0, t))
            px, py = a[0] + dx * t, a[1] + dy * t
            distanz = math.hypot(point[0] - px, point[1] - py)
            if best is None or distanz < best[0]:
                best = (distanz, (px, py), a, b)
    return best


def raumnormale(point, best):
    """Die Normale der Kante, gedreht zu der Seite, auf der das Stueck steht."""
    _, projiziert, a, b = best
    winkel = math.atan2(b[1] - a[1], b[0] - a[0])
    nx, ny = -math.sin(winkel), math.cos(winkel)
    if (point[0] - projiziert[0]) * nx + (point[1] - projiziert[1]) * ny < 0:
        nx, ny = -nx, -ny
    return nx, ny


def drehung_aus_normale(nx, ny):
    """Die Drehung, nach der die lokale Vorderseite +y auf (nx, ny) faellt."""
    return round((math.degrees(math.atan2(-nx, ny)) + 360) % 360) % 360


def vorderseite(grad):
    bogen = math.radians(grad)
    return -math.sin(bogen), math.cos(bogen)


def geometrie(project_id, cache_dir):
    pfad = os.path.join(cache_dir, "geometrie-%s.json" % project_id)
    if not os.path.exists(pfad):
        ergebnis = subprocess.run(
            [sys.executable, os.path.join(HERE, "build-simplifier-render-plan.py"),
             "--geometry-only", project_id, pfad],
            capture_output=True, text=True)
        if ergebnis.returncode != 0 or not os.path.exists(pfad):
            return None
    return json.load(open(pfad, encoding="utf-8"))


FLOOR_ALIAS = {"floor-0": "groundfloor", "floor-1": "upperfloor",
               "groundfloor": "floor-0", "upperfloor": "floor-1"}


def raeume_fuer(geom, floor_id):
    """Die Raeume des Geschosses. Die Moebeldatei heisst floor-0, die
    Geometrie nennt dasselbe Geschoss groundfloor."""
    gesucht = {floor_id, FLOOR_ALIAS.get(floor_id, floor_id)}
    floors = geom.get("floors") or []
    for floor in floors:
        if floor.get("floor_level") in gesucht:
            return floor.get("rooms") or []
    if len(floors) == 1:
        return floors[0].get("rooms") or []
    # Zwei Geschosse, aber keins passt namentlich: die Reihenfolge ist
    # groundfloor zuerst, und floor-0 ist das untere.
    reihenfolge = {"floor-0": 0, "groundfloor": 0, "floor-1": 1, "upperfloor": 1}
    index = reihenfolge.get(floor_id)
    if index is not None and index < len(floors):
        return floors[index].get("rooms") or []
    return []


def main(schreiben, cache_dir):
    # Die eigenen Sicherungen liegen im selben Ordner und enden ebenfalls auf
    # .json. Ohne diesen Filter misst ein zweiter Lauf den Bestand VOR der
    # Korrektur gleich mit und meldet die alten Zahlen als offen.
    dateien = sorted(pfad for pfad in
                     glob.glob(os.path.join(workbench_data_root(), "corrections",
                                            "*", "furniture", "*.json"))
                     if ".vor-vorderseite-" not in os.path.basename(pfad))
    gerichtet = collections.Counter()
    gemeldet = collections.Counter()
    geprueft = falsch = geaendert = 0
    ohne_geometrie = []

    for datei in dateien:
        project_id = datei.split(os.sep)[-3]
        floor_id = os.path.splitext(os.path.basename(datei))[0]
        geom = geometrie(project_id, cache_dir)
        if geom is None:
            ohne_geometrie.append(project_id)
            continue
        rooms = raeume_fuer(geom, floor_id)
        if not rooms:
            ohne_geometrie.append("%s/%s" % (project_id, floor_id))
            continue

        dokument = json.load(open(datei, encoding="utf-8"))
        symbole = dokument.get("symbols") or []
        datei_geaendert = 0
        for symbol in symbole:
            position = symbol.get("position_mm")
            if not position:
                continue                     # gezeichneter Zug, keine Drehung
            best = naechste_kante(position, rooms)
            if best is None or best[0] > REICHWEITE_MM:
                continue                     # steht frei, keine Wand in Reichweite
            geprueft += 1
            nx, ny = raumnormale(position, best)
            fx, fy = vorderseite(symbol.get("rotation_deg", 0) or 0)
            if fx * nx + fy * ny >= -EINDEUTIG:
                continue                     # zeigt nicht in die Wand
            falsch += 1
            schluessel = symbol.get("symbol")
            if schluessel not in AN_DIE_WAND:
                gemeldet[schluessel] += 1
                continue
            gerichtet[schluessel] += 1
            if schreiben:
                symbol["rotation_deg"] = drehung_aus_normale(nx, ny)
                datei_geaendert += 1

        if schreiben and datei_geaendert:
            sicherung = datei.replace(".json", ".vor-vorderseite-2026-09-03.json")
            if not os.path.exists(sicherung):
                with open(sicherung, "w", encoding="utf-8") as ziel:
                    json.dump(json.load(open(datei, encoding="utf-8")), ziel,
                              ensure_ascii=False, indent=2)
            with open(datei, "w", encoding="utf-8") as ziel:
                json.dump(dokument, ziel, ensure_ascii=False, indent=2)
            geaendert += datei_geaendert
            print("[richten] %-46s %d gedreht" % (project_id[:46], datei_geaendert))

    print()
    print("wandnahe Stuecke geprueft:      %d" % geprueft)
    print("Vorderseite zeigt in die Wand:  %d" % falsch)
    print()
    print("GERICHTET (Ruecken gehoert an die Wand):")
    for schluessel, anzahl in gerichtet.most_common():
        print("  %-24s %d" % (schluessel, anzahl))
    print()
    print("NUR GEMELDET (Vorderseite folgt einer anderen Regel):")
    for schluessel, anzahl in gemeldet.most_common():
        print("  %-24s %d" % (schluessel, anzahl))
    if ohne_geometrie:
        print()
        print("ohne Geometrie, nicht geprueft: %s" % ", ".join(sorted(set(ohne_geometrie))))
    print()
    print("geschrieben: %d" % geaendert if schreiben
          else "TROCKENLAUF -- nichts geschrieben. Mit --schreiben anwenden.")
    return 0


if __name__ == "__main__":
    cache = os.environ.get("VORDERSEITE_CACHE") or os.path.join(REPO, "tmp")
    os.makedirs(cache, exist_ok=True)
    raise SystemExit(main("--schreiben" in sys.argv, cache))
