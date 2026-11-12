#!/usr/bin/env python3
"""Publish finished renders into the born2thrill catalogue.

The catalogue links a picture to a plan by FILENAME: an attachment whose slug
starts with "<plan_id>-" belongs to that plan and shows up in its record sheet.
So publishing is: rename to the convention, upload, verify. This script does
all three and is safe to run twice -- a picture already on the site is skipped,
not duplicated.

    set WP_USER=yeary
    set WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
    python publish-renders.py --plan onehalfstorey_020 --dir ..\\exports\\codex-handoff-...

The password is a WordPress *Application Password* (Users -> Profile ->
Application Passwords), never the account password. Create it yourself; it is
not something this script or anyone else should generate for you.

Flags:
    --plan       plan_id exactly as it appears in kon_grundrisse
    --dir        folder of .png/.jpg renders to publish
    --site       default https://born2thrill.de
    --send       also tick "an Kunden" on every picture uploaded in this run
    --dry-run    show what would be uploaded, touch nothing

Naming: files are uploaded as "<plan_id>-<NN>-<name>". Keep "exterior" in the
name of exterior shots -- the card cover picture prefers them.
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SUITE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rechte  # noqa: E402  -- die abgegebene Rechteerklaerung, siehe rechte.py

DEFAULT_SITE = "https://born2thrill.de"
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


def slugify(text):
    """WordPress' own slug rules, near enough to predict the resulting slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def _lade_env_local():
    """WP_USER / WP_APP_PASSWORD aus .env.local nachziehen.

    Die Zugangsdaten lagen die ganze Zeit in
    born2thrill-local-workbench/.env.local -- dort legt sie der Workbench ab.
    Dieses Skript hat aber nur os.environ gelesen, also war in jeder frischen
    Shell "WP_USER and WP_APP_PASSWORD must be set", obwohl sie eingerichtet
    waren. Deshalb ist bis heute kein einziges Bild hochgeladen worden.

    Bereits gesetzte Umgebungsvariablen gewinnen -- die Datei fuellt nur
    Luecken.
    """
    pfad = os.path.join(SUITE, "born2thrill-local-workbench", ".env.local")
    if not os.path.exists(pfad):
        return
    try:
        with open(pfad, encoding="utf-8-sig") as handle:
            for zeile in handle:
                zeile = zeile.strip()
                if not zeile or zeile.startswith("#") or "=" not in zeile:
                    continue
                name, _, wert = zeile.partition("=")
                name = name.strip()
                if name in ("WP_USER", "WP_APP_PASSWORD") and not os.environ.get(name):
                    os.environ[name] = wert.strip().strip('"').strip("'")
    except Exception:
        pass


def auth_header():
    _lade_env_local()
    user = os.environ.get("WP_USER")
    password = os.environ.get("WP_APP_PASSWORD")
    if not user or not password:
        sys.exit(
            "WP_USER and WP_APP_PASSWORD must be set.\n"
            "Create an Application Password under Users -> Profile in wp-admin."
        )
    raw = "{}:{}".format(user, password.replace(" ", ""))
    return "Basic " + base64.b64encode(raw.encode("utf-8")).decode("ascii")


def request(url, method="GET", body=None, headers=None):
    req = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:400]
        raise SystemExit("{} {} -> HTTP {}\n{}".format(method, url, err.code, detail))


def existing_slugs(site, plan):
    """What is already on the site for this plan."""
    url = "{}/wp-json/b2t/v1/bilder?plan={}".format(site, urllib.parse.quote(plan))
    return {shot["name"] for shot in request(url)}


def _katalog_ids(site):
    return {row["id"] for row in request(site + "/wp-json/b2t/v1/grundrisse")}


def _blender_pfad(plan):
    """The modern exterior .blend of the go-baseline build, as the hand INSERTs had it."""
    daten = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"
    ordner = os.path.join(daten, "corrections", plan, "renders", "go-baseline")
    try:
        mass = json.load(open(os.path.join(SUITE, "floorplan-simplifier", "projects", plan,
                                           "gebaeudemass.json"), encoding="utf-8-sig"))
        dach = mass.get("roof_type_modern") or "flachdach"
    except Exception:
        dach = "flachdach"
    pfad = os.path.join(ordner, "exterior-%s-baseline.blend" % dach)
    return pfad if os.path.exists(pfad) else ""


