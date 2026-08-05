import assert from "node:assert/strict";
import test from "node:test";
import { FLOORPLAN_RULES, isHabitableRoom, normalizedRoomRuleKey } from "../src/lib/generator/floorplan-rulebook.mjs";

test("HWR/HTR area range allows a generously sized utility room, not just a narrow 9-10 sqm band", () => {
  // Utility/laundry rooms also serve as storage; a single square metre of
  // slack either side was unrealistically tight. Widened per explicit user
  // direction: "round about 8 to 18 qm".
  assert.equal(FLOORPLAN_RULES.rooms.hwrHtr.minimumM2, 8);
  assert.equal(FLOORPLAN_RULES.rooms.hwrHtr.maximumM2, 18);
  assert.equal(normalizedRoomRuleKey({ name: "HWR / HTR", kind: "service" }), "hwrHtr");
});

test("normalizedRoomRuleKey recognizes dressing rooms by name regardless of kind", () => {
  assert.equal(normalizedRoomRuleKey({ name: "Ankleide", kind: "flex" }), "dressing");
  assert.equal(normalizedRoomRuleKey({ name: "Dressing", kind: "flex" }), "dressing");
  assert.equal(normalizedRoomRuleKey({ name: "Büro / Gast", kind: "flex" }), null);
});

test("isHabitableRoom no longer requires a window for a dressing room", () => {
  assert.equal(isHabitableRoom({ name: "Ankleide", kind: "flex" }), false);
});

test("normalizedRoomRuleKey treats a children's bathroom as a bathroom, not a 10 sqm child bedroom", () => {
  assert.equal(normalizedRoomRuleKey({ name: "Kinderbad", kind: "wet" }), "showerBathroom");
  assert.equal(normalizedRoomRuleKey({ name: "Kinderzimmer", kind: "sleeping" }), "child");
});

test("isHabitableRoom no longer requires a window for a garage or carport", () => {
  assert.equal(isHabitableRoom({ name: "Garage / Carport", kind: "flex" }), false);
  assert.equal(normalizedRoomRuleKey({ name: "Garage / Carport", kind: "flex" }), "garage");
});

test("isHabitableRoom still requires a window for other flex, living, and sleeping rooms", () => {
  assert.equal(isHabitableRoom({ name: "Büro / Gast", kind: "flex" }), true);
  assert.equal(isHabitableRoom({ name: "Wohnen / Essen / Kochen", kind: "living" }), true);
  assert.equal(isHabitableRoom({ name: "Eltern / Schlafen", kind: "sleeping" }), true);
});

test("isHabitableRoom is unaffected for non-habitable kinds", () => {
  assert.equal(isHabitableRoom({ name: "Bad", kind: "wet" }), false);
  assert.equal(isHabitableRoom({ name: "HWR / HTR", kind: "service" }), false);
  assert.equal(isHabitableRoom({ name: "Diele", kind: "circulation" }), false);
});
