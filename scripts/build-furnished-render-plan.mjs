// Build a render plan for the furnished dollhouse proof.
//
// Reads an approved canonical floorplan, runs the EXISTING tested placement
// engine (src/lib/generator/furniture-placement.mjs — unmodified), resolves
// each placement to a real .glb on disk, and writes a single JSON that the
// Blender script consumes.
//
// This is a proof-of-pipeline script. It does not modify the approved
// generator pipeline, the scene manifest, or geometry_hash. Placements are
// presentation data only.
//
// Usage:
//   node scripts/build-furnished-render-plan.mjs <plan.canonical.json> <style> <out.json>

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { planFloorFurniture } from "../src/lib/generator/furniture-placement.mjs";
import { getFurnitureAsset } from "../src/lib/generator/furniture-catalog.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..");
const ASSET_DIRS = ["data/furniture-assets/full-catalog", "data/furniture-assets/test-batch"];
const OVERRIDES_FILE = path.join(REPO, "data/furniture-model-overrides.json");

// External model libraries (CGAxis etc.) take priority over the generated
// .glb catalogue. Real furniture with real materials beats bare text-to-3D
// geometry, and it fills types that were never generated at all.
function loadOverrides() {
  if (!fs.existsSync(OVERRIDES_FILE)) return { models: {}, preserveNativeScale: new Set() };
  const raw = JSON.parse(fs.readFileSync(OVERRIDES_FILE, "utf8"));
  return {
    models: raw.models || {},
    preserveNativeScale: new Set(raw.preserve_native_scale || []),
  };
}

// Dollhouse cutaway wall height. The reference images show walls cut well
// below ceiling so every room stays visible from an elevated camera.
const CUTAWAY_WALL_HEIGHT_MM = 1200;

function resolveMesh(assetId) {
  for (const dir of ASSET_DIRS) {
    const candidate = path.join(REPO, dir, `${assetId}.glb`);
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function main() {
  const [planPath, style = "modern", outPath] = process.argv.slice(2);
  if (!planPath || !outPath) {
    console.error("usage: node scripts/build-furnished-render-plan.mjs <plan.canonical.json> <style> <out.json>");
    process.exit(1);
  }

  const doc = JSON.parse(fs.readFileSync(planPath, "utf8"));
  if (doc.schema !== "dmh-floorplan-approved-canonical-v1") {
    console.error(`unexpected schema: ${doc.schema}`);
    process.exit(1);
  }

  const floors = [];
  const missing = new Map();
  const overrides = loadOverrides();
  let placed = 0;
  let overridden = 0;

  for (const floor of doc.floors) {
    const plan = planFloorFurniture(floor, style);
    const placements = [];

    for (const room of plan.rooms) {
      for (const p of room.placements) {
        const override = overrides.models[p.type];
        const usingOverride = Boolean(override && fs.existsSync(override));
        const mesh = usingOverride ? override : resolveMesh(p.asset_id);
        if (!mesh) {
          missing.set(p.asset_id, (missing.get(p.asset_id) ?? 0) + 1);
          continue;
        }
        const asset = getFurnitureAsset(p.type, style);
        placements.push({
          ...p,
          room_id: room.room_id,
          mesh_path: mesh,
          target_bbox_mm: asset.bounding_box,
          // Library models are authored at true real-world scale, so forcing
          // them into the catalogue bounding box would distort them. Only the
          // unit-normalised Tripo meshes need rescaling.
          preserve_native_scale: usingOverride && overrides.preserveNativeScale.has(p.type),
          source: usingOverride ? "external_library" : "generated",
        });
        placed += 1;
        if (usingOverride) overridden += 1;
      }
    }

    floors.push({
      id: floor.id,
      name: floor.name,
      level: floor.level,
      rooms: floor.rooms.map((r) => ({
        id: r.id,
        name: r.name,
        kind: r.kind,
        polygon_mm: r.polygon,
        area_m2: r.area_m2,
      })),
      walls: (floor.walls || []).map((w) => ({
        id: w.id,
        start_mm: w.start,
        end_mm: w.end,
        thickness_mm: w.thickness,
        wall_type: w.wall_type,
      })),
      // Doors, windows and passages. Without these every wall renders as a
      // solid slab and the floor reads as a maze.
      openings: (floor.openings || []).map((o) => ({
        id: o.id,
        wall_id: o.wall_id,
        opening_type: o.opening_type,
        position: o.position,
        width_mm: o.width,
        height_mm: o.height_mm ?? (o.opening_type === "window" ? 1350 : 2010),
        sill_height_mm: o.sill_height_mm ?? 0,
        traversable: o.traversable,
        // Which spaces the opening joins. Used to decide which way a door
        // leaf swings and which jamb it hinges on.
        connects: o.connects || [],
      })),
      placements,
      unplaced: plan.rooms.flatMap((r) =>
        r.unplaced.map((u) => ({ room_id: r.room_id, ...u }))),
      skipped_rooms: plan.skipped,
    });
  }

  const out = {
    schema: "dmh-furnished-render-plan-proof-v1",
    plan_id: doc.plan_id,
    source_geometry_hash: doc.geometry_hash,
    style,
    cutaway_wall_height_mm: CUTAWAY_WALL_HEIGHT_MM,
    floors,
  };

  fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2));

  console.log(`plan        ${doc.plan_id}  (${doc.building.storey_type})`);
  console.log(`style       ${style}`);
  console.log(`floors      ${floors.length}`);
  console.log(`placed      ${placed} furniture items with a real mesh`);
  console.log(`            ${overridden} from the external library, ${placed - overridden} generated`);
  for (const f of floors) {
    console.log(`  ${f.name}: ${f.rooms.length} rooms, ${f.placements.length} items`);
  }
  if (missing.size) {
    console.log(`\nno mesh on disk (${[...missing.values()].reduce((a, b) => a + b, 0)} skipped):`);
    for (const [id, n] of [...missing].sort()) console.log(`  ${id} x${n}`);
  }
  console.log(`\nwrote ${outPath}`);
}

main();
