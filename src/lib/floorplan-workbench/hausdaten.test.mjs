/**
 * Eine Wahrheit fuer Dachform und Massstab -- die vier Faelle aus dem Plan,
 * hier fuer die JS-Seite (plans/hausdaten-eine-wahrheit-v1.md).
 *
 * Dieselbe Vorrangregel wie in scripts/hausdaten.py und dieselben Feldnamen:
 * pro Feld gewinnt annotations.json; ist es dort leer, zaehlt
 * gebaeudemass.json. Massgeblich ist das Verhalten des Bauens.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { hausdaten } from "./hausdaten.mjs";
import { deriveHouseState } from "./house-state.mjs";

const ANNOTATION = {
  schema_version: "simplifier-annotations-v1",
  annotations: [{ id: "r1", floor_level: "groundfloor", label: "Wohnen" }],
  elements: [],
  roof_type_modern: null,
  roof_type_classic: null,
  floor_scale: {},
};

const wegwerf = [];
// Unsichtbares Zeichen, deshalb als Code geschrieben und nicht als Literal.
const BOM = String.fromCharCode(0xfeff);

async function projekt(annotation, sidecar) {
  const wurzel = await mkdtemp(join(tmpdir(), "hausdaten-"));
  wegwerf.push(wurzel);
  const ordner = join(wurzel, "testhaus");
  await mkdir(ordner);
  await writeFile(join(ordner, "annotations.json"),
    JSON.stringify({ ...ANNOTATION, ...(annotation || {}) }), "utf8");
  if (sidecar) {
    await writeFile(join(ordner, "gebaeudemass.json"),
      JSON.stringify({ schema: "zf-gebaeudemass-v1", plan_id: "testhaus", ...sidecar }),
      "utf8");
  }
  return ordner;
}

test.after(async () => {
  for (const ordner of wegwerf) await rm(ordner, { recursive: true, force: true });
});

test("1 -- Dachform nur in gebaeudemass.json gilt als gesetzt", async () => {
  const daten = await hausdaten(await projekt(null,
    { roof_type_modern: "flachdach", roof_type_classic: "walmdach" }));
  assert.equal(daten.dachform_modern, "flachdach");
  assert.equal(daten.dachform_classic, "walmdach");
  assert.equal(daten.herkunft.dachform_modern, "gebaeudemass");
  assert.equal(daten.herkunft.dachform_classic, "gebaeudemass");
});

test("2 -- steht die Dachform in beiden, gewinnt annotations.json", async () => {
  const daten = await hausdaten(await projekt(
    { roof_type_modern: "satteldach", roof_type_classic: "satteldach" },
    { roof_type_modern: "flachdach", roof_type_classic: "walmdach" }));
  assert.equal(daten.dachform_modern, "satteldach");
  assert.equal(daten.dachform_classic, "satteldach");
  assert.equal(daten.herkunft.dachform_modern, "annotations");
});

test("3 -- nur roof_type_modern im Sidecar zaehlt trotzdem als Dach", async () => {
  const daten = await hausdaten(await projekt(null, { roof_type_modern: "flachdach" }));
  assert.equal(daten.dachform_modern, "flachdach");
  assert.equal(daten.dachform_classic, null);
  assert.ok(daten.dachform_modern || daten.dachform_classic);
});

test("4 -- Massstab nur in gebaeudemass.json -> kein vermessung_noetig", async () => {
  const ordner = await projekt(null, {
    floor_scale: { groundfloor: 16.56 },
    rahmen_m: { groundfloor: [16.56, 11.85] },
  });
  const daten = await hausdaten(ordner);
  assert.deepEqual(daten.floor_scale, { groundfloor: 16.56 });
  assert.equal(daten.herkunft.floor_scale, "gebaeudemass");
  assert.equal(daten.hat_gebaeudemass, true);

  const zustand = deriveHouseState({
    raster: true, rooms: 1, levels: ["groundfloor"],
    scale: daten.floor_scale, gebaeudemass: daten.hat_gebaeudemass,
    alignmentComplete: true, zertifikat: false, aktuell: false, blends: 0,
    finalsLokal: 0, wordpress: null, catalogue: null,
  }, "testhaus");
  assert.notEqual(zustand.state, "vermessung_noetig");
});

test("Massstab wird pro Geschoss gemischt, gemessen gewinnt", async () => {
  const daten = await hausdaten(await projekt(
    { floor_scale: { groundfloor: 12.0 } },
    { floor_scale: { groundfloor: 16.56, upperfloor: 16.56 } }));
  assert.deepEqual(daten.floor_scale, { groundfloor: 12.0, upperfloor: 16.56 });
  assert.equal(daten.herkunft.floor_scale, "annotations");
});

test("leere Zeichenketten und leere Objekte gelten als nicht gesetzt", async () => {
  const daten = await hausdaten(await projekt(
    { roof_type_modern: "", roof_type_classic: "", floor_scale: {} },
    { roof_type_modern: "flachdach", roof_type_classic: "walmdach",
      floor_scale: { groundfloor: 16.56 } }));
  assert.equal(daten.dachform_modern, "flachdach");
  assert.equal(daten.dachform_classic, "walmdach");
  assert.deepEqual(daten.floor_scale, { groundfloor: 16.56 });
});

test("ohne Sidecar bleibt alles leer, ohne zu werfen", async () => {
  const daten = await hausdaten(await projekt(null, null));
  assert.equal(daten.dachform_modern, null);
  assert.deepEqual(daten.floor_scale, {});
  assert.equal(daten.hat_gebaeudemass, false);
  assert.equal(daten.herkunft.floor_scale, null);
});

test("eine annotations.json mit BOM wird gelesen wie auf der Python-Seite", async () => {
  const wurzel = await mkdtemp(join(tmpdir(), "hausdaten-bom-"));
  wegwerf.push(wurzel);
  const ordner = join(wurzel, "testhaus");
  await mkdir(ordner);
  await writeFile(join(ordner, "annotations.json"),
    BOM + JSON.stringify(ANNOTATION), "utf8");
  await writeFile(join(ordner, "gebaeudemass.json"),
    BOM + JSON.stringify({ roof_type_classic: "walmdach" }), "utf8");
  const daten = await hausdaten(ordner);
  assert.notEqual(daten.annotationen, null);
  assert.equal(daten.dachform_classic, "walmdach");
});

test("ein Ordner ohne annotations.json wirft nicht", async () => {
  const wurzel = await mkdtemp(join(tmpdir(), "hausdaten-leer-"));
  wegwerf.push(wurzel);
  const daten = await hausdaten(wurzel);
  assert.equal(daten.annotationen, null);
  assert.equal(daten.dachform_classic, null);
});