def check_plan(site, plan, dry_run=False):
    """Make sure the catalogue has this plan -- and create the row if it does not.

    A typo is the one failure that is expensive: the upload succeeds, the
    pictures land under a plan nobody will ever search for. So a plan id that
    has no project folder is still refused. A REAL new house, though, used to
    stop here too and needed an INSERT typed by hand in WP Data Access
    (katalogzeile-automatisch-v1, Rainer 2026-10-20: "you have to get this
    fixed why all the extra work"). Now the row is built by katalogzeile.py --
    the rule of the original import -- and sent to b2t/v1/grundriss-anlegen,
    which only ever INSERTs a missing row.
    """
    ids = _katalog_ids(site)
    if plan in ids:
        return
    ordner = os.path.join(SUITE, "floorplan-simplifier", "projects", plan)
    if not os.path.exists(os.path.join(ordner, "annotations.json")):
        near = sorted(i for i in ids if plan.split("_")[0] in i)[:6]
        sys.exit(
            "No plan '{}' in the catalogue ({} plans known), and no project folder "
            "either.{}".format(plan, len(ids),
                               "\nDid you mean: " + ", ".join(near) if near else ""))

    import katalogzeile
    zeile = katalogzeile.zeile_aus_projekt(ordner, _blender_pfad(plan))
    print("'{}' fehlt im Katalog -- neue Zeile:".format(plan))
    for key in ("plan_id", "haustyp", "geschosse", "keller", "raeume", "schlafzimmer",
                "kinderzimmer", "baeder", "ausstattung", "hash", "blender_pfade"):
        print("  {:13s} {}".format(key, zeile.get(key)))
    if dry_run:
        print("  (dry run: nicht angelegt)\n")
        return

    body = json.dumps(zeile).encode("utf-8")
    req = urllib.request.Request(site + "/wp-json/b2t/v1/grundriss-anlegen", data=body,
                                 method="POST")
    req.add_header("Authorization", auth_header())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            antwort = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:400]
        if err.code == 404 and "rest_no_route" in detail:
            sys.exit(
                "\nDie Route b2t/v1/grundriss-anlegen fehlt auf dem Server.\n"
                "Einbauen: born2thrill-local-workbench/wordpress/b2t-katalog-freigabe.php\n"
                "          nach wp-content/mu-plugins/ hochladen (ersetzt die alte Datei).")
        sys.exit("Katalogzeile anlegen: HTTP {}\n{}".format(err.code, detail))
    print("  -> {}".format("angelegt" if antwort.get("angelegt") else "war schon da"))
    if plan not in _katalog_ids(site):
        sys.exit("Die Zeile wurde gemeldet, steht aber nicht in der Katalogliste -- "
                 "nichts hochgeladen.")
    print("")


LEDGERS = (
    os.path.join(SUITE, "born2thrill-local-workbench", "data", "simplifier-v2",
                 "corpus-ledger.json"),
    os.path.join(SUITE, "born2thrill-local-workbench", "data", "simplifier-v1",
                 "corpus-ledger.json"),
)

REFUSAL = "\nABGELEHNT: --send wuerde Bilder von '{}' an Kunden freigeben.\nDas Ledger sagt corpus_status={}, commercial_generator_eligible={}.\nAGENTS.md: eingeschraenkte Referenzen werden nicht dadurch kommerziell\nnutzbar, dass sie importiert oder bearbeitet wurden.\n\nHochladen ohne --send ist erlaubt. Willst du wirklich an Kunden\nfreigeben, dann bewusst mit  --rechte-bestaetigt"


