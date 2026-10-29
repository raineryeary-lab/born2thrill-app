#!/usr/bin/env python3
"""Liest plans/masse.csv und setzt alle eingetragenen Masse auf einmal.

Statt 158-mal `gebaeudemass.py <haus> --breite B --tiefe T` zu tippen: die
Spalten in der CSV ausfuellen, einmal dieses Skript, fertig. Leere Zeilen
werden uebersprungen, du kannst also in Etappen arbeiten und immer wieder
laufen lassen.

    python masse-einlesen.py            Probelauf, zeigt nur was passieren wuerde
    python masse-einlesen.py --apply    setzt die Masse
    python masse-einlesen.py --apply --bauen    setzt sie und baut gleich

Format je Zeile:   haus,breite_m,tiefe_m
Alles ab # ist Kommentar.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
CSV = os.path.join(SUITE, "floorplan-simplifier", "plans", "masse.csv")
PY = sys.executable


def zeilen():
    if not os.path.exists(CSV):
        sys.exit("Keine Liste: " + CSV)
    with open(CSV, encoding="utf-8") as handle:
        for nummer, roh in enumerate(handle, 1):
            text = roh.split("#")[0].strip()
            if not text:
                continue
            teile = [t.strip() for t in text.split(",")]
            if len(teile) < 3 or not teile[1] or not teile[2]:
                continue          # noch nicht ausgefuellt
            try:
                yield nummer, teile[0], float(teile[1].replace(",", ".")), \
                    float(teile[2].replace(",", "."))
            except ValueError:
                print("  Zeile %d: '%s' ist keine Zahl -- uebersprungen" % (nummer, text))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--bauen", action="store_true", help="danach gleich go.py laufen lassen")
    args = parser.parse_args()

    gesetzt, fehler = [], []
    for nummer, haus, breite, tiefe in zeilen():
        if not args.apply:
            print("  wuerde  %-40s %.2f x %.2f m" % (haus[:40], breite, tiefe))
            gesetzt.append(haus)
            continue
        code = subprocess.call([PY, os.path.join(HERE, "gebaeudemass.py"), haus,
                                "--breite", str(breite), "--tiefe", str(tiefe)],
                               stdout=subprocess.DEVNULL, cwd=HERE)
        if code == 0:
            print("  gesetzt %-40s %.2f x %.2f m" % (haus[:40], breite, tiefe))
            gesetzt.append(haus)
        else:
            print("  FEHLER  %-40s (Zeile %d)" % (haus[:40], nummer))
            fehler.append(haus)

    print("")
    print("%d Haeuser%s, %d Fehler"
          % (len(gesetzt), "" if args.apply else " (Probelauf)", len(fehler)))
    if not gesetzt:
        print("Noch nichts ausgefuellt. Trage Breite und Tiefe in %s ein." % CSV)
        return 0
    if args.apply and args.bauen and gesetzt:
        print("")
        subprocess.call([PY, os.path.join(HERE, "go.py")] + gesetzt, cwd=HERE)
    elif args.apply:
        print("Bauen:  python go.py " + " ".join(gesetzt[:3])
              + (" ..." if len(gesetzt) > 3 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
