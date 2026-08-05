/* eslint-disable @typescript-eslint/no-explicit-any */
import { createHash, randomUUID } from "node:crypto";
import { spawn } from "node:child_process";
import { mkdir, readFile, readdir, rename, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import sharp from "sharp";
import { approvedGeometryHash, validateCorrectionDocument, withUpdatedHash } from "@/lib/generator/correction-editor.mjs";
import { doorColour, FLOORPLAN_RULES } from "@/lib/generator/floorplan-rulebook.mjs";
import { buildBlenderSceneManifest } from "@/lib/generator/blender-scene-manifest.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_REQUEST_BYTES = 8 * 1024 * 1024;
const INTERNAL_WATERMARK = "INTERNAL REVIEW Ã¢â‚¬â€œ NOT FOR CUSTOMER DELIVERY";

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(request.headers.get("x-forwarded-host") || request.headers.get("host") || "");
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

function dataRoot() {
  const configured = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  return configured
    ? resolve(configured)
    : join(process.env.LOCALAPPDATA || process.env.TEMP || ".", "Born2Thrill", "floorplan-workbench");
}

function appRepoDir() {
  const configured = process.env.ZF_APP_REPO_DIR?.trim();
  return configured ? resolve(configured) : resolve(process.cwd(), "..", "born2thrill-app-repo");
}

async function runBatchImport(): Promise<any> {
  const scriptPath = join(appRepoDir(), "scripts", "batch-import-approved-exports.mjs");
  return new Promise((resolveRun) => {
    let child;
    try {
      child = spawn(process.execPath, [scriptPath], {
        cwd: appRepoDir(),
        env: { ...process.env, FLOORPLAN_WORKBENCH_DATA_DIR: dataRoot() },
        windowsHide: true,
      });
    } catch (error) {
      resolveRun({ ok: false, error: error instanceof Error ? error.message : String(error) });
      return;
    }
    let stdout = "";
    let stderr = "";
    child.stdout?.on("data", (chunk) => { stdout += chunk; });
    child.stderr?.on("data", (chunk) => { stderr += chunk; });
    child.once("error", (error) => resolveRun({ ok: false, error: error.message }));
    child.once("exit", (code) => {
      if (code !== 0) { resolveRun({ ok: false, error: stderr.trim() || `Import script exited with code ${code}.` }); return; }
      try { resolveRun({ ok: true, summary: JSON.parse(stdout) }); }
      catch { resolveRun({ ok: false, error: "Could not parse import script output.", raw: stdout.slice(0, 500) }); }
    });
  });
}

function safeReference(value: unknown) {
  const reference = String(value || "").replace(/[^a-zA-Z0-9._-]/g, "");
  if (!reference) throw new Error("source_reference_id fehlt.");
  return reference;
}

async function revisionFiles(reference: string) {
  const directory = join(dataRoot(), "corrections", reference, "revisions");
  await mkdir(directory, { recursive: true });
  const files = (await readdir(directory)).filter((file) => /^revision-\d{4}\.json$/.test(file)).sort();
  return { directory, files };
}


function commercialApprovalSatisfied(document: any) {
  if (document?.rights?.usage_scope !== "commercial_generator") return false;
  if (document?.rights?.decision === "commercially_cleared") return true;
  return document?.rights?.decision === "generic_layout_reconstructed"
    && document?.rights?.commercial_approval_attested === true
    && document?.provenance?.transformation === "generic_layout_reconstruction"
    && document?.provenance?.publication_excludes_source_artifacts === true;
}
async function saveRevision(input: any, requestedStatus?: string) {
  const reference = safeReference(input.source_reference_id);
  const { directory, files } = await revisionFiles(reference);
  const revision = files.length + 1;
  const document = withUpdatedHash(structuredClone(input));
  document.revision = revision;
  document.updated_at = new Date().toISOString();
  document.status = requestedStatus || "draft";
  document.wordpress_eligible = document.status === "approved" && commercialApprovalSatisfied(document);
  if (document.rights) document.rights.wordpress_eligible = document.wordpress_eligible;
  const validation = validateCorrectionDocument(document);
  if (document.status === "approved" && !validation.valid) {
    return { ok: false, status: 422, error: "Approval requires every hard geometry check to pass.", validation };
  }
  const filename = `revision-${String(revision).padStart(4, "0")}.json`;
  const target = join(directory, filename);
  const temporary = `${target}.${randomUUID()}.tmp`;
  await writeFile(temporary, `${JSON.stringify({ ...document, validation }, null, 2)}\n`, { flag: "wx" });
  await rename(temporary, target);
  return { ok: true, status: 201, document, validation, path: target };
}

const ROOM_COLORS: Record<string, string> = {
  living: "#d9f7e5",
  sleeping: "#f5f1e8",
  wet: "#dcecff",
  service: "#fff1bd",
  flex: "#f4f1ec",
  circulation: "#ece9e2",
};

function floorBounds(floor: any) {
  const points = [
    ...(floor.footprint || []),
    ...floor.rooms.flatMap((room: any) => room.polygon),
    ...floor.walls.flatMap((wall: any) => [wall.start, wall.end]),
  ];
  return {
    minX: Math.min(...points.map((point: number[]) => point[0])),
    minY: Math.min(...points.map((point: number[]) => point[1])),
    maxX: Math.max(...points.map((point: number[]) => point[0])),
    maxY: Math.max(...points.map((point: number[]) => point[1])),
  };
}

function polygonBox(polygon: number[][]) {
  return {
    minX: Math.min(...polygon.map((point) => point[0])),
    maxX: Math.max(...polygon.map((point) => point[0])),
    minY: Math.min(...polygon.map((point) => point[1])),
    maxY: Math.max(...polygon.map((point) => point[1])),
  };
}

function roomLabelPoint(room: any, stair: any) {
  const roomBox = polygonBox(room.polygon);
  const center = [(roomBox.minX + roomBox.maxX) / 2, (roomBox.minY + roomBox.maxY) / 2];
  if (room.kind !== "circulation" || !stair?.polygon?.length) return center;
  const stairBox = polygonBox(stair.polygon);
  const overlaps = Math.min(roomBox.maxX, stairBox.maxX) > Math.max(roomBox.minX, stairBox.minX)
    && Math.min(roomBox.maxY, stairBox.maxY) > Math.max(roomBox.minY, stairBox.minY);
  if (!overlaps) return center;
  const leftWidth = stairBox.minX - roomBox.minX;
  const rightWidth = roomBox.maxX - stairBox.maxX;
  return [
    leftWidth >= rightWidth
      ? (roomBox.minX + stairBox.minX) / 2
      : (stairBox.maxX + roomBox.maxX) / 2,
    (Math.max(roomBox.minY, stairBox.minY) + Math.min(roomBox.maxY, stairBox.maxY)) / 2,
  ];
}

function openingEndpoints(opening: any, wall: any) {
  const dx = wall.end[0] - wall.start[0];
  const dy = wall.end[1] - wall.start[1];
  const length = Math.max(1, Math.hypot(dx, dy));
  const half = Math.min(0.45, opening.width / length / 2);
  return [opening.position - half, opening.position + half].map((ratio) => [
    wall.start[0] + dx * Math.max(0, Math.min(1, ratio)),
    wall.start[1] + dy * Math.max(0, Math.min(1, ratio)),
  ]);
}

function renderCorrectionSvg(document: any) {
  const footerLabel = document.wordpress_eligible ? "GEPR\u00dcFTER KONZEPTGRUNDRISS" : INTERNAL_WATERMARK;
  const footerColour = document.wordpress_eligible ? "#14532d" : "#7c2d12";
  const width = 1600;
  const height = 900;
  const panelWidth = document.floors.length > 1 ? 700 : 1040;
  const panelGap = document.floors.length > 1 ? 70 : 0;
  const startX = document.floors.length > 1 ? 70 : 280;
  const floors = document.floors.map((floor: any, floorIndex: number) => {
    const box = floorBounds(floor);
    const scale = Math.min(
      panelWidth / Math.max(box.maxX - box.minX, 1),
      610 / Math.max(box.maxY - box.minY, 1),
    );
    const originX = startX + floorIndex * (panelWidth + panelGap);
    const offsetX = originX + (panelWidth - (box.maxX - box.minX) * scale) / 2;
    const offsetY = 130 + (610 - (box.maxY - box.minY) * scale) / 2;
    const point = (value: number[]) => [
      offsetX + (value[0] - box.minX) * scale,
      offsetY + (value[1] - box.minY) * scale,
    ];
    const rooms = floor.rooms.map((room: any) => {
      const polygon = room.polygon.map((value: number[]) => point(value));
      const center = point(roomLabelPoint(room, document.shared_stair_core));
      return `<polygon points="${polygon.map((value: number[]) => value.join(",")).join(" ")}" fill="${ROOM_COLORS[room.kind] || ROOM_COLORS.flex}" stroke="none"/>
        <text x="${center[0]}" y="${center[1] - 4}" text-anchor="middle" font-size="17" font-weight="700" fill="#292524" paint-order="stroke" stroke="#fff" stroke-width="4">${escapeXml(room.name)}
          <tspan x="${center[0]}" dy="20" font-size="13" font-weight="400" fill="#64748b">ca. ${Number(room.area_m2).toFixed(1)} mÃ‚Â²</tspan>
        </text>`;
    }).join("");
    const walls = floor.walls.map((wall: any) => {
      const start = point(wall.start);
      const end = point(wall.end);
      return `<line x1="${start[0]}" y1="${start[1]}" x2="${end[0]}" y2="${end[1]}" stroke="#1c1917" stroke-width="${Math.max(3, wall.thickness * scale)}" stroke-linecap="square"/>`;
    }).join("");
    const openings = floor.openings.map((opening: any) => {
      const wall = floor.walls.find((candidate: any) => candidate.id === opening.wall_id);
      if (!wall) return "";
      const [first, second] = openingEndpoints(opening, wall).map((value) => point(value));
      const common = `x1="${first[0]}" y1="${first[1]}" x2="${second[0]}" y2="${second[1]}"`;
      const gap = `<line ${common} stroke="#fff" stroke-width="${Math.max(7, wall.thickness * scale + 4)}"/>`;
      if (opening.opening_type === "window") {
        return `${gap}<line ${common} stroke="#12aee2" stroke-width="4"/>`;
      }
      if (opening.opening_type === "passage") {
        return `${gap}<line ${common} stroke="${FLOORPLAN_RULES.doors.colours.openPassage}" stroke-width="4"/>`;
      }
      return `${gap}<line ${common} stroke="${doorColour(opening)}" stroke-width="6" stroke-linecap="square"/>`;
    }).join("");
    const stair = document.shared_stair_core?.polygon?.map((value: number[]) => point(value)) || [];
    const stairPath = document.shared_stair_core?.path?.map((value: number[]) => point(value)) || [];
    let stairMarkup = "";
    if (stair.length) {
      stairMarkup = `<polygon points="${stair.map((value: number[]) => value.join(",")).join(" ")}" fill="#fafaf9" stroke="#57534e" stroke-width="${Math.max(3, 100 * scale)}"/>`;
      if (stairPath.length >= 2) {
        const stairMinX = Math.min(...stair.map((value: number[]) => value[0]));
        const stairMaxX = Math.max(...stair.map((value: number[]) => value[0]));
        const stairMinY = Math.min(...stair.map((value: number[]) => value[1]));
        const stairMaxY = Math.max(...stair.map((value: number[]) => value[1]));
        const previous = [(stairMinX + stairMaxX) / 2, stairMaxY - (stairMaxY - stairMinY) * 0.18];
        const end = [(stairMinX + stairMaxX) / 2, stairMinY + (stairMaxY - stairMinY) * 0.18];
        const ux = 0;
        const uy = -1;
        const nx = 1;
        const ny = 0;
        const size = 10;
        const base = [end[0] - ux * size, end[1] - uy * size];
        const arrow = [
          end,
          [base[0] + nx * size * 0.55, base[1] + ny * size * 0.55],
          [base[0] - nx * size * 0.55, base[1] - ny * size * 0.55],
        ];
        stairMarkup += `<line x1="${previous[0]}" y1="${previous[1]}" x2="${end[0]}" y2="${end[1]}" stroke="#1d5b4a" stroke-width="3"/>
          <polygon points="${arrow.map((value) => value.join(",")).join(" ")}" fill="#1d5b4a"/>
          <text x="${(Math.min(...stair.map((value: number[]) => value[0])) + Math.max(...stair.map((value: number[]) => value[0]))) / 2}" y="${(Math.min(...stair.map((value: number[]) => value[1])) + Math.max(...stair.map((value: number[]) => value[1]))) / 2}" text-anchor="middle" font-size="12" font-weight="700" fill="#1d5b4a" paint-order="stroke" stroke="#fff" stroke-width="3">TREPPE Ã¢â€ â€˜</text>`;
      }
    }
    return `<text x="${originX}" y="78" font-size="28" font-weight="700">${escapeXml(floor.name)}</text>
      ${rooms}${walls}${openings}
      ${stairMarkup}`;
  }).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <rect width="100%" height="100%" fill="#ffffff"/>
    ${floors}
    <line x1="70" y1="790" x2="1530" y2="790" stroke="#d6d3d1"/>
    <text x="70" y="830" font-size="20" font-weight="700" fill="${footerColour}">${footerLabel}</text>
    <text x="70" y="865" font-size="16" fill="#57534e">Clean millimetre reconstruction Ã‚Â· no invented tread lines Ã‚Â· Geometry ${document.geometry_hash}</text>
  </svg>`;
}

function escapeXml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function sha256(value: Uint8Array | string) {
  return createHash("sha256").update(value).digest("hex");
}

async function exportApproved(document: any) {
  const validation = validateCorrectionDocument(document);
  if (document.status !== "approved" || !validation.valid) {
    return { ok: false, status: 422, error: "Only a valid approved revision can be exported.", validation };
  }
  const reference = safeReference(document.source_reference_id);
  const exportDirectory = join(dataRoot(), "corrections", reference, "exports", `revision-${String(document.revision).padStart(4, "0")}`);
  await mkdir(exportDirectory, { recursive: true });
  const corrected = withUpdatedHash(document);
  const publishable = structuredClone(corrected);
  publishable.schema = "dmh-floorplan-approved-canonical-v1";
  delete publishable.source_reference_id;
  delete publishable.source_annotation;
  delete publishable.source_annotation_sha256;
  delete publishable.validation;
  publishable.provenance = {
    creation_mode: corrected.provenance?.transformation || "manual_correction_revision",
    source_assets_included: false,
    internal_source_record_retained_locally: true,
  };
  publishable.geometry_hash = approvedGeometryHash(publishable);
  publishable.plan_id = `plan-${publishable.geometry_hash.slice(0, 16)}`;
  const publicGeometryHash = publishable.geometry_hash;
  const svg = renderCorrectionSvg(publishable);
  const jpeg = await sharp(Buffer.from(svg)).flatten({ background: "#ffffff" }).jpeg({ quality: 88, mozjpeg: true }).toBuffer();
  const guide = await sharp(Buffer.from(svg)).resize(1024, 1024, { fit: "contain", background: "#ffffff" }).png().toBuffer();
  const massing = Buffer.from(JSON.stringify({
    schema: "dmh-floorplan-massing-metadata-v1",
    geometry_hash: publicGeometryHash,
    plan_id: publishable.plan_id,
    floors: corrected.floors.map((floor: any) => ({
      id: floor.id,
      walls: floor.walls,
      openings: floor.openings,
    })),
    shared_stair_core: corrected.shared_stair_core,
    roof: { form: "satteldach", representation: "deterministic_massing" },
  }, null, 2));
  const json = Buffer.from(`${JSON.stringify(publishable, null, 2)}\n`);
  const files = {
    "canonical-plan.json": json,
    "floorplan.jpg": jpeg,
    "geometry-guide.png": guide,
    "massing.json": massing,
  };
  const manifest = {
    schema: "dmh-floorplan-approved-package-v3",
    plan_id: publishable.plan_id,
    source_assets_included: false,
    revision: corrected.revision,
    geometry_hash: publicGeometryHash,
    provenance: corrected.provenance,
    rights: corrected.rights,
    wordpress_eligible: Boolean(corrected.wordpress_eligible),
    created_at: new Date().toISOString(),
    files: Object.fromEntries(Object.entries(files).map(([name, bytes]) => [name, {
      sha256: sha256(bytes),
      bytes: bytes.length,
    }])),
  };
  for (const [name, bytes] of Object.entries(files)) await writeFile(join(exportDirectory, name), bytes);
  await writeFile(join(exportDirectory, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  const importResult = await runBatchImport();
  return { ok: true, status: 201, export_directory: exportDirectory, manifest, import_result: importResult };
}

async function preview(document: any) {
  const normalized = withUpdatedHash(document);
  const svg = renderCorrectionSvg(normalized);
  const jpeg = await sharp(Buffer.from(svg)).flatten({ background: "#ffffff" }).jpeg({ quality: 88, mozjpeg: true }).toBuffer();
  return {
    mime_type: "image/jpeg",
    filename: `${normalized.source_reference_id}-revision-preview.jpg`,
    file_base64: jpeg.toString("base64"),
    sha256: sha256(jpeg),
    bytes: jpeg.length,
    geometry_hash: normalized.geometry_hash,
    massing_geometry_hash: normalized.geometry_hash,
  };
}

const BLENDER_EXECUTABLE = ["C:", "Program Files", "Blender Foundation", "Blender 5.0", "blender.exe"].join("\\");
const BLENDER_SCRIPT = join(process.cwd(), "scripts", "export-floorplan-blender.py");

async function renderBlender(document: any, view: string) {
  const normalized = withUpdatedHash(document);
  const validation = validateCorrectionDocument(normalized);
  if (!validation.valid) return { ok: false, status: 422, error: "Hard-invalid geometry cannot render.", validation };
  const manifest = buildBlenderSceneManifest(normalized, { renderView: view });
  if (manifest.source_geometry_hash !== normalized.geometry_hash) return { ok: false, status: 409, error: "Stale Blender manifest rejected." };
  const reference = safeReference(normalized.source_reference_id);
  const directory = join(dataRoot(), "corrections", reference, "blender", normalized.geometry_hash);
  await mkdir(directory, { recursive: true });
  const manifestPath = join(directory, `scene-${view}-manifest.json`);
  const blendPath = join(directory, `scene-${view}.blend`);
  const pngPath = join(directory, `scene-${view}.png`);
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  const exitCode = await new Promise<number>((resolveExit, rejectExit) => {
    const child = spawn(BLENDER_EXECUTABLE, ["--background", "--python", BLENDER_SCRIPT, "--", manifestPath, blendPath, pngPath], { windowsHide: true, stdio: "ignore" });
    child.once("error", rejectExit);
    child.once("exit", (code) => resolveExit(code ?? -1));
  });
  if (exitCode !== 0) return { ok: false, status: 500, error: `Blender exited ${exitCode}.` };
  const png = await readFile(pngPath).catch(() => null);
  if (!png) return { ok: false, status: 500, error: "Blender finished without creating scene.png." };
  return { ok: true, status: 201, manifest, render_view: view, geometry_hash: normalized.geometry_hash, blend_path: blendPath, png_path: pngPath, png_base64: png.toString("base64") };
}
export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const reference = safeReference(new URL(request.url).searchParams.get("reference") || "onehalfstorey_003");
  const { directory, files } = await revisionFiles(reference);
  if (!files.length) return Response.json({ reference, revisions: [], latest: null });
  const latest = JSON.parse(await readFile(join(directory, files.at(-1)!), "utf8"));
  return Response.json({ reference, revisions: files, latest }, { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const text = await request.text();
  if (Buffer.byteLength(text) > MAX_REQUEST_BYTES) return Response.json({ error: "Revision too large." }, { status: 413 });
  let source: any;
  try { source = JSON.parse(text); } catch { return Response.json({ error: "Invalid JSON." }, { status: 400 }); }
  const action = source.action;
  const document = source.document;
  if (!document) return Response.json({ error: "Correction document missing." }, { status: 400 });
  if (action === "validate") {
    const normalized = withUpdatedHash(document);
    return Response.json({
      document: normalized,
      validation: validateCorrectionDocument(normalized),
      preview: await preview(normalized),
    });
  }
  if (action === "save_draft") {
    const result = await saveRevision(document, "draft");
    return Response.json(result, { status: result.status });
  }
  if (action === "approve") {
    const result = await saveRevision(document, "approved");
    return Response.json(result, { status: result.status });
  }
  if (action === "reject") {
    const result = await saveRevision(document, "rejected");
    return Response.json(result, { status: result.status });
  }
  if (action === "render_blender") {
    const view = typeof source.view === "string" ? source.view : "garden";
    if (!["garden", "street", "east", "west"].includes(view)) return Response.json({ error: "Unsupported Blender render view." }, { status: 400 });
    const result = await renderBlender(document, view);
    return Response.json(result, { status: result.status });
  }
  if (action === "export") {
    const result = await exportApproved(document);
    return Response.json(result, { status: result.status });
  }
  return Response.json({ error: "Unknown action." }, { status: 400 });
}


