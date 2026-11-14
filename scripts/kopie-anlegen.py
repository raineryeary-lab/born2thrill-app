"""Knopf "Kopie anlegen" auf /haus (kopie-anlegen-v1, Rainer 2026-11-10:
"ich denke wir brauchen dafuer einen knopf irgendwo").

Ein Schritt statt drei Skripte:
  1. haus-skalieren.py  -- Vorschau, mit --anlegen auch die Kopie
  2. Moebel der Vorlage in die Kopie (moebel-uebertragen.py, Raum fuer Raum)
  3. Moebel-Stempel der Kopie auf ihre eigenen Raeume setzen

  python kopie-anlegen.py <quelle> --flaeche 130                 nur Vorschau
  python kopie-anlegen.py <quelle> --flaeche 130 --anlegen <neu> Kopie + Moebel

Die Quelle wird nie veraendert. Letzte Zeile der Ausgabe: JSON.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.abspath(os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects"))
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"
PY = sys.executable
BUILD = os.path.join(HERE, "build-simplifier-render-plan.py")


def lauf(args):
    r = subprocess.run([PY] + args, cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode != 0:
        raise SystemExit((r.stdout + "\n" + r.stderr).strip() or "fehlgeschlagen: %s" % args)
    return r.stdout


def moebel_uebertragen(quelle, neu):
    q_dir = os.path.join(DATA, "corrections", quelle, "furniture")
    if not os.path.isdir(q_dir):
        return "Vorlage hat keine Moebel -- in der Kopie einrichten."
    z_dir = os.path.join(DATA, "corrections", neu, "furniture")
    os.makedirs(z_dir, exist_ok=True)
    dateien = sorted(f for f in os.listdir(q_dir) if re.fullmatch(r"floor-\d+\.json", f))
    for f in dateien:
        with open(os.path.join(q_dir, f), encoding="utf-8") as h:
            d = json.load(h)
        d["project_id"] = neu
        with open(os.path.join(z_dir, f), "w", encoding="utf-8") as h:
            json.dump(d, h, ensure_ascii=False, indent=2)
    tmp = tempfile.mkdtemp(prefix="kopie-")
    try:
        gq, gz = os.path.join(tmp, "q.json"), os.path.join(tmp, "z.json")
        lauf([BUILD, "--geometry-only", quelle, gq])
        lauf([BUILD, "--geometry-only", neu, gz])
        bericht = lauf([os.path.join(HERE, "moebel-uebertragen.py"), gq, gz, quelle, neu, "--schreiben"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # Stempel: die Moebel gehoeren jetzt zu den Raeumen der KOPIE.
    for f in dateien:
        pfad = os.path.join(z_dir, f)
        with open(pfad, encoding="utf-8") as h:
            d = json.load(h)
        treffer = re.findall(r"^[0-9a-f]{64}$", lauf([BUILD, "--geometrie-id", neu, f[:-5]]), re.M)
        kennung = treffer[-1] if treffer else ""
        if kennung:
            d["geometry_identity"] = kennung
        with open(pfad, "w", encoding="utf-8") as h:
            json.dump(d, h, ensure_ascii=False, indent=2)
        bak = pfad + ".before-uebertragen"
        if os.path.exists(bak):
            os.remove(bak)
    return bericht


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quelle")
    ap.add_argument("--flaeche", type=float, required=True)
    ap.add_argument("--anlegen", metavar="NEU")
    a = ap.parse_args()
    if not os.path.isdir(os.path.join(PROJECTS, a.quelle)):
        raise SystemExit("Keine Vorlage: %s" % a.quelle)
    ergebnis = {"quelle": a.quelle, "flaeche": a.flaeche}
    skal = [os.path.join(HERE, "haus-skalieren.py"), a.quelle, "--flaeche", "%g" % a.flaeche]
    if a.anlegen:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", a.anlegen):
            raise SystemExit("Name nur aus Buchstaben, Ziffern, _ . -")
        if os.path.exists(os.path.join(PROJECTS, a.anlegen)):
            raise SystemExit("%s gibt es schon -- nichts geaendert" % a.anlegen)
        skal += ["--anlegen", a.anlegen]
    text = lauf(skal)
    ergebnis["text"] = text.strip()
    m = re.search(r"^Vorschau: (.+)$", text, re.M)
    ergebnis["vorschau"] = m.group(1).strip() if m else ""
    if a.anlegen:
        ziel = os.path.join(PROJECTS, a.anlegen)
        for name in ("data.json", "training-data.json"):
            p = os.path.join(ziel, name)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as h:
                    d = json.load(h)
                d["project_id"] = a.anlegen
                with open(p, "w", encoding="utf-8") as h:
                    json.dump(d, h, ensure_ascii=False, indent=2)
        ergebnis["moebel"] = moebel_uebertragen(a.quelle, a.anlegen).strip()
        ergebnis["neu"] = a.anlegen
    print(json.dumps(ergebnis, ensure_ascii=True))


if __name__ == "__main__":
    main()
