#!/usr/bin/env python3
"""Approve ONE plan for commercial use, with the evidence recorded.

The corpus ledger marks all 310 projects commercial_generator_eligible false and
approved_real 0, so publish-renders.py refuses every customer release. This is
the only path that changes that, and it changes one plan at a time on purpose.

Approval binds to the annotation it was granted for: the sha256 is stored, so if
the plan is re-annotated afterwards the approval no longer matches the drawing it
was granted for and has to be given again. That is the ledger's own policy
`commercial_approval_requires_explicit_rights_and_quality` made real.

A plan whose provenance record DENIES commercial use is refused. The Aug-01
export approved 55 german_catalog_* projects with the reason "real plan has
explicit generator rights", while their own german-catalog-source.json says
license rights-unconfirmed and commercial_use_allowed false. Whatever happened
there should not be repeatable by accident: overriding needs --rechte-bestaetigt,
and the override is written into the record with what the provenance actually
said.

    python approve-plan.py --list
    python approve-plan.py --show bungalow_039
    python approve-plan.py bungalow_039 --reason "eigener Entwurf, Rechte bei uns"
    python approve-plan.py bungalow_039 --revoke --reason "doch ein Fremdplan"
"""

import argparse
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rechte  # noqa: E402  -- die abgegebene Rechteerklaerung, siehe rechte.py

SUITE = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(SUITE, "born2thrill-local-workbench", "data",
                      "simplifier-v2", "corpus-ledger.json")
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


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def annotation_hash(plan):
    """The same canonical hash the compiler and the annotator use."""
    doc = read_json(os.path.join(PROJECTS, plan, "annotations.json"))
    if doc is None:
        return None
    canonical = json.dumps(doc, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def provenance(plan):
    """What the project's own source record says about commercial use."""
    doc = read_json(os.path.join(PROJECTS, plan, "german-catalog-source.json"))
    if not doc:
        return None
    return doc.get("usage_rights") or {}


def delivery(plan):
    """The certified delivery, or None when nothing has been built."""
    folder = os.path.join(DATA, "corrections", plan, "renders", "go-baseline")
    manifest = read_json(os.path.join(folder, "delivery-manifest.json"))
    if not manifest:
        return None
    return {"styles": manifest.get("verified_styles"),
            "artifacts": len(manifest.get("artifacts") or []),
            "folder": folder}


def save(ledger):
    ledger["counts"] = {
        "annotated_reference": sum(1 for e in ledger["projects"]
                                   if e.get("corpus_status") == "annotated_reference"),
        "approved_real": sum(1 for e in ledger["projects"]
                             if e.get("corpus_status") == "approved_real"),
    }
    temporary = LEDGER + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=1, ensure_ascii=False)
    os.replace(temporary, LEDGER)


