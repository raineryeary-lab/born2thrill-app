/**
 * Read-only inventory of everything the floorplan suite has produced so far.
 *
 * This module NEVER writes, moves or deletes anything. It only stats and reads
 * files under three roots:
 *
 *   primary      the workbench data dir the rest of the app writes to
 *                (FLOORPLAN_WORKBENCH_DATA_DIR)
 *   secondary    the second, similarly named data dir that currently holds most
 *                of the render output (<repo>/../born2thrill-local-workbench-data)
 *   annotations  the simplifier annotation packages
 *                (<repo>/../floorplan-simplifier/projects)
 *
 * The two data roots really are separate trees on this machine. That split is
 * reported, not repaired: every entry carries the root key it was read from so
 * the overview tab can say plainly where a file lives.
 */
import { readFile, readdir, stat } from "node:fs/promises";
import { isAbsolute, join, relative, resolve } from "node:path";

export const ROOT_KEYS = ["primary", "secondary", "annotations", "deliveries"] as const;
export type RootKey = (typeof ROOT_KEYS)[number];

export type RootInfo = {
  key: RootKey;
  label: string;
  path: string;
  exists: boolean;
};

export type AssetRef = {
  root: RootKey;
  /** Path relative to the root, always with forward slashes. */
  path: string;
  name: string;
  bytes: number;
  modified_at: string;
};

export type PlanSummary = {
  file: string;
  style: string | null;
  schema: string | null;
  plan_id: string | null;
  /** simplifier_annotations_proof | correction_revision_draft | approved_correction_revision | ... */
  source: string | null;
  source_geometry_hash: string | null;
  correction_revision: string | null;
  correction_status: string | null;
  roof_type: string | null;
  floor_count: number;
  room_count: number;
  total_area_m2: number | null;
  furniture_placements: number;
  modified_at: string;
};

export type HandoffSummary = {
  schema: string | null;
  project_id: string | null;
  annotations_source: string | null;
  output_dir: string | null;
  styles_verified: string[];
  styles_unverified: string[];
  excluded: { style: string | null; reason: string | null }[];
  modified_at: string;
};

export type CatalogSummary = {
  schema_version: string | null;
  created_at: string | null;
  plan_family_id: string | null;
  geometry_source: string | null;
  asset_count: number;
  styles: string[];
  modified_at: string;
};

export type RenderSet = {
  name: string;
  root: RootKey;
  path: string;
  modified_at: string;
  handoff: HandoffSummary | null;
  catalog: CatalogSummary | null;
  plans: PlanSummary[];
  /** Beauty renders (exterior/interior PNG/JPG), newest first. */
  images: AssetRef[];
  /** Auxiliary passes: -depth / -edge / -mask. Counted, not thumbnailed. */
  aux_image_count: number;
  blend_count: number;
  log_count: number;
  total_bytes: number;
};

export type RevisionSummary = {
  file: string;
  revision: number | null;
  status: string | null;
  geometry_hash: string | null;
  schema: string | null;
  floor_count: number;
  room_count: number;
  total_area_m2: number | null;
  wall_count: number;
  opening_count: number;
  wordpress_eligible: boolean;
  validation_valid: boolean | null;
  updated_at: string | null;
  modified_at: string;
};

export type FurnitureSummary = {
  file: string;
  floor_id: string | null;
  schema: string | null;
  coordinate_space: string | null;
  symbol_count: number;
  updated_at: string | null;
  modified_at: string;
};

export type ExportSummary = {
  name: string;
  plan_id: string | null;
  revision: number | null;
  geometry_hash: string | null;
  wordpress_eligible: boolean;
  created_at: string | null;
  file_count: number;
  modified_at: string;
};

export type WorkbenchTree = {
  root: RootKey;
  root_path: string;
  path: string;
  modified_at: string;
  render_sets: RenderSet[];
  revisions: RevisionSummary[];
  furniture: FurnitureSummary[];
  exports: ExportSummary[];
  blender_scene_count: number;
  notes: string[];
};

export type AnnotationSummary = {
  root: RootKey;
  path: string;
  house_type: string | null;
  package_status: string | null;
  annotation_schema_version: string | null;
  created_at: string | null;
  updated_at: string | null;
  room_count: number;
  floor_levels: string[];
  element_counts: Record<string, number>;
  symbol_count: number;
  exterior_area_count: number;
  roof_type_modern: string | null;
  roof_type_classic: string | null;
  quality_passed: boolean | null;
  quality_warnings: string[];
  concept_images: AssetRef[];
  has_data_json: boolean;
  has_annotations_json: boolean;
  modified_at: string;
};

