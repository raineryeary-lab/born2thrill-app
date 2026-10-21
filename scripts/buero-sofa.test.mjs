// Rainer, 2026-10-16: "if an office is above 10m2 then please add a 2-seater
// couch to the einrichtungsautomatic".
import assert from "node:assert/strict";
import test from "node:test";
import { richteBereichEin } from "../src/lib/generator/moebel-vorschlag.mjs";

const rechteck = (x0, y0, x1, y1) => [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];

test("Buero ueber 10 m2 bekommt einen 2-Sitzer", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 4000, 3600),
    oeffnungen: [{ a: [1000, 3600], b: [2500, 3600], typ: "window" },
                 { a: [0, 200], b: [0, 1100], typ: "door" }] }, "buero");
  assert.ok(e.moebel.some((m) => m.symbol === "sofa_2sitzer"),
            `${e.moebel.map((m) => m.symbol)} / ${e.weggelassen}`);
});

test("Buero bis 10 m2 bekommt keinen", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 3000, 3000),
    oeffnungen: [{ a: [800, 3000], b: [2200, 3000], typ: "window" }] }, "buero");
  assert.ok(!e.moebel.some((m) => m.symbol === "sofa_2sitzer"));
});
