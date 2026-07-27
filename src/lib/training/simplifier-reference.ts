import knowledge from "../../../data/simplifier-v1/knowledge.json";
import dataset from "../../../data/simplifier-v1/dataset.json";

type SimplifierRoomProfile = {
  floor_level: string;
  room_id: string;
  occurrences: number;
  median_share_of_marked_room_area: number;
};

type SimplifierKnowledge = {
  knowledge_version: string;
  basis: { project_count: number; floor_count: number; room_count: number; element_count: number; house_types: Record<string, number>; floor_levels: Record<string, number> };
  element_counts: Record<string, number>;
  room_profiles: SimplifierRoomProfile[];
  common_floor_programs: Array<{ signature: string; occurrences: number }>;
  limitations: string[];
};

export type ReferencePoint = [number, number];
export type ReferenceRoom = {
  id: string;
  roomId: string;
  roomIds: string[];
  label: string;
  polygon: ReferencePoint[];
  areaRatio: number;
};
export type ReferenceElement = { id: string; type: string; points: ReferencePoint[] };
export type ReferenceFloor = { floorLevel: string; rooms: ReferenceRoom[]; elements: ReferenceElement[] };

type RawRoom = { id: string; room_id: string; room_ids?: string[]; label: string; polygon: number[][]; area_ratio: number };
type RawFloor = { floor_level: string; rooms: RawRoom[]; elements: Array<{ id: string; type: string; points: number[][] }> };
type RawProject = { project_id: string; house_type: string; package_status: string; floors: RawFloor[] };
type SimplifierDataset = { projects: RawProject[] };

export type ReferenceLayoutMatch = {
  projectId: string;
  houseType: string;
  score: number;
  roomIds: string[];
  hasBasement: boolean;
  hasStairs: boolean;
  floors: ReferenceFloor[];
};

export const SIMPLIFIER_REFERENCE = knowledge as SimplifierKnowledge;
const SIMPLIFIER_DATASET = dataset as SimplifierDataset;

function validPoint(point: number[]): point is ReferencePoint {
  return point.length >= 2 && Number.isFinite(point[0]) && Number.isFinite(point[1]);
}

function normalizeProject(project: RawProject) {
  const floors: ReferenceFloor[] = project.floors.map((floor) => ({
    floorLevel: floor.floor_level,
    rooms: floor.rooms.map((room) => ({
      id: room.id,
      roomId: room.room_id,
      roomIds: room.room_ids?.length ? room.room_ids : [room.room_id],
      label: room.label,
      polygon: room.polygon.filter(validPoint),
      areaRatio: Number.isFinite(room.area_ratio) ? room.area_ratio : 0,
    })).filter((room) => room.polygon.length >= 3 && room.areaRatio > 0),
    elements: floor.elements.map((element) => ({
      id: element.id,
      type: element.type,
      points: element.points.filter(validPoint),
    })).filter((element) => element.points.length >= 2),
  }));
  const roomCounts = new Map<string, number>();
  for (const room of floors.flatMap((floor) => floor.rooms)) {
    for (const roomId of new Set(room.roomIds)) roomCounts.set(roomId, (roomCounts.get(roomId) ?? 0) + 1);
  }
  const hasStairs = floors.some((floor) => floor.elements.some((element) => element.type === "stairs"));
  const stairNearWall = floors.some((floor) => floor.elements.some((element) =>
    element.type === "stairs" && element.points.some(([x, y]) => Math.min(x, y, 1 - x, 1 - y) <= 0.2)));
  return {
    projectId: project.project_id,
    houseType: project.house_type,
    floors,
    roomCounts,
    roomIds: [...roomCounts.keys()],
    hasBasement: floors.some((floor) => floor.floorLevel === "basement"),
    habitableFloors: floors.filter((floor) => floor.floorLevel !== "basement").length,
    hasStairs,
    stairNearWall,
  };
}

const STAIR_REVIEW_PROJECT_IDS = new Set([
  "cubicasa_review_high_quality_architectural_904",
]);

const REFERENCE_PROJECTS = SIMPLIFIER_DATASET.projects
  .filter((project) => !STAIR_REVIEW_PROJECT_IDS.has(project.project_id))
  .filter((project) => ["annotated", "reviewed", "training_ready"].includes(project.package_status))
  .map(normalizeProject)
  .filter((project) => project.floors.some((floor) => floor.rooms.length > 0));

