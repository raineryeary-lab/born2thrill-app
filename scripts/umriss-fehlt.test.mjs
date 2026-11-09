/** Haeuser ohne Aussenumriss rot (umriss-fehlt-rot-v1). Rainer, 2026-11-07. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { umrissFehlt } from "../src/lib/floorplan-workbench/hausdaten.mjs";

const Q = [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }];
const raum = (f) => ({ floor_level: f, points: Q });

test("kein Umriss", () => {
  assert.equal(umrissFehlt({ annotations: [raum("groundfloor")] }), "kein Außenumriss");
  assert.equal(umrissFehlt({ annotations: [raum("groundfloor")], outer_outlines: { groundfloor: [] } }), "kein Außenumriss");
});

test("Umriss je Geschoss oder alter Einzelumriss reicht", () => {
  assert.equal(umrissFehlt({ annotations: [raum("groundfloor"), raum("upperfloor")], outer_outlines: { groundfloor: Q } }), "");
  assert.equal(umrissFehlt({ annotations: [raum("groundfloor")], outer_outline: Q }), "");
});

test("Staffelgeschoss ohne eigenen Umriss wird genannt", () => {
  assert.equal(umrissFehlt({ annotations: [raum("groundfloor"), raum("staffelgeschoss")], outer_outlines: { groundfloor: Q } }),
               "Umriss fehlt: staffelgeschoss");
});

test("Umriss viel kleiner als die Raeume: zu klein (bungalow_040_17)", () => {
  const winzig = [{ x: 0.7, y: 0.5 }, { x: 0.701, y: 0.5 }, { x: 0.701, y: 0.508 }, { x: 0.7, y: 0.508 }];
  assert.match(umrissFehlt({ annotations: [raum("groundfloor")], outer_outlines: { groundfloor: winzig } }), /zu klein/);
  assert.equal(umrissFehlt({ annotations: [raum("groundfloor")], outer_outlines: { groundfloor: Q } }), "");
});

test("Naht: Route setzt umriss_fehlt, Seite zeigt es rot", () => {
  const route = readFileSync(new URL("../src/app/api/floorplan-workbench/state/route.ts", import.meta.url), "utf8");
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(route, /umriss_fehlt:\s*umrissFehlt\(/);
  assert.match(seite, /h\.umriss_fehlt/);
  assert.match(seite, /Außenumriss fehlt/);
});
