/**
 * Bilder-Tab ordnen (bilder-tab-aufraeumen-v1).
 *
 * Rainer, 2026-10-22, onehalfstorey_045: "most of them i cant even select to
 * delete and most of them i cant select to show to customer and i cant even
 * look at any of them because they are being cropped so badly". Die 10
 * Codex-Bilder standen doppelt da: einmal lokal ohne Knoepfe, einmal online.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { bilderOrdnen } from "../src/lib/floorplan-workbench/bilder-ordnen.mjs";

const online = [
  { id: 2, name: "02-exterior-satteldach-kubus", url: "o2" },
  { id: 1, name: "01-exterior-satteldach", url: "o1" },
];
const lokal = [
  { name: "01-exterior-satteldach", url: "l1", stufe: "final" },
  { name: "02-exterior-satteldach-kubus", url: "l2", stufe: "final" },
  { name: "03-floorplan-warm-modern-eg", url: "l3", stufe: "final" },
  { name: "exterior-satteldach-baseline", url: "r1", stufe: "rohbau" },
];

test("online zuerst, in Namensfolge", () => {
  const { online: o } = bilderOrdnen(online, lokal);
  assert.deepEqual(o.map((b) => b.name), ["01-exterior-satteldach", "02-exterior-satteldach-kubus"]);
});

test("ein lokales Bild, das schon online ist, kommt nicht doppelt", () => {
  const { nichtHochgeladen } = bilderOrdnen(online, lokal);
  assert.deepEqual(nichtHochgeladen.map((b) => b.name), ["03-floorplan-warm-modern-eg"]);
});

test("Rohbau zuletzt und getrennt", () => {
  const { rohbau } = bilderOrdnen(online, lokal);
  assert.deepEqual(rohbau.map((b) => b.name), ["exterior-satteldach-baseline"]);
});

test("leere Eingaben", () => {
  assert.deepEqual(bilderOrdnen(null, undefined), { online: [], nichtHochgeladen: [], rohbau: [] });
});

test("die Naht: die Seite benutzt es und schneidet nichts ab", () => {
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /bilderOrdnen\(/);
  assert.match(seite, /grid-auto-rows:\s*max-content/);
  assert.match(seite, /target="_blank"/);
});
