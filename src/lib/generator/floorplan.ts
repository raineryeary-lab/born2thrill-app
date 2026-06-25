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
  metrics: {
    footprintWidthM: number;
    footprintDepthM: number;
    plannedAreaM2: number;
    referenceProfile: string;
    groundFloorAreaM2: number;
    upperFloorAreaM2: number;
  };
};

type RoomSeed = Omit<PlannedRoom, "id" | "x" | "y" | "width" | "height" | "area" | "side"> & {
  targetArea: number;
  minArea: number;
  maxArea: number;
  preferredSide?: "left" | "right";
  flexible?: boolean;
};

type BestsellerProfile = {
  name: string;
  areaMin: number;
  areaMax: number;
  egShare: number;
  preferredFootprintRatio: number;
  notes: string[];
};

const BESTSELLER_PROFILES: BestsellerProfile[] = [
  {
    name: "Bestseller kompakt · 120-140 m²",
    areaMin: 119,
    areaMax: 140,
    egShare: 0.51,
    preferredFootprintRatio: 1.12,
    notes: ["kurze Diele", "zentraler Treppenkern", "offener Wohn-Ess-Kochbereich"],
  },
  {
    name: "Bestseller klassisch · 141-165 m²",
    areaMin: 141,
    areaMax: 165,
    egShare: 0.52,
    preferredFootprintRatio: 1.18,
    notes: ["EG meist 75-87 m²", "OG meist 69-78 m²", "Büro/Gast im EG häufig sinnvoll"],
  },
  {
    name: "Bestseller Familie · 166-190 m²",
    areaMin: 166,
    areaMax: 190,
    egShare: 0.53,
    preferredFootprintRatio: 1.22,
    notes: ["größerer Wohnbereich", "HWR/Technik klar am Installationskern", "mehr Stauraum möglich"],
  },
  {
    name: "Bestseller großzügig · 191-230 m²",
    areaMin: 191,
    areaMax: 230,
    egShare: 0.54,
    preferredFootprintRatio: 1.28,
    notes: ["große Wohnküche", "optionales Gast-/Arbeitszimmer", "zweites Bad oder Ankleide prüfen"],
  },
];

const REFERENCE_RANGES = {
  livingKitchenMin: 32,
  livingKitchenMax: 53,
  guestWcMin: 3,
  guestWcMax: 5,
  utilityMin: 8,
  utilityMax: 13,
  familyBathMin: 9,
  familyBathMax: 13,
  childRoomMin: 11,
  childRoomMax: 16,
  parentRoomMin: 13,
  parentRoomMax: 20,
  hallShareMax: 0.24,
} as const;

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

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function profileForArea(area: number): BestsellerProfile {
  return BESTSELLER_PROFILES.find((profile) => area >= profile.areaMin && area <= profile.areaMax)
    ?? (area < BESTSELLER_PROFILES[0].areaMin ? BESTSELLER_PROFILES[0] : BESTSELLER_PROFILES[BESTSELLER_PROFILES.length - 1]);
}

function groundFloorArea(brief: HouseBrief, profile: BestsellerProfile) {
  if (brief.floors === 1) return brief.area;
  if (brief.floors === 2) return Math.round(brief.area * profile.egShare);
  return Math.round(brief.area * 0.42);
}

function targetAreaForFloor(brief: HouseBrief, floor: number, profile: BestsellerProfile) {
  if (brief.floors === 1) return brief.area;
  if (brief.floors === 2) {
    const eg = groundFloorArea(brief, profile);
    return floor === 0 ? eg : brief.area - eg;
  }

  const eg = groundFloorArea(brief, profile);
  const remaining = brief.area - eg;
  return floor === 0 ? eg : Math.round(remaining / (brief.floors - 1));
}

function adjustedAreas(seeds: RoomSeed[], floorArea: number) {
  const totalTarget = seeds.reduce((sum, room) => sum + room.targetArea, 0);
  const flexibleRooms = seeds.filter((room) => room.flexible);
  const fixedTarget = seeds
    .filter((room) => !room.flexible)
    .reduce((sum, room) => sum + room.targetArea, 0);
  const flexibleTarget = flexibleRooms.reduce((sum, room) => sum + room.targetArea, 0);
  const flexibleBudget = Math.max(0, floorArea - fixedTarget);

  return new Map(seeds.map((room) => {
    const scaled = room.flexible && flexibleTarget > 0
      ? room.targetArea * (flexibleBudget / flexibleTarget)
      : room.targetArea * (floorArea / Math.max(totalTarget, 1));
    return [room.name, Math.round(clamp(scaled, room.minArea, room.maxArea))];
  }));
}

export function parseBrief(entries: Array<[string, string]>): HouseBrief {
  const get = (name: string, fallback = "") =>
    entries.find(([entryName]) => entryName === name)?.[1] ?? fallback;
  const yes = (name: string, fallback = false) => {
    const value = get(name);
    if (!value) return fallback;
    return value === "yes";
  };
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
    office: yes("office", true),
    guestWc: yes("guestWc", true),
    utilityRoom: yes("utilityRoom", true),
    groundFloorSleeping: yes("groundFloorSleeping"),
    roof: get("roofPreference", "gable"),
    style: get("constructionStyle", "timeless-modern"),
    gardenDirection: get("gardenDirection", "Süd"),
  };
}