export type ProjectEntry = {
  project_id: string;
  latest_activity: string;
  annotation: AnnotationSummary | null;
  trees: WorkbenchTree[];
  /** Derived roll-ups so the client does not have to walk the tree twice. */
  house_type: string | null;
  package_status: string | null;
  render_image_count: number;
  render_set_count: number;
  revision_count: number;
  latest_revision_status: string | null;
  furniture_symbol_count: number;
  furniture_spaces: string[];
  export_count: number;
  styles_verified: string[];
  styles_excluded: string[];
  plan_sources: string[];
  room_count: number | null;
  total_area_m2: number | null;
  codex_ready: boolean;
  readiness: "codex_ready" | "rendered_no_handoff" | "corrected" | "annotated" | "empty";
  is_scratch: boolean;
  thumbnails: AssetRef[];
};

export type DeliveryBundle = {
  name: string;
  modified_at: string;
  /** From selected-catalog.json when present. */
  schema_version: string | null;
  created_at: string | null;
  plan_family_id: string | null;
  asset_count: number;
  styles: string[];
  images: AssetRef[];
  docs: AssetRef[];
  zip: AssetRef | null;
};

export type Inventory = {
  schema: "zf-floorplan-workbench-overview-v1";
  generated_at: string;
  roots: RootInfo[];
  totals: {
    projects: number;
    codex_ready: number;
    with_renders: number;
    with_revisions: number;
    with_furniture: number;
    annotation_only: number;
    empty_folders: number;
    scratch_projects: number;
    render_images: number;
    render_sets: number;
    revisions: number;
    exports: number;
    blend_files: number;
  };
  warnings: string[];
  /** Finished packages handed to Codex, from the repo's own exports/ folder. */
  deliveries: DeliveryBundle[];
  projects: ProjectEntry[];
};

/* ------------------------------------------------------------------ roots */

function repoParent() {
  return resolve(process.cwd(), "..");
}

export function primaryDataRoot() {
  const configured = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  return configured
    ? resolve(configured)
    : join(process.env.LOCALAPPDATA || process.env.TEMP || ".", "Born2Thrill", "floorplan-workbench");
}

export function secondaryDataRoot() {
  // Same convention scripts/build-simplifier-render-plan.py uses for the
  // simplifier: a sibling of the app repo.
  return resolve(repoParent(), "born2thrill-local-workbench-data");
}

export function annotationsRoot() {
  const configured = process.env.FLOORPLAN_SIMPLIFIER_DIR?.trim();
  const base = configured ? resolve(configured) : resolve(repoParent(), "floorplan-simplifier");
  return join(base, "projects");
}

export function rootPaths(): Record<RootKey, string> {
  return {
    primary: primaryDataRoot(),
    secondary: secondaryDataRoot(),
    annotations: annotationsRoot(),
    deliveries: join(process.cwd(), "exports"),
  };
}

export const ROOT_LABELS: Record<RootKey, string> = {
  primary: "primary data root (FLOORPLAN_WORKBENCH_DATA_DIR)",
  secondary: "second data root (Floorplan-tools\\born2thrill-local-workbench-data)",
  annotations: "annotation packages (floorplan-simplifier\\projects)",
  // Finished packages handed to Codex live in the repo, not in a data root —
  // a third place entirely, which is why they looked missing.
  deliveries: "delivered packages (born2thrill-local-workbench\\exports)",
};

/**
 * Resolve a root-relative asset path, refusing anything that escapes the root.
 * Used by the asset route; kept here so both routes share one implementation.
 */
export function resolveAssetPath(rootKey: string, relativePath: string): string | null {
  if (!(ROOT_KEYS as readonly string[]).includes(rootKey)) return null;
  const base = rootPaths()[rootKey as RootKey];
  const cleaned = String(relativePath || "").replace(/\\/g, "/");
  if (!cleaned || cleaned.includes("\0") || isAbsolute(cleaned) || /^[a-zA-Z]:/.test(cleaned)) return null;
  const target = resolve(base, cleaned);
  const rel = relative(base, target);
  if (!rel || rel.startsWith("..") || isAbsolute(rel)) return null;
  return target;
}

/* ------------------------------------------------------------- small utils */

const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".svg", ".webp"]);
const AUX_SUFFIXES = ["-depth", "-edge", "-mask", "-normal"];

function iso(value: number) {
  return new Date(value).toISOString();
}

