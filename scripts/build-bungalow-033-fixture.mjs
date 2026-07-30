import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  validateCanonicalFloorplan,
  withCanonicalGeometryHash,
} from "../src/lib/generator/canonical-floorplan.mjs";

const ROOM_DEFINITIONS = [
  {
    id: "ankleide",
    name: "Ankleide",
    room_type: "storage",
    access_required: true,
    habitable: false,
    polygon_mm: [[0, 0], [2200, 0], [2200, 3600], [0, 3600]],
  },
  {
    id: "eltern",
    name: "Eltern / Schlafen",
    room_type: "bedroom",
    access_required: true,
    habitable: true,
    polygon_mm: [[2200, 0], [5530, 0], [5530, 3600], [2200, 3600]],
  },
  {
    id: "wohnen",
    name: "Wohnen / Essen / Kochen",
    room_type: "living_dining_kitchen",
    access_required: true,
    habitable: true,
    polygon_mm: [
      [5530, 0],
      [11900, 0],
      [11900, 7000],
      [9400, 7000],
      [9400, 8000],
      [11900, 8000],
      [11900, 9400],
      [9400, 9400],
      [9400, 8100],
      [5530, 8100],
    ],
  },
  {
    id: "bad",
    name: "Bad",
    room_type: "bathroom",
    access_required: true,
    habitable: false,
    polygon_mm: [[0, 3600], [2800, 3600], [2800, 6100], [0, 6100]],
  },
  {
    id: "flur",
    name: "Flur",
    room_type: "circulation",
    access_required: true,
    habitable: false,
    polygon_mm: [
      [2800, 3600],
      [5530, 3600],
      [5530, 8100],
      [4000, 8100],
      [4000, 6100],
      [2800, 6100],
    ],
  },
  {
    id: "kind_1",
    name: "Kind",
    room_type: "bedroom",
    access_required: true,
    habitable: true,
    polygon_mm: [[0, 6100], [4000, 6100], [4000, 8600], [0, 8600]],
  },
  {
    id: "kind_2",
    name: "Kind",
    room_type: "bedroom",
    access_required: true,
    habitable: true,
    polygon_mm: [[0, 8600], [4000, 8600], [4000, 11100], [0, 11100]],
  },
  {
    id: "hwr_htr",
    name: "HWR / HTR",
    room_type: "utility",
    access_required: true,
    habitable: false,
    polygon_mm: [
      [4000, 9400],
      [6500, 9400],
      [6500, 11900],
      [0, 11900],
      [0, 11100],
      [4000, 11100],
    ],
  },
  {
    id: "du_bad",
    name: "Duschbad",
    room_type: "bathroom",
    access_required: true,
    habitable: false,
    polygon_mm: [[6500, 9400], [7900, 9400], [7900, 11900], [6500, 11900]],
  },
  {
    id: "diele",
    name: "Diele",
    room_type: "circulation",
    access_required: true,
    habitable: false,
    polygon_mm: [
      [4000, 8100],
      [9400, 8100],
      [9400, 9400],
      [11900, 9400],
      [11900, 11900],
      [7900, 11900],
      [7900, 9400],
      [4000, 9400],
    ],
  },
  {
    id: "speisekammer",
    name: "Speisekammer",
    room_type: "storage",
    access_required: true,
    habitable: false,
    polygon_mm: [[9400, 7000], [11900, 7000], [11900, 8000], [9400, 8000]],
  },
  {
    id: "garage",
    name: "Garage",
    room_type: "garage",
    access_required: true,
    habitable: false,
    polygon_mm: [[11900, 5400], [16900, 5400], [16900, 11900], [11900, 11900]],
  },
];

const FOOTPRINT = [
  [0, 0],
  [11900, 0],
  [11900, 5400],
  [16900, 5400],
  [16900, 11900],
  [0, 11900],
];

function polygonEdges(polygon) {
  return polygon.map((start, index) => {
    const end = polygon[(index + 1) % polygon.length];
    if (start[0] !== end[0] && start[1] !== end[1]) {
      throw new Error(`Non-rectilinear fixture edge: ${JSON.stringify([start, end])}`);
    }
    if (start[1] === end[1]) {
      return {
        axis: "h",
        coordinate: start[1],
        start: Math.min(start[0], end[0]),
        end: Math.max(start[0], end[0]),
      };
    }
    return {
      axis: "v",
      coordinate: start[0],
      start: Math.min(start[1], end[1]),
      end: Math.max(start[1], end[1]),
    };
  });
}

function edgeCovers(edge, start, end) {
  return edge.start <= start && edge.end >= end;
}

