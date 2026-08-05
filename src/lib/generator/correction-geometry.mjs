import {
  FLOORPLAN_RULEBOOK_VERSION,
  FLOORPLAN_RULES,
  normalizedRoomRuleKey,
} from "./floorplan-rulebook.mjs";

export const CORRECTION_DEFAULTS = Object.freeze({
  exteriorWallMm: FLOORPLAN_RULES.walls.exteriorThicknessMm,
  interiorWallMm: FLOORPLAN_RULES.walls.interiorThicknessMm,
  internalDoorMm: FLOORPLAN_RULES.doors.internalWidthMm,
  smallWcDoorMm: FLOORPLAN_RULES.doors.smallWcWidthMm,
  entranceDoorMm: FLOORPLAN_RULES.doors.entranceWidthMm,
  stairWidthMm: FLOORPLAN_RULES.stairs.project.usableWidthMm,
  sourceAxisSnapTolerancePx: FLOORPLAN_RULES.geometry.sourceAxisSnapTolerancePx,
  editSnapMm: FLOORPLAN_RULES.geometry.editSnapMm,
});

function rounded(value) {
  return Math.round(Number(value) || 0);
}

function finitePoint(point) {
  return Array.isArray(point)
    && point.length >= 2
    && Number.isFinite(point[0])
    && Number.isFinite(point[1]);
}

function roomSourcePolygon(room) {
  if (Array.isArray(room.polygon) && room.polygon.length >= 3) {
    return room.polygon.map((point) => [Number(point.x), Number(point.y)]);
  }
  return [
    [Number(room.x), Number(room.y)],
    [Number(room.x + room.width), Number(room.y)],
    [Number(room.x + room.width), Number(room.y + room.height)],
    [Number(room.x), Number(room.y + room.height)],
  ];
}

function pointsBounds(points) {
  const valid = points.filter(finitePoint);
  const xs = valid.map((point) => point[0]);
  const ys = valid.map((point) => point[1]);
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
    width: Math.max(...xs) - Math.min(...xs),
    height: Math.max(...ys) - Math.min(...ys),
  };
}

function axisSnapper(values, tolerance) {
  const groups = [];
  [...values].sort((left, right) => left - right).forEach((value) => {
    const group = groups.find((candidate) => {
      const center = candidate.reduce((sum, item) => sum + item, 0) / candidate.length;
      return Math.abs(center - value) <= tolerance;
    });
    if (group) group.push(value);
    else groups.push([value]);
  });
  const centers = groups.map((group) =>
    group.reduce((sum, value) => sum + value, 0) / group.length
  );
  return (value) => centers.reduce(
    (best, center) =>
      Math.abs(center - value) < Math.abs(best - value) ? center : best,
    centers[0] ?? value,
  );
}

function cleanedRectilinearPolygon(points) {
  const unique = points.filter((point, index) => {
    const previous = points[(index - 1 + points.length) % points.length];
    return point[0] !== previous[0] || point[1] !== previous[1];
  });
  const cleaned = unique.filter((point, index) => {
    const previous = unique[(index - 1 + unique.length) % unique.length];
    const next = unique[(index + 1) % unique.length];
    return !(
      (previous[0] === point[0] && point[0] === next[0])
      || (previous[1] === point[1] && point[1] === next[1])
    );
  });
  const rectilinear = cleaned.length >= 4 && cleaned.every((point, index) => {
    const next = cleaned[(index + 1) % cleaned.length];
    return point[0] === next[0] || point[1] === next[1];
  });
  if (rectilinear) return cleaned;
  const box = pointsBounds(points);
  return [
    [box.minX, box.minY],
    [box.maxX, box.minY],
    [box.maxX, box.maxY],
    [box.minX, box.maxY],
  ];
}

