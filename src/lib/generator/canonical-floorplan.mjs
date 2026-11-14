import { createHash } from "node:crypto";

export const CANONICAL_FLOORPLAN_SCHEMA_VERSION = "dmh-canonical-floorplan-v1";
export const CANONICAL_GEOMETRY_VERSION = "dmh-canonical-geometry-v1";
export const GEOMETRY_TOLERANCE_MM = 5;

const MAX_GRID_CELLS = 250_000;
const STOREY_COUNTS = {
  "1_storey": 1,
  "1_5_storey": 2,
  "2_storey": 2,
};
const ROOM_TYPES = new Set([
  "living",
  "dining",
  "kitchen",
  "living_dining_kitchen",
  "bedroom",
  "bathroom",
  "wc",
  "office",
  "utility",
  "storage",
  "circulation",
  "garage",
  "flex",
  "other",
]);
const WALL_TYPES = new Set(["exterior", "loadbearing", "partition"]);
const OPENING_TYPES = new Set(["door", "window", "open_passage"]);
const STAIR_TYPES = new Set(["straight", "quarter_turn", "half_turn", "multi_turn"]);
const APPROVAL_STATES = new Set(["internal_reference", "commercial_approved", "rejected"]);
const QUALITY_STATES = new Set(["passed", "review_required", "rejected"]);
const RIGHTS_STATES = new Set([
  "not_explicitly_recorded",
  "confirmed_owned",
  "licensed",
  "restricted",
]);
const USAGE_SCOPES = new Set(["internal_reference_only", "commercial_generator"]);
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!isRecord(value)) return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .filter((key) => value[key] !== undefined)
      .map((key) => [key, canonicalValue(value[key])]),
  );
}

export function canonicalFloorplanGeometryPayload(plan) {
  return canonicalValue({
    schema_version: plan?.schema_version,
    units: plan?.units,
    coordinate_system: plan?.coordinate_system,
    building: plan?.building,
    footprint: plan?.footprint,
    storeys: plan?.storeys,
    entrance: plan?.entrance,
    stairs: plan?.stairs,
  });
}

export function canonicalFloorplanGeometrySha256(plan) {
  const canonical = JSON.stringify(canonicalFloorplanGeometryPayload(plan));
  return createHash("sha256").update(canonical).digest("hex");
}

export function withCanonicalGeometryHash(plan) {
  const copy = structuredClone(plan);
  copy.geometry_hash = {
    algorithm: "sha256",
    canonicalization: CANONICAL_GEOMETRY_VERSION,
    value: canonicalFloorplanGeometrySha256(copy),
  };
  return copy;
}

function addError(errors, code, path = "") {
  const value = path ? `${code}:${path}` : code;
  if (!errors.includes(value)) errors.push(value);
}

function allowedKeys(value, allowed, path, errors) {
  if (!isRecord(value)) return;
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) addError(errors, "unknown_property", `${path}.${key}`);
  }
}

function requiredString(value, path, errors) {
  if (typeof value !== "string" || !value.trim()) {
    addError(errors, "required_string", path);
    return null;
  }
  return value;
}

function requiredId(value, path, errors) {
  const id = requiredString(value, path, errors);
  if (id && !ID_PATTERN.test(id)) addError(errors, "invalid_id", path);
  return id;
}

function requiredSafeInteger(value, path, errors, { positive = false, nonNegative = false } = {}) {
  if (!Number.isSafeInteger(value)) {
    addError(errors, "invalid_integer_mm", path);
    return null;
  }
  if (positive && value <= 0) addError(errors, "integer_must_be_positive", path);
  if (nonNegative && value < 0) addError(errors, "integer_must_be_non_negative", path);
  return value;
}

function point(value, path, errors) {
  if (!Array.isArray(value) || value.length !== 2) {
    addError(errors, "invalid_point", path);
    return null;
  }
  const x = requiredSafeInteger(value[0], `${path}[0]`, errors);
  const y = requiredSafeInteger(value[1], `${path}[1]`, errors);
  return x === null || y === null ? null : [x, y];
}

function samePoint(left, right, tolerance = 0) {
  return Math.abs(left[0] - right[0]) <= tolerance
    && Math.abs(left[1] - right[1]) <= tolerance;
}

function polygonArea(points) {
  if (!Array.isArray(points) || points.length < 3) return 0;
  let sum = 0;
  for (let index = 0; index < points.length; index += 1) {
    const next = points[(index + 1) % points.length];
    sum += points[index][0] * next[1] - next[0] * points[index][1];
  }
  return Math.abs(sum) / 2;
}

function orientation(a, b, c) {
  const cross = (b[0] - a[0]) * (c[1] - a[1])
    - (b[1] - a[1]) * (c[0] - a[0]);
  return Math.sign(cross);
}

function pointOnSegment(candidate, start, end, tolerance = 0) {
  const length = Math.hypot(end[0] - start[0], end[1] - start[1]);
  if (length === 0) return samePoint(candidate, start, tolerance);
  const cross = Math.abs(
    (candidate[0] - start[0]) * (end[1] - start[1])
      - (candidate[1] - start[1]) * (end[0] - start[0]),
  );
  if (cross > tolerance * length) return false;
  return candidate[0] >= Math.min(start[0], end[0]) - tolerance
    && candidate[0] <= Math.max(start[0], end[0]) + tolerance
    && candidate[1] >= Math.min(start[1], end[1]) - tolerance
    && candidate[1] <= Math.max(start[1], end[1]) + tolerance;
}

function segmentsIntersect(a, b, c, d) {
  const o1 = orientation(a, b, c);
  const o2 = orientation(a, b, d);
  const o3 = orientation(c, d, a);
  const o4 = orientation(c, d, b);
  if (o1 !== o2 && o3 !== o4) return true;
  return (o1 === 0 && pointOnSegment(c, a, b))
    || (o2 === 0 && pointOnSegment(d, a, b))
    || (o3 === 0 && pointOnSegment(a, c, d))
    || (o4 === 0 && pointOnSegment(b, c, d));
}

