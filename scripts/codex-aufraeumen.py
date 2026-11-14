"""Raeumt die Codex-Einstellungen auf (Plan CODEX-FLOTT-001, Schritte 1 und 3).

Nur bei geschlossenem Codex. Loescht nichts: alte Dateien bleiben als Sicherung.

    python scripts/codex-aufraeumen.py            aufraeumen
    python scripts/codex-aufraeumen.py --zurueck  Sicherungen zurueckspielen

- entfernt die G:-Projekte aus config.toml
- traegt C:\\dev\\Codex-Haus als Projekt ein
- gibt Schreibrecht zusaetzlich nur fuer corrections auf E:
- entfernt aus default.rules alle G:-Regeln und die langen Einmal-Befehle
"""
import argparse
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ARBEITSORDNER = r"c:\dev\codex-haus"
CORRECTIONS = r"E:\born2thrill-local-workbench-data\corrections"
MAX_REGEL_LAENGE = 300
ENDUNG = ".before-aufraeumen"


def codex_laeuft():
    aus = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    # Der Windows-Dienst codex-windows-sandbox-service laeuft immer mit, auch bei geschlossener App.
    return bool(re.search(r'^"codex(?!-windows-sandbox-service)[^"]*\.exe"', aus, re.I | re.M))


def config_aufraeumen(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    bloecke = re.split(r"(?m)^(?=\[)", text)
    behalten = [b for b in bloecke if not re.match(r"\[projects\.'g:", b, re.I)]
    neu = "".join(behalten).rstrip() + nl
    if f"[projects.'{ARBEITSORDNER}']" not in neu:
        neu += f"{nl}[projects.'{ARBEITSORDNER}']{nl}trust_level = \"trusted\"{nl}"
    if "[sandbox_workspace_write]" not in neu:
        neu += f"{nl}[sandbox_workspace_write]{nl}writable_roots = ['{CORRECTIONS}']{nl}"
    return neu


def regeln_aufraeumen(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    zeilen = [z for z in text.splitlines() if z.strip()]
    gut = [z for z in zeilen if "G:\\\\" not in z and len(z) <= MAX_REGEL_LAENGE]
    return nl.join(gut) + nl, len(zeilen), len(gut)


def aufraeumen(home):
    config = home / "config.toml"
    regeln = home / "rules" / "default.rules"
    for datei in (config, regeln):
        sicherung = datei.with_name(datei.name + ENDUNG)
        if not sicherung.exists():
            shutil.copy2(datei, sicherung)
    alt = config.read_text(encoding="utf8")
    neu = config_aufraeumen(alt)
    tomllib.loads(neu)
    config.write_text(neu, encoding="utf8", newline="")
    text, vorher, nachher = regeln_aufraeumen(regeln.read_text(encoding="utf8"))
    regeln.write_text(text, encoding="utf8", newline="")
    print(f"config.toml: {alt.count(chr(10))} -> {neu.count(chr(10))} Zeilen")
    print(f"default.rules: {vorher} -> {nachher} Regeln")


def zurueck(home):
    for datei in (home / "config.toml", home / "rules" / "default.rules"):
        shutil.copy2(datei.with_name(datei.name + ENDUNG), datei)
    print("Sicherungen zurueckgespielt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zurueck", action="store_true")
    parser.add_argument("--home", default=str(Path.home() / ".codex"))
    args = parser.parse_args()
    home = Path(args.home)
    if home == Path.home() / ".codex" and codex_laeuft():
        print("Codex laeuft noch. Bitte erst die App ganz schliessen.")
        return 1
    zurueck(home) if args.zurueck else aufraeumen(home)
    return 0


if __name__ == "__main__":
    sys.exit(main())
