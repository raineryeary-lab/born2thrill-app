/** /haus zeigt den Anzeigenamen neben der ID (anzeigename-v1). Rainer, 2026-11-07. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("Naht: Route liest anzeigename.json, Seite zeigt ihn", () => {
  const route = readFileSync(new URL("../src/app/api/floorplan-workbench/state/route.ts", import.meta.url), "utf8");
  assert.match(route, /anzeigename\.json/);
  assert.match(route, /anzeigename:/);
  const seite = readFileSync(new URL("../src/app/haus/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /anzeigename\?: string/);
  assert.match(seite, /h\.anzeigename/);
  assert.match(seite, /aktuell\?\.anzeigename/);
});
