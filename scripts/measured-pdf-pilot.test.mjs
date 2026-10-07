import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  sha256File,
  validateMeasuredSourceRecord,
  validateMeasurementWorksheet,
} from "../src/lib/generator/measured-pdf-pilot.mjs";

const root = process.env.LOCALAPPDATA
  ? `${process.env.LOCALAPPDATA}\\Born2Thrill\\floorplan-workbench\\measured-imports\\bv-bach`
  : "C:\\Users\\Admin\\AppData\\Local\\Born2Thrill\\floorplan-workbench\\measured-imports\\bv-bach";

async function json(name) {
  return JSON.parse(await readFile(`${root}\\${name}`, "utf8"));
}

test("BV Bach source PDFs are immutable and match the recorded SHA-256 hashes", async () => {
  const record = await json("source-record.json");
  assert.deepEqual(validateMeasuredSourceRecord(record), { valid: true, errors: [] });
  for (const page of record.pages) assert.equal(await sha256File(page.path), page.sha256);
});

test("explicit measured facts are accepted but unresolved anchors block canonical geometry", async () => {
  const worksheet = await json("measurement-worksheet.json");
  const report = validateMeasurementWorksheet(worksheet);
  assert.equal(report.valid, true);
  assert.equal(report.canonicalGeometryReady, false);
  assert.deepEqual(report.unresolvedRequired, worksheet.unresolved_required);
  assert.equal(worksheet.building.roof_pitch_degrees, 22);
  assert.deepEqual(worksheet.levels.map((floor) => floor.finished_floor_mm), [165, 2985]);
  assert.deepEqual(worksheet.stairs, {
    floor_ids: ["groundfloor", "upperfloor"],
    risers: 15,
    rise_mm: 188,
    going_mm: 260,
    source_drawn_width_mm: 1100,
    canonical_clear_width_mm: 900,
    direction: "up",
    evidence_type: "printed_dimension",
    source_role: "groundfloor",
  });
  assert.equal(worksheet.rooms.reduce((sum, room) => sum + room.area_m2, 0).toFixed(2), "126.08");
  assert.deepEqual(Object.fromEntries(worksheet.measurements.map((item) => [item.name, item.value_mm])), {
    overall_exterior_width_mm: 8990,
    overall_exterior_depth_mm: 9740,
  });
  assert.deepEqual(worksheet.simplification_defaults, {
    exterior_wall_thickness_mm: 350,
    interior_wall_thickness_mm: 100,
    stair_clear_width_mm: 900,
  });
  assert.deepEqual(worksheet.ignored_technical_details, [{
    name: "source_exterior_wall_build_up_mm",
    value_mm: 425,
    reason: "technical_construction_detail_not_part_of_simplified_floorplan",
    evidence_type: "vector_scale_calibration",
    source_role: "groundfloor",
  }]);
  assert.ok(Math.abs(worksheet.vector_calibration.stair_going_derived_mm - 260) < 1);
  assert.equal(worksheet.derived_geometry.roof_ridge_height_mm, 7411);
  assert.deepEqual(worksheet.layout_anchors.groundfloor.canonical_boundary_mm, [[0, 0], [8640, 9390]]);
  assert.deepEqual(worksheet.layout_anchors.upperfloor.canonical_boundary_mm, [[0, 0], [8640, 9390]]);
  assert.deepEqual(
    worksheet.layout_anchors.groundfloor.partition_centerlines.map(({ id, canonical_mm }) => [id, canonical_mm]),
    [["htr_diele", 2456], ["stair_east", 3742], ["wc_west", 5167], ["wc_abstell", 6552]],
  );
  assert.deepEqual(
    worksheet.layout_anchors.upperfloor.partition_centerlines.map(({ id, canonical_mm }) => [id, canonical_mm]),
    [["stair_west", 2494], ["stair_east", 3704], ["bedroom_split", 4435], ["ankleide_bad", 5842]],
  );
  assert.deepEqual(
    worksheet.confirmed_exterior_openings.filter(({ source_role }) => source_role === "groundfloor").map(({ id, width_mm }) => [id, width_mm]),
    [["eg_north_left", 1760], ["eg_north_right", 1760], ["eg_west_living", 1760], ["eg_east_kitchen", 1510], ["eg_south_entrance_source", 1135], ["eg_south_entrance_canonical", 1100]],
  );
  assert.deepEqual(
    worksheet.confirmed_exterior_openings.filter(({ source_role }) => source_role === "upperfloor").map(({ id, width_mm }) => [id, width_mm]),
    [["og_north_left", 1760], ["og_north_right", 1760], ["og_west", 1510], ["og_east", 1510], ["og_south_left", 885], ["og_south_right", 885]],
  );
});

test("unresolved or unsupported measurements can never be marked canonical-ready", async () => {
  const worksheet = await json("measurement-worksheet.json");
  const falseReady = structuredClone(worksheet);
  falseReady.canonical_geometry_blocked = false;
  assert.ok(validateMeasurementWorksheet(falseReady).errors.includes(
    "canonical_geometry_must_remain_blocked_while_required_dimensions_are_unresolved",
  ));

  const invented = structuredClone(worksheet);
  invented.unresolved_required = [];
  invented.measurements = [{
    name: "overall_exterior_width_mm",
    value_mm: 9000,
    evidence_type: "guess",
  }];
  assert.ok(validateMeasurementWorksheet(invented).errors.includes(
    "unsupported_measurement_evidence:overall_exterior_width_mm",
  ));
});
