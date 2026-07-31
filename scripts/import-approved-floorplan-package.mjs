import { createHash, randomUUID } from "node:crypto";
import { lstat, mkdir, readFile, readdir, rename, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import sharp from "sharp";

const PACKAGE_SCHEMA = "dmh-floorplan-approved-package-v3";
const PLAN_SCHEMA = "dmh-floorplan-approved-canonical-v1";
const REQUIRED_PAYLOADS = ["canonical-plan.json", "floorplan.jpg", "geometry-guide.png", "massing.json"];
const EXPECTED_FILES = new Set([...REQUIRED_PAYLOADS, "manifest.json"]);
const FILE_LIMITS = {
  "canonical-plan.json": 8 * 1024 * 1024,
  "floorplan.jpg": 3 * 1024 * 1024,
  "geometry-guide.png": 8 * 1024 * 1024,
  "massing.json": 8 * 1024 * 1024,
  "manifest.json": 256 * 1024,
};
const DEFAULT_TARGET = resolve(dirname(fileURLToPath(import.meta.url)), "../src/lib/generator/fixtures/approved");

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])]));
}

export function approvedGeometryHash(document) {
  return createHash("sha256").update(JSON.stringify(canonicalValue({
    building: document.building,
    floors: document.floors,
    shared_stair_core: document.shared_stair_core,
  }))).digest("hex");
}

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const finitePoint = (point) => Array.isArray(point) && point.length === 2 && point.every(Number.isFinite);
const safePlanId = (value) => typeof value === "string" && /^plan-[a-f0-9]{16}$/.test(value);

function parseJson(bytes, label) {
  try { return JSON.parse(bytes.toString("utf8")); }
  catch { throw new Error(`${label} is not valid UTF-8 JSON.`); }
}

function assertGeometry(document) {
  const building = document.building;
  if (!building || building.coordinate_unit !== "mm") throw new Error("Canonical plan must use millimetres.");
  if (!["1_storey", "1_5_storey", "2_storey"].includes(building.storey_type)) throw new Error("Unsupported storey type.");
  for (const key of ["footprint_width_mm", "footprint_depth_mm"]) {
    if (!Number.isFinite(building[key]) || building[key] <= 0) throw new Error(`Invalid ${key}.`);
  }
  const expectedFloors = building.storey_type === "1_storey" ? 1 : 2;
  if (!Array.isArray(document.floors) || document.floors.length !== expectedFloors) throw new Error("Floor count does not match storey type.");
  for (const floor of document.floors) {
    if (!Array.isArray(floor.footprint) || floor.footprint.length < 3 || !floor.footprint.every(finitePoint)) throw new Error("Invalid floor footprint.");
    if (!Array.isArray(floor.rooms) || !floor.rooms.length) throw new Error("Floor has no rooms.");
    for (const room of floor.rooms) {
      if (!room.id || !room.name || !Array.isArray(room.polygon) || room.polygon.length < 3 || !room.polygon.every(finitePoint)) throw new Error("Invalid room geometry.");
      if (!Number.isFinite(room.area_m2) || room.area_m2 <= 0) throw new Error("Invalid room area.");
    }
    const wallIds = new Set();
    for (const wall of floor.walls || []) {
      if (!wall.id || wallIds.has(wall.id) || !finitePoint(wall.start) || !finitePoint(wall.end) || !Number.isFinite(wall.thickness) || wall.thickness <= 0) throw new Error("Invalid wall geometry.");
      wallIds.add(wall.id);
    }
    for (const opening of floor.openings || []) {
      if (!wallIds.has(opening.wall_id) || !Number.isFinite(opening.width) || opening.width <= 0) throw new Error("Opening is not attached to a valid wall.");
    }
  }
  if (expectedFloors === 2) {
    const stair = document.shared_stair_core;
    if (!stair || stair.direction !== "up" || !Number.isFinite(stair.usable_width_mm) || stair.usable_width_mm < 900) throw new Error("Valid shared stair core is required.");
    if (!document.floors.every((floor) => floor.stair_core_id === stair.id)) throw new Error("Stair core is not shared by both floors.");
  }
}

function assertCommercial(document, manifest) {
  if (document.status !== "approved") throw new Error("Canonical geometry is not approved.");
  if (document.wordpress_eligible !== true || manifest.wordpress_eligible !== true) throw new Error("Package is not WordPress eligible.");
  for (const rights of [document.rights, manifest.rights]) {
    if (!rights || rights.usage_scope !== "commercial_generator" || rights.wordpress_eligible !== true) throw new Error("Commercial rights decision is missing.");
    if (!["commercially_cleared", "generic_layout_reconstructed"].includes(rights.decision)) throw new Error("Commercial rights decision is invalid.");
  }
  if (document.rights.decision === "generic_layout_reconstructed") {
    if (document.rights.commercial_approval_attested !== true || document.provenance?.creation_mode !== "generic_layout_reconstruction") throw new Error("Reconstruction attestation is incomplete.");
  }
}

