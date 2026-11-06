"""The "Go" button: takes one annotated project and produces verified
baseline renders (interior + all 4 roof-form exteriors) plus a per-project
handoff pointer for Codex to take over from.

This does NOT produce final customer-style images. It produces the
CORRECTED, VERIFIED raw geometry baseline -- real walls, real openings,
real furniture as annotated, real roof. Style/mood variants and photoreal
polish are Codex's job from here (see docs/CODEX-HANDOFF.md and the
per-project handoff.json this script writes).

Usage:
  python scripts/run_project.py <project_id> [--styles modern,classic]

What it does, in order:
  1. Build the proof render plan per style (build-simplifier-render-plan.py)
     -- this is the ONLY plan builder that uses your real annotated
     furniture placements, not an algorithmic guess (verified 2026-08-16).
  2. Render exterior for each style (render-exterior.py).
  3. Render interior once (same for every style since interior furniture
     doesn't depend on roof style) with DMH_SAVE_BLEND set so a scene file
     is actually kept, not just a PNG.
  4. Run verify_render.py against every plan, capturing each render's log.
  5. Write renders/<project_id>/handoff.json: exact paths to the verified
     .blend files, where to write images, where to write catalog.json.

Exits non-zero if verification fails for a style; still writes handoff.json
for the styles that passed, with an EXCLUDED entry per failure -- one bad
style should not block the others.
"""
import argparse
import hashlib
import uuid
import atexit
import time
import json
import datetime
import os
import shutil
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SUITE_ROOT = os.path.dirname(REPO)
SIMPLIFIER = os.path.join(SUITE_ROOT, "floorplan-simplifier")
# NICHT den Suite-Nachbarordner hart verdrahten. Codex, 2026-08-21, vor einem
# geplanten Umzug nach E: gefragt: "run_project.py schreibt Moebel und
# Render-Ausgaben immer in den alten Suite-Nachbarordner ... Hoechstes
# Root-Split-Risiko." Genau das war der root-merge-Vorfall vom 2026-08-18 --
# zwei Datenwurzeln gleichzeitig in Benutzung, drei Bugs an einem Tag. Die
# Umgebungsvariable ist die einzig gueltige Quelle.
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
            "den Datenordner zu erraten. Siehe .env.local.")
DATA_REPO = os.path.abspath(_konfiguriert)
PYTHON = sys.executable
# The plan builder refuses to guess which workbench tree holds the furniture
# (workbench_data_root()), so the Go button states it. Without this every
# project stops at the plan step, furnished or not.
PLAN_ENV = dict(os.environ, FLOORPLAN_WORKBENCH_DATA_DIR=os.environ.get(
    "FLOORPLAN_WORKBENCH_DATA_DIR", DATA_REPO))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
# Ohne --python-exit-code beendet Blender sich nach einem Python-Fehler mit 0:
# ein abgestuerzter Render galt als gelungen, und die Pruefung sah die ALTE
# .blend vom letzten Mal (Codex, 2026-10-28; gesehen in
# bungalow_generationat interior-classic-upper-baseline.log: IndexError,
# "Blender quit", Exit 0). Gilt fuer jeden Blender-Aufruf, seriell wie parallel.
BLENDER_PY = ("--background", "--python-exit-code", "1", "--python")

# Every house now delivers all 4 roof forms as exteriors, not one per
# material style. Rainer, 2026-09-15: "he just wanted all of the roof forms
# so not just 2 exteriors but all 4" -- confirmed via clarifying question:
# roof only, one material look, 4 exteriors total (not a 4x2 combination).
# Rendered from ONE style's plan (the first requested style) with an
# EXT_ROOF_TYPE override per call (see render-exterior.py) -- roof geometry
# is a late, separate build step there, so the plan's walls/materials don't
# need to vary per roof form the way they used to vary per material style.
ROOF_TYPES = ("flachdach", "walmdach", "satteldach", "pultdach")


def roof_types_for_plan(plan_path):
    """Flach, Walm and Satteldach always deliver; the 4th slot is the Pultdach
    or, when the Dach tab says so, the versetzte Doppelpultdach -- still
    exactly 4 roof-form exteriors (the hard rule), never 5. Rainer,
    2026-09-19: "Flach Walm Satteldach (Pultdach oder Versetzes Pultdach)".
    """
    try:
        with open(plan_path, encoding="utf-8") as handle:
            _plan = json.load(handle)
        fourth = _plan.get("roof_fourth")
    except (OSError, ValueError):
        return ROOF_TYPES
    # 1,5-Geschosser: EIN Dach -- das Satteldach mit Kniestock und
    # Zwerchgiebel (Rainer, 2026-10-20: "we dont need the 4 roof forms just
    # the one with the 1,5 story houses"; anderthalb-eine-dachform-v1).
    import anderthalb
    # Zwei Aussenansichten: klassisch (Zwerchgiebel) und modern (Zwerchkubus),
    # Rainer 2026-10-21 -- anderthalb-zwerchkubus-modern-v1.
    if anderthalb.ist_anderthalb(_plan):
        return ("satteldach", "satteldach" + anderthalb.KUBUS_SUFFIX)
    # Bungalow mit Dachboden: EIN Dach -- den Dachboden gibt es nur unter dem
    # Satteldach (dachboden-ausbaureserve-v1, Rainer 2026-10-23).
    if _plan.get("dachboden"):
        return ("satteldach",)
    # Staffelgeschoss: nur das Flachdach (Rainer, 2026-11-01, Regel 19).
    if _plan.get("staffelgeschoss"):
        return ("flachdach",)
    if fourth == "doppelpultdach":
        return tuple("doppelpultdach" if roof == "pultdach" else roof
                     for roof in ROOF_TYPES)
    return ROOF_TYPES


def run_still(cmd, log_path=None, env=None):
    """Einen Befehl ausfuehren, ohne etwas zu drucken -- auch aus einem
    Arbeitsthread heraus: Ausgabe und Log gehoeren nur diesem Prozess."""
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    output = result.stdout + result.stderr
    if log_path:
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write(output)
    return result.returncode == 0, output


def run(cmd, log_path=None, env=None):
    print(f"[go] $ {' '.join(str(c) for c in cmd)}")
    ok, output = run_still(cmd, log_path, env)
    if not ok:
        print(output[-4000:])
    return ok, output


# ------------------------------------------------------------ BAU-SCHNELLER-001
# Rainer, 2026-10-27: "fuvking build takes forever". Gemessen an
# german_catalog_review_onehalfstorey_1_2_2_efh_140_1: ~6 1/2 min, davon ~3 min
# fuer 18 Pruefaufrufe hintereinander, jeder oeffnet die 255-MB-Szene neu --
# und der Treppenfehler kam erst ganz am Ende. Unabhaengige Blender-Auftraege
# laufen jetzt nebeneinander (hoechstens BAU_PARALLEL, Vorgabe 3; 1 = genau
# der alte Ablauf), jede Pruefung startet, sobald IHRE Szene fertig ist, und
# ein Fehler, der das Zertifikat ohnehin verhindert, startet nichts Neues mehr.

def bau_parallel():
    """Wie viele Blender-Prozesse gleichzeitig. BAU_PARALLEL=1: alter Ablauf."""
    try:
        return max(1, int(os.environ.get("BAU_PARALLEL", "3")))
    except ValueError:
        return 3


