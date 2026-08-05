import assert from "node:assert/strict";
import test from "node:test";
import { createCanonicalCandidate } from "../src/lib/generator/canonical-candidate.mjs";
import { correctionGeometryHash } from "../src/lib/generator/correction-editor.mjs";

const reference = { projectId: "fixture-reference", qualityStatus: "passed", packageStatus: "training_ready", approvalStatus: "annotated_reference", usageScope: "internal_reference_only", sourceRightsStatus: "restricted_reference" };
function fixture() {
  const source = { schema: "dmh-floorplan-correction-v2", revision: 0, source_reference_id: reference.projectId, provenance: { source_mutated: false }, rights: { usage_scope: "internal_reference_only", wordpress_eligible: false }, building: { coordinate_unit: "mm", footprint_width_mm: 10000, footprint_depth_mm: 8000 }, floors: [{ id: "ground", footprint: [[0,0],[10000,0],[10000,8000],[0,8000]], rooms: [{ id: "room", area_m2: 80, polygon: [[0,0],[10000,0],[10000,8000],[0,8000]] }], walls: [{ id: "wall", start: [0,0], end: [10000,0], thickness: 350 }], openings: [{ id: "window", wall_id: "wall", width: 1200, position: 0.25 }], stair_core_id: null }], shared_stair_core: null, geometry_hash: "" };
  source.geometry_hash = correctionGeometryHash(source);
  return source;
}

test("identity and whole-building mirrors are deterministic and immutable", () => {
  const source = fixture(); const before = JSON.stringify(source);
  for (const transform of ["identity", "mirror_horizontal", "mirror_vertical"]) {
    const first = createCanonicalCandidate({ source, reference, transform, validate: false });
    assert.deepEqual(first, createCanonicalCandidate({ source, reference, transform, validate: false }));
    assert.equal(first.candidate.geometry_hash, correctionGeometryHash(first.candidate));
    assert.equal(first.candidate.floors[0].rooms[0].area_m2, 80);
    assert.equal(first.candidate.floors[0].walls[0].thickness, 350);
    assert.equal(first.candidate.floors[0].openings[0].wall_id, "wall");
    assert.equal(first.candidate.rights.wordpress_eligible, false);
  }
  assert.equal(JSON.stringify(source), before);
});

test("mirrors transform all geometry and reject unsupported or unapproved inputs", () => {
  const source = fixture();
  assert.deepEqual(createCanonicalCandidate({ source, reference, transform: "mirror_horizontal", validate: false }).candidate.floors[0].walls[0], { id: "wall", start: [10000,0], end: [0,0], thickness: 350 });
  assert.deepEqual(createCanonicalCandidate({ source, reference, transform: "mirror_vertical", validate: false }).candidate.floors[0].walls[0], { id: "wall", start: [0,8000], end: [10000,8000], thickness: 350 });
  assert.throws(() => createCanonicalCandidate({ source, reference, transform: "rotate", validate: false }), /Unsupported transform/);
  assert.throws(() => createCanonicalCandidate({ source, reference: { ...reference, qualityStatus: "review" }, transform: "identity", validate: false }), /quality-passed/);
  assert.throws(() => createCanonicalCandidate({ source, reference: { ...reference, projectId: "synthetic" }, transform: "identity", validate: false }), /reference mismatch/);
});
