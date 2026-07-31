import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import sharp from "sharp";
import { approvedGeometryHash, importApprovedPackage, inspectApprovedPackage } from "./import-approved-floorplan-package.mjs";
import { selectApprovedFloorplan } from "../src/lib/generator/approved-floorplan-catalog.ts";

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

function makeDocument(storeyType = "1_5_storey", options = {}) {
  const bedrooms = options.bedrooms ?? 3;
  const groundRooms = [
    { id: "living", name: "Wohnen / Essen / Kochen", kind: "living", area_m2: 36 },
    { id: "office", name: options.office === false ? "Gast" : "B?ro", kind: "flex", area_m2: 10 },
    { id: "wc", name: "G?ste-WC", kind: "wet", area_m2: 3 },
    { id: "hwr", name: "HWR / HTR", kind: "service", area_m2: 10 },
    { id: "hall", name: "Diele", kind: "circulation", area_m2: 12 },
  ];
  const upperRooms = [
    ...Array.from({ length: bedrooms }, (_, index) => ({
      id: `bed-${index}`, name: index ? "Kind" : "Eltern / Schlafen", kind: "sleeping", area_m2: 12,
    })),
    { id: "upper-hall", name: "Flur", kind: "circulation", area_m2: 12 },
  ];
  const floor = (id, level, rooms) => ({
    id, name: level ? "Obergeschoss" : "Erdgeschoss", level,
    footprint: [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
    rooms: rooms.map((room, index) => ({
      ...room, polygon: [[index * 1000, 0], [index * 1000 + 900, 0], [index * 1000 + 900, 1000], [index * 1000, 1000]],
    })),
    walls: [{ id: `${id}-wall`, start: [0, 0], end: [10000, 0], thickness: 350, wall_type: "exterior", room_ids: rooms.map((room) => room.id) }],
    openings: [], stair_core_id: storeyType === "1_storey" ? null : "stair-core",
  });
  const floors = storeyType === "1_storey"
    ? [floor("floor-0", 0, [...groundRooms, ...upperRooms])]
    : [floor("floor-0", 0, groundRooms), floor("floor-1", 1, upperRooms)];
  const document = {
    schema: "dmh-floorplan-approved-canonical-v1", revision: 1, plan_id: "",
    provenance: { creation_mode: "manual_correction_revision", source_assets_included: false, internal_source_record_retained_locally: true },
    rights: { source_status: "user_owned", usage_scope: "commercial_generator", decision: "commercially_cleared", commercial_approval_attested: true, wordpress_eligible: true },
    building: { coordinate_unit: "mm", footprint_width_mm: 10000, footprint_depth_mm: 8000, floor_height_mm: 2800, storey_type: storeyType, roof_form: storeyType === "1_storey" ? "flat" : "gable", geometry_source: "rectified_annotated_reference" },
    floors,
    shared_stair_core: storeyType === "1_storey" ? null : { id: "stair-core", polygon: [[7000, 4500], [7900, 4500], [7900, 7000], [7000, 7000]], path: [[7450, 6700], [7450, 4800]], plan_type: "straight", usable_width_mm: 900, direction: "up", representation: "clear_core_without_treads", tread_geometry_valid: false, floor_ids: ["floor-0", "floor-1"] },
    geometry_hash: "", status: "approved", wordpress_eligible: true,
  };
  document.geometry_hash = approvedGeometryHash(document);
  document.plan_id = `plan-${document.geometry_hash.slice(0, 16)}`;
  return document;
}

async function writePackage(root, document, schema = "dmh-floorplan-approved-package-v3") {
  await mkdir(root, { recursive: true });
  const payloads = {
    "canonical-plan.json": Buffer.from(`${JSON.stringify(document, null, 2)}\n`),
    "floorplan.jpg": await sharp({ create: { width: 640, height: 480, channels: 3, background: "#fff" } }).jpeg().toBuffer(),
    "geometry-guide.png": await sharp({ create: { width: 1024, height: 1024, channels: 3, background: "#fff" } }).png().toBuffer(),
    "massing.json": Buffer.from(`${JSON.stringify({ schema: "dmh-floorplan-massing-metadata-v1", plan_id: document.plan_id, geometry_hash: document.geometry_hash, floors: document.floors, shared_stair_core: document.shared_stair_core })}\n`),
  };
  const manifest = {
    schema, plan_id: document.plan_id, source_assets_included: false, revision: document.revision, geometry_hash: document.geometry_hash,
    provenance: document.provenance, rights: document.rights, wordpress_eligible: document.wordpress_eligible, created_at: "2026-07-31T00:00:00.000Z",
    files: Object.fromEntries(Object.entries(payloads).map(([name, bytes]) => [name, { sha256: sha256(bytes), bytes: bytes.length }])),
  };
  for (const [name, bytes] of Object.entries(payloads)) await writeFile(join(root, name), bytes);
  await writeFile(join(root, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

const brief = (storeyType, overrides = {}) => ({ storeyType, area: 140, bedrooms: 3, office: true, guestWc: true, utilityRoom: true, ...overrides });
const record = (document) => ({ document, manifest: { schema: "dmh-floorplan-approved-package-v3", plan_id: document.plan_id, geometry_hash: document.geometry_hash, wordpress_eligible: true, rights: document.rights } });

test("approved package inspection and import are deterministic", async () => {
  const sandbox = await mkdtemp(join(tmpdir(), "zf-approved-"));
  const source = join(sandbox, "source");
  const target = join(sandbox, "catalog");
  const document = makeDocument();
  await writePackage(source, document);
  const inspected = await inspectApprovedPackage(source);
  assert.equal(inspected.document.geometry_hash, approvedGeometryHash(inspected.document));
  const imported = await importApprovedPackage(source, target);
  assert.equal(imported.plan_id, document.plan_id);
  const copied = JSON.parse(await readFile(join(target, `${document.plan_id}.canonical.json`), "utf8"));
  assert.equal(copied.geometry_hash, document.geometry_hash);
  const registry = await readFile(join(target, "catalog.generated.mjs"), "utf8");
  assert.match(registry, new RegExp(document.plan_id));
  assert.doesNotMatch(registry, /source_annotation|source_reference_id/);
});

test("approved package inspection rejects unsafe or unverifiable packages", async (t) => {
  await t.test("legacy package", async () => {
    const root = await mkdtemp(join(tmpdir(), "zf-legacy-"));
    await writePackage(root, makeDocument(), "dmh-floorplan-approved-package-v2");
    await assert.rejects(inspectApprovedPackage(root), /package-v3/);
  });
  await t.test("internal rights", async () => {
    const root = await mkdtemp(join(tmpdir(), "zf-rights-"));
    const document = makeDocument();
    document.rights.usage_scope = "internal_reference_only"; document.rights.wordpress_eligible = false; document.wordpress_eligible = false;
    await writePackage(root, document);
    await assert.rejects(inspectApprovedPackage(root), /commercial|WordPress/i);
  });
  await t.test("changed canonical file", async () => {
    const root = await mkdtemp(join(tmpdir(), "zf-changed-"));
    const document = makeDocument(); await writePackage(root, document);
    document.building.footprint_width_mm += 10;
    await writeFile(join(root, "canonical-plan.json"), JSON.stringify(document));
    await assert.rejects(inspectApprovedPackage(root), /checksum|size/i);
  });
  await t.test("source data", async () => {
    const root = await mkdtemp(join(tmpdir(), "zf-source-"));
    const document = makeDocument(); document.source_annotation = { forbidden: true };
    await writePackage(root, document);
    await assert.rejects(inspectApprovedPackage(root), /source/i);
  });
  await t.test("unexpected file", async () => {
    const root = await mkdtemp(join(tmpdir(), "zf-extra-"));
    await writePackage(root, makeDocument()); await writeFile(join(root, "original.svg"), "<svg/>");
    await assert.rejects(inspectApprovedPackage(root), /unexpected/i);
  });
});

test("catalogue selection never crosses storey types and respects rooms", () => {
  const bungalow = makeDocument("1_storey");
  const oneHalfFar = makeDocument("1_5_storey");
  const oneHalfClose = makeDocument("1_5_storey");
  oneHalfClose.floors[0].rooms[0].area_m2 += 3;
  oneHalfClose.geometry_hash = approvedGeometryHash(oneHalfClose); oneHalfClose.plan_id = `plan-${oneHalfClose.geometry_hash.slice(0, 16)}`;
  const twoStorey = makeDocument("2_storey");
  const records = [bungalow, oneHalfFar, oneHalfClose, twoStorey].map(record);
  assert.equal(selectApprovedFloorplan(brief("1_storey"), records).document.plan_id, bungalow.plan_id);
  assert.equal(selectApprovedFloorplan(brief("1_5_storey"), records).document.plan_id, oneHalfClose.plan_id);
  assert.equal(selectApprovedFloorplan(brief("2_storey"), records).document.plan_id, twoStorey.plan_id);
  assert.equal(selectApprovedFloorplan(brief("1_5_storey", { bedrooms: 5 }), records), null);
  assert.equal(selectApprovedFloorplan(brief("1_5_storey"), [record(makeDocument("1_5_storey", { office: false }))]), null);
});

test("WordPress route cannot use legacy generated fallback", async () => {
  const route = await readFile(
    new URL("../src/app/api/zuhausefinder/floorplan/route.ts", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(route, /generateVariants|selectQualityVariant|renderFloorplanJpeg/);
  assert.match(route, /approved_catalog_required:\s*true/);
  assert.match(route, /noch kein freigegebener korrigierter Grundriss/);
});