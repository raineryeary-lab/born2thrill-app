import assert from "node:assert/strict";
import test from "node:test";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { buildBlenderSceneManifest, assertManifestMatchesCanonical } from "../src/lib/generator/blender-scene-manifest.mjs";

const canonical = { geometry_hash: "fixture-hash", building: { coordinate_unit: "mm", footprint_width_mm: 4000, footprint_depth_mm: 3000, floor_height_mm: 2800, roof_form: "gable" }, floors: [{ id: "ground", footprint: [[0,0],[4000,0],[4000,3000],[0,3000]], walls: [{ id: "wall", start: [0,0], end: [4000,0], thickness: 350, wall_type: "exterior" }], openings: [{ id: "window", wall_id: "wall", opening_type: "window", role: "standard", position: 0.5, width: 1200, height_mm: 1200, sill_height_mm: 900, connects: ["outside", "room"] }] }], shared_stair_core: null };

test("manifest copies the canonical hash and rejects stale geometry", () => {
  const manifest = buildBlenderSceneManifest(canonical, { validate: false });
  assert.equal(manifest.source_geometry_hash, canonical.geometry_hash);
  assert.equal(manifest.wordpress_eligible, false);
  assert.doesNotThrow(() => assertManifestMatchesCanonical(manifest, canonical));
  assert.throws(() => assertManifestMatchesCanonical({ ...manifest, source_geometry_hash: "stale" }, canonical), /hash mismatch/);
});

test("manifest includes facade, roof and preserved opening semantics for geometry lock", () => {
  const manifest = buildBlenderSceneManifest(canonical, { validate: false, renderView: "garden", cameraAngleDeg: 35 });
  assert.equal(manifest.facade_analysis.selection.camera_angle_deg, 35);
  assert.match(manifest.presentation_hash, /^[a-f0-9]{64}$/);
  assert.equal(manifest.roof.representation, "deterministic_gable");
  assert.equal(manifest.roof.pitch_deg, 35);
  assert.equal(manifest.floors[0].walls[0].wall_type, "exterior");
  assert.equal(manifest.floors[0].openings[0].role, "standard");
  assert.deepEqual(manifest.floors[0].openings[0].connects, ["outside", "room"]);
});
test("manifest supplies safe vertical defaults for doors", () => {
  const withDoor = structuredClone(canonical);
  withDoor.floors[0].openings.push({ id: "door", wall_id: "wall", opening_type: "door", position: 0.2, width: 880 });
  const door = buildBlenderSceneManifest(withDoor, { validate: false }).floors[0].openings.find((opening) => opening.id === "door");
  assert.equal(door.height_mm, 2100);
  assert.equal(door.sill_height_mm, 0);
});
test("manifest allowlists and records the requested facade view", () => {
  const garden = buildBlenderSceneManifest(canonical, { validate: false, renderView: "garden" });
  assert.equal(garden.render_view, "garden");
  assert.throws(() => buildBlenderSceneManifest(canonical, { validate: false, renderView: "diagonal" }), /Unsupported Blender render view/);
});
test("exporter is fixed-path, manifest-only, and embeds the geometry hash", async () => {
  const script = await import("node:fs/promises").then(({ readFile }) => readFile(new URL("./export-floorplan-blender.py", import.meta.url), "utf8"));
  assert.match(script, /source_geometry_hash/);
  assert.match(script, /scene\["source_geometry_hash"\]/);
  assert.match(script, /render_view/);
  assert.match(script, /opening-void/);
  assert.match(script, /roof-plane/);
  assert.doesNotMatch(script, /roof-placeholder/);
  assert.doesNotMatch(script, /room|infer/i);
});

test("headless Blender writes a non-empty blend and PNG with matching metadata", { timeout: 120000 }, async (t) => {
  const executable = "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe";
  try { await stat(executable); } catch { return t.skip("fixed Blender 5.0 path unavailable"); }
  const directory = await mkdtemp(join(tmpdir(), "zf-blender-v1-"));
  const manifestPath = join(directory, "manifest.json"); const blendPath = join(directory, "scene.blend"); const pngPath = join(directory, "scene.png");
  await writeFile(manifestPath, JSON.stringify(buildBlenderSceneManifest(canonical, { validate: false, renderView: "garden" })));
  const code = await new Promise((resolve, reject) => { const child = spawn(executable, ["--background", "--python", fileURLToPath(new URL("./export-floorplan-blender.py", import.meta.url)), "--", manifestPath, blendPath, pngPath], { windowsHide: true, stdio: "ignore" }); child.once("error", reject); child.once("exit", resolve); });
  assert.equal(code, 0); assert.ok((await stat(blendPath)).size > 0); assert.ok((await stat(pngPath)).size > 0);
  const metadata = JSON.parse(await readFile(`${blendPath}.metadata.json`, "utf8"));
  assert.equal(metadata.source_geometry_hash, canonical.geometry_hash);
  assert.equal(metadata.render_view, "garden");
  assert.match(metadata.presentation_hash, /^[a-f0-9]{64}$/);
  assert.ok(metadata.camera_distance >= metadata.footprint_span * 2.75);
  assert.ok(metadata.camera_focal_length_mm <= 42);
});