function polygonIsSimple(points) {
  for (let left = 0; left < points.length; left += 1) {
    const leftNext = (left + 1) % points.length;
    for (let right = left + 1; right < points.length; right += 1) {
      const rightNext = (right + 1) % points.length;
      if (
        left === right
        || leftNext === right
        || rightNext === left
        || (left === 0 && rightNext === 0)
      ) {
        continue;
      }
      if (segmentsIntersect(points[left], points[leftNext], points[right], points[rightNext])) {
        return false;
      }
    }
  }
  return true;
}

function validatePolygon(value, path, errors) {
  if (!Array.isArray(value) || value.length < 3) {
    addError(errors, "polygon_requires_three_points", path);
    return null;
  }
  const points = value
    .map((candidate, index) => point(candidate, `${path}[${index}]`, errors))
    .filter(Boolean);
  if (points.length !== value.length) return null;
  if (samePoint(points[0], points.at(-1))) {
    addError(errors, "polygon_must_be_implicitly_closed", path);
  }
  const unique = new Set(points.map(([x, y]) => `${x}:${y}`));
  if (unique.size < 3) addError(errors, "polygon_requires_three_unique_points", path);
  for (let index = 0; index < points.length; index += 1) {
    const next = points[(index + 1) % points.length];
    if (samePoint(points[index], next)) {
      addError(errors, "polygon_zero_length_edge", `${path}[${index}]`);
    }
    if (points[index][0] !== next[0] && points[index][1] !== next[1]) {
      addError(errors, "polygon_edge_not_rectilinear", `${path}[${index}]`);
    }
  }
  if (polygonArea(points) <= 0) addError(errors, "polygon_area_zero", path);
  if (!polygonIsSimple(points)) addError(errors, "polygon_self_intersection", path);
  return points;
}

function pointInPolygon(candidate, polygon, includeBoundary = true) {
  if (includeBoundary) {
    for (let index = 0; index < polygon.length; index += 1) {
      if (pointOnSegment(candidate, polygon[index], polygon[(index + 1) % polygon.length], GEOMETRY_TOLERANCE_MM)) {
        return true;
      }
    }
  }
  let inside = false;
  for (let index = 0, previous = polygon.length - 1; index < polygon.length; previous = index++) {
    const [xi, yi] = polygon[index];
    const [xj, yj] = polygon[previous];
    const crosses = (yi > candidate[1]) !== (yj > candidate[1])
      && candidate[0] < ((xj - xi) * (candidate[1] - yi)) / (yj - yi) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
}

function polygonInside(inner, outer) {
  return inner.every((candidate) => pointInPolygon(candidate, outer, true));
}

function uniqueSorted(values) {
  return [...new Set(values)].sort((left, right) => left - right);
}

function coverageReport(boundary, rooms) {
  const xs = uniqueSorted([
    ...boundary.map(([x]) => x),
    ...rooms.flatMap((room) => room.polygon.map(([x]) => x)),
  ]);
  const ys = uniqueSorted([
    ...boundary.map(([, y]) => y),
    ...rooms.flatMap((room) => room.polygon.map(([, y]) => y)),
  ]);
  if ((xs.length - 1) * (ys.length - 1) > MAX_GRID_CELLS) {
    return { tooComplex: true, gapAreaMm2: 0, overlapAreaMm2: 0, outsideAreaMm2: 0 };
  }
  let gapAreaMm2 = 0;
  let overlapAreaMm2 = 0;
  let outsideAreaMm2 = 0;
  for (let xIndex = 0; xIndex < xs.length - 1; xIndex += 1) {
    for (let yIndex = 0; yIndex < ys.length - 1; yIndex += 1) {
      const width = xs[xIndex + 1] - xs[xIndex];
      const height = ys[yIndex + 1] - ys[yIndex];
      if (width <= 0 || height <= 0) continue;
      const sample = [xs[xIndex] + width / 2, ys[yIndex] + height / 2];
      const insideBoundary = pointInPolygon(sample, boundary, false);
      const coveringRooms = rooms.filter((room) => pointInPolygon(sample, room.polygon, false)).length;
      const area = width * height;
      if (insideBoundary && coveringRooms === 0) gapAreaMm2 += area;
      if (insideBoundary && coveringRooms > 1) overlapAreaMm2 += area * (coveringRooms - 1);
      if (!insideBoundary && coveringRooms > 0) outsideAreaMm2 += area * coveringRooms;
    }
  }
  return { tooComplex: false, gapAreaMm2, overlapAreaMm2, outsideAreaMm2 };
}

function collinearInterval(edgeStart, edgeEnd, wallStart, wallEnd) {
  const horizontal = edgeStart[1] === edgeEnd[1];
  if (horizontal) {
    if (
      wallStart[1] !== wallEnd[1]
      || Math.abs(edgeStart[1] - wallStart[1]) > GEOMETRY_TOLERANCE_MM
    ) return null;
    return [
      Math.max(Math.min(edgeStart[0], edgeEnd[0]), Math.min(wallStart[0], wallEnd[0])),
      Math.min(Math.max(edgeStart[0], edgeEnd[0]), Math.max(wallStart[0], wallEnd[0])),
    ];
  }
  if (
    wallStart[0] !== wallEnd[0]
    || Math.abs(edgeStart[0] - wallStart[0]) > GEOMETRY_TOLERANCE_MM
  ) return null;
  return [
    Math.max(Math.min(edgeStart[1], edgeEnd[1]), Math.min(wallStart[1], wallEnd[1])),
    Math.min(Math.max(edgeStart[1], edgeEnd[1]), Math.max(wallStart[1], wallEnd[1])),
  ];
}

function edgeCoveredByWalls(edgeStart, edgeEnd, walls, roomId) {
  const edgeMinimum = edgeStart[0] === edgeEnd[0]
    ? Math.min(edgeStart[1], edgeEnd[1])
    : Math.min(edgeStart[0], edgeEnd[0]);
  const edgeMaximum = edgeStart[0] === edgeEnd[0]
    ? Math.max(edgeStart[1], edgeEnd[1])
    : Math.max(edgeStart[0], edgeEnd[0]);
  const intervals = walls
    .filter((wall) => wall.separates.includes(roomId))
    .map((wall) => collinearInterval(edgeStart, edgeEnd, wall.start, wall.end))
    .filter((interval) => interval && interval[1] > interval[0])
    .sort((left, right) => left[0] - right[0]);
  let coveredUntil = edgeMinimum;
  for (const [start, end] of intervals) {
    if (start > coveredUntil + GEOMETRY_TOLERANCE_MM) return false;
    coveredUntil = Math.max(coveredUntil, end);
    if (coveredUntil >= edgeMaximum - GEOMETRY_TOLERANCE_MM) return true;
  }
  return coveredUntil >= edgeMaximum - GEOMETRY_TOLERANCE_MM;
}

function unorderedPairEqual(left, right) {
  return Array.isArray(left)
    && Array.isArray(right)
    && left.length === 2
    && right.length === 2
    && [...left].sort().join("\u0000") === [...right].sort().join("\u0000");
}

function polygonsEqualWithin(left, right, tolerance = GEOMETRY_TOLERANCE_MM) {
  if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) return false;
  for (const candidate of [right, [...right].reverse()]) {
    for (let offset = 0; offset < candidate.length; offset += 1) {
      if (left.every((value, index) =>
        samePoint(value, candidate[(index + offset) % candidate.length], tolerance))) {
        return true;
      }
    }
  }
  return false;
}

