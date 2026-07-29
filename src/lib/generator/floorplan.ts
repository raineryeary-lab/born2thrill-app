import {
  referenceAreaFromSimplifier,
  selectReferenceLayout,
  type ReferenceFloor,
  type ReferenceLayoutMatch,
  simplifierReferenceLabel,
} from "../training/simplifier-reference";
import { solveStairGeometry } from "./storey-model.mjs";

export type HouseBrief = {
  projectName: string;
  area: number;
  floors: number;
  storeyType: "1_storey" | "1_5_storey" | "2_storey";
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
  kind: "living" | "sleeping" | "wet" | "service" | "flex" | "circulation";
  x: number;
  y: number;
  width: number;
  height: number;
  area: number;
  side: "left" | "right";
  zone: "garden" | "street" | "core";
  polygon?: Array<{ x: number; y: number }>;
};

export type FloorPlan = {
  floor: number;
  name: string;
  rooms: PlannedRoom[];
  hasStair: boolean;
  stair: StairGeometry | null;
  layoutMode: "central-stair" | "wall-stair";
  wallStairSide?: "left" | "right";
  stairRect?: { x: number; y: number; width: number; height: number };
  stairPath?: Array<{ x: number; y: number }>;
  stairWidthPx?: number;
  stairType?: "straight" | "quarter_turn" | "half_or_multi_turn";
  referenceFootprint?: { x: number; y: number; width: number; height: number };
  referenceLayoutId?: string;
  referenceElements?: Array<{ id: string; type: string; points: Array<{ x: number; y: number }> }>;
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
  riseMm: number;
  goingMm: number;
  stepMeasureMm: number;
  minimumHeadroomMm: number;
};