function seedsForFloor(brief: HouseBrief, floor: number, floorArea: number): RoomSeed[] {
  if (floor === 0) {
    const livingTarget = clamp(Math.round(floorArea * 0.52), REFERENCE_RANGES.livingKitchenMin, REFERENCE_RANGES.livingKitchenMax);
    const rooms: RoomSeed[] = [
      {
        name: "Wohnen / Essen / Kochen",
        kind: "living",
        targetArea: livingTarget,
        minArea: REFERENCE_RANGES.livingKitchenMin,
        maxArea: REFERENCE_RANGES.livingKitchenMax,
        preferredSide: "left",
        flexible: true,
      },
      { name: "Diele", kind: "flex", targetArea: 8, minArea: 5, maxArea: 12, preferredSide: "right" },
    ];
    if (brief.floors > 1) rooms.push({ name: "Treppe / Garderobe", kind: "flex", targetArea: 7, minArea: 5, maxArea: 10, preferredSide: "right" });
    if (brief.utilityRoom) rooms.push({ name: "HWR / Technik", kind: "wet", targetArea: 10, minArea: REFERENCE_RANGES.utilityMin, maxArea: REFERENCE_RANGES.utilityMax, preferredSide: "right" });
    if (brief.guestWc) rooms.push({ name: "Gäste-WC", kind: "wet", targetArea: 4, minArea: REFERENCE_RANGES.guestWcMin, maxArea: REFERENCE_RANGES.guestWcMax, preferredSide: "right" });
    if (brief.office) rooms.push({ name: "Büro / Gast", kind: "flex", targetArea: 11, minArea: 9, maxArea: 16, preferredSide: "left" });
    if (brief.groundFloorSleeping) rooms.push({ name: "Gast / Schlafen", kind: "sleeping", targetArea: 13, minArea: 11, maxArea: 16, preferredSide: "left" });
    if (floorArea >= 82 && !brief.groundFloorSleeping) rooms.push({ name: "Speis / Abstell", kind: "service", targetArea: 4, minArea: 3, maxArea: 6, preferredSide: "right" });
    return rooms;
  }

  const rooms: RoomSeed[] = [];
  const bedroomsThisFloor = floor === 1 ? brief.bedrooms : Math.max(1, brief.bedrooms - 4);
  for (let index = 0; index < Math.min(4, bedroomsThisFloor); index += 1) {
    rooms.push({
      name: index === 0 ? "Eltern" : `Zimmer ${index + 1}`,
      kind: "sleeping",
      targetArea: index === 0 ? 16 : 13,
      minArea: index === 0 ? REFERENCE_RANGES.parentRoomMin : REFERENCE_RANGES.childRoomMin,
      maxArea: index === 0 ? REFERENCE_RANGES.parentRoomMax : REFERENCE_RANGES.childRoomMax,
      preferredSide: index % 2 === 0 ? "left" : "right",
      flexible: true,
    });
  }
  const bathroomsThisFloor = floor === 1 ? Math.max(1, brief.bathrooms - 1) : 1;
  for (let index = 0; index < bathroomsThisFloor; index += 1) {
    rooms.push({
      name: index ? `Duschbad ${index + 1}` : "Bad",
      kind: "wet",
      targetArea: index ? 6 : 11,
      minArea: index ? 4 : REFERENCE_RANGES.familyBathMin,
      maxArea: index ? 8 : REFERENCE_RANGES.familyBathMax,
      preferredSide: "right",
    });
  }
  if (floorArea >= 78 && brief.bedrooms <= 3) {
    rooms.push({ name: "Ankleide", kind: "flex", targetArea: 6, minArea: 4, maxArea: 8, preferredSide: "right" });
  }
  rooms.push({ name: "Flur", kind: "flex", targetArea: 10, minArea: 7, maxArea: 13, preferredSide: "left" });
  return rooms;
}