function validateApproval(approval, errors) {
  const path = "approval";
  if (!isRecord(approval)) {
    addError(errors, "required_object", path);
    return;
  }
  allowedKeys(approval, new Set([
    "state",
    "quality_status",
    "rights_status",
    "usage_scope",
    "approved_by",
    "approved_at",
    "rights_evidence_reference",
  ]), path, errors);
  if (!APPROVAL_STATES.has(approval.state)) addError(errors, "invalid_approval_state", `${path}.state`);
  if (!QUALITY_STATES.has(approval.quality_status)) addError(errors, "invalid_quality_status", `${path}.quality_status`);
  if (!RIGHTS_STATES.has(approval.rights_status)) addError(errors, "invalid_rights_status", `${path}.rights_status`);
  if (!USAGE_SCOPES.has(approval.usage_scope)) addError(errors, "invalid_usage_scope", `${path}.usage_scope`);
  for (const key of ["approved_by", "approved_at", "rights_evidence_reference"]) {
    if (approval[key] !== null && (typeof approval[key] !== "string" || !approval[key].trim())) {
      addError(errors, "invalid_optional_string", `${path}.${key}`);
    }
  }
  if (
    approval.approved_at !== null
    && typeof approval.approved_at === "string"
    && Number.isNaN(Date.parse(approval.approved_at))
  ) {
    addError(errors, "invalid_approval_timestamp", `${path}.approved_at`);
  }
  const commercial = approval.usage_scope === "commercial_generator"
    || approval.state === "commercial_approved";
  if (commercial) {
    if (approval.usage_scope !== "commercial_generator" || approval.state !== "commercial_approved") {
      addError(errors, "commercial_approval_state_scope_mismatch", path);
    }
    if (!["confirmed_owned", "licensed"].includes(approval.rights_status)) {
      addError(errors, "commercial_rights_not_confirmed", `${path}.rights_status`);
    }
    if (!approval.approved_by || !approval.approved_at || !approval.rights_evidence_reference) {
      addError(errors, "commercial_approval_evidence_missing", path);
    }
    if (approval.quality_status !== "passed") {
      addError(errors, "commercial_quality_not_passed", `${path}.quality_status`);
    }
  }
}

function validateProvenance(provenance, errors, warnings) {
  const path = "provenance";
  if (!isRecord(provenance)) {
    addError(errors, "required_object", path);
    return;
  }
  allowedKeys(provenance, new Set([
    "source_kind",
    "source_project_id",
    "source_schema_version",
    "source_annotation_sha256",
    "conversion_method",
    "scale_anchor",
  ]), path, errors);
  if (!["real_annotated", "synthetic_test"].includes(provenance.source_kind)) {
    addError(errors, "invalid_source_kind", `${path}.source_kind`);
  }
  requiredString(provenance.source_project_id, `${path}.source_project_id`, errors);
  requiredString(provenance.source_schema_version, `${path}.source_schema_version`, errors);
  requiredString(provenance.conversion_method, `${path}.conversion_method`, errors);
  if (
    provenance.source_annotation_sha256 !== null
    && !/^[a-f0-9]{64}$/.test(String(provenance.source_annotation_sha256))
  ) {
    addError(errors, "invalid_source_annotation_sha256", `${path}.source_annotation_sha256`);
  }
  const anchor = provenance.scale_anchor;
  if (!isRecord(anchor)) {
    addError(errors, "required_object", `${path}.scale_anchor`);
    return;
  }
  allowedKeys(anchor, new Set([
    "status",
    "kind",
    "source_segment_normalized",
    "length_mm",
  ]), `${path}.scale_anchor`, errors);
  if (!["verified", "user_confirmed_inferred", "not_applicable_synthetic"].includes(anchor.status)) {
    addError(errors, "invalid_scale_anchor_status", `${path}.scale_anchor.status`);
  }
  if (
    provenance.source_kind === "real_annotated"
    && !["verified", "user_confirmed_inferred"].includes(anchor.status)
  ) {
    addError(errors, "real_source_requires_verified_scale", `${path}.scale_anchor.status`);
  }
  if (provenance.source_kind === "synthetic_test" && anchor.status !== "not_applicable_synthetic") {
    addError(errors, "synthetic_source_scale_status_mismatch", `${path}.scale_anchor.status`);
  }
  if (anchor.status === "verified" || anchor.status === "user_confirmed_inferred") {
    if (!["overall_width", "overall_depth", "dimension_line", "survey"].includes(anchor.kind)) {
      addError(errors, "invalid_scale_anchor_kind", `${path}.scale_anchor.kind`);
    }
    requiredSafeInteger(anchor.length_mm, `${path}.scale_anchor.length_mm`, errors, { positive: true });
    if (!Array.isArray(anchor.source_segment_normalized) || anchor.source_segment_normalized.length !== 2) {
      addError(errors, "invalid_normalized_scale_segment", `${path}.scale_anchor.source_segment_normalized`);
    } else {
      anchor.source_segment_normalized.forEach((candidate, index) => {
        if (
          !Array.isArray(candidate)
          || candidate.length !== 2
          || candidate.some((number) => !Number.isFinite(number) || number < 0 || number > 1)
        ) {
          addError(errors, "invalid_normalized_scale_point", `${path}.scale_anchor.source_segment_normalized[${index}]`);
        }
      });
      if (
        Array.isArray(anchor.source_segment_normalized[0])
        && Array.isArray(anchor.source_segment_normalized[1])
        && anchor.source_segment_normalized[0][0] === anchor.source_segment_normalized[1][0]
        && anchor.source_segment_normalized[0][1] === anchor.source_segment_normalized[1][1]
      ) {
        addError(errors, "normalized_scale_segment_zero_length", `${path}.scale_anchor.source_segment_normalized`);
      }
    }
    if (anchor.status === "user_confirmed_inferred") {
      warnings.push("user_confirmed_inferred_scale_requires_review:provenance.scale_anchor");
    }
  } else if (
    anchor.kind !== null
    || anchor.source_segment_normalized !== null
    || anchor.length_mm !== null
  ) {
    addError(errors, "synthetic_scale_anchor_must_be_empty", `${path}.scale_anchor`);
  }
}

