/**
 * Unsichere Haustypen gruen (haustyp-pruefen-gruen-v1). Rainer, 2026-11-07:
 * "if there are stairs its not a bungalow you can also make everybody green
 * where you are unsure and i will reclassify them".
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { haustypPruefen } from "../src/lib/floorplan-workbench/hausdaten.mjs";

const Q = [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }];
const raum = (f) => ({ floor_level: f, points: Q });
const treppe = { type: "stairs", floor_level: "groundfloor", points: [Q[0], Q[1]] };
const haus = (ebenen, elemente = []) => ({ annotations: ebenen.map(raum), elements: elemente });

test("passt: Bungalow nur EG, Zweigeschosser mit OG und Treppe", () => {
  assert.equal(haustypPruefen({ plan: "bungalow_001", house_type: "bungalow", annotation: haus(["groundfloor"]) }), "");
  assert.equal(haustypPruefen({ plan: "twostorey_001", house_type: "2-storey",
    annotation: haus(["groundfloor", "upperfloor"], [treppe]) }), "");
  assert.equal(haustypPruefen({ plan: "onehalfstorey_001", house_type: "1.5-storey",
    annotation: haus(["groundfloor", "upperfloor"], [treppe]) }), "");
});

test("Bungalow mit Treppe oder zweitem Geschoss", () => {
  assert.match(haustypPruefen({ plan: "bungalow_034", house_type: "bungalow",
    annotation: haus(["groundfloor", "upperfloor"]) }), /Bungalow/);
  assert.match(haustypPruefen({ plan: "bungalow_009", house_type: "bungalow",
    annotation: haus(["groundfloor"], [treppe]) }), /Treppe/);
});

test("Mehrgeschosser mit nur einem Geschoss", () => {
  assert.match(haustypPruefen({ plan: "twostorey_099", house_type: "2-storey",
    annotation: haus(["groundfloor"]) }), /nur ein Geschoss/);
});

test("nicht gesetzt; der Dateiname allein macht nichts gruen", () => {
  assert.match(haustypPruefen({ plan: "bungalow_010", house_type: null, annotation: haus(["groundfloor"]) }), /nicht gesetzt/);
  // bungalow_040_185 ist als Zweigeschosser gespeichert und so gezeichnet:
  // bliebe sonst nach Rainers Bestaetigung fuer immer gruen.
  assert.equal(haustypPruefen({ plan: "bungalow_040_185", house_type: "2-storey",
    annotation: haus(["groundfloor", "upperfloor"], [treppe]) }), "");
});

test("Naht: Route setzt haustyp_pruefen, Seite zeigt es gruen", () => {
  const route = readFileSync(new URL("../src/app/api/floorplan-workbench/state/route.ts", import.meta.url), "utf8");
  assert.match(route, /haustyp_pruefen: haustypPruefen\(/);
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /haustyp_pruefen/);
  assert.match(seite, /\.eintrag\.haustyp \{/);
});