def corpus_entry(plan):
    """What the newest corpus ledger says about this plan, or None.

    AGENTS.md makes one question mandatory for any path that can publish:
    "Can any changed path generate, publish, or email geometry without matching
    an approved corrected corpus reference?  The required answer is no."

    Until now the answer here was yes. The only gate was whether the plan_id
    existed in the catalogue; nothing consulted the ledger. So --send could
    release pictures of a plan the ledger marks commercial_generator_eligible
    false -- which on 2026-08-20 is every one of its 310 entries, approved_real
    being 0.
    """
    newest, stamp = None, ""
    for path in LEDGERS:
        try:
            with open(path, encoding="utf-8-sig") as handle:
                document = json.load(handle)
        except Exception:
            continue
        if document.get("generated_at", "") >= stamp:
            newest, stamp = document, document.get("generated_at", "")
    if not newest:
        return None
    for entry in newest.get("projects") or []:
        if entry.get("project_id") == plan:
            return entry
    return None


def check_rights(plan, sending, override):
    """Refuse customer release of a plan the corpus does not clear.

    Uploading into the media library stays allowed -- that is internal, and
    blocking it would stop the catalogue being usable at all -- but it says
    plainly what the ledger thinks. Releasing TO CUSTOMERS is the line, and it
    is fail-closed: no ledger entry is a refusal, not a pass.
    """
    entry = corpus_entry(plan)
    status = (entry or {}).get("corpus_status", "nicht im Ledger")
    eligible = (entry or {}).get("commercial_generator_eligible")

    if eligible is not True:
        print("  ACHTUNG  {}: corpus_status={}, commercial_generator_eligible={}"
              .format(plan, status, eligible))
        print("           Interne Referenz, keine Kundenware.")
    if not sending or eligible is True:
        return
    # Eine einmal abgegebene Erklaerung zaehlt wie das Flag -- dieselbe
    # Entscheidung, nur nicht bei jedem Haus neu getippt (rechte.py).
    erklaerung = rechte.erklaerung_fuer(plan)
    if erklaerung and erklaerung.get("antwort") == "ja":
        print("  Rechteerklaerung liegt vor: %s" % rechte.zeile(erklaerung))
        return
    if erklaerung and erklaerung.get("antwort") == "nein":
        sys.exit("\nABGELEHNT: fuer '%s' wurde ausdruecklich Nein erklaert.\n  %s"
                 % (plan, rechte.zeile(erklaerung)))
    if override:
        print("  Rechte per --rechte-bestaetigt uebersteuert. Deine "
              "Entscheidung, und sie steht in diesem Protokoll.")
        return
    sys.exit(REFUSAL.format(plan, status, eligible))


# Technical passes the renderer writes beside each picture. They exist so the
# verifier can measure depth and find edges; they are not photographs of a house
# and must never reach the catalogue.
TECHNICAL_PASS_SUFFIXES = ("-depth", "-edge", "-mask")

# Der Rohbau-Nachweis aus dem Bau. Er zeigt weisse Kloetze ohne Moebel und
# ohne Material -- ein Beleg dafuer, dass die Geometrie stimmt, kein Bild
# eines Hauses. Rainer, 2026-09-01, zu
# german_catalog_review_bungalow_3_4_5_b_120: "es heisst ich muss die bilder
# freigeben das sind aber keine Bilder."
#
# Bis hierher standen nur die drei technischen Paesse auf der Liste. Am
# 2026-08-26 gingen so drei graue Rohbauten in den Kundenkatalog, und
# bungalow_001s Bild id 80 steht bis heute so drin.
BASELINE_SUFFIX = "-baseline"


def collect(folder, include_passes=False):
    """The pictures in a delivery folder -- and only the pictures.

    Measured 2026-08-20 on onehalfstorey_029: the folder holds 14 PNGs, but 10
    of them are depth, edge and mask passes. Uploading the lot would have put
    grey depth maps and black-and-white edge maps into the customer catalogue
    next to the renders, numbered as if they belonged there.
    """
    names = []
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(IMAGE_SUFFIXES):
            continue
        stem = os.path.splitext(name)[0].lower()
        if not include_passes and stem.endswith(TECHNICAL_PASS_SUFFIXES):
            continue
        if stem.endswith(BASELINE_SUFFIX):
            continue
        names.append(name)
    if not names:
        sys.exit(
            "Keine Bilder in {}.\n"
            "Rohbau-Renders (-baseline) und technische Paesse zaehlen nicht: "
            "das sind\nkeine Bilder eines Hauses. Erst eine Codex-Lieferung "
            "annehmen.".format(folder))
    return names


