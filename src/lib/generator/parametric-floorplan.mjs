import { FLOORPLAN_RULES } from "./floorplan-rulebook.mjs";

const GRID_MM = 100;
const EXTERIOR_WALL_MM = 365;
const LOADBEARING_WALL_MM = 240;
const PARTITION_WALL_MM = 115;
const MIN_ROOM_WIDTH_MM = 2100;
const MAX_ROOM_ASPECT = 2.5;
const DEFAULT_WINDOW_HEIGHT_MM = 1350;
const PUBLIC_ROOM_TYPES = new Set([
  "living",
  "dining",
  "kitchen",
  "kitchen_dining",
  "living_dining_kitchen",
  "office",
]);
const PRIVATE_ROOM_TYPES = new Set(["master_bedroom", "bedroom", "small_bedroom"]);
const HABITABLE_ROOM_TYPES = new Set([...PUBLIC_ROOM_TYPES, ...PRIVATE_ROOM_TYPES]);
const WET_ROOM_TYPES = new Set(["bathroom", "guest_wc", "utility", "kitchen", "kitchen_dining", "living_dining_kitchen"]);

function rounded(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function snapUp(value, grid = GRID_MM) {
  return Math.ceil(value / grid) * grid;
}

function snapNearest(value, grid = GRID_MM) {
  return Math.max(grid, Math.round(value / grid) * grid);
}

function finiteNumber(value) {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function integerInRange(value, minimum, maximum, label) {
  const parsed = finiteNumber(value);
  if (parsed === null || !Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error(`${label}_must_be_integer_${minimum}_to_${maximum}`);
  }
  return parsed;
}

function hashSeed(seed) {
  let state = (Number(seed) || 0) >>> 0;
  state ^= state << 13;
  state ^= state >>> 17;
  state ^= state << 5;
  return state >>> 0;
}

function normalizeInputs(source = {}) {
  const bedrooms = integerInRange(source.bedrooms, 1, 5, "bedrooms");
  const bathrooms = integerInRange(source.bathrooms, 1, 3, "bathrooms");
  const openness = finiteNumber(source.openness);
  if (openness === null || openness < 0 || openness > 100) {
    throw new Error("openness_must_be_0_to_100");
  }
  const seed = source.seed === undefined ? 1 : integerInRange(source.seed, -2147483648, 2147483647, "seed");
  const targetFloorAreaM2 = source.targetFloorAreaM2 === undefined || source.targetFloorAreaM2 === null
    ? null
    : finiteNumber(source.targetFloorAreaM2);
  if (targetFloorAreaM2 !== null && (targetFloorAreaM2 < 45 || targetFloorAreaM2 > 450)) {
    throw new Error("target_floor_area_m2_must_be_45_to_450");
  }
  let footprint = null;
  if (source.footprint !== undefined && source.footprint !== null) {
    const widthM = finiteNumber(source.footprint.widthM);
    const depthM = finiteNumber(source.footprint.depthM);
    if (widthM === null || depthM === null || widthM < 6 || depthM < 6 || widthM > 35 || depthM > 35) {
      throw new Error("footprint_dimensions_must_be_6_to_35_metres");
    }
    footprint = { widthM, depthM };
  }
  return {
    bedrooms,
    bathrooms,
    openness,
    targetFloorAreaM2,
    footprint,
    seed,
    extras: {
      guestWc: source.extras?.guestWc === true,
      utilityRoom: source.extras?.utilityRoom === true,
      homeOffice: source.extras?.homeOffice === true,
      terrace: source.extras?.terrace === true,
    },
  };
}

function roomDefinition(id, type, name, zone, targetAreaM2, minimumAreaM2, options = {}) {
  return {
    id,
    type,
    name,
    zone,
    targetAreaM2,
    minimumAreaM2,
    requiresWindow: HABITABLE_ROOM_TYPES.has(type),
    wet: WET_ROOM_TYPES.has(type),
    doorClearWidthMm: type === "bathroom" ? 900 : 800,
    ...options,
  };
}

export function expandRoomProgram(source) {
  const input = normalizeInputs(source);
  const privateRooms = [
    roomDefinition("master-bedroom", "master_bedroom", "Eltern / Schlafen", "private", 14, 12),
  ];
  for (let index = 1; index < input.bedrooms; index += 1) {
    const small = index === 4;
    privateRooms.push(roomDefinition(
      `bedroom-${index + 1}`,
      small ? "small_bedroom" : "bedroom",
      small ? "Kind / Flex" : `Kind ${index}`,
      "private",
      small ? 9 : 11,
      small ? 8 : 10,
    ));
  }
  for (let index = 0; index < input.bathrooms; index += 1) {
    privateRooms.push(roomDefinition(
      `bathroom-${index + 1}`,
      "bathroom",
      index === 0 ? "Bad" : `Duschbad ${index + 1}`,
      "private",
      index === 0 ? 6.5 : 4.5,
      index === 0 ? 5 : 3.5,
      { showerOnly: index > 0 },
    ));
  }

  const publicRooms = [];
  if (input.openness >= 75) {
    publicRooms.push(roomDefinition(
      "living-dining-kitchen",
      "living_dining_kitchen",
      "Wohnen / Essen / Kochen",
      "public",
      36,
      27,
    ));
  } else if (input.openness >= 25) {
    publicRooms.push(
      roomDefinition("living", "living", "Wohnen", "public", 24, 18),
      roomDefinition("kitchen-dining", "kitchen_dining", "Kochen / Essen", "public", 20, 16),
    );
  } else {
    publicRooms.push(
      roomDefinition("living", "living", "Wohnen", "public", 24, 18),
      roomDefinition("dining", "dining", "Essen", "public", 11, 9),
      roomDefinition("kitchen", "kitchen", "Küche", "public", 9, 7),
    );
  }
  if (input.extras.homeOffice) {
    publicRooms.push(roomDefinition("office", "office", "Büro", "public", 10, 8));
  }
  if (input.extras.utilityRoom) {
    publicRooms.push(roomDefinition("utility", "utility", "HWR / HTR", "public", 7.5, 5));
  }
  if (input.extras.guestWc) {
    publicRooms.push(roomDefinition("guest-wc", "guest_wc", "Gäste-WC", "public", 2.2, 1.6));
  }
  return { input, privateRooms, publicRooms };
}

function solveInnerDimensions(targetAreaM2, aspectRatio) {
  const areaMm2 = targetAreaM2 * 1_000_000;
  const exteriorDouble = EXTERIOR_WALL_MM * 2;
  const linear = exteriorDouble * aspectRatio - exteriorDouble;
  const depthMm = (-linear + Math.sqrt(linear ** 2 + 4 * aspectRatio * areaMm2)) / (2 * aspectRatio);
  const innerDepthMm = snapNearest(depthMm);
  const outerWidthMm = aspectRatio * (innerDepthMm + exteriorDouble);
  const innerWidthMm = snapNearest(outerWidthMm - exteriorDouble);
  return { innerWidthMm, innerDepthMm };
}

function rowWidthLimits(rooms, depthMm) {
  return rooms.map((room) => {
    const areaWidthMm = room.minimumAreaM2 * 1_000_000 / depthMm;
    return {
      minimumMm: snapUp(Math.max(MIN_ROOM_WIDTH_MM, depthMm / MAX_ROOM_ASPECT, areaWidthMm)),
      maximumMm: Math.floor((depthMm * MAX_ROOM_ASPECT) / GRID_MM) * GRID_MM,
    };
  });
}

function rowIsFeasible(rooms, widthMm, depthMm) {
  if (!rooms.length || depthMm < MIN_ROOM_WIDTH_MM || depthMm % GRID_MM !== 0) return false;
  const limits = rowWidthLimits(rooms, depthMm);
  return limits.every((limit) => limit.maximumMm >= limit.minimumMm)
    && limits.reduce((sum, limit) => sum + limit.minimumMm, 0) <= widthMm
    && limits.reduce((sum, limit) => sum + limit.maximumMm, 0) >= widthMm;
}

function allocateRowWidths(rooms, widthMm, depthMm, seedOffset) {
  const limits = rowWidthLimits(rooms, depthMm);
  const widths = limits.map((limit) => limit.minimumMm);
  let remainingUnits = Math.round((widthMm - widths.reduce((sum, width) => sum + width, 0)) / GRID_MM);
  const orderBias = rooms.map((_, index) => hashSeed(seedOffset + index * 7919));
  while (remainingUnits > 0) {
    let selected = -1;
    let bestScore = Number.NEGATIVE_INFINITY;
    for (let index = 0; index < rooms.length; index += 1) {
      if (widths[index] + GRID_MM > limits[index].maximumMm) continue;
      const targetWidthMm = rooms[index].targetAreaM2 * 1_000_000 / depthMm;
      const deficit = targetWidthMm - widths[index];
      const score = deficit * 1000 + orderBias[index];
      if (score > bestScore) {
        bestScore = score;
        selected = index;
      }
    }
    if (selected < 0) throw new Error("row_width_allocation_failed");
    widths[selected] += GRID_MM;
    remainingUnits -= 1;
  }
  return widths;
}

function findBandLayout(widthMm, depthMm, privateRooms, publicRooms) {
  const candidates = [];
  for (let hallDepthMm = 900; hallDepthMm <= 1800; hallDepthMm += GRID_MM) {
    const circulationRatio = (widthMm * hallDepthMm) / (widthMm * (depthMm - hallDepthMm));
    if (circulationRatio < 0.12 || circulationRatio > 0.15) continue;
    const availableDepthMm = depthMm - hallDepthMm;
    for (let privateDepthMm = MIN_ROOM_WIDTH_MM; privateDepthMm <= availableDepthMm - MIN_ROOM_WIDTH_MM; privateDepthMm += GRID_MM) {
      const publicDepthMm = availableDepthMm - privateDepthMm;
      if (!rowIsFeasible(privateRooms, widthMm, privateDepthMm)) continue;
      if (!rowIsFeasible(publicRooms, widthMm, publicDepthMm)) continue;
      const privateTarget = privateRooms.reduce((sum, room) => sum + room.targetAreaM2, 0);
      const publicTarget = publicRooms.reduce((sum, room) => sum + room.targetAreaM2, 0);
      const score =
        Math.abs(widthMm * privateDepthMm / 1_000_000 - privateTarget)
        + Math.abs(widthMm * publicDepthMm / 1_000_000 - publicTarget)
        + Math.abs(circulationRatio - 0.135) * 10;
      candidates.push({ hallDepthMm, privateDepthMm, publicDepthMm, circulationRatio, score });
    }
  }
  candidates.sort((left, right) =>
    left.score - right.score
    || left.hallDepthMm - right.hallDepthMm
    || left.privateDepthMm - right.privateDepthMm
  );
  return candidates[0] ?? null;
}

function resolveEnvelope(program) {
  const { input, privateRooms, publicRooms } = program;
  if (input.footprint) {
    const innerWidthMm = snapNearest(input.footprint.widthM * 1000 - EXTERIOR_WALL_MM * 2);
    const innerDepthMm = snapNearest(input.footprint.depthM * 1000 - EXTERIOR_WALL_MM * 2);
    const actualAreaM2 = innerWidthMm * innerDepthMm / 1_000_000;
    if (
      input.targetFloorAreaM2 !== null
      && Math.abs(actualAreaM2 - input.targetFloorAreaM2) / input.targetFloorAreaM2 > 0.05
    ) {
      throw new Error(`footprint_target_area_mismatch:${rounded(actualAreaM2)}m2`);
    }
    const bands = findBandLayout(innerWidthMm, innerDepthMm, privateRooms, publicRooms);
    if (!bands) throw new Error("footprint_cannot_fit_room_program");
    return {
      innerWidthMm,
      innerDepthMm,
      targetFloorAreaM2: input.targetFloorAreaM2 ?? actualAreaM2,
      aspectRatio: rounded((innerWidthMm + 730) / (innerDepthMm + 730), 3),
      bands,
    };
  }

  const netTarget = [...privateRooms, ...publicRooms]
    .reduce((sum, room) => sum + room.targetAreaM2, 0);
  const requestedTarget = input.targetFloorAreaM2;
  const initialTarget = requestedTarget ?? Math.ceil(netTarget * 1.135);
  const maximumTarget = requestedTarget ? requestedTarget * 1.05 : 450;
  const aspectRatio = 1.2 + (Math.abs(hashSeed(input.seed)) % 5) * 0.1;
  for (let target = initialTarget; target <= maximumTarget + 0.001; target += 1) {
    const dimensions = solveInnerDimensions(target, aspectRatio);
    const bands = findBandLayout(
      dimensions.innerWidthMm,
      dimensions.innerDepthMm,
      privateRooms,
      publicRooms,
    );
    if (!bands) continue;
    const actualAreaM2 = dimensions.innerWidthMm * dimensions.innerDepthMm / 1_000_000;
    if (requestedTarget && Math.abs(actualAreaM2 - requestedTarget) / requestedTarget > 0.05) continue;
    return {
      ...dimensions,
      targetFloorAreaM2: requestedTarget ?? actualAreaM2,
      aspectRatio: rounded(
        (dimensions.innerWidthMm + 730) / (dimensions.innerDepthMm + 730),
        3,
      ),
      bands,
    };
  }
  const minimumHint = Math.ceil(Math.max(initialTarget, netTarget * 1.135));
  throw new Error(`floor_area_below_geometric_minimum:try_at_least_${minimumHint}m2_or_a_larger_footprint`);
}

function rectanglePolygon(x, y, width, height) {
  return [
    [x, y],
    [x + width, y],
    [x + width, y + height],
    [x, y + height],
  ];
}

function makeRooms(definitions, widths, y, depth, mirror) {
  const orderedDefinitions = mirror ? [...definitions].reverse() : definitions;
  const orderedWidths = mirror ? [...widths].reverse() : widths;
  let x = 0;
  return orderedDefinitions.map((definition, index) => {
    const width = orderedWidths[index];
    const room = {
      ...definition,
      x,
      y,
      width,
      height: depth,
      polygon: rectanglePolygon(x, y, width, depth),
      areaM2: rounded(width * depth / 1_000_000),
      doors: [],
      windows: [],
    };
    x += width;
    return room;
  });
}

function wall(id, start, end, thicknessMm, type) {
  return { id, start, end, thicknessMm, type };
}

function makeWalls(widthMm, depthMm, privateRooms, publicRooms, privateDepthMm, hallDepthMm) {
  const hallBottom = privateDepthMm + hallDepthMm;
  const walls = [
    wall("wall-exterior-north", [-EXTERIOR_WALL_MM / 2, -EXTERIOR_WALL_MM / 2], [widthMm + EXTERIOR_WALL_MM / 2, -EXTERIOR_WALL_MM / 2], EXTERIOR_WALL_MM, "exterior"),
    wall("wall-exterior-south", [-EXTERIOR_WALL_MM / 2, depthMm + EXTERIOR_WALL_MM / 2], [widthMm + EXTERIOR_WALL_MM / 2, depthMm + EXTERIOR_WALL_MM / 2], EXTERIOR_WALL_MM, "exterior"),
    wall("wall-exterior-west", [-EXTERIOR_WALL_MM / 2, -EXTERIOR_WALL_MM / 2], [-EXTERIOR_WALL_MM / 2, depthMm + EXTERIOR_WALL_MM / 2], EXTERIOR_WALL_MM, "exterior"),
    wall("wall-exterior-east", [widthMm + EXTERIOR_WALL_MM / 2, -EXTERIOR_WALL_MM / 2], [widthMm + EXTERIOR_WALL_MM / 2, depthMm + EXTERIOR_WALL_MM / 2], EXTERIOR_WALL_MM, "exterior"),
    wall("wall-private-hall", [0, privateDepthMm], [widthMm, privateDepthMm], LOADBEARING_WALL_MM, "loadbearing"),
    wall("wall-hall-public", [0, hallBottom], [widthMm, hallBottom], PARTITION_WALL_MM, "partition"),
  ];
  for (const [rowName, rooms, startY, endY] of [
    ["private", privateRooms, 0, privateDepthMm],
    ["public", publicRooms, hallBottom, depthMm],
  ]) {
    for (let index = 0; index < rooms.length - 1; index += 1) {
      const x = rooms[index].x + rooms[index].width;
      walls.push(wall(`wall-${rowName}-${index + 1}`, [x, startY], [x, endY], PARTITION_WALL_MM, "partition"));
    }
  }
  return walls;
}

function openingSegment(room, y, widthMm) {
  const margin = Math.max(200, Math.min(500, (room.width - widthMm) / 2));
  const startX = Math.min(room.x + room.width - widthMm - 200, room.x + margin);
  return [[startX, y], [startX + widthMm, y]];
}

function attachDoors(plan, mirror) {
  const doors = [];
  const privateBoundaryY = plan.bands.privateDepthMm;
  const publicBoundaryY = privateBoundaryY + plan.bands.hallDepthMm;
  for (const room of plan.rooms.filter((candidate) => candidate.id !== "hall")) {
    const y = room.zone === "private" ? privateBoundaryY : publicBoundaryY;
    const wallId = room.zone === "private" ? "wall-private-hall" : "wall-hall-public";
    const [start, end] = openingSegment(room, y, room.doorClearWidthMm);
    const door = {
      id: `door-${room.id}`,
      roomId: room.id,
      fromRoomId: "hall",
      toRoomId: room.id,
      wallId,
      start,
      end,
      clearWidthMm: room.doorClearWidthMm,
      swingDirection: room.zone === "private" ? "north" : "south",
      exterior: false,
    };
    room.doors.push(door.id);
    doors.push(door);
  }
  const entryX = mirror ? 0 : plan.envelope.inner.widthMm;
  const entryY = privateBoundaryY + plan.bands.hallDepthMm / 2;
  doors.push({
    id: "door-entry",
    roomId: "hall",
    fromRoomId: "outside",
    toRoomId: "hall",
    wallId: mirror ? "wall-exterior-west" : "wall-exterior-east",
    start: [entryX, entryY - 500],
    end: [entryX, entryY + 500],
    clearWidthMm: 1000,
    swingDirection: mirror ? "east" : "west",
    exterior: true,
  });
  plan.rooms.find((room) => room.id === "hall").doors.push("door-entry");
  return doors;
}

function attachWindows(plan) {
  const windows = [];
  for (const room of plan.rooms.filter((candidate) => candidate.requiresWindow)) {
    const requiredAreaM2 = room.areaM2 / 8;
    let heightMm = DEFAULT_WINDOW_HEIGHT_MM;
    let widthMm = snapUp(requiredAreaM2 * 1_000_000 / heightMm);
    const availableWidthMm = room.width - 400;
    if (widthMm > availableWidthMm) {
      heightMm = 1800;
      widthMm = snapUp(requiredAreaM2 * 1_000_000 / heightMm);
    }
    if (widthMm > availableWidthMm) throw new Error(`window_cannot_fit:${room.id}`);
    const y = room.zone === "private" ? 0 : plan.envelope.inner.depthMm;
    const startX = room.x + Math.round((room.width - widthMm) / 200) * 100;
    const window = {
      id: `window-${room.id}`,
      roomId: room.id,
      wallId: room.zone === "private" ? "wall-exterior-north" : "wall-exterior-south",
      start: [startX, y],
      end: [startX + widthMm, y],
      widthMm,
      heightMm,
      glazingAreaM2: rounded(widthMm * heightMm / 1_000_000),
    };
    room.windows.push(window.id);
    windows.push(window);
  }
  return windows;
}

function sharedBoundaryLength(left, right) {
  const xTouch = left.x + left.width === right.x || right.x + right.width === left.x;
  const yOverlap = Math.max(0, Math.min(left.y + left.height, right.y + right.height) - Math.max(left.y, right.y));
  const yTouch = left.y + left.height === right.y || right.y + right.height === left.y;
  const xOverlap = Math.max(0, Math.min(left.x + left.width, right.x + right.width) - Math.max(left.x, right.x));
  return Math.max(xTouch ? yOverlap : 0, yTouch ? xOverlap : 0);
}

function overlapArea(left, right) {
  return Math.max(0, Math.min(left.x + left.width, right.x + right.width) - Math.max(left.x, right.x))
    * Math.max(0, Math.min(left.y + left.height, right.y + right.height) - Math.max(left.y, right.y));
}

export function validateParametricFloorplan(plan) {
  const errors = [];
  const warnings = [];
  const inner = plan?.envelope?.inner;
  if (!inner || !Array.isArray(plan.rooms) || !Array.isArray(plan.walls)) {
    return { passed: false, errors: ["invalid_plan_shape"], warnings, stats: {} };
  }
  const roomAreaMm2 = plan.rooms.reduce((sum, room) => sum + room.width * room.height, 0);
  const envelopeAreaMm2 = inner.widthMm * inner.depthMm;
  if (roomAreaMm2 !== envelopeAreaMm2) errors.push("room_coverage_gap_or_overflow");
  for (let index = 0; index < plan.rooms.length; index += 1) {
    for (let other = index + 1; other < plan.rooms.length; other += 1) {
      if (overlapArea(plan.rooms[index], plan.rooms[other]) > 0) {
        errors.push(`room_overlap:${plan.rooms[index].id}:${plan.rooms[other].id}`);
      }
    }
  }

  const hall = plan.rooms.find((room) => room.id === "hall");
  if (!hall || hall.areaM2 < 4) errors.push("entry_hall_below_4m2");
  for (const room of plan.rooms.filter((candidate) => candidate.id !== "hall")) {
    if (room.areaM2 + 1e-9 < room.minimumAreaM2) errors.push(`room_area_below_minimum:${room.id}`);
    const shortSide = Math.min(room.width, room.height);
    const longSide = Math.max(room.width, room.height);
    if (shortSide < MIN_ROOM_WIDTH_MM) errors.push(`room_narrower_than_2100mm:${room.id}`);
    if (longSide / shortSide > MAX_ROOM_ASPECT + 1e-9) errors.push(`room_aspect_exceeds_1_to_2_5:${room.id}`);
    const door = plan.doors.find((candidate) => candidate.roomId === room.id && !candidate.exterior);
    if (!door || door.fromRoomId !== "hall") errors.push(`room_not_reachable_from_hall:${room.id}`);
    if (door && door.clearWidthMm < (room.type === "bathroom" ? 900 : 800)) {
      errors.push(`door_clear_width_failed:${room.id}`);
    }
    if (room.requiresWindow) {
      const touchesExterior = room.y === 0 || room.y + room.height === inner.depthMm
        || room.x === 0 || room.x + room.width === inner.widthMm;
      if (!touchesExterior) errors.push(`habitable_room_not_on_exterior:${room.id}`);
      const glazing = plan.windows
        .filter((window) => window.roomId === room.id)
        .reduce((sum, window) => sum + window.glazingAreaM2, 0);
      if (
        glazing + 1e-9
        < room.areaM2 * FLOORPLAN_RULES.windows.minimumGlazingToRoomAreaRatio
      ) errors.push(`window_area_below_one_tenth:${room.id}`);
    }
  }

  const bedrooms = plan.rooms.filter((room) => PRIVATE_ROOM_TYPES.has(room.type));
  const bathrooms = plan.rooms.filter((room) => room.type === "bathroom");
  if (!bathrooms.some((bathroom) => bedrooms.some((bedroom) => sharedBoundaryLength(bathroom, bedroom) > 0))) {
    errors.push("bathroom_not_adjacent_to_bedroom_cluster");
  }
  const guestWc = plan.rooms.find((room) => room.type === "guest_wc");
  const entryDoor = plan.doors.find((door) => door.id === "door-entry");
  if (guestWc && entryDoor) {
    const wcCenterX = guestWc.x + guestWc.width / 2;
    if (Math.abs(wcCenterX - entryDoor.start[0]) > Math.max(3000, inner.widthMm * 0.3)) {
      errors.push("guest_wc_not_near_entry");
    }
    const wcDoor = plan.doors.find((door) => door.roomId === guestWc.id);
    if (!wcDoor || wcDoor.fromRoomId !== "hall") errors.push("guest_wc_opens_to_kitchen_or_dining");
  }
  const circulationAreaM2 = hall?.areaM2 ?? 0;
  const netRoomAreaM2 = plan.rooms
    .filter((room) => room.id !== "hall")
    .reduce((sum, room) => sum + room.areaM2, 0);
  const circulationRatio = circulationAreaM2 / Math.max(netRoomAreaM2, 0.001);
  if (circulationRatio < 0.12 - 0.001 || circulationRatio > 0.15 + 0.001) {
    errors.push("circulation_overhead_outside_12_to_15_percent");
  }
  const actualAreaM2 = envelopeAreaMm2 / 1_000_000;
  const targetAreaM2 = plan.stats.targetFloorAreaM2;
  const targetDeviation = Math.abs(actualAreaM2 - targetAreaM2) / targetAreaM2;
  if (targetDeviation > 0.05 + 1e-9) errors.push("target_floor_area_deviation_exceeds_5_percent");

  const allowedThicknesses = new Set([EXTERIOR_WALL_MM, LOADBEARING_WALL_MM, PARTITION_WALL_MM]);
  if (plan.walls.some((candidate) => !allowedThicknesses.has(candidate.thicknessMm))) {
    errors.push("unsupported_wall_thickness");
  }
  const wetRooms = plan.rooms.filter((room) => room.wet);
  const wetSharedWalls = wetRooms.reduce((count, room, index) =>
    count + wetRooms.slice(index + 1).filter((other) => sharedBoundaryLength(room, other) > 0).length, 0);
  if (wetRooms.length > 1 && wetSharedWalls === 0) warnings.push("wet_rooms_do_not_share_a_plumbing_wall");
  return {
    passed: errors.length === 0,
    errors,
    warnings,
    stats: {
      actualFloorAreaM2: rounded(actualAreaM2),
      targetFloorAreaM2: rounded(targetAreaM2),
      targetDeviationPercent: rounded(targetDeviation * 100),
      circulationRatio: rounded(circulationRatio, 4),
      wetSharedWallPairs: wetSharedWalls,
    },
  };
}

export function generateParametricFloorplan(source) {
  const program = expandRoomProgram(source);
  const envelope = resolveEnvelope(program);
  const mirror = (hashSeed(program.input.seed) & 1) === 1;
  const privateWidths = allocateRowWidths(
    program.privateRooms,
    envelope.innerWidthMm,
    envelope.bands.privateDepthMm,
    program.input.seed + 101,
  );
  const publicWidths = allocateRowWidths(
    program.publicRooms,
    envelope.innerWidthMm,
    envelope.bands.publicDepthMm,
    program.input.seed + 202,
  );
  const privateRooms = makeRooms(
    program.privateRooms,
    privateWidths,
    0,
    envelope.bands.privateDepthMm,
    mirror,
  );
  const hallY = envelope.bands.privateDepthMm;
  const publicY = hallY + envelope.bands.hallDepthMm;
  const publicRooms = makeRooms(
    program.publicRooms,
    publicWidths,
    publicY,
    envelope.bands.publicDepthMm,
    mirror,
  );
  const hall = {
    id: "hall",
    type: "hall",
    name: "Diele / Flur",
    zone: "circulation",
    targetAreaM2: 4,
    minimumAreaM2: 4,
    requiresWindow: false,
    wet: false,
    doorClearWidthMm: 1000,
    x: 0,
    y: hallY,
    width: envelope.innerWidthMm,
    height: envelope.bands.hallDepthMm,
    polygon: rectanglePolygon(0, hallY, envelope.innerWidthMm, envelope.bands.hallDepthMm),
    areaM2: rounded(envelope.innerWidthMm * envelope.bands.hallDepthMm / 1_000_000),
    doors: [],
    windows: [],
  };
  const plan = {
    schema: "zuhausefinder-parametric-plan-v1",
    seed: program.input.seed,
    inputs: program.input,
    storeyType: "1_storey",
    envelope: {
      inner: {
        x: 0,
        y: 0,
        widthMm: envelope.innerWidthMm,
        depthMm: envelope.innerDepthMm,
      },
      outer: {
        x: -EXTERIOR_WALL_MM,
        y: -EXTERIOR_WALL_MM,
        widthMm: envelope.innerWidthMm + EXTERIOR_WALL_MM * 2,
        depthMm: envelope.innerDepthMm + EXTERIOR_WALL_MM * 2,
      },
      aspectRatio: envelope.aspectRatio,
    },
    bands: envelope.bands,
    rooms: [...privateRooms, hall, ...publicRooms],
    walls: [],
    doors: [],
    windows: [],
    stats: {
      targetFloorAreaM2: rounded(envelope.targetFloorAreaM2),
      actualFloorAreaM2: rounded(envelope.innerWidthMm * envelope.innerDepthMm / 1_000_000),
      circulationFactorTarget: 0.135,
      wallThicknessMm: {
        exterior: EXTERIOR_WALL_MM,
        loadbearing: LOADBEARING_WALL_MM,
        partition: PARTITION_WALL_MM,
      },
    },
    disclaimer: "Schematisches Konzept – kein Ersatz für Architekt:innen und keine Prüfung des örtlichen Baurechts.",
  };
  plan.walls = makeWalls(
    envelope.innerWidthMm,
    envelope.innerDepthMm,
    privateRooms,
    publicRooms,
    envelope.bands.privateDepthMm,
    envelope.bands.hallDepthMm,
  );
  plan.doors = attachDoors(plan, mirror);
  plan.windows = attachWindows(plan);
  const validation = validateParametricFloorplan(plan);
  plan.stats = { ...plan.stats, ...validation.stats };
  plan.validation = validation;
  if (!validation.passed) {
    throw new Error(`generated_plan_failed_validation:${validation.errors.join(",")}`);
  }
  return plan;
}

function xml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function wallPolygon(candidate) {
  const [x1, y1] = candidate.start;
  const [x2, y2] = candidate.end;
  const half = candidate.thicknessMm / 2;
  if (y1 === y2) {
    return `${x1},${y1 - half} ${x2},${y2 - half} ${x2},${y2 + half} ${x1},${y1 + half}`;
  }
  return `${x1 - half},${y1} ${x1 + half},${y1} ${x2 + half},${y2} ${x2 - half},${y2}`;
}

function openingMask(opening, thicknessMm) {
  const [x1, y1] = opening.start;
  const [x2, y2] = opening.end;
  const pad = thicknessMm / 2 + 20;
  if (y1 === y2) {
    return `<rect x="${x1}" y="${y1 - pad}" width="${x2 - x1}" height="${pad * 2}" fill="#fff"/>`;
  }
  return `<rect x="${x1 - pad}" y="${y1}" width="${pad * 2}" height="${y2 - y1}" fill="#fff"/>`;
}

function doorMarkup(door, wallById) {
  const candidate = wallById.get(door.wallId);
  if (!candidate) return "";
  const [x1, y1] = door.start;
  const [x2, y2] = door.end;
  const width = Math.hypot(x2 - x1, y2 - y1);
  let leaf;
  let arc;
  if (y1 === y2) {
    const direction = door.swingDirection === "north" ? -1 : 1;
    leaf = `<line x1="${x1}" y1="${y1}" x2="${x1}" y2="${y1 + direction * width}" class="door-leaf"/>`;
    arc = `M ${x2} ${y2} A ${width} ${width} 0 0 ${direction < 0 ? 0 : 1} ${x1} ${y1 + direction * width}`;
  } else {
    const direction = door.swingDirection === "east" ? 1 : -1;
    leaf = `<line x1="${x1}" y1="${y1}" x2="${x1 + direction * width}" y2="${y1}" class="door-leaf"/>`;
    arc = `M ${x2} ${y2} A ${width} ${width} 0 0 ${direction > 0 ? 0 : 1} ${x1 + direction * width} ${y1}`;
  }
  return `${openingMask(door, candidate.thicknessMm)}${leaf}<path d="${arc}" class="door-arc"/>`;
}

function windowMarkup(window, wallById) {
  const candidate = wallById.get(window.wallId);
  if (!candidate) return "";
  const [x1, y1] = window.start;
  const [x2, y2] = window.end;
  const offset = candidate.thicknessMm * 0.18;
  const lines = y1 === y2
    ? `<line x1="${x1}" y1="${y1 - offset}" x2="${x2}" y2="${y2 - offset}"/><line x1="${x1}" y1="${y1 + offset}" x2="${x2}" y2="${y2 + offset}"/>`
    : `<line x1="${x1 - offset}" y1="${y1}" x2="${x2 - offset}" y2="${y2}"/><line x1="${x1 + offset}" y1="${y1}" x2="${x2 + offset}" y2="${y2}"/>`;
  return `${openingMask(window, candidate.thicknessMm)}<g class="window">${lines}</g>`;
}

export function renderParametricFloorplanSvg(plan, options = {}) {
  const validation = validateParametricFloorplan(plan);
  if (!validation.passed) {
    throw new Error(`cannot_render_invalid_plan:${validation.errors.join(",")}`);
  }
  const page = options.page === "A4" ? "A4" : "A3";
  const pageWidthMm = page === "A4" ? 297 : 420;
  const pageHeightMm = page === "A4" ? 210 : 297;
  const width = plan.envelope.inner.widthMm;
  const depth = plan.envelope.inner.depthMm;
  const margin = 1800;
  const viewBox = `${-margin} ${-margin} ${width + margin * 2} ${depth + margin * 2}`;
  const wallById = new Map(plan.walls.map((candidate) => [candidate.id, candidate]));
  const roomMarkup = plan.rooms.map((room) => {
    const centerX = room.x + room.width / 2;
    const centerY = room.y + room.height / 2;
    const fill = room.zone === "private" ? "#f5f1e8" : room.zone === "public" ? "#dcf7e8" : "#ece9e2";
    return `<g data-room="${xml(room.id)}">
      <polygon points="${room.polygon.map((point) => point.join(",")).join(" ")}" fill="${fill}"/>
      <text x="${centerX}" y="${centerY - 80}" class="room-name">${xml(room.name)}</text>
      <text x="${centerX}" y="${centerY + 330}" class="room-area">${room.areaM2.toFixed(1).replace(".", ",")} m²</text>
    </g>`;
  }).join("");
  const walls = plan.walls.map((candidate) =>
    `<polygon points="${wallPolygon(candidate)}" class="wall wall-${candidate.type}"/>`
  ).join("");
  const openings = [
    ...plan.windows.map((window) => windowMarkup(window, wallById)),
    ...plan.doors.map((door) => doorMarkup(door, wallById)),
  ].join("");
  const terrace = plan.inputs.extras.terrace
    ? `<rect x="${width * 0.2}" y="${depth + 650}" width="${width * 0.6}" height="900" rx="80" class="terrace"/><text x="${width / 2}" y="${depth + 1200}" class="small-label">Terrasse</text>`
    : "";
  const scaleLength = Math.min(5000, Math.floor(width / 1000) * 1000);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${pageWidthMm}mm" height="${pageHeightMm}mm" viewBox="${viewBox}" preserveAspectRatio="xMidYMid meet">
  <title>Deterministischer Grundriss – Seed ${plan.seed}</title>
  <style>
    .wall{fill:#1c1917}.wall-partition{fill:#57534e}.wall-loadbearing{fill:#44403c}
    .room-name,.room-area,.small-label{font-family:Arial,sans-serif;text-anchor:middle;fill:#1c1917}
    .room-name{font-size:360px;font-weight:700}.room-area{font-size:270px}.small-label{font-size:260px}
    .window{stroke:#06a8d8;stroke-width:55;fill:none}.door-leaf{stroke:#1d5b4a;stroke-width:45}
    .door-arc{stroke:#1d5b4a;stroke-width:28;fill:none;stroke-dasharray:90 45}
    .dimension{stroke:#78716c;stroke-width:25;fill:none}.dimension-text{font:260px Arial,sans-serif;fill:#57534e;text-anchor:middle}
    .terrace{fill:#f3efe5;stroke:#a8a29e;stroke-width:35;stroke-dasharray:120 70}
  </style>
  <rect x="${-margin}" y="${-margin}" width="${width + margin * 2}" height="${depth + margin * 2}" fill="#fff"/>
  ${roomMarkup}
  ${walls}
  ${openings}
  ${terrace}
  <g aria-label="Gesamtmaße">
    <line x1="0" y1="-950" x2="${width}" y2="-950" class="dimension"/>
    <line x1="0" y1="-1100" x2="0" y2="-800" class="dimension"/><line x1="${width}" y1="-1100" x2="${width}" y2="-800" class="dimension"/>
    <text x="${width / 2}" y="-1100" class="dimension-text">${(width / 1000).toFixed(2).replace(".", ",")} m innen</text>
    <line x1="-950" y1="0" x2="-950" y2="${depth}" class="dimension"/>
    <line x1="-1100" y1="0" x2="-800" y2="0" class="dimension"/><line x1="-1100" y1="${depth}" x2="-800" y2="${depth}" class="dimension"/>
    <text x="-1150" y="${depth / 2}" class="dimension-text" transform="rotate(-90 -1150 ${depth / 2})">${(depth / 1000).toFixed(2).replace(".", ",")} m innen</text>
  </g>
  <g aria-label="Nordpfeil" transform="translate(${width + 900} 200)">
    <text x="0" y="-250" class="dimension-text">N</text><line x1="0" y1="600" x2="0" y2="0" class="dimension"/><polygon points="0,-150 -160,100 160,100" fill="#1d5b4a"/>
  </g>
  <g aria-label="Maßstab" transform="translate(0 ${depth + 1000})">
    <line x1="0" y1="0" x2="${scaleLength}" y2="0" stroke="#1c1917" stroke-width="80"/>
    <line x1="0" y1="-120" x2="0" y2="120" stroke="#1c1917" stroke-width="45"/><line x1="${scaleLength}" y1="-120" x2="${scaleLength}" y2="120" stroke="#1c1917" stroke-width="45"/>
    <text x="${scaleLength / 2}" y="430" class="dimension-text">${scaleLength / 1000} m</text>
  </g>
  <text x="${width / 2}" y="${depth + 1700}" class="small-label">${xml(plan.disclaimer)}</text>
</svg>`;
}

export function parametricFloorplanJson(plan) {
  return `${JSON.stringify(plan, null, 2)}\n`;
}
