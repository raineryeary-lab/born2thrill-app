#!/usr/bin/env python3
"""Doppelpunkte aus gespeicherten Moebellaeufen ziehen -- nur die harmlosen.

Rainer, 2026-08-28: "when i doubleclick to end the creation many times there
are 2 points created at the end." Und auf die Frage, ob ein Durchlauf die
bestehenden bereinigen soll: "what ever you think is better."

Die Ursache steckt im Ereignis: ein Doppelklick feuert erst ZWEI
click-Ereignisse -- jedes haengt einen Punkt an den Entwurf -- und erst danach
`dblclick`, das den Lauf abschliesst. Der Editor entdoppelt seit heute beim
Anlegen; die schon gespeicherten Laeufe behalten ihren Doppelpunkt.

Beim Nachsehen zerfiel der Befund in zwei Sorten, und nur eine wird angefasst:

  bereinigt   Ein Pfad, dessen letzter Punkt den vorletzten wiederholt. Die
              Strecke dazwischen ist null lang; sie zu entfernen aendert die
              Form nicht. Der Test rechnet das nach.

  gemeldet    Ein Rechteck, dessen zwei Eckpunkte zusammenfallen.
              `onehalfstorey_020` hat eine Kuecheninsel von 0 x 0 mm,
              `onehalfstorey_029` eine von 0 x 50 mm. Das ist kein
              Doppelpunkt, sondern eine kaputte Platzierung -- sie zu
              "bereinigen" liesse einen einzelnen Punkt zurueck. Sie gehoert
              neu gezeichnet oder geloescht, und das ist eine Entscheidung
              ueber Geometrie in Haeusern, deren Lieferung angenommen ist.

    python moebel-doppelpunkte.py            # nur zeigen
    python moebel-doppelpunkte.py --schreiben # mit Sicherung .vor-entdoppeln
"""

import argparse
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
             "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)

# Der Editor entdoppelt beim Anlegen mit 60 mm Toleranz -- dort ist der Punkt
# noch nicht gespeichert, und die Hand hat gerade zweimal geklickt.
#
# Ein Durchlauf ueber schon gespeicherte Haeuser darf das nicht. Beim ersten
# Trockenlauf schlug die Sicherheitspruefung an: in
# `german_catalog_review_bungalow_3_1_2_b_85` liegen die letzten zwei Punkte
# einer Vorwandinstallation 50 mm auseinander -- sie zu verschmelzen kuerzt den
# Lauf wirklich um 50 mm. Das ist eine Geometrieaenderung, keine Bereinigung.
#
# Hier faellt deshalb nur, was beweisbar nichts ist: eine Strecke der Laenge
# null. Alles dazwischen wird gemeldet und von Hand entschieden.
DOPPELT_MM = 1.0
KNAPP_MM = 60.0
RECHTECKE = ("kuecheninsel", "abstellschrank")
SICHERUNG = ".vor-entdoppeln"


def entdoppelt(punkte):
    """Aufeinanderfolgende Punkte zusammenziehen, die praktisch aufeinanderliegen."""
    raus = []
    for punkt in punkte:
        if raus and math.dist(punkt, raus[-1]) <= DOPPELT_MM:
            continue
        raus.append(punkt)
    return raus


def laenge(punkte):
    """Die Streckenlaenge des Laufs -- das Mass, das gleich bleiben muss."""
    return sum(math.dist(punkte[i], punkte[i - 1]) for i in range(1, len(punkte)))


def knapp_daneben(punkte):
    """Punktpaare, die dicht beieinander liegen, aber nicht aufeinander."""
    return [i for i in range(1, len(punkte))
            if DOPPELT_MM < math.dist(punkte[i], punkte[i - 1]) <= KNAPP_MM]


