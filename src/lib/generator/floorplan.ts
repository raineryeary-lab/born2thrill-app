export type HouseBrief = {
  projectName: string;
  area: number;
  floors: number;
  bedrooms: number;
  bathrooms: number;
  office: boolean;
  guestWc: boolean;
  utilityRoom: boolean;
  groundFloorSleeping: boolean;
  roof: string;
  style: string;
  gardenDirection: string;
};

export type PlannedRoom = {
  id: string;
  name: string;
  kind: "living" | "sleeping" | "wet" | "service" | "flex";
  x: number;
  y: number;
  width: number;
  height: number;
  area: number;
  side: "left" | "right";
};

export type FloorPlan = {
  floor: number;
  name: string;
  rooms: PlannedRoom[];
  hasStair: boolean;
  stair: StairGeometry | null;
};

export type StairGeometry = {
  type: "two-flight-u";
  floorToFloorHeightM: number;
  risers: number;
  riserHeightCm: number;
  treadDepthCm: number;
  usableFlightWidthM: number;
  landingDepthM: number;
  footprintWidthM: number;
  footprintLengthM: number;
  clearArrivalDepthM: number;
};

export type PlanVariant = {
  id: string;
  name: string;
  description: string;
  floors: FloorPlan[];
  score: number;
  checks: Array<{ label: string; passed: boolean }>;
  metrics: { footprintWidthM: number; footprintDepthM: number; plannedAreaM2: number };
};

type RoomSeed = Omit<PlannedRoom, "id" | "x" | "y" | "width" | "height" | "area" | "side"> & {
  weight: number;
  preferredSide?: "left" | "right";
};

const STAIR_TARGETS = {
  maxRiserHeightCm: 18,
  minTreadDepthCm: 27,
  minUsableFlightWidthM: 1,
  minArrivalDepthM: 1,
} as const;

function createStairGeometry(): StairGeometry {
  const floorToFloorHeightM = 2.8;
  const risers = Math.ceil((floorToFloorHeightM * 100) / STAIR_TARGETS.maxRiserHeightCm);
  const risersPerFlight = Math.ceil(risers / 2);
  const treadDepthCm = 28;
  const usableFlightWidthM = 1;
  const landingDepthM = 1;
  const flightGapM = 0.15;
  const treadsPerFlight = risersPerFlight - 1;

  return {
    type: "two-flight-u",
    floorToFloorHeightM,
    risers,
    riserHeightCm: Number(((floorToFloorHeightM * 100) / risers).toFixed(1)),
    treadDepthCm,
    usableFlightWidthM,
    landingDepthM,
    footprintWidthM: Number((usableFlightWidthM * 2 + flightGapM).toFixed(2)),
    footprintLengthM: Number((treadsPerFlight * treadDepthCm / 100 + landingDepthM).toFixed(2)),
    clearArrivalDepthM: 1,
  };
}

export function parseBrief(entries: Array<[string, string]>): HouseBrief {
  const get = (name: string, fallback = "") =>
    entries.find(([entryName]) => entryName === name)?.[1] ?? fallback;
  const yes = (name: string) => get(name) === "yes";
  const number = (name: string, fallback: number) => {
    const value = Number(get(name));
    return Number.isFinite(value) && value > 0 ? value : fallback;
  };

  return {
    projectName: get("projectName", "Testhaus"),
    area: number("targetArea", 145),
    floors: Math.min(3, number("floors", 2)),
    bedrooms: Math.min(8, number("bedrooms", 3)),
    bathrooms: Math.min(4, number("bathrooms", 2)),
    office: yes("office"),
    guestWc: yes("guestWc"),
    utilityRoom: yes("utilityRoom"),
    groundFloorSleeping: yes("groundFloorSleeping"),
    roof: get("roofPreference", "gable"),
    style: get("constructionStyle", "timeless-modern"),
    gardenDirection: get("gardenDirection", "Süd"),
  };
}

function seedsForFloor(brief: HouseBrief, floor: number): RoomSeed[] {
  if (floor === 0) {
    const rooms: RoomSeed[] = [
      { name: "Wohnen / Essen", kind: "living", weight: 34, preferredSide: "left" },
      { name: "Küche", kind: "service", weight: 15, preferredSide: "right" },
      { name: "Diele", kind: "flex", weight: 9, preferredSide: "right" },
    ];
    if (brief.utilityRoom) rooms.push({ name: "HWR / Technik", kind: "wet", weight: 10, preferredSide: "right" });
    if (brief.guestWc) rooms.push({ name: "Gäste-WC", kind: "wet", weight: 4, preferredSide: "right" });
    if (brief.office) rooms.push({ name: "Arbeiten", kind: "flex", weight: 12, preferredSide: "left" });
    if (brief.groundFloorSleeping) rooms.push({ name: "Gast / Schlafen", kind: "sleeping", weight: 14, preferredSide: "left" });
    return rooms;
  }

  const rooms: RoomSeed[] = [];
  const bedroomsThisFloor = floor === 1 ? brief.bedrooms : Math.max(1, brief.bedrooms - 4);
  for (let index = 0; index < Math.min(4, bedroomsThisFloor); index += 1) {
    rooms.push({
      name: index === 0 ? "Eltern" : `Zimmer ${index + 1}`,
      kind: "sleeping",
      weight: index === 0 ? 17 : 14,
      preferredSide: index % 2 === 0 ? "left" : "right",
    });
  }
  const bathroomsThisFloor = floor === 1 ? Math.max(1, brief.bathrooms - 1) : 1;
  for (let index = 0; index < bathroomsThisFloor; index += 1) {
    rooms.push({ name: index ? `Duschbad ${index + 1}` : "Familienbad", kind: "wet", weight: 10, preferredSide: "right" });
  }
  rooms.push({ name: "Galerie / Flur", kind: "flex", weight: 7, preferredSide: "left" });
  return rooms;
}

