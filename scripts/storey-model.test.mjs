import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  headroomDistanceMm,
  migrateReferenceProjectToStoreyTemplate,
  referenceGeometryFingerprint,
  roofAreaBands,
  roomRoofHeadroomReport,
  solveStairGeometry,
  validateStoreyTemplate,
} from "../src/lib/generator/storey-model.mjs";

test("stair solver returns a compliant solution or an explicit failure", () => {
  for (let height = 2400; height <= 3200; height += 10) {
    const result = solveStairGeometry(height);
    if (!result.ok) {
      assert.match(result.reason, /^no_compliant_|^invalid_/);
      continue;
    }
    assert.ok(result.riseMm <= 200, `${height}: rise`);
    assert.ok(result.goingMm >= 260, `${height}: going`);
    assert.ok(result.stepMeasureMm >= 590 && result.stepMeasureMm <= 650, `${height}: step measure`);
    assert.ok(result.clearWidthMm >= 800, `${height}: width`);
    assert.ok(result.landingDepthMm >= result.clearWidthMm, `${height}: landing`);
  }
});

test("2800 mm resolves to a compact 90 cm half-turn stair", () => {
  const result = solveStairGeometry(2800);
  assert.equal(result.ok, true);
  assert.equal(result.type, "half_turn");
  assert.equal(result.riserCount, 16);
  assert.equal(result.riseMm, 175);
  assert.equal(result.goingMm, 280);
  assert.equal(result.stepMeasureMm, 630);
  assert.equal(result.clearWidthMm, 900);
  assert.equal(result.footprint.widthMm, 2100);
  assert.equal(result.footprint.lengthMm, 2860);
});

test("roof headroom matches the 9 m / 40 degree / 1.2 m knee-wall example", () => {
  const roof = { pitchDeg: 40, kneeWallMm: 1200 };
  assert.ok(Math.abs(headroomDistanceMm(2000, roof) - 953.4) < 0.1);
  const bands = roofAreaBands({
    buildingWidthMm: 9000,
    buildingLengthMm: 10000,
    roof,
  });
  assert.ok(Math.abs(bands.fullWidthMm - 7093.2) < 0.2);
  assert.equal(bands.zeroAreaM2, 0);
  assert.ok(Math.abs(bands.wohnflaecheM2 - 80.47) < 0.02);
});

test("roof-storey bedroom qualification uses the 2.30 m half-area gate", () => {
  const qualified = roomRoofHeadroomReport({
    polygon: [
      [1000, 0],
      [8000, 0],
      [8000, 4000],
      [1000, 4000],
    ],
    axis: "x",
    envelopeMinimumMm: 0,
    envelopeMaximumMm: 9000,
    roof: { pitchDeg: 40, kneeWallMm: 1200 },
  });
  assert.equal(qualified.qualifiesAsHabitableRoom, true);

  const failed = roomRoofHeadroomReport({
    polygon: [
      [0, 0],
      [1800, 0],
      [1800, 4000],
      [0, 4000],
    ],
    axis: "x",
    envelopeMinimumMm: 0,
    envelopeMaximumMm: 9000,
    roof: { pitchDeg: 40, kneeWallMm: 1200 },
  });
  assert.equal(failed.qualifiesAsHabitableRoom, false);
});

test("validator catches stair and roof-storey hard failures", () => {
  const stair = solveStairGeometry(2800);
  const core = [[0, 0], [2100, 0], [2100, 2860], [0, 2860]];
  const template = {
    storeyType: "1_5_storey",
    storeys: [
      { level: 0, rooms: [], slabOpenings: [] },
      {
        level: 1,
        slabOpenings: [[[10, 0], [2110, 0], [2110, 2860], [10, 2860]]],
        rooms: [{
          id: "bad-bedroom",
          type: "bedroom",
          headroom: { qualifiesAsHabitableRoom: false },
        }],
      },
    ],
    stairCore: {
      footprint: core,
      geometry: {
        ...stair,
        riseMm: 210,
        availableHeadroomMm: 1900,
      },
    },
    roof: {
      form: "gable",
      pitchDeg: 40,
      kneeWallMm: 1200,
      ridgeAxis: "short_side",
    },
  };
  const report = validateStoreyTemplate(template);
  assert.equal(report.passed, false);
  assert.ok(report.errors.includes("stair_opening_mismatch_level_1"));
  assert.ok(report.errors.includes("stair_rise_exceeds_limit"));
  assert.ok(report.errors.includes("stair_headroom_below_limit"));
  assert.ok(report.errors.includes("ridge_axis_must_follow_long_side"));
  assert.ok(report.errors.includes("roof_bedroom_headroom_failed:bad-bedroom"));
});

test("legacy migration preserves every current reference geometry byte-for-byte", async () => {
  const dataset = JSON.parse(
    await readFile(new URL("../data/simplifier-v1/dataset.json", import.meta.url), "utf8"),
  );
  const manifest = JSON.parse(
    await readFile(new URL("../data/simplifier-v1/manifest.json", import.meta.url), "utf8"),
  );
  assert.equal(dataset.projects.length, manifest.project_count);
  for (const project of dataset.projects) {
    const before = referenceGeometryFingerprint(project);
    const migrated = migrateReferenceProjectToStoreyTemplate(project);
    assert.equal(
      referenceGeometryFingerprint(migrated.legacySource),
      before,
      `${project.project_id} geometry changed during migration`,
    );
    assert.equal(migrated.migration.geometryChanged, false);
  }
});

test("legacy multi-storey references remain review-only when stair cores differ", async () => {
  const dataset = JSON.parse(
    await readFile(new URL("../data/simplifier-v1/dataset.json", import.meta.url), "utf8"),
  );
  const multiStorey = dataset.projects.filter((project) =>
    project.floors.filter((floor) => floor.floor_level !== "basement").length > 1
  );
  assert.equal(multiStorey.length, 83);
  const reports = multiStorey.map((project) =>
    migrateReferenceProjectToStoreyTemplate(project).migration
  );
  assert.ok(reports.every((report) => report.requiresReview));
  assert.ok(reports.some((report) =>
    report.issues.some((issue) => issue.startsWith("stair_core_misaligned"))
  ));
});