function unorderedPair(left, right) {
  return left.length === right.length
    && left.every((value) => right.includes(value));
}

function buildWalls(rooms, footprint) {
  const roomEdges = rooms.flatMap((room) =>
    polygonEdges(room.polygon_mm).map((edge) => ({ ...edge, room_id: room.id })),
  );
  const footprintEdges = polygonEdges(footprint);
  const lineKeys = new Set(
    roomEdges.map((edge) => `${edge.axis}:${edge.coordinate}`),
  );
  const raw = [];

  for (const lineKey of [...lineKeys].sort()) {
    const [axis, coordinateText] = lineKey.split(":");
    const coordinate = Number(coordinateText);
    const onLine = roomEdges.filter(
      (edge) => edge.axis === axis && edge.coordinate === coordinate,
    );
    const breakpoints = [...new Set(onLine.flatMap((edge) => [edge.start, edge.end]))]
      .sort((left, right) => left - right);
    for (let index = 0; index < breakpoints.length - 1; index += 1) {
      const start = breakpoints[index];
      const end = breakpoints[index + 1];
      if (end <= start) continue;
      const adjacent = [...new Set(
        onLine.filter((edge) => edgeCovers(edge, start, end)).map((edge) => edge.room_id),
      )].sort();
      if (!adjacent.length) continue;
      if (adjacent.length > 2) {
        throw new Error(`Invalid wall adjacency ${lineKey}:${start}-${end}`);
      }
      const onFootprint = footprintEdges.some(
        (edge) => edge.axis === axis
          && edge.coordinate === coordinate
          && edgeCovers(edge, start, end),
      );
      if (adjacent.length === 1 && !onFootprint) {
        throw new Error(`Internal fixture gap ${lineKey}:${start}-${end}`);
      }
      const separates = adjacent.length === 1
        ? [adjacent[0], "outside"]
        : adjacent;
      raw.push({
        axis,
        coordinate,
        start,
        end,
        wall_type: adjacent.length === 1 ? "exterior" : "partition",
        thickness_mm: adjacent.length === 1 ? 350 : 100,
        separates,
      });
    }
  }

  const merged = [];
  for (const wall of raw.sort((left, right) =>
    left.axis.localeCompare(right.axis)
      || left.coordinate - right.coordinate
      || left.start - right.start
  )) {
    const previous = merged.at(-1);
    if (
      previous
      && previous.axis === wall.axis
      && previous.coordinate === wall.coordinate
      && previous.end === wall.start
      && previous.wall_type === wall.wall_type
      && unorderedPair(previous.separates, wall.separates)
    ) {
      previous.end = wall.end;
    } else {
      merged.push({ ...wall });
    }
  }

  return merged.map((wall, index) => ({
    id: `wall_${String(index + 1).padStart(3, "0")}`,
    wall_type: wall.wall_type,
    start_mm: wall.axis === "h"
      ? [wall.start, wall.coordinate]
      : [wall.coordinate, wall.start],
    end_mm: wall.axis === "h"
      ? [wall.end, wall.coordinate]
      : [wall.coordinate, wall.end],
    thickness_mm: wall.thickness_mm,
    separates: wall.separates,
  }));
}

function wallLength(wall) {
  return Math.hypot(
    wall.end_mm[0] - wall.start_mm[0],
    wall.end_mm[1] - wall.start_mm[1],
  );
}