function rectifiedSourceRooms(floor) {
  const source = floor.rooms.map((room) => {
    const polygon = roomSourcePolygon(room);
    return { room, polygon, box: pointsBounds(polygon) };
  });
  const snapX = axisSnapper(
    source.flatMap(({ polygon }) => polygon.map((point) => point[0])),
    CORRECTION_DEFAULTS.sourceAxisSnapTolerancePx,
  );
  const snapY = axisSnapper(
    source.flatMap(({ polygon }) => polygon.map((point) => point[1])),
    CORRECTION_DEFAULTS.sourceAxisSnapTolerancePx,
  );
  const rectified = source.map(({ room, polygon }) => {
    const snapped = polygon.map(([x, y]) => [snapX(x), snapY(y)]);
    return {
      room,
      polygon: cleanedRectilinearPolygon(snapped),
    };
  });
  for (let leftIndex = 0; leftIndex < rectified.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < rectified.length; rightIndex += 1) {
      if (
        rectified[leftIndex].polygon.length !== 4
        || rectified[rightIndex].polygon.length !== 4
      ) continue;
      const left = pointsBounds(rectified[leftIndex].polygon);
      const right = pointsBounds(rectified[rightIndex].polygon);
      const overlapX = Math.min(left.maxX, right.maxX) - Math.max(left.minX, right.minX);
      const overlapY = Math.min(left.maxY, right.maxY) - Math.max(left.minY, right.minY);
      if (overlapX <= 0 || overlapY <= 0) continue;
      if (overlapY <= overlapX) {
        const leftAbove = (left.minY + left.maxY) / 2 <= (right.minY + right.maxY) / 2;
        const upper = leftAbove ? rectified[leftIndex] : rectified[rightIndex];
        const lower = leftAbove ? rectified[rightIndex] : rectified[leftIndex];
        const upperBox = leftAbove ? left : right;
        const lowerBox = leftAbove ? right : left;
        const boundary = (upperBox.maxY + lowerBox.minY) / 2;
        upper.polygon = upper.polygon.map(([x, y]) => [x, y === upperBox.maxY ? boundary : y]);
        lower.polygon = lower.polygon.map(([x, y]) => [x, y === lowerBox.minY ? boundary : y]);
      } else {
        const leftFirst = (left.minX + left.maxX) / 2 <= (right.minX + right.maxX) / 2;
        const west = leftFirst ? rectified[leftIndex] : rectified[rightIndex];
        const east = leftFirst ? rectified[rightIndex] : rectified[leftIndex];
        const westBox = leftFirst ? left : right;
        const eastBox = leftFirst ? right : left;
        const boundary = (westBox.maxX + eastBox.minX) / 2;
        west.polygon = west.polygon.map(([x, y]) => [x === westBox.maxX ? boundary : x, y]);
        east.polygon = east.polygon.map(([x, y]) => [x === eastBox.minX ? boundary : x, y]);
      }
    }
  }
  return rectified;
}

function sourceFloorTransform(variant, floor, rectified) {
  const fallback = pointsBounds(rectified.flatMap((entry) => entry.polygon));
  const source = floor.referenceFootprint
    ? {
        minX: floor.referenceFootprint.x,
        minY: floor.referenceFootprint.y,
        width: floor.referenceFootprint.width,
        height: floor.referenceFootprint.height,
      }
    : fallback;
  const widthMm = Math.max(1000, rounded(Number(variant.metrics.footprintWidthM) * 1000));
  const depthMm = Math.max(1000, rounded(Number(variant.metrics.footprintDepthM) * 1000));
  const scaleX = widthMm / Math.max(source.width, 0.001);
  const scaleY = depthMm / Math.max(source.height, 0.001);
  return {
    widthMm,
    depthMm,
    point(point) {
      const sourcePoint = Array.isArray(point)
        ? point
        : [Number(point.x), Number(point.y)];
      return [
        rounded((sourcePoint[0] - source.minX) * scaleX),
        rounded((sourcePoint[1] - source.minY) * scaleY),
      ];
    },
  };
}

function snapToFootprintBoundary(point, transform) {
  const threshold = FLOORPLAN_RULES.geometry.footprintBoundarySnapMm;
  const snap = (value, maximum) => {
    if (Math.abs(value) <= threshold) return 0;
    if (Math.abs(maximum - value) <= threshold) return maximum;
    return value;
  };
  return [
    snap(point[0], transform.widthMm),
    snap(point[1], transform.depthMm),
  ];
}

// Raw, unrounded polygon area in mm^2. Kept separate from polygonAreaM2()
// below (which rounds to 2 decimal places for display/storage as room.area_m2)
// because summing several already-rounded room areas and comparing against a
// footprint can accumulate up to ~5,000mm^2 of rounding error per room. With
// five or six rooms sharing one footprint that easily exceeds the 10,000mm^2
// coverage tolerance and flags a false-positive room_coverage_gap even when
// the rooms tile the footprint exactly. Callers that need an exact area
// comparison (coverage checks) should use this instead of polygonAreaM2.
export function polygonAreaMm2(polygon) {
  if (!Array.isArray(polygon) || polygon.length < 3) return 0;
  const twiceArea = polygon.reduce((sum, point, index) => {
    const next = polygon[(index + 1) % polygon.length];
    return sum + point[0] * next[1] - next[0] * point[1];
  }, 0);
  return Math.abs(twiceArea) / 2;
}

