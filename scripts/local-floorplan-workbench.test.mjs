import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  approvedGeometryHash,
  buildCorrectionDocument,
  commitEditorHistory,
  createEditorHistory,
  redoEditorHistory,
  resetEditorHistory,
  undoEditorHistory,
  validateCorrectionDocument,
  withUpdatedHash,
} from "../src/lib/generator/correction-editor.mjs";
import { FLOORPLAN_RULES, isHabitableRoom } from "../src/lib/generator/floorplan-rulebook.mjs";

const origin = process.env.FLOORPLAN_WORKBENCH_ORIGIN || "http://127.0.0.1:3020";

async function proof() {
  const response = await fetch(`${origin}/api/floorplan-workbench/generate`);
  assert.equal(response.status, 200);
  return response.json();
}

function satisfyGlazingRule(document) {
  const copy = structuredClone(document);
  for (const floor of copy.floors) {
    for (const room of floor.rooms.filter(isHabitableRoom)) {
      const windows = floor.openings.filter((opening) =>
        opening.opening_type === "window" && opening.connects?.includes(room.id)
      );
      assert.ok(windows.length, `fixture room ${room.name} needs an exterior window`);
      const totalWidth = windows.reduce((sum, opening) => sum + opening.width, 0);
      const height = Math.ceil(
        room.area_m2
        * FLOORPLAN_RULES.windows.minimumGlazingToRoomAreaRatio
        * 1_000_000
        / totalWidth,
      );
      windows.forEach((window) => { window.height_mm = height; });
    }
  }
  return withUpdatedHash(copy);
}

test("local health endpoint is explicit about bind and delivery rights", async () => {
  const response = await fetch(`${origin}/api/floorplan-workbench/health`);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    status: "ok",
    service: "floorplan-workbench-local",
    bind: "127.0.0.1:3020",
    rights: "internal_reference_only",
    delivery: "blocked",
  });
});

test("explicit 1.5-storey inspection uses the same clean reference without area synthesis", async () => {
  const first = await proof();
  const second = await proof();
  assert.equal(first.brief.area, 140);
  assert.equal(first.brief.storeyType, "1_5_storey");
  assert.equal(first.reference_layout_id, "onehalfstorey_020");
  assert.equal(first.reference_layout_id, second.reference_layout_id);
  assert.equal(first.geometry_sha256, second.geometry_sha256);
  assert.equal(first.variant.floors.length, 2);
  assert.ok(first.variant.floors.every((floor) => floor.referenceLayoutId === first.reference_layout_id));
  assert.equal(first.validation.synthetic_geometry_fallback, false);
  assert.equal(first.validation.all_floors_reference_based, true);
  assert.equal(first.reference_candidate.quality_status, "passed");
  assert.equal(first.reference_candidate.package_status, "training_ready");
  assert.ok(first.reference_candidates.length > 1);
  assert.ok(first.reference_candidates.every((candidate) =>
    candidate.quality_status === "passed"
    && candidate.package_status === "training_ready"
    && candidate.project_id !== "onehalfstorey_003"
  ));
});

test("restricted references are available only through the explicit reconstruction catalog", async () => {
  const reference = "german_catalog_review_onehalfstorey_1_1_1_efh_120";
  const response = await fetch(`${origin}/api/floorplan-workbench/generate?reference=${reference}`);
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.reference_layout_id, reference);
  assert.equal(result.reference_candidate.reconstruction_only, true);
  assert.equal(result.reference_candidate.source_rights_status, "restricted_reference");
  assert.equal(result.reference_candidate.count, 55);
  assert.equal(result.brief.storeyType, "1_5_storey");
  assert.equal(result.variant.floors.length, 2);
  assert.ok(result.reference_candidates.every((candidate) =>
    candidate.reconstruction_only === true
    && candidate.source_rights_status === "restricted_reference"
  ));
});

test("shared stair core and wall-linked openings survive on both floors", async () => {
  const result = await proof();
  assert.equal(result.validation.shared_stair_core, true);
  assert.equal(result.validation.openings_retained, true);
  assert.ok(result.variant.floors.every((floor) =>
    floor.referenceElements.some((element) => element.type === "door")
    && floor.referenceElements.some((element) => element.type === "window")));
  const stair = JSON.stringify({
    rect: result.variant.stairCore.footprint,
    path: result.variant.stairCore.path,
  });
  assert.ok(result.variant.floors.every((floor) => JSON.stringify({
    rect: floor.stairRect,
    path: floor.stairPath,
  }) === stair));
});

