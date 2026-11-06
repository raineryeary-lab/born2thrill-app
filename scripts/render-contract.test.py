import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module():
    spec = importlib.util.spec_from_file_location("render_contract", HERE / "render-contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RenderContractTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.blend = self.root / "interior-modern-baseline.blend"
        self.blend.write_bytes(b"exact blend revision")
        self.reference = self.root / "approved-reference.png"
        self.reference.write_bytes(b"approved reference")
        self.policy = {
            "schema": "zf-render-policy-v1",
            "policy_version": "ZF-RENDER-HARD-RULES-v1",
            "hard_rules": {
                "architecture_locked": True,
                "camera_locked": True,
                "furniture_transform_locked": True,
                "wall_color_family": "warm-white-ivory",
                "roof_colors_excluded": ["red"],
                "entrance_door": "anthracite-brushed-steel-vertical-handle",
                "entrance_door_closed": True,
                "wall_light_anchor": "window-door-head-height",
            },
        }
        self.references = {
            "schema": "zf-render-reference-registry-v1",
            "references": [{
                "id": "warm-modern-master",
                "role": "interior-style",
                "path": str(self.reference),
                "sha256": self.mod.sha256_file(self.reference),
                "approval": "approved",
            }],
        }
        self.job = {
            "schema": "zf-codex-job-v1",
            "job_id": "house-2026-09-15",
            "plan_id": "house",
            "inputs": [{"file": self.blend.name, "sha256": self.mod.sha256_file(self.blend)}],
            "required_outputs": [{
                "filename_hint": "floorplan-warm-modern.png",
                "kind": "interior",
                "source_blend": self.blend.name,
                "floor": "eg",
                "style": "warm-modern",
            }],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def compile(self, references=None, policy=None):
        return self.mod.compile_contract(
            self.job, self.root, policy or self.policy,
            references or self.references, ["warm-modern-master"])

    def test_stale_blender_sha_is_rejected(self):
        contract = self.compile()
        self.blend.write_bytes(b"changed")
        self.assertIn("blend_sha_mismatch", self.mod.preflight(contract, self.root)["error_codes"])

    def test_unapproved_or_wrong_role_reference_is_rejected(self):
        refs = copy.deepcopy(self.references)
        refs["references"][0]["approval"] = "draft"
        with self.assertRaisesRegex(ValueError, "approved"):
            self.compile(refs)
        refs["references"][0]["approval"] = "approved"
        refs["references"][0]["role"] = "exterior-style"
        with self.assertRaisesRegex(ValueError, "role"):
            self.compile(refs)

    def test_missing_hard_rules_are_rejected(self):
        for key in ("wall_color_family", "roof_colors_excluded", "entrance_door",
                    "entrance_door_closed", "wall_light_anchor"):
            policy = copy.deepcopy(self.policy)
            del policy["hard_rules"][key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                self.compile(policy=policy)

    def test_variants_require_approval_bound_to_all_hashes(self):
        contract = self.compile()
        snapshot = {"schema": "zf-scene-snapshot-v1", "camera": {}, "objects": {}}
        master = self.root / "master.png"
        master.write_bytes(b"master")
        no_approval = self.mod.variant_gate(contract, snapshot, master, None)
        self.assertFalse(no_approval["ok"])
        approval = self.mod.make_approval(contract, snapshot, master, "Rainer")
        self.assertTrue(self.mod.variant_gate(contract, snapshot, master, approval)["ok"])
        changed = copy.deepcopy(contract)
        changed["required_outputs"].append({"filename_hint": "other.png"})
        changed["contract_sha256"] = self.mod.content_hash(
            {k: v for k, v in changed.items() if k != "contract_sha256"})
        self.assertFalse(self.mod.variant_gate(changed, snapshot, master, approval)["ok"])

    def test_foreign_old_and_unapproved_outputs_are_excluded(self):
        contract = self.compile()
        active = self.root / "floorplan-warm-modern.png"
        active.write_bytes(b"active")
        old = self.root / "old.png"
        old.write_bytes(b"old")
        catalog = {"images": [
            {"filename": active.name, "sha256": self.mod.sha256_file(active),
             "contract_sha256": contract["contract_sha256"], "state": "approved"},
            {"filename": old.name, "sha256": self.mod.sha256_file(old),
             "contract_sha256": "foreign", "state": "approved"},
            {"filename": "rejected.png", "contract_sha256": contract["contract_sha256"],
             "state": "rejected"},
        ]}
        package = self.mod.package_manifest(contract, self.root, catalog)
        self.assertEqual([x["filename"] for x in package["outputs"]], [active.name])


if __name__ == "__main__":
    unittest.main()