async function checkedFiles(packageDirectory) {
  const root = resolve(packageDirectory);
  const rootStat = await lstat(root);
  if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) throw new Error("Package path must be a real directory.");
  const names = (await readdir(root)).sort();
  const unexpected = names.filter((name) => !EXPECTED_FILES.has(name));
  const missing = [...EXPECTED_FILES].filter((name) => !names.includes(name));
  if (unexpected.length) throw new Error(`Unexpected package file: ${unexpected.join(", ")}.`);
  if (missing.length) throw new Error(`Missing package file: ${missing.join(", ")}.`);
  const files = {};
  for (const name of names) {
    const path = join(root, name);
    const stat = await lstat(path);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Unsafe package entry: ${name}.`);
    if (stat.size < 1 || stat.size > FILE_LIMITS[name]) throw new Error(`Invalid file size: ${name}.`);
    files[name] = await readFile(path);
  }
  return files;
}

export async function inspectApprovedPackage(packageDirectory) {
  const files = await checkedFiles(packageDirectory);
  const manifest = parseJson(files["manifest.json"], "manifest.json");
  if (manifest.schema !== PACKAGE_SCHEMA) throw new Error(`Only ${PACKAGE_SCHEMA} is accepted.`);
  if (manifest.source_assets_included !== false) throw new Error("Source assets must not be included.");
  if (!safePlanId(manifest.plan_id)) throw new Error("Invalid public plan ID.");
  const listed = Object.keys(manifest.files || {}).sort();
  if (JSON.stringify(listed) !== JSON.stringify([...REQUIRED_PAYLOADS].sort())) throw new Error("Manifest payload list is invalid.");
  for (const name of REQUIRED_PAYLOADS) {
    const expected = manifest.files[name];
    if (!expected || expected.bytes !== files[name].length || expected.sha256 !== sha256(files[name])) throw new Error(`Checksum or size mismatch: ${name}.`);
  }
  const document = parseJson(files["canonical-plan.json"], "canonical-plan.json");
  for (const forbidden of ["source_annotation", "source_annotation_sha256", "source_reference_id"]) {
    if (forbidden in document) throw new Error(`Source field is forbidden: ${forbidden}.`);
  }
  if (document.schema !== PLAN_SCHEMA || document.provenance?.source_assets_included !== false) throw new Error("Canonical plan is not sanitized.");
  assertGeometry(document);
  assertCommercial(document, manifest);
  const geometryHash = approvedGeometryHash(document);
  if (document.geometry_hash !== geometryHash || manifest.geometry_hash !== geometryHash) throw new Error("Canonical geometry hash mismatch.");
  if (document.plan_id !== manifest.plan_id || document.plan_id !== `plan-${geometryHash.slice(0, 16)}`) throw new Error("Plan ID does not match canonical geometry.");
  if (document.revision !== manifest.revision) throw new Error("Revision mismatch.");
  const massing = parseJson(files["massing.json"], "massing.json");
  if (massing.schema !== "dmh-floorplan-massing-metadata-v1" || massing.plan_id !== document.plan_id || massing.geometry_hash !== geometryHash) throw new Error("Massing geometry hash mismatch.");
  const jpeg = await sharp(files["floorplan.jpg"], { failOn: "error" }).metadata();
  if (jpeg.format !== "jpeg") throw new Error("Floorplan artifact is not JPEG.");
  const guide = await sharp(files["geometry-guide.png"], { failOn: "error" }).metadata();
  if (guide.format !== "png" || guide.width !== 1024 || guide.height !== 1024) throw new Error("Geometry guide must be a 1024x1024 PNG.");
  return { document, manifest };
}

async function writeAtomic(path, contents) {
  const temporary = `${path}.${randomUUID()}.tmp`;
  await writeFile(temporary, contents, { flag: "wx" });
  await rename(temporary, path);
}

async function rebuildRegistry(targetRoot) {
  const canonicalFiles = (await readdir(targetRoot)).filter((name) => /^plan-[a-f0-9]{16}\.canonical\.json$/.test(name)).sort();
  const lines = ["/* Generated by import-approved-floorplan-package.mjs. */"];
  canonicalFiles.forEach((name, index) => {
    const base = name.slice(0, -".canonical.json".length);
    lines.push(`import plan${index} from "./${name}" with { type: "json" };`);
    lines.push(`import manifest${index} from "./${base}.manifest.json" with { type: "json" };`);
  });
  lines.push("", "export const APPROVED_FLOORPLAN_RECORDS = [");
  canonicalFiles.forEach((name, index) => lines.push(`  { document: plan${index}, manifest: manifest${index} },`));
  lines.push("];", "");
  await writeAtomic(join(targetRoot, "catalog.generated.mjs"), lines.join("\n"));
}

export async function importApprovedPackage(packageDirectory, targetRoot = DEFAULT_TARGET) {
  const inspected = await inspectApprovedPackage(packageDirectory);
  const root = resolve(targetRoot);
  await mkdir(root, { recursive: true });
  const base = inspected.document.plan_id;
  const canonicalPath = join(root, `${base}.canonical.json`);
  const manifestPath = join(root, `${base}.manifest.json`);
  for (const [path, value] of [[canonicalPath, inspected.document], [manifestPath, inspected.manifest]]) {
    try {
      const existing = JSON.parse(await readFile(path, "utf8"));
      if (JSON.stringify(canonicalValue(existing)) !== JSON.stringify(canonicalValue(value))) throw new Error(`Catalogue entry already exists with different content: ${base}.`);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      await writeAtomic(path, `${JSON.stringify(value, null, 2)}\n`);
    }
  }
  await rebuildRegistry(root);
  return { plan_id: base, geometry_hash: inspected.document.geometry_hash, target: root };
}

async function main() {
  const packageDirectory = process.argv[2];
  if (!packageDirectory) throw new Error("Usage: node scripts/import-approved-floorplan-package.mjs <approved-package-directory>");
  const result = await importApprovedPackage(packageDirectory);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

const invoked = process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url;
if (invoked) main().catch((error) => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