test("hard-invalid canonical candidates withhold JPEG and Blender artifacts", async () => {
  const result = await proof();
  assert.equal(result.validation.valid, false);
  assert.equal(result.jpeg, null);
  assert.equal(result.blender, null);
  assert.equal(result.external_delivery, "blocked");
});

test("massing uses the floorplan geometry hash and external delivery stays blocked", async () => {
  const result = await proof();
  assert.equal(result.massing_geometry_sha256, result.geometry_sha256);
  assert.equal(result.approval_status, "annotated_reference");
  assert.equal(result.usage_scope, "internal_reference_only");
  assert.equal(result.rights_watermark, "INTERNAL REVIEW – NOT FOR CUSTOMER DELIVERY");
  assert.equal(result.external_delivery, "blocked");
});

test("launcher is fixed to loopback port 3020 and loads ignored local env", async () => {
  const launcher = await readFile(new URL("./start-floorplan-workbench.ps1", import.meta.url), "utf8");
  assert.match(launcher, /\[int\]\$Port = 3020/);
  assert.match(launcher, /next dev -H 127\.0\.0\.1 -p \$Port/);
  assert.match(launcher, /\.env\.local/);
  assert.doesNotMatch(launcher, /3011/);
});

test("editor history supports deterministic undo, redo and reset to immutable source", async () => {
  const result = await proof();
  const source = buildCorrectionDocument(result.variant, { createdAt: "2026-07-30T00:00:00.000Z" });
  const history = createEditorHistory(source);
  const changed = structuredClone(source);
  changed.floors[0].rooms[0].polygon[0][0] += 25;
  const committed = commitEditorHistory(history, changed);
  assert.notEqual(committed.present.geometry_hash, source.geometry_hash);
  assert.deepEqual(undoEditorHistory(committed).present, source);
  assert.deepEqual(redoEditorHistory(undoEditorHistory(committed)).present, committed.present);
  assert.deepEqual(resetEditorHistory(committed).present, source);
  assert.equal(source.source_annotation_sha256, committed.present.source_annotation_sha256);
});