function newest(...values: (string | null | undefined)[]) {
  return values.filter((value): value is string => Boolean(value)).sort().at(-1) || "";
}

function toForwardSlashes(value: string) {
  return value.replace(/\\/g, "/");
}

function extensionOf(name: string) {
  const dot = name.lastIndexOf(".");
  return dot < 0 ? "" : name.slice(dot).toLowerCase();
}

function isAuxImage(name: string) {
  const base = name.replace(/\.[^.]+$/, "");
  return AUX_SUFFIXES.some((suffix) => base.endsWith(suffix));
}

async function safeReaddir(directory: string) {
  try {
    return await readdir(directory, { withFileTypes: true });
  } catch {
    return [];
  }
}

async function safeStat(path: string) {
  try {
    return await stat(path);
  } catch {
    return null;
  }
}

/**
 * Parsed JSON keyed by path + mtime. The inventory re-reads a few hundred small
 * files per request; without this the tab feels sluggish on a cold page load.
 */
const jsonCache = new Map<string, { mtimeMs: number; value: unknown }>();

async function readJson<T = Record<string, unknown>>(path: string): Promise<{ value: T; modified_at: string; bytes: number } | null> {
  const info = await safeStat(path);
  if (!info || !info.isFile()) return null;
  const cached = jsonCache.get(path);
  if (cached && cached.mtimeMs === info.mtimeMs) {
    return { value: cached.value as T, modified_at: iso(info.mtimeMs), bytes: info.size };
  }
  try {
    const value = JSON.parse(await readFile(path, "utf8"));
    jsonCache.set(path, { mtimeMs: info.mtimeMs, value });
    return { value: value as T, modified_at: iso(info.mtimeMs), bytes: info.size };
  } catch {
    return null;
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.length ? value : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function round1(value: number) {
  return Math.round(value * 10) / 10;
}

/* ------------------------------------------------------------- plan / render */

function summarizePlan(file: string, value: Record<string, unknown>, modifiedAt: string): PlanSummary {
  const floors = asArray(value.floors).map(asRecord);
  let rooms = 0;
  let area = 0;
  let placements = 0;
  let sawArea = false;
  for (const floor of floors) {
    const floorRooms = asArray(floor.rooms).map(asRecord);
    rooms += floorRooms.length;
    placements += asArray(floor.placements).length;
    for (const room of floorRooms) {
      const value = asNumber(room.area_m2);
      if (value !== null) {
        area += value;
        sawArea = true;
      }
    }
  }
  const styleFromName = /plan-([a-z0-9_]+)\.json$/i.exec(file)?.[1] || null;
  return {
    file,
    style: asString(value.style) || styleFromName,
    schema: asString(value.schema),
    plan_id: asString(value.plan_id),
    source: asString(value.source),
    source_geometry_hash: asString(value.source_geometry_hash),
    correction_revision: asString(value.correction_revision),
    correction_status: asString(value.correction_status),
    roof_type: asString(value.roof_type),
    floor_count: floors.length,
    room_count: rooms,
    total_area_m2: sawArea ? round1(area) : null,
    furniture_placements: placements,
    modified_at: modifiedAt,
  };
}

function summarizeHandoff(value: Record<string, unknown>, modifiedAt: string): HandoffSummary {
  const styles = asRecord(value.styles);
  const verified: string[] = [];
  const unverified: string[] = [];
  for (const [style, raw] of Object.entries(styles)) {
    if (asRecord(raw).verified === true) verified.push(style);
    else unverified.push(style);
  }
  const excluded = asArray(value.excluded).map((entry) => {
    if (typeof entry === "string") return { style: entry, reason: null };
    const record = asRecord(entry);
    return {
      style: asString(record.style) || asString(record.name),
      reason: asString(record.reason) || asString(record.why) || asString(record.error),
    };
  });
  return {
    schema: asString(value.schema),
    project_id: asString(value.project_id),
    annotations_source: asString(value.annotations_source),
    output_dir: asString(value.output_dir_for_images_and_catalog),
    styles_verified: verified.sort(),
    styles_unverified: unverified.sort(),
    excluded,
    modified_at: modifiedAt,
  };
}

function summarizeCatalog(value: Record<string, unknown>, modifiedAt: string): CatalogSummary {
  const assets = asArray(value.assets).map(asRecord);
  const styles = [...new Set(assets.map((asset) => asString(asset.style)).filter((style): style is string => Boolean(style)))];
  return {
    schema_version: asString(value.schema_version),
    created_at: asString(value.created_at),
    plan_family_id: asString(value.plan_family_id),
    geometry_source: asString(value.geometry_source),
    asset_count: assets.length,
    styles: styles.sort(),
    modified_at: modifiedAt,
  };
}

async function scanRenderSet(root: RootKey, rootPath: string, relativeDir: string, name: string): Promise<RenderSet> {
  const absolute = join(rootPath, relativeDir);
  const entries = await safeReaddir(absolute);
  const images: AssetRef[] = [];
  const plans: PlanSummary[] = [];
  let auxImages = 0;
  let blends = 0;
  let logs = 0;
  let bytes = 0;
  let modified = "";
  let handoff: HandoffSummary | null = null;
  let catalog: CatalogSummary | null = null;

  for (const entry of entries) {
    if (!entry.isFile()) continue;
    const file = entry.name;
    const absoluteFile = join(absolute, file);
    const info = await safeStat(absoluteFile);
    if (!info) continue;
    bytes += info.size;
    modified = newest(modified, iso(info.mtimeMs));
    const extension = extensionOf(file);
    if (IMAGE_EXTENSIONS.has(extension)) {
      if (isAuxImage(file)) auxImages += 1;
      else {
        images.push({
          root,
          path: toForwardSlashes(join(relativeDir, file)),
          name: file,
          bytes: info.size,
          modified_at: iso(info.mtimeMs),
        });
      }
      continue;
    }
    if (extension === ".blend") blends += 1;
    else if (extension === ".log") logs += 1;
    else if (file === "handoff.json") {
      const parsed = await readJson(absoluteFile);
      if (parsed) handoff = summarizeHandoff(asRecord(parsed.value), parsed.modified_at);
    } else if (file === "catalog.json") {
      const parsed = await readJson(absoluteFile);
      if (parsed) catalog = summarizeCatalog(asRecord(parsed.value), parsed.modified_at);
    } else if (/^plan-.+\.json$/i.test(file)) {
      const parsed = await readJson(absoluteFile);
      if (parsed) plans.push(summarizePlan(file, asRecord(parsed.value), parsed.modified_at));
    }
  }

  images.sort((left, right) => left.name.localeCompare(right.name));
  plans.sort((left, right) => left.file.localeCompare(right.file));
  return {
    name,
    root,
    path: toForwardSlashes(relativeDir),
    modified_at: modified,
    handoff,
    catalog,
    plans,
    images,
    aux_image_count: auxImages,
    blend_count: blends,
    log_count: logs,
    total_bytes: bytes,
  };
}

/* --------------------------------------------------------- revisions etc. */

function summarizeRevision(file: string, value: Record<string, unknown>, modifiedAt: string): RevisionSummary {
  const floors = asArray(value.floors).map(asRecord);
  let rooms = 0;
  let walls = 0;
  let openings = 0;
  let area = 0;
  let sawArea = false;
  for (const floor of floors) {
    const floorRooms = asArray(floor.rooms).map(asRecord);
    rooms += floorRooms.length;
    walls += asArray(floor.walls).length;
    openings += asArray(floor.openings).length;
    for (const room of floorRooms) {
      const roomArea = asNumber(room.area_m2);
      if (roomArea !== null) {
        area += roomArea;
        sawArea = true;
      }
    }
  }
  const validation = asRecord(value.validation);
  return {
    file,
    revision: asNumber(value.revision),
    status: asString(value.status),
    geometry_hash: asString(value.geometry_hash),
    schema: asString(value.schema),
    floor_count: floors.length,
    room_count: rooms,
    total_area_m2: sawArea ? round1(area) : null,
    wall_count: walls,
    opening_count: openings,
    wordpress_eligible: value.wordpress_eligible === true,
    validation_valid: typeof validation.valid === "boolean" ? validation.valid : null,
    updated_at: asString(value.updated_at) || asString(value.created_at),
    modified_at: modifiedAt,
  };
}

async function scanRevisions(root: RootKey, rootPath: string, relativeDir: string) {
  const entries = await safeReaddir(join(rootPath, relativeDir));
  const revisions: RevisionSummary[] = [];
  for (const entry of entries) {
    if (!entry.isFile() || !/^revision-\d{4}\.json$/.test(entry.name)) continue;
    const parsed = await readJson(join(rootPath, relativeDir, entry.name));
    if (parsed) revisions.push(summarizeRevision(entry.name, asRecord(parsed.value), parsed.modified_at));
  }
  revisions.sort((left, right) => (left.revision || 0) - (right.revision || 0));
  return revisions;
}

async function scanFurniture(rootPath: string, relativeDir: string) {
  const entries = await safeReaddir(join(rootPath, relativeDir));
  const furniture: FurnitureSummary[] = [];
  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith(".json")) continue;
    const parsed = await readJson(join(rootPath, relativeDir, entry.name));
    if (!parsed) continue;
    const value = asRecord(parsed.value);
    furniture.push({
      file: entry.name,
      floor_id: asString(value.floor_id),
      schema: asString(value.schema),
      coordinate_space: asString(value.coordinate_space),
      symbol_count: asArray(value.symbols).length,
      updated_at: asString(value.updated_at),
      modified_at: parsed.modified_at,
    });
  }
  furniture.sort((left, right) => left.file.localeCompare(right.file));
  return furniture;
}