class Auftrag:
    """Ein Prozess im Bau.

    braucht -- muessen ERFOLGREICH fertig sein (die Pruefung braucht ihre Szene).
    nach    -- muessen fertig sein, gleich wie (Kette: dieselbe Kameradatei).
    wesentlich -- scheitert er, ist das Zertifikat ohnehin verloren: keine
               neuen Auftraege mehr. Eine Zusatz-Ausfuehrung (-b) war das nie.
    cmd     -- Liste, oder Funktion(ergebnisse) -> Liste/None, wenn der Befehl
               erst beim Start feststeht (None: entfaellt).
    zeigen  -- Funktion(ok, ausgabe), was nach dem Lauf ins Bau-Log gehoert.
    schreibt / liest -- Dateischluessel (normierte Pfade), aus denen
               datei_abhaengigkeiten() die Reihenfolge der alten seriellen
               Schleife fuer jede gemeinsame Datei wiederherstellt.
    braucht_dateien -- gelesen UND noetig: der letzte Schreiber muss gelungen sein.
    """

    def __init__(self, name, cmd, log_path=None, env=None, braucht=(), nach=(),
                 wesentlich=True, prio=0, zeigen=None, schreibt=(), liest=(),
                 braucht_dateien=()):
        self.name = name
        self.cmd = cmd
        self.log_path = log_path
        self.env = env
        self.braucht = tuple(braucht)
        self.nach = tuple(nach)
        self.wesentlich = wesentlich
        self.prio = prio
        self.zeigen = zeigen
        self.schreibt = set(schreibt)
        self.liest = set(liest)
        self.braucht_dateien = set(braucht_dateien)


def datei_schluessel(pfad):
    return os.path.normcase(os.path.abspath(pfad))


def datei_abhaengigkeiten(auftraege):
    """Gemeinsame Dateien in der Reihenfolge der Liste (= der seriellen Schleife).

    Codex, 2026-10-28: zwei Auftraege, die dieselbe Datei schreiben, liefen
    nebeneinander (--finishes modern-a,modern-b: beide Stile schreiben
    interior-modern-b-baseline.*). Seriell hiess das: erst der eine samt
    allen, die ihn lesen, dann der andere. Genau das stellt diese Funktion
    fuer JEDEN Schluessel her:
      - wer liest, kommt nach dem letzten Schreiber davor;
      - wer schreibt, kommt nach dem letzten Schreiber und nach allen, die
        seitdem gelesen haben;
      - braucht_dateien: wie lesen, aber der Schreiber muss GELUNGEN sein.
    Die Liste muss dafuer in der seriellen Reihenfolge stehen.
    """
    letzter = {}
    leser = {}
    for a in auftraege:
        nach, braucht = set(a.nach), set(a.braucht)
        for k in a.liest | a.braucht_dateien:
            w = letzter.get(k)
            if w and w != a.name:
                (braucht if k in a.braucht_dateien else nach).add(w)
            leser.setdefault(k, []).append(a.name)
        for k in a.schreibt:
            w = letzter.get(k)
            if w and w != a.name:
                nach.add(w)
            nach.update(r for r in leser.get(k, []) if r != a.name)
            letzter[k] = a.name
            leser[k] = []
        a.braucht = tuple(sorted(braucht))
        a.nach = tuple(sorted(nach - braucht))
    return auftraege


def fehler_zeile(name, output):
    """Der Grund in EINER Zeile, fuer go.py: "BAU-FEHLER: <grund>".

    Codex, 2026-10-28: stuerzte ein Render ab, nachdem eine andere Pruefung
    schon ihr "[verify-blend] ..." und "PASS ..." gedruckt hatte, nannte go.py
    diese PASS-Zeile als Grund. Deshalb sagt der Bau selbst, was zuerst
    gescheitert ist.
    """
    zeilen = output.splitlines()
    for i, z in enumerate(zeilen):
        if z.startswith("FAIL "):
            regel = z.split()[1] if len(z.split()) > 1 else z[5:]
            nach = zeilen[i + 1] if i + 1 < len(zeilen) else ""
            grund = nach[4:].strip() if nach.startswith("  - ") else ""
            return "Verifier %s%s" % (regel, ": " + grund if grund else "")
    if any(z.startswith("Traceback") for z in zeilen):
        letzte = [z.strip() for z in zeilen if z.strip() and not z.startswith((" ", "Blender quit"))]
        return "%s: %s" % (name, letzte[-1] if letzte else "Python-Fehler")
    letzte = [z.strip() for z in zeilen if z.strip() and z.strip() != "Blender quit"]
    return "%s: gescheitert%s" % (name, (" -- " + letzte[-1]) if letzte else "")


def _ausfuehren(auftrag, cmd):
    return run_still(cmd, auftrag.log_path, auftrag.env)


def abarbeiten(auftraege, parallel, ausfuehren=None):
    """Fuehrt die Auftraege aus, hoechstens `parallel` gleichzeitig.

    Gibt {name: (ok, ausgabe)} fuer jeden gelaufenen Auftrag zurueck; wer
    fehlt, ist nie gestartet (Voraussetzung gescheitert oder Abbruch).
    Gedruckt wird nur hier im Hauptthread, ein Auftrag am Stueck -- so stehen
    die FAIL-Zeilen eines Pruefers samt ihren "  - "-Gruenden zusammen im
    Bau-Log, wo go.py sie liest.
    """
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

    ausfuehren = ausfuehren or _ausfuehren
    reihenfolge = {a.name: i for i, a in enumerate(auftraege)}
    offen = list(auftraege)
    ergebnisse = {}
    laufend = {}
    abbruch = False

    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        while True:
            # Wer nie laufen wird, faellt raus -- so lange, bis sich nichts
            # mehr aendert (eine Kette faellt Glied fuer Glied).
            while True:
                lebend = {a.name for a in offen} | {a.name for a in laufend.values()}
                bleibt = [a for a in offen
                          if not any(d in ergebnisse and not ergebnisse[d][0] for d in a.braucht)
                          and all(d in ergebnisse or d in lebend for d in a.braucht + a.nach)]
                if len(bleibt) == len(offen):
                    break
                offen = bleibt

            if not abbruch:
                bereit = sorted((a for a in offen
                                 if all(d in ergebnisse for d in a.braucht + a.nach)),
                                key=lambda a: (a.prio, reihenfolge[a.name]))
                for a in bereit:
                    if len(laufend) >= max(1, parallel):
                        break
                    cmd = a.cmd(ergebnisse) if callable(a.cmd) else a.cmd
                    offen.remove(a)
                    if cmd is None:
                        continue
                    print(f"[go] $ {' '.join(str(c) for c in cmd)}")
                    laufend[pool.submit(ausfuehren, a, cmd)] = a

            if not laufend:
                if offen and not abbruch and any(
                        all(d in ergebnisse for d in a.braucht + a.nach) for a in offen):
                    continue            # ein entfallener Befehl hat Platz gemacht
                break

            fertig, _ = wait(list(laufend), return_when=FIRST_COMPLETED)
            for future in sorted(fertig, key=lambda f: reihenfolge[laufend[f].name]):
                a = laufend.pop(future)
                try:
                    ok, output = future.result()
                except Exception as fehler:          # der Thread selbst, nicht der Prozess
                    ok, output = False, f"{type(fehler).__name__}: {fehler}"
                ergebnisse[a.name] = (ok, output)
                if not ok:
                    print(output[-4000:])
                if a.zeigen:
                    a.zeigen(ok, output)
                if not ok and a.wesentlich and not abbruch:
                    abbruch = True
                    print(f"BAU-FEHLER: {fehler_zeile(a.name, output)}")
                    print(f"[go] Abbruch nach {a.name}: keine neuen Auftraege mehr, "
                          f"laufende werden zu Ende gebaut")
    return ergebnisse


