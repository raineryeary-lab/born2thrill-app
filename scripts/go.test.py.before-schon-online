"""go.py's Bauen-gate must check whether the existing certificate is still
current, not just whether one exists.

Rainer, 2026-08-22: "i just saved it and codex says the last save is an
hour ago and you say the last save was 6 hours ago ... This is not working
we need a good and secure save and a new build when 'Bauen' is clicked."

go.py's zertifikat() only ever checked "does delivery-manifest.json exist"
-- once a house had any certificate, every later annotation edit was
invisible to it, and "Bauen" silently skipped rebuilding. ist_aktuell()
reuses batch-build.py's own annotation_state()/built_hash() (already
correct, already the batch tool's own gate) instead of writing a second,
divergent implementation.
"""

import os
import tempfile
import shutil
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent


def load_module():
    spec = importlib.util.spec_from_file_location("go", HERE / "go.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IstAktuellTests(unittest.TestCase):
    def setUp(self):
        self.go = load_module()
        self.batch_build = self.go._lade_batch_build()

    def test_skips_when_the_certificate_matches_the_current_annotation(self):
        with mock.patch.object(self.batch_build, "annotation_state", return_value=("hash-a", None)), \
             mock.patch.object(self.batch_build, "built_hash", return_value="hash-a"):
            self.assertTrue(self.go.ist_aktuell("irgendein_haus"))

    def test_rebuilds_when_the_certificate_does_not_match(self):
        # Exactly the reported bug: the annotation was saved again
        # (current hash changed) but a certificate from before that save
        # still sits on disk.
        with mock.patch.object(self.batch_build, "annotation_state", return_value=("hash-b", None)), \
             mock.patch.object(self.batch_build, "built_hash", return_value="hash-a-stale"):
            self.assertFalse(self.go.ist_aktuell("irgendein_haus"))

    def test_rebuilds_when_there_is_no_certificate_at_all(self):
        with mock.patch.object(self.batch_build, "annotation_state", return_value=("hash-a", None)), \
             mock.patch.object(self.batch_build, "built_hash", return_value=None):
            self.assertFalse(self.go.ist_aktuell("irgendein_haus"))

    def test_fails_safe_when_annotation_state_itself_is_blocked(self):
        # go.py's own earlier checks (hat_massstab etc.) normally catch a
        # missing-scale house before this point, but ist_aktuell() must
        # never report "current" (skip) in a state it cannot verify.
        with mock.patch.object(self.batch_build, "annotation_state", return_value=(None, "kein Massstab")):
            self.assertFalse(self.go.ist_aktuell("irgendein_haus"))




class BauLogTests(unittest.TestCase):
    """Wer auf ein Log verweist, schreibt es auch.

    Rainer, 2026-08-28: "Bau fehlgeschlagen -- Log in renders/go-baseline/",
    und in keinem dieser Logs stand der Grund. Er stand in der Ausgabe von
    run_project.py, die go.py verwarf; die zwei entscheidenden Zeilen mussten
    von Hand nachgestellt werden. Ausserdem las verifier_fails() bis dahin
    `batch-build.log` -- eine Datei, die go.py nie schreibt und die an jenem
    Tag sechs Tage alt war.
    """

    def setUp(self):
        self.go = load_module()

    def _schreibe(self, text):
        ordner = tempfile.mkdtemp()
        pfad = os.path.join(ordner, "bau.log")
        with open(pfad, "w", encoding="utf-8") as datei:
            datei.write(text)
        return pfad

    def test_a_failure_carries_its_reason_not_just_the_rule_name(self):
        """'R9_stair_access' allein sagt nicht, WAS im Weg stand."""
        pfad = self._schreibe(
            "PASS R2_gelaender\n"
            "FAIL R9_stair_access\n"
            "  - loch-rail-west blocks 97% of the arrival width of stair-step-15\n"
            "  - loch-rail-west-baluster-15 blocks 40%\n"
            "PASS R8_opening_heights\n")
        fails = self.go.fails_aus_log(pfad)
        self.assertEqual(len(fails), 1)
        regel, gruende = fails[0]
        self.assertEqual(regel, "R9_stair_access")
        self.assertEqual(len(gruende), 2)
        self.assertIn("loch-rail-west", gruende[0])

    def test_the_same_rule_failing_in_four_finishes_is_named_once(self):
        """Vier Ausfuehrungen je Stil melden dieselbe Regel viermal."""
        pfad = self._schreibe("FAIL R9_stair_access\n  - a\n" * 4)
        self.assertEqual(len(self.go.fails_aus_log(pfad)), 1)

    def test_a_clean_log_has_no_failures(self):
        pfad = self._schreibe("PASS R0_symbol_sizes\nPASS R9_stair_access\n")
        self.assertEqual(self.go.fails_aus_log(pfad), [])

    def test_a_missing_log_is_not_a_crash(self):
        """Vor dem ersten Bau gibt es keins."""
        self.assertEqual(self.go.fails_aus_log("gibt-es-nicht.log"), [])

class AbbruchgrundAusDemLog(unittest.TestCase):
    """Wenn der Grund im Log steht, gehoert er in die Hausliste.

    Rainer, 2026-08-29: `3_3_1_b_100_2` meldete nur "Bau fehlgeschlagen --
    Log in renders/go-baseline/bau.log". Der Grund stand vollstaendig im Log:

        furniture/floor-0.json: die RAEUME dieses Geschosses wurden
        umgezeichnet, seit diese Moebel gesetzt wurden (Stempel 592ffe7f4ffc,
        heute 264c9c9b6070). Im Moebel-Schritt pruefen ...

    `fails_aus_log()` findet ihn nicht: es sucht "FAIL "-Zeilen des
    Verifiers, und das hier ist ein Abbruch VOR dem Verifier -- der
    Plan-Builder verweigert. Dieselbe Lehre wie bei `run(log=...)`: wer auf
    ein Log verweist, schreibt es auch. Und wer den Grund hat, sagt ihn auch.
    """

    def schreibe(self, text):
        pfad = os.path.join(self.tmp, "bau.log")
        with open(pfad, "w", encoding="utf-8") as handle:
            handle.write(text)
        return pfad

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.go = load_module()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_der_moebel_stempel_wird_gefunden(self):
        pfad = self.schreibe(
            "[go] === modern ===\n"
            r"E:\...\furniture\floor-0.json" ": die RAEUME dieses Geschosses "
            "wurden umgezeichnet, seit diese Moebel gesetzt wurden "
            "(Stempel 592ffe7f4ffc, heute 264c9c9b6070). Im Moebel-Schritt "
            "pruefen, ob sie noch dort stehen.\n"
            "[go] FEHLGESCHLAGEN: keine zertifizierte Lieferung\n")
        grund = self.go.abbruchgrund(pfad)
        self.assertIn("umgezeichnet", grund)
        self.assertIn("Moebel-Schritt", grund)

    def test_go_zeilen_sind_kein_grund(self):
        """Die eigenen Fortschrittszeilen erklaeren nichts."""
        pfad = self.schreibe("[go] === modern ===\n[go] wrote handoff.json\n"
                             "[go] FEHLGESCHLAGEN: keine zertifizierte Lieferung\n")
        self.assertIsNone(self.go.abbruchgrund(pfad))

    def test_ein_leeres_log_gibt_nichts(self):
        self.assertIsNone(self.go.abbruchgrund(self.schreibe("")))

    def test_eine_fehlende_datei_gibt_nichts(self):
        self.assertIsNone(self.go.abbruchgrund(os.path.join(self.tmp, "gibtsnicht.log")))

    def test_der_grund_wird_gekuerzt(self):
        """Die Hausliste ist eine Zeile, kein Absatz."""
        lang = "X" * 400
        pfad = self.schreibe(f"floor-0.json: {lang}\n")
        grund = self.go.abbruchgrund(pfad)
        self.assertLessEqual(len(grund), 200)

    def test_nur_die_erste_meldung_zaehlt(self):
        """Modern und classic melden dasselbe zweimal."""
        pfad = self.schreibe(
            "floor-0.json: erster Grund hier\n"
            "[go] === classic ===\n"
            "floor-0.json: zweiter Grund hier\n")
        self.assertIn("erster Grund", self.go.abbruchgrund(pfad))
        self.assertNotIn("zweiter Grund", self.go.abbruchgrund(pfad))

    def test_der_datenordner_wird_abgeschnitten(self):
        """130 Zeichen Pfad, bevor die Meldung anfaengt -- dann faellt der
        Handgriff am Ende der Kuerzung zum Opfer."""
        pfad = self.schreibe(
            os.path.join("E:", "born2thrill-local-workbench-data", "corrections",
                         "german_catalog_review_bungalow_3_3_1_b_100_2",
                         "furniture", "floor-0.json")
            + ": die RAEUME wurden umgezeichnet. Im Moebel-Schritt "
              "pruefen und einmal speichern.\n")
        grund = self.go.abbruchgrund(pfad)
        self.assertTrue(grund.startswith("floor-0.json:"), grund)
        self.assertIn("einmal speichern", grund)

    def test_eine_meldung_ohne_pfad_bleibt_ganz(self):
        pfad = self.schreibe("Verifier R9_stair_access: kein Gelaender\n")
        self.assertEqual(self.go.abbruchgrund(pfad),
                         "Verifier R9_stair_access: kein Gelaender")


class HochladenOhneLieferungTest(unittest.TestCase):
    """Ohne Codex-Lieferung wird nicht hochgeladen -- auch nicht ersatzweise.

    `bilderordner()` gibt seit dem 2026-09-01 None zurueck, wenn nur
    `go-baseline` da ist. Der Aufrufer in `treibe()` machte den Rueckfall
    danach aber ein zweites Mal:

        ordner = bilderordner(name) or os.path.join(
            DATA, "corrections", name, "renders", "go-baseline")

    Damit waeren die drei grauen Rohbauten von
    german_catalog_review_bungalow_3_4_5_b_120 doch hochgeladen worden.
    """

    def test_ohne_lieferung_sagt_es_das_statt_hochzuladen(self):
        modul = load_module()
        aufrufe = []
        modul.bilderordner = lambda name: None
        modul.run = lambda *a, **k: aufrufe.append(a) or 0
        modul.hat_massstab = lambda name: True
        modul.hat_dach = lambda name: True
        modul.ist_aktuell = lambda name: True
        modul.read_json = lambda pfad: {"annotations": [{"floor_level": "groundfloor"}]}
        fertig, satz = modul.treibe("pruef_haus", hochladen=True)
        self.assertFalse(fertig)
        self.assertIn("Lieferung", satz)
        self.assertEqual(aufrufe, [], "es wurde trotzdem etwas hochgeladen")


class HochladenAusDemLieferordnerTest(unittest.TestCase):
    """Plan codex-ein-ordner-ein-knopf-v1: Hochladen nimmt GENAU den Ordner
    aus codex-job.json und laedt nur eine vollstaendige Lieferung hoch."""

    JOB = {"plan_id": "pruef_haus", "required_outputs": [
        {"filename_hint": "01-exterior-satteldach.png"},
        {"filename_hint": "02-floorplan-warm-modern-eg.png"},
        {"filename_hint": "03-floorplan-dark-modern-eg.png"}]}

    def _modul(self, job):
        modul = load_module()
        self.aufrufe = []
        modul.run = lambda *a, **k: self.aufrufe.append(a) or 0
        modul.hat_massstab = lambda name: True
        modul.hat_dach = lambda name: True
        modul.ist_aktuell = lambda name: True
        modul.bilderordner = lambda name: "FALSCHER-ORDNER"
        modul.read_json = lambda pfad: (job if pfad.endswith("codex-job.json")
                                        else {"annotations": [{"floor_level": "groundfloor"}]})
        return modul

    def test_fehlende_bilder_und_catalog_werden_genannt(self):
        modul = self._modul(None)
        modul._pruefer = lambda job, ordner: []
        with tempfile.TemporaryDirectory() as ordner:
            open(os.path.join(ordner, "01-exterior-satteldach.png"), "wb").close()
            fehlt = modul.lieferung_fehlt(self.JOB, ordner)
        text = " ".join(fehlt)
        self.assertIn("2 von 3", text)
        self.assertIn("02", text)
        self.assertIn("03", text)
        self.assertIn("catalog.json", text)

    def test_unvollstaendig_wird_nicht_hochgeladen(self):
        with tempfile.TemporaryDirectory() as ordner:
            job = dict(self.JOB, delivery_folder=ordner)
            modul = self._modul(job)
            modul._pruefer = lambda job, ordner: []
            fertig, satz = modul.treibe("pruef_haus", hochladen=True)
        self.assertFalse(fertig)
        self.assertIn("fehlen", satz)
        self.assertEqual(self.aufrufe, [], "unvollstaendige Lieferung hochgeladen")

    def test_pruefer_beanstandung_haelt_auf(self):
        with tempfile.TemporaryDirectory() as ordner:
            for r in self.JOB["required_outputs"]:
                open(os.path.join(ordner, r["filename_hint"]), "wb").close()
            open(os.path.join(ordner, "catalog.json"), "w").close()
            job = dict(self.JOB, delivery_folder=ordner)
            modul = self._modul(job)
            modul._pruefer = lambda job, ordner: ["03: 100 x 100 statt 2000 x 1500"]
            fertig, satz = modul.treibe("pruef_haus", hochladen=True)
        self.assertFalse(fertig)
        self.assertIn("2000 x 1500", satz)
        self.assertEqual(self.aufrufe, [])

    def test_vollstaendig_laedt_genau_diesen_ordner(self):
        with tempfile.TemporaryDirectory() as ordner:
            for r in self.JOB["required_outputs"]:
                open(os.path.join(ordner, r["filename_hint"]), "wb").close()
            open(os.path.join(ordner, "catalog.json"), "w").close()
            job = dict(self.JOB, delivery_folder=ordner)
            modul = self._modul(job)
            modul._pruefer = lambda job, ordner: []
            modul.treibe("pruef_haus", hochladen=True)
        self.assertEqual(len(self.aufrufe), 1)
        befehl = self.aufrufe[0][0]
        self.assertTrue(befehl[1].endswith("publish-renders.py"))
        self.assertEqual(befehl[befehl.index("--dir") + 1], ordner)
        self.assertNotIn("--send", befehl)

if __name__ == "__main__":
    unittest.main()

