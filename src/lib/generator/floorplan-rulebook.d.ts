export interface RulebookRoom {
  name?: string;
  kind?: string;
  [key: string]: unknown;
}
export interface RulebookOpening {
  role?: string;
  width?: number;
  opening_type?: string;
  [key: string]: unknown;
}

export interface FloorplanRulesGeometry {
  coordinateUnit: string;
  editSnapMm: number;
  alignmentToleranceMm: number;
  coverageToleranceMm2: number;
  sourceAxisSnapTolerancePx: number;
  footprintBoundarySnapMm: number;
}
export interface FloorplanRulesWalls {
  exteriorThicknessMm: number;
  interiorThicknessMm: number;
  rectilinearOnly: boolean;
  openingsMustBeWallLinked: boolean;
}
export interface FloorplanRulesDoorColours {
  mainEntrance: string;
  terraceDoor: string;
  internal: string;
  smallWc: string;
  openPassage: string;
}
export interface FloorplanRulesDoors {
  internalWidthMm: number;
  smallWcWidthMm: number;
  entranceWidthMm: number;
  terraceWidthMm: number;
  terraceMinimumHeightMm: number;
  renderClosed: boolean;
  colours: FloorplanRulesDoorColours;
}
export interface FloorplanRulesWindows {
  minimumGlazingToRoomAreaRatio: number;
  defaultHeightMm: number;
  defaultSillHeightMm: number;
  habitableRoomKinds: readonly string[];
  wetAndServiceRoomsMayBeInternal: boolean;
}
export interface FloorplanRulesRoomRule {
  match: string;
  minimumM2?: number;
  maximumM2?: number;
  preferredMinimumM2?: number;
  preferredMaximumM2?: number;
  preferredM2?: number;
}
export interface FloorplanRulesRooms {
  hwrHtr: FloorplanRulesRoomRule;
  wc: FloorplanRulesRoomRule;
  showerBathroom: FloorplanRulesRoomRule;
  pantry: FloorplanRulesRoomRule;
  child: FloorplanRulesRoomRule;
  parents: FloorplanRulesRoomRule;
  dressing: FloorplanRulesRoomRule;
}
export interface FloorplanRulesCirculation {
  entranceMustReachCirculation: boolean;
  everyRequiredRoomReachable: boolean;
  noUncoveredResidualGaps: boolean;
  stairMustConnectToCirculation: boolean;
}
export interface FloorplanRulesStairReference {
  id: string;
  title: string;
  url: string;
  allowedPlanTypes: readonly string[];
  walkingZoneRatio: number;
  walkingLineLocation: string;
  windingTreadGeometry: string;
}
export interface FloorplanRulesStairProject {
  usableWidthMm: number;
  minimumUsableWidthMm: number;
  minimumRiseMm: number;
  maximumRiseMm: number;
  minimumGoingMm: number;
  minimumHeadroomMm: number;
  minimumLandingDepthMm: number;
  stepMeasureMinimumMm: number;
  stepMeasureOptimumMm: number;
  stepMeasureMaximumMm: number;
  direction: string;
  alignedBetweenFloorsToleranceMm: number;
  outerCorners: string;
  treadDisplay: string;
  positionPreference: string;
}
export interface FloorplanRulesStairs {
  reference: FloorplanRulesStairReference;
  project: FloorplanRulesStairProject;
}
export interface FloorplanRulesWorkflow {
  immutableSourceAnnotation: boolean;
  separateRevisions: boolean;
  humanApprovalRequired: boolean;
  sameGeometryFor2dAnd3d: boolean;
  wordpressRequiresRightsClearance: boolean;
}
export interface FloorplanRules {
  geometry: FloorplanRulesGeometry;
  walls: FloorplanRulesWalls;
  doors: FloorplanRulesDoors;
  windows: FloorplanRulesWindows;
  rooms: FloorplanRulesRooms;
  circulation: FloorplanRulesCirculation;
  stairs: FloorplanRulesStairs;
  workflow: FloorplanRulesWorkflow;
}

export const FLOORPLAN_RULEBOOK_VERSION: string;
export const FLOORPLAN_RULES: FloorplanRules;
export function normalizedRoomRuleKey(room: RulebookRoom): string | null;
export function isHabitableRoom(room: RulebookRoom): boolean;
export function doorCategory(opening: RulebookOpening): "mainEntrance" | "smallWc" | "internal";
export function doorColour(opening: RulebookOpening): string;
