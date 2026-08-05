import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ACCEPTED_STATUSES = new Set(["annotated", "reviewed", "training_ready"]);

async function readJson(file) {
  const value = await readFile(file, "utf8");
  return JSON.parse(value.replace(/^\uFEFF/, ""));
}

function validPoint(point) {
  const x = Array.isArray(point) ? point[0] : point?.x;
  const y = Array.isArray(point) ? point[1] : point?.y;
  return Number.isFinite(Number(x)) && Number.isFinite(Number(y));
}

function hasValidRoom(annotations) {
  return (annotations.annotations || []).some((room) => {
    const points = room.points || room.polygon || [];
    return Array.isArray(points) && points.length >= 3 && points.every(validPoint);
  });
}

function hasUnassignedRoom(annotations) {
  return (annotations.annotations || []).some((room) =>
    [room.room_id, ...(room.room_ids || [])].some((id) => String(id || "").toLowerCase() === "unassigned"));
}

function authoritativeDimensions(annotations, metadata) {
  const candidates = [
    annotations.building_dimensions,
    annotations.footprint_dimensions,
    annotations.scale_reference,
    metadata.building_dimensions,
    metadata.footprint_dimensions,
    metadata.scale_reference,
  ].filter(Boolean);
  for (const value of candidates) {
    const width = Number(value.width_mm ?? value.footprint_width_mm ?? value.overall_width_mm);
    const depth = Number(value.depth_mm ?? value.footprint_depth_mm ?? value.overall_depth_mm);
    if (width > 0 && depth > 0) return { width_mm: width, depth_mm: depth };
  }
  return null;
}

export async function inspectProject(projectDir) {
  const projectId = path.basename(projectDir);
  let annotations;
  let metadata;
  try {
    annotations = await readJson(path.join(projectDir, "annotations.json"));
  } catch (error) {
    return { project_id: projectId, included: false, reason: error?.code === "ENOENT" ? "missing_annotations" : "invalid_annotations_json" };
  }
  try {
    metadata = await readJson(path.join(projectDir, "training-data.json"));
  } catch (error) {
    return { project_id: projectId, included: false, reason: error?.code === "ENOENT" ? "missing_training_data" : "invalid_training_data_json" };
  }
  if (hasUnassignedRoom(annotations)) return { project_id: projectId, included: false, reason: "unassigned_room" };
  const rights = metadata.usage_rights || {};
  if (rights.commercial_use_allowed === false || rights.generator_export_allowed === false) {
    return { project_id: projectId, included: false, reason: "rights_disallow_export" };
  }
  const packageStatus = annotations.package_status || metadata.package_status || "draft";
  if (!ACCEPTED_STATUSES.has(packageStatus)) return { project_id: projectId, included: false, reason: "package_status_not_exportable", package_status: packageStatus };
  if ((annotations.quality_checks?.empty_floors || []).length) return { project_id: projectId, included: false, reason: "empty_floor" };
  if (!hasValidRoom(annotations)) return { project_id: projectId, included: false, reason: "no_valid_room_polygon" };
  const dimensions = authoritativeDimensions(annotations, metadata);
  return {
    project_id: annotations.project_id || metadata.project_id || projectId,
    included: true,
    reason: "included",
    house_type: metadata.house_type || "other",
    package_status: packageStatus,
    quality_passed: annotations.quality_checks?.passed === true,
    dimensions,
    canonical_ready: Boolean(dimensions) && annotations.quality_checks?.passed === true,
    publication_eligible: false,
    external_delivery: "blocked",
  };
}

export async function auditCorpus(projectsDir) {
  const entries = (await readdir(projectsDir, { withFileTypes: true })).filter((entry) => entry.isDirectory()).sort((a, b) => a.name.localeCompare(b.name));
  const projects = [];
  for (const entry of entries) projects.push(await inspectProject(path.join(projectsDir, entry.name)));
  const included = projects.filter((item) => item.included);
  const excluded = projects.filter((item) => !item.included);
  const countBy = (items, field) => Object.fromEntries([...items.reduce((map, item) => map.set(String(item[field] ?? "unknown"), (map.get(String(item[field] ?? "unknown")) || 0) + 1), new Map())].sort(([a], [b]) => a.localeCompare(b)));
  return {
    schema: "simplifier-batch-canonical-audit-v1",
    source_project_count: projects.length,
    included_count: included.length,
    excluded_count: excluded.length,
    quality_passed_count: included.filter((item) => item.quality_passed).length,
    scale_ready_count: included.filter((item) => item.dimensions).length,
    canonical_ready_count: included.filter((item) => item.canonical_ready).length,
    publication_eligible_count: 0,
    external_delivery: "blocked",
    included_by_house_type: countBy(included, "house_type"),
    excluded_by_reason: countBy(excluded, "reason"),
    projects,
  };
}

async function main() {
  const projectsDir = path.resolve(process.argv[2]);
  const outputFile = path.resolve(process.argv[3]);
  const report = await auditCorpus(projectsDir);
  await mkdir(path.dirname(outputFile), { recursive: true });
  await writeFile(outputFile, JSON.stringify({ ...report, generated_at: new Date().toISOString() }, null, 2) + "\n");
  console.log(JSON.stringify({ source_project_count: report.source_project_count, included_count: report.included_count, excluded_count: report.excluded_count, quality_passed_count: report.quality_passed_count, scale_ready_count: report.scale_ready_count, canonical_ready_count: report.canonical_ready_count, included_by_house_type: report.included_by_house_type, excluded_by_reason: report.excluded_by_reason }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => { console.error(error); process.exit(1); });
}