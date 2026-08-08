// Furniture asset catalogue for the furnished 3D dollhouse render pipeline.
// See plans/furnished-3d-dollhouse-render-v1.md (PROPOSED, 2026-08-05).
//
// IMPORTANT: every entry below is a PLACEHOLDER. Bounding-box dimensions are
// real-world standard furniture sizes (so placement logic can be developed
// and tested meaningfully), but no actual 3D mesh exists yet for any entry.
// `status: "placeholder"` must flip to "accepted" (with a real `asset_path`
// and recorded `source`/`license`) before any entry is used in a real render.
// Sourcing (AI-generation vendor pick, or fallback asset-pack purchase) is
// an unresolved question in the plan and needs Rainer's decision — nothing
// here should be treated as production-ready.

export const FURNITURE_STYLES = Object.freeze(["modern", "classic"]);

/**
 * @typedef {Object} FurnitureCatalogEntry
 * @property {string} id
 * @property {string} type
 * @property {"modern"|"classic"} style
 * @property {{ width_mm: number, depth_mm: number, height_mm: number }} bounding_box
 * @property {"placeholder"|"accepted"|"rejected"} status
 * @property {string|null} asset_path
 * @property {"ai_generated"|"asset_pack"|null} source
 * @property {string|null} license
 */

function entry(type, style, width_mm, depth_mm, height_mm) {
  return Object.freeze({
    id: `${type}__${style}`,
    type,
    style,
    bounding_box: Object.freeze({ width_mm, depth_mm, height_mm }),
    status: "placeholder",
    asset_path: null,
    source: null,
    license: null,
  });
}

// Real-world standard dimensions (mm), duplicated per style until real
// per-style geometry exists. Width = along the wall it's typically placed
// against; depth = distance the piece projects into the room.
const BASE_DIMENSIONS = Object.freeze({
  bed_double: [1600, 2000, 600],
  nightstand: [450, 400, 550],
  wardrobe: [1200, 600, 2100],
  sofa: [2000, 900, 800],
  coffee_table: [1100, 600, 400],
  tv_unit: [1600, 400, 500],
  dining_table: [1600, 900, 750],
  dining_chair: [450, 500, 900],
  washer_dryer_unit: [600, 600, 850],
  storage_shelving: [900, 400, 1800],
  dressing_wardrobe: [1500, 600, 2100],
  desk: [1400, 700, 750],
  office_chair: [600, 600, 950],
  coat_rack: [800, 350, 1900],
  bathroom_vanity: [900, 500, 850],
  // Decor/accessory items, added to close the gap between bare furniture
  // and Rainer's reference photos (rug, art, lamps, plant, mirror all
  // visible there). Width/depth = floor footprint or wall-facing extent;
  // depth is intentionally tiny for flat wall-mounted pieces.
  rug: [2000, 1400, 20],
  wall_art: [800, 30, 1000],
  mirror: [700, 30, 1600],
  floor_lamp: [400, 400, 1600],
  table_lamp: [250, 250, 450],
  potted_plant: [400, 400, 1200],
  // Bathroom fixtures and accessories (modern + classic styles for each).
  shower: [1000, 1000, 2100],
  bathtub: [1800, 800, 600],
  sink: [600, 500, 850],
  towel: [600, 400, 20],
  // Wardrobe/closet storage.
  clothing_rack: [1500, 500, 1700],
  shoe_rack: [900, 400, 1000],
});

export const FURNITURE_CATALOG = Object.freeze(
  Object.entries(BASE_DIMENSIONS).flatMap(([type, [width_mm, depth_mm, height_mm]]) =>
    FURNITURE_STYLES.map((style) => entry(type, style, width_mm, depth_mm, height_mm))
  )
);

const CATALOG_BY_KEY = new Map(FURNITURE_CATALOG.map((item) => [item.id, item]));

export function getFurnitureAsset(type, style) {
  const item = CATALOG_BY_KEY.get(`${type}__${style}`);
  if (!item) throw new Error(`No furniture catalog entry for type "${type}" style "${style}".`);
  return item;
}

export function listFurnitureTypesForStyle(style) {
  if (!FURNITURE_STYLES.includes(style)) throw new Error(`Unsupported furniture style: ${style}`);
  return FURNITURE_CATALOG.filter((item) => item.style === style).map((item) => item.type);
}

// --- Material finishes -----------------------------------------------------
// Colour/material variety within a style is applied procedurally at render
// time (same pattern as wall/door/glass materials in
// export-floorplan-blender.py: `material(name, color, metallic, roughness)`),
// not by generating a new mesh. One accepted mesh per (type, style) can be
// rendered in any of its compatible finishes for zero extra generation cost.

/**
 * @typedef {Object} FurnitureFinish
 * @property {string} name
 * @property {"fabric"|"glass"|"metal"|"wood"} category
 * @property {[number, number, number]} color RGB, 0-1, matches the Blender `material()` helper
 * @property {number} metallic
 * @property {number} roughness
 * @property {boolean} striped
 */