def vorpruefung(plan, roof_types=None):
    """Was den Bau sicher scheitern liesse, VOR Blender -- oder None.

    1,5-Geschosser: das Kniestock-Dach gibt es nur, wenn das Obergeschoss ein
    Rechteck (oder ein Rechteck mit flachen Erkern) ist. Sonst baute
    render-exterior.py bisher still einen Zweigeschosser-Kasten mit flachem
    Dach (german_catalog_review_onehalfstorey_1_2_2_efh_140_1, 2026-10-27: 6
    "Aussenwaende" im DG). Dieselbe Eingabe wie dort (render-exterior.py,
    1,5-Geschosser-Block): die Aussenwaende des obersten Geschosses aus dem
    Plan, dieselbe Funktion anderthalb.rechteck_mit_erkern().
    """
    import anderthalb
    if not anderthalb.ist_anderthalb(plan):
        return None
    # Der Renderer prueft nur fuer Sattel- und Walmdach (render-exterior.py).
    if roof_types is not None and not set(roof_types) & {"satteldach", "walmdach"}:
        return None
    floors = plan.get("floors") or []
    if len(floors) < 2:
        return None
    oben = [w for w in floors[-1].get("walls", []) if w.get("wall_type") == "exterior"]
    # Vier Waende: der Renderer nimmt dann die Bounding-Box, wenn das Haus
    # EIN Massing-Rechteck ist (len(massing_rects) == 1), sonst fragt er
    # rechteck_mit_erkern(). massing_rects entsteht erst im Renderer aus der
    # Zerlegung des Grundrisses; hier wird es nicht nachgebaut. Vier Waende
    # gehen darum immer durch -- die Vorpruefung kann so einen Fall
    # verpassen (dann warnt der Renderer wie bisher), aber nie ein Haus
    # ablehnen, das der Renderer baut (Codex, 2026-10-28).
    if len(oben) == 4:
        return None
    mm = 0.001
    if anderthalb.rechteck_mit_erkern(
            [((w["start_mm"][0] * mm, w["start_mm"][1] * mm),
              (w["end_mm"][0] * mm, w["end_mm"][1] * mm)) for w in oben]) is not None:
        return None
    return ("1,5-Geschosser: DG-Umriss ist kein Rechteck (%d Aussenwaende) -- "
            "Aussenumriss im DG zeichnen" % len(oben))


def vorpruefung_datei(plan_path, roof_types=None):
    try:
        with open(plan_path, encoding="utf-8-sig") as handle:
            return vorpruefung(json.load(handle), roof_types)
    except (OSError, ValueError):
        return None             # unlesbar: das meldet der Renderer selbst


def trim_to_delivery(out_dir, primary_style, floors, roof_types=ROOF_TYPES):
    """HARD RULE: a two-storey house delivers exactly 6 .blend files, a
    single-storey exactly 5 -- four roof-form exteriors plus one interior
    per storey. (Was 2 exteriors + 1/storey until 2026-09-15: Rainer, "he
    just wanted all of the roof forms so not just 2 exteriors but all 4".)

    The build necessarily makes more than that: every style times every finish
    times every storey. Leaving the surplus in the delivery folder is how the
    wrong upper floor got handed over once already, and how a "4 files please"
    delivery arrived as ten. So the surplus is MOVED ASIDE at the end of every
    build, by the build itself -- not by whoever remembers to do it afterwards.

    Moved, never deleted: this tree is not a git repo.
    """
    keep = {f"exterior-{roof}-baseline" for roof in roof_types}
    for index, _floor in enumerate(floors):
        tag = "" if index == 0 else f"-{'upper' if index == 1 else f'floor{index}'}"
        keep.add(f"interior-{primary_style}{tag}-baseline")

    # Der Dachboden liegt auf E:, nicht neben der Lieferung. Rainer,
    # 2026-08-21: "mein C ist bald voll" -- 10,3 GB verdraengte Altstaende
    # lagen unter corrections/. Gleiche Struktur, anderes Laufwerk; existiert
    # E: nicht (Laptop unterwegs), faellt es auf den alten Platz zurueck,
    # verschoben wird IMMER, geloescht nie.
    attic_root = os.environ.get("ZF_ATTIC_ROOT", r"E:\_floorplan_dachboden")
    # Das Haus aus dem Pfad (…/corrections/<haus>/renders/go-baseline), wie
    # der Renderer es auch tut -- trim_to_delivery kennt die project_id nicht.
    teile = os.path.abspath(out_dir).replace("\\", "/").split("/")
    haus = teile[teile.index("corrections") + 1] if "corrections" in teile else "unbekannt"
    if os.path.isdir(attic_root):
        attic = os.path.join(attic_root, haus,
                             f"superseded-{datetime.date.today().isoformat()}")
    else:
        attic = os.path.join(out_dir, f"superseded-{datetime.date.today().isoformat()}")
    moved = []
    for name in sorted(os.listdir(out_dir)):
        if not name.endswith(".blend"):
            continue
        stem = name[:-len(".blend")]
        if stem in keep:
            continue
        os.makedirs(attic, exist_ok=True)
        for sibling in sorted(os.listdir(out_dir)):
            if sibling.startswith(stem) and os.path.isfile(os.path.join(out_dir, sibling)):
                shutil.move(os.path.join(out_dir, sibling), os.path.join(attic, sibling))
                moved.append(sibling)

    kept = [n for n in sorted(os.listdir(out_dir)) if n.endswith(".blend")]
    expected = len(roof_types) + len(floors)
    print(f"[go] delivery: {len(kept)} .blend (expected {expected}), "
          f"{len(moved)} file(s) moved to {os.path.basename(attic) if moved else '-'}")
    for name in kept:
        print(f"[go]   {name}")
    if len(kept) != expected:
        print(f"[go] WARNING: delivery folder holds {len(kept)} .blend, the rule says {expected}")
    return kept


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def furniture_fingerprint(project_id):
    """sha256 ueber die gesetzten Moebel dieses Hauses, oder None.

    Ohne das galt eine Lieferung als aktuell, obwohl inzwischen 23 Moebel
    gesetzt worden waren: der Annotationshash aendert sich nicht (die
    Zeichnung blieb gleich), die Toolchain auch nicht -- und `go.py` stieg
    mit "fertig" aus, ohne zu bauen. Der Bauen-Knopf schien nichts zu tun.
    Gemessen an bungalow_039 am 2026-08-20: 23 Symbole gesetzt, Build meldete
    weiter "0 instances from 0 meshes", erst --force brachte sie hinein.
    """
    ordner = os.path.join(DATA_REPO, "corrections", project_id, "furniture")
    if not os.path.isdir(ordner):
        return None
    digest = hashlib.sha256()
    for name in sorted(os.listdir(ordner)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(ordner, name), "rb") as handle:
            digest.update(name.encode("utf-8"))
            digest.update(handle.read())
    return digest.hexdigest()[:16]


