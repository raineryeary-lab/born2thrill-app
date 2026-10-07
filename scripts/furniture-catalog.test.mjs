import assert from "node:assert/strict";
import test from "node:test";
import {
  FURNITURE_CATALOG,
  FURNITURE_STYLES,
  FURNITURE_FINISHES,
  getFurnitureAsset,
  listFurnitureTypesForStyle,
  getFinish,
  listFinishesForType,
  isFinishCompatible,
  getPlacementMode,
  MOUNT_HEIGHT_MM,
} from "../src/lib/generator/furniture-catalog.mjs";

test("every catalog entry is explicitly a placeholder with no asset path", () => {
  assert.ok(FURNITURE_CATALOG.length > 0);
  for (const item of FURNITURE_CATALOG) {
    assert.equal(item.status, "placeholder");
    assert.equal(item.asset_path, null);
    assert.equal(item.source, null);
  }
});

test("every furniture type exists for every declared style", () => {
  const types = new Set(FURNITURE_CATALOG.map((item) => item.type));
  for (const style of FURNITURE_STYLES) {
    const availableForStyle = new Set(listFurnitureTypesForStyle(style));
    for (const type of types) assert.ok(availableForStyle.has(type), `${type} missing for style ${style}`);
  }
});

test("getFurnitureAsset returns a positive bounding box and throws for unknown entries", () => {
  const bed = getFurnitureAsset("bed_double", "modern");
  assert.equal(bed.type, "bed_double");
  assert.equal(bed.style, "modern");
  assert.ok(bed.bounding_box.width_mm > 0);
  assert.ok(bed.bounding_box.depth_mm > 0);
  assert.ok(bed.bounding_box.height_mm > 0);
  assert.throws(() => getFurnitureAsset("bed_double", "brutalist"), /No furniture catalog entry/);
  assert.throws(() => getFurnitureAsset("spaceship", "modern"), /No furniture catalog entry/);
});

test("listFurnitureTypesForStyle rejects unsupported styles", () => {
  assert.throws(() => listFurnitureTypesForStyle("brutalist"), /Unsupported furniture style/);
});

test("every furniture type declares at least one compatible finish", () => {
  const types = new Set(FURNITURE_CATALOG.map((item) => item.type));
  for (const type of types) {
    const finishes = listFinishesForType(type);
    assert.ok(finishes.length > 0, `${type} has no compatible finishes`);
  }
});

test("a sofa can be reupholstered in fabric but cannot become glass", () => {
  assert.equal(isFinishCompatible("sofa", "fabric-navy-stripe"), true);
  assert.equal(isFinishCompatible("sofa", "glass-clear"), false);
});

test("a dining table can be wood or glass-topped but not upholstered fabric", () => {
  assert.equal(isFinishCompatible("dining_table", "wood-walnut"), true);
  assert.equal(isFinishCompatible("dining_table", "glass-clear"), true);
  assert.equal(isFinishCompatible("dining_table", "fabric-charcoal"), false);
});

test("getFinish returns Blender-material-ready properties and rejects unknown names", () => {
  const finish = getFinish("metal-brass");
  assert.equal(finish.category, "metal");
  assert.equal(finish.color.length, 3);
  for (const channel of finish.color) assert.ok(channel >= 0 && channel <= 1);
  assert.ok(finish.metallic >= 0 && finish.metallic <= 1);
  assert.ok(finish.roughness >= 0 && finish.roughness <= 1);
  assert.throws(() => getFinish("unobtainium"), /No furniture finish named/);
});

test("striped fabric finishes are flagged so the renderer knows to add a pattern", () => {
  const striped = FURNITURE_FINISHES.filter((item) => item.striped);
  assert.ok(striped.length > 0);
  for (const item of striped) assert.equal(item.category, "fabric");
});

test("isFinishCompatible and listFinishesForType reject furniture types with no declared categories", () => {
  assert.throws(() => listFinishesForType("spaceship"), /No finish categories declared/);
  assert.throws(() => isFinishCompatible("spaceship", "wood-oak"), /No finish categories declared/);
});

test("getPlacementMode defaults to floor and reports rug/wall_art/mirror correctly", () => {
  assert.equal(getPlacementMode("sofa"), "floor");
  assert.equal(getPlacementMode("rug"), "floor_center");
  assert.equal(getPlacementMode("wall_art"), "wall_mounted");
  assert.equal(getPlacementMode("mirror"), "wall_mounted");
});

test("every wall_mounted type has a declared mount height", () => {
  for (const [type, mode] of Object.entries({ wall_art: "wall_mounted", mirror: "wall_mounted" })) {
    assert.equal(getPlacementMode(type), mode);
    assert.ok(MOUNT_HEIGHT_MM[type] > 0);
  }
});

test("every new decor type is present for both styles with a compatible finish", () => {
  for (const type of ["rug", "wall_art", "mirror", "floor_lamp", "table_lamp", "potted_plant"]) {
    for (const style of FURNITURE_STYLES) {
      const asset = getFurnitureAsset(type, style);
      assert.equal(asset.type, type);
    }
    assert.ok(listFinishesForType(type).length > 0);
  }
});