export type PlanVariant = {
  id: string;
  name: string;
  description: string;
  floors: FloorPlan[];
  storeyType: HouseBrief["storeyType"];
  stairCore: {
    id: string;
    footprint: { x: number; y: number; width: number; height: number };
    path: Array<{ x: number; y: number }>;
    geometry: StairGeometry;
  } | null;
  score: number;
  checks: Array<{ label: string; passed: boolean }>;
  metrics: {
    footprintWidthM: number;
    footprintDepthM: number;
    plannedAreaM2: number;
    referenceProfile: string;
    groundFloorAreaM2: number;
    upperFloorAreaM2: number;
    referenceLayoutId: string;
    storeyType: HouseBrief["storeyType"];
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
  minUsableFlightWidthM: 0.9,
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
  const solved = solveStairGeometry(2800, {
    type: "half_turn",
    clearWidthMm: 900,
  });
  if (!solved.ok) {
    throw new Error(`No compliant stair geometry: ${solved.reason}`);
  }
  const compliant = solved as {
    floorToFloorMm: number;
    riserCount: number;
    riseMm: number;
    goingMm: number;
    stepMeasureMm: number;
    clearWidthMm: number;
    landingDepthMm: number;
    minimumHeadroomMm: number;
    footprint: { widthMm: number; lengthMm: number };
  };

  return {
    type: "two-flight-u",
    floorToFloorHeightM: compliant.floorToFloorMm / 1000,
    risers: compliant.riserCount,
    riserHeightCm: compliant.riseMm / 10,
    treadDepthCm: compliant.goingMm / 10,
    usableFlightWidthM: compliant.clearWidthMm / 1000,
    landingDepthM: compliant.landingDepthMm / 1000,
    footprintWidthM: compliant.footprint.widthMm / 1000,
    footprintLengthM: compliant.footprint.lengthMm / 1000,
    clearArrivalDepthM: 1,
    riseMm: compliant.riseMm,
    goingMm: compliant.goingMm,
    stepMeasureMm: compliant.stepMeasureMm,
    minimumHeadroomMm: compliant.minimumHeadroomMm,
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
  if (plan.stairRect) return plan.stairRect;
  if (plan.referenceLayoutId) return null;
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
  return plan.rooms.filter((room) => room.kind !== "circulation").every((room) => !rectsOverlap(room, stairRect));
}

function rectGap(a: SvgRect, b: SvgRect) {
  const horizontal = Math.max(0, Math.max(a.x, b.x) - Math.min(a.x + a.width, b.x + b.width));
  const vertical = Math.max(0, Math.max(a.y, b.y) - Math.min(a.y + a.height, b.y + b.height));
  return Math.hypot(horizontal, vertical);
}

function stairConnectsToHall(plan: FloorPlan) {
  const stairRect = stairRectForPlan(plan);
  if (!stairRect) return !plan.hasStair;
  const circulation = plan.rooms.filter((room) => room.kind === "circulation" || /flur|diele|eingang/i.test(room.name));
  return circulation.some((room) => rectGap(room, stairRect) <= 36);
}

function hasUsableRoomWidths(plan: FloorPlan) {
  return plan.rooms.every((room) => room.width >= 38 && room.height >= 38);
}

function hasDoorDrawableWall(plan: FloorPlan) {
  return Boolean(plan.referenceElements?.some((element) => element.type === "door"));
}

function hasExteriorWindowWall(plan: FloorPlan) {
  return Boolean(plan.referenceElements?.some((element) => element.type === "window"));
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
  const floors = Math.min(3, number("floors", 2));
  const roof = get("roofPreference", "gable");
  const rawStoreyType = get("storeyType");
  const explicitStoreyType = (
    ["1_storey", "1_5_storey", "2_storey"] as const
  ).find((value) => value === rawStoreyType);
  const storeyType: HouseBrief["storeyType"] = explicitStoreyType ?? (
    floors === 1
      ? "1_storey"
      : roof.toLowerCase().includes("sattel") || roof.toLowerCase().includes("gable")
        ? "1_5_storey"
        : "2_storey"
  );

  return {
    projectName: get("projectName", "Testhaus"),
    area: number("targetArea", 145),
    floors,
    storeyType,
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
    roof,
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

function wantsEntranceCirculation(brief: HouseBrief) {
  const text = brief.critiqueNotes.toLowerCase();
  return (text.includes("diele") || text.includes("eingang"))
    && (
      text.includes("kein eigenes zimmer")
      || text.includes("kein raum")
      || text.includes("eingangsbereich")
      || text.includes("zirkulation")
      || text.includes("circulation")
    );
}

function wantsWallStair(brief: HouseBrief) {
  const text = brief.critiqueNotes.toLowerCase();
  const explicitlyRequestsCentral = text.includes("treppe")
    && ["mittig", "zentral", "mittelzone"].some((word) => text.includes(word));
  if (explicitlyRequestsCentral || brief.stairPreference === "central") return false;
  if (brief.floors > 1) return true;

  return text.includes("treppe") && [
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

function referenceHouseTypeForBrief(brief: HouseBrief) {
  if (brief.storeyType === "1_storey") return "bungalow";
  if (brief.storeyType === "1_5_storey") return "onehalfstorey";
  return "twostorey";
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
  const entranceCirculation = wantsEntranceCirculation(brief);
  if (floor === 0) {
    const fallbackLivingTarget = clamp(
      Math.round(floorArea * (wallStair ? 0.57 : 0.52)) + kitchenAreaAdjustment(brief) + gardenAreaAdjustment(brief),
      REFERENCE_RANGES.livingKitchenMin,
      REFERENCE_RANGES.livingKitchenMax,
    );
    const livingTarget = clamp(
      referenceAreaFromSimplifier(
        "groundfloor",
        brief.kitchen === "separate" ? ["wohnen", "wohnen_essen"] : ["wohnen_essen_kochen", "wohnen_essen"],
        floorArea,
        fallbackLivingTarget,
        brief.kitchen === "separate" ? 28 : REFERENCE_RANGES.livingKitchenMin,
        brief.kitchen === "separate" ? 45 : REFERENCE_RANGES.livingKitchenMax,
      ) + kitchenAreaAdjustment(brief) + gardenAreaAdjustment(brief),
      brief.kitchen === "separate" ? 28 : REFERENCE_RANGES.livingKitchenMin,
      brief.kitchen === "separate" ? 45 : REFERENCE_RANGES.livingKitchenMax,
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
        name: entranceCirculation ? "Eingangsbereich" : wallStair ? "Kompakte Diele" : "Diele",
        kind: "circulation",
        targetArea: entranceCirculation || wallStair || critiqueIncludes(brief, ["flur zu groß", "flur zu gross", "diele zu groß", "zu viel flur"]) ? 5 : 8,
        minArea: entranceCirculation ? 4 : 5,
        maxArea: entranceCirculation || wallStair ? 8 : 12,
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
        name: "Garderobe",
        kind: entranceCirculation && !wallStair ? "circulation" : "flex",
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
    if (brief.utilityRoom) rooms.push({
      name: "HWR / Technik",
      kind: "wet",
      targetArea: referenceAreaFromSimplifier("groundfloor", ["hwr_htr"], floorArea, critiqueIncludes(brief, ["technik", "hwr", "hauswirtschaft"]) ? 12 : 10, REFERENCE_RANGES.utilityMin, REFERENCE_RANGES.utilityMax),
      minArea: REFERENCE_RANGES.utilityMin,
      maxArea: REFERENCE_RANGES.utilityMax,
      preferredSide: preferredServiceSide(archetype),
      preferredZone: "core",
    });
    if (brief.guestWc) rooms.push({
      name: "Gäste-WC",
      kind: "wet",
      targetArea: referenceAreaFromSimplifier("groundfloor", ["wc", "du_wc"], floorArea, 4, REFERENCE_RANGES.guestWcMin, REFERENCE_RANGES.guestWcMax),
      minArea: REFERENCE_RANGES.guestWcMin,
      maxArea: REFERENCE_RANGES.guestWcMax,
      preferredSide: preferredServiceSide(archetype),
      preferredZone: "core",
    });
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
    const fallbackBedroomArea = critiqueIncludes(brief, ["zimmer zu klein", "kinderzimmer klein", "schlafzimmer klein"])
      ? (index === 0 ? 18 : 15)
      : index === 0 ? 16 : 13;
    rooms.push({
      name: index === 0 ? "Eltern" : `Zimmer ${index + 1}`,
      kind: "sleeping",
      targetArea: referenceAreaFromSimplifier(
        "upperfloor",
        index === 0 ? ["eltern"] : ["kind"],
        floorArea,
        fallbackBedroomArea,
        index === 0 ? REFERENCE_RANGES.parentRoomMin : REFERENCE_RANGES.childRoomMin,
        index === 0 ? REFERENCE_RANGES.parentRoomMax : REFERENCE_RANGES.childRoomMax,
      ),
      minArea: index === 0 ? REFERENCE_RANGES.parentRoomMin : REFERENCE_RANGES.childRoomMin,
      maxArea: index === 0 ? REFERENCE_RANGES.parentRoomMax : REFERENCE_RANGES.childRoomMax,
      preferredSide: index % 2 === 0 ? preferredLivingSide(archetype) : preferredServiceSide(archetype),
      preferredZone: index === 0 ? "garden" : "street",
      flexible: true,
    });
  }
  const bathroomsThisFloor = floor === 1 ? Math.max(1, brief.bathrooms - 1) : 1;
  for (let index = 0; index < bathroomsThisFloor; index += 1) {
    const fallbackBathArea = critiqueIncludes(brief, ["bad zu klein", "bad klein", "bäder klein"])
      ? (index ? 7 : 13)
      : index ? 6 : 11;
    rooms.push({
      name: index ? `Duschbad ${index + 1}` : "Bad",
      kind: "wet",
      targetArea: referenceAreaFromSimplifier(
        "upperfloor",
        index ? ["du_wc", "wc"] : ["bad"],
        floorArea,
        fallbackBathArea,
        index ? 4 : REFERENCE_RANGES.familyBathMin,
        index ? 8 : REFERENCE_RANGES.familyBathMax,
      ),
      minArea: index ? 4 : REFERENCE_RANGES.familyBathMin,
      maxArea: index ? 8 : REFERENCE_RANGES.familyBathMax,
      preferredSide: preferredServiceSide(archetype),
      preferredZone: "core",
    });
  }
  if (floorArea >= 78 && brief.bedrooms <= 3 && brief.bathrooms <= 2) {
    rooms.push({ name: "Ankleide", kind: "flex", targetArea: 6, minArea: 4, maxArea: 8, preferredSide: preferredServiceSide(archetype), preferredZone: "core" });
  }
  rooms.push({
    name: "Flur",
    kind: "flex",
    targetArea: referenceAreaFromSimplifier("upperfloor", ["flur"], floorArea, 10, 7, 13),
    minArea: 7,
    maxArea: 13,
    preferredSide: preferredLivingSide(archetype),
    preferredZone: "core",
  });
  if (wantsEntranceCirculation(brief)) {
    const hall = rooms.find((room) => room.name === "Flur");
    if (hall) {
      hall.kind = "circulation";
      hall.targetArea = 8;
      hall.maxArea = 10;
    }
  }
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

function roomKind(roomIds: string[]): PlannedRoom["kind"] {
  const ids = new Set(roomIds);
  if (["flur", "diele", "eingang", "treppenoeffnung"].some((id) => ids.has(id))) return "circulation";
  if (["bad", "wc", "du_wc", "elternbad", "kinderbad"].some((id) => ids.has(id))) return "wet";
  if (["hwr_htr", "technik", "abstell", "speisekammer", "keller"].some((id) => ids.has(id))) return "service";
  if (["wohnen", "essen", "kueche", "wohnen_essen", "wohnen_essen_kochen"].some((id) => ids.has(id))) return "living";
  if (["eltern", "kind", "zimmer", "gast"].some((id) => ids.has(id))) return "sleeping";
  return "flex";
}

function referenceFloorFor(reference: ReferenceLayoutMatch, floor: number): ReferenceFloor | undefined {
  const level = floor === 0 ? "groundfloor" : floor === 1 ? "upperfloor" : "attic";
  return reference.floors.find((candidate) => candidate.floorLevel === level);
}

function layoutFloorFromReference(
  brief: HouseBrief, floor: number, stair: StairGeometry | null, floorArea: number,
  archetype: VariantArchetype, reference: ReferenceLayoutMatch, footprintWidthM: number,
): FloorPlan | null {
  const source = referenceFloorFor(reference, floor);
  if (!source?.rooms.length) return null;
  const sourcePoints = [...source.rooms.flatMap((room) => room.polygon), ...source.elements.flatMap((element) => element.points)];
  if (!sourcePoints.length) return null;
  const anchorFloor = referenceFloorFor(reference, 0) ?? source;
  const anchorPoints = [...anchorFloor.rooms.flatMap((room) => room.polygon), ...anchorFloor.elements.flatMap((element) => element.points)];
  const anchorXs = anchorPoints.map(([x]) => x); const anchorYs = anchorPoints.map(([, y]) => y);
  const anchorMinX = Math.min(...anchorXs); const anchorMaxX = Math.max(...anchorXs);
  const anchorMinY = Math.min(...anchorYs); const anchorMaxY = Math.max(...anchorYs);
  const anchorWidth = Math.max(0.01, anchorMaxX - anchorMinX); const anchorHeight = Math.max(0.01, anchorMaxY - anchorMinY);
  const anchorScale = Math.min(620 / anchorWidth, 420 / anchorHeight);
  const footprintWidth = anchorWidth * anchorScale; const footprintHeight = anchorHeight * anchorScale;
  const offsetX = 40 + (620 - footprintWidth) / 2; const offsetY = 40 + (420 - footprintHeight) / 2;
  const sourceXs = sourcePoints.map(([x]) => x); const sourceYs = sourcePoints.map(([, y]) => y);
  const sourceMinX = Math.min(...sourceXs); const sourceMaxX = Math.max(...sourceXs);
  const sourceMinY = Math.min(...sourceYs); const sourceMaxY = Math.max(...sourceYs);
  const sourceWidth = Math.max(0.01, sourceMaxX - sourceMinX); const sourceHeight = Math.max(0.01, sourceMaxY - sourceMinY);
  const transform = ([x, y]: [number, number]) => ({
    x: archetype.mirrored ? 700 - (offsetX + ((x - sourceMinX) / sourceWidth) * footprintWidth) : offsetX + ((x - sourceMinX) / sourceWidth) * footprintWidth,
    y: offsetY + ((y - sourceMinY) / sourceHeight) * footprintHeight,
  });
  const anchorTransform = ([x, y]: [number, number]) => ({
    x: archetype.mirrored ? 700 - (offsetX + (x - anchorMinX) * anchorScale) : offsetX + (x - anchorMinX) * anchorScale,
    y: offsetY + (y - anchorMinY) * anchorScale,
  });  const roomSources = source.rooms.filter((room) => {
    const ids = new Set(room.roomIds);
    return !ids.has("treppe") && !ids.has("stairs") && !/treppe|stair/i.test(room.label);
  });
  const totalRatio = roomSources.reduce((sum, room) => sum + room.areaRatio, 0);
  const rooms: PlannedRoom[] = roomSources.map((room, index) => {
    const polygon = room.polygon.map(transform);
    const px = polygon.map((point) => point.x); const py = polygon.map((point) => point.y);
    const x = Math.min(...px); const y = Math.min(...py); const width = Math.max(...px) - x; const height = Math.max(...py) - y;
    const centerX = x + width / 2; const centerY = y + height / 2; const kind = roomKind(room.roomIds);
    const proportionalArea = Math.max(1, Math.round((room.areaRatio / Math.max(totalRatio, 0.001)) * floorArea));
    const isHtr = room.roomIds.some((id) => id === "hwr_htr" || id === "technik") || /\bHTR\b|\bHWR\b/i.test(room.label);
    const isWc = room.roomIds.some((id) => id === "wc" || id === "du_wc") || /\bWC\b/i.test(room.label);
    const area = isHtr ? 10 : isWc ? Math.max(2, proportionalArea) : proportionalArea;
    return {
      id: "ref-" + floor + "-" + (room.id || index), name: room.label, kind, x, y, width, height,
      area,
      side: centerX < 350 ? "left" : "right",
      zone: kind === "circulation" || kind === "wet" || kind === "service" ? "core" : centerY < 250 ? "street" : "garden",
      polygon,
    };
  });
  const referenceElements = source.elements.map((element) => ({ id: element.id, type: element.type, points: element.points.map(transform) }));
  const stairSource = anchorFloor.elements.find((element) => element.type === "stairs");
  const stairPath = stairSource?.points.map(anchorTransform) ?? [];
  const stairWidthPx = stairPath.length
    ? Math.max(28, Math.min(64, (0.9 * footprintWidth) / Math.max(footprintWidthM, 0.1)))
    : undefined;
  let stairRect: SvgRect | undefined;
  if (stairPath.length && stairWidthPx) {
    const sx = stairPath.map((point) => point.x); const sy = stairPath.map((point) => point.y);
    const halfWidth = stairWidthPx / 2;
    const minX = Math.min(...sx) - halfWidth; const maxX = Math.max(...sx) + halfWidth;
    const minY = Math.min(...sy) - halfWidth; const maxY = Math.max(...sy) + halfWidth;
    stairRect = { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
  }
  const stairType = stairPath.length === 2 ? "straight" : stairPath.length === 3 ? "quarter_turn" : stairPath.length >= 4 ? "half_or_multi_turn" : undefined;
  const wallStairSide = stairRect ? stairRect.x + stairRect.width / 2 < 350 ? "left" : "right" : undefined;  const wallStair = Boolean(stairRect && (stairRect.x < 170 || stairRect.x + stairRect.width > 530));
  return {
    floor, name: floor === 0 ? "Erdgeschoss" : floor === 1 ? "Obergeschoss" : (floor + 1) + ". Geschoss",
    rooms, hasStair: brief.floors > 1, stair: brief.floors > 1 ? stair : null,
    layoutMode: wallStair ? "wall-stair" : "central-stair", wallStairSide, stairRect, stairPath, stairWidthPx, stairType,
    referenceFootprint: { x: offsetX, y: offsetY, width: footprintWidth, height: footprintHeight },
    referenceLayoutId: reference.projectId, referenceElements,
  };
}

function sameRect(
  left: { x: number; y: number; width: number; height: number } | null,
  right: { x: number; y: number; width: number; height: number } | null,
) {
  if (!left || !right) return left === right;
  return left.x === right.x
    && left.y === right.y
    && left.width === right.width
    && left.height === right.height;
}

function samePath(
  left: Array<{ x: number; y: number }>,
  right: Array<{ x: number; y: number }>,
) {
  return left.length === right.length && left.every((point, index) =>
    point.x === right[index].x && point.y === right[index].y
  );
}

function sharedStairCoreForFloors(
  floors: FloorPlan[],
  stair: StairGeometry | null,
): PlanVariant["stairCore"] {
  if (!stair || floors.length < 2) return null;
  const footprint = stairRectForPlan(floors[0]);
  if (!footprint) return null;
  return {
    id: "shared-stair-core",
    footprint,
    path: floors[0].stairPath ?? [],
    geometry: stair,
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
    const referenceHouseType = referenceHouseTypeForBrief(brief);
    const referenceLayout = selectReferenceLayout({
      houseType: referenceHouseType, floors: brief.floors, bedrooms: brief.bedrooms, bathrooms: brief.bathrooms,
      office: brief.office, guestWc: brief.guestWc, utilityRoom: brief.utilityRoom,
      basement: brief.basement !== "none", stairPreference: brief.stairPreference,
      variantOffset: brief.generationAttempt + index,
    });
    const baseFloorArea = targetAreaForFloor(brief, 0, profile);
    const attemptRatioOffset = ((brief.generationAttempt + index) % 3 - 1) * 0.04;
    const ratio = Math.max(1.04, profile.preferredFootprintRatio + archetype.ratioOffset + attemptRatioOffset);
    const floorArea = brief.floors === 1 ? brief.area : baseFloorArea;
    const depth = Math.sqrt(floorArea / ratio);
    const width = depth * ratio;
    const stair = brief.floors > 1 ? createStairGeometry() : null;
    const floors = Array.from({ length: brief.floors }, (_, floor) => {
      const floorAreaTarget = targetAreaForFloor(brief, floor, profile);
      return referenceLayout
        ? layoutFloorFromReference(brief, floor, stair, floorAreaTarget, archetype, referenceLayout, width)
          ?? layoutFloor(brief, floor, stair, floorAreaTarget, archetype)
        : layoutFloor(brief, floor, stair, floorAreaTarget, archetype);
    });
    const stairCore = sharedStairCoreForFloors(floors, stair);
    const stairCoreAligned = !stair || (stairCore !== null && floors.every((plan) => {
      const footprint = stairRectForPlan(plan);
      const path = plan.stairPath ?? [];
      return sameRect(footprint, stairCore.footprint)
        && (
          stairCore.path.length === 0 ||
          samePath(path, stairCore.path)
        );
    }));
    const sourceStairCoreConfirmed = brief.floors === 1
      || (Boolean(referenceLayout) && referenceLayout?.sourceStairCoreAligned === true);
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
    const livingKitchen = groundRooms.find((room) => /wohn|essen|koch|küche/i.test(room.name));
    const bedroomSizesOk = upperRooms
      .filter((room) => room.kind === "sleeping")
      .every((room) => room.area >= REFERENCE_RANGES.childRoomMin && room.area <= REFERENCE_RANGES.parentRoomMax);
    const hallAreasOk = floors.every((plan) => {
      const circulation = plan.rooms
        .filter((room) => room.kind === "circulation")
        .reduce((sum, room) => sum + room.area, 0);
      const planned = plan.rooms.reduce((sum, room) => sum + room.area, 0);
      return circulation / Math.max(planned, 1) <= REFERENCE_RANGES.hallShareMax;
    });
    const stairHasReservedFootprint = floors.every(stairIsReserved);
    const stairHallConnected = floors.every(stairConnectsToHall);
    const roomWidthsUsable = floors.every(hasUsableRoomWidths);
    const doorsDrawable = floors.every(hasDoorDrawableWall);
    const exteriorWindowsOk = floors.every(hasExteriorWindowWall);
    const allFloorsUseReference = Boolean(referenceLayout)
      && floors.every((plan) => plan.referenceLayoutId === referenceLayout?.projectId);
    const stairRoomsAbsent = floors.every((plan) =>
      plan.rooms.every((room) => !/treppe|stairs/i.test(room.name)),
    );    const stairGeometryPresent = brief.floors === 1
      || floors.every((plan) => Boolean(plan.stairRect));
    const checks = [
      { label: "Reale, annotierte Raum-Polygone werden auf allen Etagen verwendet", passed: allFloorsUseReference },
      { label: referenceLayout
        ? `Reales Simplifier-Referenzlayout ausgewählt: ${referenceLayout.projectId} (${referenceLayout.houseType}, Trefferwert ${referenceLayout.score})`
        : "Kein passendes reales Simplifier-Referenzlayout gefunden", passed: Boolean(referenceLayout) },
      { label: `Lokale Simplifier-Referenz geladen: ${simplifierReferenceLabel()}`, passed: Boolean(referenceLayout) },
      { label: "Treppe bleibt feste Geometrie; kein erfundener Treppen-Raum", passed: stairRoomsAbsent },
      { label: "Gemeinsamer Treppenkern ist auf allen Etagen punktgleich", passed: stairCoreAligned },
      {
        label: referenceLayout?.sourceStairReviewRequired
          ? `Quellreferenz ${referenceLayout.projectId}: EG-/OG-Treppenkern muss vor Kundennutzung gemeinsam bestätigt werden`
          : "Quellreferenz besitzt einen bestätigten gemeinsamen Treppenkern",
        passed: sourceStairCoreConfirmed,
      },
      { label: "Annotierte Treppengeometrie ist für mehrgeschossige Häuser vorhanden", passed: stairGeometryPresent },
      { label: "Flur- und Dielenflächen bleiben unter ca. 24 % der geplanten Fläche", passed: hallAreasOk },
      { label: "Interne Kollisionsprüfung: Treppe liegt nicht über Räumen oder Raumtexten", passed: stairHasReservedFootprint },
      { label: "Treppe hat direkte nutzbare Verbindung zum Flur / zur Ankunftszone", passed: stairHallConnected },
      { label: "Raumgeometrien bleiben zeichnerisch nutzbar und werden nicht zu Reststreifen", passed: roomWidthsUsable },
      { label: "Annotierte Türen aus der Referenz werden übernommen", passed: doorsDrawable },
      { label: "Annotierte Fenster aus der Referenz werden übernommen", passed: exteriorWindowsOk },
      {
        label: stair
          ? `Treppenlauf bemessen: ${stair.risers} Steigungen à ${stair.riserHeightCm} cm, ${stair.treadDepthCm} cm Auftritt, ${stair.usableFlightWidthM.toFixed(2)} m Laufbreite und freie Ankunft`
          : "Keine Geschosstreppe erforderlich",
        passed: stairDimensioned,
      },
      {
        label: `Wohn-/Ess-/Kochbereich liegt im Referenzkorridor ${REFERENCE_RANGES.livingKitchenMin}-${REFERENCE_RANGES.livingKitchenMax} m²`,
        passed: !livingKitchen || (livingKitchen.area >= REFERENCE_RANGES.livingKitchenMin && livingKitchen.area <= REFERENCE_RANGES.livingKitchenMax),
      },
      { label: "Schlaf- und Kinderzimmer liegen in marktüblichen Größenkorridoren", passed: brief.floors === 1 || bedroomSizesOk },
    ];    const passedChecks = checks.filter((check) => check.passed).length;
    return {
      id: archetype.id,
      name: brief.generationAttempt > 0 ? `${archetype.name} · Lauf ${brief.generationAttempt + 1}` : archetype.name,
      description: `Geometrie, Türen, Fenster und Treppe stammen aus der real annotierten Referenz ${referenceLayout?.projectId ?? "ohne Treffer"}. Die Proportionen bleiben erhalten und werden auf die gewünschte Wohnfläche skaliert; es werden keine künstlichen Flure oder Öffnungen ergänzt.`,
      floors,
      storeyType: brief.storeyType,
      stairCore,
      score: Math.round((passedChecks / checks.length) * 100),
      checks,
      metrics: {
        footprintWidthM: Number(width.toFixed(1)),
        footprintDepthM: Number(depth.toFixed(1)),
        plannedAreaM2: brief.area,
        referenceProfile: `${profile.name} / ${simplifierReferenceLabel()} / ${referenceLayout?.projectId ?? "kein Layouttreffer"}`,
        referenceLayoutId: referenceLayout?.projectId ?? "",
        groundFloorAreaM2: targetAreaForFloor(brief, 0, profile),
        upperFloorAreaM2: brief.floors > 1 ? targetAreaForFloor(brief, 1, profile) : 0,
        storeyType: brief.storeyType,
      },
    };
  });
}
