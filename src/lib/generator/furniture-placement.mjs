// Room-kind-driven automatic furniture placement.
// See plans/furnished-3d-dollhouse-render-v1.md (PROPOSED, 2026-08-05).
//
// v1 scope, deliberately limited and documented rather than guessed:
//  - Places one furniture item per room-boundary edge, largest footprint
//    first, centered along the edge and offset inward by half its depth.
//  - Does NOT do "surround" placement (e.g. dining chairs around a table).
//    Freestanding chairs are intentionally left unplaced in v1 rather than
//    pushed against a wall, which would look wrong. Tracked as a v2 item.
//  - A room with more required items than usable edges (or an edge too
//    short for an item) reports those items as `unplaced`, it does not
//    crash or silently overlap geometry.
//
// This module only reasons about `room.polygon` (already used elsewhere in
// the codebase for `polygonAreaM2`) and does not touch `floor.walls`, so it
// has no coupling to wall IDs, openings, or the geometry-lock/hash — it is
// presentation-only, matching the "Floorplan-suite invariant" in the plan.

import { normalizedRoomRuleKey } from "./floorplan-rulebook.mjs";
import { getFurnitureAsset, getPlacementMode, MOUNT_HEIGHT_MM } from "./furniture-catalog.mjs";
import { polygonAreaM2 } from "./correction-geometry.mjs";

const WALL_MARGIN_MM = 40;

// Room-rule-key -> furniture types, for room kinds normalizedRoomRuleKey
// already recognizes by name (mirrors floorplan-rulebook.mjs's own
// precedence: specific rule key first, then a `room.kind` fallback below).
// `table_lamp` is deliberately never auto-placed (like `dining_chair`) — it
// needs to sit on top of another placed item (a nightstand/side table),
// which is relative-to-another-item placement, not wall/floor placement.
// Tracked as a v2 item alongside dining-chair surround-placement.
const FURNITURE_BY_RULE_KEY = Object.freeze({
  hwrHtr: ["washer_dryer_unit", "storage_shelving"],
  wc: ["sink", "bathroom_vanity"],
  showerBathroom: ["shower", "bathtub", "sink", "bathroom_vanity", "towel", "mirror"],
  pantry: [],
  child: ["bed_double", "wardrobe", "nightstand", "rug", "mirror", "shoe_rack"],
  parents: ["bed_double", "wardrobe", "nightstand", "rug", "mirror", "shoe_rack"],
  dressing: ["dressing_wardrobe", "clothing_rack", "shoe_rack"],
  garage: [],
});

function furnitureTypesForRoom(room) {
  const ruleKey = normalizedRoomRuleKey(room);
  if (ruleKey && Object.prototype.hasOwnProperty.call(FURNITURE_BY_RULE_KEY, ruleKey)) {
    return FURNITURE_BY_RULE_KEY[ruleKey];
  }
  switch (room.kind) {
    case "sleeping":
      return ["bed_double", "wardrobe", "nightstand", "rug", "mirror", "shoe_rack"];
    case "living": {
      const name = `${room.name || ""}`.toLocaleLowerCase("de-DE");
      const hasDining = /essen|dining/.test(name);
      const base = ["sofa", "coffee_table", "tv_unit", "rug", "wall_art", "floor_lamp", "potted_plant"];
      return hasDining ? [...base, "dining_table"] : base;
    }
    case "wet":
      // A room named "Bad" matches no rule key in floorplan-rulebook.mjs
      // (which knows duschbad/du-bad/shower and wc, but not plain "Bad"), so
      // it arrived here with no rule key and fell through to the default,
      // getting no furniture at all. Keyed off room.kind instead, which is
      // reliable for wet rooms. Deliberately not fixed in the rulebook: that
      // file also drives validation, where showerBathroom carries a 3-4 sqm
      // preferred range that a 12.4 sqm Bad would immediately violate.
      return ["shower", "bathtub", "sink", "bathroom_vanity", "towel", "mirror"];
    case "service":
      return ["washer_dryer_unit", "storage_shelving"];
    case "circulation":
      return ["coat_rack", "mirror"];
    case "flex":
      return ["desk", "office_chair", "wall_art"];
    default:
      return [];
  }
}

function distance(a, b) {
  return Math.hypot(b[0] - a[0], b[1] - a[1]);
}

function polygonEdges(polygon) {
  return polygon.map((point, index) => [point, polygon[(index + 1) % polygon.length]]);
}

function polygonCentroid(polygon) {
  const sum = polygon.reduce((acc, [x, y]) => [acc[0] + x, acc[1] + y], [0, 0]);
  return [sum[0] / polygon.length, sum[1] / polygon.length];
}

