import assert from "node:assert/strict";
import test from "node:test";
import { approvalMatches, approvedPackageEntries, contentHash } from "./render-contract.mjs";

test("approval is invalidated by a bound hash change", () => {
  const contract = { contract_sha256: "contract", references: [{ sha256: "reference" }] };
  const snapshot = { camera: [1, 2, 3] };
  const approval = {
    state: "approved",
    contract_sha256: "contract",
    scene_snapshot_sha256: contentHash(snapshot),
    master_sha256: "master",
    reference_sha256s: ["reference"],
  };
  assert.equal(approvalMatches({ contract, snapshot, masterSha256: "master", approval }), true);
  assert.equal(approvalMatches({ contract: { ...contract, contract_sha256: "changed" }, snapshot, masterSha256: "master", approval }), false);
});

test("packaging excludes rejected, foreign, and unrequested outputs", () => {
  const contract = { contract_sha256: "active", required_outputs: [{ filename_hint: "wanted.png" }] };
  const entries = [
    { filename: "wanted.png", state: "approved", contract_sha256: "active" },
    { filename: "wanted.png", state: "rejected", contract_sha256: "active" },
    { filename: "wanted.png", state: "approved", contract_sha256: "foreign" },
    { filename: "old.png", state: "approved", contract_sha256: "active" },
  ];
  assert.deepEqual(approvedPackageEntries(contract, entries), [entries[0]]);
});