def write_delivery_manifest(out_dir, project_id, floors, verified, expected,
                            requested=None):
    """The delivery is what this file says it is, or there is no delivery.

    Codex, 2026-08-19, asked for exactly one thing next: "an atomic delivery
    manifest written only after all expected .blend files pass verification.
    It should record normalized annotation hash, correction hash,
    compiler/renderer revision, asset fingerprints and each artifact's hash.
    Batch 'current' must consult only that manifest."

    The reason is the failure it prevents: until now "is this house current?"
    was answered from plan-modern.json alone, so a delivery with a missing,
    stale or half-written .blend could be declared current. Codex called that
    "the highest remaining risk: silently delivering a mixed, incomplete or
    renderer-obsolete artifact set that passes the single-plan hash check."

    Written ONLY when every expected artifact exists and every style verified.
    On failure the old manifest is REMOVED rather than left behind, because a
    stale manifest claiming success is worse than none. Written atomically
    (temp + replace) so a crash mid-write cannot leave a half-file that reads
    as valid JSON.
    """
    manifest_path = os.path.join(out_dir, "delivery-manifest.json")
    blends = sorted(n for n in os.listdir(out_dir) if n.endswith(".blend"))

    # EVERY requested style must have verified, not merely one of them.
    # Measured 2026-08-20: bungalow_040_66 lost its classic interior to a
    # Blender EXCEPTION_ACCESS_VIOLATION, run_project reported "1 style(s)
    # verified and ready, 1 excluded" -- and the delivery was still CERTIFIED,
    # because this test only asked whether the list was non-empty and the
    # .blend count happened to match (the classic interior is not one of the
    # expected artifacts for a single-storey house, so its absence did not
    # change the count). A certificate that silently means "half the styles"
    # is worse than no certificate. Standing rule: always run both styles.
    missing_styles = sorted(set(requested or []) - set(verified or []))
    if missing_styles:
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
        print("[go] delivery-manifest: NOT written -- Stil(e) nicht verifiziert: %s"
              % ", ".join(missing_styles))
        return None

    if not verified or len(blends) != expected:
        # Refuse to certify, and take any previous certificate with it.
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
        print("[go] delivery-manifest: NOT written (%d/%d .blend, verified=%s)"
              % (len(blends), expected, bool(verified)))
        return None

    provenance = {}
    for style_plan in ("plan-modern.json", "plan-classic.json"):
        candidate = os.path.join(out_dir, style_plan)
        if os.path.exists(candidate):
            with open(candidate, encoding="utf-8-sig") as handle:
                document = json.load(handle)
            provenance = document.get("source_provenance") or {}
            geometry_hash = document.get("source_geometry_hash")
            roof = {"roof_type": document.get("roof_type"),
                    "roof_type_source": document.get("roof_type_source")}
            break
    else:
        geometry_hash = None
        roof = {}

    # Ein Haus ohne gewaehlte Dachform bekommt ein Flachdach, weil nichts
    # anderes dasteht -- nicht weil es eines ist. Der Renderer sagt das laut,
    # aber laut Sagen ist keine Sperre: Codex, 2026-08-20, "Damit kann eine
    # Lieferung trotz unbekannter Dachform Exit 0 erhalten." Genau das ist die
    # Sorte Fehler, die als fertiges Bild im Katalog landet.
    if not roof.get("roof_type"):
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
        print("[go] delivery-manifest: NICHT geschrieben -- keine Dachform "
              "gewaehlt. Setzen mit: python dachform.py %s" % project_id)
        return None

    # The code that produced this. A renderer change invalidates a delivery
    # just as surely as an annotation change; hashing the scripts is the
    # cheapest honest way to notice.
    revision = {}
    for script in ("run_project.py", "build-simplifier-render-plan.py",
                   "render-furnished-dollhouse.py", "render-exterior.py",
                   # Hilfsmodule, die der Bau importiert (DG-MIT-KNIESTOCK-001):
                   # eine Aenderung an anderthalb.py baute other_vito NICHT neu,
                   # weil nur die vier Hauptskripte im Fingerabdruck standen.
                   "anderthalb.py", "dachboden.py", "doppelhaus.py", "hausdaten.py",
                   "roof_profile.py", "roof_wings.py", "teppich_klemmen.py"):
        path = os.path.join(HERE, script)
        if os.path.exists(path):
            revision[script] = _sha256(path)[:16]

    manifest = {
        "schema": "zf-delivery-manifest-v1",
        "plan_id": project_id,
        "written_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "storeys": len(floors),
        "expected_blends": expected,
        "annotation_hash": provenance.get("annotation_hash"),
        # Zeichnung UND gebaeudemass.json -- der Massstab steht bei 119
        # Haeusern nur im Sidecar, und ohne ihn galt eine in falscher Groesse
        # gebaute Lieferung weiter als aktuell.
        "input_hash": provenance.get("input_hash"),
        "sidecar_hash": provenance.get("sidecar_hash"),
        "geometry_hash": geometry_hash,
        # A certified delivery must not hide that its roof was never chosen.
        "roof": roof,
        # Moebel sind Teil der Lieferung: aendern sie sich, ist das Modell alt.
        "furniture_fingerprint": furniture_fingerprint(project_id),
        "toolchain": revision,
        "artifacts": [{"file": name, "sha256": _sha256(os.path.join(out_dir, name)),
                       "bytes": os.path.getsize(os.path.join(out_dir, name))}
                      for name in blends],
        "verified_styles": sorted(verified),
    }
    temporary = manifest_path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    os.replace(temporary, manifest_path)
    print("[go] delivery-manifest: %d artifact(s) certified" % len(blends))
    return manifest


LOCK_NAME = "build.lock"
LOCK_STALE_SECONDS = 6 * 60 * 60


def _process_alive(pid):
    """True if pid is running. Windows has no os.kill(0), so ask tasklist."""
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            # errors="replace": tasklist prints process names in the console
            # codepage, and a single non-ASCII byte otherwise raises
            # UnicodeDecodeError in the reader thread -- which this function
            # would swallow as "not alive" and then steal a LIVE build's lock.
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                                 capture_output=True, text=True,
                                 errors="replace", timeout=10).stdout or ""
            return str(pid) in out
        os.kill(pid, 0)
        return True
    except Exception:
        return False        # cannot tell -> treat as dead, staleness still guards


