"""ZUVERLAESSIGKEIT-001, Teil 3 (Rainer, 2026-10-25: "the upload and the
Freigaben are all totally clicking constantly and after 4 tries maybe they
work or not").

  B1  Das alte Plugin (1.1.1) lehnt den Haustyp in b2t/v1/katalog mit
      HTTP 400 ab. Das brach das ganze Hochladen ab, obwohl die Bilder mit
      dem Haustyp nichts zu tun haben.
  B5  urlopen ohne Zeitlimit: ein haengender Server liess "laedt ..." ewig
      stehen.
  B7  Zwei Hochladen-Laeufe fuer dasselbe Haus sahen beide denselben
      fehlenden Slug und luden doppelt hoch.

Kein Test spricht mit born2thrill.de: urlopen ist ueberall ersetzt.
"""

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def lade():
    spec = importlib.util.spec_from_file_location("publish_renders_z", HERE / "publish-renders.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class Antwort:
    def __init__(self, daten):
        self.daten = json.dumps(daten).encode("utf-8")

    def read(self):
        return self.daten

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class HaustypIstNichtTodlichTest(unittest.TestCase):

    def test_http_400_beim_haustyp_bricht_nicht_ab(self):
        modul = lade()

        def urlopen(req, timeout=None):
            if req.get_method() == "POST":
                raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
                                             io.BytesIO(b'{"message":"Weder bilder noch approved"}'))
            return Antwort([{"id": "pruef_haus", "t": "bungalow"}])

        katalogzeile = mock.Mock()
        katalogzeile.zeile_aus_projekt.return_value = {"haustyp": "Bungalow"}
        with tempfile.TemporaryDirectory() as suite:
            ordner = os.path.join(suite, "floorplan-simplifier", "projects", "pruef_haus")
            os.makedirs(ordner)
            open(os.path.join(ordner, "annotations.json"), "w").close()
            modul.SUITE = suite
            with mock.patch.object(modul.urllib.request, "urlopen", urlopen), \
                 mock.patch.dict("sys.modules", {"katalogzeile": katalogzeile}), \
                 mock.patch.object(modul, "auth_header", lambda: "Basic x"), \
                 mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                modul.haustyp_nachziehen("https://example.invalid", "pruef_haus")
        self.assertIn("WARNUNG", out.getvalue())
        self.assertIn("400", out.getvalue())


class ZeitlimitTest(unittest.TestCase):

    def test_request_setzt_ein_zeitlimit(self):
        modul = lade()
        gesehen = {}

        def urlopen(req, timeout=None):
            gesehen["timeout"] = timeout
            return Antwort([])
        with mock.patch.object(modul.urllib.request, "urlopen", urlopen):
            modul.request("https://example.invalid/x")
        self.assertTrue(gesehen["timeout"])

    def test_netzfehler_wird_eine_klare_meldung(self):
        modul = lade()

        def urlopen(req, timeout=None):
            raise urllib.error.URLError("timed out")
        with mock.patch.object(modul.urllib.request, "urlopen", urlopen):
            with self.assertRaises(SystemExit) as fehler:
                modul.request("https://example.invalid/x")
        self.assertIn("timed out", str(fehler.exception))


class HochladenSperreTest(unittest.TestCase):
    """Runde 2: das Betriebssystem haelt die Sperre. Eine lebende Sperre wird
    nie uebernommen, eine tote ist von selbst frei."""

    def setUp(self):
        self.modul = lade()
        self.tmp = tempfile.TemporaryDirectory()
        self.modul._daten_ordner = lambda: self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_zweiter_lauf_wird_abgelehnt(self):
        sperre = self.modul.sperre_nehmen("pruef_haus")
        try:
            with self.assertRaises(SystemExit) as fehler:
                self.modul.sperre_nehmen("pruef_haus")
            self.assertIn("laeuft schon", str(fehler.exception))
            self.assertIn(str(os.getpid()), str(fehler.exception))   # Besitzer genannt
        finally:
            self.modul.sperre_freigeben(sperre)

    def test_nach_freigeben_wieder_frei(self):
        sperre = self.modul.sperre_nehmen("pruef_haus")
        self.modul.sperre_freigeben(sperre)
        self.modul.sperre_freigeben(sperre)          # doppelt freigeben schadet nicht
        self.modul.sperre_freigeben(self.modul.sperre_nehmen("pruef_haus"))

    def test_lebende_sperre_wird_auch_nach_30_min_nicht_gestohlen(self):
        sperre = self.modul.sperre_nehmen("pruef_haus")
        try:
            # alte Zeitangabe in der Besitzerzeile aendert nichts
            os.lseek(sperre.fd, 0, os.SEEK_SET)
            os.write(sperre.fd, json.dumps({"pid": os.getpid(),
                                            "seit": time.time() - 3 * 3600}).encode())
            with self.assertRaises(SystemExit):
                self.modul.sperre_nehmen("pruef_haus")
        finally:
            self.modul.sperre_freigeben(sperre)

    def test_sperre_eines_beendeten_prozesses_ist_frei(self):
        skript = "\n".join([
            "import importlib.util, os, sys",
            "spec = importlib.util.spec_from_file_location('p', sys.argv[1])",
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)",
            "m._daten_ordner = lambda: sys.argv[2]",
            "m.sperre_nehmen('pruef_haus')",
            "print('gesperrt', flush=True)",
            "sys.stdin.read()",
        ])
        kind = subprocess.Popen([sys.executable, "-c", skript, str(HERE / "publish-renders.py"),
                                 self.tmp.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                text=True)
        try:
            self.assertEqual(kind.stdout.readline().strip(), "gesperrt")
            with self.assertRaises(SystemExit):
                self.modul.sperre_nehmen("pruef_haus")
        finally:
            kind.kill()
            kind.wait()
            kind.stdin.close()
            kind.stdout.close()
        self.modul.sperre_freigeben(self.modul.sperre_nehmen("pruef_haus"))

    def test_kaputte_sperrdatei_blockiert_nicht(self):
        ordner = os.path.join(self.tmp.name, "corrections", "pruef_haus")
        os.makedirs(ordner)
        with open(os.path.join(ordner, "upload.lock"), "w", encoding="utf-8") as h:
            h.write("kaputt")
        self.modul.sperre_freigeben(self.modul.sperre_nehmen("pruef_haus"))

    def test_andere_haeuser_sind_unabhaengig(self):
        a = self.modul.sperre_nehmen("haus_a")
        b = self.modul.sperre_nehmen("haus_b")
        self.modul.sperre_freigeben(a)
        self.modul.sperre_freigeben(b)


if __name__ == "__main__":
    unittest.main()