function buildOpenings(walls) {
  const openings = [];
  const intervals = new Map();

  function matchingWalls(first, second) {
    return walls
      .filter((wall) => unorderedPair(wall.separates, [first, second]))
      .sort((left, right) => wallLength(right) - wallLength(left));
  }

  function availableOffset(wall, width) {
    const length = wallLength(wall);
    const occupied = intervals.get(wall.id) ?? [];
    const candidates = [
      Math.round((length - width) / 2),
      400,
      Math.max(400, length - width - 400),
    ];
    return candidates.find((offset) =>
      offset >= 0
      && offset + width <= length
      && occupied.every(([start, end]) => Math.max(start, offset) >= Math.min(end, offset + width))
    );
  }

  function add(id, openingType, first, second, width, windowDimensions = null) {
    for (const wall of matchingWalls(first, second)) {
      const offset = availableOffset(wall, width);
      if (offset === undefined) continue;
      const opening = {
        id,
        opening_type: openingType,
        wall_id: wall.id,
        offset_mm: offset,
        width_mm: width,
        connects: [first, second],
        traversable: openingType !== "window",
      };
      if (windowDimensions) {
        opening.sill_height_mm = windowDimensions.sill;
        opening.height_mm = windowDimensions.height;
      }
      openings.push(opening);
      const occupied = intervals.get(wall.id) ?? [];
      occupied.push([offset, offset + width]);
      intervals.set(wall.id, occupied);
      return;
    }
    throw new Error(`No wall available for opening ${id}: ${first}/${second}`);
  }

  add("door_entrance", "door", "diele", "outside", 1000);
  add("door_diele_living", "open_passage", "diele", "wohnen", 1400);
  add("door_diele_flur", "open_passage", "diele", "flur", 1200);
  add("door_diele_hwr", "door", "diele", "hwr_htr", 900);
  add("door_diele_du", "door", "diele", "du_bad", 900);
  add("door_diele_kind_2", "door", "diele", "kind_2", 800);
  add("door_flur_bad", "door", "flur", "bad", 900);
  add("door_flur_kind_1", "door", "flur", "kind_1", 900);
  add("door_flur_eltern", "door", "flur", "eltern", 900);
  add("door_eltern_ankleide", "door", "eltern", "ankleide", 900);
  add("door_living_pantry", "door", "wohnen", "speisekammer", 800);
  add("door_diele_garage", "door", "diele", "garage", 900);
  add("door_garage_vehicle", "door", "garage", "outside", 3000);

  const window = { sill: 900, height: 1300 };
  add("window_eltern", "window", "eltern", "outside", 1800, window);
  add("window_bad", "window", "bad", "outside", 1200, { sill: 1200, height: 900 });
  add("window_kind_1", "window", "kind_1", "outside", 1600, window);
  add("window_kind_2", "window", "kind_2", "outside", 1600, window);
  add("window_living", "window", "wohnen", "outside", 2400, { sill: 300, height: 2100 });
  add("window_hwr", "window", "hwr_htr", "outside", 1200, { sill: 1100, height: 900 });
  add("window_du", "window", "du_bad", "outside", 1000, { sill: 1200, height: 900 });

  return openings;
}

const walls = buildWalls(ROOM_DEFINITIONS, FOOTPRINT);
const openings = buildOpenings(walls);
const fixture = withCanonicalGeometryHash({
  schema_version: "dmh-canonical-floorplan-v1",
  plan_id: "bungalow_033_inferred_v1",
  units: "mm",
  coordinate_system: {
    origin: "northwest",
    x_positive: "east",
    y_positive: "south",
    integer_precision_mm: 1,
    north_rotation_degrees: null,
    wall_reference: "centerline",
  },
  building: {
    storey_type: "1_storey",
  },
  footprint: {
    boundary_reference: "exterior_wall_centerline",
    boundary_polygon_mm: FOOTPRINT,
  },
  storeys: [
    {
      id: "groundfloor",
      level_index: 0,
      elevation_mm: 0,
      planning_boundary_mm: FOOTPRINT,
      rooms: ROOM_DEFINITIONS,
      walls,
      openings,
      slab_openings: [],
    },
  ],
  entrance: {
    storey_id: "groundfloor",
    opening_id: "door_entrance",
    enters_room_id: "diele",
  },
  stairs: [],
  provenance: {
    source_kind: "real_annotated",
    source_project_id: "bungalow_033",
    source_schema_version: "simplifier-annotations-v1",
    source_annotation_sha256: "bf0d61d01c408ac220706d54f107b010208cb0e3622e5a900027b6d2dc50a114",
    conversion_method: "user-confirmed inferred 11900 mm main-house width; room polygons redrawn to the confirmed target areas",
    scale_anchor: {
      status: "user_confirmed_inferred",
      kind: "overall_width",
      source_segment_normalized: [[0.072749, 0.053857], [0.696824, 0.053857]],
      length_mm: 11900,
    },
  },
  geometry_hash: {
    algorithm: "sha256",
    canonicalization: "dmh-canonical-geometry-v1",
    value: "0".repeat(64),
  },
  approval: {
    state: "internal_reference",
    quality_status: "review_required",
    rights_status: "not_explicitly_recorded",
    usage_scope: "internal_reference_only",
    approved_by: null,
    approved_at: null,
    rights_evidence_reference: null,
  },
});

const report = validateCanonicalFloorplan(fixture);
if (!report.passed) {
  throw new Error(`Generated fixture is invalid: ${report.errors.join(", ")}`);
}

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const outputDirectory = path.resolve(scriptDirectory, "../src/lib/generator/fixtures");
const outputPath = path.join(outputDirectory, "bungalow_033.canonical.json");
await mkdir(outputDirectory, { recursive: true });
await writeFile(outputPath, `${JSON.stringify(fixture, null, 2)}\n`, "utf8");
console.log(`Wrote ${outputPath}`);
console.log(JSON.stringify(report, null, 2));
