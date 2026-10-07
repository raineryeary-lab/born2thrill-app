import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { auditCorpus, inspectProject } from "./batch-canonical-promotion.mjs";

async function fixture(root, id, { status = "reviewed", rights = {}, rooms = true, empty = false, passed = true, dimensions = null, bom = false } = {}) {
  const dir = path.join(root, id);
  await mkdir(dir, { recursive: true });
  const annotations = { project_id: id, package_status: status, annotations: rooms ? [{ room_id: "wohnen", points: [[0,0],[1,0],[1,1]] }] : [], quality_checks: { passed, empty_floors: empty ? ["groundfloor"] : [] } };
  if (dimensions) annotations.building_dimensions = dimensions;
  const metadata = { project_id: id, house_type: "bungalow", package_status: status, usage_rights: rights };
  await writeFile(path.join(dir, "annotations.json"), JSON.stringify(annotations));
  await writeFile(path.join(dir, "training-data.json"), (bom ? "\uFEFF" : "") + JSON.stringify(metadata));
  return dir;
}

test("inspectProject accepts BOM and blocks publication while classifying canonical readiness", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "batch-canonical-"));
  const dir = await fixture(root, "valid", { bom: true, dimensions: { width_mm: 10000, depth_mm: 8000 } });
  const result = await inspectProject(dir);
  assert.equal(result.included, true);
  assert.equal(result.canonical_ready, true);
  assert.equal(result.publication_eligible, false);
  assert.equal(result.external_delivery, "blocked");
});

test("audit accounts for every directory with stable exclusion reasons", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "batch-canonical-"));
  await fixture(root, "valid");
  await fixture(root, "draft", { status: "draft" });
  await fixture(root, "empty", { empty: true });
  await fixture(root, "rights", { rights: { generator_export_allowed: false } });
  await fixture(root, "rooms", { rooms: false });
  await mkdir(path.join(root, "missing"));
  const report = await auditCorpus(root);
  assert.equal(report.source_project_count, 6);
  assert.equal(report.included_count + report.excluded_count, 6);
  assert.deepEqual(report.excluded_by_reason, { empty_floor: 1, missing_annotations: 1, no_valid_room_polygon: 1, package_status_not_exportable: 1, rights_disallow_export: 1 });
  assert.equal(report.publication_eligible_count, 0);
});