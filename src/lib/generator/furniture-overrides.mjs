// Manual furniture overrides layered on the automatic placement engine.
// See plans/move-furniture-to-workbench.md (APPROVED, 2026-08-16).
//
// Furnishing used to be hand-drawn in the Simplifier annotator, in a symbol
// system that had no route into the renderer at all — 1 of 234 projects ever
// used it. The workbench already places furniture automatically
// (furniture-placement.mjs) and already renders it, so the hand work moves
// here and becomes a diff against the engine's output rather than a parallel
// world.
//
// A diff, specifically, and not a saved copy of the final layout: geometry
// gets corrected, rooms get re-cut, the engine re-runs. If the editor stored
// absolute results, every re-run would either throw away the hand work or
// freeze the layout against stale rooms. Overrides key off a stable
// `placement_id`, so an untouched item follows the geometry while an edited
// one keeps its edit.
//
// Presentation-only, exactly like the engine it wraps: nothing here touches
// walls, openings, geometry_hash, or the canonical JSON.

/**
 * Stable identity for an engine placement.
 *
 * `room_id:type` works because the engine places at most one item of each
 * type per room (furnitureTypesForRoom returns a unique list). Manual
 * additions use `room_id:manual-N`, which cannot collide with a type name.
 */
export function placementId(roomId, type) {
  return `${roomId}:${type}`;
}

export function emptyOverrideDocument(meta = {}) {
  return {
    project_id: meta.project_id ?? null,
    floor_id: meta.floor_id ?? null,
    style: meta.style ?? null,
    overrides: [],
  };
}

const ACTIONS = new Set(["move", "replace", "delete", "add"]);

/**
 * Record an edit, replacing any earlier edit of the same placement.
 *
 * Returns a new document; the caller's copy is left alone so an editor can
 * keep an undo stack of plain values.
 */
export function upsertOverride(document, override) {
  if (!override?.placement_id) throw new Error("An override needs a placement_id.");
  if (!ACTIONS.has(override.action)) {
    throw new Error(`Unknown override action: ${override.action}`);
  }
  const kept = (document.overrides || []).filter(
    (item) => item.placement_id !== override.placement_id);
  return { ...document, overrides: [...kept, { ...override }] };
}

export function removeOverride(document, placementIdValue) {
  return {
    ...document,
    overrides: (document.overrides || []).filter(
      (item) => item.placement_id !== placementIdValue),
  };
}

function decorate(placement, roomId) {
  return {
    ...placement,
    placement_id: placement.placement_id ?? placementId(roomId, placement.type),
    mirrored: placement.mirrored ?? false,
    source: placement.source ?? "engine",
  };
}

function applyToPlacement(placement, override) {
  const next = { ...placement, source: "manual" };
  if (override.action === "move") {
    if (override.position_mm) next.position_mm = [...override.position_mm];
    if (override.rotation_deg !== undefined) next.rotation_deg = override.rotation_deg;
    if (override.mirrored !== undefined) next.mirrored = override.mirrored;
    return next;
  }
  if (override.action === "replace") {
    if (override.asset_id) next.asset_id = override.asset_id;
    if (override.type) next.type = override.type;
    // Deliberately not touching position/rotation: swapping which sofa it is
    // should not move the sofa.
    return next;
  }
  return next;
}

/**
 * Merge a saved override document into a floor plan from planFloorFurniture().
 *
 * Pure: the input plan is never mutated, so a caller can re-merge a different
 * document against the same engine result.
 *
 * Overrides that match nothing are surfaced in `orphaned_overrides` rather
 * than dropped — an override pointing at a room that no longer exists means a
 * human edit is about to be lost, and that has to be visible.
 */
export function applyFurnitureOverrides(plan, document) {
  const overrides = new Map(
    (document?.overrides || []).map((item) => [item.placement_id, item]));
  const consumed = new Set();

  const rooms = (plan?.rooms || []).map((room) => {
    const placements = [];
    const removed = [];
    for (const placement of room.placements || []) {
      const decorated = decorate(placement, room.room_id);
      const override = overrides.get(decorated.placement_id);
      if (!override) {
        placements.push(decorated);
        continue;
      }
      consumed.add(decorated.placement_id);
      if (override.action === "delete") {
        removed.push(decorated.placement_id);
        continue;
      }
      if (override.action === "add") {
        // An "add" whose id already exists is a move in disguise; treat it as
        // one rather than producing two items with the same id.
        placements.push(applyToPlacement(decorated, { ...override, action: "move" }));
        continue;
      }
      placements.push(applyToPlacement(decorated, override));
    }

    for (const override of overrides.values()) {
      if (override.action !== "add") continue;
      if (consumed.has(override.placement_id)) continue;
      if (override.room_id !== room.room_id) continue;
      consumed.add(override.placement_id);
      placements.push({
        placement_id: override.placement_id,
        asset_id: override.asset_id,
        type: override.type,
        position_mm: [...(override.position_mm || [0, 0])],
        rotation_deg: override.rotation_deg ?? 0,
        mirrored: override.mirrored ?? false,
        height_mm: override.height_mm ?? 0,
        source: "manual",
      });
    }

    return { ...room, placements, removed };
  });

  const orphaned = [...overrides.keys()].filter((id) => !consumed.has(id));
  return { ...plan, rooms, orphaned_overrides: orphaned };
}
