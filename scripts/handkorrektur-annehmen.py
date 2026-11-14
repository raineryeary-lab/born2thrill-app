"""Rainers Handkorrektur in einer gebauten .blend annehmen (handkorrektur-v1).

Rainer, 2026-11-12: "der fehler stimmt nicht ich musste neu bauen und selber
korrigieren gib das so frei bitte". Korrigiert er eine .blend nach dem Bau in
Blender, passt sie nicht mehr zu ihrem Zertifikat (delivery-manifest.json) und
der Codex-Schritt meldet "Bau veraltet". Dieses Skript zieht das Zertifikat
fuer genau die geaenderten .blend-Dateien nach -- nur wenn sonst alles stimmt
(Renderer, Moebel, Zeichnung unveraendert). Sicherung:
delivery-manifest.json.before-handkorrektur-<zeit>.

  python handkorrektur-annehmen.py <plan>

Achtung: Ein neuer Bau ueberschreibt die Handkorrektur wieder.
Letzte Zeile der Ausgabe: JSON.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def batch():
    spec = importlib.util.spec_from_file_location("batch_build", os.path.join(HERE, "batch-build.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def annehmen(plan):
    b = batch()
    ordner = os.path.join(b.DATA, "corrections", plan, "renders", "go-baseline")
    pfad = os.path.join(ordner, "delivery-manifest.json")
    with open(pfad, encoding="utf-8") as f:
        m = json.load(f)
    if m.get("toolchain") != b.toolchain_now():
        raise SystemExit("Renderer geaendert -- das ist keine Handkorrektur, neu bauen.")
    jetzt, grund = b.annotation_state(plan)
    if grund or not jetzt or jetzt != m.get("input_hash"):
        raise SystemExit("Zeichnung oder Mass seit dem Bau geaendert -- neu bauen.")
    geaendert = []
    for a in m.get("artifacts") or []:
        datei = os.path.join(ordner, a.get("file", ""))
        if not os.path.exists(datei):
            raise SystemExit(f"{a.get('file')} fehlt -- neu bauen.")
        h = hashlib.sha256(open(datei, "rb").read()).hexdigest()
        if os.path.getsize(datei) != a.get("bytes") or (a.get("sha256") and h != a["sha256"]):
            a.setdefault("bytes_vor_handkorrektur", a.get("bytes"))
            a.setdefault("sha256_vor_handkorrektur", a.get("sha256"))
            a["bytes"], a["sha256"] = os.path.getsize(datei), h
            a["handkorrektur"] = {"von": "Rainer", "am": time.strftime("%Y-%m-%dT%H:%M:%S")}
            geaendert.append(a["file"])
    if not geaendert:
        return {"ok": True, "plan": plan, "geaendert": [], "hinweis": "nichts zu tun"}
    shutil.copy2(pfad, pfad + ".before-handkorrektur-" + time.strftime("%Y%m%d-%H%M%S"))
    with open(pfad + ".tmp", "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
    os.replace(pfad + ".tmp", pfad)
    if b.built_hash(plan) is None:
        raise SystemExit("Zertifikat nachgezogen, gilt aber noch nicht (Moebel geaendert?) -- neu bauen.")
    return {"ok": True, "plan": plan, "geaendert": geaendert}


if __name__ == "__main__":
    print(json.dumps(annehmen(sys.argv[1]), ensure_ascii=True))
