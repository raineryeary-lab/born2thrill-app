import assert from "node:assert/strict";
import test from "node:test";
import { planRoomFurniture, planFloorFurniture } from "../src/lib/generator/furniture-placement.mjs";

const sleepingRoom = { id: "room-bed", name: "Eltern / Schlafen", kind: "sleeping", polygon: [[0, 0], [4000, 0], [4000, 3500], [0, 3500]] };

test("bed, wardrobe, nightstand, rug and mirror are placed with exact centered/offset geometry", () => {
  const plan = planRoomFurniture(sleepingRoom, "modern");
  assert.equal(plan.room_id, "room-bed");
  assert.equal(plan.unplaced.length, 0);
  assert.equal(plan.placements.length, 5);

  const bed = plan.placements.find((item) => item.type === "bed_double");
  assert.deepEqual(bed.position_mm, [2000, 1040]);
  assert.equal(bed.rotation_deg, 0);
  assert.equal(bed.height_mm, 0);

  const wardrobe = plan.placements.find((item) => item.type === "wardrobe");
  assert.deepEqual(wardrobe.position_mm, [2000, 3160]);
  assert.equal(wardrobe.rotation_deg, 180);

  const mirror = plan.placements.find((item) => item.type === "mirror");
  assert.deepEqual(mirror.position_mm, [3945, 1750]);
  assert.equal(mirror.rotation_deg, 90);
  assert.equal(mirror.height_mm, 1400, "wall-mounted items render at their catalog mount height, not on the floor");

  const nightstand = plan.placements.find((item) => item.type === "nightstand");
  assert.deepEqual(nightstand.position_mm, [240, 1750]);
  assert.equal(nightstand.rotation_deg, -90);

  const rug = plan.placements.find((item) => item.type === "rug");
  assert.deepEqual(rug.position_mm, [2000, 1750], "a floor_center item sits at the room centroid");
  assert.equal(rug.rotation_deg, 0);
  assert.equal(rug.height_mm, 0);
});

test("a rug is always placed (never competes for wall space) even when the room is too small for wall furniture", () => {
  const tinyRoom = { id: "room-tiny", kind: "sleeping", polygon: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]] };
  const plan = planRoomFurniture(tinyRoom, "modern");
  const types = plan.placements.map((item) => item.type).sort();
  assert.deepEqual(types, ["mirror", "nightstand", "rug"]);
  const unplacedTypes = plan.unplaced.map((item) => item.type).sort();
  assert.deepEqual(unplacedTypes, ["bed_double", "wardrobe"]);
  for (const item of plan.unplaced) assert.equal(item.reason, "insufficient_wall_length");
});

test("a plain living room gets seating and decor but no dining table", () => {
  const room = { id: "room-living", name: "Wohnen", kind: "living", polygon: [[0, 0], [5000, 0], [5000, 4000], [0, 4000]] };
  const plan = planRoomFurniture(room, "modern");
  const placedTypes = plan.placements.map((item) => item.type).sort();
  assert.deepEqual(placedTypes, ["coffee_table", "rug", "sofa", "tv_unit", "wall_art"]);
  assert.ok(!placedTypes.includes("dining_table"));
  // A plain rectangle only has 4 wall edges; rug doesn't need one, but with
  // sofa/tv_unit/coffee_table/wall_art already claiming all 4, floor_lamp
  // and potted_plant correctly run out of walls rather than overlapping.
  const unplacedTypes = plan.unplaced.map((item) => item.type).sort();
  assert.deepEqual(unplacedTypes, ["floor_lamp", "potted_plant"]);
});

test("a combined living/dining room adds a dining table but never auto-places freestanding chairs", () => {
  const room = { id: "room-living-dining", name: "Wohnen / Essen / Kochen", kind: "living", polygon: [[0, 0], [6000, 0], [6000, 4500], [0, 4500]] };
  const plan = planRoomFurniture(room, "modern");
  const types = plan.placements.map((item) => item.type).sort();
  assert.deepEqual(types, ["coffee_table", "dining_table", "rug", "sofa", "tv_unit"]);
  assert.ok(!types.includes("dining_chair"), "dining chairs are a deferred v2 surround-placement feature, not a v1 wall placement");
});

test("a garage gets no furniture even though it is a recognized room kind", () => {
  const room = { id: "room-garage", name: "Garage / Carport", kind: "flex", polygon: [[0, 0], [6000, 0], [6000, 6000], [0, 6000]] };
  const plan = planRoomFurniture(room, "modern");
  assert.equal(plan.placements.length, 0);
  assert.equal(plan.unplaced.length, 0);
});

test("an unrecognized room kind produces no furniture rather than guessing", () => {
  const room = { id: "room-mystery", kind: "unknown_kind", polygon: [[0, 0], [3000, 0], [3000, 3000], [0, 3000]] };
  const plan = planRoomFurniture(room, "modern");
  assert.equal(plan.placements.length, 0);
  assert.equal(plan.unplaced.length, 0);
});

test("planRoomFurniture rejects a room without a usable polygon", () => {
  assert.throws(() => planRoomFurniture({ id: "no-polygon", kind: "sleeping", polygon: [] }, "modern"), /no usable polygon/);
});

test("planFloorFurniture skips rooms below the minimum area and reports why", () => {
  const floor = {
    id: "floor-0",
    rooms: [
      { id: "tiny", kind: "sleeping", polygon: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]] },
      sleepingRoom,
    ],
  };
  const plan = planFloorFurniture(floor, "modern");
  assert.equal(plan.floor_id, "floor-0");
  assert.equal(plan.skipped.length, 1);
  assert.equal(plan.skipped[0].room_id, "tiny");
  assert.equal(plan.skipped[0].reason, "room_too_small");
  assert.equal(plan.rooms.length, 1);
  assert.equal(plan.rooms[0].room_id, "room-bed");
});
