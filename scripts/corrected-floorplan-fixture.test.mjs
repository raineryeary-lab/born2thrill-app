import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import correction from "../src/lib/generator/fixtures/corrected/onehalfstorey_020.revision-0003.json" with {
  type: "json",
};

const EXPECTED_HASH =
  "7782ddb04f0c9228c09a7e19c509c4c1c886ce5bb2eb5a2f100c048cb07d622e";

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, canonical(value[key])]),
  );
}

function geometryHash(document) {
  return createHash("sha256")
    .update(JSON.stringify(canonical({
      schema: document.schema,
      source_reference_id: document.source_reference_id,
      building: document.building,
      floors: document.floors,
      shared_stair_core: document.shared_stair_core,
    })))
    .digest("hex");
}

test("approved correction fixture keeps its canonical geometry hash", () => {
  assert.equal(correction.schema, "dmh-floorplan-correction-v2");
  assert.equal(correction.source_reference_id, "onehalfstorey_020");
  assert.equal(correction.revision, 3);
  assert.equal(correction.building.coordinate_unit, "mm");
  assert.equal(correction.building.storey_type, "1_5_storey");
  assert.equal(correction.floors.length, 2);
  assert.equal(correction.status, "approved");
  assert.equal(correction.validation.valid, true);
  assert.deepEqual(correction.validation.errors, []);
  assert.equal(correction.geometry_hash, EXPECTED_HASH);
  assert.equal(correction.validation.geometry_hash, EXPECTED_HASH);
  assert.equal(geometryHash(correction), EXPECTED_HASH);
});

test("every corrected opening is linked to a wall and remains inside it", () => {
  for (const floor of correction.floors) {
    const walls = new Map(floor.walls.map((wall) => [wall.id, wall]));
    for (const opening of floor.openings) {
      const wall = walls.get(opening.wall_id);
      assert.ok(wall, `${floor.id}:${opening.id} has no wall`);
      assert.ok(
        Number.isFinite(opening.position)
          && opening.position >= 0
          && opening.position <= 1,
        `${floor.id}:${opening.id} has invalid position`,
      );
      assert.ok(
        Number.isFinite(opening.width) && opening.width > 0,
        `${floor.id}:${opening.id} has invalid width`,
      );
      assert.ok(
        Math.hypot(
          wall.end[0] - wall.start[0],
          wall.end[1] - wall.start[1],
        ) >= opening.width,
        `${floor.id}:${opening.id} is wider than its wall`,
      );
    }
  }
});

test("the corrected stair is one coherent aligned upward system", () => {
  assert.ok(correction.shared_stair_core);
  assert.equal(correction.shared_stair_core.usable_width_mm, 900);
  assert.equal(correction.shared_stair_core.direction, "up");
  assert.equal(correction.shared_stair_core.tread_geometry_valid, false);
  assert.equal(
    correction.shared_stair_core.representation,
    "clear_core_without_treads",
  );
  assert.deepEqual(
    correction.floors.map((floor) => floor.stair_core_id),
    correction.floors.map(() => correction.shared_stair_core.id),
  );
});

test("rights-restricted correction cannot silently become customer eligible", () => {
  assert.equal(correction.rights.usage_scope, "internal_reference_only");
  assert.equal(correction.rights.wordpress_eligible, false);
  assert.equal(correction.wordpress_eligible, false);
});
