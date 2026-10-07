import { createHash } from "node:crypto";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function json(file) {
  return JSON.parse((await readFile(file, "utf8")).replace(/^\uFEFF/, ""));
}
async function sha256(file) {
  return createHash("sha256").update(await readFile(file)).digest("hex");
}
function counts(projects) {
  const result = { annotated_reference: 0, approved_real: 0 };
  for (const project of projects) result[project.approval_status] += 1;
  return result;
}
export async function hardenSimplifierExport({ exportDir, projectsDir, priorLedgerPath }) {
  const dataset = await json(path.join(exportDir, "dataset.json"));
  const audit = await json(path.join(exportDir, "batch-audit.json"));
  const priorLedger = await json(priorLedgerPath);
  const auditById = new Map(audit.projects.filter((item) => item.included).map((item) => [item.project_id, item]));
  const priorById = new Map((priorLedger.projects || []).map((item) => [item.project_id, item]));
  const projects = [];
  for (const source of dataset.projects) {
    const auditItem = auditById.get(source.project_id);
    if (!auditItem) throw new Error("Missing included audit entry for " + source.project_id);
    const hash = await sha256(path.join(projectsDir, source.project_id, "annotations.json"));
    const prior = priorById.get(source.project_id);
    const unchangedApproved = prior?.corpus_status === "approved_real"
      && prior?.annotation_sha256 === hash
      && auditItem.quality_passed === true;
    const approvalStatus = unchangedApproved ? "approved_real" : "annotated_reference";
    projects.push({
      ...source,
      package_status: auditItem.quality_passed ? "training_ready" : source.package_status,
      source_kind: "real_annotated",
      approval_status: approvalStatus,
      usage_scope: approvalStatus === "approved_real" ? "commercial_generator" : "internal_reference_only",
      quality_status: auditItem.quality_passed ? "passed" : "review_required",
      annotation_sha256: hash,
      source_rights_status: approvalStatus === "approved_real" ? "rights_cleared" : "not_restricted",
      reconstruction_only: false,
      commercial_generator_eligible: approvalStatus === "approved_real",
    });
  }
  dataset.projects = projects;
  dataset.generated_at = new Date().toISOString();
  await writeFile(path.join(exportDir, "dataset.json"), JSON.stringify(dataset, null, 2) + "\n");
  const ledgerProjects = projects.map((project) => ({
    project_id: project.project_id,
    annotation_sha256: project.annotation_sha256,
    corpus_status: project.approval_status,
    internal_reference_eligible: true,
    commercial_generator_eligible: project.approval_status === "approved_real",
  }));
  const ledger = {
    schema_version: "floorplan-corpus-ledger-v1",
    generated_at: dataset.generated_at,
    policy: {
      unchanged_annotations_are_not_reprocessed_until_hash_changes: true,
      commercial_approval_requires_explicit_rights_and_quality: true,
      generated_candidates_require_human_approval: true,
    },
    counts: counts(projects),
    projects: ledgerProjects,
  };
  await writeFile(path.join(exportDir, "corpus-ledger.json"), JSON.stringify(ledger, null, 2) + "\n");
  return { projects: projects.length, passed: projects.filter((item) => item.quality_status === "passed").length, commercial: projects.filter((item) => item.commercial_generator_eligible).length };
}
async function main() {
  const exportDir = path.resolve(process.argv[2]);
  const projectsDir = path.resolve(process.argv[3]);
  const priorDataDir = path.resolve(process.argv[4]);
  const result = await hardenSimplifierExport({ exportDir, projectsDir, priorLedgerPath: path.join(priorDataDir, "corpus-ledger.json") });
  await copyFile(path.join(priorDataDir, "reconstruction-dataset.json"), path.join(exportDir, "reconstruction-dataset.json"));
  await mkdir(exportDir, { recursive: true });
  console.log(JSON.stringify(result, null, 2));
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => { console.error(error); process.exit(1); });
}