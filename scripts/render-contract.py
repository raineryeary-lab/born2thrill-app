#!/usr/bin/env python3
"""Compile and enforce content-addressed ZuhauseFinder render contracts."""

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path


REQUIRED_RULES = (
    "architecture_locked", "camera_locked", "furniture_transform_locked",
    "wall_color_family", "roof_colors_excluded", "entrance_door",
    "entrance_door_closed", "wall_light_anchor",
)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def content_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _expected_reference_roles(job):
    kinds = {item.get("kind") for item in job.get("required_outputs", [])}
    roles = set()
    if "interior" in kinds:
        roles.add("interior-style")
    if "exterior" in kinds:
        roles.add("exterior-style")
    return roles


def compile_contract(job, job_folder, policy, registry, reference_ids):
    rules = policy.get("hard_rules") or {}
    for key in REQUIRED_RULES:
        if key not in rules or rules[key] in (None, "", [], False):
            raise ValueError("required hard rule missing: %s" % key)
    by_id = {item.get("id"): item for item in registry.get("references", [])}
    refs = []
    expected_roles = _expected_reference_roles(job)
    for reference_id in reference_ids:
        item = by_id.get(reference_id)
        if not item:
            raise ValueError("reference not registered: %s" % reference_id)
        if item.get("approval") != "approved":
            raise ValueError("reference is not approved: %s" % reference_id)
        if item.get("role") not in expected_roles:
            raise ValueError("reference has wrong role: %s" % reference_id)
        path = Path(item["path"])
        if not path.is_absolute():
            path = Path(job_folder) / path
        actual = sha256_file(path)
        if actual != item.get("sha256"):
            raise ValueError("reference sha256 mismatch: %s" % reference_id)
        refs.append({"id": reference_id, "role": item["role"], "path": str(path),
                     "sha256": actual, "approval": "approved"})
    covered_roles = {item["role"] for item in refs}
    missing_roles = sorted(expected_roles - covered_roles)
    if missing_roles:
        raise ValueError("approved reference missing for role: %s"
                         % ", ".join(missing_roles))
    inputs = []
    for item in job.get("inputs", []):
        path = Path(job_folder) / item["file"]
        inputs.append({"file": item["file"], "path": str(path),
                       "sha256": item["sha256"]})
    contract = {
        "schema": "zf-effective-render-contract-v1",
        "policy_version": policy["policy_version"],
        "job_id": job["job_id"],
        "plan_id": job["plan_id"],
        "job_schema": job.get("schema"),
        "inputs": inputs,
        "references": refs,
        "protected_invariants": rules,
        "required_outputs": job.get("required_outputs", []),
    }
    contract["contract_sha256"] = content_hash(contract)
    return contract


def preflight(contract, job_folder):
    errors = []
    for item in contract.get("inputs", []):
        path = Path(item.get("path") or Path(job_folder) / item["file"])
        if not path.exists():
            errors.append({"code": "blend_missing", "file": item["file"]})
        elif sha256_file(path) != item.get("sha256"):
            errors.append({"code": "blend_sha_mismatch", "file": item["file"]})
    for item in contract.get("references", []):
        path = Path(item["path"])
        if item.get("approval") != "approved":
            errors.append({"code": "reference_unapproved", "id": item.get("id")})
        elif not path.exists() or sha256_file(path) != item.get("sha256"):
            errors.append({"code": "reference_sha_mismatch", "id": item.get("id")})
    return {
        "schema": "zf-render-preflight-v1", "ok": not errors,
        "contract_sha256": contract.get("contract_sha256"),
        "errors": errors, "error_codes": [x["code"] for x in errors],
        "human_required": ["semantic image quality", "master approval"],
    }


def snapshot_hash(snapshot):
    return content_hash(snapshot)


def make_approval(contract, snapshot, master_path, reviewer):
    master_path = Path(master_path)
    return {
        "schema": "zf-render-master-approval-v1",
        "state": "approved",
        "reviewer": reviewer,
        "approved_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "contract_sha256": contract["contract_sha256"],
        "scene_snapshot_sha256": snapshot_hash(snapshot),
        "master_file": master_path.name,
        "master_sha256": sha256_file(master_path),
        "reference_sha256s": [x["sha256"] for x in contract.get("references", [])],
    }


def variant_gate(contract, snapshot, master_path, approval):
    reasons = []
    if not approval or approval.get("state") != "approved":
        reasons.append("master_not_approved")
    else:
        expected = {
            "contract_sha256": contract.get("contract_sha256"),
            "scene_snapshot_sha256": snapshot_hash(snapshot),
            "master_sha256": sha256_file(master_path),
            "reference_sha256s": [x["sha256"] for x in contract.get("references", [])],
        }
        for key, value in expected.items():
            if approval.get(key) != value:
                reasons.append("approval_%s_mismatch" % key)
    return {"ok": not reasons, "reasons": reasons}


def package_manifest(contract, folder, catalog):
    allowed = {item["filename_hint"] for item in contract.get("required_outputs", [])}
    outputs = []
    for item in catalog.get("images", catalog.get("entries", [])):
        name = item.get("filename")
        path = Path(folder) / str(name)
        if (name in allowed and item.get("state") == "approved"
                and item.get("contract_sha256") == contract.get("contract_sha256")
                and path.is_file() and sha256_file(path) == item.get("sha256")):
            outputs.append({"filename": name, "sha256": item["sha256"]})
    return {"schema": "zf-render-package-manifest-v1",
            "contract_sha256": contract.get("contract_sha256"),
            "outputs": sorted(outputs, key=lambda x: x["filename"])}


def _read(path):
    with Path(path).open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("--job", required=True)
    compile_cmd.add_argument("--policy", required=True)
    compile_cmd.add_argument("--references", required=True)
    compile_cmd.add_argument("--reference-id", action="append", default=[])
    compile_cmd.add_argument("--output", default="effective-contract.json")
    check = sub.add_parser("preflight")
    check.add_argument("--contract", required=True)
    check.add_argument("--output", default="preflight.json")
    args = parser.parse_args()
    if args.command == "compile":
        job_path = Path(args.job).resolve()
        result = compile_contract(_read(job_path), job_path.parent, _read(args.policy),
                                  _read(args.references), args.reference_id)
    else:
        contract_path = Path(args.contract).resolve()
        result = preflight(_read(contract_path), contract_path.parent)
    _write(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("ok", True) else 2)


if __name__ == "__main__":
    main()
