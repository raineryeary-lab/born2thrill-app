"""Katalog-Listen nachziehen, wenn ein Haus fertig wird (katalog-anstoss-v1).

Rainer, 2026-11-09: "you need to refresh your list in the front when
something gets finished". Bisher lief katalog-aktualisieren.py nur nach einem
Speichern im Annotator (app.py, katalog-automatisch-v1). Fertig wird ein Haus
aber beim Bauen, Hochladen und Freigeben -- dann blieben Countdown, Luecken-
liste und Filter auf dem alten Stand.

Aufruf (losgeloest, kehrt sofort zurueck):  anstossen()  bzw.
    python katalog-anstossen.py            -> startet sich selbst im Hintergrund
    python katalog-anstossen.py --jetzt    -> wartet RUHE_S, dann ein Lauf

Nie zwei Laeufe zugleich: eine Sperrdatei im Datenordner. Kommt waehrenddessen
ein weiterer Anstoss, laeuft danach genau noch einer. Aus: KATALOG_AUTO=0.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RUHE_S = 45
SPERRE_ALT_S = 30 * 60


def datenordner():
    return os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"


def anstossen():
    """Startet einen losgeloesten Lauf; Fehler werden nur gemeldet, nie geworfen."""
    if os.environ.get("KATALOG_AUTO", "1") == "0":
        return False
    try:
        flags = 0
        if os.name == "nt":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([sys.executable, os.path.join(HERE, "katalog-anstossen.py"), "--jetzt"],
                         cwd=HERE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=flags, close_fds=True,
                         env={**os.environ, "FLOORPLAN_WORKBENCH_DATA_DIR": datenordner()})
        print("Katalog-Listen werden in ~{} s aktualisiert.".format(RUHE_S))
        return True
    except OSError as fehler:
        print("Katalog-Listen nicht angestossen: {}".format(fehler))
        return False


def _lauf():
    ordner = datenordner()
    sperre = os.path.join(ordner, "katalog-aktualisieren.sperre")
    nachlauf = os.path.join(ordner, "katalog-aktualisieren.nachlauf")
    time.sleep(RUHE_S)
    try:
        if os.path.exists(sperre) and time.time() - os.path.getmtime(sperre) > SPERRE_ALT_S:
            os.remove(sperre)
        fd = os.open(sperre, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        open(nachlauf, "w").close()      # laeuft schon: danach noch einmal
        return 0
    os.close(fd)
    try:
        while True:
            if os.path.exists(nachlauf):
                os.remove(nachlauf)
            with open(os.path.join(ordner, "katalog-aktualisieren.log"), "a", encoding="utf-8") as log:
                log.write("\n--- {} (anstoss)\n".format(time.strftime("%Y-%m-%dT%H:%M:%S")))
                log.flush()
                subprocess.run([sys.executable, os.path.join(HERE, "katalog-aktualisieren.py")],
                               cwd=HERE, stdout=log, stderr=subprocess.STDOUT,
                               env={**os.environ, "FLOORPLAN_WORKBENCH_DATA_DIR": ordner})
            if not os.path.exists(nachlauf):
                break
    finally:
        os.remove(sperre)
    return 0


if __name__ == "__main__":
    if "--jetzt" in sys.argv:
        sys.exit(_lauf())
    anstossen()
