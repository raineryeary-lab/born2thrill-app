// Aggregates every per-project visual-catalog.json (images + descriptions,
// schema "visual-catalog-v1") under the durable corrections data repo into
// one searchable index -- the "database" until the real Postgres import
// (born2thrill-app-repo/plans/catalog-database-import-v1.md) exists.
//
// Mirrors the existing build-floorplan-search-catalog.mjs pattern
// (stableJson output, --check mode) but reads FROM
// born2thrill-local-workbench-data/corrections/*/renders/**/catalog.json
// instead of the simplifier dataset.
//
// Usage:
//   node scripts/build-visual-catalog-index.mjs           # write the index
//   node scripts/build-visual-catalog-index.mjs --check   # verify it's current

import { readFile, writeFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..");
// Nicht raten. Codex, 2026-08-21, zweiter Durchgang: der erste Fix las die
// Env-Var, fiel aber bei fehlender Var weiter auf den alten C:-Nachbarordner
// zurueck -- entspricht nicht der Fail-closed-Regel, die alle anderen Skripte
// seit heute befolgen.
if (!process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim()) {
  console.error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
    + "den Datenordner zu erraten. Siehe .env.local.");
  process.exit(1);
}
const DATA_ROOT = path.resolve(process.env.FLOORPLAN_WORKBENCH_DATA_DIR, "corrections");
const OUTPUT_PATH = path.join(REPO, "data", "visual-catalog", "visual-search-catalog.json");
const SCHEMA = "visual-catalog-index-v1";

async function findCatalogFiles(root) {
  const found = [];
  async function walk(dir) {
    let entries;
    try {
      entries = await readdir(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
      } else if (entry.isFile() && entry.name === "catalog.json") {
        found.push(full);
      }
    }
  }
  await walk(root);
  return found.sort();
}

// project_id is the corrections/<project_id>/ path segment right after
// DATA_ROOT -- every catalog file lives at corrections/<id>/renders/...
function projectIdFor(catalogPath) {
  const rel = path.relative(DATA_ROOT, catalogPath);
  return rel.split(path.sep)[0];
}

const REQUIRED_FIELDS = ["asset_id", "file", "asset_type", "description_de", "qc_status"];

async function validateAndCollect(catalogPath, projectId, seenAssetIds, issues) {
  const dir = path.dirname(catalogPath);
  let parsed;
  try {
    parsed = JSON.parse(await readFile(catalogPath, "utf8"));
  } catch (error) {
    issues.push({ project_id: projectId, catalog: catalogPath, issue: "unreadable_or_invalid_json", detail: String(error) });
    return [];
  }
  const records = [];
  for (const asset of parsed.assets ?? []) {
    const missing = REQUIRED_FIELDS.filter((field) => !asset[field]);
    if (missing.length) {
      issues.push({ project_id: projectId, catalog: catalogPath, asset_id: asset.asset_id ?? null,
        issue: "missing_required_fields", detail: missing.join(",") });
      continue;
    }
    if (seenAssetIds.has(asset.asset_id)) {
      issues.push({ project_id: projectId, catalog: catalogPath, asset_id: asset.asset_id,
        issue: "duplicate_asset_id" });
      continue;
    }
    seenAssetIds.add(asset.asset_id);

    const imagePath = path.join(dir, asset.file);
    let imageExists = true;
    try {
      await stat(imagePath);
    } catch {
      imageExists = false;
      issues.push({ project_id: projectId, catalog: catalogPath, asset_id: asset.asset_id,
        issue: "image_file_missing", detail: asset.file });
    }

    if (!asset.geometry_source) {
      issues.push({ project_id: projectId, catalog: catalogPath, asset_id: asset.asset_id,
        issue: "provenance_missing_geometry_source" });
    }
    // Reference render is required for anything a human is meant to trust
    // as "verified against real geometry" (Rainer, 2026-08-16) -- flagged,
    // not silently dropped, since older entries predate this rule.
    if (!asset.geometry_reference_render) {
      issues.push({ project_id: projectId, catalog: catalogPath, asset_id: asset.asset_id,
        issue: "provenance_missing_reference_render" });
    }

    records.push({
      ...asset,
      project_id: projectId,
      source_catalog: path.relative(REPO, catalogPath).split(path.sep).join("/"),
      image_path: path.relative(REPO, imagePath).split(path.sep).join("/"),
      image_verified: imageExists,
    });
  }
  return records;
}

export async function buildVisualCatalogIndex(dataRoot = DATA_ROOT) {
  const catalogFiles = await findCatalogFiles(dataRoot);
  const seenAssetIds = new Set();
  const issues = [];
  const records = [];
  for (const catalogPath of catalogFiles) {
    const projectId = projectIdFor(catalogPath);
    records.push(...(await validateAndCollect(catalogPath, projectId, seenAssetIds, issues)));
  }
  const byStatus = {};
  for (const record of records) byStatus[record.qc_status] = (byStatus[record.qc_status] ?? 0) + 1;

  return {
    schema: SCHEMA,
    source_catalog_count: catalogFiles.length,
    totals: { records: records.length, projects: new Set(records.map((r) => r.project_id)).size, issues: issues.length },
    by_qc_status: byStatus,
    issues,
    records,
  };
}

export function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function runCli() {
  const output = stableJson(await buildVisualCatalogIndex());
  if (process.argv.includes("--check")) {
    const current = await readFile(OUTPUT_PATH, "utf8").catch(() => "");
    if (current !== output) throw new Error("visual-search-catalog.json is missing or stale; run the index builder.");
    console.log("visual-search-catalog.json is current.");
    return;
  }
  await import("node:fs/promises").then(({ mkdir }) => mkdir(path.dirname(OUTPUT_PATH), { recursive: true }));
  await writeFile(OUTPUT_PATH, output, "utf8");
  const parsed = JSON.parse(output);
  console.log(`Wrote ${OUTPUT_PATH} — ${parsed.totals.records} records from ${parsed.totals.projects} project(s), ${parsed.totals.issues} issue(s) flagged.`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  await runCli();
}