async function scanExports(rootPath: string, relativeDir: string) {
  const entries = await safeReaddir(join(rootPath, relativeDir));
  const exports: ExportSummary[] = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const directory = join(rootPath, relativeDir, entry.name);
    const files = await safeReaddir(directory);
    const info = await safeStat(directory);
    const manifest = await readJson(join(directory, "manifest.json"));
    const value = asRecord(manifest?.value);
    exports.push({
      name: entry.name,
      plan_id: asString(value.plan_id),
      revision: asNumber(value.revision),
      geometry_hash: asString(value.geometry_hash),
      wordpress_eligible: value.wordpress_eligible === true,
      created_at: asString(value.created_at),
      file_count: files.filter((file) => file.isFile()).length,
      modified_at: manifest?.modified_at || (info ? iso(info.mtimeMs) : ""),
    });
  }
  exports.sort((left, right) => left.name.localeCompare(right.name));
  return exports;
}

async function countBlenderScenes(rootPath: string, relativeDir: string) {
  const hashes = await safeReaddir(join(rootPath, relativeDir));
  let count = 0;
  for (const hash of hashes) {
    if (!hash.isDirectory()) continue;
    const files = await safeReaddir(join(rootPath, relativeDir, hash.name));
    count += files.filter((file) => file.isFile() && file.name.endsWith(".png")).length;
  }
  return count;
}

