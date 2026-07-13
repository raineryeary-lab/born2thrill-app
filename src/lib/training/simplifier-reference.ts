import knowledge from "../../../data/simplifier-v1/knowledge.json";

type SimplifierRoomProfile = {
  floor_level: string;
  room_id: string;
  occurrences: number;
  median_share_of_marked_room_area: number;
};

type SimplifierKnowledge = {
  knowledge_version: string;
  basis: {
    project_count: number;
    floor_count: number;
    room_count: number;
    element_count: number;
    house_types: Record<string, number>;
    floor_levels: Record<string, number>;
  };
  element_counts: Record<"door" | "window" | "stairs", number>;
  room_profiles: SimplifierRoomProfile[];
  common_floor_programs: Array<{ signature: string; occurrences: number }>;
  limitations: string[];
};

export const SIMPLIFIER_REFERENCE = knowledge as SimplifierKnowledge;

export function simplifierReferenceLabel() {
  const basis = SIMPLIFIER_REFERENCE.basis;
  return `Simplifier-v1: ${basis.project_count} Projekte / ${basis.floor_count} Geschosse / ${basis.room_count} Räume`;
}

export function simplifierReferenceElementLabel() {
  const counts = SIMPLIFIER_REFERENCE.element_counts;
  return `Referenz enthält ${counts.door} Türen, ${counts.window} Fenster und ${counts.stairs} Treppen`;
}

function profileFor(floorLevel: string, roomIds: string[]) {
  return SIMPLIFIER_REFERENCE.room_profiles
    .filter((profile) => profile.floor_level === floorLevel && roomIds.includes(profile.room_id))
    .sort((left, right) => right.occurrences - left.occurrences)[0];
}

export function referenceAreaFromSimplifier(
  floorLevel: "groundfloor" | "upperfloor" | "basement",
  roomIds: string[],
  floorArea: number,
  fallbackArea: number,
  minArea: number,
  maxArea: number,
) {
  const profile = profileFor(floorLevel, roomIds);
  if (!profile) return fallbackArea;

  const area = Math.round(profile.median_share_of_marked_room_area * floorArea);
  return Math.min(maxArea, Math.max(minArea, area));
}

export function commonUpperFloorProgramFor(houseType: string) {
  return SIMPLIFIER_REFERENCE.common_floor_programs.find((program) =>
    program.signature.startsWith(`${houseType}:upperfloor:`));
}
