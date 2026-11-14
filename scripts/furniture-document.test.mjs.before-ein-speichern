import assert from "node:assert/strict";
import test from "node:test";
import {
  emptyFurnitureDocument,
  normalizeFurnitureDocument,
  normalizeFurnitureSymbol,
  symbolBoundsMm,
  symbolAtPointMm,
  worldDeltaToLocalMm,
} from "../src/lib/generator/furniture-document.mjs";

test("a stamp keeps its catalogue footprint unless the drawing says otherwise", () => {
  const bed = normalizeFurnitureSymbol({ symbol: "doppelbett", position_mm: [1000, 2000] });
  assert.deepEqual(bed.footprint_mm, { width_mm: 1800, depth_mm: 2000 });
  const measured = normalizeFurnitureSymbol({
    symbol: "doppelbett", position_mm: [0, 0],
    footprint_mm: { width_mm: 2070, depth_mm: 2228 },
  });
  assert.deepEqual(measured.footprint_mm, { width_mm: 2070, depth_mm: 2228 },
    "a measurement off the plan beats the nominal size");
});

test("an unknown symbol key is refused, not stored", () => {
  assert.throws(() => normalizeFurnitureSymbol({ symbol: "chaiselongue", position_mm: [0, 0] }),
    /Unknown furniture symbol/);
  assert.throws(() => normalizeFurnitureSymbol({ position_mm: [0, 0] }), /Unknown furniture symbol/);
});

test("rotation normalises to 0-359 whatever the editor sends", () => {
  const at = (deg) => normalizeFurnitureSymbol({ symbol: "doppelbett", position_mm: [0, 0], rotation_deg: deg }).rotation_deg;
  assert.equal(at(-90), 270);
  assert.equal(at(450), 90);
  assert.equal(at(0), 0);
  assert.equal(at(undefined), 0);
});

test("path and rect symbols carry drawn geometry, not a point", () => {
  const run = normalizeFurnitureSymbol({ symbol: "kuechenzeile", points_mm: [[0, 0], [3000, 0], [3000, 2000]] });
  assert.equal(run.points_mm.length, 3);
  assert.equal(run.depth_mm, 600, "a Küchenzeile is 600 deep by catalogue");
  assert.equal(run.position_mm, undefined);
  assert.throws(() => normalizeFurnitureSymbol({ symbol: "kuechenzeile", points_mm: [[0, 0]] }),
    /at least two points_mm/);
});

test("a stamp without a position is refused", () => {
  assert.throws(() => normalizeFurnitureSymbol({ symbol: "doppelbett" }), /needs a position_mm/);
});

test("duplicate ids are made unique so 'move that one' stays unambiguous", () => {
  const doc = normalizeFurnitureDocument({
    project_id: "onehalfstorey_020", floor_id: "groundfloor",
    symbols: [
      { id: "same", symbol: "schrank_60", position_mm: [0, 0] },
      { id: "same", symbol: "schrank_60", position_mm: [1000, 0] },
    ],
  });
  assert.equal(new Set(doc.symbols.map((s) => s.id)).size, 2);
});

test("bounds grow when a piece is rotated off-axis", () => {
  const straight = symbolBoundsMm({ symbol: "doppelbett", position_mm: [0, 0], rotation_deg: 0,
    footprint_mm: { width_mm: 1800, depth_mm: 2000 } });
  assert.equal(Math.round(straight.width), 1800);
  assert.equal(Math.round(straight.height), 2000);

  const turned = symbolBoundsMm({ symbol: "doppelbett", position_mm: [0, 0], rotation_deg: 90,
    footprint_mm: { width_mm: 1800, depth_mm: 2000 } });
  assert.equal(Math.round(turned.width), 2000);
  assert.equal(Math.round(turned.height), 1800);

  const diagonal = symbolBoundsMm({ symbol: "doppelbett", position_mm: [0, 0], rotation_deg: 45,
    footprint_mm: { width_mm: 1800, depth_mm: 2000 } });
  assert.ok(diagonal.width > 2600 && diagonal.width < 2700, diagonal.width);
});

test("worldDeltaToLocalMm passes the delta through unchanged at 0 degrees", () => {
  const local = worldDeltaToLocalMm(120, -40, 0);
  assert.equal(Math.round(local.x), 120);
  assert.equal(Math.round(local.y), -40);
});

