#!/usr/bin/env python3
"""Rechteerklaerungen: einmal fragen, dann merken.

Die Rechtefrage ist keine Qualitaetspruefung. Ein Haus wird nicht dadurch
freigabefaehig, dass man besser zeichnet -- das Feld
`usage_rights.commercial_use_allowed` bleibt `false`, egal wie viel Arbeit
drinsteckt. Trotzdem stand die Frage bisher bei jedem der 55 gesperrten
Haeuser neu im Weg, beantwortbar nur ueber ein Flag, das man kennen musste
(Rainer, 2026-08-25: "wieso wird mir das sichern so erschwert?").

Hier steht die Antwort. Einmal gegeben, gilt sie -- fuer ein Haus oder fuer
einen ganzen Datensatz.

Was sie NICHT tut: den Herkunftsnachweis umschreiben. Der bleibt, was er ist;
die Erklaerung steht daneben und nimmt mit, was er zum Zeitpunkt der Erklaerung
gesagt hat. Am 2026-08-01 wurden genau diese 55 Projekte pauschal mit der
Begruendung "real plan has explicit generator rights" freigegeben, waehrend
ihre eigenen Nachweise `rights-unconfirmed` sagten. Passiert so etwas wieder,
soll man es hinterher lesen koennen.

    python rechte.py --zeigen
    python rechte.py --plan bungalow_039 --ja --grund "eigener Entwurf"
    python rechte.py --datensatz "Team Massivhaus catalog" --ja --grund "..." --wer Rainer
    python rechte.py --plan foo --nein --grund "doch ein Fremdplan"
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")

SCHEMA = "zf-rechte-v1"


def datenordner():
    """Nicht raten -- gleiche Regel wie approve-plan.py und der Compiler."""
    konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
    if not konfiguriert:
        sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
                 "den Datenordner zu erraten. Siehe .env.local.")
    return os.path.abspath(konfiguriert)


def ablage(data=None):
    return os.path.join(data or datenordner(), "rechte-erklaerungen.json")


def _read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def herkunft(plan, projects=None):
    """Was der Herkunftsnachweis des Plans sagt -- Datensatz und Rechte."""
    doc = _read_json(os.path.join(projects or PROJECTS, plan,
                                  "german-catalog-source.json")) or {}
    return {"datensatz": doc.get("dataset"),
            "quelldatei": doc.get("source_file"),
            "rechte": doc.get("usage_rights") or {}}


def gesperrt(plan, projects=None):
    """Sagt der eigene Nachweis des Plans ausdruecklich Nein zur Nutzung?"""
    return herkunft(plan, projects).get("rechte", {}).get(
        "commercial_use_allowed") is False


def laden(data=None):
    doc = _read_json(ablage(data))
    if not isinstance(doc, dict):
        return {"schema": SCHEMA, "erklaerungen": []}
    doc.setdefault("erklaerungen", [])
    return doc


def erklaerung_fuer(plan, data=None, projects=None):
    """Die geltende Erklaerung fuer diesen Plan, oder None.

    Erst die plan-eigene -- eine Entscheidung fuer ein einzelnes Haus schlaegt
    die pauschale des Datensatzes, in beide Richtungen. Dann die des
    Datensatzes. Bei mehreren gilt die juengste.
    """
    eintraege = laden(data)["erklaerungen"]
    eigen = [e for e in eintraege
             if e.get("geltung") == "plan" and e.get("wert") == plan]
    if eigen:
        return sorted(eigen, key=lambda e: e.get("wann") or "")[-1]
    datensatz = herkunft(plan, projects).get("datensatz")
    if not datensatz:
        return None
    passend = [e for e in eintraege
               if e.get("geltung") == "datensatz" and e.get("wert") == datensatz]
    if not passend:
        return None
    return sorted(passend, key=lambda e: e.get("wann") or "")[-1]


def erlaubt(plan, data=None, projects=None):
    """True nur bei einem ausdruecklichen Ja. Kein Eintrag heisst Nein."""
    eintrag = erklaerung_fuer(plan, data, projects)
    return bool(eintrag and eintrag.get("antwort") == "ja")


def erklaeren(antwort, grund, geltung, wert, wer="", data=None, projects=None):
    """Eine Antwort festhalten. Gibt den geschriebenen Eintrag zurueck."""
    if antwort not in ("ja", "nein"):
        raise ValueError("antwort muss 'ja' oder 'nein' sein")
    if not (grund or "").strip():
        raise ValueError("Ohne Begruendung keine Erklaerung")
    if geltung not in ("plan", "datensatz"):
        raise ValueError("geltung muss 'plan' oder 'datensatz' sein")
    if not (wert or "").strip():
        raise ValueError("wert fehlt")

    # Was der Nachweis JETZT sagt, wandert in den Eintrag. Spaeter soll
    # nachlesbar sein, wogegen entschieden wurde -- nicht nur, dass entschieden
    # wurde.
    if geltung == "plan":
        sagte = herkunft(wert, projects).get("rechte", {})
    else:
        sagte = {"datensatz": wert}

    eintrag = {
        "geltung": geltung,
        "wert": wert,
        "antwort": antwort,
        "grund": grund.strip(),
        "wer": (wer or "").strip() or "unbenannt",
        "wann": datetime.datetime.now().isoformat(timespec="seconds"),
        "herkunft_sagte": sagte,
    }
    doc = laden(data)
    doc["schema"] = SCHEMA
    doc["erklaerungen"].append(eintrag)
    ziel = ablage(data)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, ensure_ascii=False, indent=1)
    return eintrag


def zeile(eintrag):
    """Eine Zeile fuer Menschen -- in Protokollen und in der Oberflaeche."""
    if not eintrag:
        return "keine Erklaerung"
    return "%s (%s) am %s durch %s: %s" % (
        "Ja" if eintrag.get("antwort") == "ja" else "Nein",
        "Datensatz «%s»" % eintrag["wert"] if eintrag.get("geltung") == "datensatz"
        else "dieser Plan",
        (eintrag.get("wann") or "")[:16].replace("T", " "),
        eintrag.get("wer") or "unbenannt",
        eintrag.get("grund") or "")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan")
    parser.add_argument("--datensatz")
    parser.add_argument("--ja", action="store_true")
    parser.add_argument("--nein", action="store_true")
    parser.add_argument("--grund", default="")
    parser.add_argument("--wer", default="")
    parser.add_argument("--zeigen", action="store_true")
    args = parser.parse_args(argv)

    if args.zeigen or not (args.ja or args.nein):
        doc = laden()
        if not doc["erklaerungen"]:
            print("Keine Erklaerungen abgelegt (%s)." % ablage())
            return 0
        print("%d Erklaerung(en) in %s:" % (len(doc["erklaerungen"]), ablage()))
        for eintrag in doc["erklaerungen"]:
            print("  " + zeile(eintrag))
        if args.plan:
            print("")
            print("Fuer %s gilt: %s" % (args.plan, zeile(erklaerung_fuer(args.plan))))
        return 0

    if args.ja and args.nein:
        sys.exit("--ja und --nein zugleich geht nicht.")
    if bool(args.plan) == bool(args.datensatz):
        sys.exit("Entweder --plan ODER --datensatz.")

    try:
        eintrag = erklaeren("ja" if args.ja else "nein", args.grund,
                            "plan" if args.plan else "datensatz",
                            args.plan or args.datensatz, args.wer)
    except ValueError as fehler:
        sys.exit(str(fehler))
    print("[rechte] " + zeile(eintrag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
