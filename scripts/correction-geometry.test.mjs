import assert from "node:assert/strict";
import test from "node:test";
import { mergeCollinearWalls } from "../src/lib/generator/correction-geometry.mjs";

// Manual corrections routinely leave behind wall fragments that are
// collinear, touching, and share the same type/thickness/room pair — e.g.
// a floor rescale or a wall retype only ever touches the fragment the editor
// clicked on, not its neighbour. mergeCollinearWalls collapses those back
// into one wall and re-homes any openings that were sitting on the
// merged-away fragment, recomputing their position ratio from their
// absolute point rather than just copying it.

test("merges two contiguous collinear walls with matching type/thickness/room_ids", () => {
  const floor = {
    walls: [
      {
        id: "f0-wall-001",
        start: [0, 0],
        end: [1000, 0],
        thickness: 100,
        wall_type: "partition",
        room_ids: ["a", "b"],
        length_mm: 1000,
      },
      {
        id: "f0-wall-002",
        start: [1000, 0],
        end: [2500, 0],
        thickness: 100,
        wall_type: "partition",
        room_ids: ["a", "b"],
        length_mm: 1500,
      },
    ],
    openings: [
      // sits on wall-002 at absolute x=2000 (position 0.6667 along [1000,2500])
      { id: "door-1", wall_id: "f0-wall-002", position: 2 / 3, width: 880 },
    ],
  };

  mergeCollinearWalls(floor);

  assert.equal(floor.walls.length, 1, "the two fragments should collapse into one wall");
  const [wall] = floor.walls;
  assert.equal(wall.id, "f0-wall-001", "the earlier wall id survives");
  assert.deepEqual(wall.start, [0, 0]);
  assert.deepEqual(wall.end, [2500, 0]);
  assert.equal(wall.length_mm, 2500);

  const [door] = floor.openings;
  assert.equal(door.wall_id, "f0-wall-001", "opening is re-homed onto the survivor");
  // absolute point was x=2000 on a wall now spanning 0..2500 -> ratio 0.8
  assert.equal(door.position, 0.8);
});

test("does not merge across a real gap between two collinear walls", () => {
  const floor = {
    walls: [
      { id: "w1", start: [0, 0], end: [1000, 0], thickness: 350, wall_type: "exterior", room_ids: ["a"], length_mm: 1000 },
      { id: "w2", start: [1200, 0], end: [2000, 0], thickness: 350, wall_type: "exterior", room_ids: ["a"], length_mm: 800 },
    ],
    openings: [],
  };
  mergeCollinearWalls(floor);
  assert.equal(floor.walls.length, 2, "a gap means these are not the same physical wall");
});

test("does not merge collinear walls with different thickness or room_ids", () => {
  const floor = {
    walls: [
      { id: "w1", start: [0, 0], end: [1000, 0], thickness: 350, wall_type: "exterior", room_ids: ["a"], length_mm: 1000 },
      { id: "w2", start: [1000, 0], end: [2000, 0], thickness: 100, wall_type: "partition", room_ids: ["a", "b"], length_mm: 1000 },
    ],
    openings: [],
  };
  mergeCollinearWalls(floor);
  assert.equal(floor.walls.length, 2, "different wall_type/thickness means these are genuinely different walls");
});

test("merges three contiguous fragments in one pass and re-homes openings on every fragment", () => {
  const floor = {
    walls: [
      { id: "w1", start: [0, 0], end: [500, 0], thickness: 100, wall_type: "partition", room_ids: ["x", "y"], length_mm: 500 },
      { id: "w2", start: [500, 0], end: [1000, 0], thickness: 100, wall_type: "partition", room_ids: ["x", "y"], length_mm: 500 },
      { id: "w3", start: [1000, 0], end: [1500, 0], thickness: 100, wall_type: "partition", room_ids: ["x", "y"], length_mm: 500 },
    ],
    openings: [
      { id: "d1", wall_id: "w1", position: 0.5 }, // absolute x=250 -> new ratio 250/1500
      { id: "d2", wall_id: "w3", position: 0.5 }, // absolute x=1250 -> new ratio 1250/1500
    ],
  };
  mergeCollinearWalls(floor);
  assert.equal(floor.walls.length, 1);
  assert.equal(floor.walls[0].length_mm, 1500);
  assert.equal(floor.openings[0].wall_id, "w1");
  assert.equal(Math.round(floor.openings[0].position * 1500), 250);
  assert.equal(floor.openings[1].wall_id, "w1");
  assert.equal(Math.round(floor.openings[1].position * 1500), 1250);
});

test("fixes an opening's connects order when the merged-away fragment recorded room_ids in the opposite order", () => {
  // Real-world case from onehalfstorey_014: f0-wall-023 had room_ids
  // [HWR, Diele] and f0-wall-024 had [Diele, HWR] — same pair, same physical
  // wall, but each polygon edge lists its own room first. The validator
  // compares opening.connects to wall.room_ids order-sensitively, so a naive
  // merge that just changes wall_id would trip opening_connections_mismatch.
  const floor = {
    walls: [
      { id: "w1", start: [0, 0], end: [1000, 0], thickness: 100, wall_type: "partition", room_ids: ["hwr", "diele"], length_mm: 1000 },
      { id: "w2", start: [1000, 0], end: [2000, 0], thickness: 100, wall_type: "partition", room_ids: ["diele", "hwr"], length_mm: 1000 },
    ],
    openings: [
      { id: "door-1", wall_id: "w2", position: 0.5, connects: ["diele", "hwr"] },
    ],
  };
  mergeCollinearWalls(floor);
  assert.equal(floor.walls.length, 1);
  assert.deepEqual(floor.openings[0].connects, floor.walls[0].room_ids, "connects must match the survivor's room_ids order exactly");
});

test("leaves a floor with no mergeable walls untouched", () => {
  const floor = {
    walls: [
      { id: "w1", start: [0, 0], end: [1000, 0], thickness: 350, wall_type: "exterior", room_ids: [], length_mm: 1000 },
      { id: "w2", start: [1000, 0], end: [1000, 1000], thickness: 350, wall_type: "exterior", room_ids: [], length_mm: 1000 },
    ],
    openings: [],
  };
  const before = structuredClone(floor);
  mergeCollinearWalls(floor);
  assert.deepEqual(floor, before, "perpendicular walls sharing an endpoint must never merge");
});
