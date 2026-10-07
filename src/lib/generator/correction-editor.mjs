import { createHash } from "node:crypto";
import {
  buildMillimetreCorrectionGeometry,
  CORRECTION_DEFAULTS,
  mergeCollinearWalls,
  polygonAreaM2,
  polygonAreaMm2,
} from "./correction-geometry.mjs";
import {
  FLOORPLAN_RULEBOOK_VERSION,
  FLOORPLAN_RULES,
  isHabitableRoom,
  normalizedRoomRuleKey,
} from "./floorplan-rulebook.mjs";

export const CORRECTION_SCHEMA = "dmh-floorplan-correction-v2";
export const DEFAULT_RIGHTS = "internal_reference_only";
export { CORRECTION_DEFAULTS, FLOORPLAN_RULEBOOK_VERSION, FLOORPLAN_RULES };

function rounded(value) {
  return Math.round(Number(value) || 0);
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])]));
}

export function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export function correctionGeometryHash(document) {
  return createHash("sha256").update(canonicalJson({
    schema: document.schema,
    source_reference_id: document.source_reference_id,
    building: document.building,
    floors: document.floors,
    shared_stair_core: document.shared_stair_core,
  })).digest("hex");
}

export function approvedGeometryHash(document) {
  return createHash("sha256").update(canonicalJson({
    building: document.building,
    floors: document.floors,
    shared_stair_core: document.shared_stair_core,
  })).digest("hex");
}

export function snapCoordinate(value, grid = 5) {
  const spacing = Math.max(1, rounded(grid));
  return Math.round((Number(value) || 0) / spacing) * spacing;
}

export function buildCorrectionDocument(variant, options = {}) {
  const workingGeometry = buildMillimetreCorrectionGeometry(variant);
  const reconstructionOnly = options.reconstructionOnly === true;
  const sourceRightsStatus = options.sourceRightsStatus || (reconstructionOnly ? "restricted_reference" : "not_restricted");
  const sourceSnapshot = structuredClone({
    reference_layout_id: variant.metrics.referenceLayoutId,
    floors: variant.floors,
    stair_core: variant.stairCore,
  });
  const document = {
    schema: CORRECTION_SCHEMA,
    revision: 0,
    source_reference_id: variant.metrics.referenceLayoutId,
    source_annotation: sourceSnapshot,
    source_annotation_sha256: createHash("sha256").update(canonicalJson(sourceSnapshot)).digest("hex"),
    provenance: {
      created_from: reconstructionOnly ? "restricted_functional_reference" : "annotated_reference",
      transformation: reconstructionOnly ? "generic_layout_reconstruction" : "manual_correction_revision",
      source_mutated: false,
      source_snapshot_scope: "internal_revision_only",
      publication_excludes_source_artifacts: true,
    },
    rulebook_version: FLOORPLAN_RULEBOOK_VERSION,
    rights: {
      source_status: sourceRightsStatus,
      usage_scope: DEFAULT_RIGHTS,
      decision: "undecided",
      commercial_approval_attested: false,
      wordpress_eligible: false,
    },
    building: {
      coordinate_unit: "mm",
      footprint_width_mm: rounded(Number(variant.metrics.footprintWidthM) * 1000),
      footprint_depth_mm: rounded(Number(variant.metrics.footprintDepthM) * 1000),
      floor_height_mm: 2800,
      storey_type: variant.storeyType,
      roof_form: "gable",
      geometry_source: reconstructionOnly ? "generic_layout_reconstruction" : "rectified_annotated_reference",
    },
    defaults: CORRECTION_DEFAULTS,
    floors: workingGeometry.floors,
    shared_stair_core: workingGeometry.shared_stair_core,
    geometry_hash: "",
    status: "draft",
    created_at: options.createdAt || new Date().toISOString(),
  };
  document.geometry_hash = correctionGeometryHash(document);
  return document;
}

function finitePair(point) {
  return Array.isArray(point)
    && point.length === 2
    && point.every((value) => Number.isFinite(value));
}

function polygonBounds(polygon) {
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
  };
}

