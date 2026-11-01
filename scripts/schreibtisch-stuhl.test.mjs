// Rainer, 2026-10-13: "could you also include the desk chair whenever a desk
// is added? it is actually one set right?" -- wer einen Schreibtisch setzt,
// bekommt den Stuhl davor dazu, mit dem Gesicht zum Tisch und ein Stueck
// unter die Platte geschoben (dieselbe Rechnung wie "Bereich einrichten").
import assert from "node:assert/strict";
import test from "node:test";
import { deskChairFor } from "../src/lib/generator/furniture-document.mjs";

const tisch = (symbol, rotation_deg, position_mm = [1000, 1000]) => ({
  symbol, rotation_deg, position_mm,
  footprint_mm: symbol === "schreibtisch" ? { width_mm: 1600, depth_mm: 800 }
                                          : { width_mm: 1200, depth_mm: 600 },
});

test("vor dem Tisch, Gesicht zum Tisch", () => {
  // Lokal +y ist vorn. Ungedreht liegt vorn bei +y.
  const stuhl = deskChairFor(tisch("schreibtisch", 0));
  assert.equal(stuhl.symbol, "schreibtischstuhl");
  assert.equal(stuhl.rotation_deg, 180);
  // 800/2 + 610/2 - 150 = 555 vor der Tischmitte
  assert.deepEqual(stuhl.position_mm, [1000, 1555]);
  assert.deepEqual(stuhl.footprint_mm, { width_mm: 610, depth_mm: 610 });
});

test("gedrehter Tisch: der Stuhl dreht mit", () => {
  // 90 Grad: lokales +y faellt auf (-1, 0).
  const stuhl = deskChairFor(tisch("schreibtisch_kind", 90));
  assert.equal(stuhl.rotation_deg, 270);
  assert.deepEqual(stuhl.position_mm, [1000 - (300 + 305 - 150), 1000]);
});

test("nur Schreibtische bringen einen Stuhl mit", () => {
  assert.equal(deskChairFor(tisch("sideboard", 0)), null);
  assert.equal(deskChairFor({ symbol: "esstisch", rotation_deg: 0, position_mm: [0, 0] }), null);
});