export function polygonAreaM2(polygon) {
  return Number((polygonAreaMm2(polygon) / 1_000_000).toFixed(2));
}

function enforceHwrAreaAndCloseAdjacentGap(rooms) {
  const hwr = rooms.find((room) => normalizedRoomRuleKey(room) === "hwrHtr");
  if (!hwr || hwr.polygon.length !== 4) return;
  const box = pointsBounds(hwr.polygon);
  const targetAreaM2 = (
    FLOORPLAN_RULES.rooms.hwrHtr.minimumM2
    + FLOORPLAN_RULES.rooms.hwrHtr.maximumM2
  ) / 2;
  const targetTop = rounded(box.maxY - (targetAreaM2 * 1_000_000) / Math.max(box.width, 1));
  if (targetTop >= box.minY || targetTop < 0) return;
  let best = null;
  for (const room of rooms) {
    if (room.id === hwr.id) continue;
    for (let index = 0; index < room.polygon.length; index += 1) {
      const start = room.polygon[index];
      const end = room.polygon[(index + 1) % room.polygon.length];
      if (start[1] !== end[1] || start[1] > box.minY) continue;
      const overlap = Math.min(Math.max(start[0], end[0]), box.maxX)
        - Math.max(Math.min(start[0], end[0]), box.minX);
      if (overlap <= box.width * 0.75) continue;
      const distance = box.minY - start[1];
      if (!best || distance < best.distance) best = { room, index, distance };
    }
  }
  hwr.polygon = hwr.polygon.map(([x, y]) => [x, y === box.minY ? targetTop : y]);
  hwr.area_m2 = polygonAreaM2(hwr.polygon);
  if (best) {
    const nextIndex = (best.index + 1) % best.room.polygon.length;
    best.room.polygon[best.index][1] = targetTop;
    best.room.polygon[nextIndex][1] = targetTop;
    best.room.area_m2 = polygonAreaM2(best.room.polygon);
  }
}

function polygonSegments(polygon, extra) {
  return polygon.map((start, index) => {
    const end = polygon[(index + 1) % polygon.length];
    const horizontal = start[1] === end[1];
    return {
      axis: horizontal ? "h" : "v",
      coordinate: horizontal ? start[1] : start[0],
      from: horizontal ? Math.min(start[0], end[0]) : Math.min(start[1], end[1]),
      to: horizontal ? Math.max(start[0], end[0]) : Math.max(start[1], end[1]),
      ...extra,
    };
  }).filter((segment) => segment.to > segment.from);
}

function segmentSignature(segment) {
  return [
    segment.wall_type,
    [...segment.room_ids].sort().join(","),
  ].join("|");
}

function mergeAdjacentSegments(segments) {
  const merged = [];
  for (const segment of segments) {
    const previous = merged.at(-1);
    if (
      previous
      && previous.axis === segment.axis
      && previous.coordinate === segment.coordinate
      && previous.to === segment.from
      && segmentSignature(previous) === segmentSignature(segment)
    ) {
      previous.to = segment.to;
    } else {
      merged.push({ ...segment });
    }
  }
  return merged;
}

export function wallsForMillimetreRooms(rooms, footprint, floorIndex) {
  const sourceSegments = [
    ...polygonSegments(footprint, { exterior: true, room_id: null }),
    ...rooms.flatMap((room) =>
      polygonSegments(room.polygon, { exterior: false, room_id: room.id })
    ),
  ];
  const groups = new Map();
  for (const segment of sourceSegments) {
    const key = `${segment.axis}:${segment.coordinate}`;
    const group = groups.get(key) || [];
    group.push(segment);
    groups.set(key, group);
  }
  const atomic = [];
  for (const group of groups.values()) {
    const breakpoints = [...new Set(group.flatMap((segment) => [segment.from, segment.to]))]
      .sort((left, right) => left - right);
    for (let index = 0; index < breakpoints.length - 1; index += 1) {
      const from = breakpoints[index];
      const to = breakpoints[index + 1];
      const midpoint = (from + to) / 2;
      const contributors = group.filter((segment) =>
        midpoint >= segment.from && midpoint <= segment.to
      );
      if (!contributors.length) continue;
      const exterior = contributors.some((segment) => segment.exterior);
      atomic.push({
        axis: group[0].axis,
        coordinate: group[0].coordinate,
        from,
        to,
        wall_type: exterior ? "exterior" : "partition",
        room_ids: [...new Set(contributors.map((segment) => segment.room_id).filter(Boolean))].sort(),
      });
    }
  }
  const stable = mergeAdjacentSegments(atomic.sort((left, right) =>
    left.axis.localeCompare(right.axis)
    || left.coordinate - right.coordinate
    || left.from - right.from
  ));
  return stable.map((segment, index) => {
    const horizontal = segment.axis === "h";
    const start = horizontal
      ? [segment.from, segment.coordinate]
      : [segment.coordinate, segment.from];
    const end = horizontal
      ? [segment.to, segment.coordinate]
      : [segment.coordinate, segment.to];
    return {
      id: `f${floorIndex}-wall-${String(index + 1).padStart(3, "0")}`,
      start,
      end,
      thickness: segment.wall_type === "exterior"
        ? CORRECTION_DEFAULTS.exteriorWallMm
        : CORRECTION_DEFAULTS.interiorWallMm,
      wall_type: segment.wall_type,
      room_ids: segment.room_ids,
      length_mm: rounded(Math.hypot(end[0] - start[0], end[1] - start[1])),
    };
  });
}