async function scanWorkbenchTree(root: RootKey, rootPath: string, projectId: string): Promise<WorkbenchTree | null> {
  const relativeProject = toForwardSlashes(join("corrections", projectId));
  const info = await safeStat(join(rootPath, relativeProject));
  if (!info || !info.isDirectory()) return null;
  const notes: string[] = [];
  const children = await safeReaddir(join(rootPath, relativeProject));
  const childNames = new Set(children.filter((child) => child.isDirectory()).map((child) => child.name));

  const renderSets: RenderSet[] = [];
  if (childNames.has("renders")) {
    const renderDirs = await safeReaddir(join(rootPath, relativeProject, "renders"));
    for (const renderDir of renderDirs) {
      if (!renderDir.isDirectory()) continue;
      renderSets.push(await scanRenderSet(root, rootPath, join(relativeProject, "renders", renderDir.name), renderDir.name));
    }
  }
  renderSets.sort((left, right) => right.modified_at.localeCompare(left.modified_at));

  const revisions = childNames.has("revisions") ? await scanRevisions(root, rootPath, join(relativeProject, "revisions")) : [];
  const furniture = childNames.has("furniture") ? await scanFurniture(rootPath, join(relativeProject, "furniture")) : [];
  const exports = childNames.has("exports") ? await scanExports(rootPath, join(relativeProject, "exports")) : [];
  const blenderScenes = childNames.has("blender") ? await countBlenderScenes(rootPath, join(relativeProject, "blender")) : 0;

  for (const child of childNames) {
    if (child.startsWith("furniture-archive")) notes.push(`archived furniture folder ${child} (not counted)`);
  }

  const modified = newest(
    iso(info.mtimeMs),
    ...renderSets.map((set) => set.modified_at),
    ...revisions.map((revision) => revision.modified_at),
    ...furniture.map((entry) => entry.modified_at),
    ...exports.map((entry) => entry.modified_at),
  );

  return {
    root,
    root_path: rootPath,
    path: relativeProject,
    modified_at: modified,
    render_sets: renderSets,
    revisions,
    furniture,
    exports,
    blender_scene_count: blenderScenes,
    notes,
  };
}

/* -------------------------------------------------------------- annotations */

