import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function contentHash(value) {
  return createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

export async function fileHash(path) {
  return createHash("sha256").update(await readFile(path)).digest("hex");
}

export function approvalMatches({ contract, snapshot, masterSha256, approval }) {
  if (!approval || approval.state !== "approved") return false;
  return approval.contract_sha256 === contract.contract_sha256
    && approval.scene_snapshot_sha256 === contentHash(snapshot)
    && approval.master_sha256 === masterSha256
    && canonicalJson(approval.reference_sha256s ?? [])
      === canonicalJson((contract.references ?? []).map((item) => item.sha256));
}

export function approvedPackageEntries(contract, entries) {
  const allowed = new Set((contract.required_outputs ?? []).map((item) => item.filename_hint));
  return entries.filter((item) => allowed.has(item.filename)
    && item.state === "approved"
    && item.contract_sha256 === contract.contract_sha256);
}