test("worldDeltaToLocalMm swaps the axes at 90 degrees -- the resize bug's exact case", () => {
  // Rainer, 2026-08-22: "when i try to scale the furniture i feel as if the
  // x and y are mixed up" -- a piece rotated to 90 (routine: snapStampToWalls
  // rotates to match the wall it snaps to) had a pure-X world drag read as a
  // depth change and a pure-Y drag read as a width change.
  const fromX = worldDeltaToLocalMm(100, 0, 90);
  assert.equal(Math.round(fromX.x), 0);
  assert.equal(Math.round(fromX.y), -100);

  const fromY = worldDeltaToLocalMm(0, 100, 90);
  assert.equal(Math.round(fromY.x), 100);
  assert.equal(Math.round(fromY.y), 0);
});

test("worldDeltaToLocalMm at 45 degrees matches the hand-computed rotation", () => {
  const local = worldDeltaToLocalMm(100, 0, 45);
  const expected = 100 / Math.SQRT2;
  assert.ok(Math.abs(local.x - expected) < 0.001, local.x);
  assert.ok(Math.abs(local.y + expected) < 0.001, local.y);
});

test("hit-testing picks the item you clicked, topmost first", () => {
  const doc = normalizeFurnitureDocument({
    project_id: "p", floor_id: "groundfloor",
    symbols: [
      { id: "rug", symbol: "ecksofa", position_mm: [2000, 2000] },
      { id: "table", symbol: "couchtisch", position_mm: [2000, 2000] },
    ],
  });
  assert.equal(symbolAtPointMm(doc, [2000, 2000]).id, "table",
    "the small item on top is the one you grab");
  assert.equal(symbolAtPointMm(doc, [9000, 9000]), null);
});

test("an empty document is a valid document", () => {
  const doc = normalizeFurnitureDocument(emptyFurnitureDocument("onehalfstorey_020", "groundfloor"));
  assert.equal(doc.schema, "workbench-furniture-v1");
  assert.equal(doc.project_id, "onehalfstorey_020");
  assert.equal(doc.floor_id, "groundfloor");
  assert.deepEqual(doc.symbols, []);
});

// Codex review, 2026-09-18, after twostorey_047's furniture was found
// reflected into the wrong room: normalizeFurnitureDocument() used to
// overwrite ANY incoming coordinate_space with the current one unconditionally.
// A file still carrying the legacy render space (never migrated) would come
// out of a save looking like modern, correctly-placed data without a single
// coordinate having actually moved.
test("saving a document still in the legacy render space is refused, not relabelled", () => {
  const legacy = {
    coordinate_space: "simplifier-render-plan-mm-v1",
    symbols: [{ symbol: "doppelbett", position_mm: [1000, 2000] }],
  };
  assert.throws(() => normalizeFurnitureDocument(legacy, { projectId: "twostorey_047" }),
    /simplifier-render-plan-mm-v1.*moebel-migrieren\.py twostorey_047/s);
});

test("saving a document already in today's render space still works", () => {
  const current = {
    coordinate_space: "render-geometry-mm-y-down-v1",
    symbols: [{ symbol: "doppelbett", position_mm: [1000, 2000] }],
  };
  const doc = normalizeFurnitureDocument(current, { projectId: "twostorey_047" });
  assert.equal(doc.coordinate_space, "render-geometry-mm-y-down-v1");
  assert.equal(doc.symbols.length, 1);
});

test("a brand new document with no coordinate_space yet is still accepted", () => {
  const doc = normalizeFurnitureDocument({ symbols: [] }, { projectId: "twostorey_047" });
  assert.equal(doc.coordinate_space, "render-geometry-mm-y-down-v1");
});

// moebel-speichern-bei-neuen-raeumen-v1 (Rainer, 2026-10-22, onehalfstorey_vv1):
// Speichern war grau, obwohl der Bau die Moebel wegen umgezeichneter Raeume ablehnte.
test("moebelVeraltet: alter Raumstempel -> speichern noetig", async () => {
  const { moebelVeraltet } = await import("../src/lib/generator/furniture-document.mjs");
  const doc = { geometry_identity: "59b6bc038df4", symbols: [{ key: "bed" }] };
  assert.equal(moebelVeraltet(doc, "5c295aa91b8a"), true);
  assert.equal(moebelVeraltet(doc, "59b6bc038df4"), false);
  assert.equal(moebelVeraltet({ ...doc, symbols: [] }, "5c295aa91b8a"), false);
  assert.equal(moebelVeraltet({ symbols: [{ key: "bed" }] }, "5c295aa91b8a"), false);
  assert.equal(moebelVeraltet(doc, undefined), false);
});

test("die Naht: der Moebel-Editor benutzt moebelVeraltet", async () => {
  const { readFileSync } = await import("node:fs");
  const quelle = readFileSync(new URL("../src/app/floorplan-workbench/furniture.tsx", import.meta.url), "utf8");
  assert.match(quelle, /moebelVeraltet\(/);
});
