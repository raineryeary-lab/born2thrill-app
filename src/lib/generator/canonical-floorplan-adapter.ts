import fixtureSource from "./fixtures/bungalow_033.canonical.json";
import type {
  CanonicalFloorplan,
  PointMm,
  PolygonMm,
} from "./canonical-floorplan";
import { loadCanonicalFloorplan } from "./canonical-floorplan.mjs";
import type {
  FloorPlan,
  PlannedRoom,
  PlanVariant,
} from "./floorplan";

export const CANONICAL_BUNGALOW_GENERATOR_VERSION = "canonical-reference-v1";

function polygonAreaMm2(polygon: PolygonMm) {
  return Math.abs(polygon.reduce((sum, point, index) => {
    const next = polygon[(index + 1) % polygon.length];
    return sum + point[0] * next[1] - next[0] * point[1];
  }, 0) / 2);
}

function polygonBounds(polygon: PolygonMm) {
  const xs = polygon.map(([x]) => x);
  const ys = polygon.map(([, y]) => y);
  const x = Math.min(...xs);
  const y = Math.min(...ys);
  return {
    x,
    y,
    width: Math.max(...xs) - x,
    height: Math.max(...ys) - y,
  };
}

function rendererKind(roomType: string): PlannedRoom["kind"] {
  if (roomType === "living_dining_kitchen" || roomType === "living" || roomType === "dining" || roomType === "kitchen") {
    return "living";
  }
  if (roomType === "bedroom") return "sleeping";
  if (roomType === "bathroom" || roomType === "wc") return "wet";
  if (roomType === "circulation") return "circulation";
  if (roomType === "utility" || roomType === "storage" || roomType === "garage") return "service";
  return "flex";
}

function pointOnWall(
  start: PointMm,
  end: PointMm,
  distance: number,
): { x: number; y: number } {
  const length = Math.hypot(end[0] - start[0], end[1] - start[1]);
  const ratio = length > 0 ? distance / length : 0;
  return {
    x: start[0] + (end[0] - start[0]) * ratio,
    y: start[1] + (end[1] - start[1]) * ratio,
  };
}

function floorFromCanonical(
  plan: CanonicalFloorplan,
  storey: CanonicalFloorplan["storeys"][number],
): FloorPlan {
  const footprint = polygonBounds(plan.footprint.boundary_polygon_mm);
  const rooms = storey.rooms.map((room) => {
    const bounds = polygonBounds(room.polygon_mm);
    return {
      id: room.id,
      name: room.name,
      kind: rendererKind(room.room_type),
      ...bounds,
      area: Number((polygonAreaMm2(room.polygon_mm) / 1_000_000).toFixed(2)),
      side: bounds.x + bounds.width / 2 < footprint.x + footprint.width / 2 ? "left" : "right",
      zone: room.room_type === "living_dining_kitchen"
        ? "garden"
        : room.room_type === "circulation" || room.room_type === "utility"
          ? "core"
          : "street",
      polygon: room.polygon_mm.map(([x, y]) => ({ x, y })),
    } satisfies PlannedRoom;
  });
  const wallById = new Map(storey.walls.map((wall) => [wall.id, wall]));
  const referenceElements = storey.openings
    .filter((opening) => opening.opening_type !== "open_passage")
    .map((opening) => {
      const wall = wallById.get(opening.wall_id);
      if (!wall) throw new Error(`Canonical opening references missing wall: ${opening.id}`);
      return {
        id: opening.id,
        type: opening.opening_type,
        points: [
          pointOnWall(wall.start_mm, wall.end_mm, opening.offset_mm),
          pointOnWall(wall.start_mm, wall.end_mm, opening.offset_mm + opening.width_mm),
        ],
      };
    });

  return {
    floor: storey.level_index,
    name: storey.level_index === 0 ? "Erdgeschoss" : `Geschoss ${storey.level_index + 1}`,
    rooms,
    hasStair: false,
    stair: null,
    layoutMode: "central-stair",
    referenceFootprint: footprint,
    referenceFootprintPolygon: plan.footprint.boundary_polygon_mm.map(([x, y]) => ({ x, y })),
    referenceLayoutId: plan.plan_id,
    referenceElements,
  };
}

export function canonicalBungalow033Plan(): CanonicalFloorplan {
  return loadCanonicalFloorplan(
    fixtureSource as unknown as CanonicalFloorplan,
  );
}

export function canonicalBungalow033Variant(): PlanVariant {
  const plan = canonicalBungalow033Plan();
  const floors = plan.storeys.map((storey) => floorFromCanonical(plan, storey));
  const footprint = polygonBounds(plan.footprint.boundary_polygon_mm);
  const plannedAreaM2 = floors.reduce(
    (sum, floor) => sum + floor.rooms
      .filter((room) => room.id !== "garage")
      .reduce((floorSum, room) => floorSum + room.area, 0),
    0,
  );
  return {
    id: "canonical-bungalow-033",
    name: "Bungalow 033 – interner Prüfstand",
    description: "Deterministische kanonische Arbeitsfassung mit nutzerbestätigtem, abgeleitetem Maßstab.",
    floors,
    storeyType: "1_storey",
    stairCore: null,
    canonicalGeometrySha256: plan.geometry_hash.value,
    score: 100,
    checks: [
      { label: "Kanonisches JSON ist geometrisch und topologisch gültig", passed: true },
      { label: "Eingang und alle zugangspflichtigen Räume sind verbunden", passed: true },
      { label: "Angefordertes Raumprogramm ist in der Referenz vollständig vorhanden", passed: false },
    ],
    metrics: {
      footprintWidthM: footprint.width / 1000,
      footprintDepthM: footprint.height / 1000,
      plannedAreaM2: Number(plannedAreaM2.toFixed(2)),
      referenceProfile: "canonical-internal-review",
      groundFloorAreaM2: Number(plannedAreaM2.toFixed(2)),
      upperFloorAreaM2: 0,
      referenceLayoutId: plan.plan_id,
      storeyType: "1_storey",
    },
  };
}
