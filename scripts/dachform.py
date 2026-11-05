#!/usr/bin/env python3
"""Give every house a roof form, so bpypolyskel has something to build.

The roof machinery has worked all along: render-exterior.py feeds the footprint
to bpypolyskel (the straight-skeleton clone in scripts/bpypolyskel) which solves
the real hips and valleys, including where wings meet. bungalow_040_66's classic
exterior proves it.

It only ever built roofs for TWO houses, because `roof_type_modern` and
`roof_type_classic` are set in exactly two annotations. Every other house handed
the renderer None, and `plan.get("roof_type") or "flachdach"` quietly turned that
into a flat roof.

The pattern comes from those two houses, not from me guessing:

    bungalow_040_66     modern=flachdach   classic=walmdach
    onehalfstorey_020   modern=flachdach   classic=walmdach

One is a bungalow, one a 1.5-storey, and both use the same pair -- so it is the
house STYLE that decides the roof here, not the house type.

Written to gebaeudemass.json beside the annotation, never into it. Change any
single house afterwards with --modern/--classic, or drop it with --entfernen.

    python dachform.py --list
    python dachform.py --alle
    python dachform.py onehalfstorey_043 --classic satteldach
    python dachform.py onehalfstorey_043 --entfernen
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# Eine Wahrheit fuer Dachform und Massstab (siehe scripts/hausdaten.py).
import hausdaten  # noqa: E402

SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")

# What render-exterior.py can actually build. walmdach and satteldach both go
# through bpypolyskel; flachdach is the parapet-and-deck path.
FORMEN = ("flachdach", "walmdach", "satteldach")
STANDARD_MODERN = "flachdach"
STANDARD_CLASSIC = "walmdach"


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def write_sidecar(folder, record):
    path = os.path.join(folder, "gebaeudemass.json")
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=1, ensure_ascii=False)
    os.replace(temporary, path)
    return path


def standard_fuer(name):
    """Die Dachform, die gesetzt wird, wenn niemand eine gewaehlt hat.

    1,5-Geschosser: Satteldach in beiden Stilen -- sie werden nur mit diesem
    einen Dach geliefert (anderthalb-eine-dachform-v1). Alle anderen: das
    bisherige Muster (modern flach, classic Walm).
    """
    import anderthalb
    try:
        with open(os.path.join(PROJECTS, name, "data.json"), encoding="utf-8-sig") as handle:
            typ = json.load(handle).get("house_type")
    except (OSError, ValueError):
        typ = None
    if anderthalb.ist_anderthalb({"plan_id": name, "house_type": typ}):
        return "satteldach", "satteldach"
    return STANDARD_MODERN, STANDARD_CLASSIC


def set_roof(name, modern, classic):
    """Merge the roof forms into the project's sidecar, keeping what is there."""
    folder = os.path.join(PROJECTS, name)
    annotations = read_json(os.path.join(folder, "annotations.json"))
    if not annotations:
        return None
    record = read_json(os.path.join(folder, "gebaeudemass.json")) or {
        "schema": "zf-gebaeudemass-v1", "plan_id": name}
    record["roof_type_modern"] = modern
    record["roof_type_classic"] = classic
    record["dachform_gesetzt_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    record["dachform_herkunft"] = (
        "1,5-Geschosser: Satteldach mit Kniestock (anderthalb-eine-dachform-v1)"
        if (modern, classic) == ("satteldach", "satteldach") and standard_fuer(name) == (modern, classic)
        else "Muster aus bungalow_040_66 und onehalfstorey_020: modern flach, classic Walm")
    write_sidecar(folder, record)
    return record


def already_annotated(name):
    """Roof forms set in the annotation itself always win -- do not shadow them.

    Gefragt wird nicht mehr selbst nach, sondern die Herkunft aus
    scripts/hausdaten.py: "annotations" heisst, die Zeichnung setzt die
    Dachform und das Sidecar wuerde sie ohnehin nicht ueberschreiben.
    """
    herkunft = hausdaten.hausdaten(os.path.join(PROJECTS, name))["herkunft"]
    return "annotations" in (herkunft["dachform_modern"],
                             herkunft["dachform_classic"])


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--alle", action="store_true", help="alle Haeuser ohne Dachform")
    parser.add_argument("--list", action="store_true")
    # Ohne Angabe: der Standard des HAUSES (standard_fuer), nicht fuer alle gleich.
    parser.add_argument("--modern", default=None, choices=FORMEN)
    parser.add_argument("--classic", default=None, choices=FORMEN)
    parser.add_argument("--entfernen", action="store_true")
    args = parser.parse_args()

    if args.list or (not args.plan and not args.alle):
        offen = fertig = annotiert = 0
        for name in sorted(os.listdir(PROJECTS)):
            folder = os.path.join(PROJECTS, name)
            daten = hausdaten.hausdaten(folder)
            if not daten["annotationen"]:
                continue
            # Beide Stile zaehlen: ein Haus mit nur roof_type_modern im Sidecar
            # galt frueher als "noch ohne Dachform".
            if "annotations" in (daten["herkunft"]["dachform_modern"],
                                 daten["herkunft"]["dachform_classic"]):
                annotiert += 1
            elif daten["dachform_modern"] or daten["dachform_classic"]:
                fertig += 1
            else:
                offen += 1
        print("Dachform gesetzt in der Annotation : %d" % annotiert)
        print("Dachform im Sidecar                : %d" % fertig)
        print("noch ohne Dachform                 : %d" % offen)
        print("")
        print("  python dachform.py --alle      setzt modern=%s, classic=%s"
              % (STANDARD_MODERN, STANDARD_CLASSIC))
        return 0

    if args.plan and args.entfernen:
        folder = os.path.join(PROJECTS, args.plan)
        record = read_json(os.path.join(folder, "gebaeudemass.json"))
        if not record:
            print("nichts zu entfernen")
            return 0
        for key in ("roof_type_modern", "roof_type_classic",
                    "dachform_gesetzt_at", "dachform_herkunft"):
            record.pop(key, None)
        write_sidecar(folder, record)
        print("Dachform aus %s entfernt" % args.plan)
        return 0

    if args.plan:
        if already_annotated(args.plan):
            print("%s hat die Dachform in der Annotation -- die gilt, "
                  "das Sidecar wuerde sie nicht ueberschreiben." % args.plan)
            return 1
        _m, _c = standard_fuer(args.plan)
        modern, classic = args.modern or _m, args.classic or _c
        record = set_roof(args.plan, modern, classic)
        if not record:
            sys.exit("Kein Projekt: " + args.plan)
        print("[dach] %s: modern=%s classic=%s" % (args.plan, modern, classic))
        return 0

    gesetzt = uebersprungen = 0
    for name in sorted(os.listdir(PROJECTS)):
        folder = os.path.join(PROJECTS, name)
        if not read_json(os.path.join(folder, "annotations.json")):
            continue
        if already_annotated(name):
            uebersprungen += 1
            continue
        _m, _c = standard_fuer(name)
        if set_roof(name, args.modern or _m, args.classic or _c):
            gesetzt += 1
    print("%d Haeuser bekommen ihre Standard-Dachform (1,5-Geschosser: Satteldach; sonst modern=%s, classic=%s)"
          % (gesetzt, args.modern or STANDARD_MODERN, args.classic or STANDARD_CLASSIC))
    print("%d uebersprungen (Dachform steht schon in der Annotation)" % uebersprungen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