def target_name(plan, index, filename):
    """<plan>-<NN>-<name>.<ext>, keeping any numbering the file already has."""
    stem, ext = os.path.splitext(filename)
    if stem.startswith(plan + "-"):
        return filename
    if not re.match(r"^\d{2}-", stem):
        stem = "{:02d}-{}".format(index, stem)
    return "{}-{}{}".format(plan, slugify(stem), ext.lower())


def upload(site, path, name, auth):
    """WordPress takes the raw bytes; the filename decides the slug."""
    with open(path, "rb") as handle:
        payload = handle.read()
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return request(
        site + "/wp-json/wp/v2/media",
        method="POST",
        body=payload,
        headers={
            "Authorization": auth,
            "Content-Type": mime,
            "Content-Disposition": 'attachment; filename="{}"'.format(name),
        },
    )


def release(site, attachment_id, auth):
    request(
        site + "/wp-json/b2t/v1/freigabe",
        method="POST",
        body=json.dumps({"id": attachment_id, "send": True}).encode("utf-8"),
        headers={"Authorization": auth, "Content-Type": "application/json"},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--dir", required=True)
    parser.add_argument("--site", default=DEFAULT_SITE)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mit-hilfsbildern", dest="mit_hilfsbildern",
                        action="store_true",
                        help="auch die technischen depth/edge/mask-Bilder hochladen")
    parser.add_argument("--rechte-bestaetigt", action="store_true",
                        dest="rechte_bestaetigt",
                        help="bewusst an Kunden freigeben, obwohl das Ledger den Plan nicht als kommerziell nutzbar fuehrt")
    args = parser.parse_args()

    site = args.site.rstrip("/")
    folder = os.path.abspath(args.dir)
    if not os.path.isdir(folder):
        sys.exit("Not a folder: " + folder)

    files = collect(folder, include_passes=args.mit_hilfsbildern)
    check_plan(site, args.plan, dry_run=args.dry_run)
    check_rights(args.plan, args.send, args.rechte_bestaetigt)
    # The lookup is read-only, so a dry run does it too -- otherwise it would
    # claim it was about to upload pictures that are already on the site.
    already = existing_slugs(site, args.plan)
    auth = None if args.dry_run else auth_header()

    print("{}  ->  {}".format(folder, site))
    print("plan {} already has {} picture(s)\n".format(args.plan, len(already)))

    uploaded, skipped = 0, 0
    for index, filename in enumerate(files, start=1):
        name = target_name(args.plan, index, filename)
        slug = slugify(os.path.splitext(name)[0]).replace(args.plan + "-", "", 1)
        if slug in already:
            print("  skip    {}  (already published)".format(name))
            skipped += 1
            continue
        if args.dry_run:
            print("  would   {}".format(name))
            uploaded += 1
            continue
        media = upload(site, os.path.join(folder, filename), name, auth)
        note = ""
        if args.send:
            release(site, media["id"], auth)
            note = "  [an Kunden]"
        print("  upload  {}  id={}{}".format(name, media["id"], note))
        uploaded += 1

    print("\n{} uploaded, {} skipped".format(uploaded, skipped))

    if args.dry_run:
        return

    # Say what the site actually holds now, not what we think we sent.
    shots = request("{}/wp-json/b2t/v1/bilder?plan={}".format(
        site, urllib.parse.quote(args.plan)))
    print("\n{} now has {} picture(s) in the catalogue:".format(args.plan, len(shots)))
    for shot in shots:
        print("  {}{}".format(shot["name"], "  [an Kunden]" if shot["send"] else ""))
    print("\n{}/grundriss-katalog/  ->  search {}".format(site, args.plan))


if __name__ == "__main__":
    main()
