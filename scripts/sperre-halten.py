#!/usr/bin/env python3
"""Eine Betriebssystem-Sperre fuer einen anderen Prozess halten (ZUVERLAESSIGKEIT-001, Runde 5).

    python sperre-halten.py <sperrdatei> [--frist SEKUNDEN]

Node kann keine Betriebssystem-Sperre auf eine Datei legen. Die Statusroute
startet deshalb dieses Skript als Kind:

- Es nimmt die Sperre (os_sperre, wie go.py und publish-renders.py) und
  wartet dafuer hoechstens --frist Sekunden (Vorgabe 10).
- Hat es sie, schreibt es "GESPERRT" auf stdout und haelt sie, bis stdin
  zugeht. Die Route schliesst stdin, wenn sie fertig geschrieben hat.
- Stirbt die Route (oder der ganze Next-Server), geht stdin ebenfalls zu,
  und das Skript gibt frei. Stirbt das Skript selbst, gibt das
  Betriebssystem frei.
- Bekommt es die Sperre nicht rechtzeitig: "BESETZT<besitzer>", Ausgang 2.

Es gibt keinen Zeitablauf: eine Sperre, deren Halter lebt, bekommt niemand
(Codex Runde 5, N1 -- die Generationen-Sperre der Runde 4 uebernahm nach
120 s auch von einem lebenden, nur langsamen Besitzer).

Ledger-Modus (Runde 6):

    python sperre-halten.py <sperrdatei> --ledger <ledgerdatei> [--frist S]

Codex Runde 5: solange NODE schrieb, konnte der Halter sterben, waehrend
Node weiterlief und dann ohne Sperre schrieb. Jetzt schreibt nur noch,
wer die Sperre haelt -- dieses Skript -- und zwar als Vergleichen-und-
Tauschen:

1. Nach "GESPERRT" liest es das Ledger und schreibt eine Zeile
   ``LEDGER {"basis": sha256|"LEER", "text": str|null, "fehler": str|null}``.
   Nur eine FEHLENDE Datei ist "LEER"; unlesbar gibt "fehler".
2. Node gleicht ab und schickt GENAU EINE Zeile: ``ABBRUCH`` oder
   ``{"basis": ..., "inhalt": "<JSON-Text>"}``.
3. Noch unter der Sperre: Datei neu lesen, Basis vergleichen. Gleich ->
   tmp + os.replace, ``GESCHRIEBEN``. Anders -> ``VERALTET``. Inhalt kein
   JSON-Objekt -> ``VERWEIGERT``. Stirbt dieses Skript vorher, wurde nichts
   geschrieben.
"""
import hashlib
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os_sperre  # noqa: E402


LEER = "LEER"


def ledger_stand(pfad):
    """(basis, text, fehler) des Ledgers, wie es JETZT auf der Platte steht."""
    try:
        with open(pfad, "rb") as handle:
            roh = handle.read()
    except FileNotFoundError:
        return LEER, None, None
    except OSError as error:
        return None, None, "Ledger unlesbar: %s" % error
    try:
        text = roh.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, None, "Ledger nicht UTF-8: %s" % error
    return hashlib.sha256(roh).hexdigest(), text, None


def ledger_tauschen(pfad, zeile):
    """Eine Antwortzeile von Node ausfuehren; gibt die Ergebniszeile zurueck."""
    zeile = zeile.strip()
    if not zeile or zeile == "ABBRUCH":
        return None
    try:
        auftrag = json.loads(zeile)
        basis = auftrag["basis"]
        inhalt = auftrag["inhalt"]
        if not isinstance(inhalt, str) or not isinstance(json.loads(inhalt), dict):
            return "VERWEIGERT kein JSON-Objekt"
    except (ValueError, KeyError, TypeError) as error:
        return "VERWEIGERT %s" % error
    jetzt, _text, fehler = ledger_stand(pfad)
    if fehler or jetzt != basis:
        return "VERALTET"
    ordner = os.path.dirname(os.path.abspath(pfad))
    tmp = os.path.join(ordner, "%s.%d.%s.tmp" % (os.path.basename(pfad), os.getpid(), uuid.uuid4().hex))
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(inhalt)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, pfad)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return "GESCHRIEBEN"


def main(argv):
    if not argv:
        print("Aufruf: sperre-halten.py <sperrdatei> [--frist SEKUNDEN] [--ledger DATEI]",
              file=sys.stderr)
        return 64
    pfad = argv[0]
    frist = 10.0
    if "--frist" in argv:
        frist = float(argv[argv.index("--frist") + 1])
    ledger = argv[argv.index("--ledger") + 1] if "--ledger" in argv else None
    ende = time.monotonic() + frist
    while True:
        sperre = os_sperre.nehmen(pfad)
        if sperre is not None:
            break
        if time.monotonic() >= ende:
            print("BESETZT" + os_sperre.besitzer_text(pfad), flush=True)
            return 2
        time.sleep(0.05)
    try:
        print("GESPERRT", flush=True)
        if ledger is not None:
            basis, text, fehler = ledger_stand(ledger)
            print("LEDGER " + json.dumps({"basis": basis, "text": text, "fehler": fehler}),
                  flush=True)
            antwort = sys.stdin.buffer.readline().decode("utf-8", "replace")
            ergebnis = None if fehler else ledger_tauschen(ledger, antwort)
            if ergebnis:
                print(ergebnis, flush=True)
        # Halten, bis der Auftraggeber stdin schliesst (oder stirbt).
        while sys.stdin.buffer.read(65536):
            pass
    finally:
        os_sperre.freigeben(sperre)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