async function scanAnnotationPackage(rootPath: string, projectId: string): Promise<AnnotationSummary | null> {
  const directory = join(rootPath, projectId);
  const info = await safeStat(directory);
  if (!info || !info.isDirectory()) return null;
  const entries = await safeReaddir(directory);
  const files = entries.filter((entry) => entry.isFile());

  const data = await readJson(join(directory, "data.json"));
  const annotations = await readJson(join(directory, "annotations.json"));
  const dataValue = asRecord(data?.value);
  const annotationValue = asRecord(annotations?.value);

  const roomEntries = asArray(annotationValue.annotations).map(asRecord);
  const floorLevels = [...new Set(roomEntries.map((room) => asString(room.floor_level)).filter((level): level is string => Boolean(level)))];
  const elementCounts: Record<string, number> = {};
  for (const element of asArray(annotationValue.elements).map(asRecord)) {
    const type = asString(element.type) || "unknown";
    elementCounts[type] = (elementCounts[type] || 0) + 1;
  }

  const quality = asRecord(dataValue.quality_checks ?? annotationValue.quality_checks);
  const conceptImages: AssetRef[] = [];
  let modified = iso(info.mtimeMs);
  for (const file of files) {
    const fileInfo = await safeStat(join(directory, file.name));
    if (!fileInfo) continue;
    modified = newest(modified, iso(fileInfo.mtimeMs));
    const extension = extensionOf(file.name);
    if ((extension === ".png" || extension === ".svg") && /concept/i.test(file.name)) {
      conceptImages.push({
        root: "annotations",
        path: toForwardSlashes(join(projectId, file.name)),
        name: file.name,
        bytes: fileInfo.size,
        modified_at: iso(fileInfo.mtimeMs),
      });
    }
  }
  // PNG first so the card thumbnails a raster when one exists.
  conceptImages.sort((left, right) => {
    const byType = Number(extensionOf(left.name) === ".svg") - Number(extensionOf(right.name) === ".svg");
    return byType || left.name.localeCompare(right.name);
  });

  return {
    root: "annotations",
    path: projectId,
    house_type: asString(dataValue.house_type),
    package_status: asString(dataValue.package_status) || asString(annotationValue.package_status),
    annotation_schema_version: asString(dataValue.annotation_schema_version) || asString(annotationValue.schema_version),
    created_at: asString(dataValue.created_at),
    updated_at: asString(dataValue.annotation_updated_at) || asString(annotationValue.updated_at),
    room_count: roomEntries.length,
    floor_levels: floorLevels,
    element_counts: elementCounts,
    symbol_count: asArray(annotationValue.symbols).length,
    exterior_area_count: asArray(annotationValue.exterior_areas).length,
    roof_type_modern: asString(annotationValue.roof_type_modern),
    roof_type_classic: asString(annotationValue.roof_type_classic),
    quality_passed: typeof quality.passed === "boolean" ? quality.passed : null,
    quality_warnings: asArray(quality.warnings).filter((warning): warning is string => typeof warning === "string"),
    concept_images: conceptImages,
    has_data_json: Boolean(data),
    has_annotations_json: Boolean(annotations),
    modified_at: modified,
  };
}

/* ------------------------------------------------------------------- build */

