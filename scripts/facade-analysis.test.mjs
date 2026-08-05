import assert from "node:assert/strict";
import test from "node:test";
import { analyzeFacades } from "../src/lib/generator/facade-analysis.mjs";

const canonical = {
  geometry_hash: "facade-fixture",
  building: { footprint_width_mm: 10000, footprint_depth_mm: 8000, floor_height_mm: 2800 },
  floors: [{
    id: "ground",
    footprint: [[0,0],[10000,0],[10000,8000],[0,8000]],
    walls: [
      { id: "street-wall", start: [0,0], end: [10000,0], thickness: 350, wall_type: "exterior" },
      { id: "east-wall", start: [10000,0], end: [10000,8000], thickness: 350, wall_type: "exterior" },
      { id: "garden-wall", start: [10000,8000], end: [0,8000], thickness: 350, wall_type: "exterior" },
      { id: "west-wall", start: [0,8000], end: [0,0], thickness: 350, wall_type: "exterior" },
    ],
    openings: [
      { id: "entrance", wall_id: "street-wall", opening_type: "door", role: "main_entrance", width: 1100, height_mm: 2100, sill_height_mm: 0, connects: ["outside","hall"] },
      { id: "terrace", wall_id: "garden-wall", opening_type: "door", role: "terrace_door", glazed: true, width: 1800, height_mm: 2300, sill_height_mm: 0, connects: ["outside","living"] },
      { id: "garden-window", wall_id: "garden-wall", opening_type: "window", role: "standard", width: 1800, height_mm: 2300, sill_height_mm: 0, connects: ["outside","living"] },
      { id: "east-window", wall_id: "east-wall", opening_type: "window", role: "standard", width: 1200, height_mm: 1350, sill_height_mm: 900, connects: ["outside","office"] },
      { id: "west-window", wall_id: "west-wall", opening_type: "window", role: "standard", width: 700, height_mm: 1350, sill_height_mm: 900, connects: ["outside","utility"] },
    ],
  }],
};

test("facade analysis identifies garden and street from opening roles", () => {
  const analysis = analyzeFacades(canonical, { preferredView: "garden", cameraAngleDeg: 35 });
  assert.equal(analysis.facades.length, 4);
  assert.equal(analysis.semantic.garden_facade_id, "facade-max_y");
  assert.equal(analysis.semantic.street_facade_id, "facade-min_y");
  assert.equal(analysis.selection.selected_facade_id, "facade-max_y");
  assert.equal(analysis.selection.camera_angle_deg, 35);
  assert.equal(analysis.selection.adjacent_facade_id, "facade-max_x");
  assert.ok(analysis.facades.every((facade) => Array.isArray(facade.score_breakdown)));
  assert.ok(analysis.facades.find((facade) => facade.id === "facade-max_y").evidence_opening_ids.includes("terrace"));
});

test("facade camera angle is constrained to 28 through 45 degrees", () => {
  assert.throws(() => analyzeFacades(canonical, { preferredView: "garden", cameraAngleDeg: 27 }), /28.*45/);
  assert.throws(() => analyzeFacades(canonical, { preferredView: "garden", cameraAngleDeg: 46 }), /28.*45/);
  assert.doesNotThrow(() => analyzeFacades(canonical, { preferredView: "garden", cameraAngleDeg: 28 }));
  assert.doesNotThrow(() => analyzeFacades(canonical, { preferredView: "garden", cameraAngleDeg: 45 }));
});

test("facade analysis is deterministic and keeps presentation separate from geometry", () => {
  const first = analyzeFacades(canonical, { preferredView: "garden", cameraAngleDeg: 35 });
  const second = analyzeFacades(structuredClone(canonical), { preferredView: "garden", cameraAngleDeg: 35 });
  assert.deepEqual(first, second);
  assert.equal(first.source_geometry_hash, canonical.geometry_hash);
  assert.match(first.presentation_hash, /^[a-f0-9]{64}$/);
});
