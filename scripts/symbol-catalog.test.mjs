// Pins the ported Ausstattung catalogue against the annotator original.
// See plans/move-furniture-to-workbench.md, step 1.
//
// The point of these tests is not that the numbers are "right" in the
// abstract — they are measurements off Rainer's Möbel3svg.svg, calibrated on
// the Doppelbett — but that the port did not quietly change any of them. A
// footprint drifting by a few centimetres here moves real furniture in a real
// render, and would be invisible until someone looked at a picture.

import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  SYMBOL_CATALOG,
  SYMBOL_CATEGORIES,
  SYMBOL_SOURCE_GROUP,
  getSymbol,
  symbolsInCategory,
  symbolsForRoomLabel,
  bucketForRoomLabel,
} from "../src/lib/generator/symbol-catalog.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
// The annotator's copy is gone — furniture moved here. The verbatim copy taken
// during the move is the reference this test diffs against.
const ANNOTATOR_COPY = path.resolve(HERE, "../src/app/floorplan-workbench/legacy/symbol-catalog.js");

test("every symbol key from the annotator survived the port", () => {
  // Read the original as text and pull its keys out of the s(...) calls, so
  // this compares against the actual file rather than a list retyped by hand.
  const original = readFileSync(ANNOTATOR_COPY, "utf8");
  const keys = [...original.matchAll(/^\s*s\("([a-z0-9_]+)"/gm)].map((match) => match[1]);
  assert.ok(keys.length >= 40, `expected the full catalogue, parsed ${keys.length}`);
  assert.deepEqual(SYMBOL_CATALOG.map((item) => item.key).sort(), keys.sort());
});

test("measured footprints are unchanged", () => {
  // The three the annotator's own header calls out as calibration points.
  assert.deepEqual(getSymbol("doppelbett").footprint_mm, { width_mm: 1800, depth_mm: 2000 });
  assert.deepEqual(getSymbol("badewanne").footprint_mm, { width_mm: 1700, depth_mm: 750 });
  assert.equal(getSymbol("vorwandinstallation").depth_mm, 150);
  // And the desk, which was deliberately corrected away from the drawing.
  assert.deepEqual(getSymbol("schreibtisch").footprint_mm, { width_mm: 1600, depth_mm: 800 });
  assert.deepEqual(getSymbol("schreibtisch_kind").footprint_mm, { width_mm: 1200, depth_mm: 600 });
});

test("wall behaviour keeps its three modes", () => {
  assert.deepEqual(getSymbol("wand_wc").wall, { mode: "flush", gap_mm: 0 });
  assert.deepEqual(getSymbol("ecksofa").wall, { mode: "gap", gap_mm: 100 });
  assert.deepEqual(getSymbol("doppelbett").wall, { mode: "gap", gap_mm: 50 });
  assert.deepEqual(getSymbol("kochfeld").wall, { mode: "free", gap_mm: 0 },
    "a hob sits in the worktop, it is never pulled against the plaster");
});

test("placement kinds survive: stamp, path and rect are all still represented", () => {
  assert.equal(getSymbol("doppelbett").placement, "stamp");
  assert.equal(getSymbol("kuechenzeile").placement, "path");
  assert.equal(getSymbol("kuecheninsel").placement, "rect");
  assert.equal(getSymbol("kuechenzeile").footprint_mm, null,
    "a path symbol has no fixed footprint — it is drawn along the wall");
});

test("vertical placement survives", () => {
  assert.equal(getSymbol("waschtisch").height, "wall");
  assert.equal(getSymbol("waschtisch").mount_height_mm, 850);
  assert.equal(getSymbol("kochfeld").height, "surface");
  assert.equal(getSymbol("fernseher").mount_height_mm, 1100);
});

test("Elternbad is a wet room, not a bedroom", () => {
  // The ordering bug the annotator's comment records: sorting the buckets by
  // length puts "eltern" before "bad" and offers wardrobes in a bathroom.
  assert.equal(bucketForRoomLabel("Elternbad"), "bad");
  assert.equal(bucketForRoomLabel("Eltern / Schlafen"), "schlafen");
  assert.equal(bucketForRoomLabel("Gäste-WC"), "wc");
  assert.equal(bucketForRoomLabel("HWR / HTR"), "hwr");
  assert.equal(bucketForRoomLabel("Wohnen / Essen / Kochen"), "kueche",
    "a combined room matches the first clue in declared order");
});

test("room filtering returns the plausible symbols, and null for an unknown room", () => {
  assert.ok(symbolsForRoomLabel("Bad").includes("badewanne"));
  assert.ok(symbolsForRoomLabel("Büro").includes("schreibtisch"));
  assert.equal(symbolsForRoomLabel("Luftraum"), null);
});

test("categories and drawing groups came across", () => {
  assert.deepEqual(SYMBOL_CATEGORIES.map((c) => c.key),
    ["sanitaer", "kueche", "wohnen", "schlafen", "essen"]);
  assert.ok(symbolsInCategory("kueche").length >= 6);
  // The group ids are the handles into Rainer's own linework.
  assert.equal(SYMBOL_SOURCE_GROUP.doppelbett, "Doppelbett");
  assert.equal(SYMBOL_SOURCE_GROUP.ecksofa, "L-couch");
});

test("the keys bungalow_040_66 actually uses all resolve", () => {
  // The only project with hand-placed furniture; every key it holds must
  // still exist or its render silently loses items.
  const used = ["doppelbett", "essgruppe_6", "ecksofa", "sofa_2sitzer", "sofa_1sitzer",
    "schreibtisch", "hochschrank_herd", "spuele", "kuechenzeile", "kuecheninsel",
    "kochfeld", "waschmaschine", "trockner", "waschtisch", "eckbadewanne", "dusche",
    "badheizkoerper", "couchtisch", "lowboard", "fernseher", "handwaschbecken",
    "garderobe", "dusche_klein", "schrank_60", "schrank_40", "vorwandinstallation",
    "wand_wc", "kleiderschrank"];
  for (const key of used) {
    assert.ok(getSymbol(key), `catalogue lost ${key}`);
  }
});

test("Stuff ist ein aufziehbares Rechteck und steht in jedem Raum", () => {
  // Rainer, 2026-08-25: "i need a new symbol type for furnishing, this one is
  // called stuff" -- freies Rechteck, in allen Raeumen waehlbar.
  const stuff = getSymbol("stuff");
  assert.ok(stuff, "Katalog kennt stuff nicht");
  assert.equal(stuff.placement, "rect");
  assert.equal(stuff.label, "Stuff");
  const raeume = ["Bad", "Gäste-WC", "Küche", "Wohnen / Essen / Kochen",
                  "Eltern / Schlafen", "Kind", "Diele", "HWR / HTR", "Büro"];
  for (const raum of raeume) {
    const keys = symbolsForRoomLabel(raum);
    assert.ok(keys, `kein Symbolsatz für ${raum}`);
    assert.ok(keys.includes("stuff"), `${raum} bietet stuff nicht an`);
  }
});

test("jedes Symbol steckt in einer Kategorie, die die Palette auch zeichnet", () => {
  // Die Palette rendert nur SYMBOL_CATEGORIES (furniture.tsx). Ein Symbol mit
  // einer Kategorie, die dort fehlt, ist unsichtbar -- genau das passierte
  // "stuff" beim ersten Versuch (2026-08-25).
  const bekannt = new Set(SYMBOL_CATEGORIES.map((c) => c.key));
  for (const item of SYMBOL_CATALOG) {
    assert.ok(bekannt.has(item.category),
      `${item.key} hat Kategorie "${item.category}", die die Palette nicht zeichnet`);
  }
});

test("Esstisch und Esszimmerstuhl sind einzeln setzbar", () => {
  // Rainer, 2026-08-25: "a dining table without chairs plus a dining room
  // chair". Vorher gab es nur essgruppe_6 als Block.
  const tisch = getSymbol("esstisch");
  const stuhl = getSymbol("esszimmerstuhl");
  assert.ok(tisch && stuhl, "Katalog kennt die neuen Schlüssel nicht");
  assert.equal(tisch.placement, "stamp");
  assert.equal(stuhl.placement, "stamp");
  assert.deepEqual(tisch.footprint_mm, { width_mm: 1600, depth_mm: 900 });
  assert.deepEqual(stuhl.footprint_mm, { width_mm: 560, depth_mm: 590 });
  const keys = symbolsForRoomLabel("Wohnen / Essen / Kochen");
  assert.ok(keys.includes("esstisch"), "Esstisch fehlt im Essbereich");
  assert.ok(keys.includes("esszimmerstuhl"), "Stuhl fehlt im Essbereich");
  // Die Essgruppe bleibt, wie sie war.
  assert.equal(getSymbol("essgruppe_6").assembly, true);
  assert.deepEqual(getSymbol("essgruppe_6").footprint_mm,
                   { width_mm: 1710, depth_mm: 1600 });
});

test("Kinderzimmer hat seinen eigenen Satz", () => {
  // Rainer, 2026-10-11: "kids room need to have einzelbett schrank
  // kinderschreibtisch schreibtischstuhl playstationgruppe".
  for (const raum of ["Kind", "Kinderzimmer", "Kind 2"]) {
    assert.equal(bucketForRoomLabel(raum), "kind", raum);
    const keys = symbolsForRoomLabel(raum);
    for (const key of ["einzelbett", "kleiderschrank", "schreibtisch_kind",
                       "schreibtischstuhl", "playstation_gruppe", "stuff"]) {
      assert.ok(keys.includes(key), `${raum} bietet ${key} nicht an`);
    }
    assert.ok(!keys.includes("doppelbett"), `${raum} bietet ein Doppelbett an`);
  }
  assert.equal(bucketForRoomLabel("Kinderbad"), "bad");
  assert.ok(!symbolsForRoomLabel("Eltern / Schlafen").includes("playstation_gruppe"));
});

test("Gästezimmer hat seinen eigenen Satz", () => {
  // Rainer, 2026-10-11: "gast need 2 seater couch small desk desk chair
  // einzelbett stuff".
  for (const raum of ["Gast", "Gästezimmer", "Gaestezimmer"]) {
    assert.equal(bucketForRoomLabel(raum), "gast", raum);
    const keys = symbolsForRoomLabel(raum);
    for (const key of ["sofa_2sitzer", "schreibtisch_kind", "schreibtischstuhl",
                       "einzelbett", "stuff"]) {
      assert.ok(keys.includes(key), `${raum} bietet ${key} nicht an`);
    }
    assert.ok(!keys.includes("doppelbett"), `${raum} bietet ein Doppelbett an`);
  }
  assert.equal(bucketForRoomLabel("Gäste-WC"), "wc");
  assert.equal(bucketForRoomLabel("Gästebad"), "bad");
});

// sauna-fitness-hobby-v1 (Rainer, 2026-10-23: Sauna als "cabin in the room").
test("Saunakabine: Rechteck-Moebel zum Aufziehen, 2,10 m hoch, Sanitaer", async () => {
  const { getSymbol } = await import("../src/lib/generator/symbol-catalog.mjs");
  const k = getSymbol("saunakabine");
  assert.ok(k, "saunakabine fehlt");
  assert.equal(k.placement, "rect");
  assert.equal(k.height_mm, 2100);
  assert.equal(k.category, "sanitaer");
});

test("Sauna-, Fitness- und Hobbyraum bekommen ihre Moebel und immer Stuff", async () => {
  const { symbolsForRoomLabel } = await import("../src/lib/generator/symbol-catalog.mjs");
  const sauna = symbolsForRoomLabel("Sauna / Wellness");
  assert.ok(sauna.includes("saunakabine") && sauna.includes("stuff"), JSON.stringify(sauna));
  assert.ok(symbolsForRoomLabel("Fitness").includes("stuff"));
  const hobby = symbolsForRoomLabel("Hobbyraum");
  assert.ok(hobby.includes("schreibtisch") && hobby.includes("stuff"), JSON.stringify(hobby));
});
