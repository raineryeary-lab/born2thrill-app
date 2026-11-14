import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";

const SOURCE_ROLES = new Set(["groundfloor", "upperfloor", "section_elevations"]);
const SUPPORTED_EVIDENCE = new Set([
  "printed_dimension",
  "printed_area",
  "printed_level",
  "printed_note",
  "vector_scale_calibration",
]);

function finitePositive(value) {
  return Number.isFinite(value) && value > 0;
}

export async function sha256File(path) {
  const hash = createHash("sha256");
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest("hex");
}

export function validateMeasuredSourceRecord(record) {
  const errors = [];
  if (record?.schema !== "dmh-measured-floorplan-source-v1") errors.push("invalid_source_schema");
  if (record?.project_id !== "bv-bach") errors.push("invalid_project_id");
  if (record?.source_assets_copied !== false) errors.push("source_assets_must_not_be_copied");
  if (record?.usage_scope !== "internal_review_only") errors.push("source_must_remain_internal_review_only");
  if (!Array.isArray(record?.pages) || record.pages.length !== 3) {
    errors.push("exactly_three_source_pages_required");
  } else {
    const roles = new Set();
    for (const page of record.pages) {
      if (!SOURCE_ROLES.has(page?.role)) errors.push(`invalid_source_role:${page?.role ?? ""}`);
      if (roles.has(page?.role)) errors.push(`duplicate_source_role:${page.role}`);
      roles.add(page?.role);
      if (typeof page?.path !== "string" || !/^[A-Za-z]:\\/.test(page.path)) {
        errors.push(`invalid_source_path:${page?.role ?? ""}`);
      }
      if (page?.page !== 1) errors.push(`invalid_source_page:${page?.role ?? ""}`);
      if (!finitePositive(page?.bytes)) errors.push(`invalid_source_size:${page?.role ?? ""}`);
      if (!/^[a-f0-9]{64}$/.test(page?.sha256 ?? "")) {
        errors.push(`invalid_source_sha256:${page?.role ?? ""}`);
      }
    }
  }
  return { valid: errors.length === 0, errors };
}

export function validateMeasurementWorksheet(worksheet) {
  const errors = [];
  if (worksheet?.schema !== "dmh-measured-floorplan-worksheet-v1") errors.push("invalid_worksheet_schema");
  if (worksheet?.project_id !== "bv-bach") errors.push("invalid_project_id");
  if (worksheet?.coordinate_unit !== "mm") errors.push("coordinate_unit_must_be_mm");
  if (worksheet?.building?.storey_type !== "2_storey") errors.push("invalid_storey_type");
  if (worksheet?.building?.roof_form !== "gable") errors.push("invalid_roof_form");
  if (worksheet?.building?.roof_pitch_degrees !== 22) errors.push("invalid_roof_pitch");
  if (!Array.isArray(worksheet?.levels) || worksheet.levels.length !== 2) errors.push("two_levels_required");
  if (!Array.isArray(worksheet?.rooms) || worksheet.rooms.length !== 11) errors.push("eleven_rooms_required");
  if (
    worksheet?.stairs?.risers !== 15
    || worksheet?.stairs?.rise_mm !== 188
    || worksheet?.stairs?.going_mm !== 260
    || worksheet?.stairs?.source_drawn_width_mm !== 1100
    || worksheet?.stairs?.canonical_clear_width_mm !== 900
    || worksheet?.stairs?.direction !== "up"
  ) {
    errors.push("invalid_stair_measurements");
  }
  if (
    worksheet?.simplification_defaults?.exterior_wall_thickness_mm !== 350
    || worksheet?.simplification_defaults?.interior_wall_thickness_mm !== 100
    || worksheet?.simplification_defaults?.stair_clear_width_mm !== 900
  ) {
    errors.push("invalid_simplification_defaults");
  }
  const ignoredWallBuildUp = worksheet?.ignored_technical_details?.find(
    (item) => item?.name === "source_exterior_wall_build_up_mm",
  );
  if (
    ignoredWallBuildUp?.value_mm !== 425
    || ignoredWallBuildUp?.reason !== "technical_construction_detail_not_part_of_simplified_floorplan"
  ) {
    errors.push("source_wall_build_up_must_be_recorded_as_ignored_technical_detail");
  }

  for (const room of worksheet?.rooms ?? []) {
    if (!["groundfloor", "upperfloor"].includes(room?.floor_id)) errors.push(`invalid_room_floor:${room?.name ?? ""}`);
    if (typeof room?.name !== "string" || !room.name.trim()) errors.push("room_name_required");
    if (!finitePositive(room?.area_m2)) errors.push(`invalid_room_area:${room?.name ?? ""}`);
  }

  for (const measurement of worksheet?.measurements ?? []) {
    if (typeof measurement?.name !== "string" || !measurement.name.trim()) errors.push("measurement_name_required");
    if (!finitePositive(measurement?.value_mm)) errors.push(`invalid_measurement_value:${measurement?.name ?? ""}`);
    if (!SUPPORTED_EVIDENCE.has(measurement?.evidence_type)) {
      errors.push(`unsupported_measurement_evidence:${measurement?.name ?? ""}`);
    }
  }

  const unresolvedRequired = Array.isArray(worksheet?.unresolved_required)
    ? worksheet.unresolved_required.filter((value) => typeof value === "string" && value.trim())
    : [];
  if (unresolvedRequired.length && worksheet?.canonical_geometry_blocked !== true) {
    errors.push("canonical_geometry_must_remain_blocked_while_required_dimensions_are_unresolved");
  }
  const canonicalGeometryReady = errors.length === 0
    && unresolvedRequired.length === 0
    && worksheet?.canonical_geometry_blocked === false;
  return {
    valid: errors.length === 0,
    errors,
    unresolvedRequired,
    canonicalGeometryReady,
  };
}