// Collapses wall fragments that are collinear, touching end-to-end, and share
// the same type/thickness/room pair into a single wall. Manual corrections
// (moving a door to a different wall, rescaling a floor, retyping a wall)
// routinely leave behind redundant fragments that wallsForMillimetreRooms
// would never have produced in one pass — e.g. twostorey_030's right exterior
// wall stayed split into two pieces after the garage was removed, so only one
// of the two got the exterior-thickness fix on the first pass. Openings on a
// merged-away fragment are re-homed onto the surviving wall with their
// position ratio recomputed from their absolute point, not just copied.
export function mergeCollinearWalls(floor) {
  const walls = floor?.walls || [];
  if (walls.length < 2) return floor;

  const originalGeometry = new Map(
    walls.map((wall) => [wall.id, { start: [...wall.start], end: [...wall.end] }]),
  );

  const keyOf = (wall) => {
    if (!finitePoint(wall.start) || !finitePoint(wall.end)) return null;
    const horizontal = wall.start[1] === wall.end[1];
    const vertical = wall.start[0] === wall.end[0];
    if (!horizontal && !vertical) return null; // never merge non-axis-aligned walls
    const axis = horizontal ? "h" : "v";
    const coordinate = horizontal ? wall.start[1] : wall.start[0];
    return [axis, coordinate, wall.wall_type, wall.thickness, [...(wall.room_ids || [])].sort().join(",")].join("|");
  };

  const groups = new Map();
  for (const wall of walls) {
    const key = keyOf(wall);
    if (key === null) continue;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(wall);
  }

  const survivorOf = new Map();
  const removedIds = new Set();

  for (const group of groups.values()) {
    if (group.length < 2) continue;
    const horizontal = group[0].start[1] === group[0].end[1];
    const withRange = group
      .map((wall) => ({
        wall,
        from: horizontal ? Math.min(wall.start[0], wall.end[0]) : Math.min(wall.start[1], wall.end[1]),
        to: horizontal ? Math.max(wall.start[0], wall.end[0]) : Math.max(wall.start[1], wall.end[1]),
      }))
      .sort((left, right) => left.from - right.from);

    let chain = [withRange[0]];
    const flush = () => {
      if (chain.length > 1) {
        const survivor = chain[0].wall;
        const coordinate = horizontal ? survivor.start[1] : survivor.start[0];
        const newFrom = chain[0].from;
        const newTo = chain.at(-1).to;
        survivor.start = horizontal ? [newFrom, coordinate] : [coordinate, newFrom];
        survivor.end = horizontal ? [newTo, coordinate] : [coordinate, newTo];
        survivor.length_mm = rounded(Math.hypot(
          survivor.end[0] - survivor.start[0],
          survivor.end[1] - survivor.start[1],
        ));
        for (const { wall } of chain) {
          survivorOf.set(wall.id, survivor);
          if (wall.id !== survivor.id) removedIds.add(wall.id);
        }
      }
      chain = [];
    };

    for (let index = 1; index < withRange.length; index += 1) {
      const previous = chain[chain.length - 1];
      const current = withRange[index];
      if (previous.to === current.from) {
        chain.push(current);
      } else {
        flush();
        chain = [current];
      }
    }
    flush();
  }

  if (!removedIds.size) return floor;

  floor.walls = walls.filter((wall) => !removedIds.has(wall.id));

  for (const opening of floor.openings || []) {
    const survivor = survivorOf.get(opening.wall_id);
    if (!survivor) continue;
    const original = originalGeometry.get(opening.wall_id);
    const point = [
      original.start[0] + (original.end[0] - original.start[0]) * opening.position,
      original.start[1] + (original.end[1] - original.start[1]) * opening.position,
    ];
    const dx = survivor.end[0] - survivor.start[0];
    const dy = survivor.end[1] - survivor.start[1];
    const lengthSquared = dx * dx + dy * dy || 1;
    const ratio = ((point[0] - survivor.start[0]) * dx + (point[1] - survivor.start[1]) * dy) / lengthSquared;
    opening.wall_id = survivor.id;
    opening.position = Number(Math.max(0, Math.min(1, ratio)).toFixed(6));
    if ("wall_length_mm" in opening) opening.wall_length_mm = survivor.length_mm;
    // The two merged fragments can carry the same room_ids in a different
    // order (each polygon edge records its own room first) even though the
    // validator treats connects as order-sensitive against wall.room_ids —
    // re-derive it the same way the original generator does so a merge never
    // trips opening_connections_mismatch on its own.
    if (Array.isArray(opening.connects)) {
      opening.connects = survivor.wall_type === "exterior"
        ? ["outside", ...survivor.room_ids]
        : [...survivor.room_ids];
    }
  }

  return floor;
}

