/**
 * Hausliste: Haeuser ohne Gebaeudemasse leuchtend rot (masse-fehlen-rot-v1).
 *
 * Rainer, 2026-11-05: "can you make the ones that need the 2 numbers bright red".
 * Ohne Vorlagebild und ohne Seitenverhaeltnis lassen sich Flaeche, Zimmer und
 * Preis nicht rechnen -- "Gebaeudemasse eingeben" (Breite + Tiefe) behebt es.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { masseFehlen } from "../src/lib/floorplan-workbench/hausdaten.mjs";

test("kein Vorlagebild, kein Seitenverhaeltnis -> fehlt", () => {
  assert.equal(masseFehlen({ dateien: ["annotations.json", "room_concept.png"], annotation_space: null }), true);
});

test("Vorlagebild vorhanden -> fehlt nicht", () => {
  assert.equal(masseFehlen({ dateien: ["groundfloor_original_preview.png"], annotation_space: null }), false);
  assert.equal(masseFehlen({ dateien: ["original_preview.png"], annotation_space: {} }), false);
});

test("Seitenverhaeltnis vorhanden -> fehlt nicht", () => {
  assert.equal(masseFehlen({ dateien: [], annotation_space: { aspect: 0.82 } }), false);
});

test("unsinniges Seitenverhaeltnis zaehlt nicht", () => {
  assert.equal(masseFehlen({ dateien: [], annotation_space: { aspect: 0 } }), true);
  assert.equal(masseFehlen({ dateien: [], annotation_space: { aspect: "x" } }), true);
});

test("Naht: Route setzt masse_fehlen, Liste zeigt es", () => {
  const route = readFileSync(new URL("../src/app/api/floorplan-workbench/state/route.ts", import.meta.url), "utf8");
  assert.match(route, /masse_fehlen:\s*masseFehlen\(/);
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /h\.masse_fehlen/);
  assert.match(seite, /2 Maße fehlen/);
});

test("Naht: nach dem Speichern der Zeichnung wird die Liste neu geladen", () => {
  // Rainer, 2026-11-05 (onehalfstorey_029): "i put in both measurements and it is still red".
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /resolve\(ok\);\s*\n\s*\/\/ masse-fehlen-rot-v1[^\n]*\n\s*if \(ok\) laden\(\);/);
  assert.match(seite, /typ === "projekt-fertig"[^]*?laden\(\);/);
});
