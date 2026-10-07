export const STOREY_MODEL_VERSION = "zf-storey-model-v1";

export const DEFAULT_STOREY_CONFIG = Object.freeze({
  stair: Object.freeze({
    clearWidthMm: 900,
    minimumClearWidthMm: 800,
    maximumRiseMm: 200,
    minimumRiseMm: 140,
    minimumGoingMm: 260,
    minimumHeadroomMm: 2000,
    minimumLandingDepthMm: 800,
    halfTurnGapMm: 300,
    stepMeasureMinimumMm: 590,
    stepMeasureOptimumMm: 630,
    stepMeasureMaximumMm: 650,
  }),
  roof: Object.freeze({
    pitchMinimumDeg: 35,
    pitchMaximumDeg: 48,
    kneeWallMinimumMm: 0,
    kneeWallMaximumMm: 1500,
    fullAreaHeadroomMm: 2000,
    halfAreaHeadroomMm: 1000,
    habitableHeadroomMm: 2300,
    habitableAreaShare: 0.5,
  }),
});

const STOREY_TYPE_ALIASES = new Map([
  ["1_storey", "1_storey"],
  ["bungalow", "1_storey"],
  ["1", "1_storey"],
  ["1_5_storey", "1_5_storey"],
  ["onehalfstorey", "1_5_storey"],
  ["one_and_half_storeys", "1_5_storey"],
  ["1.5", "1_5_storey"],
  ["1,5", "1_5_storey"],
  ["2_storey", "2_storey"],
  ["twostorey", "2_storey"],
  ["two_storeys", "2_storey"],
  ["2", "2_storey"],
]);

function finiteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function rounded(value, digits = 3) {
  return Number(value.toFixed(digits));
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function mergeConfig(overrides = {}) {
  return {
    stair: {
      ...DEFAULT_STOREY_CONFIG.stair,
      ...(overrides.stair ?? overrides),
    },
    roof: {
      ...DEFAULT_STOREY_CONFIG.roof,
      ...(overrides.roof ?? {}),
    },
  };
}

export function canonicalStoreyType(value) {
  return STOREY_TYPE_ALIASES.get(String(value ?? "").trim().toLowerCase()) ?? null;
}

export function expectedStoreyCount(storeyType) {
  const canonical = canonicalStoreyType(storeyType);
  if (canonical === "1_storey") return 1;
  if (canonical === "1_5_storey" || canonical === "2_storey") return 2;
  return null;
}

export function storeyTypeForReferenceProject(project) {
  const explicit = canonicalStoreyType(project?.house_type);
  if (explicit) return explicit;
  const floors = Array.isArray(project?.floors)
    ? project.floors.filter((floor) => floor?.floor_level !== "basement")
    : [];
  return floors.length <= 1 ? "1_storey" : "2_storey";
}

export function solveStairGeometry(floorToFloorMm, options = {}) {
  const config = mergeConfig(options).stair;
  const height = finiteNumber(floorToFloorMm);
  const requestedType = options.type === "straight" ? "straight" : "half_turn";
  const clearWidthMm = Math.max(
    config.minimumClearWidthMm,
    finiteNumber(options.clearWidthMm) ?? config.clearWidthMm,
  );
  if (height === null || height <= 0) {
    return {
      ok: false,
      reason: "invalid_floor_to_floor_height",
      floorToFloorMm,
    };
  }

  const minimumRisers = Math.ceil(height / config.maximumRiseMm);
  const maximumRisers = Math.floor(height / config.minimumRiseMm);
  const candidates = [];
  for (let riserCount = minimumRisers; riserCount <= maximumRisers; riserCount += 1) {
    const riseMm = height / riserCount;
    const idealGoing = config.stepMeasureOptimumMm - 2 * riseMm;
    const goingMm = Math.ceil(
      Math.max(config.minimumGoingMm, idealGoing) / 5,
    ) * 5;
    const stepMeasureMm = 2 * riseMm + goingMm;
    if (
      riseMm > config.maximumRiseMm ||
      goingMm < config.minimumGoingMm ||
      stepMeasureMm < config.stepMeasureMinimumMm ||
      stepMeasureMm > config.stepMeasureMaximumMm
    ) {
      continue;
    }
    candidates.push({
      riserCount,
      riseMm,
      goingMm,
      stepMeasureMm,
      score:
        Math.abs(stepMeasureMm - config.stepMeasureOptimumMm) +
        Math.abs(riseMm - 175) * 0.2,
    });
  }

  candidates.sort((left, right) =>
    left.score - right.score ||
    Math.abs(left.riseMm - 175) - Math.abs(right.riseMm - 175) ||
    left.riserCount - right.riserCount
  );
  const selected = candidates[0];
  if (!selected) {
    return {
      ok: false,
      reason: "no_compliant_rise_going_solution",
      floorToFloorMm: height,
    };
  }

  const landingDepthMm = Math.max(
    clearWidthMm,
    config.minimumLandingDepthMm,
    finiteNumber(options.landingDepthMm) ?? 0,
  );
  const flightRisers = requestedType === "straight"
    ? [selected.riserCount]
    : [
        Math.ceil(selected.riserCount / 2),
        Math.floor(selected.riserCount / 2),
      ];
  const flightRunsMm = flightRisers.map((risers) =>
    Math.max(0, risers - 1) * selected.goingMm
  );
  const footprint = requestedType === "straight"
    ? {
        widthMm: clearWidthMm,
        lengthMm: flightRunsMm[0],
      }
    : {
        widthMm: clearWidthMm * 2 + config.halfTurnGapMm,
        lengthMm: Math.max(...flightRunsMm) + landingDepthMm,
      };

  return {
    ok: true,
    type: requestedType,
    floorToFloorMm: height,
    riserCount: selected.riserCount,
    riseMm: rounded(selected.riseMm, 2),
    goingMm: rounded(selected.goingMm, 2),
    stepMeasureMm: rounded(selected.stepMeasureMm, 2),
    clearWidthMm,
    landingDepthMm,
    minimumHeadroomMm: config.minimumHeadroomMm,
    flightRisers,
    flightRunsMm,
    footprint,
  };
}

export function headroomDistanceMm(heightMm, roof) {
  const targetHeight = finiteNumber(heightMm);
  const kneeWallMm = finiteNumber(roof?.kneeWallMm);
  const pitchDeg = finiteNumber(roof?.pitchDeg);
  if (
    targetHeight === null ||
    kneeWallMm === null ||
    pitchDeg === null ||
    pitchDeg <= 0 ||
    pitchDeg >= 90
  ) {
    throw new Error("Roof height calculation requires finite height, knee wall, and pitch.");
  }
  if (targetHeight <= kneeWallMm) return 0;
  return (targetHeight - kneeWallMm) / Math.tan(pitchDeg * Math.PI / 180);
}

function widthAtHeadroom(buildingWidthMm, heightMm, roof) {
  const distance = Math.max(0, headroomDistanceMm(heightMm, roof));
  return clamp(buildingWidthMm - 2 * distance, 0, buildingWidthMm);
}

export function roofAreaBands(input, overrides = {}) {
  const config = mergeConfig(overrides).roof;
  const width = finiteNumber(input?.buildingWidthMm);
  const length = finiteNumber(input?.buildingLengthMm);
  if (width === null || width <= 0 || length === null || length <= 0) {
    throw new Error("Roof area bands require positive building width and length.");
  }
  const roof = input.roof;
  const fullWidth = widthAtHeadroom(width, config.fullAreaHeadroomMm, roof);
  const halfOrFullWidth = widthAtHeadroom(width, config.halfAreaHeadroomMm, roof);
  const physicalAreaM2 = width * length / 1_000_000;
  const fullAreaM2 = fullWidth * length / 1_000_000;
  const halfAreaM2 = Math.max(0, halfOrFullWidth - fullWidth) * length / 1_000_000;
  const zeroAreaM2 = Math.max(0, width - halfOrFullWidth) * length / 1_000_000;
  return {
    physicalAreaM2: rounded(physicalAreaM2),
    fullAreaM2: rounded(fullAreaM2),
    halfAreaM2: rounded(halfAreaM2),
    zeroAreaM2: rounded(zeroAreaM2),
    wohnflaecheM2: rounded(fullAreaM2 + halfAreaM2 * 0.5),
    fullWidthMm: rounded(fullWidth),
    halfOrFullWidthMm: rounded(halfOrFullWidth),
  };
}

export function polygonArea(points) {
  if (!Array.isArray(points) || points.length < 3) return 0;
  let total = 0;
  for (let index = 0; index < points.length; index += 1) {
    const next = (index + 1) % points.length;
    total += points[index][0] * points[next][1] - points[next][0] * points[index][1];
  }
  return Math.abs(total) / 2;
}

function clipAgainstAxis(points, axisIndex, boundary, keepGreater) {
  const output = [];
  for (let index = 0; index < points.length; index += 1) {
    const current = points[index];
    const previous = points[(index + points.length - 1) % points.length];
    const currentInside = keepGreater
      ? current[axisIndex] >= boundary
      : current[axisIndex] <= boundary;
    const previousInside = keepGreater
      ? previous[axisIndex] >= boundary
      : previous[axisIndex] <= boundary;
    if (currentInside !== previousInside) {
      const denominator = current[axisIndex] - previous[axisIndex];
      const ratio = denominator === 0 ? 0 : (boundary - previous[axisIndex]) / denominator;
      output.push([
        previous[0] + (current[0] - previous[0]) * ratio,
        previous[1] + (current[1] - previous[1]) * ratio,
      ]);
    }
    if (currentInside) output.push(current);
  }
  return output;
}

export function clipPolygonToHeadroomBand(points, input) {
  const axisIndex = input.axis === "x" ? 0 : 1;
  const envelopeMinimum = finiteNumber(input.envelopeMinimumMm) ?? 0;
  const envelopeMaximum = finiteNumber(input.envelopeMaximumMm);
  if (envelopeMaximum === null || envelopeMaximum <= envelopeMinimum) return [];
  const distance = Math.max(0, headroomDistanceMm(input.heightMm, input.roof));
  const minimum = envelopeMinimum + distance;
  const maximum = envelopeMaximum - distance;
  if (maximum <= minimum) return [];
  const lowerClipped = clipAgainstAxis(points, axisIndex, minimum, true);
  return lowerClipped.length
    ? clipAgainstAxis(lowerClipped, axisIndex, maximum, false)
    : [];
}

export function roomRoofHeadroomReport(input, overrides = {}) {
  const config = mergeConfig(overrides).roof;
  const points = Array.isArray(input?.polygon) ? input.polygon : [];
  const physicalAreaMm2 = polygonArea(points);
  if (physicalAreaMm2 <= 0) {
    throw new Error("Room headroom calculation requires a valid room polygon.");
  }
  const areaAtLeast = (heightMm) => polygonArea(
    clipPolygonToHeadroomBand(points, {
      ...input,
      heightMm,
    }),
  );
  const fullAreaMm2 = areaAtLeast(config.fullAreaHeadroomMm);
  const atLeastHalfAreaMm2 = areaAtLeast(config.halfAreaHeadroomMm);
  const habitableAreaMm2 = areaAtLeast(config.habitableHeadroomMm);
  const halfAreaMm2 = Math.max(0, atLeastHalfAreaMm2 - fullAreaMm2);
  const zeroAreaMm2 = Math.max(0, physicalAreaMm2 - atLeastHalfAreaMm2);
  const habitableShare = habitableAreaMm2 / physicalAreaMm2;
  return {
    physicalAreaM2: rounded(physicalAreaMm2 / 1_000_000),
    fullAreaM2: rounded(fullAreaMm2 / 1_000_000),
    halfAreaM2: rounded(halfAreaMm2 / 1_000_000),
    zeroAreaM2: rounded(zeroAreaMm2 / 1_000_000),
    wohnflaecheM2: rounded((fullAreaMm2 + halfAreaMm2 * 0.5) / 1_000_000),
    habitableAreaShare: rounded(habitableShare, 4),
    qualifiesAsHabitableRoom: habitableShare >= config.habitableAreaShare,
  };
}

function pointList(value) {
  return Array.isArray(value)
    ? value
        .filter((point) =>
          Array.isArray(point) &&
          point.length >= 2 &&
          Number.isFinite(Number(point[0])) &&
          Number.isFinite(Number(point[1]))
        )
        .map((point) => [Number(point[0]), Number(point[1])])
    : [];
}

function pointListsEqual(left, right) {
  return left.length === right.length &&
    left.every((point, index) =>
      point[0] === right[index][0] && point[1] === right[index][1]
    );
}

function stairFootprintFromPath(path, padding = 0.04) {
  if (path.length < 2) return [];
  const xs = path.map((point) => point[0]);
  const ys = path.map((point) => point[1]);
  const minimumX = Math.min(...xs) - padding;
  const maximumX = Math.max(...xs) + padding;
  const minimumY = Math.min(...ys) - padding;
  const maximumY = Math.max(...ys) + padding;
  return [
    [minimumX, minimumY],
    [maximumX, minimumY],
    [maximumX, maximumY],
    [minimumX, maximumY],
  ];
}

export function referenceGeometryFingerprint(project) {
  return JSON.stringify(
    (project?.floors ?? []).map((floor) => ({
      floor_level: floor.floor_level,
      rooms: floor.rooms ?? floor.annotations ?? [],
      elements: floor.elements ?? [],
    })),
  );
}

export function migrateReferenceProjectToStoreyTemplate(project) {
  const floors = Array.isArray(project?.floors) ? project.floors : [];
  const habitableFloors = floors.filter((floor) => floor?.floor_level !== "basement");
  const storeyType = storeyTypeForReferenceProject(project);
  const groundFloor = habitableFloors.find((floor) => floor.floor_level === "groundfloor")
    ?? habitableFloors[0];
  const groundStair = (groundFloor?.elements ?? []).find((element) => element.type === "stairs");
  const groundStairPath = pointList(groundStair?.points);
  const stairCore = habitableFloors.length > 1 && groundStairPath.length >= 2
    ? {
        anchor: groundStairPath[0],
        footprint: stairFootprintFromPath(groundStairPath),
        type: groundStairPath.length === 2
          ? "straight"
          : groundStairPath.length === 3
            ? "quarter_turn"
            : "half_turn",
        flightDirection: [
          groundStairPath.at(-1)[0] - groundStairPath[0][0],
          groundStairPath.at(-1)[1] - groundStairPath[0][1],
        ],
        source: "legacy_normalized_annotation",
        dimensionStatus: "scale_required",
      }
    : undefined;

  const storeys = habitableFloors.map((floor, index) => {
    const stair = (floor.elements ?? []).find((element) => element.type === "stairs");
    const stairPath = pointList(stair?.points);
    return {
      level: index,
      sourceFloorLevel: floor.floor_level,
      envelope: null,
      rooms: structuredClone(floor.rooms ?? floor.annotations ?? []),
      walls: [],
      elements: structuredClone(floor.elements ?? []),
      floorToFloorMm: null,
      slabOpenings: stairPath.length >= 2
        ? [stairFootprintFromPath(stairPath)]
        : [],
    };
  });

  const issues = [];
  if (habitableFloors.length !== expectedStoreyCount(storeyType)) {
    issues.push("storey_count_conflicts_with_house_type");
  }
  if (habitableFloors.length > 1 && !stairCore) {
    issues.push("shared_stair_core_missing");
  }
  if (stairCore) {
    for (const storey of storeys.slice(1)) {
      const opening = storey.slabOpenings[0] ?? [];
      if (!pointListsEqual(stairCore.footprint, opening)) {
        issues.push(`stair_core_misaligned_on_level_${storey.level}`);
      }
    }
  }
  if (storeyType === "1_5_storey") {
    issues.push("roof_geometry_requires_scale_and_human_confirmation");
  }

  return {
    id: String(project?.project_id ?? ""),
    name: String(project?.project_id ?? "Unbenanntes Referenzprojekt"),
    storeyType,
    storeys,
    excludedStoreys: floors
      .filter((floor) => floor?.floor_level === "basement")
      .map((floor) => structuredClone(floor)),
    stairCore,
    roof: undefined,
    legacySource: {
      floors: structuredClone(floors),
    },
    migration: {
      sourceSchema: "simplifier-annotations-v1",
      geometryChanged: false,
      requiresReview: issues.length > 0,
      issues,
    },
  };
}

export function validateStoreyTemplate(template, overrides = {}) {
  const config = mergeConfig(overrides);
  const errors = [];
  const warnings = [];
  const storeyType = canonicalStoreyType(template?.storeyType);
  const storeys = Array.isArray(template?.storeys) ? template.storeys : [];
  if (!storeyType) errors.push("unknown_storey_type");
  const expectedCount = expectedStoreyCount(storeyType);
  if (expectedCount !== null && storeys.length !== expectedCount) {
    errors.push("storey_count_mismatch");
  }

  if (storeyType === "1_storey" && template?.stairCore) {
    errors.push("single_storey_must_not_have_stair_core");
  }
  if (expectedCount > 1) {
    const coreFootprint = pointList(template?.stairCore?.footprint);
    if (coreFootprint.length < 3 || polygonArea(coreFootprint) <= 0) {
      errors.push("shared_stair_core_missing");
    } else {
      for (const storey of storeys.slice(1)) {
        const openings = Array.isArray(storey?.slabOpenings)
          ? storey.slabOpenings.map(pointList)
          : [];
        if (!openings.some((opening) => pointListsEqual(opening, coreFootprint))) {
          errors.push(`stair_opening_mismatch_level_${storey?.level ?? "unknown"}`);
        }
      }
    }
    const stairGeometry = template?.stairCore?.geometry;
    if (!stairGeometry?.ok) {
      errors.push("compliant_stair_geometry_missing");
    } else {
      if (stairGeometry.riseMm > config.stair.maximumRiseMm) {
        errors.push("stair_rise_exceeds_limit");
      }
      if (stairGeometry.goingMm < config.stair.minimumGoingMm) {
        errors.push("stair_going_below_limit");
      }
      if (
        stairGeometry.stepMeasureMm < config.stair.stepMeasureMinimumMm ||
        stairGeometry.stepMeasureMm > config.stair.stepMeasureMaximumMm
      ) {
        errors.push("stair_step_measure_outside_range");
      }
      if (stairGeometry.availableHeadroomMm < config.stair.minimumHeadroomMm) {
        errors.push("stair_headroom_below_limit");
      }
    }
  }

  if (storeyType === "1_5_storey") {
    const pitch = finiteNumber(template?.roof?.pitchDeg);
    const kneeWall = finiteNumber(template?.roof?.kneeWallMm);
    if (
      !template?.roof ||
      !["gable", "hip"].includes(template.roof.form) ||
      pitch === null ||
      kneeWall === null
    ) {
      errors.push("roof_geometry_missing");
    } else {
      if (pitch < config.roof.pitchMinimumDeg || pitch > config.roof.pitchMaximumDeg) {
        errors.push("roof_pitch_outside_configured_range");
      }
      if (
        kneeWall < config.roof.kneeWallMinimumMm ||
        kneeWall > config.roof.kneeWallMaximumMm
      ) {
        errors.push("knee_wall_outside_configured_range");
      }
      if (template.roof.ridgeAxis !== "long_side") {
        errors.push("ridge_axis_must_follow_long_side");
      }
    }
    const upperStorey = storeys[1];
    for (const room of upperStorey?.rooms ?? []) {
      const isBedroom = room?.type === "bedroom" ||
        /schlaf|eltern|kind|zimmer/i.test(String(room?.label ?? room?.name ?? ""));
      if (isBedroom && room?.headroom?.qualifiesAsHabitableRoom !== true) {
        errors.push(`roof_bedroom_headroom_failed:${room?.id ?? room?.room_id ?? "unknown"}`);
      }
    }
  }

  if (template?.migration?.requiresReview) {
    warnings.push(...(template.migration.issues ?? []));
  }
  return {
    schema: "zf-storey-validation-v1",
    passed: errors.length === 0,
    errors: [...new Set(errors)],
    warnings: [...new Set(warnings)],
  };
}
