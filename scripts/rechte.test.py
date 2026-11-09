#!/usr/bin/env python3
"""Tests fuer die Rechteerklaerung (plans/rechte-erklaerung-einmal-v1.md).

Jeder Test baut sich Wegwerf-Ordner: ein Projektordner mit
german-catalog-source.json und ein Datenordner fuer die Erklaerungsdatei.
Nichts hiervon fasst echte Projekte an.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rechte  # noqa: E402


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rechte-test-")
        self.data = os.path.join(self.tmp, "daten")
        self.projects = os.path.join(self.tmp, "projects")
        os.makedirs(self.data)
        os.makedirs(self.projects)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plan(self, name, datensatz="Team Massivhaus catalog", erlaubt=False):
        ordner = os.path.join(self.projects, name)
        os.makedirs(ordner, exist_ok=True)
        with open(os.path.join(ordner, "german-catalog-source.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"dataset": datensatz,
                       "source_file": "%s.pdf" % name,
                       "usage_rights": {"license": "rights-unconfirmed",
                                        "commercial_use_allowed": erlaubt,
                                        "generator_export_allowed": erlaubt}},
                      handle)
        return name


class OhneErklaerung(Basis):
    def test_kein_eintrag_heisst_nein(self):
        """Kriterium 1: ohne Erklaerung bleibt gesperrt, was gesperrt war."""
        p = self.plan("haus_a")
        self.assertIsNone(rechte.erklaerung_fuer(p, self.data, self.projects))
        self.assertFalse(rechte.erlaubt(p, self.data, self.projects))

    def test_gesperrt_liest_den_nachweis(self):
        self.assertTrue(rechte.gesperrt(self.plan("haus_a"), self.projects))
        self.assertFalse(rechte.gesperrt(
            self.plan("haus_frei", erlaubt=True), self.projects))

    def test_ohne_nachweis_keine_datensatz_erklaerung(self):
        """Ein Plan ohne german-catalog-source.json erbt nichts."""
        os.makedirs(os.path.join(self.projects, "eigenbau"))
        rechte.erklaeren("ja", "alles meins", "datensatz",
                         "Team Massivhaus catalog", "Rainer", self.data,
                         self.projects)
        self.assertFalse(rechte.erlaubt("eigenbau", self.data, self.projects))


class JaFuerEinenPlan(Basis):
    def test_ja_oeffnet_genau_diesen_plan(self):
        """Kriterium 2."""
        a, b = self.plan("haus_a"), self.plan("haus_b")
        rechte.erklaeren("ja", "selbst neu gezeichnet", "plan", a, "Rainer",
                         self.data, self.projects)
        self.assertTrue(rechte.erlaubt(a, self.data, self.projects))
        self.assertFalse(rechte.erlaubt(b, self.data, self.projects))

    def test_eintrag_haelt_fest_wer_wann_warum(self):
        p = self.plan("haus_a")
        eintrag = rechte.erklaeren("ja", "eigener Entwurf", "plan", p, "Rainer",
                                   self.data, self.projects)
        self.assertEqual(eintrag["antwort"], "ja")
        self.assertEqual(eintrag["wer"], "Rainer")
        self.assertEqual(eintrag["grund"], "eigener Entwurf")
        self.assertTrue(eintrag["wann"])

    def test_widersprechender_nachweis_wandert_mit(self):
        """Kriterium 6: der Widerspruch wird protokolliert, nicht getilgt."""
        p = self.plan("haus_a")
        eintrag = rechte.erklaeren("ja", "neu gezeichnet", "plan", p, "Rainer",
                                   self.data, self.projects)
        self.assertEqual(eintrag["herkunft_sagte"]["license"],
                         "rights-unconfirmed")
        self.assertIs(eintrag["herkunft_sagte"]["commercial_use_allowed"], False)

    def test_der_nachweis_bleibt_unveraendert(self):
        p = self.plan("haus_a")
        pfad = os.path.join(self.projects, p, "german-catalog-source.json")
        with open(pfad, encoding="utf-8") as handle:
            vorher = handle.read()
        rechte.erklaeren("ja", "neu gezeichnet", "plan", p, "Rainer",
                         self.data, self.projects)
        with open(pfad, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), vorher)


class JaFuerDenDatensatz(Basis):
    def test_ein_ja_gilt_fuer_alle_haeuser_des_datensatzes(self):
        """Kriterium 3: eine Erklaerung statt 55."""
        haeuser = [self.plan("haus_%d" % i) for i in range(5)]
        fremd = self.plan("fremd", datensatz="Anderer Katalog")
        rechte.erklaeren("ja", "alle selbst neu gezeichnet", "datensatz",
                         "Team Massivhaus catalog", "Rainer", self.data,
                         self.projects)
        for haus in haeuser:
            self.assertTrue(rechte.erlaubt(haus, self.data, self.projects), haus)
        self.assertFalse(rechte.erlaubt(fremd, self.data, self.projects))

    def test_ein_einziger_eintrag_in_der_datei(self):
        for i in range(5):
            self.plan("haus_%d" % i)
        rechte.erklaeren("ja", "alle meine", "datensatz",
                         "Team Massivhaus catalog", "Rainer", self.data,
                         self.projects)
        self.assertEqual(len(rechte.laden(self.data)["erklaerungen"]), 1)


class Nein(Basis):
    def test_nein_lehnt_ab_und_ist_beantwortet(self):
        """Kriterium 4: ein Nein ist eine Antwort, keine offene Frage."""
        p = self.plan("haus_a")
        rechte.erklaeren("nein", "doch ein Fremdplan", "plan", p, "Rainer",
                         self.data, self.projects)
        eintrag = rechte.erklaerung_fuer(p, self.data, self.projects)
        self.assertIsNotNone(eintrag)
        self.assertEqual(eintrag["antwort"], "nein")
        self.assertFalse(rechte.erlaubt(p, self.data, self.projects))

    def test_plan_nein_schlaegt_datensatz_ja(self):
        """Das einzelne Haus ist die genauere Aussage -- in beide Richtungen."""
        p = self.plan("haus_a")
        rechte.erklaeren("ja", "alle meine", "datensatz",
                         "Team Massivhaus catalog", "Rainer", self.data,
                         self.projects)
        rechte.erklaeren("nein", "dieses eine nicht", "plan", p, "Rainer",
                         self.data, self.projects)
        self.assertFalse(rechte.erlaubt(p, self.data, self.projects))

    def test_plan_ja_schlaegt_datensatz_nein(self):
        p = self.plan("haus_a")
        rechte.erklaeren("nein", "Katalog gehoert uns nicht", "datensatz",
                         "Team Massivhaus catalog", "Rainer", self.data,
                         self.projects)
        rechte.erklaeren("ja", "dieses eine habe ich neu gezeichnet", "plan", p,
                         "Rainer", self.data, self.projects)
        self.assertTrue(rechte.erlaubt(p, self.data, self.projects))

    def test_die_juengste_erklaerung_gilt(self):
        p = self.plan("haus_a")
        rechte.erklaeren("ja", "erst dachte ich ja", "plan", p, "Rainer",
                         self.data, self.projects)
        rechte.erklaeren("nein", "dann doch nicht", "plan", p, "Rainer",
                         self.data, self.projects)
        self.assertFalse(rechte.erlaubt(p, self.data, self.projects))


class Eingaben(Basis):
    def test_ohne_begruendung_keine_erklaerung(self):
        p = self.plan("haus_a")
        with self.assertRaises(ValueError):
            rechte.erklaeren("ja", "   ", "plan", p, "Rainer", self.data,
                             self.projects)
        self.assertFalse(rechte.erlaubt(p, self.data, self.projects))

    def test_unsinnige_antwort_wird_abgewiesen(self):
        p = self.plan("haus_a")
        with self.assertRaises(ValueError):
            rechte.erklaeren("vielleicht", "weiss nicht", "plan", p, "Rainer",
                             self.data, self.projects)

    def test_kaputte_ablage_wirft_nicht(self):
        with open(rechte.ablage(self.data), "w", encoding="utf-8") as handle:
            handle.write("{kaputt")
        p = self.plan("haus_a")
        self.assertFalse(rechte.erlaubt(p, self.data, self.projects))


if __name__ == "__main__":
    unittest.main(verbosity=1)