def acquire_lock(out_dir, project_id):
    """Take an exclusive build lock on a delivery folder, or refuse.

    Codex asked for a real queue with locking; this is the part that actually
    prevents damage. Two runs on one house are not merely wasteful: the build
    MOVES older artifacts into a superseded-<date> attic and rewrites the
    manifest, so concurrent runs would shuffle each other's files and could
    certify a delivery assembled from two different runs.

    O_CREAT|O_EXCL is atomic on Windows and POSIX alike, so the create either
    wins or raises.

    Codex, 2026-08-20, on the first version: "Build B erklaert ihn nach sechs
    Stunden fuer stale, loescht ihn und erstellt einen neuen. Build A endet und
    loescht mit release_lock() den Lock von B. Build C startet parallel zu B."
    That is exactly what happened, and it turned the lock into the very thing
    it exists to prevent. Two changes close it:

    1. Every lock carries a random TOKEN. release_lock only deletes a lock that
       still holds its own token, so a run that lost the lock cannot free
       somebody else's.
    2. A lock whose process is demonstrably ALIVE is never taken over, however
       old it is. A long build is still a build. Age only decides for a lock
       that cannot be read at all (truncated, hand-edited), where there is no
       pid to ask.

    PID reuse remains theoretically possible: a dead build's pid can be handed
    to an unrelated process, which then looks alive and holds the house until
    the file is deleted by hand. The message below says how.
    """
    path = os.path.join(out_dir, LOCK_NAME)
    token = uuid.uuid4().hex
    for attempt in (1, 2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                with open(path, encoding="utf-8-sig") as handle:
                    holder = json.load(handle)
            except Exception:
                holder = None
            if holder is None:
                # No pid to ask. Only the file's own age can decide, and only
                # once it is well past any plausible build.
                try:
                    age = time.time() - os.path.getmtime(path)
                except OSError:
                    age = LOCK_STALE_SECONDS + 1
                takeover = age > LOCK_STALE_SECONDS
                why = "unlesbar und aelter als %d h" % (LOCK_STALE_SECONDS // 3600)
            else:
                takeover = not _process_alive(int(holder.get("pid", -1) or -1))
                why = "Prozess %s lebt nicht mehr" % holder.get("pid")
            if attempt == 1 and takeover:
                print("[go] uebernehme verwaisten build.lock (%s)" % why)
                try:
                    os.remove(path)
                except OSError:
                    pass
                continue
            print("[go] ABGELEHNT: %s wird bereits gebaut (pid %s, seit %s)."
                  % (project_id, (holder or {}).get("pid", "?"),
                     (holder or {}).get("started_at", "?")))
            print("[go] Zwei gleichzeitige Builds wuerden sich die Artefakte "
                  "gegenseitig verschieben.")
            print("[go] Laeuft dort nachweislich nichts mehr: %s loeschen." % path)
            return None
        else:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump({"token": token, "pid": os.getpid(),
                           "project_id": project_id,
                           "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
                           "started_epoch": time.time()}, handle)
            return {"path": path, "token": token}
    return None


def release_lock(lock):
    """Give up a lock -- but only if it is still ours.

    Between acquiring and releasing, another run may have declared this lock
    orphaned and replaced it with its own. Deleting by path alone would then
    open the house to a third build while the second is still writing.
    """
    if not lock:
        return
    path, token = lock["path"], lock["token"]
    try:
        with open(path, encoding="utf-8-sig") as handle:
            if json.load(handle).get("token") != token:
                print("[go] build.lock gehoert inzwischen einem anderen Lauf "
                      "-- nicht angefasst.")
                return
    except FileNotFoundError:
        return
    except Exception:
        pass            # unreadable: it was ours when we made it, clear it
    try:
        os.remove(path)
    except OSError:
        pass


def _blend_zeilen(ok, output):
    for line in output.splitlines():
        if line.startswith(("PASS", "FAIL", "  -", "[verify-blend]")):
            print(line)


def _plan_geschoss(plan, floor_key):
    """(Index, Geschoss) wie render-furnished-dollhouse.py DMH_FLOOR aufloest."""
    if not plan:
        return None, None
    floors = plan.get("floors") or []
    for i, f in enumerate(floors):
        if f.get("id") == floor_key:
            return i, f
    try:
        i = int(floor_key)
        return i, floors[i]
    except (ValueError, IndexError):
        return None, None


def _kamera_innen_pfad(blend, floor_index):
    """Dieselbe Kameradatei wie render-furnished-dollhouse.py KAMERA_INNEN_JSON."""
    if os.environ.get("DMH_KAMERA_JSON"):
        return os.environ["DMH_KAMERA_JSON"]
    ziel = os.path.abspath(blend)
    if os.path.basename(os.path.dirname(ziel)) != "go-baseline":
        return None
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ziel))),
                        "kamera-innen-%s.json" % floor_index)


def _kamera_aussen_pfad(png):
    """Dieselbe Kameradatei wie render-exterior.py KAMERA_JSON. Zeigen
    EXT_KAMERA_JSON und DMH_KAMERA_JSON auf dieselbe Datei, teilen Aussen-
    und Innen-Render sie (Codex, Runde 2) -- der gemeinsame Schluessel
    stellt dann auch zwischen ihnen die serielle Reihenfolge her."""
    if os.environ.get("EXT_KAMERA_JSON"):
        return os.environ["EXT_KAMERA_JSON"]
    ziel = os.path.abspath(png)
    if os.path.basename(os.path.dirname(ziel)) != "go-baseline":
        return None
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ziel))),
                        "kamera-aussen.json")


def _luftraum_quelle(blend, plan_geschoss, floor_index):
    """Die .blend des Geschosses darunter, die render-furnished-dollhouse.py
    fuer einen Luftraum laedt (_geschoss_darunter_im_luftraum) -- oder None.
    Ist der Plan unlesbar, zaehlt jedes obere Geschoss vorsichtshalber."""
    if floor_index == 0:
        return None
    if plan_geschoss is not None:
        luft = [r.get("polygon_mm") or [] for r in plan_geschoss.get("rooms") or []
                if r.get("kind") == "luftraum"]
        if not [q for q in luft if len(q) >= 3]:
            return None
    unten = re.sub(r"-(upper|floor\d+)-baseline\.blend$", "-baseline.blend", blend)
    return None if unten == blend else unten