function inwardNormalForEdge([a, b], centroid) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const length = Math.hypot(dx, dy) || 1;
  const candidate = [-dy / length, dx / length];
  const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const towardCentroid = [centroid[0] - mid[0], centroid[1] - mid[1]];
  const dot = candidate[0] * towardCentroid[0] + candidate[1] * towardCentroid[1];
  return dot >= 0 ? candidate : [-candidate[0], -candidate[1]];
}

function edgeRotationDeg([a, b]) {
  return (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180) / Math.PI;
}

/**
 * Plan furniture placement for a single room.
 * @param {{ id: string, name?: string, kind?: string, polygon: number[][] }} room
 * @param {"modern"|"classic"} style
 * @returns {{ room_id: string, placements: Array<{asset_id:string,type:string,position_mm:number[],rotation_deg:number,height_mm:number}>, unplaced: Array<{type:string,reason:string}> }}
 */
export function planRoomFurniture(room, style) {
  if (!room?.polygon || room.polygon.length < 3) throw new Error(`Room ${room?.id ?? "?"} has no usable polygon.`);
  const types = furnitureTypesForRoom(room);
  const centroid = polygonCentroid(room.polygon);
  const edges = polygonEdges(room.polygon)
    .map((edge) => ({ edge, length: distance(edge[0], edge[1]) }))
    .sort((a, b) => b.length - a.length);

  const placements = [];
  const unplaced = [];
  const usedEdgeIndexes = new Set();

  // "floor_center" items (e.g. a rug) don't compete for wall space — place
  // them first and separately, at the room centroid.
  const floorCenterTypes = types.filter((type) => getPlacementMode(type) === "floor_center");
  for (const type of floorCenterTypes) {
    const asset = getFurnitureAsset(type, style);
    placements.push({
      asset_id: asset.id,
      type,
      position_mm: [Math.round(centroid[0]), Math.round(centroid[1])],
      rotation_deg: 0,
      height_mm: 0,
    });
  }

  // Everything else (default "floor" items, and "wall_mounted" items like
  // art/mirrors, which use the same X/Y wall logic but render higher up)
  // competes for wall edges, largest footprint first, so big items claim
  // the longest walls.
  const wallItems = types
    .filter((type) => getPlacementMode(type) !== "floor_center")
    .map((type) => ({ type, asset: getFurnitureAsset(type, style) }))
    .sort((a, b) => b.asset.bounding_box.width_mm - a.asset.bounding_box.width_mm);

  for (const item of wallItems) {
    const requiredLength = item.asset.bounding_box.width_mm + WALL_MARGIN_MM * 2;
    const edgeSlot = edges.find(({ length }, index) => !usedEdgeIndexes.has(index) && length >= requiredLength);
    const edgeIndex = edgeSlot ? edges.indexOf(edgeSlot) : -1;
    if (edgeIndex === -1) {
      unplaced.push({ type: item.type, reason: "insufficient_wall_length" });
      continue;
    }
    usedEdgeIndexes.add(edgeIndex);
    const { edge } = edges[edgeIndex];
    const [a, b] = edge;
    const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    const normal = inwardNormalForEdge(edge, centroid);
    const offset = item.asset.bounding_box.depth_mm / 2 + WALL_MARGIN_MM;
    const position_mm = [mid[0] + normal[0] * offset, mid[1] + normal[1] * offset];
    placements.push({
      asset_id: item.asset.id,
      type: item.type,
      position_mm: [Math.round(position_mm[0]), Math.round(position_mm[1])],
      rotation_deg: Math.round(edgeRotationDeg(edge) * 100) / 100,
      height_mm: MOUNT_HEIGHT_MM[item.type] ?? 0,
    });
  }

  return { room_id: room.id, style, placements, unplaced };
}

/**
 * Plan furniture for every room on a floor. Rooms below `minAreaM2` are
 * skipped entirely (too small to furnish meaningfully) and reported in
 * `skipped` rather than producing cramped/overlapping placements.
 */
export function planFloorFurniture(floor, style, options = {}) {
  const minAreaM2 = Number(options.minAreaM2 ?? 3);
  const rooms = floor?.rooms || [];
  const results = [];
  const skipped = [];
  for (const room of rooms) {
    const areaM2 = room.area_m2 ?? polygonAreaM2(room.polygon);
    if (areaM2 < minAreaM2) {
      skipped.push({ room_id: room.id, reason: "room_too_small", area_m2: areaM2 });
      continue;
    }
    results.push(planRoomFurniture(room, style));
  }
  return { floor_id: floor?.id ?? null, style, rooms: results, skipped };
}
