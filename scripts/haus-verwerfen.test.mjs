/**
 * Schlechte Grundrisse verwerfen (haus-verwerfen-v1).
 * Rainer, 2026-11-06: "floorplans that are just shitty so I can delete them".
 * Verschieben nach projects/_verworfen, nie loeschen.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, readdir, readFile } from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { planNameOk, hausVerwerfen } from "../src/lib/floorplan-workbench/haus-verwerfen.mjs";

async function projekte(...plaene) {
  const dir = await mkdtemp(join(tmpdir(), "verwerfen-"));
  for (const p of plaene) {
    await mkdir(join(dir, p));
    await writeFile(join(dir, p, "data.json"), "{}");
  }
  return dir;
}

test("unsaubere Plannamen werden abgelehnt", () => {
  for (const n of ["", "..", "../x", "a/b", "a\b", "_verworfen", "_backup", "x:y"]) {
    assert.equal(planNameOk(n), false, n);
  }
  assert.equal(planNameOk("bungalow_012"), true);
});

test("verschiebt den Ordner, loescht nichts", async () => {
  const dir = await projekte("bungalow_x");
  const r = await hausVerwerfen({ projects: dir, plan: "bungalow_x" });
  assert.equal(r.ok, true);
  assert.equal(existsSync(join(dir, "bungalow_x")), false);
  assert.equal(await readFile(join(dir, "_verworfen", "bungalow_x", "data.json"), "utf8"), "{}");
});

test("zweites Verwerfen desselben Namens bekommt einen freien Namen", async () => {
  const dir = await projekte("bungalow_x");
  await hausVerwerfen({ projects: dir, plan: "bungalow_x" });
  await mkdir(join(dir, "bungalow_x"));
  const r = await hausVerwerfen({ projects: dir, plan: "bungalow_x" });
  assert.equal(r.ok, true);
  assert.deepEqual((await readdir(join(dir, "_verworfen"))).sort(), ["bungalow_x", "bungalow_x-1"]);
});

test("veroeffentlicht oder im Bau: abgelehnt, nichts bewegt", async () => {
  const dir = await projekte("bungalow_x");
  const a = await hausVerwerfen({ projects: dir, plan: "bungalow_x", veroeffentlicht: true });
  const b = await hausVerwerfen({ projects: dir, plan: "bungalow_x", imBau: true });
  assert.equal(a.ok, false); assert.match(a.fehler, /Katalog/);
  assert.equal(b.ok, false); assert.match(b.fehler, /Bau/);
  assert.equal(existsSync(join(dir, "bungalow_x")), true);
});

test("fehlender Plan: abgelehnt", async () => {
  const dir = await projekte();
  const r = await hausVerwerfen({ projects: dir, plan: "gibtsnicht" });
  assert.equal(r.ok, false);
});

test("Naht: Seite ruft die Route, Liste ueberspringt _-Ordner", () => {
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  const route = readFileSync(new URL("../src/app/api/floorplan-workbench/state/route.ts", import.meta.url), "utf8");
  assert.match(seite, /\/api\/floorplan-workbench\/haus-verwerfen/);
  assert.match(seite, /Grundriss verwerfen/);
  assert.match(route, /startsWith\("_"\)/);
  assert.ok(existsSync(new URL("../src/app/api/floorplan-workbench/haus-verwerfen/route.ts", import.meta.url)));
});