function wallProjection(point, wall) {
  const [x, y] = point;
  const [x1, y1] = wall.start;
  const [x2, y2] = wall.end;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lengthSquared = dx * dx + dy * dy;
  const ratio = lengthSquared
    ? Math.max(0, Math.min(1, ((x - x1) * dx + (y - y1) * dy) / lengthSquared))
    : 0;
  const projected = [x1 + dx * ratio, y1 + dy * ratio];
  return { ratio, distance: Math.hypot(x - projected[0], y - projected[1]) };
}

function wallOrientation(wall) {
  return Math.abs(wall.end[0] - wall.start[0]) >= Math.abs(wall.end[1] - wall.start[1])
    ? "h"
    : "v";
}

function elementOrientation(points) {
  const first = points[0];
  const second = points[1];
  return Math.abs(second[0] - first[0]) >= Math.abs(second[1] - first[1])
    ? "h"
    : "v";
}

function requestedOpeningWidth(type, wall, sourceWidth, roomById) {
  if (type === "window") return Math.max(500, Math.min(2400, rounded(sourceWidth)));
  if (type === "passage") return Math.max(800, Math.min(2400, rounded(sourceWidth)));
  if (wall.wall_type === "exterior") return CORRECTION_DEFAULTS.entranceDoorMm;
  if (wall.room_ids.some((roomId) =>
    /\bwc\b|toilet/i.test(roomById.get(roomId)?.name || "")
  )) {
    return CORRECTION_DEFAULTS.smallWcDoorMm;
  }
  return CORRECTION_DEFAULTS.internalDoorMm;
}

export function openingsForMillimetreFloor(elements, walls, rooms, transform, floorIndex) {
  let entranceAssigned = false;
  const roomById = new Map(rooms.map((room) => [room.id, room]));
  return (elements || [])
    .filter((element) => ["door", "window", "opening"].includes(element.type))
    .map((element, index) => {
      const sourcePoints = element.points.map((point) => transform.point(point));
      const midpoint = [
        (sourcePoints[0][0] + sourcePoints[1][0]) / 2,
        (sourcePoints[0][1] + sourcePoints[1][1]) / 2,
      ];
      const orientation = elementOrientation(sourcePoints);
      const sourceWidth = Math.hypot(
        sourcePoints[1][0] - sourcePoints[0][0],
        sourcePoints[1][1] - sourcePoints[0][1],
      );
      const openingType = element.type === "opening" ? "passage" : element.type;
      const ranked = walls.map((wall) => {
        const projection = wallProjection(midpoint, wall);
        const orientationPenalty = wallOrientation(wall) === orientation ? 0 : 5000;
        const facadePenalty = openingType === "window" && wall.wall_type !== "exterior" ? 3000 : 0;
        return {
          wall,
          ...projection,
          score: projection.distance + orientationPenalty + facadePenalty,
        };
      }).sort((left, right) =>
        left.score - right.score
        || right.wall.length_mm - left.wall.length_mm
        || left.wall.id.localeCompare(right.wall.id)
      );
      const selected = ranked[0];
      const requestedWidth = requestedOpeningWidth(
        openingType,
        selected.wall,
        sourceWidth,
        roomById,
      );
      const width = Math.min(requestedWidth, Math.max(300, selected.wall.length_mm - 200));
      const halfRatio = width / Math.max(selected.wall.length_mm, 1) / 2;
      const position = Math.max(
        halfRatio,
        Math.min(1 - halfRatio, selected.ratio),
      );
      const isEntrance = openingType === "door"
        && selected.wall.wall_type === "exterior"
        && !entranceAssigned;
      if (isEntrance) entranceAssigned = true;
      const connects = selected.wall.wall_type === "exterior"
        ? ["outside", ...selected.wall.room_ids]
        : [...selected.wall.room_ids];
      return {
        id: element.id || `f${floorIndex}-opening-${index + 1}`,
        opening_type: openingType,
        wall_id: selected.wall.id,
        position: Number(position.toFixed(6)),
        width: rounded(width),
        role: isEntrance ? "main_entrance" : "standard",
        connects,
        traversable: openingType !== "window",
        ...(openingType === "window"
          ? {
              height_mm: FLOORPLAN_RULES.windows.defaultHeightMm,
              sill_height_mm: FLOORPLAN_RULES.windows.defaultSillHeightMm,
            }
          : {}),
        source_points_mm: sourcePoints,
        source_distance_to_wall_mm: rounded(selected.distance),
        wall_length_mm: selected.wall.length_mm,
      };
    });
}

