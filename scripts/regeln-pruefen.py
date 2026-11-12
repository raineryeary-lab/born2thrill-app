"""Prueft das Regelbuch: Laenge, Verbindung zu Codex, keine G:-Arbeitsorte.

    python scripts/regeln-pruefen.py              nur pruefen, Exit 1 bei Fehlern
    python scripts/regeln-pruefen.py --reparieren Codex-Verbindung neu anlegen
"""
import argparse
import os
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
REGELN = WURZEL / "REGELN.md"
CODEX = Path.home() / ".codex" / "AGENTS.md"
MAX_ZEILEN = 60
AKTIVE_REGELDATEIEN = [
    "born2thrill-local-workbench/AGENTS.md",
    "born2thrill-local-workbench/docs/CODEX-REGELN-4PLUS2.md",
    "floorplan-simplifier/AGENTS.md",
    "WORKFLOW.md",
]
G_ARBEITSORT = re.compile(r"_CodexSync|My Drive")
# Beschlossen und einmal schon verloren: Die Bereinigung vom 2026-09-03 lag nur in
# der Kopie eines Hauses. Geprueft wird deshalb die Quelle, aus der jeder Auftrag entsteht.
QUELLEN = ["born2thrill-local-workbench/docs/CODEX-REGELN-4PLUS2.md"]
ALTE_FASSUNG = re.compile(r"symmetrische Anordnungen|sechs Dateien bei")


def pruefen(regeln=REGELN, codex=CODEX, dateien=None):
    fehler = []
    if not regeln.exists():
        return [f"{regeln} fehlt"]
    zeilen = len(regeln.read_text(encoding="utf8").splitlines())
    if zeilen > MAX_ZEILEN:
        fehler.append(f"{regeln.name} hat {zeilen} Zeilen, erlaubt sind {MAX_ZEILEN}")
    if not codex.exists() or not os.path.samefile(regeln, codex):
        fehler.append(f"{codex} ist nicht mit {regeln.name} verbunden")
    for datei in (dateien if dateien is not None else [WURZEL / d for d in AKTIVE_REGELDATEIEN]):
        for nr, zeile in enumerate(Path(datei).read_text(encoding="utf8").splitlines(), 1):
            if G_ARBEITSORT.search(zeile):
                fehler.append(f"{datei}:{nr} nennt G: als Arbeitsort")
    if dateien is None:
        for datei in QUELLEN:
            for nr, zeile in enumerate((WURZEL / datei).read_text(encoding="utf8").splitlines(), 1):
                if ALTE_FASSUNG.search(zeile):
                    fehler.append(f"{datei}:{nr} enthaelt eine ueberholte Regel")
    return fehler


def reparieren(regeln=REGELN, codex=CODEX):
    if codex.exists() and not os.path.samefile(regeln, codex):
        codex.replace(codex.with_name("AGENTS.md.vor-reparatur"))
    if not codex.exists():
        os.link(regeln, codex)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reparieren", action="store_true")
    if parser.parse_args().reparieren:
        reparieren()
    fehler = pruefen()
    for f in fehler:
        print("FEHLER", f)
    print("Regelbuch in Ordnung" if not fehler else f"{len(fehler)} Fehler")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