def _bauen_parallel(args, styles, requested_finishes, floors, out_dir,
                    annotations_path, handoff, parallel):
    """Dieselben Prozesse wie die serielle Schleife in main(), als Abhaengigkeiten.

    Abhaengigkeiten (gemessen an run_project.py, 2026-10-27):
      plan:<stil>            -- keine; schreibt nur plan-<stil>.json
      ext:<dach>             -- Plan des ersten Stils; KETTE ueber alle Daecher:
                                alle teilen kamera-aussen.json (Handkamera-Rettung)
      int:<stil>:<geschoss>:<ausf.> -- Plan des Stils; je Geschoss teilen alle
                                kamera-innen-<n>.json: Schreiber in alter
                                Reihenfolge, Leser danach nebeneinander
      vb:<stil>:<schluessel> -- braucht seine Innenszene, sonst nichts
      vr:<stil>              -- Aussen-Log (erstes gelungenes Dach) und
                                interior-<stil>-baseline.log
    Ergebnis und handoff werden danach genau so zusammengesetzt wie seriell.
    """
    plaene = {style: os.path.join(out_dir, f"plan-{style}.json") for style in styles}
    plan_jobs = []
    for style in styles:
        if args.corrected:
            cmd = [PYTHON, os.path.join(HERE, "build-simplifier-render-plan.py"),
                   "--correction-revision", args.corrected, style, plaene[style]]
        else:
            cmd = [PYTHON, os.path.join(HERE, "build-simplifier-render-plan.py"),
                   args.project_id, style, plaene[style]]
        plan_jobs.append(Auftrag(f"plan:{style}", cmd, env=PLAN_ENV))
    erg = abarbeiten(plan_jobs, parallel)
    gute = [s for s in styles if erg.get(f"plan:{s}", (False, ""))[0]]
    for style in styles:
        if style not in gute:
            handoff["excluded"].append({"style": style, "reason": "plan_build_failed"})
    if len(gute) != len(styles):
        # Ein fehlender Stil verhindert das Zertifikat ohnehin.
        return {}, roof_types_for_plan(plaene[gute[0]]) if gute else ROOF_TYPES

    erster = gute[0]
    roof_types = roof_types_for_plan(plaene[erster])
    grund = vorpruefung_datei(plaene[erster], roof_types)
    if grund:
        print(f"Vorpruefung: {grund}")
        handoff["excluded"].append({"style": erster, "reason": "vorpruefung", "detail": grund})
        return {}, roof_types

    jobs = []
    vorher = None
    for roof in roof_types:
        name = f"ext:{roof}"
        ext_png = os.path.join(out_dir, f"exterior-{roof}-baseline.png")
        ext_kamera = _kamera_aussen_pfad(ext_png)
        # Jeder Aussen-Render kann die Kamera retten (schreiben) -- wie seriell.
        ext_kamera_key = {"kamera:" + datei_schluessel(ext_kamera)} if ext_kamera else set()
        jobs.append(Auftrag(
            name,
            [BLENDER, *BLENDER_PY, os.path.join(HERE, "render-exterior.py"), "--",
             plaene[erster], ext_png],
            log_path=os.path.join(out_dir, f"exterior-{roof}-baseline.log"),
            env=dict(os.environ, EXT_ROOF_TYPE=roof),
            nach=(vorher,) if vorher else (), prio=2,
            schreibt=ext_kamera_key, liest=ext_kamera_key))
        vorher = name
    ext_namen = [f"ext:{roof}" for roof in roof_types]

    def erstes_aussen_log(ergebnisse):
        for roof in roof_types:
            if ergebnisse.get(f"ext:{roof}", (False, ""))[0]:
                return os.path.join(out_dir, f"exterior-{roof}-baseline.log")
        return None

    innen = {}                 # stil -> [(floor_index, floor_key, index, finish, name, png, blend, log)]
    # Welche Dateien ein Innen-Render liest und schreibt -- daraus stellt
    # datei_abhaengigkeiten() die serielle Reihenfolge je Datei her:
    #  - stem (png, blend, log, Zusatzbilder, .manifest.json, .blend1): mit
    #    --finishes koennen zwei Stile denselben Namen schreiben (Codex P1);
    #  - die Kameradatei (render-furnished-dollhouse.py KAMERA_INNEN_JSON):
    #    SCHREIBEN kann ein Render sie nur, wenn seine alte .blend hier liegt;
    #    nach jedem Bau liegt nur die Haupt-Innenszene je Geschoss noch hier,
    #    die anderen LESEN nur. Der Schluessel ist der aufgeloeste Pfad, auch
    #    mit DMH_KAMERA_JSON (dann teilen alle Geschosse eine Datei, Codex P2);
    #  - der Luftraum: ein oberes Geschoss mit Luftraum holt die Szene des
    #    Geschosses darunter (_geschoss_darunter_im_luftraum), und zwar die
    #    FRISCHE -- es braucht deren gelungenen Render (Codex P1).
    # Gemessen an bungalow_037: die volle Kette je Geschoss (4 x ~45 s) war
    # der Engpass; Leser derselben Kamera laufen nebeneinander.
    kamera_beruehrt = set()
    geschrieben = set()        # stems, die ein frueherer Auftrag schreibt
    erzeuger = {}              # blend-Schluessel -> Auftrag, der ihn baut
    oben_braucht_unten = set()
    primary = styles[0]
    plan_daten = {}
    for style in gute:
        try:
            with open(plaene[style], encoding="utf-8-sig") as handle:
                plan_daten[style] = json.load(handle)
        except (OSError, ValueError):
            plan_daten[style] = None
    for style in gute:
        finishes = requested_finishes or [f"{style}-a", f"{style}-b"]
        innen[style] = []
        for floor_index, floor_key in enumerate(floors):
            floor_tag = "" if floor_index == 0 else (
                "-upper" if floor_index == 1 else f"-floor{floor_index}")
            plan_index, plan_geschoss = _plan_geschoss(plan_daten[style], floor_key)
            for index, finish in enumerate(finishes):
                base = f"interior-{style}" if index == 0 else f"interior-{finish}"
                stem = f"{base}{floor_tag}-baseline"
                png = os.path.join(out_dir, f"{stem}.png")
                log = os.path.join(out_dir, f"{stem}.log")
                blend = os.path.join(out_dir, f"{stem}.blend")
                name = f"int:{style}:{floor_key}:{finish}"
                # Wesentlich: was die Lieferung behaelt (erste Ausfuehrung des
                # ersten Stils, jedes Geschoss) und die Hauptszene jedes Stils.
                # Eine fehlende -b oder ein classic-Obergeschoss verhinderte
                # das Zertifikat auch seriell nicht.
                wesentlich = index == 0 and (floor_index == 0 or style == primary)
                stem_key = datei_schluessel(os.path.join(out_dir, stem))
                kamera = _kamera_innen_pfad(blend, plan_index if plan_index is not None else floor_key)
                kamera_key = "kamera:" + (datei_schluessel(kamera) if kamera else f"?{floor_key}")
                kamera_schreiber = (kamera_key not in kamera_beruehrt or os.path.exists(blend)
                                    or stem_key in geschrieben)
                kamera_beruehrt.add(kamera_key)
                geschrieben.add(stem_key)
                unten = _luftraum_quelle(blend, plan_geschoss, floor_index)
                job = Auftrag(
                    name,
                    [BLENDER, *BLENDER_PY,
                     os.path.join(HERE, "render-furnished-dollhouse.py"), "--", plaene[style], png],
                    log_path=log,
                    env=dict(os.environ, DMH_SAVE_BLEND=blend, DMH_FINISH=finish,
                             DMH_FLOOR=floor_key),
                    wesentlich=wesentlich,
                    # Obere Geschosse zuerst: dort steht die Treppenpruefung R9.
                    prio=1 - floor_index * 0.01,
                    schreibt={stem_key} | ({kamera_key} if kamera_schreiber else set()),
                    liest={kamera_key},
                    braucht_dateien={"blend:" + datei_schluessel(unten)} if unten else ())
                if unten:
                    oben_braucht_unten.add("blend:" + datei_schluessel(unten))
                job.schreibt.add("blend:" + datei_schluessel(blend))
                erzeuger["blend:" + datei_schluessel(blend)] = job
                jobs.append(job)
                innen[style].append((floor_index, floor_key, index, finish, name, png, blend, log))
                jobs.append(Auftrag(
                    f"vb:{style}:{name}",
                    [BLENDER, *BLENDER_PY,
                     os.path.join(HERE, "verify_render_blend.py"), "--", blend, plaene[style]],
                    braucht=(name,), prio=-1, zeigen=_blend_zeilen,
                    liest={stem_key, "blend:" + datei_schluessel(blend)}))

        def vr_cmd(ergebnisse, style=style):
            aussen_log = erstes_aussen_log(ergebnisse)
            if aussen_log is None:
                return None
            return [PYTHON, os.path.join(HERE, "verify_render.py"), plaene[style],
                    "--annotations", annotations_path, "--log", aussen_log,
                    "--interior-log", os.path.join(out_dir, f"interior-{style}-baseline.log")]
        jobs.append(Auftrag(
            f"vr:{style}", vr_cmd,
            braucht=(innen[style][0][4],), nach=tuple(ext_namen), prio=0,
            zeigen=lambda ok, output: print(output),
            liest={datei_schluessel(os.path.join(out_dir, f"interior-{style}-baseline"))}))

    # Ein Geschoss, dessen Szene oben im Luftraum gebraucht wird, kommt vor
    # den anderen Innen-Renders dran -- sonst wartete das obere Geschoss (mit
    # der Treppenpruefung) am Ende der Schlange.
    for schluessel in oben_braucht_unten:
        if schluessel in erzeuger:
            erzeuger[schluessel].prio = 0.5
    datei_abhaengigkeiten(jobs)

    erg = abarbeiten(jobs, parallel)

    # --- Ergebnis zusammensetzen, wie die serielle Schleife ---------------
    roof_exteriors = {}
    for roof in roof_types:
        name = f"ext:{roof}"
        if erg.get(name, (False, ""))[0]:
            roof_exteriors[roof] = {
                "png": os.path.join(out_dir, f"exterior-{roof}-baseline.png"),
                "log": os.path.join(out_dir, f"exterior-{roof}-baseline.log"),
                "blend": os.path.join(out_dir, f"exterior-{roof}-baseline.blend"),
            }
        else:
            handoff["excluded"].append({"roof": roof, "reason": "exterior_render_failed"
                                        if name in erg else "abgebrochen"})

    for style in gute:
        print(f"\n[go] === {style} ===")
        if not roof_exteriors:
            handoff["excluded"].append({"style": style, "reason": "all_exteriors_failed"})
            continue
        exterior_png = next(iter(roof_exteriors.values()))["png"]
        finish_outputs = {}
        interior_png = interior_blend = None
        for floor_index, floor_key, index, finish, name, png, blend, log in innen[style]:
            if not erg.get(name, (False, ""))[0]:
                handoff["excluded"].append({"style": style, "finish": finish, "floor": floor_key,
                                            "reason": "interior_render_failed"
                                            if name in erg else "abgebrochen"})
                continue
            key = finish if floor_index == 0 else f"{finish}@{floor_key}"
            finish_outputs[key] = {"png": png, "blend": blend, "log": log, "floor": floor_key}
            if index == 0 and floor_index == 0:
                interior_png, interior_blend = png, blend
        if interior_png is None:
            continue

        scene_rules_ok = True
        for floor_index, floor_key, index, finish, name, png, blend, log in innen[style]:
            if not erg.get(name, (False, ""))[0]:
                continue
            vb = erg.get(f"vb:{style}:{name}")
            if not vb or not vb[0]:
                key = finish if floor_index == 0 else f"{finish}@{floor_key}"
                handoff["excluded"].append({"style": style, "finish": key,
                                            "reason": "scene_rules_failed" if vb else "abgebrochen"})
                scene_rules_ok = False

        vr = erg.get(f"vr:{style}")
        verify_ok = bool(vr and vr[0])
        if not verify_ok or not scene_rules_ok:
            if not verify_ok:
                handoff["excluded"].append({"style": style,
                                            "reason": "verify_render_failed" if vr else "abgebrochen",
                                            "detail": vr[1] if vr else ""})
            continue

        handoff["styles"][style] = {
            "plan": plaene[style],
            "exterior_baseline_blend": next(iter(roof_exteriors.values()))["blend"],
            "exterior_baseline_png": exterior_png,
            "interior_baseline_blend": interior_blend,
            "interior_baseline_png": interior_png,
            "interior_finishes": finish_outputs,
            "verified": True,
        }
    return roof_exteriors, roof_types


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("--styles", default="modern,classic")
    parser.add_argument("--corrected", metavar="REVISION.json",
                        help="build from a corrected revision instead of the "
                             "annotation proof path (step 10 of "
                             "plans/renderer-switch-execution-order.md). "
                             "Explicit: no project is switched by accident.")
    # The package is 4 interiors + 2 exteriors: each furniture style
    # (modern/classic model picks) rendered in two FINISH sets (wall tone,
    # floor tint, kitchen fronts, upholstery -- FINISH_SETS in
    # render-furnished-dollhouse.py, selected with DMH_FINISH). The exterior
    # does not depend on the interior finish, so it is still rendered once
    # per style, giving 2.
    parser.add_argument("--finishes", default="",
                        help="comma list of DMH_FINISH sets to render per "
                             "style; default <style>-a,<style>-b")
    # onehalfstorey_020 is a full TWO-storey house (its metadata claiming
    # 1.5-storey is a known wrong record). Everything before 2026-08-17
    # rendered floors[0] only, so the upper storey's 18 furniture items had
    # never appeared in any deliverable.
    parser.add_argument("--floors", default="0",
                        help="comma list of storeys to render as interiors: "
                             "indices (0,1) or floor ids (floor-0,floor-1)")
    args = parser.parse_args()
    styles = [s.strip() for s in args.styles.split(",") if s.strip()]
    requested_finishes = [f.strip() for f in args.finishes.split(",") if f.strip()]
    floors = [f.strip() for f in args.floors.split(",") if f.strip()] or ["0"]

    annotations_path = os.path.join(SIMPLIFIER, "projects", args.project_id, "annotations.json")
    if not os.path.exists(annotations_path):
        print(f"[go] FATAL: no annotations at {annotations_path}")
        sys.exit(1)

    out_dir = os.path.join(DATA_REPO, "corrections", args.project_id, "renders", "go-baseline")
    os.makedirs(out_dir, exist_ok=True)

    lock = acquire_lock(out_dir, args.project_id)
    if lock is None:
        sys.exit(2)                      # 2 = belegt, nicht "Build kaputt"
    atexit.register(release_lock, lock)

    handoff = {
        "schema": "codex-handoff-v1",
        "project_id": args.project_id,
        "annotations_source": annotations_path,
        "output_dir_for_images_and_catalog": out_dir,
        "catalog_json_path": os.path.join(out_dir, "catalog.json"),
        "styles": {},
        "excluded": [],
        "instructions": (
            "Produce style/mood variants FROM these verified baselines. "
            "Structure (walls, windows, doors, room layout) must not "
            "change -- material, lighting, atmosphere only. Write images "
            "plus a catalog.json (schema visual-catalog-v1, one entry per "
            "image, each with geometry_source pointing at the matching "
            "*_baseline.blend below and geometry_reference_render pointing "
            "at the matching *_baseline.png) to output_dir_for_images_and_catalog."
        ),
    }

    # All 4 roof forms, from the FIRST style's plan only -- roof geometry is
    # a late, separate build step in render-exterior.py, so the plan's
    # walls/materials don't need to vary per roof form (see ROOF_TYPES
    # above). Built once, before the per-style loop, so every style's
    # verify_render.py call below has an exterior log to check wall
    # angles/openings against (those don't depend on roof shape, so sharing
    # one across styles is correct, not a shortcut).
    roof_exteriors = {}
    roof_types = ROOF_TYPES

    # BAU-SCHNELLER-001: parallel, ausser BAU_PARALLEL=1 -- dann laeuft die
    # Schleife unten genau wie bisher, Auftrag fuer Auftrag.
    parallel = bau_parallel()
    if parallel > 1:
        roof_exteriors, roof_types = _bauen_parallel(
            args, styles, requested_finishes, floors, out_dir, annotations_path,
            handoff, parallel)
    for style in (styles if parallel <= 1 else []):
        print(f"\n[go] === {style} ===")
        plan_path = os.path.join(out_dir, f"plan-{style}.json")
        if args.corrected:
            plan_cmd = [PYTHON, os.path.join(HERE, "build-simplifier-render-plan.py"),
                        "--correction-revision", args.corrected, style, plan_path]
        else:
            plan_cmd = [PYTHON, os.path.join(HERE, "build-simplifier-render-plan.py"),
                        args.project_id, style, plan_path]
        ok, _ = run(plan_cmd, env=PLAN_ENV)
        if not ok:
            handoff["excluded"].append({"style": style, "reason": "plan_build_failed"})
            continue

        if not roof_exteriors:
            roof_types = roof_types_for_plan(plan_path)
            # Vor dem ersten Blender-Aufruf (BAU-SCHNELLER-001). Keine
            # "[go] "-Zeile: go.py abbruchgrund() ueberspringt die.
            grund = vorpruefung_datei(plan_path, roof_types)
            if grund:
                print(f"Vorpruefung: {grund}")
                handoff["excluded"].append({"style": style, "reason": "vorpruefung",
                                            "detail": grund})
                break
            for roof in roof_types:
                roof_png = os.path.join(out_dir, f"exterior-{roof}-baseline.png")
                roof_log = os.path.join(out_dir, f"exterior-{roof}-baseline.log")
                roof_env = dict(os.environ, EXT_ROOF_TYPE=roof)
                roof_ok, _ = run([BLENDER, *BLENDER_PY,
                                 os.path.join(HERE, "render-exterior.py"), "--",
                                 plan_path, roof_png],
                                log_path=roof_log, env=roof_env)
                if roof_ok:
                    roof_exteriors[roof] = {
                        "png": roof_png, "log": roof_log,
                        "blend": os.path.join(out_dir, f"exterior-{roof}-baseline.blend"),
                    }
                else:
                    handoff["excluded"].append({"roof": roof, "reason": "exterior_render_failed"})
            if not roof_exteriors:
                handoff["excluded"].append({"style": style, "reason": "all_exteriors_failed"})
                continue

        # Kept for backward compatibility with anything still reading a
        # single exterior_baseline_* per style (e.g. an older catalog.json
        # generator) -- points at whichever roof form built successfully
        # first. New consumers should read `handoff["roof_exteriors"]`.
        exterior_png = next(iter(roof_exteriors.values()))["png"]
        exterior_log = next(iter(roof_exteriors.values()))["log"]

        finishes = requested_finishes or [f"{style}-a", f"{style}-b"]
        # The first finish keeps the historic filenames, so the overview tab,
        # verify_render and every existing catalog.json entry still resolve.
        # Further finishes are named after the finish itself.
        finish_outputs = {}
        interior_png = interior_blend = None
        for floor_index, floor_key in enumerate(floors):
            # Storey 0 keeps the historic names; further storeys are tagged,
            # so nothing that already resolves an existing path breaks.
            floor_tag = "" if floor_index == 0 else (
                "-upper" if floor_index == 1 else f"-floor{floor_index}")
            for index, finish in enumerate(finishes):
                base = f"interior-{style}" if index == 0 else f"interior-{finish}"
                stem = f"{base}{floor_tag}-baseline"
                png = os.path.join(out_dir, f"{stem}.png")
                log = os.path.join(out_dir, f"{stem}.log")
                blend = os.path.join(out_dir, f"{stem}.blend")
                env = dict(os.environ, DMH_SAVE_BLEND=blend, DMH_FINISH=finish,
                           DMH_FLOOR=floor_key)
                ok, _ = run([BLENDER, *BLENDER_PY,
                             os.path.join(HERE, "render-furnished-dollhouse.py"),
                             "--", plan_path, png],
                            log_path=log, env=env)
                if not ok:
                    handoff["excluded"].append({"style": style, "finish": finish,
                                                "floor": floor_key,
                                                "reason": "interior_render_failed"})
                    if index == 0 and floor_index == 0:
                        break
                    continue
                key = finish if floor_index == 0 else f"{finish}@{floor_key}"
                finish_outputs[key] = {"png": png, "blend": blend, "log": log,
                                       "floor": floor_key}
                if index == 0 and floor_index == 0:
                    interior_png, interior_blend = png, blend
            if interior_png is None:
                break
        if interior_png is None:
            continue

        # The interior log carries the evidence for Rainer's rules (R0-R5),
        # so verification fails the style if any of them was broken.
        scene_rules_ok = True
        # HARD RULE gate. verify_render.py reads the plan and the logs;
        # verify_render_blend.py opens the SCENE and answers from geometry,
        # which is the only check that could not be fooled by a renderer that
        # reports a Treppenloch it never cut. Every interior scene goes
        # through it, and a failure excludes the style.
        for finish_key, outputs in finish_outputs.items():
            blend_ok, blend_output = run(
                [BLENDER, *BLENDER_PY,
                 os.path.join(HERE, "verify_render_blend.py"), "--",
                 outputs["blend"], plan_path])
            for line in blend_output.splitlines():
                if line.startswith(("PASS", "FAIL", "  -", "[verify-blend]")):
                    print(line)
            if not blend_ok:
                handoff["excluded"].append({"style": style, "finish": finish_key,
                                            "reason": "scene_rules_failed"})
                scene_rules_ok = False

        verify_ok, verify_output = run([PYTHON, os.path.join(HERE, "verify_render.py"), plan_path,
                                        "--annotations", annotations_path, "--log", exterior_log,
                                        "--interior-log",
                                        os.path.join(out_dir, f"interior-{style}-baseline.log")])
        print(verify_output)
        if not verify_ok or not scene_rules_ok:
            if not verify_ok:
                handoff["excluded"].append({"style": style, "reason": "verify_render_failed",
                                            "detail": verify_output})
            continue

        handoff["styles"][style] = {
            "plan": plan_path,
            # Backward-compat single exterior reference -- see roof_exteriors
            # for all 4. Points at whichever roof form rendered first.
            "exterior_baseline_blend": next(iter(roof_exteriors.values()))["blend"],
            "exterior_baseline_png": exterior_png,
            "interior_baseline_blend": interior_blend,
            "interior_baseline_png": interior_png,
            "interior_finishes": finish_outputs,
            "verified": True,
        }

    handoff["roof_exteriors"] = roof_exteriors

    # The rule is enforced by the build, so a delivery folder is never left
    # holding a surplus for someone to trim by hand.
    trim_to_delivery(out_dir, styles[0] if styles else "modern", floors, roof_types)

    # Certify the delivery only if everything expected is present and verified.
    manifest = write_delivery_manifest(out_dir, args.project_id, floors,
                                       sorted(handoff["styles"].keys()),
                                       len(roof_types) + len(floors), requested=styles)

    handoff_path = os.path.join(out_dir, "handoff.json")
    with open(handoff_path, "w", encoding="utf-8") as f:
        json.dump(handoff, f, indent=2)
    print(f"\n[go] wrote {handoff_path}")
    print(f"[go] {len(handoff['styles'])} style(s) verified and ready, {len(handoff['excluded'])} excluded")

    # The exit code says DELIVERED, not "something rendered". It used to be
    # `0 if any_style_ok`, so a house that lost one of its two styles still
    # reported success: measured 2026-08-20 on bungalow_040_66, where Blender
    # died with EXCEPTION_ACCESS_VIOLATION on the classic interior, the batch
    # printed "ok", no manifest was written -- and the next batch would have
    # rebuilt it and printed "ok" again, indefinitely, with nobody told.
    #
    # Tying the code to the manifest makes the two agree by construction:
    # exit 0 exactly when a certificate exists. (2 stays reserved for "another
    # process holds the build lock".)
    if not manifest:
        print("[go] FEHLGESCHLAGEN: keine zertifizierte Lieferung "
              "(%d Stil(e) verifiziert, %d ausgeschlossen)"
              % (len(handoff["styles"]), len(handoff["excluded"])))
    sys.exit(0 if manifest else 1)


if __name__ == "__main__":
    main()
