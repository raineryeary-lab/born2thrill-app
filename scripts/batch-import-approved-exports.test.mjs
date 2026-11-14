import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import sharp from "sharp";
import { approvedGeometryHash } from "./import-approved-floorplan-package.mjs";
import { batchImportApprovedExports, listExportDirectories } from "./batch-import-approved-exports.mjs";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

function makeDocument(overrides = {}) {
  const floor = {
    id: "floor-0", name: "Erdgeschoss", level: 0,
    footprint: [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
    rooms: [{ id: "living", name: "Wohnen", kind: "living", area_m2: 30, polygon: [[0, 0], [900, 0], [900, 1000], [0, 1000]] }],
    walls: [{ id: "w1", start: [0, 0], end: [10000, 0], thickness: 350, wall_type: "exterior", room_ids: ["living"] }],
    openings: [], stair_core_id: null,
  };
  const document = {
    schema: "dmh-floorplan-approved-canonical-v1", revision: 1, plan_id: "",
    provenance: { creation_mode: "manual_correction_revision", source_assets_included: false, internal_source_record_retained_locally: true },
    rights: { source_status: "user_owned", usage_scope: "commercial_generator", decision: "commercially_cleared", commercial_approval_attested: true, wordpress_eligible: true },
    building: { coordinate_unit: "mm", footprint_width_mm: 10000, footprint_depth_mm: 8000, floor_height_mm: 2800, storey_type: "1_storey", roof_form: "flat", geometry_source: "rectified_annotated_reference" },
    floors: [floor],
    shared_stair_core: null,
    geometry_hash: "", status: "approved", wordpress_eligible: true,
    ...overrides,
  };
  document.geometry_hash = approvedGeometryHash(document);
  document.plan_id = `plan-${document.geometry_hash.slice(0, 16)}`;
  return document;
}

async function writePackage(root, document) {
  await mkdir(root, { recursive: true });
  const payloads = {
    "canonical-plan.json": Buffer.from(`${JSON.stringify(document, null, 2)}\n`),
    "floorplan.jpg": await sharp({ create: { width: 640, height: 480, channels: 3, background: "#fff" } }).jpeg().toBuffer(),
    "geometry-guide.png": await sharp({ create: { width: 1024, height: 1024, channels: 3, background: "#fff" } }).png().toBuffer(),
    "massing.json": Buffer.from(`${JSON.stringify({ schema: "dmh-floorplan-massing-metadata-v1", plan_id: document.plan_id, geometry_hash: document.geometry_hash, floors: document.floors, shared_stair_core: document.shared_stair_core })}\n`),
  };
  const manifest = {
    schema: "dmh-floorplan-approved-package-v3", plan_id: document.plan_id, source_assets_included: false, revision: document.revision, geometry_hash: document.geometry_hash,
    provenance: document.provenance, rights: document.rights, wordpress_eligible: document.wordpress_eligible, created_at: "2026-07-31T00:00:00.000Z",
    files: Object.fromEntries(Object.entries(payloads).map(([name, bytes]) => [name, { sha256: sha256(bytes), bytes: bytes.length }])),
  };
  for (const [name, bytes] of Object.entries(payloads)) await writeFile(join(root, name), bytes);
  await writeFile(join(root, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
}

test("listExportDirectories walks corrections/*/exports/* and tolerates a missing root", async () => {
  const sandbox = await mkdtemp(join(tmpdir(), "zf-batch-scan-"));
  assert.deepEqual(await listExportDirectories(join(sandbox, "does-not-exist")), []);
  const exportDir = join(sandbox, "corrections", "bungalow_024", "exports", "revision-0001");
  await mkdir(exportDir, { recursive: true });
  const found = await listExportDirectories(sandbox);
  assert.equal(found.length, 1);
  assert.equal(found[0].reference, "bungalow_024");
  assert.equal(found[0].revision, "revision-0001");
});

test("batch import only ingests packages already marked commercially cleared", async () => {
  const sandbox = await mkdtemp(join(tmpdir(), "zf-batch-import-"));
  const dataRoot = join(sandbox, "data");
  const targetRoot = join(sandbox, "catalog");

  const cleared = makeDocument();
  await writePackage(join(dataRoot, "corrections", "bungalow_024", "exports", "revision-0001"), cleared);

  const notCleared = makeDocument({
    rights: { source_status: "user_owned", usage_scope: "internal_reference_only", decision: "undecided", commercial_approval_attested: false, wordpress_eligible: false },
    wordpress_eligible: false,
  });
  await writePackage(join(dataRoot, "corrections", "bungalow_034", "exports", "revision-0001"), notCleared);

  const summary = await batchImportApprovedExports({ dataRoot, targetRoot });
  assert.equal(summary.scanned, 2);
  assert.equal(summary.imported.length, 1);
  assert.equal(summary.imported[0].plan_id, cleared.plan_id);
  assert.equal(summary.not_yet_commercially_cleared.length, 1);
  assert.equal(summary.not_yet_commercially_cleared[0].reference, "bungalow_034");
  assert.equal(summary.failed.length, 0);

  const registry = await readdir(targetRoot);
  assert.ok(registry.includes("catalog.generated.mjs"));
  assert.ok(registry.includes(`${cleared.plan_id}.canonical.json`));
  assert.ok(!registry.includes(`${notCleared.plan_id}.canonical.json`));
});

test("re-running the batch import is idempotent for already-imported packages", async () => {
  const sandbox = await mkdtemp(join(tmpdir(), "zf-batch-idempotent-"));
  const dataRoot = join(sandbox, "data");
  const targetRoot = join(sandbox, "catalog");
  const document = makeDocument();
  await writePackage(join(dataRoot, "corrections", "bungalow_024", "exports", "revision-0001"), document);

  const first = await batchImportApprovedExports({ dataRoot, targetRoot });
  const second = await batchImportApprovedExports({ dataRoot, targetRoot });
  assert.equal(first.imported.length, 1);
  assert.equal(second.imported.length, 1);
  assert.equal(second.failed.length, 0);
});
