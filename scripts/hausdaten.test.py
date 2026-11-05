"""Eine Wahrheit fuer Dachform und Massstab -- die vier Faelle aus dem Plan.

plans/hausdaten-eine-wahrheit-v1.md: Dachform und Massstab liegen in zwei
Dateien (annotations.json und gebaeudemass.json). Vorher fuehrten fuenf Stellen
sie selbst zusammen, mit drei verschiedenen Vorrangregeln -- dasselbe Haus galt
an einer Stelle als "Dachform gesetzt" und an einer anderen als "fehlt".

Vorrangregel, ueberall gleich und pro Feld: annotations.json gewinnt; ist das
Feld dort leer, zaehlt gebaeudemass.json. Das ist das Verhalten des Bauens
(build-simplifier-render-plan.load_annotations) und damit die Wahrheit -- die
Anzeigen richten sich danach, nicht umgekehrt.

Geprueft wird nicht nur der Helfer, sondern jede der Python-Aufrufstellen an
Wegwerf-Projektordnern.
"""

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Die Skripte verweigern ohne gesetzten Datenordner den Start (sie raten nicht).
# Fuer diese Tests reicht ein Wegwerf-Ordner: gelesen werden nur die
# Projektordner, und die zeigen wir per PROJECTS auf das Testverzeichnis.
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR",
                      os.path.join(tempfile.gettempdir(), "hausdaten-test-data"))

import hausdaten  # noqa: E402


def lade(dateiname, modulname):
    spec = importlib.util.spec_from_file_location(
        modulname, os.path.join(HERE, dateiname))
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


ANNOTATION = {
    "schema_version": "simplifier-annotations-v1",
    "annotations": [{"id": "r1", "floor_level": "groundfloor", "label": "Wohnen",
                     "points": [{"x": 0.1, "y": 0.1}, {"x": 0.4, "y": 0.1},
                                {"x": 0.4, "y": 0.4}, {"x": 0.1, "y": 0.4}]}],
    "elements": [],
    "roof_type_modern": None,
    "roof_type_classic": None,
    "floor_scale": {},
    "annotation_space": {"aspect": 0.75},
}


