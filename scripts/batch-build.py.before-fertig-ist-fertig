#!/usr/bin/env python3
"""Run many houses through the build, resumably, without babysitting.

Codex, 2026-08-19, on throughput for ~100 houses: "Batch queue for prepare,
Blender, Codex intake and publishing; stop running houses individually."

What this does per house, in order, and why:

  1. SKIP if the annotation cannot support a build. A missing ground-floor
     scale means the surroundings get discarded and the render plan refuses the
     level outright -- better to say so in one line than to fail four minutes
     into Blender.
  2. SKIP if the delivery is already current. "Current" is the annotation hash
     stamped in the built plan matching the hash the annotator last saved --
     not file timestamps, which lie the moment anything is copied.
  3. BUILD otherwise, and keep going when one house fails. A batch that stops
     on the first error is a batch you have to babysit.

    python batch-build.py --all              every house that can build
    python batch-build.py --all --dry-run    say what it would do, touch nothing
    python batch-build.py twostorey_030 onehalfstorey_029
    python batch-build.py --all --limit 10   the first ten that need work

Exit code is the number of houses that failed, so a wrapper can act on it.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import hausdaten  # noqa: E402
SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")
# Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein Skript,
# das ohne gesetzte Variable still auf den alten C:-Nachbarordner
# zurueckfiele, wuerde unbemerkt gegen veraltete Daten arbeiten.
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
            "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)


# Pruefsummen der Artefakte wirklich nachrechnen. Nur --ohne-pruefsumme
# schaltet es ab, und dann sagt der Lauf das auch.
PRUEFSUMMEN = True


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return None


def annotation_state(plan):
    """(annotation_hash, blocking reason or None) for one house."""
    daten = hausdaten.hausdaten(os.path.join(PROJECTS, plan))
    annotations = daten["annotationen"]
    if annotations is None:
        return None, "keine annotations.json"

    levels = sorted({a.get("floor_level") for a in (annotations.get("annotations") or [])
                     if a.get("floor_level")})
    if not levels:
        return None, "keine annotierten Geschosse"
    # A house whose source image was deleted carries its scale in
    # gebaeudemass.json beside the annotation, not inside it -- the drawing is
    # never rewritten to record a measurement. Zusammengefuehrt wird nicht mehr
    # hier, sondern in hausdaten.py -- derselbe Helfer, den der Bau liest.
    #
    # Und zwar PRO GESCHOSS. Die alten drei Zeilen waren alles-oder-nichts:
    # stand in der Zeichnung auch nur EIN Geschoss-Schluessel, wurde das Sidecar
    # gar nicht erst aufgeschlagen. Der Annotator legt floor_scale[<geschoss>]
    # aber schon an, sobald das Geschoss existiert -- gemessen ist es damit
    # nicht. Ein Haus mit {"groundfloor": null} in der Zeichnung und einem
    # gemessenen Erdgeschoss im Sidecar galt hier deshalb als "kein Massstab"
    # und war nie baubar, obwohl der Bau selbst den Sidecar-Wert genommen haette.
    scale = dict(daten["floor_scale"])
    # The render plan refuses any level without a scale -- but it first
    # INHERITS the ground floor's scale for a level that has none (see
    # build-simplifier-render-plan.py, "Massstab ... uebernommen"). Demanding
    # a measured scale per level here was therefore stricter than the build:
    # twostorey_030 built and certified fine, yet could never read as current,
    # so it showed "bau_veraltet" forever and rebuilt on every single run
    # (found 2026-08-23 by comparing this oracle against a successful build).
    # Same rule, same order, one truth.
    basis = next((lvl for lvl in ("groundfloor", "basement") if scale.get(lvl)), None)
    if basis is None:
        basis = next((lvl for lvl in levels if scale.get(lvl)), None)
    if basis:
        for level in levels:
            scale.setdefault(level, scale[basis])
    missing = [level for level in levels if not scale.get(level)]
    if missing:
        return None, "kein Massstab fuer " + ", ".join(missing)

    # source-state.json is the annotator's cache of this hash. Houses not saved
    # since that hook existed have none -- and treating that as "unknown" made
    # every one of them rebuild on every batch, forever, because the comparison
    # below was against None. Fall back to hashing the annotation itself, the
    # authority the cache copies. Verified identical: onehalfstorey_029 has both
    # and they agree (f04ed2d7cd).
    state = read_json(os.path.join(PROJECTS, plan, "source-state.json")) or {}
    current = state.get("annotation_hash")
    if not current:
        canonical = json.dumps(annotations, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":")).encode("utf-8")
        current = hashlib.sha256(canonical).hexdigest()

    # Das Gebaeudemass gehoert zum Eingang: es liefert Massstab, Seitenver-
    # haeltnis und Dachform fuer die 119 Haeuser ohne Bild. Aendert es sich,
    # ist die Lieferung alt, auch wenn an der Zeichnung nichts geschah. Die
    # Formel steht in hausdaten.py, damit sie nicht an drei Stellen driften
    # kann (build-simplifier-render-plan.py und render-furnished-dollhouse.py
    # rechnen mit derselben Funktion).
    return hausdaten.eingangshash(os.path.join(PROJECTS, plan), current), None


def toolchain_now():
    """sha256 prefix per pipeline script, exactly as run_project stamps them."""
    revision = {}
    for script in ("run_project.py", "build-simplifier-render-plan.py",
                   "render-furnished-dollhouse.py", "render-exterior.py"):
        path = os.path.join(HERE, script)
        if not os.path.exists(path):
            continue
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        revision[script] = digest.hexdigest()[:16]
    return revision


def built_hash(plan):
    """The annotation hash of the CERTIFIED delivery, or None.

    Reads delivery-manifest.json and nothing else. Codex: "One plan-modern.json
    represents neither four .blend artifacts nor their verification. Missing,
    partial, corrupt, classic, or old .blend files can be declared current ...
    Batch 'current' must consult only that manifest."

    The manifest is written by run_project.py only after every expected .blend
    exists and every style verified, and is deleted when a build fails -- so
    its mere presence is the certificate. It is re-checked here anyway: every
    artifact it names must still exist at the size it recorded, because a
    manifest describes the delivery as it was, not as the folder is now.
    """
    folder = os.path.join(DATA, "corrections", plan, "renders", "go-baseline")
    manifest = read_json(os.path.join(folder, "delivery-manifest.json"))
    if not manifest or manifest.get("schema") != "zf-delivery-manifest-v1":
        return None
    # A renderer change invalidates a delivery as surely as an annotation
    # change. The manifest has always RECORDED the toolchain; until now nothing
    # COMPARED it, so an edit to the compiler or the renderer left every
    # existing delivery still counting as current -- exactly the "silently
    # delivering a renderer-obsolete artifact set" Codex called the highest
    # remaining risk. Claiming it in the manifest docstring while not enforcing
    # it was the worse half of the bug.
    if manifest.get("toolchain") != toolchain_now():
        return None

    # Moebel gehoeren zur Lieferung. Werden welche gesetzt oder verschoben,
    # bleibt der Annotationshash gleich -- die Zeichnung hat sich ja nicht
    # geaendert -- und das Haus galt faelschlich als fertig.
    ordner = os.path.join(DATA, "corrections", plan, "furniture")
    jetzt = None
    if os.path.isdir(ordner):
        digest = hashlib.sha256()
        for name in sorted(os.listdir(ordner)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(ordner, name), "rb") as handle:
                digest.update(name.encode("utf-8"))
                digest.update(handle.read())
        jetzt = digest.hexdigest()[:16]
    if manifest.get("furniture_fingerprint") != jetzt:
        return None

    # Erst jetzt die Artefakte selbst -- die Pruefsummen kosten 5,5 GB Lesen
    # ueber den ganzen Bestand, und das lohnt nur fuer Lieferungen, die die
    # billigen Pruefungen ueberhaupt ueberstanden haben.
    #
    # Codex, 2026-08-20: "Eine beschaedigte oder ersetzte .blend mit gleicher
    # Groesse gilt als aktuell." Der Hash stand seit jeher im Manifest und
    # wurde nie verglichen -- ein Zertifikat, das niemand einloest.
    artifacts = manifest.get("artifacts") or []
    if len(artifacts) != manifest.get("expected_blends"):
        return None
    for artifact in artifacts:
        path = os.path.join(folder, artifact.get("file", ""))
        if not os.path.exists(path) or os.path.getsize(path) != artifact.get("bytes"):
            return None            # the delivery changed under its own certificate
        stamped = artifact.get("sha256")
        if PRUEFSUMMEN and stamped and _sha256(path) != stamped:
            print("  ! %s: %s stimmt nicht mit der Pruefsumme im Zertifikat "
                  "ueberein" % (plan, artifact.get("file")))
            return None

    # Der Eingangshash umfasst Zeichnung UND Gebaeudemass. Ein Manifest ohne
    # ihn stammt aus der Zeit davor und kann nicht beweisen, aus welchem Mass
    # es gebaut wurde -- also gilt es nicht als aktuell.
    return manifest.get("input_hash")


def storeys(plan):
    annotations = read_json(os.path.join(PROJECTS, plan, "annotations.json")) or {}
    levels = {a.get("floor_level") for a in (annotations.get("annotations") or [])
              if a.get("floor_level")}
    return max(1, len(levels))


def build(plan, quiet):
    floors = ",".join(str(i) for i in range(storeys(plan)))
    command = [sys.executable, os.path.join(HERE, "run_project.py"), plan,
               "--styles", "modern,classic", "--floors", floors]
    log_dir = os.path.join(DATA, "corrections", plan, "renders", "go-baseline")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "batch-build.log")
    with open(log_path, "w", encoding="utf-8") as log:
        result = subprocess.call(command, stdout=log, stderr=subprocess.STDOUT,
                                 cwd=HERE)
    return result, log_path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plans", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ohne-pruefsumme", action="store_true",
                        help="Artefakt-Pruefsummen nicht nachrechnen (schneller, "
                             "erkennt aber eine ausgetauschte .blend gleicher "
                             "Groesse nicht)")
    parser.add_argument("--force", action="store_true",
                        help="rebuild even when the delivery is already current")
    args = parser.parse_args()

    global PRUEFSUMMEN
    PRUEFSUMMEN = not args.ohne_pruefsumme
    if not PRUEFSUMMEN:
        print("Hinweis: Artefakt-Pruefsummen werden NICHT nachgerechnet.")

    plans = args.plans
    if args.all:
        plans = sorted(name for name in os.listdir(PROJECTS)
                       if os.path.exists(os.path.join(PROJECTS, name, "annotations.json")))
    if not plans:
        sys.exit("nothing to do: name some plans or pass --all")

    todo, skipped, blocked = [], [], []
    for plan in plans:
        current, reason = annotation_state(plan)
        if reason:
            blocked.append((plan, reason))
            continue
        if not args.force and current and built_hash(plan) == current:
            skipped.append(plan)
            continue
        todo.append(plan)

    if args.limit:
        todo = todo[:args.limit]

    print("%d bereit zum Bauen, %d schon aktuell, %d blockiert\n"
          % (len(todo), len(skipped), len(blocked)))
    for plan, reason in blocked[:20]:
        print("  blockiert  %-34s %s" % (plan, reason))
    if len(blocked) > 20:
        print("  blockiert  ... und %d weitere" % (len(blocked) - 20))
    if blocked:
        print()

    failed = 0
    busy = 0
    for index, plan in enumerate(todo, start=1):
        if args.dry_run:
            print("  wuerde bauen  %s" % plan)
            continue
        print("  [%d/%d] baue %-30s " % (index, len(todo), plan), end="", flush=True)
        code, log_path = build(plan, quiet=True)
        if code == 0:
            print("ok")
        elif code == 2:
            # run_project exits 2 when another process holds the build lock.
            # That is not a broken house and must not count as a failure --
            # otherwise a second batch running alongside the first would call
            # every house failed and the exit code would lie to any wrapper.
            busy += 1
            print("belegt (wird bereits gebaut)")
        else:
            failed += 1
            print("FEHLER (exit %d) -> %s" % (code, log_path))

    if not args.dry_run:
        print("\n%d gebaut, %d fehlgeschlagen%s"
              % (len(todo) - failed - busy, failed,
                 ", %d belegt" % busy if busy else ""))
    # Codex, 2026-08-20: "Ein Batch mit ausschliesslich belegten Haeusern
    # liefert Exit 0, nicht 2." Er tat es, und ein Wrapper haette daraus
    # "alles erledigt" gelesen, obwohl kein einziges Haus gebaut wurde.
    # Fehler haben Vorrang; ohne Fehler und ohne einen einzigen Bau heisst
    # belegt eben belegt.
    if failed:
        sys.exit(failed)
    if busy and busy == len(todo):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