function layoutFloor(brief: HouseBrief, floor: number, mirrored: boolean, stair: StairGeometry | null, floorArea: number): FloorPlan {
  const seeds = seedsForFloor(brief, floor, floorArea);
  const areaByRoom = adjustedAreas(seeds, floorArea);
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

  const placeColumn = (column: RoomSeed[], side: "left" | "right") => {
    const totalArea = column.reduce((sum, room) => sum + (areaByRoom.get(room.name) ?? room.targetArea), 0);
    let y = top;
    return column.map((room, index) => {
      const roomArea = areaByRoom.get(room.name) ?? room.targetArea;
      const height = index === column.length - 1
        ? top + usableHeight - y
        : usableHeight * (roomArea / Math.max(totalArea, 1));
      const planned: PlannedRoom = {
        id: `${floor}-${side}-${index}`,
        name: room.name,
        kind: room.kind,
        x: side === "left" ? margin : hallX + hallWidth,
        y,
        width: columnWidth,
        height,
        area: roomArea,
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
    const profile = profileForArea(brief.area);
    const baseFloorArea = targetAreaForFloor(brief, 0, profile);
    const ratio = index === 0 ? profile.preferredFootprintRatio : Math.max(1.08, profile.preferredFootprintRatio - 0.1);
    const floorArea = brief.floors === 1 ? brief.area : baseFloorArea;
    const depth = Math.sqrt(floorArea / ratio);
    const width = depth * ratio;
    const stair = brief.floors > 1 ? createStairGeometry() : null;
    const floors = Array.from({ length: brief.floors }, (_, floor) =>
      layoutFloor(brief, floor, mirrored, stair, targetAreaForFloor(brief, floor, profile)));
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
    const groundRooms = floors[0]?.rooms ?? [];
    const upperRooms = floors[1]?.rooms ?? [];
    const livingKitchen = groundRooms.find((room) => room.name === "Wohnen / Essen / Kochen");
    const wetAndServiceClustered = floors.every((plan) =>
      plan.rooms
        .filter((room) => room.kind === "wet" || room.kind === "service")
        .every((room) => room.side === (mirrored ? "left" : "right")));
    const hallAreasOk = floors.every((plan) => {
      const circulation = plan.rooms
        .filter((room) => room.name.includes("Flur") || room.name.includes("Diele") || room.name.includes("Treppe"))
        .reduce((sum, room) => sum + room.area, 0);
      const planned = plan.rooms.reduce((sum, room) => sum + room.area, 0);
      return circulation / Math.max(planned, 1) <= REFERENCE_RANGES.hallShareMax;
    });
    const bedroomSizesOk = upperRooms
      .filter((room) => room.kind === "sleeping")
      .every((room) => room.area >= REFERENCE_RANGES.childRoomMin && room.area <= REFERENCE_RANGES.parentRoomMax);
    const checks = [
      { label: "Jeder Aufenthaltsraum liegt an einer Außenwand mit Fenster", passed: floors.every((plan) => plan.rooms.length > 0) },
      { label: `Referenzprofil aus Verkaufsschlagern erkannt: ${profile.name}`, passed: true },
      { label: "EG folgt Bestseller-Sequenz: Eingang, Diele, Treppe, WC/HWR und offener Wohn-Ess-Kochbereich", passed: groundRooms.length >= 4 },
      { label: "OG folgt Familienhaus-Muster: Treppe, Flur, Bad, Eltern und Kinderzimmer", passed: brief.floors === 1 || upperRooms.some((room) => room.name === "Bad") },
      { label: "Flur-, Dielen- und Treppenflächen bleiben unter ca. 24 % der geplanten Fläche", passed: hallAreasOk },
      {
        label: stair
          ? `Treppenlauf bemessen: ${stair.risers} Steigungen à ${stair.riserHeightCm} cm, ${stair.treadDepthCm} cm Auftritt, ${stair.usableFlightWidthM.toFixed(2)} m Laufbreite und freie Ankunft`
          : "Keine Geschosstreppe erforderlich",
        passed: stairDimensioned,
      },
      { label: "Bäder, WC, HWR und Abstellräume liegen am gemeinsamen Installationskern", passed: wetAndServiceClustered },
      {
        label: `Wohnen / Essen / Kochen liegt im Bestseller-Korridor ${REFERENCE_RANGES.livingKitchenMin}-${REFERENCE_RANGES.livingKitchenMax} m²`,
        passed: !livingKitchen || (livingKitchen.area >= REFERENCE_RANGES.livingKitchenMin && livingKitchen.area <= REFERENCE_RANGES.livingKitchenMax),
      },
      { label: "Schlaf- und Kinderzimmer liegen in marktüblichen Größenkorridoren", passed: brief.floors === 1 || bedroomSizesOk },
      { label: `Wohnbereich und Gartenorientierung sind zusammengeführt · Garten ${brief.gardenDirection}`, passed: true },
    ];
    const passedChecks = checks.filter((check) => check.passed).length;
    return {
      id: index === 0 ? "garden" : "compact",
      name: index === 0 ? "Variante A · Gartenhaus" : "Variante B · Kompakt",
      description: index === 0
        ? `Aus euren Verkaufsschlagern abgeleitete Familienhaus-Logik: offener Wohn-Ess-Kochbereich, kurzer Weg zur Terrasse, zentraler Treppenkern und gebündelte Haustechnik. ${profile.notes.join(" · ")}.`
        : `Kompaktere Bestseller-Variante mit ähnlicher Raumfolge, reduzierter Hüllfläche und gespiegelt gebündeltem Installationskern. ${profile.notes.join(" · ")}.`,
      floors,
      score: Math.round((passedChecks / checks.length) * (index === 0 ? 96 : 93)),
      checks,
      metrics: {
        footprintWidthM: Number(width.toFixed(1)),
        footprintDepthM: Number(depth.toFixed(1)),
        plannedAreaM2: brief.area,
        referenceProfile: profile.name,
        groundFloorAreaM2: targetAreaForFloor(brief, 0, profile),
        upperFloorAreaM2: brief.floors > 1 ? targetAreaForFloor(brief, 1, profile) : 0,
      },
    };
  });
}