class HausdatenFall(unittest.TestCase):
    """Basis: ein Wegwerf-Projektordner, auf den alle Aufrufstellen zeigen."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hausdaten-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.plan = "testhaus"
        self.folder = os.path.join(self.tmp, self.plan)
        os.makedirs(self.folder)

    def schreibe(self, name, inhalt):
        with open(os.path.join(self.folder, name), "w", encoding="utf-8") as handle:
            json.dump(inhalt, handle, ensure_ascii=False)

    def projekt(self, annotation=None, sidecar=None):
        eintrag = json.loads(json.dumps(ANNOTATION))
        eintrag.update(annotation or {})
        self.schreibe("annotations.json", eintrag)
        pfad = os.path.join(self.folder, "gebaeudemass.json")
        if sidecar is None:
            if os.path.exists(pfad):
                os.remove(pfad)
        else:
            self.schreibe("gebaeudemass.json",
                          dict({"schema": "zf-gebaeudemass-v1", "plan_id": self.plan},
                               **sidecar))
        return self.folder

    # -- die vier Python-Aufrufstellen, auf den Wegwerf-Ordner gebogen --------

    def go(self):
        modul = lade("go.py", "go_test_modul")
        modul.PROJECTS = self.tmp
        return modul

    def werkbank(self):
        modul = lade("werkbank.py", "werkbank_test_modul")
        modul.PROJECTS = self.tmp
        return modul

    def dachform(self):
        modul = lade("dachform.py", "dachform_test_modul")
        modul.PROJECTS = self.tmp
        return modul

    def bauplan(self):
        return lade("build-simplifier-render-plan.py", "bauplan_test_modul")

    def werkbank_stufe(self, titel):
        for zeile in self.werkbank().stufen(self.plan):
            if zeile["titel"] == titel:
                return zeile
        self.fail("Stufe %s fehlt" % titel)


class NurImSidecar(HausdatenFall):
    """Kriterium 1: Dachform nur in gebaeudemass.json -> ueberall gesetzt."""

    def setUp(self):
        super().setUp()
        self.projekt(sidecar={"roof_type_modern": "flachdach",
                              "roof_type_classic": "walmdach"})

    def test_helfer(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["dachform_modern"], "flachdach")
        self.assertEqual(daten["dachform_classic"], "walmdach")
        self.assertEqual(daten["herkunft"]["dachform_modern"], "gebaeudemass")
        self.assertEqual(daten["herkunft"]["dachform_classic"], "gebaeudemass")

    def test_bauplan(self):
        annotations = self.bauplan().load_annotations(self.folder)
        self.assertEqual(annotations["roof_type_modern"], "flachdach")
        self.assertEqual(annotations["roof_type_classic"], "walmdach")

    def test_go(self):
        self.assertTrue(self.go().hat_dach(self.plan))

    def test_werkbank(self):
        zeile = self.werkbank_stufe("Dachform")
        self.assertTrue(zeile["gut"])
        self.assertIn("walmdach", zeile["wert"])
        self.assertIn("flachdach", zeile["wert"])

    def test_dachform(self):
        # Nicht in der Annotation -> das Sidecar darf weiter gesetzt werden.
        self.assertFalse(self.dachform().already_annotated(self.plan))


class BeideVerschieden(HausdatenFall):
    """Kriterium 2: in beiden Dateien -> annotations.json gewinnt."""

    def setUp(self):
        super().setUp()
        self.projekt(annotation={"roof_type_modern": "satteldach",
                                 "roof_type_classic": "satteldach"},
                     sidecar={"roof_type_modern": "flachdach",
                              "roof_type_classic": "walmdach"})

    def test_helfer(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["dachform_modern"], "satteldach")
        self.assertEqual(daten["dachform_classic"], "satteldach")
        self.assertEqual(daten["herkunft"]["dachform_classic"], "annotations")

    def test_bauplan(self):
        annotations = self.bauplan().load_annotations(self.folder)
        self.assertEqual(annotations["roof_type_modern"], "satteldach")
        self.assertEqual(annotations["roof_type_classic"], "satteldach")

    def test_werkbank(self):
        zeile = self.werkbank_stufe("Dachform")
        self.assertIn("satteldach", zeile["wert"])
        self.assertNotIn("walmdach", zeile["wert"])

    def test_dachform(self):
        self.assertTrue(self.dachform().already_annotated(self.plan))


class NurModernImSidecar(HausdatenFall):
    """Kriterium 3: nur roof_type_modern im Sidecar -> hat_dach ist wahr.

    go.py sah frueher im Sidecar NUR roof_type_classic nach; ein Haus mit
    ausschliesslich moderner Dachform galt als dachlos.
    """

    def setUp(self):
        super().setUp()
        self.projekt(sidecar={"roof_type_modern": "flachdach"})

    def test_helfer(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["dachform_modern"], "flachdach")
        self.assertIsNone(daten["dachform_classic"])

    def test_go(self):
        self.assertTrue(self.go().hat_dach(self.plan))

    def test_dachform_zaehlt_es_als_gesetzt(self):
        modul = self.dachform()
        self.assertFalse(modul.already_annotated(self.plan))
        daten = hausdaten.hausdaten(self.folder)
        self.assertTrue(daten["dachform_modern"] or daten["dachform_classic"])


class MassstabNurImSidecar(HausdatenFall):
    """Kriterium 4: Massstab nur in gebaeudemass.json -> keine Vermessung noetig."""

    def setUp(self):
        super().setUp()
        self.projekt(sidecar={"floor_scale": {"groundfloor": 16.56},
                              "rahmen_m": {"groundfloor": [16.56, 11.85]}})

    def test_helfer(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["floor_scale"], {"groundfloor": 16.56})
        self.assertEqual(daten["herkunft"]["floor_scale"], "gebaeudemass")
        self.assertTrue(daten["hat_gebaeudemass"])

    def test_go(self):
        self.assertTrue(self.go().hat_massstab(self.plan))

    def test_bauplan(self):
        annotations = self.bauplan().load_annotations(self.folder)
        self.assertEqual(annotations["floor_scale"]["groundfloor"], 16.56)

    def test_werkbank(self):
        zeile = self.werkbank_stufe("Massstab")
        self.assertTrue(zeile["gut"])
        self.assertIn("groundfloor", zeile["wert"])

    def test_gemessener_massstab_gewinnt_pro_geschoss(self):
        # Der Bau mischt pro Geschoss: gemessen schlaegt eingetragen, und ein
        # Geschoss, das nur im Sidecar steht, geht trotzdem nicht verloren.
        self.projekt(annotation={"floor_scale": {"groundfloor": 12.0}},
                     sidecar={"floor_scale": {"groundfloor": 16.56,
                                              "upperfloor": 16.56}})
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["floor_scale"],
                         {"groundfloor": 12.0, "upperfloor": 16.56})
        self.assertEqual(daten["herkunft"]["floor_scale"], "annotations")


class LeereWerteZaehlenNicht(HausdatenFall):
    """Leere Zeichenketten und leere Objekte sind "nicht gesetzt"."""

    def setUp(self):
        super().setUp()
        self.projekt(annotation={"roof_type_modern": "", "roof_type_classic": "",
                                 "floor_scale": {}},
                     sidecar={"roof_type_modern": "flachdach",
                              "roof_type_classic": "walmdach",
                              "floor_scale": {"groundfloor": 16.56}})

    def test_helfer(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["dachform_modern"], "flachdach")
        self.assertEqual(daten["dachform_classic"], "walmdach")
        self.assertEqual(daten["floor_scale"], {"groundfloor": 16.56})

    def test_ohne_sidecar(self):
        self.projekt()
        daten = hausdaten.hausdaten(self.folder)
        self.assertIsNone(daten["dachform_modern"])
        self.assertEqual(daten["floor_scale"], {})
        self.assertFalse(daten["hat_gebaeudemass"])
        self.assertIsNone(daten["herkunft"]["floor_scale"])


# ---------------------------------------------------------------------------
# plans/hausdaten-restleser-v1.md -- die vier Leser, die den Massstab bis
# 2026-08-25 noch selbst zusammenfuehrten, und zwar ALLES-ODER-NICHTS statt pro
# Geschoss: stand in annotations.json auch nur ein einziger Geschoss-Eintrag,
# wurde gebaeudemass.json gar nicht erst aufgeschlagen. Ein Haus mit einem
# gezeichneten, aber nie gemessenen Geschoss (floor_scale: {"groundfloor": null}
# -- der Annotator legt den Schluessel an, sobald das Geschoss existiert) galt
# diesen Lesern deshalb als vermessen, obwohl der Bau es ablehnt.


class Restleser(HausdatenFall):
    """Basis fuer batch-build.py, workflow.py, masse-server.py und den
    Eingangshash des Dollhouse-Renderers."""

    def batch_build(self):
        modul = lade("batch-build.py", "batch_build_test_modul")
        modul.PROJECTS = self.tmp
        return modul

    def workflow(self):
        modul = lade("workflow.py", "workflow_test_modul")
        modul.PROJECTS = self.tmp
        modul.DATA = self.tmp
        return modul

    def workflow_stufe(self):
        return self.workflow().stufe_von(self.plan, {}, {})

    def masse_server(self):
        modul = lade("masse-server.py", "masse_server_test_modul")
        modul.PROJECTS = self.tmp
        return modul

    def masse_zeile(self):
        for haus in self.masse_server().haeuser():
            if haus["name"] == self.plan:
                return haus
        self.fail("masse-server.py kennt %s nicht" % self.plan)

    def dollhouse_pruefer(self):
        """_refuse_stale_plan aus dem echten Renderer, ohne Blender.

        render-furnished-dollhouse.py importiert bpy und laeuft nur in Blender.
        Dieselbe Technik wie render-furnished-dollhouse.test.py: die Funktion
        wird per ast aus der ECHTEN Datei geholt, nie von Hand kopiert -- eine
        Kopie koennte driften, und genau das ist der Defekt, den dieser Plan
        schliesst.
        """
        quelle = os.path.join(HERE, "render-furnished-dollhouse.py")
        with open(quelle, encoding="utf-8") as handle:
            baum = ast.parse(handle.read())
        knoten = next(n for n in baum.body
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "_refuse_stale_plan")
        namensraum = {"os": os, "json": json, "hashlib": hashlib,
                      "hausdaten": hausdaten}
        exec(compile(ast.Module(body=[knoten], type_ignores=[]), quelle, "exec"),
             namensraum)
        return namensraum["_refuse_stale_plan"]

    def dollhouse_urteil(self, plan_doc):
        """None wenn der Renderer den Plan annimmt, sonst der Refusal-Text."""
        # Der Renderer leitet die Projekt-Id aus dem PFAD des Plans ab:
        # .../corrections/<id>/renders/go-baseline/plan-*.json
        plan_datei = os.path.join(self.tmp, "corrections", self.plan,
                                  "renders", "go-baseline", "plan-modern.json")
        os.makedirs(os.path.dirname(plan_datei), exist_ok=True)
        with open(plan_datei, "w", encoding="utf-8") as handle:
            json.dump(plan_doc, handle)
        pruefer = self.dollhouse_pruefer()
        # FLOORPLAN_SIMPLIFIER_PROJECTS biegt den Renderer auf den
        # Wegwerf-Ordner -- so liest er dieselbe annotations.json und
        # dieselbe gebaeudemass.json wie der Helfer.
        alt = os.environ.get("FLOORPLAN_SIMPLIFIER_PROJECTS")
        os.environ["FLOORPLAN_SIMPLIFIER_PROJECTS"] = self.tmp
        try:
            pruefer(plan_doc, plan_datei)
            return None
        except SystemExit as abbruch:
            return str(abbruch)
        finally:
            if alt is None:
                os.environ.pop("FLOORPLAN_SIMPLIFIER_PROJECTS", None)
            else:
                os.environ["FLOORPLAN_SIMPLIFIER_PROJECTS"] = alt

    def annotationshash(self):
        with open(os.path.join(self.folder, "annotations.json"),
                  encoding="utf-8-sig") as handle:
            annotationen = json.load(handle)
        return hashlib.sha256(json.dumps(
            annotationen, sort_keys=True, ensure_ascii=False,
            separators=(",", ":")).encode("utf-8")).hexdigest()


class RestleserMassstabNurImSidecar(Restleser):
    """Kriterium 1: Massstab nur in gebaeudemass.json -> alle vier sehen ihn."""

    def setUp(self):
        super().setUp()
        self.projekt(sidecar={"floor_scale": {"groundfloor": 16.56},
                              "rahmen_m": {"groundfloor": [16.56, 11.85]},
                              "gebaeude_breite_m": 16.56,
                              "gebaeude_tiefe_m": 11.85})

    def test_batch_build_baut(self):
        hashwert, grund = self.batch_build().annotation_state(self.plan)
        self.assertIsNone(grund)
        self.assertTrue(hashwert)

    def test_workflow_ist_vermessen(self):
        stufe, grund = self.workflow_stufe()
        self.assertGreaterEqual(stufe, 2, grund)

    def test_masse_server_meldet_fertig(self):
        self.assertTrue(self.masse_zeile()["fertig"])


class RestleserMassstabProGeschoss(Restleser):
    """Kriterium 2: je Geschoss aus verschiedenen Quellen -> zusammengefuehrt.

    Erdgeschoss in der Zeichnung, Obergeschoss nur im Sidecar. Die Zeichnung
    gewinnt pro GESCHOSS; das Obergeschoss darf nicht verloren gehen, nur weil
    die Zeichnung ueberhaupt einen Massstab mitbringt.
    """

    def setUp(self):
        super().setUp()
        eintrag = json.loads(json.dumps(ANNOTATION))
        eintrag["annotations"] = [
            dict(ANNOTATION["annotations"][0], id="r1", floor_level="groundfloor"),
            dict(ANNOTATION["annotations"][0], id="r2", floor_level="upperfloor"),
        ]
        eintrag["floor_scale"] = {"groundfloor": 12.0}
        self.projekt(annotation=eintrag,
                     sidecar={"floor_scale": {"groundfloor": 16.56,
                                              "upperfloor": 9.0}})

    def test_helfer_fuehrt_pro_geschoss_zusammen(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["floor_scale"],
                         {"groundfloor": 12.0, "upperfloor": 9.0})

    def test_batch_build_kennt_beide_geschosse(self):
        hashwert, grund = self.batch_build().annotation_state(self.plan)
        self.assertIsNone(grund)
        self.assertTrue(hashwert)

    def test_workflow_ist_vermessen(self):
        stufe, grund = self.workflow_stufe()
        self.assertGreaterEqual(stufe, 2, grund)


class RestleserLeererMassstabInDerZeichnung(Restleser):
    """Der Kern des Defekts: ein Geschoss-Schluessel OHNE Wert.

    Der Annotator legt floor_scale[<geschoss>] an, sobald das Geschoss
    existiert -- gemessen ist es damit nicht. Die alten Leser sahen nur
    `annotations["floor_scale"]` als Ganzes: nicht leer, also "vermessen".
    """

    def setUp(self):
        super().setUp()
        self.projekt(annotation={"floor_scale": {"groundfloor": None}},
                     sidecar={"floor_scale": {"groundfloor": 16.56},
                              "gebaeude_breite_m": 16.56,
                              "gebaeude_tiefe_m": 11.85})

    def test_helfer_nimmt_den_gemessenen_wert(self):
        daten = hausdaten.hausdaten(self.folder)
        self.assertEqual(daten["floor_scale"], {"groundfloor": 16.56})

    def test_batch_build_blockiert_nicht_mehr(self):
        # Alt: "kein Massstab fuer groundfloor" -- das Haus war nie baubar,
        # obwohl der Bau selbst den Sidecar-Wert genommen haette.
        hashwert, grund = self.batch_build().annotation_state(self.plan)
        self.assertIsNone(grund)
        self.assertTrue(hashwert)


class RestleserLeererMassstabOhneSidecar(Restleser):
    """Und die Gegenrichtung: leerer Schluessel, kein Sidecar -> NICHT vermessen.

    Alt meldeten workflow.py und masse-server.py dieses Haus als vermessen,
    obwohl der Bau es ablehnt ("no calibrated scale"). Ein Leser, der ein
    unbaubares Haus als fertig ausweist, schickt niemanden mehr zum Messen.
    """

    def setUp(self):
        super().setUp()
        self.projekt(annotation={"floor_scale": {"groundfloor": None}})

    def test_helfer_zaehlt_es_als_nicht_gesetzt(self):
        self.assertEqual(hausdaten.hausdaten(self.folder)["floor_scale"], {})

    def test_workflow_haengt_bei_massstab(self):
        stufe, grund = self.workflow_stufe()
        self.assertEqual(stufe, 1)
        self.assertIn("Massstab", grund)

    def test_masse_server_meldet_offen(self):
        self.assertFalse(self.masse_zeile()["fertig"])

    def test_batch_build_blockiert(self):
        hashwert, grund = self.batch_build().annotation_state(self.plan)
        self.assertIsNone(hashwert)
        self.assertIn("Massstab", grund)


class EingangshashIstEinerFuerAlle(Restleser):
    """Kriterium 1/4, Hash-Seite: Zeichnung UND Sidecar, ueberall dieselbe Formel.

    Die Formel stand dreimal von Hand da (build-simplifier-render-plan.py,
    batch-build.py, render-furnished-dollhouse.py). Wer sie an einer Stelle
    aendert, baut, was die andere fuer alt haelt.
    """

    def setUp(self):
        super().setUp()
        self.projekt(sidecar={"floor_scale": {"groundfloor": 16.56}})

    def test_helfer_und_bauplan_rechnen_gleich(self):
        bauplan = self.bauplan()
        self.assertEqual(hausdaten.sidecar_hash(self.folder),
                         bauplan.sidecar_hash(self.folder))
        annotation = self.annotationshash()
        self.assertEqual(
            hausdaten.eingangshash(self.folder, annotation),
            bauplan.input_hash(annotation, bauplan.sidecar_hash(self.folder)))

    def test_ohne_sidecar_kein_hash_aber_ein_eingangshash(self):
        self.projekt()
        self.assertIsNone(hausdaten.sidecar_hash(self.folder))
        self.assertTrue(hausdaten.eingangshash(self.folder, "abc"))

    def test_ohne_annotationshash_kein_eingangshash(self):
        self.assertIsNone(hausdaten.eingangshash(self.folder, None))

    def test_batch_build_stempelt_denselben_eingangshash(self):
        hashwert, grund = self.batch_build().annotation_state(self.plan)
        self.assertIsNone(grund)
        self.assertEqual(hashwert,
                         hausdaten.eingangshash(self.folder, self.annotationshash()))

    def test_dollhouse_nimmt_den_plan_mit_diesem_eingangshash_an(self):
        annotation = self.annotationshash()
        plan_doc = {"source_provenance": {
            "annotation_hash": annotation,
            "sidecar_hash": hausdaten.sidecar_hash(self.folder),
            "input_hash": hausdaten.eingangshash(self.folder, annotation)}}
        self.assertIsNone(self.dollhouse_urteil(plan_doc))

    def test_dollhouse_verweigert_nach_einer_massaenderung(self):
        annotation = self.annotationshash()
        plan_doc = {"source_provenance": {
            "annotation_hash": annotation,
            "sidecar_hash": hausdaten.sidecar_hash(self.folder),
            "input_hash": hausdaten.eingangshash(self.folder, annotation)}}
        # Nur das Gebaeudemass aendert sich -- die Zeichnung bleibt gleich.
        self.schreibe("gebaeudemass.json",
                      {"schema": "zf-gebaeudemass-v1", "plan_id": self.plan,
                       "floor_scale": {"groundfloor": 18.0}})
        urteil = self.dollhouse_urteil(plan_doc)
        self.assertIsNotNone(urteil)
        self.assertIn("STALE PLAN", urteil)


if __name__ == "__main__":
    unittest.main(verbosity=2)