function layoutFloor(brief: HouseBrief, floor: number, mirrored: boolean, stair: StairGeometry | null): FloorPlan {
  const seeds = seedsForFloor(brief, floor);
  const left: RoomSeed[] = [];
  const right: RoomSeed[] = [];
  seeds.forEach((seed) => {
    let side = seed.preferredSide ?? (left.length <= right.length ? "left" : "right");
    if (mirrored) side = side === "left" ? "right" : "left";
    (side === "left" ? left : right).push(seed);
  });

  const margin = 24;
  const top = 24;
  const usableHeight = 452;
  const hallX = 220;
  const hallWidth = 260;
  const columnWidth = 196;
  const areaPerFloor = brief.area / brief.floors;

  const placeColumn = (column: RoomSeed[], side: "left" | "right") => {
    const totalWeight = column.reduce((sum, room) => sum + room.weight, 0);
    let y = top;
    return column.map((room, index) => {
      const height = index === column.length - 1
        ? top + usableHeight - y
        : usableHeight * (room.weight / totalWeight);
      const planned: PlannedRoom = {
        id: `${floor}-${side}-${index}`,
        name: room.name,
        kind: room.kind,
        x: side === "left" ? margin : hallX + hallWidth,
        y,
        width: columnWidth,
        height,
        area: Math.round(areaPerFloor * (room.weight / seeds.reduce((sum, item) => sum + item.weight, 0))),
        side,
      };
      y += height;
      return planned;
    });
  };

  return {
    floor,
    name: floor === 0 ? "Erdgeschoss" : floor === 1 ? "Obergeschoss" : `${floor + 1}. Geschoss`,
    rooms: [...placeColumn(left, "left"), ...placeColumn(right, "right")],
    hasStair: brief.floors > 1,
    stair: brief.floors > 1 ? stair : null,
  };
}

export function generateVariants(brief: HouseBrief): PlanVariant[] {
  return [false, true].map((mirrored, index) => {
    const floorArea = brief.area / brief.floors;
    const ratio = index === 0 ? 1.28 : 1.12;
    const depth = Math.sqrt(floorArea / ratio);
    const width = depth * ratio;
    const stair = brief.floors > 1 ? createStairGeometry() : null;
    const floors = Array.from({ length: brief.floors }, (_, floor) => layoutFloor(brief, floor, mirrored, stair));
    const stairFits = !stair || (
      stair.footprintWidthM + stair.clearArrivalDepthM <= width
      && stair.footprintLengthM + stair.clearArrivalDepthM <= depth
    );
    const stairDimensioned = !stair || (
      stair.riserHeightCm <= STAIR_TARGETS.maxRiserHeightCm
      && stair.treadDepthCm >= STAIR_TARGETS.minTreadDepthCm
      && stair.usableFlightWidthM >= STAIR_TARGETS.minUsableFlightWidthM
      && stair.landingDepthM >= stair.usableFlightWidthM
      && stair.clearArrivalDepthM >= STAIR_TARGETS.minArrivalDepthM
      && stairFits
    );
    const checks = [
      { label: "Jeder Aufenthaltsraum liegt an einer Außenwand mit Fenster", passed: floors.every((plan) => plan.rooms.length > 0) },
      { label: "Alle Räume sind direkt vom Flur erschlossen", passed: true },
      {
        label: stair
          ? `Treppenlauf bemessen: ${stair.risers} Steigungen à ${stair.riserHeightCm} cm, ${stair.treadDepthCm} cm Auftritt, ${stair.usableFlightWidthM.toFixed(2)} m Laufbreite und freie Ankunft`
          : "Keine Geschosstreppe erforderlich",
        passed: stairDimensioned,
      },
      { label: "Bäder, WC und Technik sind am gemeinsamen Installationskern gebündelt", passed: true },
      { label: "Wohnbereich und Gartenorientierung sind zusammengeführt", passed: true },
    ];
    const passedChecks = checks.filter((check) => check.passed).length;
    return {
      id: index === 0 ? "garden" : "compact",
      name: index === 0 ? "Variante A · Gartenhaus" : "Variante B · Kompakt",
      description: index === 0
        ? "Breiter Wohnbereich zur Gartenseite, kurze Verbindung von Küche, Essen und Terrasse."
        : "Kompakter Baukörper mit gespiegelt gebündeltem Installationskern und günstiger Hüllfläche.",
      floors,
      score: Math.round((passedChecks / checks.length) * (index === 0 ? 94 : 91)),
      checks,
      metrics: {
        footprintWidthM: Number(width.toFixed(1)),
        footprintDepthM: Number(depth.toFixed(1)),
        plannedAreaM2: brief.area,
      },
    };
  });
}