export function buildMillimetreCorrectionGeometry(variant) {
  const transforms = [];
  const floors = variant.floors.map((floor, floorIndex) => {
    const rectified = rectifiedSourceRooms(floor);
    const transform = sourceFloorTransform(variant, floor, rectified);
    transforms.push(transform);
    const rooms = rectified.map(({ room, polygon }) => {
      const workingPolygon = polygon.map((point) =>
        snapToFootprintBoundary(transform.point(point), transform)
      );
      return {
        id: room.id,
        name: room.name,
        kind: room.kind,
        polygon: workingPolygon,
        area_m2: polygonAreaM2(workingPolygon),
      };
    });
    enforceHwrAreaAndCloseAdjacentGap(rooms);
    const footprint = [
      [0, 0],
      [transform.widthMm, 0],
      [transform.widthMm, transform.depthMm],
      [0, transform.depthMm],
    ];
    const walls = wallsForMillimetreRooms(rooms, footprint, floorIndex);
    return {
      id: `floor-${floor.floor}`,
      name: floor.name,
      level: floor.floor,
      footprint,
      rooms,
      walls,
      openings: openingsForMillimetreFloor(
        floor.referenceElements,
        walls,
        rooms,
        transform,
        floorIndex,
      ),
      stair_core_id: variant.stairCore?.id || null,
    };
  });
  const groundTransform = transforms[0];
  const stairPath = (variant.stairCore?.path || []).map((point) =>
    groundTransform.point(point)
  );
  const planType = stairPath.length <= 2
    ? "straight"
    : stairPath.length === 3
      ? "quarter_turn"
      : "double_quarter_turn";
  const stair = variant.stairCore && groundTransform ? {
    id: variant.stairCore.id,
    polygon: [
      groundTransform.point([variant.stairCore.footprint.x, variant.stairCore.footprint.y]),
      groundTransform.point([
        variant.stairCore.footprint.x + variant.stairCore.footprint.width,
        variant.stairCore.footprint.y,
      ]),
      groundTransform.point([
        variant.stairCore.footprint.x + variant.stairCore.footprint.width,
        variant.stairCore.footprint.y + variant.stairCore.footprint.height,
      ]),
      groundTransform.point([
        variant.stairCore.footprint.x,
        variant.stairCore.footprint.y + variant.stairCore.footprint.height,
      ]),
    ],
    path: stairPath,
    plan_type: planType,
    usable_width_mm: Math.max(
      CORRECTION_DEFAULTS.stairWidthMm,
      rounded((variant.stairCore.geometry?.usableFlightWidthM || 0) * 1000),
    ),
    geometry: structuredClone(variant.stairCore.geometry || null),
    direction: "up",
    representation: "clear_core_without_treads",
    tread_geometry_valid: false,
    floor_ids: floors.map((floor) => floor.id),
    rulebook_version: FLOORPLAN_RULEBOOK_VERSION,
    reference_rules: FLOORPLAN_RULES.stairs.reference,
    project_rules: FLOORPLAN_RULES.stairs.project,
  } : null;
  return { floors, shared_stair_core: stair };
}
