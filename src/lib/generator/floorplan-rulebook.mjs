export const FLOORPLAN_RULEBOOK_VERSION = "dmh-floorplan-rulebook-v3-2026-07-31";

export const FLOORPLAN_RULES = Object.freeze({
  geometry: Object.freeze({
    coordinateUnit: "mm",
    editSnapMm: 50,
    alignmentToleranceMm: 5,
    coverageToleranceMm2: 10_000,
    sourceAxisSnapTolerancePx: 10,
    footprintBoundarySnapMm: 150,
  }),
  walls: Object.freeze({
    exteriorThicknessMm: 350,
    interiorThicknessMm: 100,
    rectilinearOnly: true,
    openingsMustBeWallLinked: true,
  }),
  doors: Object.freeze({
    internalWidthMm: 880,
    smallWcWidthMm: 760,
    entranceWidthMm: 1100,
    terraceWidthMm: 1800,
    terraceMinimumHeightMm: 2100,
    renderClosed: true,
    colours: Object.freeze({
      mainEntrance: "#047857",
      terraceDoor: "#0891b2",
      internal: "#2563eb",
      smallWc: "#d97706",
      openPassage: "#0f766e",
    }),
  }),
  windows: Object.freeze({
    minimumGlazingToRoomAreaRatio: 0.1,
    defaultHeightMm: 1350,
    defaultSillHeightMm: 900,
    habitableRoomKinds: Object.freeze(["living", "sleeping", "flex"]),
    wetAndServiceRoomsMayBeInternal: true,
  }),
  rooms: Object.freeze({
    hwrHtr: Object.freeze({ match: "hwr_htr", minimumM2: 8, maximumM2: 18 }),
    wc: Object.freeze({ match: "wc", minimumM2: 2 }),
    showerBathroom: Object.freeze({ match: "shower_bathroom", preferredMinimumM2: 3, preferredMaximumM2: 4 }),
    pantry: Object.freeze({ match: "pantry", preferredM2: 2.5 }),
    child: Object.freeze({ match: "child", minimumM2: 10 }),
    parents: Object.freeze({ match: "parents", minimumM2: 12 }),
    dressing: Object.freeze({ match: "dressing", minimumM2: 8 }),
  }),
  circulation: Object.freeze({
    entranceMustReachCirculation: true,
    everyRequiredRoomReachable: true,
    noUncoveredResidualGaps: true,
    stairMustConnectToCirculation: true,
  }),
  stairs: Object.freeze({
    reference: Object.freeze({
      id: "system-bastian-eta-06-0261-annex-1-page-9",
      title: "System Bastian Treppe - ETA-06/0261, Anhang 1, Seite 9",
      url: "https://www.dibt.de/pdf_storage/2011/ETA-06%210261%288.05.06-35%2111%29.pdf",
      allowedPlanTypes: Object.freeze(["straight", "quarter_turn", "double_quarter_turn"]),
      walkingZoneRatio: 0.2,
      walkingLineLocation: "freely_selectable_within_walking_zone",
      windingTreadGeometry: "fan_shaped",
    }),
    project: Object.freeze({
      usableWidthMm: 900,
      minimumUsableWidthMm: 900,
      minimumRiseMm: 140,
      maximumRiseMm: 200,
      minimumGoingMm: 260,
      minimumHeadroomMm: 2000,
      minimumLandingDepthMm: 800,
      stepMeasureMinimumMm: 590,
      stepMeasureOptimumMm: 630,
      stepMeasureMaximumMm: 650,
      direction: "up",
      alignedBetweenFloorsToleranceMm: 5,
      outerCorners: "rectilinear_90_degree",
      treadDisplay: "hidden_until_valid",
      positionPreference: "at_wall",
    }),
  }),
  workflow: Object.freeze({
    immutableSourceAnnotation: true,
    separateRevisions: true,
    humanApprovalRequired: true,
    sameGeometryFor2dAnd3d: true,
    wordpressRequiresRightsClearance: true,
  }),
});

export function normalizedRoomRuleKey(room) {
  const text = `${room?.name || ""} ${room?.kind || ""}`.toLocaleLowerCase("de-DE");
  if (/\bhwr\b|\bhtr\b|hauswirtschaft|technik/.test(text)) return "hwrHtr";
  if (/ankleide|dressing/.test(text)) return "dressing";
  if (/garage|carport|stellplatz/.test(text)) return "garage";
  if (/speise|vorrat|pantry/.test(text)) return "pantry";
  if (/eltern|master/.test(text)) return "parents";
  // Check bathroom/wet-room compounds before the generic "kinder" bedroom
  // match below — "Kinderbad" (children's bathroom) contains "kinder" as a
  // substring and was incorrectly being held to the 10 sqm child-bedroom
  // minimum instead of the bathroom rule.
  if (/kinderbad|kinderdusche|kinderwc/.test(text)) return "showerBathroom";
  if (/\bkind\b|kinder/.test(text)) return "child";
  if (/duschbad|du-?bad|shower/.test(text)) return "showerBathroom";
  if (/\bwc\b|toilet/.test(text)) return "wc";
  return null;
}

export function isHabitableRoom(room) {
  if (!FLOORPLAN_RULES.windows.habitableRoomKinds.includes(room?.kind)) return false;
  // Dressing rooms (Ankleide) and garages/carports share the generic "flex"
  // kind with rooms like a home office, but are not an Aufenthaltsraum and
  // do not need a window.
  if (["dressing", "garage"].includes(normalizedRoomRuleKey(room))) return false;
  return true;
}

export function doorCategory(opening) {
  if (opening?.role === "main_entrance") return "mainEntrance";
  if (opening?.role === "terrace_door") return "terraceDoor";
  if (Number(opening?.width) === FLOORPLAN_RULES.doors.smallWcWidthMm) return "smallWc";
  return "internal";
}

export function doorColour(opening) {
  return FLOORPLAN_RULES.doors.colours[doorCategory(opening)];
}
