/**
 * Kleine Zimmer gruen auf /haus, bis Rainer sie prueft (kleine-zimmer-v1).
 * Rainer, 2026-11-07: "yes but mark them as green and let me review them".
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { kleineZimmerAusCsv, zimmerPruefen } from "../src/lib/floorplan-workbench/hausdaten.mjs";

test("CSV: Spalte kleine_zimmer je Haus", () => {
  const csv = "plan;zimmer;kleine_zimmer\r\nbungalow_032;3.0;Büro 10,0 m²\r\nbungalow_035;4.0;\r\n";
  assert.deepEqual(kleineZimmerAusCsv(csv), { bungalow_032: "Büro 10,0 m²", bungalow_035: "" });
  assert.deepEqual(kleineZimmerAusCsv("plan;zimmer\nx;3\n"), {});
  // Feld mit Semikolon steht in Anfuehrungszeichen (bungalow_040_36, 2026-11-07)
  assert.deepEqual(kleineZimmerAusCsv('plan;kleine_zimmer;x\nb;"Büro 10,0 m²; Gast 8,1 m²";1\n'),
                   { b: "Büro 10,0 m²; Gast 8,1 m²" });
});

test("gruen bis geprueft; aendert sich die Liste, wieder gruen", () => {
  assert.equal(zimmerPruefen({ kleine: "Büro 8,5 m²", geprueft: "" }), "Büro 8,5 m²");
  assert.equal(zimmerPruefen({ kleine: "Büro 8,5 m²", geprueft: "Büro 8,5 m²" }), "");
  assert.equal(zimmerPruefen({ kleine: "Büro 8,5 m²; Gast 7,0 m²", geprueft: "Büro 8,5 m²" }), "Büro 8,5 m²; Gast 7,0 m²");
  assert.equal(zimmerPruefen({ kleine: "", geprueft: "" }), "");
});

test("Naht: Route, API und Seite", () => {
  const route = readFileSync(new URL("../src/app/api/floorplan-workbench/state/route.ts", import.meta.url), "utf8");
  assert.match(route, /zimmer_pruefen: zimmerPruefen\(/);
  assert.match(route, /zimmer-geprueft\.json/);
  const api = readFileSync(new URL("../src/app/api/floorplan-workbench/zimmer-geprueft/route.ts", import.meta.url), "utf8");
  assert.match(api, /Local-only endpoint/);
  assert.match(api, /zimmer-geprueft\.json/);
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /zimmer_pruefen/);
  assert.match(seite, /Zimmer geprüft/);
});
