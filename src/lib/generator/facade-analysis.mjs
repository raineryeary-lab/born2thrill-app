import { createHash } from "node:crypto";

const FACADE_DEFINITIONS = [
  { id: "facade-min_y", normal: [0, -1], tangent: [1, 0] },
  { id: "facade-max_x", normal: [1, 0], tangent: [0, 1] },
  { id: "facade-max_y", normal: [0, 1], tangent: [-1, 0] },
  { id: "facade-min_x", normal: [-1, 0], tangent: [0, -1] },
];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const round = (value, digits = 4) => Number(value.toFixed(digits));
const scoreItem = (code, value, evidence = []) => ({ code, value: round(value), evidence });

function boundsOf(canonical) {
  const points = canonical?.floors?.[0]?.footprint || [];
  if (points.length < 3) throw new Error("Facade analysis requires a valid footprint.");
  const xs = points.map((point) => Number(point[0]));
  const ys = points.map((point) => Number(point[1]));
  return { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
}

function classifyWall(wall, bounds) {
  const [x1, y1] = wall.start;
  const [x2, y2] = wall.end;
  const midpoint = [(x1 + x2) / 2, (y1 + y2) / 2];
  const dx = Math.abs(x2 - x1);
  const dy = Math.abs(y2 - y1);
  if (dx >= dy) return Math.abs(midpoint[1] - bounds.minY) <= Math.abs(midpoint[1] - bounds.maxY) ? "facade-min_y" : "facade-max_y";
  return Math.abs(midpoint[0] - bounds.minX) <= Math.abs(midpoint[0] - bounds.maxX) ? "facade-min_x" : "facade-max_x";
}

function openingBalance(openings) {
  if (!openings.length) return 0;
  const positions = openings.map((item) => Number(item.position)).filter(Number.isFinite).sort((a, b) => a - b);
  if (!positions.length) return 0;
  if (positions.length === 1) return clamp(1 - Math.abs(positions[0] - 0.5) * 2, 0, 1);
  let error = 0;
  for (let index = 0; index < Math.ceil(positions.length / 2); index += 1) {
    error += Math.abs((positions[index] + positions[positions.length - 1 - index]) - 1);
  }
  return clamp(1 - error / Math.ceil(positions.length / 2), 0, 1);
}

function verticalAlignment(openings) {
  const floors = new Map();
  for (const opening of openings) {
    if (!floors.has(opening.floor_id)) floors.set(opening.floor_id, []);
    floors.get(opening.floor_id).push(Number(opening.position));
  }
  if (floors.size < 2) return 0;
  const lists = [...floors.values()];
  const lower = lists[0];
  const upper = lists.slice(1).flat();
  if (!lower.length || !upper.length) return 0;
  const matches = lower.filter((position) => upper.some((candidate) => Math.abs(candidate - position) <= 0.08)).length;
  return matches / Math.max(lower.length, upper.length);
}

function verticalConsistency(openings) {
  if (!openings.length) return 0;
  const groups = new Map();
  for (const opening of openings) {
    const key = `${Number(opening.sill_height_mm ?? 0)}:${Number(opening.height_mm ?? 0)}`;
    groups.set(key, (groups.get(key) || 0) + 1);
  }
  return Math.max(...groups.values()) / openings.length;
}

function analyzeOneFacade(definition, walls, openings) {
  const terrace = openings.filter((opening) => opening.role === "terrace_door");
  const entrances = openings.filter((opening) => opening.role === "main_entrance");
  const glazed = openings.filter((opening) => opening.opening_type === "window" || opening.glazed === true);
  const glazedWidthMm = glazed.reduce((sum, opening) => sum + Number(opening.width_mm || opening.width || 0), 0);
  const balance = openingBalance(openings);
  const alignment = verticalAlignment(openings);
  const consistency = verticalConsistency(openings);
  const usefulGlazing = Math.min(15, glazedWidthMm / 1000 * 4);
  const common = [
    scoreItem("useful_glazing", usefulGlazing, glazed.map((opening) => opening.id)),
    scoreItem("balanced_openings", balance * 10, openings.map((opening) => opening.id)),
    scoreItem("cross_floor_alignment", alignment * 8, openings.map((opening) => opening.id)),
    scoreItem("head_sill_consistency", consistency * 8, openings.map((opening) => opening.id)),
    scoreItem("blank_wall_penalty", openings.length ? 0 : -5, []),
  ];
  const gardenBreakdown = [
    scoreItem("terrace_access", terrace.length * 25, terrace.map((opening) => opening.id)),
    ...common,
    scoreItem("entrance_on_garden_penalty", entrances.length * -15, entrances.map((opening) => opening.id)),
  ];
  const streetBreakdown = [
    scoreItem("main_entrance_hierarchy", entrances.length * 25, entrances.map((opening) => opening.id)),
    ...common,
    scoreItem("terrace_on_street_penalty", terrace.length * -10, terrace.map((opening) => opening.id)),
  ];
  const visualBreakdown = [...common, scoreItem("opening_rhythm", Math.min(6, openings.length * 1.5), openings.map((opening) => opening.id))];
  const sum = (items) => round(items.reduce((total, item) => total + item.value, 0));
  return {
    id: definition.id,
    outward_normal: definition.normal,
    tangent: definition.tangent,
    wall_ids: walls.map((item) => item.wall.id),
    evidence_opening_ids: openings.map((item) => item.id),
    metrics: {
      opening_count: openings.length,
      terrace_door_count: terrace.length,
      main_entrance_count: entrances.length,
      glazed_width_mm: glazedWidthMm,
      balance: round(balance),
      cross_floor_alignment: round(alignment),
      vertical_consistency: round(consistency),
    },
    scores: { garden: sum(gardenBreakdown), street: sum(streetBreakdown), visual: sum(visualBreakdown) },
    score_breakdown: visualBreakdown,
    garden_score_breakdown: gardenBreakdown,
    street_score_breakdown: streetBreakdown,
  };
}

export function analyzeFacades(canonical, options = {}) {
  const cameraAngleDeg = Number(options.cameraAngleDeg ?? 35);
  if (!Number.isFinite(cameraAngleDeg) || cameraAngleDeg < 28 || cameraAngleDeg > 45) {
    throw new Error("Facade camera angle must be between 28 and 45 degrees.");
  }
  const preferredView = options.preferredView || "garden";
  if (!["garden", "street", "east", "west"].includes(preferredView)) throw new Error(`Unsupported facade view: ${preferredView}`);
  const bounds = boundsOf(canonical);
  const wallsByFacade = new Map(FACADE_DEFINITIONS.map((definition) => [definition.id, []]));
  const openingsByFacade = new Map(FACADE_DEFINITIONS.map((definition) => [definition.id, []]));
  for (const floor of canonical.floors || []) {
    const wallMap = new Map((floor.walls || []).map((wall) => [wall.id, wall]));
    for (const wall of floor.walls || []) {
      if (wall.wall_type !== "exterior") continue;
      const facadeId = classifyWall(wall, bounds);
      wallsByFacade.get(facadeId).push({ floor_id: floor.id, wall });
    }
    for (const opening of floor.openings || []) {
      const wall = wallMap.get(opening.wall_id);
      if (!wall || wall.wall_type !== "exterior") continue;
      const facadeId = classifyWall(wall, bounds);
      openingsByFacade.get(facadeId).push({ ...opening, floor_id: floor.id, width_mm: Number(opening.width_mm ?? opening.width ?? 0) });
    }
  }
  const facades = FACADE_DEFINITIONS.map((definition) => analyzeOneFacade(definition, wallsByFacade.get(definition.id), openingsByFacade.get(definition.id)));
  const bestBy = (scoreName) => [...facades].sort((a, b) => b.scores[scoreName] - a.scores[scoreName] || a.id.localeCompare(b.id))[0];
  const gardenEvidence = facades.filter((facade) => facade.metrics.terrace_door_count > 0);
  const streetEvidence = facades.filter((facade) => facade.metrics.main_entrance_count > 0);
  const gardenFacade = gardenEvidence.length ? [...gardenEvidence].sort((a, b) => b.scores.garden - a.scores.garden || a.id.localeCompare(b.id))[0] : bestBy("garden");
  const streetFacade = streetEvidence.length ? [...streetEvidence].sort((a, b) => b.scores.street - a.scores.street || a.id.localeCompare(b.id))[0] : bestBy("street");
  const preferredMap = { garden: gardenFacade.id, street: streetFacade.id, east: "facade-max_x", west: "facade-min_x" };
  const selectedFacade = facades.find((facade) => facade.id === preferredMap[preferredView]) || bestBy("visual");
  const selectedIndex = FACADE_DEFINITIONS.findIndex((definition) => definition.id === selectedFacade.id);
  const adjacentCandidates = [
    facades[(selectedIndex + FACADE_DEFINITIONS.length - 1) % FACADE_DEFINITIONS.length],
    facades[(selectedIndex + 1) % FACADE_DEFINITIONS.length],
  ];
  const adjacentFacade = [...adjacentCandidates].sort((a, b) => b.scores.visual - a.scores.visual || a.id.localeCompare(b.id))[0];
  const payload = {
    schema: "dmh-facade-analysis-v1",
    source_geometry_hash: canonical.geometry_hash,
    preferred_view: preferredView,
    facades,
    semantic: {
      garden_facade_id: gardenFacade.id,
      street_facade_id: streetFacade.id,
      schokoladenseite_facade_id: gardenEvidence.length ? gardenFacade.id : bestBy("visual").id,
      confidence: gardenEvidence.length && streetEvidence.length ? "high" : "review_required",
    },
    selection: {
      selected_facade_id: selectedFacade.id,
      adjacent_facade_id: adjacentFacade.id,
      camera_angle_deg: cameraAngleDeg,
      outward_normal: selectedFacade.outward_normal,
      adjacent_normal: adjacentFacade.outward_normal,
      left_right_rule: "stronger_adjacent_visual_score_then_stable_id",
    },
  };
  return { ...payload, presentation_hash: createHash("sha256").update(JSON.stringify(payload)).digest("hex") };
}
