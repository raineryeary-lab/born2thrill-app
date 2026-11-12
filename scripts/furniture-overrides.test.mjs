// Manual furniture overrides on top of the automatic placement engine.
// See plans/move-furniture-to-workbench.md (APPROVED, 2026-08-16).
//
// The annotator's hand-placed symbols are being retired; the workbench takes
// over furnishing. The engine keeps producing the default layout, and a human
// edit is recorded as an override against a stable placement id rather than
// as a wholesale replacement — so re-running the engine after a geometry fix
// does not silently discard the hand work.

import assert from "node:assert/strict";
import test from "node:test";
import { planRoomFurniture, planFloorFurniture } from "../src/lib/generator/furniture-placement.mjs";
import {
  applyFurnitureOverrides,
  placementId,
  emptyOverrideDocument,
  upsertOverride,
} from "../src/lib/generator/furniture-overrides.mjs";

const sleepingRoom = {
  id: "room-bed",
  name: "Eltern / Schlafen",
  kind: "sleeping",
  polygon: [[0, 0], [4000, 0], [4000, 3500], [0, 3500]],
};
const floor = { id: "groundfloor", rooms: [sleepingRoom] };

function planned() {
  return planFloorFurniture(floor, "modern");
}

test("every engine placement carries a stable id and an engine source", () => {
  const merged = applyFurnitureOverrides(planned(), emptyOverrideDocument());
  const bed = merged.rooms[0].placements.find((item) => item.type === "bed_double");
  assert.equal(bed.placement_id, "room-bed:bed_double");
  assert.equal(bed.source, "engine");
  assert.equal(bed.mirrored, false);
  // Ids must survive a re-plan, or an override would orphan itself the first
  // time the engine runs again.
  const again = applyFurnitureOverrides(planned(), emptyOverrideDocument());
  assert.equal(again.rooms[0].placements.find((i) => i.type === "bed_double").placement_id,
    "room-bed:bed_double");
});

test("a move override replaces position, rotation and mirroring, and marks the item manual", () => {
  const doc = upsertOverride(emptyOverrideDocument(), {
    placement_id: "room-bed:bed_double",
    action: "move",
    position_mm: [1234, 2345],
    rotation_deg: 45,
    mirrored: true,
  });
  const merged = applyFurnitureOverrides(planned(), doc);
  const bed = merged.rooms[0].placements.find((item) => item.type === "bed_double");
  assert.deepEqual(bed.position_mm, [1234, 2345]);
  assert.equal(bed.rotation_deg, 45);
  assert.equal(bed.mirrored, true);
  assert.equal(bed.source, "manual");
  assert.equal(bed.asset_id, planRoomFurniture(sleepingRoom, "modern")
    .placements.find((i) => i.type === "bed_double").asset_id,
    "moving an item must not change which model it is");
});

test("a delete override removes the item and records why it vanished", () => {
  const doc = upsertOverride(emptyOverrideDocument(), {
    placement_id: "room-bed:wardrobe",
    action: "delete",
  });
  const merged = applyFurnitureOverrides(planned(), doc);
  assert.equal(merged.rooms[0].placements.some((i) => i.type === "wardrobe"), false);
  assert.deepEqual(merged.rooms[0].removed, ["room-bed:wardrobe"]);
});

test("an add override introduces furniture the engine never placed", () => {
  const doc = upsertOverride(emptyOverrideDocument(), {
    placement_id: "room-bed:manual-1",
    action: "add",
    room_id: "room-bed",
    type: "dining_chair",
    asset_id: "dining_chair_modern",
    position_mm: [500, 500],
    rotation_deg: 0,
    mirrored: false,
    height_mm: 0,
  });
  const merged = applyFurnitureOverrides(planned(), doc);
  const added = merged.rooms[0].placements.find((i) => i.placement_id === "room-bed:manual-1");
  assert.equal(added.type, "dining_chair");
  assert.equal(added.source, "manual");
  assert.deepEqual(added.position_mm, [500, 500]);
});

test("a replace override swaps the model but keeps the slot", () => {
  const doc = upsertOverride(emptyOverrideDocument(), {
    placement_id: "room-bed:wardrobe",
    action: "replace",
    asset_id: "dressing_wardrobe_classic",
  });
  const merged = applyFurnitureOverrides(planned(), doc);
  const wardrobe = merged.rooms[0].placements.find((i) => i.placement_id === "room-bed:wardrobe");
  assert.equal(wardrobe.asset_id, "dressing_wardrobe_classic");
  assert.equal(wardrobe.source, "manual");
  assert.deepEqual(wardrobe.position_mm,
    planRoomFurniture(sleepingRoom, "modern").placements.find((i) => i.type === "wardrobe").position_mm,
    "replacing a model must not move it");
});

test("upsertOverride replaces an earlier edit of the same placement rather than stacking", () => {
  let doc = emptyOverrideDocument();
  doc = upsertOverride(doc, { placement_id: "room-bed:bed_double", action: "move", position_mm: [1, 1] });
  doc = upsertOverride(doc, { placement_id: "room-bed:bed_double", action: "move", position_mm: [2, 2] });
  assert.equal(doc.overrides.length, 1);
  const merged = applyFurnitureOverrides(planned(), doc);
  assert.deepEqual(merged.rooms[0].placements.find((i) => i.type === "bed_double").position_mm, [2, 2]);
});

test("an override for a room the engine skipped is reported, not silently dropped", () => {
  const doc = upsertOverride(emptyOverrideDocument(), {
    placement_id: "room-gone:sofa",
    action: "move",
    position_mm: [0, 0],
  });
  const merged = applyFurnitureOverrides(planned(), doc);
  assert.deepEqual(merged.orphaned_overrides, ["room-gone:sofa"]);
});

test("placementId is the id the engine and the editor agree on", () => {
  assert.equal(placementId("room-bed", "bed_double"), "room-bed:bed_double");
});

test("overrides never touch the engine's own result object", () => {
  const original = planned();
  const doc = upsertOverride(emptyOverrideDocument(), {
    placement_id: "room-bed:bed_double", action: "delete",
  });
  applyFurnitureOverrides(original, doc);
  assert.equal(original.rooms[0].placements.some((i) => i.type === "bed_double"), true,
    "merging must be pure — the caller may re-use the plan");
});