def befund(eintrag):
    """`sauber`, `zu_bereinigen`, `knapp` oder `entartet`."""
    punkte = eintrag.get("points_mm")
    if not punkte or len(punkte) < 2:
        return "sauber"
    if len(entdoppelt(punkte)) == len(punkte):
        return "knapp" if knapp_daneben(punkte) else "sauber"
    # Ein Rechteck hat genau zwei Ecken; faellt eine weg, bleibt kein Rechteck.
    if eintrag.get("symbol") in RECHTECKE or len(punkte) == 2:
        return "entartet"
    return "zu_bereinigen"


def bereinige_datei(pfad, schreiben):
    """Eine Moebeldatei durchgehen. Gibt (bereinigt, entartet, knapp) zurueck."""
    with open(pfad, encoding="utf-8") as datei:
        daten = json.load(datei)
    bereinigt, entartet, knapp = [], [], []
    for eintrag in daten.get("symbols", []):
        stand = befund(eintrag)
        if stand == "entartet":
            entartet.append(eintrag)
        elif stand == "knapp":
            knapp.append(eintrag)
        elif stand == "zu_bereinigen":
            vorher = eintrag["points_mm"]
            nachher = entdoppelt(vorher)
            # Die Form MUSS gleich bleiben, sonst wird nichts geschrieben.
            assert abs(laenge(vorher) - laenge(nachher)) < 1e-6, pfad
            bereinigt.append((eintrag, len(vorher), len(nachher)))
            if schreiben:
                eintrag["points_mm"] = nachher
    if schreiben and bereinigt:
        # Erst die Sicherung, dann schreiben. Ueber fremde Daten faehrt hier
        # niemand ohne Rueckweg.
        with open(pfad, encoding="utf-8") as gelesen:
            roh = gelesen.read()
        with open(pfad + SICHERUNG, "w", encoding="utf-8") as sicherung:
            sicherung.write(roh)
        with open(pfad, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, ensure_ascii=False, indent=2)
    return bereinigt, entartet, knapp


def main():
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("--schreiben", action="store_true",
                          help="wirklich aendern; ohne das wird nur gezeigt")
    argumente = zerleger.parse_args()

    muster = os.path.join(DATA, "corrections", "*", "furniture", "*.json")
    gesamt_bereinigt = gesamt_entartet = gesamt_knapp = 0
    for pfad in sorted(glob.glob(muster)):
        plan = os.path.basename(os.path.dirname(os.path.dirname(pfad)))
        bereinigt, entartet, knapp = bereinige_datei(pfad, argumente.schreiben)
        for eintrag, vorher, nachher in bereinigt:
            print("%-8s %-44s %-20s %d -> %d Punkte"
                  % ("geaendert" if argumente.schreiben else "wuerde",
                     plan, eintrag.get("symbol"), vorher, nachher))
            gesamt_bereinigt += 1
        for eintrag in entartet:
            punkte = eintrag["points_mm"]
            breite = abs(punkte[-1][0] - punkte[0][0])
            tiefe = abs(punkte[-1][1] - punkte[0][1])
            print("%-8s %-44s %-20s %.0f x %.0f mm -- neu zeichnen oder loeschen"
                  % ("ENTARTET", plan, eintrag.get("symbol"), breite, tiefe))
            gesamt_entartet += 1
        for eintrag in knapp:
            punkte = eintrag["points_mm"]
            paare = knapp_daneben(punkte)
            abstand = min(math.dist(punkte[i], punkte[i - 1]) for i in paare)
            print("%-8s %-44s %-20s zwei Punkte %.0f mm auseinander -- von Hand"
                  % ("KNAPP", plan, eintrag.get("symbol"), abstand))
            gesamt_knapp += 1

    print("")
    print("%d Lauf/Laeufe entdoppelt%s, %d knapp danebenliegende und "
          "%d entartete Platzierung(en) gemeldet."
          % (gesamt_bereinigt, "" if argumente.schreiben else " (nur gezeigt)",
             gesamt_knapp, gesamt_entartet))
    if not argumente.schreiben and gesamt_bereinigt:
        print("Zum Aendern: --schreiben. Es bleibt je Datei eine Sicherung "
              "%s liegen." % SICHERUNG)


if __name__ == "__main__":
    main()