export function selectReferenceLayout(input: {
  houseType: string; floors: number; bedrooms: number; bathrooms: number;
  office: boolean; guestWc: boolean; utilityRoom: boolean; basement: boolean;
  stairPreference: "central" | "feature" | "separable" | "undecided";
  variantOffset?: number;
}): ReferenceLayoutMatch | null {
  const desired = new Map<string, number>([
    ["eltern", 1], ["kind", Math.max(0, input.bedrooms - 1)], ["bad", Math.max(1, input.bathrooms)],
    ["wc", input.guestWc ? 1 : 0], ["hwr_htr", input.utilityRoom ? 1 : 0],
    ["wohnen", 1], ["essen", 1], ["kueche", 1],
  ]);
  if (input.office) desired.set("buero", 1);

  const candidates = REFERENCE_PROJECTS.map((project) => {
    let programMatches = 0;
    let programMissing = 0;
    for (const [roomId, wanted] of desired) {
      if (!wanted) continue;
      const actual = project.roomCounts.get(roomId) ?? (roomId === "buero" ? project.roomCounts.get("gast") ?? 0 : 0);
      programMatches += Math.min(actual, wanted);
      programMissing += Math.max(0, wanted - actual);
    }
    const wantsWallStair = input.stairPreference !== "central";
    const score = (project.houseType === input.houseType ? 40 : 0)
      + (project.habitableFloors === input.floors ? 25 : -Math.abs(project.habitableFloors - input.floors) * 8)
      + (project.hasBasement === input.basement ? 10 : -10)
      + programMatches * 3 - programMissing * 2
      + (input.floors > 1 && project.hasStairs ? 8 : input.floors > 1 ? -20 : 0)
      + (input.floors > 1 && wantsWallStair && project.stairNearWall ? 8 : 0);
    return { project, score };
  }).sort((left, right) => right.score - left.score || left.project.projectId.localeCompare(right.project.projectId));

  if (!candidates.length) return null;
  const bestScore = candidates[0].score;
  const shortlist = candidates.filter((candidate) => candidate.score >= bestScore - 4);
  const selected = shortlist[(input.variantOffset ?? 0) % shortlist.length];
  return {
    projectId: selected.project.projectId,
    houseType: selected.project.houseType,
    score: selected.score,
    roomIds: selected.project.roomIds,
    hasBasement: selected.project.hasBasement,
    hasStairs: selected.project.hasStairs,
    floors: selected.project.floors,
  };
}

export function simplifierReferenceLabel() {
  const basis = SIMPLIFIER_REFERENCE.basis;
  return `Simplifier-v1: ${basis.project_count} Projekte / ${basis.floor_count} Geschosse / ${basis.room_count} Räume`;
}

export function simplifierReferenceElementLabel() {
  const counts = SIMPLIFIER_REFERENCE.element_counts;
  const count = (key: string) => Number.isFinite(counts[key]) ? counts[key] : 0;
  return `Referenz enthält ${count("door")} Türen, ${count("window")} Fenster und ${count("stairs")} Treppen`;
}

function profileFor(floorLevel: string, roomIds: string[]) {
  return SIMPLIFIER_REFERENCE.room_profiles
    .filter((profile) => profile.floor_level === floorLevel && roomIds.includes(profile.room_id))
    .sort((left, right) => right.occurrences - left.occurrences)[0];
}

export function referenceAreaFromSimplifier(
  floorLevel: "groundfloor" | "upperfloor" | "basement", roomIds: string[], floorArea: number,
  fallbackArea: number, minArea: number, maxArea: number,
) {
  const profile = profileFor(floorLevel, roomIds);
  if (!profile) return fallbackArea;
  const area = Math.round(profile.median_share_of_marked_room_area * floorArea);
  return Math.min(maxArea, Math.max(minArea, area));
}

export function commonUpperFloorProgramFor(houseType: string) {
  return SIMPLIFIER_REFERENCE.common_floor_programs.find((program) => program.signature.startsWith(`${houseType}:upperfloor:`));
}