function finish(name, category, color, metallic, roughness, striped = false) {
  return Object.freeze({ name, category, color: Object.freeze(color), metallic, roughness, striped });
}

export const FURNITURE_FINISHES = Object.freeze([
  finish("fabric-charcoal", "fabric", [0.16, 0.16, 0.18], 0, 0.85),
  finish("fabric-navy", "fabric", [0.09, 0.13, 0.28], 0, 0.85),
  finish("fabric-cream", "fabric", [0.88, 0.84, 0.76], 0, 0.85),
  finish("fabric-terracotta", "fabric", [0.62, 0.32, 0.22], 0, 0.85),
  finish("fabric-sage-stripe", "fabric", [0.55, 0.62, 0.52], 0, 0.85, true),
  finish("fabric-navy-stripe", "fabric", [0.09, 0.13, 0.28], 0, 0.85, true),
  finish("wood-oak", "wood", [0.72, 0.58, 0.4], 0, 0.55),
  finish("wood-walnut", "wood", [0.32, 0.2, 0.14], 0, 0.5),
  finish("wood-white-oak", "wood", [0.82, 0.76, 0.66], 0, 0.6),
  finish("metal-matte-black", "metal", [0.06, 0.06, 0.07], 0.6, 0.35),
  finish("metal-brass", "metal", [0.71, 0.55, 0.24], 0.85, 0.25),
  finish("metal-brushed-steel", "metal", [0.62, 0.63, 0.65], 0.75, 0.3),
  finish("glass-clear", "glass", [0.85, 0.9, 0.92], 0.05, 0.08),
  finish("glass-smoked", "glass", [0.22, 0.24, 0.26], 0.05, 0.1),
]);

const FINISHES_BY_NAME = new Map(FURNITURE_FINISHES.map((item) => [item.name, item]));

// Which finish categories make sense on which furniture type. A sofa can be
// reupholstered (fabric); it cannot become "glass". A dining table can be
// wood or glass-topped. Deliberately conservative — extend as needed rather
// than allowing nonsensical combinations by default.
const TYPE_FINISH_CATEGORIES = Object.freeze({
  bed_double: ["fabric", "wood"],
  nightstand: ["wood", "metal"],
  wardrobe: ["wood"],
  sofa: ["fabric"],
  coffee_table: ["wood", "glass", "metal"],
  tv_unit: ["wood", "metal"],
  dining_table: ["wood", "glass"],
  dining_chair: ["fabric", "wood", "metal"],
  washer_dryer_unit: ["metal"],
  storage_shelving: ["wood", "metal"],
  dressing_wardrobe: ["wood"],
  desk: ["wood", "metal", "glass"],
  office_chair: ["fabric", "metal"],
  coat_rack: ["metal", "wood"],
  bathroom_vanity: ["wood", "metal"],
  rug: ["fabric"],
  wall_art: ["wood", "metal"],
  mirror: ["wood", "metal"],
  floor_lamp: ["metal", "wood"],
  table_lamp: ["metal", "wood"],
  potted_plant: ["wood"],
  shower: ["metal"],
  bathtub: ["metal"],
  sink: ["metal"],
  towel: ["fabric"],
  clothing_rack: ["metal", "wood"],
  shoe_rack: ["wood", "metal"],
});

// --- Placement mode ---------------------------------------------------------
// Most furniture stands on the floor against a wall (the default). A few
// decor types need different placement logic, handled in
// furniture-placement.mjs:
//  - "floor_center": placed at the room's centroid, not against any wall,
//    and does not consume a wall edge (e.g. a rug).
//  - "wall_mounted": placed like a normal wall item in X/Y, but rendered at
//    `mount_height_mm` above the floor instead of sitting on it (e.g. art,
//    a mirror).
// Anything not listed here is "floor" (the existing default behaviour).
export const PLACEMENT_MODE = Object.freeze({
  rug: "floor_center",
  towel: "floor_center",
  wall_art: "wall_mounted",
  mirror: "wall_mounted",
});

export const MOUNT_HEIGHT_MM = Object.freeze({
  wall_art: 1500,
  mirror: 1400,
});

export function getPlacementMode(type) {
  return PLACEMENT_MODE[type] || "floor";
}

export function getFinish(name) {
  const item = FINISHES_BY_NAME.get(name);
  if (!item) throw new Error(`No furniture finish named "${name}".`);
  return item;
}

export function listFinishesForType(type) {
  const categories = TYPE_FINISH_CATEGORIES[type];
  if (!categories) throw new Error(`No finish categories declared for furniture type "${type}".`);
  return FURNITURE_FINISHES.filter((item) => categories.includes(item.category));
}

export function isFinishCompatible(type, finishName) {
  const categories = TYPE_FINISH_CATEGORIES[type];
  if (!categories) throw new Error(`No finish categories declared for furniture type "${type}".`);
  return categories.includes(getFinish(finishName).category);
}
