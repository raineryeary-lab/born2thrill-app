"""approve-plan.py must cope with a plan that was annotated AFTER the ledger was
last generated (twostorey_050, 2026-09-20: "'twostorey_050' steht nicht im
Ledger" -- 72 of 350 projects were in that state). It creates the entry, but
every existing check stays: reason required, rights declaration honoured,
nothing saved unless the approval goes through."""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def load(tmp):
    os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"] = os.path.join(tmp, "data")
    os.makedirs(os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"], exist_ok=True)
    spec = importlib.util.spec_from_file_location("approve_plan", os.path.join(HERE, "approve-plan.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.LEDGER = os.path.join(tmp, "corpus-ledger.json")
    module.PROJECTS = os.path.join(tmp, "projects")
    module.DATA = os.environ["FLOORPLAN_WORKBENCH_DATA_DIR"]
    return module


def run(module, *argv):
    import sys
    old = sys.argv
    sys.argv = ["approve-plan.py", *argv]
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            try:
                code = module.main()
            except SystemExit as exit_:
                code = exit_.code
    finally:
        sys.argv = old
    return code, out.getvalue()


class MissingLedgerEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.module = load(self.tmp)
        self.ledger = {"schema_version": "floorplan-corpus-ledger-v1",
                       "counts": {"annotated_reference": 1, "approved_real": 0},
                       "projects": [{"project_id": "old_plan", "corpus_status": "annotated_reference",
                                     "commercial_generator_eligible": False}]}
        with open(self.module.LEDGER, "w", encoding="utf-8") as handle:
            json.dump(self.ledger, handle)
        os.makedirs(os.path.join(self.module.PROJECTS, "new_plan"))
        with open(os.path.join(self.module.PROJECTS, "new_plan", "annotations.json"), "w", encoding="utf-8") as handle:
            json.dump({"annotations": []}, handle)

    def read_ledger(self):
        with open(self.module.LEDGER, encoding="utf-8") as handle:
            return json.load(handle)

    def test_a_plan_missing_from_the_ledger_is_added_and_approved(self):
        code, _ = run(self.module, "new_plan", "--reason", "eigener Plan des Chefs", "--by", "Rainer")
        self.assertEqual(code, 0)
        ledger = self.read_ledger()
        entry = next(e for e in ledger["projects"] if e["project_id"] == "new_plan")
        self.assertEqual(entry["corpus_status"], "approved_real")
        self.assertTrue(entry["commercial_generator_eligible"])
        self.assertEqual(entry["reason"], "eigener Plan des Chefs")
        self.assertEqual(entry["approved_by"], "Rainer")
        self.assertEqual(entry["annotation_sha256"], self.module.annotation_hash("new_plan"))
        self.assertEqual(ledger["counts"], {"annotated_reference": 1, "approved_real": 1})

    def test_the_reason_is_still_required_and_nothing_is_saved_without_it(self):
        code, _ = run(self.module, "new_plan")
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.read_ledger()["projects"]), 1)

    def test_a_plan_that_is_not_on_disk_is_still_refused(self):
        code, _ = run(self.module, "ghost_plan", "--reason", "x")
        self.assertIn("ghost_plan", str(code))
        self.assertEqual(len(self.read_ledger()["projects"]), 1)

    def test_revoking_a_plan_the_ledger_never_had_is_refused(self):
        code, _ = run(self.module, "new_plan", "--revoke", "--reason", "x")
        self.assertNotEqual(code, 0)
        self.assertEqual(len(self.read_ledger()["projects"]), 1)

    def test_an_explicit_no_declaration_still_blocks_and_saves_nothing(self):
        self.module.rechte.erklaeren("nein", "Fremdplan", "plan", "new_plan", "Rainer",
                                     data=self.module.DATA, projects=self.module.PROJECTS)
        code, out = run(self.module, "new_plan", "--reason", "x")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.read_ledger()["projects"]), 1)

    def test_existing_entries_behave_as_before(self):
        os.makedirs(os.path.join(self.module.PROJECTS, "old_plan"))
        with open(os.path.join(self.module.PROJECTS, "old_plan", "annotations.json"), "w", encoding="utf-8") as handle:
            json.dump({"annotations": []}, handle)
        code, _ = run(self.module, "old_plan", "--reason", "ok", "--by", "Rainer")
        self.assertEqual(code, 0)
        ledger = self.read_ledger()
        self.assertEqual(len(ledger["projects"]), 1)
        self.assertEqual(ledger["projects"][0]["corpus_status"], "approved_real")


if __name__ == "__main__":
    unittest.main()
