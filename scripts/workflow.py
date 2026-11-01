#!/usr/bin/env python3
"""Where every house stands, and the one next action for it.

The pipeline has seven gates. A house passes them in order, and at any moment it
is sitting at exactly one of them. This prints that -- as a funnel, so the shape
of the remaining work is visible at a glance, and per house so you can act.

    1  gezeichnet      Raeume annotiert
    2  vermessen       Massstab da (annotiert oder gebaeudemass.json)
    3  gebaut          .blend erzeugt
    4  geprueft        Verifier ohne FAIL
    5  zertifiziert    delivery-manifest.json, beide Stile
    6  hochgeladen     Bilder im WordPress-Katalog
    7  freigegeben     Rechte geklaert, an Kunden lieferbar

Nothing here changes anything. It reads and reports.

    python workflow.py                 Trichter + naechste Schritte
    python workflow.py --stufe 2       welche Haeuser genau dort haengen
    python workflow.py --haus bungalow_039
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import hausdaten  # noqa: E402
SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")
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
LEDGER = os.path.join(SUITE, "born2thrill-local-workbench", "data",
                      "simplifier-v2", "corpus-ledger.json")

STUFEN = [
    (1, "gezeichnet", "im Annotator Raeume zeichnen"),
    (2, "vermessen", "python gebaeudemass.py <haus> --breite B --tiefe T"),
    (3, "gebaut", "python batch-build.py <haus>"),
    (4, "geprueft", "Verifier-FAIL beheben (siehe plans/winkel-report.html)"),
    (5, "zertifiziert", "python batch-build.py <haus>  (beide Stile noetig)"),
    (6, "hochgeladen", "python publish-renders.py --plan <haus> --dir <ordner>"),
    # Zwei Befehle, eine Stufe: das Ledger und der Katalog. Siehe go.py.
    (7, "freigegeben", "python approve-plan.py <haus> --reason \"...\"  UND  python freigeben.py <haus>"),
]


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def stufe_von(name, ledger_idx, katalog):
    """The highest gate this house has passed, and why it stopped."""
    folder = os.path.join(PROJECTS, name)
    # Zeichnung und Gebaeudemass werden nicht mehr hier zusammengefuehrt,
    # sondern in hausdaten.py -- pro Geschoss, mit derselben Vorrangregel, die
    # der Bau benutzt. Die alten zwei Zeilen waren alles-oder-nichts und
    # zaehlten einen leeren Geschoss-Schluessel ({"groundfloor": null}, den der
    # Annotator anlegt, sobald das Geschoss existiert) als "vermessen": dieser
    # Trichter meldete Haeuser fertig, die der Bau ablehnt -- und schickte
    # damit niemanden mehr zum Messen.
    daten = hausdaten.hausdaten(folder)
    annotations = daten["annotationen"]
    if not annotations or not (annotations.get("annotations") or []):
        return 0, "keine Raeume gezeichnet"

    scale = daten["floor_scale"]
    if not scale:
        hat_bild = any(x.lower().endswith((".png", ".jpg", ".jpeg", ".pdf"))
                       and "room_concept" not in x.lower()
                       for x in os.listdir(folder))
        return 1, ("kein Massstab (Bild da -> im Annotator messen)" if hat_bild
                   else "kein Massstab und kein Bild -> Breite und Tiefe noetig")

    renders = os.path.join(DATA, "corrections", name, "renders", "go-baseline")
    blends = [x for x in os.listdir(renders)] if os.path.isdir(renders) else []
    if not any(x.endswith(".blend") for x in blends):
        return 2, "noch nicht gebaut"

    log = os.path.join(renders, "batch-build.log")
    fails = []
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as handle:
            fails = sorted({line.split()[1] for line in handle
                            if line.startswith("FAIL ") and len(line.split()) > 1})
    manifest = read_json(os.path.join(renders, "delivery-manifest.json"))
    if fails and not manifest:
        return 3, "Verifier: " + ", ".join(fails)
    if not manifest:
        return 3, "kein Zertifikat (Stil fehlgeschlagen?)"

    bilder = katalog.get(name, {}).get("images", 0)
    if not bilder:
        return 5, "%d Artefakte zertifiziert, keine Bilder im Katalog" % len(manifest.get("artifacts") or [])

    entry = ledger_idx.get(name) or {}
    if not entry.get("commercial_generator_eligible"):
        return 6, "%d Bilder im Katalog, Rechte nicht geklaert" % bilder
    return 7, ""


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stufe", type=int)
    parser.add_argument("--haus")
    args = parser.parse_args()

    ledger = read_json(LEDGER) or {}
    ledger_idx = {e["project_id"]: e for e in (ledger.get("projects") or [])}
    katalog = {}          # Katalog nur lesen, wenn erreichbar -- offline soll gehen

    namen = sorted(n for n in os.listdir(PROJECTS)
                   if os.path.exists(os.path.join(PROJECTS, n, "annotations.json")))

    if args.haus:
        s, warum = stufe_von(args.haus, ledger_idx, katalog)
        name = dict((n, t) for n, t, _ in STUFEN).get(s, "unbegonnen")
        print("%s: Stufe %d (%s)" % (args.haus, s, name))
        if warum:
            print("   haengt an: " + warum)
            for nr, _, tun in STUFEN:
                if nr == s + 1:
                    print("   naechster Schritt: " + tun)
        else:
            print("   fertig")
        return 0

    zaehler = {}
    haeuser = {}
    for n in namen:
        s, warum = stufe_von(n, ledger_idx, katalog)
        zaehler[s] = zaehler.get(s, 0) + 1
        haeuser.setdefault(s, []).append((n, warum))

    if args.stufe is not None:
        for n, warum in haeuser.get(args.stufe, []):
            print("   %-46s %s" % (n[:46], warum))
        print("")
        print("%d Haeuser auf Stufe %d" % (len(haeuser.get(args.stufe, [])), args.stufe))
        return 0

    gesamt = len(namen)
    print("%d Haeuser insgesamt" % gesamt)
    print("")
    durch = gesamt
    for nr, name, tun in STUFEN:
        haengen = zaehler.get(nr - 1, 0)
        durch -= haengen
        balken = "#" * int(40 * durch / max(gesamt, 1))
        print("  %d %-14s %4d  %s" % (nr, name, durch, balken))
        if haengen:
            print("      %4d haengen davor: %s" % (haengen, tun))
    print("")
    print("  Details:  python workflow.py --stufe <n>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