test("canonical correction validation blocks floating openings and unshared stairs", async () => {
  const result = await proof();
  const document = buildCorrectionDocument(result.variant);
  const sourceValidation = validateCorrectionDocument(document);
  assert.equal(sourceValidation.valid, false);
  assert.ok(sourceValidation.errors.some((error) => error.startsWith("window_area_below_one_tenth")));
  const validDocument = satisfyGlazingRule(document);
  assert.equal(validateCorrectionDocument(validDocument).valid, true);
  assert.equal(document.building.coordinate_unit, "mm");
  assert.equal(document.source_reference_id, "onehalfstorey_020");
  assert.ok(document.floors.every((floor) =>
    floor.rooms.every((room) => room.polygon.every((point, index) => {
      const next = room.polygon[(index + 1) % room.polygon.length];
      return point[0] === next[0] || point[1] === next[1];
    }))));
  assert.ok(document.floors.every((floor) =>
    floor.walls.every((wall) =>
      (wall.start[0] === wall.end[0] || wall.start[1] === wall.end[1])
      && wall.thickness === (wall.wall_type === "exterior" ? 350 : 100))));
  assert.ok(document.floors.every((floor) =>
    floor.openings.every((opening) =>
      floor.walls.some((wall) => wall.id === opening.wall_id)
      && opening.width >= 300)));
  assert.equal(document.shared_stair_core.usable_width_mm, 900);
  assert.equal(document.shared_stair_core.direction, "up");
  assert.equal(document.shared_stair_core.representation, "clear_core_without_treads");
  assert.equal(document.shared_stair_core.reference_rules.walkingZoneRatio, 0.2);
  assert.deepEqual(document.shared_stair_core.reference_rules.allowedPlanTypes, [
    "straight",
    "quarter_turn",
    "double_quarter_turn",
  ]);
  const hwrArea = document.floors[0].rooms.find((room) => /HWR/.test(room.name)).area_m2;
  assert.ok(hwrArea >= 9 && hwrArea <= 10);
  const groundDoors = document.floors[0].openings.filter((opening) => opening.opening_type === "door");
  assert.equal(groundDoors.find((opening) => opening.role === "main_entrance").width, 1100);
  assert.equal(groundDoors.find((opening) => opening.width === 760).width, 760);
  assert.ok(groundDoors.filter((opening) => opening.role === "standard" && opening.width !== 760).every((opening) => opening.width === 880));
  const floating = structuredClone(validDocument);
  floating.floors[0].openings[0].wall_id = "missing-wall";
  assert.ok(validateCorrectionDocument(withUpdatedHash(floating)).errors.some((error) => error.startsWith("opening_floating")));
  const stair = structuredClone(validDocument);
  stair.floors[1].stair_core_id = "different-stair";
  assert.ok(validateCorrectionDocument(withUpdatedHash(stair)).errors.includes("stair_core_not_shared"));
  const narrow = structuredClone(validDocument);
  narrow.shared_stair_core.usable_width_mm = 899;
  assert.ok(validateCorrectionDocument(withUpdatedHash(narrow)).errors.includes("stair_usable_width_below_900mm"));

  const terrace = structuredClone(validDocument);
  const living = terrace.floors[0].rooms.find((room) => room.kind === "living");
  const terraceOpening = terrace.floors[0].openings.find((opening) =>
    opening.opening_type === "window" && opening.connects?.includes(living.id)
  );
  terraceOpening.opening_type = "door";
  terraceOpening.role = "terrace_door";
  terraceOpening.width = FLOORPLAN_RULES.doors.terraceWidthMm;
  terraceOpening.height_mm = 2300;
  terraceOpening.sill_height_mm = 0;
  terraceOpening.glazed = true;
  terraceOpening.traversable = true;
  assert.equal(validateCorrectionDocument(withUpdatedHash(terrace)).valid, true);
});