function derive(entry: {
  projectId: string;
  annotation: AnnotationSummary | null;
  trees: WorkbenchTree[];
}): ProjectEntry {
  const { projectId, annotation, trees } = entry;
  const renderSets = trees.flatMap((tree) => tree.render_sets);
  const revisions = trees.flatMap((tree) => tree.revisions);
  const furniture = trees.flatMap((tree) => tree.furniture);
  const exports = trees.flatMap((tree) => tree.exports);
  const plans = renderSets.flatMap((set) => set.plans);
  const handoffs = renderSets.map((set) => set.handoff).filter((handoff): handoff is HandoffSummary => Boolean(handoff));

  const stylesVerified = [...new Set(handoffs.flatMap((handoff) => handoff.styles_verified))].sort();
  const stylesExcluded = [...new Set(handoffs.flatMap((handoff) => handoff.excluded.map((item) => item.style || "unnamed")))].sort();
  const renderImageCount = renderSets.reduce((total, set) => total + set.images.length, 0);

  // Newest by file mtime, not by array order: the same project can carry two
  // independent revision histories, one per data root, and the higher revision
  // number is not necessarily the more recent edit.
  const latestRevision = [...revisions].sort((left, right) => left.modified_at.localeCompare(right.modified_at)).at(-1) || null;
  const planWithArea = plans.find((plan) => plan.total_area_m2 !== null) || null;
  const revisionWithArea = [...revisions].reverse().find((revision) => revision.total_area_m2 !== null) || null;

  const codexReady = handoffs.some((handoff) => handoff.styles_verified.length > 0);
  // A project folder can exist with nothing in it at all — those are shells,
  // not annotated packages, and saying "annotated" about them would be a lie.
  const hasAnnotationFiles = Boolean(annotation && (annotation.has_annotations_json || annotation.has_data_json));
  const readiness: ProjectEntry["readiness"] = codexReady
    ? "codex_ready"
    : renderImageCount > 0
      ? "rendered_no_handoff"
      : revisions.length > 0 || furniture.length > 0 || exports.length > 0
        ? "corrected"
        : hasAnnotationFiles
          ? "annotated"
          : "empty";

  const thumbnails: AssetRef[] = [];
  // Finished renders first. Card thumbnails were taken in render-set order,
  // which put the grey `go-baseline` scaffolding on the card and hid Codex's
  // actual delivered images behind "Show details" — the product looked missing
  // (Rainer, 2026-08-17: "all of the renders from codex are missing").
  // A set carrying a catalog.json is a delivered set; baselines are inputs.
  const deliveredFirst = [
    ...renderSets.filter((set) => set.catalog),
    ...renderSets.filter((set) => !set.catalog),
  ];
  for (const set of deliveredFirst) {
    for (const image of set.images) {
      if (thumbnails.length >= 4) break;
      if (extensionOf(image.name) === ".svg") continue;
      thumbnails.push(image);
    }
  }
  if (annotation) {
    for (const image of annotation.concept_images) {
      if (thumbnails.length >= 6) break;
      thumbnails.push(image);
    }
  }

  const latestActivity = newest(
    annotation?.modified_at,
    ...trees.map((tree) => tree.modified_at),
  );

  return {
    project_id: projectId,
    latest_activity: latestActivity,
    annotation,
    trees,
    house_type: annotation?.house_type || null,
    package_status: annotation?.package_status || null,
    render_image_count: renderImageCount,
    render_set_count: renderSets.length,
    revision_count: revisions.length,
    latest_revision_status: latestRevision?.status || null,
    furniture_symbol_count: furniture.reduce((total, item) => total + item.symbol_count, 0),
    furniture_spaces: [...new Set(furniture.map((item) => item.coordinate_space).filter((space): space is string => Boolean(space)))],
    export_count: exports.length,
    styles_verified: stylesVerified,
    styles_excluded: stylesExcluded,
    plan_sources: [...new Set(plans.map((plan) => plan.source).filter((source): source is string => Boolean(source)))].sort(),
    room_count: planWithArea?.room_count ?? revisionWithArea?.room_count ?? annotation?.room_count ?? null,
    total_area_m2: planWithArea?.total_area_m2 ?? revisionWithArea?.total_area_m2 ?? null,
    codex_ready: codexReady,
    readiness,
    is_scratch: /^test-/.test(projectId),
    thumbnails,
  };
}

async function scanDeliveries(root: string): Promise<DeliveryBundle[]> {
  const bundles: DeliveryBundle[] = [];
  const zips = new Map<string, AssetRef>();
  const entries = await safeReaddir(root);
  for (const entry of entries) {
    if (entry.isFile() && entry.name.toLowerCase().endsWith(".zip")) {
      const info = await safeStat(join(root, entry.name));
      if (info) {
        zips.set(entry.name.replace(/\.zip$/i, ""), {
          root: "deliveries", path: entry.name, name: entry.name,
          bytes: info.size, modified_at: info.mtime.toISOString(),
        });
      }
    }
  }
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const dir = join(root, entry.name);
    const images: AssetRef[] = [];
    const docs: AssetRef[] = [];
    let catalog: Record<string, unknown> | null = null;
    for (const file of await safeReaddir(dir)) {
      if (!file.isFile()) continue;
      const info = await safeStat(join(dir, file.name));
      if (!info) continue;
      const ref: AssetRef = {
        root: "deliveries",
        path: `${entry.name}/${file.name}`,
        name: file.name,
        bytes: info.size,
        modified_at: info.mtime.toISOString(),
      };
      const extension = extensionOf(file.name);
      if (extension === ".png" || extension === ".jpg" || extension === ".jpeg" || extension === ".webp") {
        images.push(ref);
      } else {
        docs.push(ref);
        if (file.name === "selected-catalog.json") {
          catalog = (await readJson(join(dir, file.name)))?.value ?? null;
        }
      }
    }
    if (!images.length && !docs.length) continue;
    const assets = Array.isArray(catalog?.assets) ? (catalog!.assets as Record<string, unknown>[]) : [];
    const info = await safeStat(dir);
    bundles.push({
      name: entry.name,
      modified_at: info ? info.mtime.toISOString() : "",
      schema_version: (catalog?.schema_version as string) ?? null,
      created_at: (catalog?.created_at as string) ?? null,
      plan_family_id: (catalog?.plan_family_id as string) ?? null,
      asset_count: assets.length,
      styles: [...new Set(assets.map((asset) => String(asset.style ?? "")).filter(Boolean))],
      images: images.sort((a, b) => a.name.localeCompare(b.name)),
      docs,
      zip: zips.get(entry.name) ?? null,
    });
  }
  return bundles.sort((a, b) => b.modified_at.localeCompare(a.modified_at));
}