function rectilinearPolygon(polygon) {
  return polygon.every((point, index) => {
    const next = polygon[(index + 1) % polygon.length];
    return point[0] === next[0] || point[1] === next[1];
  });
}

function overlapArea(left, right) {
  const width = Math.max(0, Math.min(left.maxX, right.maxX) - Math.max(left.minX, right.minX));
  const height = Math.max(0, Math.min(left.maxY, right.maxY) - Math.max(left.minY, right.minY));
  return width * height;
}

function pointInPolygon(point, polygon) {
  let inside = false;
  for (let index = 0, previous = polygon.length - 1; index < polygon.length; previous = index, index += 1) {
    const [xi, yi] = polygon[index];
    const [xj, yj] = polygon[previous];
    const crosses = ((yi > point[1]) !== (yj > point[1]))
      && point[0] < ((xj - xi) * (point[1] - yi)) / Math.max(yj - yi, Number.EPSILON) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
}

function rectilinearIntersectionArea(left, right) {
  const xs = [...new Set([...left, ...right].map((point) => point[0]))].sort((a, b) => a - b);
  const ys = [...new Set([...left, ...right].map((point) => point[1]))].sort((a, b) => a - b);
  let area = 0;
  for (let xIndex = 0; xIndex < xs.length - 1; xIndex += 1) {
    for (let yIndex = 0; yIndex < ys.length - 1; yIndex += 1) {
      const middle = [
        (xs[xIndex] + xs[xIndex + 1]) / 2,
        (ys[yIndex] + ys[yIndex + 1]) / 2,
      ];
      if (pointInPolygon(middle, left) && pointInPolygon(middle, right)) {
        area += (xs[xIndex + 1] - xs[xIndex]) * (ys[yIndex + 1] - ys[yIndex]);
      }
    }
  }
  return area;
}

function requiredDoorWidth(opening, wall, roomById) {
  if (opening.role === "main_entrance") return FLOORPLAN_RULES.doors.entranceWidthMm;
  if (opening.role === "terrace_door") return FLOORPLAN_RULES.doors.terraceWidthMm;
  const adjacentRooms = wall.room_ids.map((roomId) => roomById.get(roomId)).filter(Boolean);
  if (adjacentRooms.some((room) => normalizedRoomRuleKey(room) === "wc")) {
    return FLOORPLAN_RULES.doors.smallWcWidthMm;
  }
  return FLOORPLAN_RULES.doors.internalWidthMm;
}

function openingInterval(opening, wall) {
  const length = Math.hypot(wall.end[0] - wall.start[0], wall.end[1] - wall.start[1]);
  const center = opening.position * length;
  return [center - opening.width / 2, center + opening.width / 2];
}

export function validateCorrectionDocument(document) {
  const errors = [];
  const warnings = [];
  if (document?.schema !== CORRECTION_SCHEMA) errors.push("invalid_schema");
  if (document?.rulebook_version !== FLOORPLAN_RULEBOOK_VERSION) errors.push("rulebook_version_mismatch");
  if (document?.building?.coordinate_unit !== "mm") errors.push("coordinate_unit_must_be_mm");
  if (!document?.source_annotation || document?.provenance?.source_mutated !== false) {
    errors.push("source_annotation_not_preserved");
  } else {
    const sourceHash = createHash("sha256").update(canonicalJson(document.source_annotation)).digest("hex");
    if (sourceHash !== document.source_annotation_sha256) errors.push("source_annotation_hash_mismatch");
  }
  for (const floor of document?.floors || []) {
    const wallIds = new Set((floor.walls || []).map((wall) => wall.id));
    const footprint = Array.isArray(floor.footprint) && floor.footprint.length >= 3
      ? floor.footprint
      : [];
    const footprintBox = footprint.every(finitePair) ? polygonBounds(footprint) : null;
    if (!footprintBox) errors.push(`floor_footprint_invalid:${floor.id}`);
    const roomEntries = [];
    const roomById = new Map();
    for (const room of floor.rooms || []) {
      if (
        !Array.isArray(room.polygon)
        || room.polygon.length < 3
        || !room.polygon.every(finitePair)
      ) {
        errors.push(`room_polygon_invalid:${floor.id}:${room.id}`);
        continue;
      }
      if (!rectilinearPolygon(room.polygon)) {
        errors.push(`room_polygon_not_rectilinear:${floor.id}:${room.id}`);
      }
      const roomBox = polygonBounds(room.polygon);
      roomEntries.push({ id: room.id, polygon: room.polygon, box: roomBox });
      roomById.set(room.id, room);
      if (
        footprintBox
        && (
          roomBox.minX < footprintBox.minX
          || roomBox.minY < footprintBox.minY
          || roomBox.maxX > footprintBox.maxX
          || roomBox.maxY > footprintBox.maxY
        )
      ) {
        errors.push(`room_outside_footprint:${floor.id}:${room.id}`);
      }
      if (!(Number(room.area_m2) > 0)) {
        errors.push(`room_area_invalid:${floor.id}:${room.id}`);
      }
      const ruleKey = normalizedRoomRuleKey(room);
      const areaRule = ruleKey ? FLOORPLAN_RULES.rooms[ruleKey] : null;
      if (areaRule?.minimumM2 && Number(room.area_m2) < areaRule.minimumM2) {
        errors.push(`room_area_below_minimum:${floor.id}:${room.id}:${areaRule.minimumM2}`);
      }
      if (areaRule?.maximumM2 && Number(room.area_m2) > areaRule.maximumM2) {
        errors.push(`room_area_above_maximum:${floor.id}:${room.id}:${areaRule.maximumM2}`);
      }
      if (
        areaRule?.preferredMinimumM2
        && (
          Number(room.area_m2) < areaRule.preferredMinimumM2
          || Number(room.area_m2) > areaRule.preferredMaximumM2
        )
      ) {
        warnings.push(`room_area_outside_preferred_range:${floor.id}:${room.id}:${areaRule.preferredMinimumM2}-${areaRule.preferredMaximumM2}`);
      }
      if (areaRule?.preferredM2 && Math.abs(Number(room.area_m2) - areaRule.preferredM2) > 0.5) {
        warnings.push(`room_area_outside_preferred_target:${floor.id}:${room.id}:${areaRule.preferredM2}`);
      }
    }
    for (let leftIndex = 0; leftIndex < roomEntries.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < roomEntries.length; rightIndex += 1) {
        if (
          overlapArea(roomEntries[leftIndex].box, roomEntries[rightIndex].box) > 0
          && rectilinearIntersectionArea(
            roomEntries[leftIndex].polygon,
            roomEntries[rightIndex].polygon,
          ) > FLOORPLAN_RULES.geometry.coverageToleranceMm2
        ) {
          errors.push(`room_overlap:${floor.id}:${roomEntries[leftIndex].id}:${roomEntries[rightIndex].id}`);
        }
      }
    }
    if (footprint.length) {
      const footprintAreaMm2 = polygonAreaMm2(footprint);
      const roomAreaMm2 = (floor.rooms || []).reduce(
        (sum, room) => sum + polygonAreaMm2(room.polygon),
        0,
      );
      if (footprintAreaMm2 - roomAreaMm2 > FLOORPLAN_RULES.geometry.coverageToleranceMm2) {
        errors.push(`room_coverage_gap:${floor.id}:${Math.round(footprintAreaMm2 - roomAreaMm2)}`);
      }
    }
    const wallKeys = new Set();
    for (const wall of floor.walls || []) {
      if (!finitePair(wall.start) || !finitePair(wall.end)) {
        errors.push(`wall_geometry_invalid:${floor.id}:${wall.id}`);
      } else if (wall.start[0] === wall.end[0] && wall.start[1] === wall.end[1]) {
        errors.push(`wall_zero_length:${floor.id}:${wall.id}`);
      } else {
        if (wall.start[0] !== wall.end[0] && wall.start[1] !== wall.end[1]) {
          errors.push(`wall_not_rectilinear:${floor.id}:${wall.id}`);
        }
        const endpoints = [wall.start.join(","), wall.end.join(",")].sort().join("|");
        if (wallKeys.has(endpoints)) errors.push(`wall_duplicate:${floor.id}:${wall.id}`);
        wallKeys.add(endpoints);
        const expectedThickness = wall.wall_type === "exterior"
          ? CORRECTION_DEFAULTS.exteriorWallMm
          : CORRECTION_DEFAULTS.interiorWallMm;
        if (wall.thickness !== expectedThickness) {
          warnings.push(`wall_thickness_non_default:${floor.id}:${wall.id}`);
        }
      }
    }
    const openingsByWall = new Map();
    for (const opening of floor.openings || []) {
      const wall = (floor.walls || []).find((candidate) => candidate.id === opening.wall_id);
      if (!wallIds.has(opening.wall_id) || !wall) errors.push(`opening_floating:${floor.id}:${opening.id}`);
      if (!(opening.position >= 0 && opening.position <= 1)) errors.push(`opening_outside_wall:${floor.id}:${opening.id}`);
      if (!(opening.width > 0)) errors.push(`opening_width_invalid:${floor.id}:${opening.id}`);
      if (wall) {
        const length = Math.hypot(wall.end[0] - wall.start[0], wall.end[1] - wall.start[1]);
        if (opening.width > length) errors.push(`opening_wider_than_wall:${floor.id}:${opening.id}`);
        const halfRatio = opening.width / Math.max(length, 1) / 2;
        if (opening.position - halfRatio < 0 || opening.position + halfRatio > 1) {
          errors.push(`opening_crosses_wall_end:${floor.id}:${opening.id}`);
        }
        const expectedConnects = wall.wall_type === "exterior"
          ? ["outside", ...wall.room_ids]
          : [...wall.room_ids];
        if (canonicalJson(opening.connects) !== canonicalJson(expectedConnects)) {
          errors.push(`opening_connections_mismatch:${floor.id}:${opening.id}`);
        }
        if (opening.opening_type === "door") {
          const expectedDoorWidth = requiredDoorWidth(opening, wall, roomById);
          if (opening.width !== expectedDoorWidth) {
            errors.push(`door_width_not_rulebook_default:${floor.id}:${opening.id}:${expectedDoorWidth}`);
          }
        }
        if (opening.opening_type === "window" && wall.wall_type !== "exterior") {
          errors.push(`window_not_on_exterior_wall:${floor.id}:${opening.id}`);
        }
        if (opening.role === "terrace_door") {
          if (opening.opening_type !== "door") errors.push(`terrace_door_type_invalid:${floor.id}:${opening.id}`);
          if (wall.wall_type !== "exterior") errors.push(`terrace_door_not_on_exterior_wall:${floor.id}:${opening.id}`);
          if (opening.traversable !== true) errors.push(`terrace_door_not_traversable:${floor.id}:${opening.id}`);
          if (opening.glazed !== true) errors.push(`terrace_door_not_glazed:${floor.id}:${opening.id}`);
          if (Number(opening.height_mm) < FLOORPLAN_RULES.doors.terraceMinimumHeightMm) {
            errors.push(`terrace_door_height_below_minimum:${floor.id}:${opening.id}`);
          }
          if (Number(opening.sill_height_mm) !== 0) errors.push(`terrace_door_sill_not_zero:${floor.id}:${opening.id}`);
        }
        const wallOpenings = openingsByWall.get(wall.id) || [];
        wallOpenings.push(opening);
        openingsByWall.set(wall.id, wallOpenings);
      }
      if (Number(opening.source_distance_to_wall_mm) > 500) {
        warnings.push(`opening_source_offset_review:${floor.id}:${opening.id}`);
      }
    }
    for (const [wallId, openings] of openingsByWall) {
      const wall = (floor.walls || []).find((candidate) => candidate.id === wallId);
      for (let leftIndex = 0; leftIndex < openings.length; leftIndex += 1) {
        for (let rightIndex = leftIndex + 1; rightIndex < openings.length; rightIndex += 1) {
          const left = openingInterval(openings[leftIndex], wall);
          const right = openingInterval(openings[rightIndex], wall);
          if (Math.min(left[1], right[1]) - Math.max(left[0], right[0]) > 0) {
            errors.push(`openings_overlap:${floor.id}:${openings[leftIndex].id}:${openings[rightIndex].id}`);
          }
        }
      }
    }
    for (const room of floor.rooms || []) {
      if (!isHabitableRoom(room)) continue;
      const glazingAreaM2 = (floor.openings || [])
        .filter((opening) =>
          (opening.opening_type === "window"
            || (opening.opening_type === "door" && opening.glazed === true))
          && Array.isArray(opening.connects)
          && opening.connects.includes(room.id)
        )
        .reduce((sum, opening) =>
          sum + (Number(opening.width) * Number(opening.height_mm || 0)) / 1_000_000
        , 0);
      const requiredM2 = Number(room.area_m2) * FLOORPLAN_RULES.windows.minimumGlazingToRoomAreaRatio;
      if (glazingAreaM2 + 0.001 < requiredM2) {
        errors.push(`window_area_below_one_tenth:${floor.id}:${room.id}:${glazingAreaM2.toFixed(2)}:${requiredM2.toFixed(2)}`);
      }
    }
  }
  const stair = document?.shared_stair_core;
  const stairRequired = (document?.floors?.length || 0) > 1;
  if (!stair && stairRequired) {
    errors.push("shared_stair_core_missing");
  } else if (stair) {
    if (stair.usable_width_mm < FLOORPLAN_RULES.stairs.project.minimumUsableWidthMm) {
      errors.push("stair_usable_width_below_900mm");
    }
    if (!Array.isArray(stair.polygon) || stair.polygon.length < 4 || !stair.polygon.every(finitePair)) {
      errors.push("stair_core_geometry_invalid");
    }
    if (!Array.isArray(stair.path) || stair.path.length < 2 || !stair.path.every(finitePair)) {
      errors.push("stair_path_invalid");
    }
    if (stair.direction !== "up") errors.push("stair_direction_not_up");
    if (!FLOORPLAN_RULES.stairs.reference.allowedPlanTypes.includes(stair.plan_type)) {
      errors.push("stair_plan_type_not_allowed");
    }
    if (stair.rulebook_version !== FLOORPLAN_RULEBOOK_VERSION) errors.push("stair_rulebook_version_mismatch");
    if (stair.reference_rules?.walkingZoneRatio !== FLOORPLAN_RULES.stairs.reference.walkingZoneRatio) {
      errors.push("stair_walking_zone_rule_mismatch");
    }
    if (!stair.tread_geometry_valid && stair.representation !== "clear_core_without_treads") {
      errors.push("stair_treads_visible_before_geometry_valid");
    }
    const geometry = stair.geometry;
    if (geometry?.riseMm > FLOORPLAN_RULES.stairs.project.maximumRiseMm) errors.push("stair_rise_exceeds_limit");
    if (geometry?.riseMm < FLOORPLAN_RULES.stairs.project.minimumRiseMm) errors.push("stair_rise_below_limit");
    if (geometry?.goingMm < FLOORPLAN_RULES.stairs.project.minimumGoingMm) errors.push("stair_going_below_limit");
    if (
      geometry?.stepMeasureMm < FLOORPLAN_RULES.stairs.project.stepMeasureMinimumMm
      || geometry?.stepMeasureMm > FLOORPLAN_RULES.stairs.project.stepMeasureMaximumMm
    ) errors.push("stair_step_measure_outside_range");
    if (geometry?.minimumHeadroomMm < FLOORPLAN_RULES.stairs.project.minimumHeadroomMm) {
      errors.push("stair_headroom_below_limit");
    }
    const floorIds = (document.floors || []).map((floor) => floor.id);
    if (canonicalJson(stair.floor_ids) !== canonicalJson(floorIds)) errors.push("stair_floor_interfaces_mismatch");
    if ((document.floors || []).some((floor) => floor.stair_core_id !== stair.id)) errors.push("stair_core_not_shared");
  }
  const allRooms = new Map((document.floors || []).flatMap((floor) =>
    (floor.rooms || []).map((room) => [room.id, { room, floor }])
  ));
  const graph = new Map([["outside", new Set()]]);
  const link = (left, right) => {
    if (!graph.has(left)) graph.set(left, new Set());
    if (!graph.has(right)) graph.set(right, new Set());
    graph.get(left).add(right);
    graph.get(right).add(left);
  };
  for (const floor of document.floors || []) {
    for (const room of floor.rooms || []) if (!graph.has(room.id)) graph.set(room.id, new Set());
    for (const opening of floor.openings || []) {
      if (opening.traversable && opening.connects?.length === 2) {
        link(opening.connects[0], opening.connects[1]);
      }
    }
  }
  const stairCirculation = [];
  if (stair?.polygon) {
    for (const floor of document.floors || []) {
      const candidates = (floor.rooms || []).filter((room) =>
        room.kind === "circulation"
        && rectilinearIntersectionArea(room.polygon, stair.polygon) > 0
      );
      if (!candidates.length) errors.push(`stair_not_connected_to_circulation:${floor.id}`);
      else stairCirculation.push(candidates[0].id);
    }
  }
  for (let index = 1; index < stairCirculation.length; index += 1) {
    link(stairCirculation[index - 1], stairCirculation[index]);
  }
  const reached = new Set(["outside"]);
  const queue = ["outside"];
  while (queue.length) {
    const current = queue.shift();
    for (const neighbor of graph.get(current) || []) {
      if (!reached.has(neighbor)) {
        reached.add(neighbor);
        queue.push(neighbor);
      }
    }
  }
  for (const [roomId] of allRooms) {
    if (!reached.has(roomId)) errors.push(`room_unreachable_from_entrance:${roomId}`);
  }
  if (document?.rights?.usage_scope === DEFAULT_RIGHTS) warnings.push("internal_reference_only");
  if (document?.rights?.decision === "undecided") warnings.push("rights_decision_required_for_wordpress");
  const calculatedHash = correctionGeometryHash(document);
  if (document?.geometry_hash && document.geometry_hash !== calculatedHash) errors.push("geometry_hash_mismatch");
  return {
    valid: errors.length === 0,
    errors,
    warnings,
    geometry_hash: calculatedHash,
    hard_checks: {
      source_annotation_preserved: !errors.some((error) => error.startsWith("source_annotation_")),
      wall_linked_openings: !errors.some((error) => error.startsWith("opening_")),
      rooms_rectilinear_and_contained: !errors.some((error) =>
        error.startsWith("room_polygon_")
        || error.startsWith("room_outside_")
        || error.startsWith("room_overlap:")
      ),
      unique_rectilinear_walls: !errors.some((error) =>
        error.startsWith("wall_not_rectilinear")
        || error.startsWith("wall_duplicate")
      ),
      shared_stair_core: !errors.some((error) => error.startsWith("stair_")),
      usable_stair_width_900mm: !errors.includes("stair_usable_width_below_900mm"),
      geometry_hash_matches: !errors.includes("geometry_hash_mismatch"),
    },
  };
}

export function withUpdatedHash(document) {
  const copy = structuredClone(document);
  for (const floor of copy.floors || []) {
    mergeCollinearWalls(floor);
    for (const room of floor.rooms || []) {
      room.area_m2 = polygonAreaM2(room.polygon);
    }
  }
  copy.geometry_hash = correctionGeometryHash(copy);
  return copy;
}

export function createEditorHistory(source) {
  return { source: structuredClone(source), past: [], present: structuredClone(source), future: [] };
}

export function commitEditorHistory(history, next) {
  return {
    source: history.source,
    past: [...history.past, history.present],
    present: withUpdatedHash(next),
    future: [],
  };
}

export function undoEditorHistory(history) {
  if (!history.past.length) return history;
  return {
    source: history.source,
    past: history.past.slice(0, -1),
    present: history.past.at(-1),
    future: [history.present, ...history.future],
  };
}

export function redoEditorHistory(history) {
  if (!history.future.length) return history;
  return {
    source: history.source,
    past: [...history.past, history.present],
    present: history.future[0],
    future: history.future.slice(1),
  };
}

export function resetEditorHistory(history) {
  return {
    source: history.source,
    past: [...history.past, history.present],
    present: structuredClone(history.source),
    future: [],
  };
}