test("revision persistence, approval gating and approved package export stay local", async () => {
  const result = await proof();
  const testReference = `test-onehalfstorey-020-${Date.now()}`;
  const variant = structuredClone(result.variant);
  variant.metrics.referenceLayoutId = testReference;
  variant.floors.forEach((floor) => { floor.referenceLayoutId = testReference; });
  const document = buildCorrectionDocument(variant);
  const validDocument = satisfyGlazingRule(document);
  const request = async (action, candidate) => {
    const response = await fetch(`${origin}/api/floorplan-workbench/corrections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, document: candidate }),
    });
    return { response, body: await response.json() };
  };

  const draft = await request("save_draft", validDocument);
  assert.equal(draft.response.status, 201);
  assert.equal(draft.body.document.revision, 1);
  assert.equal(draft.body.document.status, "draft");

  const invalid = structuredClone(draft.body.document);
  invalid.floors[0].openings[0].wall_id = "floating";
  const blocked = await request("approve", withUpdatedHash(invalid));
  assert.equal(blocked.response.status, 422);
  assert.equal(blocked.body.validation.valid, false);

  const approved = await request("approve", draft.body.document);
  assert.equal(approved.response.status, 201);
  assert.equal(approved.body.document.status, "approved");
  assert.equal(approved.body.document.wordpress_eligible, false);

  const exported = await request("export", approved.body.document);
  assert.equal(exported.response.status, 201);
  assert.equal(exported.body.manifest.schema, "dmh-floorplan-approved-package-v3");
  assert.notEqual(exported.body.manifest.geometry_hash, approved.body.document.geometry_hash);
  assert.equal(exported.body.manifest.wordpress_eligible, false);
  assert.equal(exported.body.manifest.source_assets_included, false);
  assert.deepEqual(Object.keys(exported.body.manifest.files).sort(), [
    "canonical-plan.json",
    "floorplan.jpg",
    "geometry-guide.png",
    "massing.json",
  ]);
  const canonical = JSON.parse(await readFile(
    `${exported.body.export_directory}\\canonical-plan.json`,
    "utf8",
  ));
  assert.equal(canonical.provenance.source_assets_included, false);
  assert.equal(canonical.schema, "dmh-floorplan-approved-canonical-v1");
  assert.equal(canonical.geometry_hash, approvedGeometryHash(canonical));
  assert.equal(canonical.geometry_hash, exported.body.manifest.geometry_hash);
  assert.equal(canonical.plan_id, `plan-${canonical.geometry_hash.slice(0, 16)}`);
  const massing = JSON.parse(await readFile(
    `${exported.body.export_directory}\\massing.json`, "utf8",
  ));
  assert.equal(massing.geometry_hash, canonical.geometry_hash);
  assert.equal("source_annotation" in canonical, false);
  assert.equal("source_reference_id" in canonical, false);

  const commercial = structuredClone(approved.body.document);
  commercial.rights = {
    usage_scope: "commercial_generator",
    decision: "commercially_cleared",
    wordpress_eligible: false,
  };
  const commerciallyApproved = await request("approve", commercial);
  assert.equal(commerciallyApproved.body.document.wordpress_eligible, true);

  const commercialExport = await request("export", commerciallyApproved.body.document);
  assert.equal(commercialExport.response.status, 201);
  assert.equal(commercialExport.body.manifest.wordpress_eligible, true);
  assert.equal(commercialExport.body.manifest.rights.usage_scope, "commercial_generator");
  assert.equal(commercialExport.body.manifest.rights.wordpress_eligible, true);
  const reconstructed = satisfyGlazingRule(buildCorrectionDocument(variant, {
    reconstructionOnly: true,
    sourceRightsStatus: "restricted_reference",
  }));
  reconstructed.rights.usage_scope = "commercial_generator";
  reconstructed.rights.decision = "generic_layout_reconstructed";
  reconstructed.rights.commercial_approval_attested = true;
  const reconstructedApproved = await request("approve", reconstructed);
  assert.equal(reconstructedApproved.response.status, 201);
  assert.equal(reconstructedApproved.body.document.wordpress_eligible, true);
});

test("reference review decisions persist locally before loading the next candidate", async () => {
  const result = await proof();
  const response = await fetch(`${origin}/api/floorplan-workbench/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_reference_id: result.reference_layout_id,
      compared_to: null,
      decision: "better",
      note: "automated fixture review",
      geometry_hash: result.geometry_sha256,
    }),
  });
  assert.equal(response.status, 201);
  const body = await response.json();
  assert.equal(body.record.source_reference_id, "onehalfstorey_020");
  assert.equal(body.record.decision, "better");
  assert.equal(body.record.geometry_hash, result.geometry_sha256);
});

test("explicit reference plus allowlisted transform replaces free generation", async () => {
  const referenceId = "german_catalog_review_onehalfstorey_1_1_1_efh_120";
  const response = await fetch(`${origin}/api/floorplan-workbench/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reference_id: referenceId, transform: "identity" }) });
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.source.project_id, referenceId);
  assert.equal(result.transform, "identity");
  assert.equal(result.candidate.geometry_hash, result.geometry_hash);
  assert.equal(result.wordpress_eligible, false);
  assert.equal(result.external_delivery, "blocked");
  if (result.jpeg) assert.equal(result.jpeg.geometry_hash, result.geometry_hash);
  if (result.blender) assert.equal(result.blender.source_geometry_hash, result.geometry_hash);
});

test("free, unknown, and unsupported candidate requests are rejected without fallback", async () => {
  const send = async (body) => fetch(`${origin}/api/floorplan-workbench/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  assert.equal((await send({ entries: [["area", "140"]] })).status, 400);
  assert.equal((await send({ reference_id: "unknown-reference", transform: "identity" })).status, 404);
  assert.equal((await send({ reference_id: "german_catalog_review_onehalfstorey_1_1_1_efh_120", transform: "rotate" })).status, 400);
});

test("hard-invalid geometry cannot invoke Blender or approval", async () => {
  const result = await proof();
  const invalid = structuredClone(result.candidate);
  invalid.floors[0].openings[0].wall_id = "floating";
  const request = async (action) => fetch(`${origin}/api/floorplan-workbench/corrections`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, document: withUpdatedHash(invalid) }) });
  assert.equal((await request("render_blender")).status, 422);
  assert.equal((await request("approve")).status, 422);
});