export async function buildInventory(): Promise<Inventory> {
  const paths = rootPaths();
  const warnings: string[] = [];
  const roots: RootInfo[] = [];
  for (const key of ROOT_KEYS) {
    const info = await safeStat(paths[key]);
    roots.push({ key, label: ROOT_LABELS[key], path: paths[key], exists: Boolean(info?.isDirectory()) });
  }

  const projectIds = new Set<string>();
  const correctionRoots: { key: RootKey; path: string }[] = [];
  for (const key of ["primary", "secondary"] as const) {
    const root = roots.find((candidate) => candidate.key === key);
    if (!root?.exists) {
      warnings.push(`${ROOT_LABELS[key]} not found at ${paths[key]}.`);
      continue;
    }
    correctionRoots.push({ key, path: paths[key] });
    for (const entry of await safeReaddir(join(paths[key], "corrections"))) {
      if (entry.isDirectory()) projectIds.add(entry.name);
    }
  }
  if (paths.primary === paths.secondary) {
    warnings.push("Both data roots resolve to the same folder; entries are reported once.");
  } else if (correctionRoots.length === 2) {
    warnings.push(
      `Two separate data roots are in use: ${paths.primary} (written by the workbench UI) and ${paths.secondary} (holds the render output). Each entry below names the tree it came from.`,
    );
  }

  const annotationsExist = roots.find((root) => root.key === "annotations")?.exists;
  if (!annotationsExist) warnings.push(`Annotation packages not found at ${paths.annotations}.`);
  const annotationIds = new Set<string>();
  if (annotationsExist) {
    for (const entry of await safeReaddir(paths.annotations)) {
      if (entry.isDirectory()) {
        annotationIds.add(entry.name);
        projectIds.add(entry.name);
      }
    }
  }

  const projects: ProjectEntry[] = [];
  for (const projectId of projectIds) {
    const trees: WorkbenchTree[] = [];
    for (const root of correctionRoots) {
      if (root.key === "secondary" && paths.primary === paths.secondary) continue;
      const tree = await scanWorkbenchTree(root.key, root.path, projectId);
      if (tree) trees.push(tree);
    }
    const annotation = annotationIds.has(projectId) ? await scanAnnotationPackage(paths.annotations, projectId) : null;
    projects.push(derive({ projectId, annotation, trees }));
  }

  projects.sort((left, right) => right.latest_activity.localeCompare(left.latest_activity) || left.project_id.localeCompare(right.project_id));

  const totals = {
    projects: projects.length,
    codex_ready: projects.filter((project) => project.codex_ready).length,
    with_renders: projects.filter((project) => project.render_image_count > 0).length,
    with_revisions: projects.filter((project) => project.revision_count > 0).length,
    with_furniture: projects.filter((project) => project.furniture_symbol_count > 0).length,
    annotation_only: projects.filter((project) => project.readiness === "annotated").length,
    empty_folders: projects.filter((project) => project.readiness === "empty").length,
    scratch_projects: projects.filter((project) => project.is_scratch).length,
    render_images: projects.reduce((total, project) => total + project.render_image_count, 0),
    render_sets: projects.reduce((total, project) => total + project.render_set_count, 0),
    revisions: projects.reduce((total, project) => total + project.revision_count, 0),
    exports: projects.reduce((total, project) => total + project.export_count, 0),
    blend_files: projects.reduce(
      (total, project) => total + project.trees.reduce((sum, tree) => sum + tree.render_sets.reduce((count, set) => count + set.blend_count, 0), 0),
      0,
    ),
  };

  return {
    schema: "zf-floorplan-workbench-overview-v1",
    generated_at: new Date().toISOString(),
    roots,
    totals,
    warnings,
    projects,
    deliveries: await scanDeliveries(paths.deliveries),
  };
}
