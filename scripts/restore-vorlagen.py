#!/usr/bin/env python3
"""Put the 9 recoverable source plans back, verified against their hashes.

The Drive survey (plans/HANDOFF-2026-08-19.md, "Google Drive") established that
of 133 projects without a raster, exactly 9 record where they came from. This
turns that finding into something runnable, because the matching rule is easy
to get wrong by hand:

  DO NOT derive the filename from the project id. The id replaces "-" with "_"
  and that is not reversible -- checked against all 55 catalogue projects, 12
  disagree (id ..._3_2_1_b_100_1 suggests 3.2.1_b_100_1.pdf, the real file is
  3.2.1_b_100-1.pdf). Read source_file from german-catalog-source.json instead,
  then verify source_sha256.

This script DOWNLOADS NOTHING. Fetching from Drive is yours to do; it prints
exactly which files to fetch and from where. Point it at the folder you put
them in and it checks and places them.

    python restore-vorlagen.py --list
    python restore-vorlagen.py --from ~/Downloads            # dry run
    python restore-vorlagen.py --from ~/Downloads --apply

A file whose sha256 does not match the recorded one is REFUSED, not copied --
a wrong template silently in place would be worse than a missing one, because
everything downstream would treat it as the truth. Nothing here writes to
annotations.json.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
LIST = os.path.join(SUITE, "floorplan-simplifier", "plans", "fehlende-vorlagen.json")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load():
    with open(LIST, encoding="utf-8-sig") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="source", help="Ordner mit den geladenen PDFs")
    parser.add_argument("--list", action="store_true", help="nur zeigen, was zu holen ist")
    parser.add_argument("--apply", action="store_true", help="wirklich kopieren")
    parser.add_argument("--force", action="store_true",
                        help="vorhandene original.pdf ueberschreiben")
    args = parser.parse_args()

    document = load()
    entries = document["recoverable"]

    if args.list or not args.source:
        print("Von Google Drive zu holen (%s):\n" % document["drive_root"])
        for entry in entries:
            print("  %s" % entry["drive_path"])
            print("      -> %s   sha256 %s"
                  % (entry["plan_id"], entry["source_sha256"][:16]))
        print("\n%d Datei(en). Danach:  python restore-vorlagen.py --from <ordner>"
              % len(entries))
        print("Hinweis: alle %d sind im Ledger commercial_generator_eligible=false."
              % len(entries))
        return 0

    source = os.path.abspath(args.source)
    if not os.path.isdir(source):
        sys.exit("Kein Ordner: " + source)

    ok = missing = mismatch = skipped = 0
    for entry in entries:
        name = entry["drive_path"].rsplit("/", 1)[-1]
        candidate = os.path.join(source, name)
        target = os.path.join(SUITE, entry["target"])

        if not os.path.exists(candidate):
            print("  fehlt      %-46s (%s)" % (entry["plan_id"][:46], name))
            missing += 1
            continue

        digest = sha256(candidate)
        if digest != entry["source_sha256"]:
            print("  ABGELEHNT  %-46s sha256 stimmt nicht" % entry["plan_id"][:46])
            print("             erwartet %s" % entry["source_sha256"][:32])
            print("             gefunden %s" % digest[:32])
            mismatch += 1
            continue

        if os.path.exists(target) and not args.force:
            print("  vorhanden  %-46s (--force zum Ersetzen)" % entry["plan_id"][:46])
            skipped += 1
            continue

        if args.apply:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(candidate, target)
            print("  kopiert    %-46s -> %s" % (entry["plan_id"][:46], entry["target"]))
        else:
            print("  wuerde     %-46s -> %s" % (entry["plan_id"][:46], entry["target"]))
        ok += 1

    print("\n%d in Ordnung, %d fehlen, %d abgelehnt, %d uebersprungen%s"
          % (ok, missing, mismatch, skipped,
             "" if args.apply else "   (Probelauf, --apply zum Ausfuehren)"))
    if ok and args.apply:
        print("Danach im Annotator das Gebaeudemass ziehen -- erst dann ist ein Haus baubar.")
    return 1 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
