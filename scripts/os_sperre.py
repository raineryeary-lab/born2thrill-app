"""Betriebssystem-Sperren auf einer Datei (ZUVERLAESSIGKEIT-001).

Das Betriebssystem haelt die Sperre (msvcrt.locking / fcntl.flock), solange
der Prozess lebt, der sie genommen hat; stirbt er, ist sie von selbst frei.
Eine lebende Sperre wird nie uebernommen, und es gibt keine Zeitablauf-
oder Umbenenn-Uebernahme, die sich ein zweiter Lauf erschleichen koennte
(Codex, Runde 2 und 4).

Die Datei bleibt liegen. Ihre erste Zeile nennt den Besitzer (pid, seit),
gesperrt wird ein Byte DAHINTER: Windows sperrt Bereiche hart, auch gegen
Lesen, so bleibt die Besitzerzeile fuer die Meldung lesbar.

Benutzt von publish-renders.py (upload.lock) und go.py (pipeline.lock).
os.open liefert seit Python 3.4 nicht vererbbare Handles: Kindprozesse
(run_project, Blender, publish-renders) erben die Sperre nicht und koennen
sie weder halten noch blockieren.
"""
import json
import os
import time

SPERR_BYTE = 1 << 20


class Sperre:
    """Eine gehaltene Sperre: offene Datei mit Betriebssystem-Sperre."""

    def __init__(self, pfad, fd):
        self.pfad = pfad
        self.fd = fd


def _os_sperre(fd):
    """True, wenn die Sperre jetzt uns gehoert; False, wenn ein anderer sie haelt."""
    if os.name == "nt":
        import msvcrt
        os.lseek(fd, SPERR_BYTE, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def nehmen(pfad):
    """Die Sperre nehmen, ohne zu warten. Sperre oder None (besetzt)."""
    fd = os.open(pfad, os.O_RDWR | os.O_CREAT, 0o644)
    if not _os_sperre(fd):
        os.close(fd)
        return None
    zeile = (json.dumps({"pid": os.getpid(), "seit": time.time()}) + "\n").encode("utf-8")
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, zeile)
    os.fsync(fd)
    return Sperre(pfad, fd)


def besitzer_text(pfad):
    """' (Prozess N, seit S s)' aus der Besitzerzeile, oder ''."""
    try:
        with open(pfad, encoding="utf-8") as handle:
            info = json.loads(handle.readline() or "{}")
        return " (Prozess {}, seit {:.0f} s)".format(
            info.get("pid"), time.time() - float(info.get("seit", time.time())))
    except Exception:
        return ""


def freigeben(sperre):
    """Nur die eigene, gehaltene Sperre loesen; die Datei bleibt liegen."""
    if sperre is None or sperre.fd is None:
        return
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(sperre.fd, SPERR_BYTE, os.SEEK_SET)
            try:
                msvcrt.locking(sperre.fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl
            fcntl.flock(sperre.fd, fcntl.LOCK_UN)
    finally:
        os.close(sperre.fd)
        sperre.fd = None
