// GLAS-SCHIEBETUER-001 (Rainer, 2026-10-18): "inner glass doors to the möbel
// tab ... right click 3 door 2 door 1 door".
import assert from "node:assert/strict";
import test from "node:test";
import { getSymbol, symbolsForRoomLabel } from "../src/lib/generator/symbol-catalog.mjs";
import { normalizeFurnitureSymbol } from "../src/lib/generator/furniture-document.mjs";

test("the glass closet is an area with an arrow, offered in Schlafen and Ankleide", () => {
  // "could we build it like an area with the arrow?" (Rainer, 2026-10-18)
  const s = getSymbol("glasschiebetuer");
  assert.ok(s);
  assert.equal(s.placement, "stamp");
  assert.ok(s.footprint_mm.width_mm >= 1000 && s.footprint_mm.depth_mm >= 600);
  assert.ok(symbolsForRoomLabel("Ankleide").some((x) => (x.key || x) === "glasschiebetuer"));
  assert.ok(symbolsForRoomLabel("Eltern / Schlafen").some((x) => (x.key || x) === "glasschiebetuer"));
});

test("the panel count survives saving", () => {
  const n = normalizeFurnitureSymbol({ symbol: "glasschiebetuer", position_mm: [1000, 1000], fluegel: 3 });
  assert.equal(n.fluegel, 3);
});

test("a nonsense panel count falls back to 2, and other symbols get none", () => {
  assert.equal(normalizeFurnitureSymbol({ symbol: "glasschiebetuer", position_mm: [1000, 1000], fluegel: 7 }).fluegel, 2);
  assert.equal(normalizeFurnitureSymbol({ symbol: "glasschiebetuer", position_mm: [1000, 1000] }).fluegel, 2);
  assert.equal(normalizeFurnitureSymbol({ symbol: "kuechenzeile", points_mm: [[0, 0], [2400, 0]], fluegel: 3 }).fluegel, undefined);
});
