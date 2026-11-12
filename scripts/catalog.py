#!/usr/bin/env python3
"""One entry point for the render pipeline. Three verbs.

    python catalog.py status onehalfstorey_020
    python catalog.py blends onehalfstorey_020 <folder with the .blend files>
    python catalog.py images onehalfstorey_020 <folder Codex handed back>

`status` is read-only and needs no credentials. Run it whenever you are not
sure what has happened -- it prints every stage of the pipeline, what is done,
and the exact next command. `blends` and `images` need WP_USER and
WP_APP_PASSWORD (a WordPress Application Password).

Nothing here is destructive. `images` skips pictures already published;
`blends` overwrites the stored path list for that plan and nothing else.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("B2T_SITE", "https://born2thrill.de").rstrip("/")
HERE = os.path.dirname(os.path.abspath(__file__))
TICK, CROSS, DASH = "[x]", "[!]", "[ ]"


def get(path):
    with urllib.request.urlopen(SITE + path) as response:
        return json.loads(response.read().decode("utf-8"))


def _lade_env_local():
    """WP_USER / WP_APP_PASSWORD aus .env.local nachziehen.

    Genau derselbe Fehler wie in publish-renders.py: die Zugangsdaten liegen in
    born2thrill-local-workbench/.env.local, dieses Skript las aber nur
    os.environ -- also "WP_USER and WP_APP_PASSWORD must be set" in jeder
    frischen Shell, obwohl das Application Password laengst eingerichtet war.
    Dort behoben am 2026-08-19, hier nicht mitgezogen; gemerkt am 2026-08-20,
    als catalog.py blends bungalow_039 genau daran abbrach.
    """
    suite = os.path.dirname(os.path.dirname(HERE))
    pfad = os.path.join(suite, "born2thrill-local-workbench", ".env.local")
    try:
        with open(pfad, encoding="utf-8-sig") as handle:
            for zeile in handle:
                if "=" not in zeile or zeile.lstrip().startswith("#"):
                    continue
                name, _, wert = zeile.partition("=")
                name = name.strip()
                if name in ("WP_USER", "WP_APP_PASSWORD") and not os.environ.get(name):
                    os.environ[name] = wert.strip().strip('"').strip("'")
    except OSError:
        pass


def post(path, payload):
    _lade_env_local()
    user = os.environ.get("WP_USER")
    password = os.environ.get("WP_APP_PASSWORD")
    if not user or not password:
        sys.exit("WP_USER and WP_APP_PASSWORD must be set (Application Password).")
    raw = "{}:{}".format(user, password.replace(" ", ""))
    request = urllib.request.Request(
        SITE + path, data=json.dumps(payload).encode("utf-8"), method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization",
                       "Basic " + base64.b64encode(raw.encode()).decode("ascii"))
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        sys.exit("POST {} -> HTTP {}\n{}".format(
            path, err.code, err.read().decode("utf-8", "replace")[:300]))


def record(plan):
    for row in get("/wp-json/b2t/v1/grundrisse"):
        if row["id"] == plan:
            return row
    sys.exit("No plan '{}' in the catalogue.".format(plan))


def status(plan):
    row = record(plan)
    shots = get("/wp-json/b2t/v1/bilder?plan=" + urllib.parse.quote(plan))
    paths = row.get("bp") or []
    on_disk = [p for p in paths if os.path.exists(p)]
    released = [s for s in shots if s["send"]]
    expected = 4 if int(row["f"]) > 1 else 3

    print("\n  {}   {}, {} Geschoss(e), {} Raeume".format(
        plan, row["t"], row["f"], row["r"]))
    print("  " + "-" * 66)

    steps = []
    steps.append((
        bool(paths),
        "Blender-Dateien registriert",
        "{} Pfad(e) in der Datenbank".format(len(paths)) if paths else "keine",
        "catalog.py blends {} <ordner>".format(plan)))
    steps.append((
        bool(paths) and len(on_disk) == len(paths),
        "Blender-Dateien vorhanden",
        "{}/{} auf dieser Maschine".format(len(on_disk), len(paths)) if paths else "-",
        "die Pfade zeigen ins Leere -- neu registrieren oder Dateien holen"))
    steps.append((
        bool(shots),
        "Renderings hochgeladen",
        "{} Bild(er)".format(len(shots)) if shots else "keine",
        "catalog.py images {} <ordner>".format(plan)))
    steps.append((
        bool(released),
        "Fuer Kunden freigegeben",
        "{}/{} angehakt".format(len(released), len(shots)) if shots else "-",
        "auf {}/grundriss-katalog/ die Haken setzen".format(SITE)))
    steps.append((
        row["ok"] == "ja",
        "Plan freigegeben",
        row["ok"],
        "approved auf 'ja' setzen (kon_grundrisse)"))

    todo = None
    for done, label, detail, nxt in steps:
        print("  {} {:<30} {}".format(TICK if done else DASH, label, detail))
        if not done and todo is None:
            todo = nxt

    if paths and len(paths) != expected:
        print("\n  {} {} Blender-Dateien, erwartet werden {} "
              "({}-geschossig).".format(CROSS, len(paths), expected, row["f"]))
        print("      Zwei Aussenansichten plus eine Innenansicht pro Geschoss.")

    if todo:
        if todo.startswith("catalog.py"):
            todo = "python " + todo
        print("\n  Als naechstes:\n      " + todo)
    else:
        print("\n  Fertig. Nichts offen.")
    print("\n  {}/grundriss-katalog/  ->  {}\n".format(SITE, plan))


def blends(plan, folder):
    record(plan)
    folder = os.path.abspath(folder)
    found = sorted(n for n in os.listdir(folder) if n.endswith(".blend"))
    if not found:
        sys.exit("No .blend files in " + folder)
    paths = [os.path.join(folder, n) for n in found]
    print("Registering {} file(s) for {}:".format(len(paths), plan))
    for p in paths:
        print("  " + p)
    post("/wp-json/b2t/v1/pfade", {"plan": plan, "paths": "\n".join(paths)})
    print("\nStored. Check with:  python catalog.py status " + plan)


def images(plan, folder, extra):
    script = os.path.join(HERE, "publish-renders.py")
    command = [sys.executable, script, "--plan", plan, "--dir", folder] + extra
    raise SystemExit(subprocess.call(command))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("verb", choices=["status", "blends", "images"])
    parser.add_argument("plan")
    parser.add_argument("folder", nargs="?")
    args, extra = parser.parse_known_args()

    if args.verb == "status":
        status(args.plan)
    elif not args.folder:
        sys.exit("{} needs a folder: catalog.py {} {} <folder>".format(
            args.verb, args.verb, args.plan))
    elif args.verb == "blends":
        blends(args.plan, args.folder)
    else:
        images(args.plan, args.folder, extra)


if __name__ == "__main__":
    main()