def show(plan, ledger):
    entry = next((e for e in ledger.get("projects") or []
                  if e.get("project_id") == plan), None)
    print("  " + plan)
    if not entry:
        print("    im Ledger        : nein")
    else:
        print("    im Ledger        : %s, commercial=%s"
              % (entry.get("corpus_status"),
                 entry.get("commercial_generator_eligible")))
    rights = provenance(plan)
    if rights is None:
        print("    Herkunftsnachweis: keiner (Herkunft undokumentiert)")
    else:
        print("    Herkunftsnachweis: license=%s commercial_use_allowed=%s"
              % (rights.get("license"), rights.get("commercial_use_allowed")))
    built = delivery(plan)
    if not built:
        print("    gebaut           : nein -- es gibt nichts anzusehen")
    else:
        print("    gebaut           : %d Artefakte, Stile %s"
              % (built["artifacts"], built["styles"]))
        print("    Bilder liegen in : " + built["folder"])
    current = annotation_hash(plan)
    stamped = (entry or {}).get("annotation_sha256")
    if stamped and current and stamped != current:
        print("    ACHTUNG          : Annotation hat sich seit dem Eintrag geaendert")
    return entry


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--list", action="store_true",
                        help="was zur Freigabe ansteht")
    parser.add_argument("--show", metavar="PLAN")
    parser.add_argument("--reason", help="warum du die Rechte hast (wird gespeichert)")
    parser.add_argument("--revoke", action="store_true")
    parser.add_argument("--rechte-bestaetigt", dest="override", action="store_true",
                        help="trotz gegenteiligem Herkunftsnachweis freigeben")
    parser.add_argument("--by", default=os.environ.get("USERNAME") or "unbekannt")
    args = parser.parse_args()

    ledger = read_json(LEDGER)
    if not ledger:
        sys.exit("Ledger nicht lesbar: " + LEDGER)

    if args.show:
        show(args.show, ledger)
        return 0

    if args.list or not args.plan:
        built, rest = [], 0
        for entry in ledger["projects"]:
            plan = entry["project_id"]
            if entry.get("commercial_generator_eligible"):
                continue
            if delivery(plan):
                built.append(plan)
            else:
                rest += 1
        print("Zur Freigabe bereit (gebaut, Bilder ansehbar): %d" % len(built))
        print("")
        for plan in built:
            show(plan, ledger)
        print("")
        print("Weitere %d Projekte sind nicht gebaut -- ohne Bilder gibt es" % rest)
        print("nichts zu beurteilen. Erst bauen, dann freigeben.")
        print("")
        print("  python approve-plan.py <plan> --reason \"...\"")
        return 0

    plan = args.plan
    entry = next((e for e in ledger["projects"] if e.get("project_id") == plan), None)
    if entry is None:
        # Das Ledger wird von einem Export erzeugt (harden-simplifier-export.mjs)
        # und kennt nur Projekte bis zu diesem Stand. Ein danach annotierter Plan
        # ist dort schlicht noch nicht eingetragen -- 72 von 350 Projekten, am
        # 2026-09-20 als "steht nicht im Ledger" abgewiesen, obwohl nichts
        # gegen sie sprach (Rainer: "they are my bosses own plans"). Der Eintrag
        # entsteht hier im selben Zustand, den der Export ihm gegeben haette;
        # gespeichert wird erst, wenn die Freigabe unten wirklich durchgeht.
        if args.revoke:
            sys.exit("'%s' steht nicht im Ledger -- es gibt nichts zurueckzuziehen." % plan)
        first_hash = annotation_hash(plan)
        if first_hash is None:
            sys.exit("'%s' steht nicht im Ledger und hat keine annotations.json "
                     "in projects/ -- es gibt nichts freizugeben." % plan)
        entry = {
            "project_id": plan,
            "source_kind": "real_annotated",
            "corpus_status": "annotated_reference",
            "internal_reference_eligible": True,
            "commercial_generator_eligible": False,
            "quality_status": None,
            "annotation_sha256": first_hash,
            "annotation_recorded_at": None,
            "approval_recorded_at": None,
            "unchanged_until_hash_changes": True,
            "last_seen_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "reason": "vom Ledger-Export noch nicht erfasst; Eintrag von approve-plan.py angelegt",
        }
        ledger["projects"].append(entry)
        print("[ledger] %s war noch nicht im Ledger (Stand %s) -- neuer Eintrag."
              % (plan, str(ledger.get("generated_at") or "?")[:10]))
    if not args.reason:
        sys.exit("--reason fehlt. Der Grund wird gespeichert und ist der Sinn "
                 "der Freigabe.")

    if args.revoke:
        entry.update({
            "corpus_status": "annotated_reference",
            "commercial_generator_eligible": False,
            "quality_status": None,
            "approval_recorded_at": None,
            "reason": args.reason,
            "revoked_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "revoked_by": args.by,
        })
        save(ledger)
        print("[ledger] %s zurueckgezogen: %s" % (plan, args.reason))
        return 0

    rights = provenance(plan)
    # Eine abgegebene Rechteerklaerung zaehlt wie das Flag -- sie IST dieselbe
    # Erklaerung, nur einmal gegeben statt 55 Mal getippt, und mit Name, Datum
    # und dem widersprechenden Nachweis im Eintrag (rechte.py).
    erklaerung = rechte.erklaerung_fuer(plan)
    if erklaerung and erklaerung.get("antwort") == "ja":
        print("[rechte] Erklaerung liegt vor: %s" % rechte.zeile(erklaerung))
        entry["rights_declaration"] = erklaerung
    elif erklaerung and erklaerung.get("antwort") == "nein":
        print("ABGELEHNT: du hast fuer %s ausdruecklich Nein erklaert." % plan)
        print("  %s" % rechte.zeile(erklaerung))
        print("Meinung geaendert? python rechte.py --plan %s --ja --grund \"...\""
              % plan)
        return 1
    elif rights and rights.get("commercial_use_allowed") is False and not args.override:
        print("ABGELEHNT: der Herkunftsnachweis von %s sagt" % plan)
        print("  license=%s  commercial_use_allowed=%s  generator_export_allowed=%s"
              % (rights.get("license"), rights.get("commercial_use_allowed"),
                 rights.get("generator_export_allowed")))
        print("AGENTS.md: eingeschraenkte Referenzen werden nicht dadurch")
        print("kommerziell nutzbar, dass sie bearbeitet wurden.")
        print("Wenn du die Rechte trotzdem hast: --rechte-bestaetigt")
        print("Oder einmal erklaeren, dann fragt es nicht wieder -- im Schritt")
        print("\"Hochladen & Freigeben\", oder:")
        print("  python rechte.py --plan %s --ja --grund \"...\"" % plan)
        datensatz = rechte.herkunft(plan).get("datensatz")
        if datensatz:
            print("  python rechte.py --datensatz \"%s\" --ja --grund \"...\""
                  % datensatz)
        return 1

    built = delivery(plan)
    if not built:
        print("Hinweis: %s ist nicht gebaut -- du gibst etwas frei, das du "
              "nicht angesehen hast." % plan)

    current = annotation_hash(plan)
    entry.update({
        "corpus_status": "approved_real",
        "commercial_generator_eligible": True,
        "internal_reference_eligible": True,
        "quality_status": "passed" if built else "not_built",
        "annotation_sha256": current,
        "approval_recorded_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "approved_by": args.by,
        "unchanged_until_hash_changes": True,
        "reason": args.reason,
    })
    if rights and rights.get("commercial_use_allowed") is False:
        entry["rights_override"] = {
            "provenance_said": dict(rights),
            "overridden_by": args.by,
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    save(ledger)
    print("[ledger] %s freigegeben von %s" % (plan, args.by))
    print("         Grund: " + args.reason)
    print("         gebunden an Annotation %s" % (current or "-")[:16])
    print("         approved_real jetzt: %d" % ledger["counts"]["approved_real"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
