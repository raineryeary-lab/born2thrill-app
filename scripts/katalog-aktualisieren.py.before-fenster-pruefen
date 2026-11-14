"""Grundriss-Katalog automatisch nachziehen (katalog-automatisch-v1).

Rainer, 2026-11-07: "i just built a bungalow 3 zimmer over 600k why doesn't it
show in the grundrisscatalog" -- und dann: "this has to go automatically".
Bis heute legte nur publish-renders.py (beim Bilder-Hochladen) eine
Katalogzeile an, und Matrix, Fragebogen-Filter, Countdown und Preistabelle
waren Schnappschuesse, die jemand von Hand neu erzeugen und in WordPress
einfuegen musste.

Ein Lauf:
  1. konfigurator-matrix.py neu rechnen.
  2. Jedes Haus der Matrix, das im Katalog fehlt: Zeile anlegen
     (katalogzeile.py -> b2t/v1/grundriss-anlegen, nur INSERT), Grundrissbild
     zeichnen (katalog-grundriss-bilder.py) und in die Mediathek laden.
     Nie `approved`, nie eine Freigabe, nie eine E-Mail (REGELN 10).
     CubiCasa-Plaene bleiben draussen (Rechte, corpus_rights_blocker).
  3. Snippets 10, 11, 12 neu erzeugen und nur bei Aenderung ueber die
     Code-Snippets-API ersetzen.

Zugang: WP_USER / WP_APP_PASSWORD aus .env.local (wie publish-renders.py).
Aufruf: python katalog-aktualisieren.py [--trocken]
Der Annotator startet es nach jedem Speichern im Hintergrund (gebremst).
"""

import csv
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.abspath(os.path.join(HERE, "..", ".."))
PROJEKTE = os.path.join(SUITE, "floorplan-simplifier", "projects")
SITE = "https://born2thrill.de"
WORDPRESS = os.path.join(HERE, "..", "wordpress")
# Snippet-ID -> (Generator, erzeugte Datei)
SNIPPETS = {
    10: ("katalog-fragebogen-snippet.py", "katalog-fragebogen-filter.php"),
    11: ("katalog-countdown-snippet.py", "katalog-countdown.php"),
    12: ("katalog-preistabelle-snippet.py", "katalog-preistabelle.php"),
}
NIE_IN_DEN_KATALOG = ("cubicasa",)


def _lade(datei, name):
    argv, sys.argv = sys.argv, ["x"]
    try:
        spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, datei))
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
    finally:
        sys.argv = argv
    return modul


def datenordner():
    pr = publish()
    pr._lade_env_local()
    wert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
    if not wert:
        pfad = os.path.join(HERE, "..", ".env.local")
        for zeile in open(pfad, encoding="utf-8-sig"):
            if zeile.startswith("FLOORPLAN_WORKBENCH_DATA_DIR="):
                wert = zeile.split("=", 1)[1].strip().strip('"')
        os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"] = wert
    return wert


_PR = None


def publish():
    global _PR
    if _PR is None:
        _PR = _lade("publish-renders.py", "publish_renders_auto")
    return _PR


def python(skript, *argumente):
    ergebnis = subprocess.run([sys.executable, os.path.join(HERE, skript), *argumente],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=dict(os.environ))
    if ergebnis.returncode != 0:
        raise RuntimeError(f"{skript}: {ergebnis.stderr.strip()[-400:]}")
    return ergebnis.stdout


def snippet_code(php_text):
    """Was in Code Snippets steht: die Datei ohne die oeffnende PHP-Marke."""
    text = php_text.replace("\r\n", "\n")
    if text.startswith("<?php"):
        text = text[len("<?php"):].lstrip("\n")
    return text.rstrip("\n")


def ohne_stand(code):
    """Der Zeitstempel allein ist keine Aenderung (sonst jedes Mal ersetzen)."""
    return re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", "", code)


def fehlende_plaene(matrix_plaene, katalog_ids):
    return [p for p in matrix_plaene
            if p not in katalog_ids and not p.lower().startswith(NIE_IN_DEN_KATALOG)]


def neue_zeilen(daten, katalog_ids, auth, trocken):
    pr = publish()
    katalogzeile = _lade("katalogzeile.py", "katalogzeile_auto")
    with open(os.path.join(daten, "konfigurator-matrix.csv"), encoding="utf-8-sig") as f:
        plaene = [z["plan"] for z in csv.DictReader(f, delimiter=";")]
    angelegt = []
    for plan in fehlende_plaene(plaene, katalog_ids):
        zeile = katalogzeile.zeile_aus_projekt(os.path.join(PROJEKTE, plan))
        if trocken:
            print(f"  wuerde anlegen  {plan}")
            continue
        antwort = pr.request(SITE + "/wp-json/b2t/v1/grundriss-anlegen", method="POST",
                             body=json.dumps(zeile).encode("utf-8"),
                             headers={"Authorization": auth, "Content-Type": "application/json"})
        if not (antwort or {}).get("ok"):
            raise RuntimeError(f"grundriss-anlegen {plan}: {antwort}")
        ziel = os.path.join(daten, "katalog-grundrisse")
        python("katalog-grundriss-bilder.py", ziel, plan)
        name = f"{plan}-grundriss.png"
        pr.upload(SITE, os.path.join(ziel, name), name, auth)
        print(f"  angelegt  {plan}  (Zeile + Grundrissbild)")
        angelegt.append(plan)
    return angelegt


def snippets_ersetzen(auth, trocken):
    pr = publish()
    geaendert = []
    for nummer, (generator, datei) in SNIPPETS.items():
        python(generator)
        with open(os.path.join(WORDPRESS, datei), encoding="utf-8") as f:
            neu = snippet_code(f.read())
        url = f"{SITE}/wp-json/code-snippets/v1/snippets/{nummer}"
        alt = pr.request(url, headers={"Authorization": auth})
        if ohne_stand(snippet_code(alt.get("code") or "")) == ohne_stand(neu):
            continue
        if trocken:
            print(f"  wuerde ersetzen  Snippet {nummer}")
            continue
        antwort = pr.request(url, method="POST", body=json.dumps({"code": neu}).encode("utf-8"),
                             headers={"Authorization": auth, "Content-Type": "application/json"})
        if snippet_code(antwort.get("code") or "") != neu or not antwort.get("active"):
            raise RuntimeError(f"Snippet {nummer} nicht sauber gespeichert")
        print(f"  ersetzt  Snippet {nummer} ({alt.get('name')})")
        geaendert.append(nummer)
    return geaendert


def main():
    trocken = "--trocken" in sys.argv
    daten = datenordner()
    pr = publish()
    auth = pr.auth_header()
    python("konfigurator-matrix.py")
    katalog_ids = {r.get("id") for r in pr.request(SITE + "/wp-json/b2t/v1/grundrisse")}
    angelegt = neue_zeilen(daten, katalog_ids, auth, trocken)
    geaendert = snippets_ersetzen(auth, trocken)
    print(f"fertig: {len(angelegt)} neu im Katalog, Snippets ersetzt: {geaendert or 'keine'}")


if __name__ == "__main__":
    main()