export function validateCanonicalFloorplan(plan) {
  const errors = [];
  const warnings = [];
  if (!isRecord(plan)) {
    return { passed: false, errors: ["invalid_plan_shape"], warnings, stats: {} };
  }
  allowedKeys(plan, new Set([
    "schema_version",
    "plan_id",
    "units",
    "coordinate_system",
    "building",
    "footprint",
    "storeys",
    "entrance",
    "stairs",
    "provenance",
    "geometry_hash",
    "approval",
  ]), "plan", errors);
  if (plan.schema_version !== CANONICAL_FLOORPLAN_SCHEMA_VERSION) {
    addError(errors, "unsupported_schema_version", "schema_version");
  }
  requiredId(plan.plan_id, "plan_id", errors);
  if (plan.units !== "mm") addError(errors, "units_must_be_mm", "units");

  const coordinate = plan.coordinate_system;
  if (!isRecord(coordinate)) {
    addError(errors, "required_object", "coordinate_system");
  } else {
    allowedKeys(coordinate, new Set([
      "origin",
      "x_positive",
      "y_positive",
      "integer_precision_mm",
      "north_rotation_degrees",
      "wall_reference",
    ]), "coordinate_system", errors);
    if (coordinate.origin !== "northwest") addError(errors, "invalid_coordinate_origin", "coordinate_system.origin");
    if (coordinate.x_positive !== "east") addError(errors, "invalid_x_axis", "coordinate_system.x_positive");
    if (coordinate.y_positive !== "south") addError(errors, "invalid_y_axis", "coordinate_system.y_positive");
    if (coordinate.integer_precision_mm !== 1) addError(errors, "invalid_coordinate_precision", "coordinate_system.integer_precision_mm");
    if (coordinate.wall_reference !== "centerline") addError(errors, "invalid_wall_reference", "coordinate_system.wall_reference");
    if (
      coordinate.north_rotation_degrees !== null
      && (!Number.isFinite(coordinate.north_rotation_degrees)
        || coordinate.north_rotation_degrees < 0
        || coordinate.north_rotation_degrees >= 360)
    ) {
      addError(errors, "invalid_north_rotation", "coordinate_system.north_rotation_degrees");
    }
  }

  const building = plan.building;
  if (!isRecord(building)) {
    addError(errors, "required_object", "building");
  } else {
    allowedKeys(building, new Set(["storey_type"]), "building", errors);
    if (!Object.hasOwn(STOREY_COUNTS, building.storey_type)) {
      addError(errors, "invalid_storey_type", "building.storey_type");
    }
  }

  const footprint = plan.footprint;
  let footprintPolygon = null;
  if (!isRecord(footprint)) {
    addError(errors, "required_object", "footprint");
  } else {
    allowedKeys(footprint, new Set(["boundary_reference", "boundary_polygon_mm"]), "footprint", errors);
    if (footprint.boundary_reference !== "exterior_wall_centerline") {
      addError(errors, "invalid_footprint_boundary_reference", "footprint.boundary_reference");
    }
    footprintPolygon = validatePolygon(footprint.boundary_polygon_mm, "footprint.boundary_polygon_mm", errors);
  }

  if (!Array.isArray(plan.storeys) || plan.storeys.length < 1) {
    addError(errors, "storeys_required", "storeys");
  }
  const storeys = Array.isArray(plan.storeys) ? plan.storeys : [];
  if (
    building
    && Object.hasOwn(STOREY_COUNTS, building.storey_type)
    && storeys.length !== STOREY_COUNTS[building.storey_type]
  ) {
    addError(errors, "storey_count_mismatch", "storeys");
  }

  const globalIds = new Set();
  const storeyById = new Map();
  const roomById = new Map();
  const roomStorey = new Map();
  const openingById = new Map();
  const openingStorey = new Map();
  const slabById = new Map();
  const parsedStoreys = [];

  function registerId(id, path) {
    if (!requiredId(id, path, errors)) return false;
    if (globalIds.has(id)) {
      addError(errors, "duplicate_id", path);
      return false;
    }
    globalIds.add(id);
    return true;
  }

  for (const [storeyIndex, storey] of storeys.entries()) {
    const storeyPath = `storeys[${storeyIndex}]`;
    if (!isRecord(storey)) {
      addError(errors, "invalid_storey", storeyPath);
      continue;
    }
    allowedKeys(storey, new Set([
      "id",
      "level_index",
      "elevation_mm",
      "planning_boundary_mm",
      "rooms",
      "walls",
      "openings",
      "slab_openings",
    ]), storeyPath, errors);
    registerId(storey.id, `${storeyPath}.id`);
    if (typeof storey.id === "string") storeyById.set(storey.id, storey);
    requiredSafeInteger(storey.level_index, `${storeyPath}.level_index`, errors, { nonNegative: true });
    requiredSafeInteger(storey.elevation_mm, `${storeyPath}.elevation_mm`, errors);
    const boundary = validatePolygon(storey.planning_boundary_mm, `${storeyPath}.planning_boundary_mm`, errors);
    if (boundary && footprintPolygon && !polygonInside(boundary, footprintPolygon)) {
      addError(errors, "planning_boundary_outside_footprint", `${storeyPath}.planning_boundary_mm`);
    }
    const rooms = Array.isArray(storey.rooms) ? storey.rooms : [];
    const walls = Array.isArray(storey.walls) ? storey.walls : [];
    const openings = Array.isArray(storey.openings) ? storey.openings : [];
    const slabs = Array.isArray(storey.slab_openings) ? storey.slab_openings : [];
    if (!Array.isArray(storey.rooms) || rooms.length < 1) addError(errors, "rooms_required", `${storeyPath}.rooms`);
    if (!Array.isArray(storey.walls) || walls.length < 1) addError(errors, "walls_required", `${storeyPath}.walls`);
    if (!Array.isArray(storey.openings)) addError(errors, "openings_array_required", `${storeyPath}.openings`);
    if (!Array.isArray(storey.slab_openings)) addError(errors, "slab_openings_array_required", `${storeyPath}.slab_openings`);

    const parsedRooms = [];
    for (const [roomIndex, room] of rooms.entries()) {
      const roomPath = `${storeyPath}.rooms[${roomIndex}]`;
      if (!isRecord(room)) {
        addError(errors, "invalid_room", roomPath);
        continue;
      }
      allowedKeys(room, new Set([
        "id",
        "name",
        "room_type",
        "access_required",
        "habitable",
        "polygon_mm",
      ]), roomPath, errors);
      registerId(room.id, `${roomPath}.id`);
      requiredString(room.name, `${roomPath}.name`, errors);
      if (!ROOM_TYPES.has(room.room_type)) addError(errors, "invalid_room_type", `${roomPath}.room_type`);
      if (typeof room.access_required !== "boolean") addError(errors, "invalid_boolean", `${roomPath}.access_required`);
      if (typeof room.habitable !== "boolean") addError(errors, "invalid_boolean", `${roomPath}.habitable`);
      const roomPolygon = validatePolygon(room.polygon_mm, `${roomPath}.polygon_mm`, errors);
      if (roomPolygon && boundary && !polygonInside(roomPolygon, boundary)) {
        addError(errors, "room_outside_planning_boundary", `${roomPath}.polygon_mm`);
      }
      if (typeof room.id === "string") {
        roomById.set(room.id, room);
        roomStorey.set(room.id, storey.id);
      }
      if (roomPolygon) parsedRooms.push({ id: room.id, polygon: roomPolygon });
    }

    const parsedWalls = [];
    for (const [wallIndex, wall] of walls.entries()) {
      const wallPath = `${storeyPath}.walls[${wallIndex}]`;
      if (!isRecord(wall)) {
        addError(errors, "invalid_wall", wallPath);
        continue;
      }
      allowedKeys(wall, new Set([
        "id",
        "wall_type",
        "start_mm",
        "end_mm",
        "thickness_mm",
        "separates",
      ]), wallPath, errors);
      registerId(wall.id, `${wallPath}.id`);
      if (!WALL_TYPES.has(wall.wall_type)) addError(errors, "invalid_wall_type", `${wallPath}.wall_type`);
      const start = point(wall.start_mm, `${wallPath}.start_mm`, errors);
      const end = point(wall.end_mm, `${wallPath}.end_mm`, errors);
      requiredSafeInteger(wall.thickness_mm, `${wallPath}.thickness_mm`, errors, { positive: true });
      if (start && end) {
        if (samePoint(start, end)) addError(errors, "wall_zero_length", wallPath);
        if (start[0] !== end[0] && start[1] !== end[1]) addError(errors, "wall_not_rectilinear", wallPath);
        if (boundary && (!pointInPolygon(start, boundary, true) || !pointInPolygon(end, boundary, true))) {
          addError(errors, "wall_outside_planning_boundary", wallPath);
        }
      }
      if (
        !Array.isArray(wall.separates)
        || wall.separates.length !== 2
        || wall.separates.some((value) => typeof value !== "string" || !value)
        || wall.separates[0] === wall.separates[1]
      ) {
        addError(errors, "invalid_wall_separates", `${wallPath}.separates`);
      }
      if (wall.wall_type === "exterior" && wall.separates?.filter((value) => value === "outside").length !== 1) {
        addError(errors, "exterior_wall_must_separate_outside", wallPath);
      }
      if (wall.wall_type !== "exterior" && wall.separates?.includes("outside")) {
        addError(errors, "internal_wall_cannot_separate_outside", wallPath);
      }
      if (start && end && Array.isArray(wall.separates)) {
        parsedWalls.push({ ...wall, start, end });
      }
    }
    for (const wall of parsedWalls) {
      for (const spaceId of wall.separates) {
        if (spaceId !== "outside" && !parsedRooms.some((room) => room.id === spaceId)) {
          addError(errors, "wall_references_unknown_room", `${storeyPath}.walls.${wall.id}`);
        }
      }
    }
    for (const room of parsedRooms) {
      for (let edgeIndex = 0; edgeIndex < room.polygon.length; edgeIndex += 1) {
        if (!edgeCoveredByWalls(
          room.polygon[edgeIndex],
          room.polygon[(edgeIndex + 1) % room.polygon.length],
          parsedWalls,
          room.id,
        )) {
          addError(errors, "room_boundary_without_wall", `${storeyPath}.rooms.${room.id}.edge[${edgeIndex}]`);
        }
      }
    }

    const wallById = new Map(parsedWalls.map((wall) => [wall.id, wall]));
    const openingIntervals = new Map();
    for (const [openingIndex, opening] of openings.entries()) {
      const openingPath = `${storeyPath}.openings[${openingIndex}]`;
      if (!isRecord(opening)) {
        addError(errors, "invalid_opening", openingPath);
        continue;
      }
      allowedKeys(opening, new Set([
        "id",
        "opening_type",
        "wall_id",
        "offset_mm",
        "width_mm",
        "connects",
        "traversable",
        "sill_height_mm",
        "height_mm",
      ]), openingPath, errors);
      registerId(opening.id, `${openingPath}.id`);
      if (!OPENING_TYPES.has(opening.opening_type)) addError(errors, "invalid_opening_type", `${openingPath}.opening_type`);
      requiredString(opening.wall_id, `${openingPath}.wall_id`, errors);
      const offset = requiredSafeInteger(opening.offset_mm, `${openingPath}.offset_mm`, errors, { nonNegative: true });
      const width = requiredSafeInteger(opening.width_mm, `${openingPath}.width_mm`, errors, { positive: true });
      if (typeof opening.traversable !== "boolean") addError(errors, "invalid_boolean", `${openingPath}.traversable`);
      const shouldTraverse = opening.opening_type === "door" || opening.opening_type === "open_passage";
      if (typeof opening.traversable === "boolean" && opening.traversable !== shouldTraverse) {
        addError(errors, "opening_traversability_mismatch", openingPath);
      }
      if (opening.opening_type === "window") {
        requiredSafeInteger(opening.sill_height_mm, `${openingPath}.sill_height_mm`, errors, { nonNegative: true });
        requiredSafeInteger(opening.height_mm, `${openingPath}.height_mm`, errors, { positive: true });
      } else if (opening.sill_height_mm !== undefined || opening.height_mm !== undefined) {
        addError(errors, "door_or_passage_window_dimensions_forbidden", openingPath);
      }
      const wall = wallById.get(opening.wall_id);
      if (!wall) {
        addError(errors, "opening_references_unknown_wall", `${openingPath}.wall_id`);
      } else {
        const wallLength = Math.hypot(wall.end[0] - wall.start[0], wall.end[1] - wall.start[1]);
        if (offset !== null && width !== null && offset + width > wallLength + GEOMETRY_TOLERANCE_MM) {
          addError(errors, "opening_outside_wall", openingPath);
        }
        if (!unorderedPairEqual(opening.connects, wall.separates)) {
          addError(errors, "opening_connections_mismatch_wall", `${openingPath}.connects`);
        }
        if (offset !== null && width !== null) {
          const intervals = openingIntervals.get(wall.id) ?? [];
          if (intervals.some(([start, end]) =>
            Math.max(start, offset) < Math.min(end, offset + width) - GEOMETRY_TOLERANCE_MM)) {
            addError(errors, "openings_overlap", openingPath);
          }
          intervals.push([offset, offset + width]);
          openingIntervals.set(wall.id, intervals);
        }
      }
      if (
        !Array.isArray(opening.connects)
        || opening.connects.length !== 2
        || opening.connects.some((value) => typeof value !== "string" || !value)
      ) {
        addError(errors, "invalid_opening_connections", `${openingPath}.connects`);
      } else {
        for (const spaceId of opening.connects) {
          if (spaceId !== "outside" && !parsedRooms.some((room) => room.id === spaceId)) {
            addError(errors, "opening_references_unknown_room", `${openingPath}.connects`);
          }
        }
      }
      if (typeof opening.id === "string") {
        openingById.set(opening.id, opening);
        openingStorey.set(opening.id, storey.id);
      }
    }

    const parsedSlabs = [];
    for (const [slabIndex, slab] of slabs.entries()) {
      const slabPath = `${storeyPath}.slab_openings[${slabIndex}]`;
      if (!isRecord(slab)) {
        addError(errors, "invalid_slab_opening", slabPath);
        continue;
      }
      allowedKeys(slab, new Set(["id", "opening_type", "polygon_mm"]), slabPath, errors);
      registerId(slab.id, `${slabPath}.id`);
      if (!["stairs", "shaft", "void"].includes(slab.opening_type)) {
        addError(errors, "invalid_slab_opening_type", `${slabPath}.opening_type`);
      }
      const slabPolygon = validatePolygon(slab.polygon_mm, `${slabPath}.polygon_mm`, errors);
      if (slabPolygon && boundary && !polygonInside(slabPolygon, boundary)) {
        addError(errors, "slab_opening_outside_planning_boundary", `${slabPath}.polygon_mm`);
      }
      if (slabPolygon && !parsedRooms.some((room) => polygonInside(slabPolygon, room.polygon))) {
        addError(errors, "slab_opening_not_inside_room", `${slabPath}.polygon_mm`);
      }
      if (typeof slab.id === "string") slabById.set(slab.id, { ...slab, polygon: slabPolygon, storeyId: storey.id });
      if (slabPolygon) parsedSlabs.push({ ...slab, polygon: slabPolygon });
    }

    if (boundary && parsedRooms.length) {
      const coverage = coverageReport(boundary, parsedRooms);
      const toleranceAreaMm2 = Math.max(10_000, polygonArea(boundary) * 0.0001);
      if (coverage.tooComplex) addError(errors, "coverage_grid_too_complex", storeyPath);
      if (coverage.gapAreaMm2 > toleranceAreaMm2) addError(errors, "room_coverage_gap", storeyPath);
      if (coverage.overlapAreaMm2 > toleranceAreaMm2) addError(errors, "room_overlap", storeyPath);
      if (coverage.outsideAreaMm2 > toleranceAreaMm2) addError(errors, "room_outside_planning_boundary", storeyPath);
    }
    parsedStoreys.push({ storey, boundary, rooms: parsedRooms, walls: parsedWalls, openings, slabs: parsedSlabs });
  }

  const levels = storeys.map((storey) => storey?.level_index).filter(Number.isSafeInteger);
  if (new Set(levels).size !== levels.length) addError(errors, "duplicate_storey_level", "storeys");
  const sortedLevels = [...levels].sort((left, right) => left - right);
  if (sortedLevels.some((level, index) => level !== index)) {
    addError(errors, "storey_levels_must_be_consecutive_from_zero", "storeys");
  }
  const elevations = [...storeys]
    .sort((left, right) => Number(left?.level_index) - Number(right?.level_index))
    .map((storey) => storey?.elevation_mm);
  if (elevations.some((value, index) => index > 0 && value <= elevations[index - 1])) {
    addError(errors, "storey_elevations_not_increasing", "storeys");
  }

  const graph = new Map([["outside", new Set()]]);
  for (const roomId of roomById.keys()) graph.set(roomId, new Set());
  for (const opening of openingById.values()) {
    if (!opening.traversable || !Array.isArray(opening.connects) || opening.connects.length !== 2) continue;
    const [from, to] = opening.connects;
    if (!graph.has(from) || !graph.has(to)) continue;
    graph.get(from).add(to);
    graph.get(to).add(from);
  }

  const stairs = Array.isArray(plan.stairs) ? plan.stairs : [];
  if (!Array.isArray(plan.stairs)) addError(errors, "stairs_array_required", "stairs");
  if (building?.storey_type === "1_storey" && stairs.length) {
    addError(errors, "single_storey_must_not_have_stairs", "stairs");
  }
  const referencedSlabs = new Set();
  for (const [stairIndex, stair] of stairs.entries()) {
    const stairPath = `stairs[${stairIndex}]`;
    if (!isRecord(stair)) {
      addError(errors, "invalid_stair", stairPath);
      continue;
    }
    allowedKeys(stair, new Set([
      "id",
      "stair_type",
      "from_storey_id",
      "to_storey_id",
      "clear_width_mm",
      "direction",
      "path_mm",
      "interfaces",
    ]), stairPath, errors);
    registerId(stair.id, `${stairPath}.id`);
    if (!STAIR_TYPES.has(stair.stair_type)) addError(errors, "invalid_stair_type", `${stairPath}.stair_type`);
    if (stair.direction !== "up") addError(errors, "stair_direction_must_be_up", `${stairPath}.direction`);
    requiredSafeInteger(stair.clear_width_mm, `${stairPath}.clear_width_mm`, errors, { positive: true });
    const fromStorey = storeyById.get(stair.from_storey_id);
    const toStorey = storeyById.get(stair.to_storey_id);
    if (!fromStorey) addError(errors, "stair_from_storey_missing", `${stairPath}.from_storey_id`);
    if (!toStorey) addError(errors, "stair_to_storey_missing", `${stairPath}.to_storey_id`);
    if (fromStorey && toStorey && toStorey.level_index !== fromStorey.level_index + 1) {
      addError(errors, "stair_storeys_not_adjacent", stairPath);
    }
    if (!Array.isArray(stair.path_mm) || stair.path_mm.length < 2) {
      addError(errors, "stair_path_requires_two_points", `${stairPath}.path_mm`);
    } else {
      stair.path_mm.forEach((candidate, index) => point(candidate, `${stairPath}.path_mm[${index}]`, errors));
    }
    if (!Array.isArray(stair.interfaces) || stair.interfaces.length !== 2) {
      addError(errors, "stair_requires_two_interfaces", `${stairPath}.interfaces`);
      continue;
    }
    const interfaces = stair.interfaces.map((entry, interfaceIndex) => {
      const interfacePath = `${stairPath}.interfaces[${interfaceIndex}]`;
      if (!isRecord(entry)) {
        addError(errors, "invalid_stair_interface", interfacePath);
        return null;
      }
      allowedKeys(entry, new Set([
        "storey_id",
        "footprint_polygon_mm",
        "arrival_room_id",
        "slab_opening_id",
      ]), interfacePath, errors);
      const footprintValue = validatePolygon(entry.footprint_polygon_mm, `${interfacePath}.footprint_polygon_mm`, errors);
      const storey = storeyById.get(entry.storey_id);
      if (!storey) addError(errors, "stair_interface_storey_missing", `${interfacePath}.storey_id`);
      const room = roomById.get(entry.arrival_room_id);
      if (!room || roomStorey.get(entry.arrival_room_id) !== entry.storey_id) {
        addError(errors, "stair_arrival_room_missing", `${interfacePath}.arrival_room_id`);
      } else if (footprintValue) {
        const roomPolygon = room.polygon_mm;
        if (Array.isArray(roomPolygon) && !polygonInside(footprintValue, roomPolygon)) {
          addError(errors, "stair_footprint_outside_arrival_room", `${interfacePath}.footprint_polygon_mm`);
        }
      }
      return { entry, footprint: footprintValue };
    }).filter(Boolean);
    if (
      interfaces.length === 2
      && interfaces[0].footprint
      && interfaces[1].footprint
      && !polygonsEqualWithin(interfaces[0].footprint, interfaces[1].footprint)
    ) {
      addError(errors, "stair_interfaces_not_aligned", `${stairPath}.interfaces`);
    }
    const fromInterface = interfaces.find(({ entry }) => entry.storey_id === stair.from_storey_id);
    const toInterface = interfaces.find(({ entry }) => entry.storey_id === stair.to_storey_id);
    if (!fromInterface || !toInterface) addError(errors, "stair_interfaces_do_not_match_storeys", stairPath);
    if (fromInterface?.entry.slab_opening_id !== null) {
      addError(errors, "lower_stair_interface_must_not_reference_slab_opening", stairPath);
    }
    if (!toInterface?.entry.slab_opening_id) {
      addError(errors, "upper_stair_slab_opening_required", stairPath);
    } else {
      const slab = slabById.get(toInterface.entry.slab_opening_id);
      referencedSlabs.add(toInterface.entry.slab_opening_id);
      if (!slab || slab.storeyId !== stair.to_storey_id || slab.opening_type !== "stairs") {
        addError(errors, "upper_stair_slab_opening_invalid", stairPath);
      } else if (
        toInterface.footprint
        && slab.polygon
        && !polygonsEqualWithin(toInterface.footprint, slab.polygon)
      ) {
        addError(errors, "stair_slab_opening_not_aligned", stairPath);
      }
    }
    if (
      fromInterface
      && toInterface
      && graph.has(fromInterface.entry.arrival_room_id)
      && graph.has(toInterface.entry.arrival_room_id)
    ) {
      graph.get(fromInterface.entry.arrival_room_id).add(toInterface.entry.arrival_room_id);
      graph.get(toInterface.entry.arrival_room_id).add(fromInterface.entry.arrival_room_id);
    }
  }
  for (const [slabId, slab] of slabById) {
    if (slab.opening_type === "stairs" && !referencedSlabs.has(slabId)) {
      addError(errors, "unreferenced_stair_slab_opening", `slab_openings.${slabId}`);
    }
  }

  const entrance = plan.entrance;
  if (!isRecord(entrance)) {
    addError(errors, "required_object", "entrance");
  } else {
    allowedKeys(entrance, new Set([
      "storey_id",
      "opening_id",
      "enters_room_id",
    ]), "entrance", errors);
    const entranceOpening = openingById.get(entrance.opening_id);
    if (!storeyById.has(entrance.storey_id)) addError(errors, "entrance_storey_missing", "entrance.storey_id");
    if (!entranceOpening) {
      addError(errors, "entrance_opening_missing", "entrance.opening_id");
    } else {
      if (openingStorey.get(entrance.opening_id) !== entrance.storey_id) {
        addError(errors, "entrance_opening_storey_mismatch", "entrance");
      }
      if (!entranceOpening.traversable || entranceOpening.opening_type !== "door") {
        addError(errors, "entrance_must_be_exterior_door", "entrance.opening_id");
      }
      if (!unorderedPairEqual(entranceOpening.connects, ["outside", entrance.enters_room_id])) {
        addError(errors, "entrance_connections_invalid", "entrance");
      }
    }
    if (
      !roomById.has(entrance.enters_room_id)
      || roomStorey.get(entrance.enters_room_id) !== entrance.storey_id
    ) {
      addError(errors, "entrance_room_missing", "entrance.enters_room_id");
    }
  }

  const visited = new Set();
  const queue = ["outside"];
  while (queue.length) {
    const current = queue.shift();
    if (visited.has(current)) continue;
    visited.add(current);
    for (const adjacent of graph.get(current) ?? []) {
      if (!visited.has(adjacent)) queue.push(adjacent);
    }
  }
  for (const [roomId, room] of roomById) {
    if (room.access_required && !visited.has(roomId)) {
      addError(errors, "room_unreachable_from_entrance", `rooms.${roomId}`);
    }
  }

  validateProvenance(plan.provenance, errors, warnings);
  validateApproval(plan.approval, errors);
  if (
    plan.approval?.usage_scope === "commercial_generator"
    && plan.provenance?.scale_anchor?.status !== "verified"
  ) {
    addError(errors, "commercial_use_requires_verified_scale", "provenance.scale_anchor.status");
  }
  if (
    plan.provenance?.source_kind === "synthetic_test"
    && plan.approval?.usage_scope === "commercial_generator"
  ) {
    addError(errors, "synthetic_source_cannot_be_commercial", "approval.usage_scope");
  }

  const geometryHash = plan.geometry_hash;
  if (!isRecord(geometryHash)) {
    addError(errors, "required_object", "geometry_hash");
  } else {
    allowedKeys(geometryHash, new Set([
      "algorithm",
      "canonicalization",
      "value",
    ]), "geometry_hash", errors);
    if (geometryHash.algorithm !== "sha256") addError(errors, "invalid_geometry_hash_algorithm", "geometry_hash.algorithm");
    if (geometryHash.canonicalization !== CANONICAL_GEOMETRY_VERSION) {
      addError(errors, "invalid_geometry_hash_canonicalization", "geometry_hash.canonicalization");
    }
    if (!/^[a-f0-9]{64}$/.test(String(geometryHash.value))) {
      addError(errors, "invalid_geometry_hash_value", "geometry_hash.value");
    } else if (geometryHash.value !== canonicalFloorplanGeometrySha256(plan)) {
      addError(errors, "geometry_hash_mismatch", "geometry_hash.value");
    }
  }

  return {
    passed: errors.length === 0,
    errors,
    warnings,
    stats: {
      storeyCount: storeys.length,
      roomCount: roomById.size,
      openingCount: openingById.size,
      stairCount: stairs.length,
      geometrySha256: canonicalFloorplanGeometrySha256(plan),
    },
  };
}

export class CanonicalFloorplanValidationError extends Error {
  constructor(report) {
    super(`canonical_floorplan_invalid:${report.errors.join(",")}`);
    this.name = "CanonicalFloorplanValidationError";
    this.report = report;
  }
}

export function loadCanonicalFloorplan(source) {
  let value;
  try {
    if (typeof source === "string" || Buffer.isBuffer(source)) {
      value = JSON.parse(source.toString());
    } else {
      value = structuredClone(source);
    }
  } catch {
    throw new CanonicalFloorplanValidationError({
      passed: false,
      errors: ["invalid_json"],
      warnings: [],
      stats: {},
    });
  }
  const report = validateCanonicalFloorplan(value);
  if (!report.passed) throw new CanonicalFloorplanValidationError(report);
  return value;
}
