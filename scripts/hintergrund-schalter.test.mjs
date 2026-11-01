/**
 * Hintergrund ein/aus im Moebel-Tab (HINTERGRUND-SCHALTER-001).
 * Naht-Test: page.tsx ist React ohne Testrenderer, geprueft wird die Verdrahtung.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../src/app/floorplan-workbench/page.tsx", import.meta.url), "utf8");

test("der Knopf steuert den Zustand und reicht ihn an den Editor", () => {
  assert.match(page, /const \[hintergrundAn, setHintergrundAn\] = useState\(true\)/);
  assert.match(page, /onClick=\{\(\) => setHintergrundAn\(\(an\) => !an\)\}/);
  assert.match(page, /zeigeHintergrund=\{hintergrundAn\}/);
});

test("ausgeblendet: kein Bild, und die Raeume multiplizieren nicht mehr", () => {
  assert.match(page, /const bildAn = zeigeReferenz && zeigeHintergrund/);
  assert.match(page, /\{bildAn && \(\(\) => \{/);
  assert.match(page, /style=\{bildAn \? \{ mixBlendMode: "multiply" \} : undefined\}/);
});

test("der Sichtbereich haengt nicht am Knopf: der Plan springt nicht", () => {
  const kasten = page.slice(page.indexOf("const ecken = (floor as any)?.imageCorners"),
                            page.indexOf("const sichtbar = sichtKasten"));
  assert.ok(kasten.length > 0);
  assert.ok(!kasten.includes("zeigeHintergrund"));
});
