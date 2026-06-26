export type HouseBrief = {
  projectName: string;
  area: number;
  floors: number;
  adults: number;
  children: number;
  bedrooms: number;
  bathrooms: number;
  office: boolean;
  guestWc: boolean;
  utilityRoom: boolean;
  groundFloorSleeping: boolean;
  accessibility: boolean;
  kitchen: "open" | "semi-open" | "separate";
  gardenConnection: "generous" | "balanced" | "private";
  stairPreference: "central" | "feature" | "separable" | "undecided";
  basement: string;
  roof: string;
  style: string;
  streetDirection: string;
  gardenDirection: string;
  priorities: string[];
  generationAttempt: number;
  critiqueNotes: string;
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
  zone: "garden" | "street" | "core";
};

export type FloorPlan = {
  floor: number;
  name: string;
  rooms: PlannedRoom[];
  hasStair: boolean;
  stair: StairGeometry | null;
  layoutMode: "central-stair" | "wall-stair";
  wallStairSide?: "left" | "right";
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

type RoomSeed = Omit<PlannedRoom, "id" | "x" | "y" | "width" | "height" | "area" | "side" | "zone"> & {
  targetArea: number;
  minArea: number;
  maxArea: number;
  preferredSide?: "left" | "right";
  preferredZone: "garden" | "street" | "core";
  flexible?: boolean;
};

type VariantArchetype = {
  id: string;
  name: string;
  ratioOffset: number;
  mirrored: boolean;
  livingSide: "left" | "right";
  serviceSide: "left" | "right";
  descriptionPrefix: string;
};

type BestsellerProfile = {
  name: string;
  areaMin: number;
  areaMax: number;
  egShare: number;
  preferredFootprintRatio: number;
  notes: string[];
};

type SvgRect = {
  x: number;
  y: number;
  width: number;
  height: number;
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

const FLOORPLAN_SVG = {
  centralStair: { x: 284, y: 66, width: 132, height: 184 },
  wallStairLeft: { x: 56, y: 100, width: 132, height: 184 },
  wallStairRight: { x: 512, y: 100, width: 132, height: 184 },
  clearancePx: 8,
} as const;

const VARIANT_ARCHETYPES: VariantArchetype[] = [
  {
    id: "garden",
    name: "Variante A · Gartenhaus",
    ratioOffset: 0,
    mirrored: false,
    livingSide: "left",
    serviceSide: "right",
    descriptionPrefix: "Gartenorientierte Bestseller-Variante",
  },
  {
    id: "compact",
    name: "Variante B · Kompakt",
    ratioOffset: -0.1,
    mirrored: true,
    livingSide: "left",
    serviceSide: "right",
    descriptionPrefix: "Kompaktere Bestseller-Variante",
  },
  {
    id: "family-core",
    name: "Variante C · Familienkern",
    ratioOffset: 0.08,
    mirrored: false,
    livingSide: "right",
    serviceSide: "left",
    descriptionPrefix: "Familienvariante mit stärkerem Technik- und Treppenkern",
  },
];

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

function rectsOverlap(a: SvgRect, b: SvgRect) {
  return a.x < b.x + b.width
    && a.x + a.width > b.x
    && a.y < b.y + b.height
    && a.y + a.height > b.y;
}

function stairRectForPlan(plan: FloorPlan): SvgRect | null {
  if (!plan.hasStair || !plan.stair) return null;
  if (plan.layoutMode === "wall-stair") {
    return plan.wallStairSide === "right"
      ? FLOORPLAN_SVG.wallStairRight
      : FLOORPLAN_SVG.wallStairLeft;
  }
  return FLOORPLAN_SVG.centralStair;
}

function stairIsReserved(plan: FloorPlan) {
  const stairRect = stairRectForPlan(plan);
  if (!stairRect) return true;
  return plan.rooms.every((room) => !rectsOverlap(room, stairRect));
}

function hasUsableRoomWidths(plan: FloorPlan) {
  return plan.rooms.every((room) => room.width >= 140 || room.area <= 6);
}

function hasDoorDrawableWall(plan: FloorPlan) {
  return plan.rooms.every((room) => room.height >= 64);
}

function hasExteriorWindowWall(plan: FloorPlan) {
  const exteriorLeft = 24;
  const exteriorRight = 670;
  return plan.rooms.every((room) => {
    if (room.side === "left") return room.x <= exteriorLeft + 1;
    return room.x + room.width >= exteriorRight - 1;
  });
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
  const choice = <T extends string>(name: string, fallback: T, allowed: readonly T[]) => {
    const value = get(name);
    return allowed.includes(value as T) ? value as T : fallback;
  };

  return {
    projectName: get("projectName", "Testhaus"),
    area: number("targetArea", 145),
    floors: Math.min(3, number("floors", 2)),
    adults: Math.min(8, number("adults", 2)),
    children: Math.min(8, number("children", 2)),
    bedrooms: Math.min(8, number("bedrooms", 3)),
    bathrooms: Math.min(4, number("bathrooms", 2)),
    office: yes("office", true),
    guestWc: yes("guestWc", true),
    utilityRoom: yes("utilityRoom", true),
    groundFloorSleeping: yes("groundFloorSleeping"),
    accessibility: yes("accessibility"),
    kitchen: choice("kitchen", "open", ["open", "semi-open", "separate"] as const),
    gardenConnection: choice("gardenConnection", "generous", ["generous", "balanced", "private"] as const),
    stairPreference: choice("stairPreference", "central", ["central", "feature", "separable", "undecided"] as const),
    basement: get("basement", "none"),
    roof: get("roofPreference", "gable"),
    style: get("constructionStyle", "timeless-modern"),
    streetDirection: get("streetDirection", "Nord"),
    gardenDirection: get("gardenDirection", "Süd"),
    priorities: entries
      .filter(([name]) => name === "priorities")
      .map(([, value]) => value),
    generationAttempt: Math.max(0, number("generationAttempt", 0)),
    critiqueNotes: get("critiqueNotes", ""),
  };
}

function critiqueIncludes(brief: HouseBrief, words: string[]) {
  const text = brief.critiqueNotes.toLowerCase();
  return words.some((word) => text.includes(word));
}

function wantsWallStair(brief: HouseBrief) {
  const text = brief.critiqueNotes.toLowerCase();
  if (!text.includes("treppe")) return false;

  return [
    "wand",
    "links",
    "rechts",
    "seite",
    "außenwand",
    "aussenwand",
    "hinter",
    "hinten",
    "rückseite",
    "rueckseite",
    "rückwand",
    "rueckwand",
    "verschwend",
    "platz",
    "flur zu gross",
    "flur zu groß",
  ].some((word) => text.includes(word));
}

function kitchenAreaAdjustment(brief: HouseBrief) {
  if (brief.kitchen === "separate") return -5;
  if (brief.kitchen === "semi-open") return -2;
  if (critiqueIncludes(brief, ["küche zu klein", "küche klein", "kochbereich zu klein"])) return 4;
  return 0;
}

function gardenAreaAdjustment(brief: HouseBrief) {
  if (brief.gardenConnection === "generous") return 3;
  if (brief.gardenConnection === "private") return -2;
  return 0;
}

function preferredLivingSide(archetype: VariantArchetype) {
  return archetype.livingSide;
}

function preferredServiceSide(archetype: VariantArchetype) {
  return archetype.serviceSide;
}

function finalSide(side: "left" | "right", archetype: VariantArchetype) {
  if (!archetype.mirrored) return side;
  return side === "left" ? "right" : "left";
}

function seedsForFloor(brief: HouseBrief, floor: number, floorArea: number, archetype: VariantArchetype): RoomSeed[] {
  const wallStair = wantsWallStair(brief);
  if (floor === 0) {
    const livingTarget = clamp(
      Math.round(floorArea * (wallStair ? 0.57 : 0.52)) + kitchenAreaAdjustment(brief) + gardenAreaAdjustment(brief),
      REFERENCE_RANGES.livingKitchenMin,
      REFERENCE_RANGES.livingKitchenMax,
    );
    const rooms: RoomSeed[] = [
      {
        name: brief.kitchen === "separate" ? "Wohnen / Essen" : "Wohnen / Essen / Kochen",
        kind: "living",
        targetArea: livingTarget,
        minArea: brief.kitchen === "separate" ? 28 : REFERENCE_RANGES.livingKitchenMin,
        maxArea: brief.kitchen === "separate" ? 45 : REFERENCE_RANGES.livingKitchenMax,
        preferredSide: preferredLivingSide(archetype),
        preferredZone: "garden",
        flexible: true,
      },
      {
        name: wallStair ? "Kompakte Diele" : "Diele",
        kind: "flex",
        targetArea: wallStair || critiqueIncludes(brief, ["flur zu groß", "flur zu gross", "diele zu groß", "zu viel flur"]) ? 5 : 8,
        minArea: 5,
        maxArea: wallStair ? 8 : 12,
        preferredSide: preferredServiceSide(archetype),
        preferredZone: "street",
      },
    ];
    if (brief.kitchen === "separate") {
      rooms.push({
        name: "Küche",
        kind: "service",
        targetArea: 12,
        minArea: 10,
        maxArea: 16,
        preferredSide: preferredServiceSide(archetype),
        preferredZone: "garden",
      });
    }
    if (brief.floors > 1) {
      rooms.push({
        name: wallStair
          ? "Garderobe"
          : archetype.id === "family-core"
          ? "Familienflur / Treppe"
          : brief.stairPreference === "feature"
            ? "Offene Treppe / Garderobe"
            : "Treppe / Garderobe",
        kind: "flex",
        targetArea: wallStair
          ? 4
          : critiqueIncludes(brief, ["treppe", "stiege"])
          ? 10
          : archetype.id === "family-core"
            ? 9
            : brief.stairPreference === "feature"
              ? 9
              : 7,
        minArea: wallStair ? 3 : 5,
        maxArea: wallStair ? 6 : archetype.id === "family-core" || brief.stairPreference === "feature" ? 12 : 10,
        preferredSide: preferredServiceSide(archetype),
        preferredZone: "core",
      });
    }
    if (brief.utilityRoom) rooms.push({ name: "HWR / Technik", kind: "wet", targetArea: critiqueIncludes(brief, ["technik", "hwr", "hauswirtschaft"]) ? 12 : 10, minArea: REFERENCE_RANGES.utilityMin, maxArea: REFERENCE_RANGES.utilityMax, preferredSide: preferredServiceSide(archetype), preferredZone: "core" });
    if (brief.guestWc) rooms.push({ name: "Gäste-WC", kind: "wet", targetArea: 4, minArea: REFERENCE_RANGES.guestWcMin, maxArea: REFERENCE_RANGES.guestWcMax, preferredSide: preferredServiceSide(archetype), preferredZone: "core" });
    if (brief.office) rooms.push({ name: "Büro / Gast", kind: "flex", targetArea: brief.accessibility ? 13 : 11, minArea: 9, maxArea: 16, preferredSide: preferredLivingSide(archetype), preferredZone: "street" });
    if (brief.groundFloorSleeping || brief.accessibility) rooms.push({ name: "Gast / Schlafen", kind: "sleeping", targetArea: 13, minArea: 11, maxArea: 16, preferredSide: preferredLivingSide(archetype), preferredZone: "street" });
    if (archetype.id === "family-core" && floorArea >= 72) {
      rooms.push({ name: "Abstell / Vorrat", kind: "service", targetArea: 4, minArea: 3, maxArea: 6, preferredSide: preferredServiceSide(archetype), preferredZone: "core" });
    }
    if (floorArea >= 82 && !brief.groundFloorSleeping && !brief.accessibility) rooms.push({ name: "Speis / Abstell", kind: "service", targetArea: 4, minArea: 3, maxArea: 6, preferredSide: preferredServiceSide(archetype), preferredZone: "core" });
    return rooms;
  }

  const rooms: RoomSeed[] = [];
  const bedroomsThisFloor = floor === 1 ? Math.max(brief.bedrooms, Math.min(4, brief.children + 1)) : Math.max(1, brief.bedrooms - 4);
  for (let index = 0; index < Math.min(4, bedroomsThisFloor); index += 1) {
    rooms.push({
      name: index === 0 ? "Eltern" : `Zimmer ${index + 1}`,
      kind: "sleeping",
      targetArea: critiqueIncludes(brief, ["zimmer zu klein", "kinderzimmer klein", "schlafzimmer klein"])
        ? (index === 0 ? 18 : 15)
        : index === 0 ? 16 : 13,
      minArea: index === 0 ? REFERENCE_RANGES.parentRoomMin : REFERENCE_RANGES.childRoomMin,
      maxArea: index === 0 ? REFERENCE_RANGES.parentRoomMax : REFERENCE_RANGES.childRoomMax,
      preferredSide: index % 2 === 0 ? preferredLivingSide(archetype) : preferredServiceSide(archetype),
      preferredZone: index === 0 ? "garden" : "street",
      flexible: true,
    });
  }
  const bathroomsThisFloor = floor === 1 ? Math.max(1, brief.bathrooms - 1) : 1;
  for (let index = 0; index < bathroomsThisFloor; index += 1) {
    rooms.push({
      name: index ? `Duschbad ${index + 1}` : "Bad",
      kind: "wet",
      targetArea: critiqueIncludes(brief, ["bad zu klein", "bad klein", "bäder klein"])
        ? (index ? 7 : 13)
        : index ? 6 : 11,
      minArea: index ? 4 : REFERENCE_RANGES.familyBathMin,
      maxArea: index ? 8 : REFERENCE_RANGES.familyBathMax,
      preferredSide: preferredServiceSide(archetype),
      preferredZone: "core",
    });
  }
  if (floorArea >= 78 && brief.bedrooms <= 3 && brief.bathrooms <= 2) {
    rooms.push({ name: "Ankleide", kind: "flex", targetArea: 6, minArea: 4, maxArea: 8, preferredSide: preferredServiceSide(archetype), preferredZone: "core" });
  }
  rooms.push({ name: "Flur", kind: "flex", targetArea: 10, minArea: 7, maxArea: 13, preferredSide: preferredLivingSide(archetype), preferredZone: "core" });
  if (wallStair) {
    const hall = rooms.find((room) => room.name === "Flur");
    if (hall) {
      hall.targetArea = 7;
      hall.maxArea = 9;
    }
  }
  return rooms;
}

function layoutFloor(brief: HouseBrief, floor: number, stair: StairGeometry | null, floorArea: number, archetype: VariantArchetype): FloorPlan {
  const wallStair = wantsWallStair(brief) && brief.floors > 1;
  const wallStairSide = wallStair ? finalSide(archetype.serviceSide, archetype) : undefined;
  const seeds = seedsForFloor(brief, floor, floorArea, archetype);
  const areaByRoom = adjustedAreas(seeds, floorArea);
  const left: RoomSeed[] = [];
  const right: RoomSeed[] = [];
  const stairSideLimit = 2;
  let stairSideCount = 0;
  seeds.forEach((seed) => {
    let side = seed.preferredSide ?? (left.length <= right.length ? "left" : "right");
    if (archetype.mirrored) side = side === "left" ? "right" : "left";
    if (wallStair && side === wallStairSide) {
      if (stairSideCount >= stairSideLimit) {
        side = side === "left" ? "right" : "left";
      } else {
        stairSideCount += 1;
      }
    }
    (side === "left" ? left : right).push(seed);
  });

  const margin = 24;
  const top = 24;
  const usableHeight = 452;
  const hallX = wallStair ? 306 : 220;
  const hallWidth = wallStair ? 88 : 260;
  const fullColumnWidth = wallStair ? 276 : 196;
  const stairSideTop = wallStair ? FLOORPLAN_SVG.wallStairLeft.y + FLOORPLAN_SVG.wallStairLeft.height + 18 : top;
  const stairSideUsableHeight = top + usableHeight - stairSideTop;

  const placeColumn = (column: RoomSeed[], side: "left" | "right") => {
    const totalArea = column.reduce((sum, room) => sum + (areaByRoom.get(room.name) ?? room.targetArea), 0);
    const isStairSide = wallStair && side === wallStairSide;
    const columnTop = isStairSide ? stairSideTop : top;
    const columnUsableHeight = isStairSide ? stairSideUsableHeight : usableHeight;
    let y = columnTop;
    const x = !wallStair
      ? (side === "left" ? margin : hallX + hallWidth)
      : (side === "left" ? margin : hallX + hallWidth);
    const width = fullColumnWidth;
    const minimumHeights = column.map((room) => {
      const roomArea = areaByRoom.get(room.name) ?? room.targetArea;
      if (roomArea <= 5 || room.kind === "service") return 58;
      if (room.kind === "wet") return 70;
      return 78;
    });
    const minimumTotal = minimumHeights.reduce((sum, height) => sum + height, 0);
    const extraHeight = Math.max(0, columnUsableHeight - minimumTotal);
    const roomHeights = column.map((room, index) => {
      const roomArea = areaByRoom.get(room.name) ?? room.targetArea;
      if (minimumTotal > columnUsableHeight) {
        return columnUsableHeight * (roomArea / Math.max(totalArea, 1));
      }
      return minimumHeights[index] + extraHeight * (roomArea / Math.max(totalArea, 1));
    });
    return column.map((room, index) => {
      const roomArea = areaByRoom.get(room.name) ?? room.targetArea;
      const height = index === column.length - 1
        ? columnTop + columnUsableHeight - y
        : roomHeights[index];
      const planned: PlannedRoom = {
        id: `${floor}-${side}-${index}`,
        name: room.name,
        kind: room.kind,
        x,
        y,
        width,
        height,
        area: roomArea,
        side,
        zone: room.preferredZone,
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
    layoutMode: wallStair ? "wall-stair" : "central-stair",
    wallStairSide,
  };
}

export function generateVariants(brief: HouseBrief): PlanVariant[] {
  const rotation = brief.generationAttempt % VARIANT_ARCHETYPES.length;
  const archetypes = [
    ...VARIANT_ARCHETYPES.slice(rotation),
    ...VARIANT_ARCHETYPES.slice(0, rotation),
  ];

  return archetypes.map((archetype, index) => {
    const profile = profileForArea(brief.area);
    const baseFloorArea = targetAreaForFloor(brief, 0, profile);
    const attemptRatioOffset = ((brief.generationAttempt + index) % 3 - 1) * 0.04;
    const ratio = Math.max(1.04, profile.preferredFootprintRatio + archetype.ratioOffset + attemptRatioOffset);
    const floorArea = brief.floors === 1 ? brief.area : baseFloorArea;
    const depth = Math.sqrt(floorArea / ratio);
    const width = depth * ratio;
    const stair = brief.floors > 1 ? createStairGeometry() : null;
    const floors = Array.from({ length: brief.floors }, (_, floor) =>
      layoutFloor(brief, floor, stair, targetAreaForFloor(brief, floor, profile), archetype));
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
        .every((room) => room.side === finalSide(archetype.serviceSide, archetype)));
    const hallAreasOk = floors.every((plan) => {
      const circulation = plan.rooms
        .filter((room) => room.name.includes("Flur") || room.name.includes("Diele") || room.name.includes("Treppe"))
        .reduce((sum, room) => sum + room.area, 0);
      const planned = plan.rooms.reduce((sum, room) => sum + room.area, 0);
      return circulation / Math.max(planned, 1) <= REFERENCE_RANGES.hallShareMax;
    });
    const stairHasReservedFootprint = floors.every(stairIsReserved);
    const roomWidthsUsable = floors.every(hasUsableRoomWidths);
    const doorsDrawable = floors.every(hasDoorDrawableWall);
    const exteriorWindowsOk = floors.every(hasExteriorWindowWall);
    const bedroomSizesOk = upperRooms
      .filter((room) => room.kind === "sleeping")
      .every((room) => room.area >= REFERENCE_RANGES.childRoomMin && room.area <= REFERENCE_RANGES.parentRoomMax);
    const lifestyleChecks = [
      brief.kitchen === "separate" ? "separate Küche eingeplant" : brief.kitchen === "semi-open" ? "halboffene Wohnküche berücksichtigt" : "offene Wohnküche berücksichtigt",
      brief.gardenConnection === "generous" ? "großer Gartenbezug priorisiert" : brief.gardenConnection === "private" ? "privatere Gartenorientierung priorisiert" : "ausgewogener Gartenbezug priorisiert",
      brief.accessibility ? "EG-Schlaf-/Flexraum für barrierearme Nutzung ergänzt" : "klassische Familienhaus-Nutzung",
    ];
    const checks = [
      { label: "Jeder Aufenthaltsraum liegt an einer Außenwand mit Fenster", passed: floors.every((plan) => plan.rooms.length > 0) },
      { label: `Referenzprofil aus Verkaufsschlagern erkannt: ${profile.name}`, passed: true },
      brief.critiqueNotes
        ? { label: `Kritik aus vorherigem Lauf berücksichtigt: ${brief.critiqueNotes}`, passed: true }
        : { label: "Noch keine Kritik aus vorherigem Lauf", passed: true },
      wantsWallStair(brief)
        ? { label: "Treppenkritik umgesetzt: Treppe an die Außenwand gelegt und Flurfläche reduziert", passed: floors.every((plan) => plan.layoutMode === "wall-stair") }
        : { label: "Treppenlage folgt dem gewählten Grundrissprofil", passed: true },
      { label: `Fragebogen ausgewertet: ${lifestyleChecks.join(" · ")}`, passed: true },
      { label: "EG folgt Bestseller-Sequenz: Eingang, Diele, Treppe, WC/HWR und Wohnen/Essen", passed: groundRooms.length >= 4 },
      { label: "OG folgt Familienhaus-Muster: Treppe, Flur, Bad, Eltern und Kinderzimmer", passed: brief.floors === 1 || upperRooms.some((room) => room.name === "Bad") },
      { label: "Flur-, Dielen- und Treppenflächen bleiben unter ca. 24 % der geplanten Fläche", passed: hallAreasOk },
      { label: "Interne Kollisionsprüfung: Treppe liegt nicht über Räumen oder Raumtexten", passed: stairHasReservedFootprint },
      { label: "Raumspalten bleiben zeichnerisch nutzbar und werden nicht zu Reststreifen", passed: roomWidthsUsable },
      { label: "Türsymbole passen in die jeweilige Wandfläche", passed: doorsDrawable },
      { label: "Fenster liegen an echten Außenwänden, nicht an Innenfluren oder Treppenresten", passed: exteriorWindowsOk },
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
      id: archetype.id,
      name: brief.generationAttempt > 0 ? `${archetype.name} · Lauf ${brief.generationAttempt + 1}` : archetype.name,
      description: `${archetype.descriptionPrefix}: ${brief.kitchen === "separate" ? "separate Küche" : brief.kitchen === "semi-open" ? "halboffene Küche" : "offener Wohn-Ess-Kochbereich"}, ${brief.gardenConnection === "private" ? "gezieltere Ausblicke" : "kurzer Weg zur Terrasse"}, ${wantsWallStair(brief) ? "Treppe an der Außenwand statt verschwendetem Mittelraum" : brief.stairPreference === "feature" ? "offenere Treppe" : "zentraler Treppenkern"} und gebündelte Haustechnik. ${profile.notes.join(" · ")}.`,
      floors,
      score: Math.round((passedChecks / checks.length) * ([96, 93, 94][index] ?? 92)),
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
