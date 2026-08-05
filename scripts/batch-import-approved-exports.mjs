import { readdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import { importApprovedPackage } from "./import-approved-floorplan-package.mjs";

// Scans every exported Workbench revision under a local data root and
// imports each one that has already been marked commercially cleared and
// wordpress_eligible by a human in the Workbench UI. importApprovedPackage()
// enforces this itself (assertCommercial in import-approved-floorplan-
// package.mjs) — this script makes no rights decisions of its own. Anything
// not yet approved for commercial use fails the import and is reported,
// never silently skipped or force-approved.

export function defaultDataRoot() {
  const configured = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (configured) return resolve(configured);
  const base = process.env.LOCALAPPDATA || process.env.TEMP || ".";
  return join(base, "Born2Thrill", "floorplan-workbench");
}

export async function listExportDirectories(dataRoot) {
  const correctionsRoot = join(dataRoot, "corrections");
  const results = [];
  let references = [];
  try {
    references = await readdir(correctionsRoot);
  } catch (error) {
    if (error?.code === "ENOENT") return results;
    throw error;
  }
  for (const reference of references) {
    const exportsRoot = join(correctionsRoot, reference, "exports");
    let revisions = [];
    try {
      revisions = await readdir(exportsRoot);
    } catch (error) {
      if (error?.code === "ENOENT") continue;
      throw error;
    }
    for (const revision of revisions) {
      results.push({ reference, revision, directory: join(exportsRoot, revision) });
    }
  }
  return results;
}

export async function batchImportApprovedExports({ dataRoot, targetRoot } = {}) {
  const root = dataRoot || defaultDataRoot();
  const directories = await listExportDirectories(root);
  const imported = [];
  const notEligible = [];
  const failed = [];
  for (const entry of directories) {
    try {
      const result = await importApprovedPackage(entry.directory, targetRoot);
      imported.push({ ...entry, ...result });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (/eligible|Commercial rights|attestation|approved/i.test(message)) {
        notEligible.push({ ...entry, reason: message });
      } else {
        failed.push({ ...entry, reason: message });
      }
    }
  }
  return {
    scanned: directories.length,
    imported: imported.map((item) => ({ reference: item.reference, revision: item.revision, plan_id: item.plan_id })),
    not_yet_commercially_cleared: notEligible.map((item) => ({ reference: item.reference, revision: item.revision, reason: item.reason })),
    failed: failed.map((item) => ({ reference: item.reference, revision: item.revision, reason: item.reason })),
  };
}

async function main() {
  const summary = await batchImportApprovedExports({});
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
  if (!summary.scanned) process.stderr.write("No exported Workbench revisions found under the local data root.\n");
}

async function isMain() {
  const { pathToFileURL } = await import("node:url");
  return process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url;
}

if (await isMain()) main().catch((error) => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
