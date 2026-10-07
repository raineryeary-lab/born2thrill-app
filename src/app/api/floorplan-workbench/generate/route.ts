/* eslint-disable @typescript-eslint/no-explicit-any */
import sharp from "sharp";
import { buildVariantFromExplicitReference, type HouseBrief } from "@/lib/generator/floorplan";
import { buildCorrectionDocument, validateCorrectionDocument } from "@/lib/generator/correction-editor.mjs";
import { createCanonicalCandidate, ALLOWED_CANDIDATE_TRANSFORMS } from "@/lib/generator/canonical-candidate.mjs";
import { buildBlenderSceneManifest } from "@/lib/generator/blender-scene-manifest.mjs";
import { reconstructionReferenceCatalog, referenceLayoutById, referenceLayoutCandidates, type ReferenceLayoutMatch } from "@/lib/training/simplifier-reference";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const DEFAULT_REFERENCE = "onehalfstorey_020";

function hostname(value: string) { const first = value.split(",")[0]?.trim().toLowerCase() || ""; return first.startsWith("[") ? first.slice(1, first.indexOf("]")) : first.split(":")[0]; }
function enabled(request: Request) { const local = ["127.0.0.1", "localhost", "::1"]; return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true" && local.includes(new URL(request.url).hostname.toLowerCase()) && local.includes(hostname(request.headers.get("x-forwarded-host") || request.headers.get("host") || "")); }
function safeTransform(value: unknown) { const transform = String(value || "identity"); return ALLOWED_CANDIDATE_TRANSFORMS.includes(transform) ? transform as "identity" | "mirror_horizontal" | "mirror_vertical" : null; }
function roomMatches(room: ReferenceLayoutMatch["floors"][number]["rooms"][number], pattern: RegExp) { return pattern.test([room.roomId, ...room.roomIds, room.label].join(" ").toLowerCase()); }
function briefFor(reference: ReferenceLayoutMatch): HouseBrief {
  const rooms = reference.floors.flatMap((floor) => floor.rooms); const floors = reference.habitableFloors;
  return { projectName: reference.projectId, area: Number((reference.projectId.match(/\d+/g) || []).map(Number).filter((v) => v >= 80 && v <= 300).at(-1) || 140), floors, storeyType: floors === 1 ? "1_storey" : reference.houseType === "onehalfstorey" ? "1_5_storey" : "2_storey", adults: 2, children: 2, bedrooms: Math.max(1, rooms.filter((room) => roomMatches(room, /eltern|kind|schlaf|gast/)).length), bathrooms: Math.max(1, rooms.filter((room) => roomMatches(room, /bad|dusch/)).length), office: rooms.some((room) => roomMatches(room, /buero|arbeit/)), guestWc: rooms.some((room) => roomMatches(room, /wc/)), utilityRoom: rooms.some((room) => roomMatches(room, /hwr|htr|technik/)), groundFloorSleeping: false, accessibility: false, kitchen: "open", gardenConnection: "generous", stairPreference: "central", basement: "none", roof: "gable", style: "timeless-modern", streetDirection: "Nord", gardenDirection: "Süd", priorities: [], generationAttempt: 0, critiqueNotes: "", referenceUsageScope: "internal_reference_only", preferredReferenceLayoutId: reference.projectId };
}
function svg(document: any) {
  const colours: Record<string,string> = { living: "#d9f7e5", sleeping: "#f5f1e8", wet: "#dcecff", service: "#fff1bd", circulation: "#ece9e2", flex: "#f4f1ec" };
  const floors = document.floors.map((floor: any, index: number) => { const ox = 50 + index * 750; const scale = Math.min(650 / document.building.footprint_width_mm, 650 / document.building.footprint_depth_mm); const p = (v:number[]) => `${ox + v[0] * scale},${80 + v[1] * scale}`; return (floor.rooms || []).map((room:any) => `<polygon points="${room.polygon.map(p).join(" ")}" fill="${colours[room.kind] || colours.flex}"/>`).join("") + (floor.walls || []).map((wall:any) => `<line x1="${p(wall.start).split(",")[0]}" y1="${p(wall.start).split(",")[1]}" x2="${p(wall.end).split(",")[0]}" y2="${p(wall.end).split(",")[1]}" stroke="#1c1917" stroke-width="${Math.max(2, wall.thickness * scale)}"/>`).join(""); }).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900"><rect width="100%" height="100%" fill="white"/>${floors}<text x="50" y="860" font-size="18">Internal canonical candidate · ${document.geometry_hash}</text></svg>`;
}
async function result(referenceId: string, transform: string) {
  const reference = referenceLayoutById(referenceId);
  if (!reference) return { status: 404, body: { error: "Unknown explicit reference." } };
  if (reference.qualityStatus !== "passed" || reference.packageStatus !== "training_ready" || reference.approvalStatus !== "annotated_reference") return { status: 422, body: { error: "Reference is not quality-passed, training-ready, and explicitly annotated." } };
  const variant = buildVariantFromExplicitReference(briefFor(reference), reference);
  const source = buildCorrectionDocument(variant, { reconstructionOnly: reference.reconstructionOnly, sourceRightsStatus: reference.sourceRightsStatus, createdAt: "2026-08-01T00:00:00.000Z" });
  const envelope = createCanonicalCandidate({ source, reference, transform, validate: false });
  const validation = validateCorrectionDocument(envelope.candidate);
  let jpeg = null; let blender = null;
  if (validation.valid) { const bytes = await sharp(Buffer.from(svg(envelope.candidate))).flatten({ background: "#fff" }).jpeg({ quality: 88 }).toBuffer(); jpeg = { mime_type: "image/jpeg", file_base64: bytes.toString("base64"), geometry_hash: envelope.geometry_hash }; blender = buildBlenderSceneManifest(envelope.candidate); }
  const catalog = reference.reconstructionOnly ? reconstructionReferenceCatalog() : referenceLayoutCandidates({ houseType: reference.houseType, floors: reference.habitableFloors, bedrooms: briefFor(reference).bedrooms, bathrooms: briefFor(reference).bathrooms, office: briefFor(reference).office, guestWc: briefFor(reference).guestWc, utilityRoom: briefFor(reference).utilityRoom, basement: reference.hasBasement, stairPreference: "central", usageScope: "internal_reference_only" });
  const candidates = catalog.map((item) => ({ project_id: item.projectId, quality_status: item.qualityStatus, package_status: item.packageStatus, approval_status: item.approvalStatus, usage_scope: item.usageScope, source_rights_status: item.sourceRightsStatus, reconstruction_only: item.reconstructionOnly, stair_review_required: item.sourceStairReviewRequired }));
  return { status: 200, body: { schema: "dmh-floorplan-result-v3", brief: briefFor(reference), variant, source: envelope.parent_reference, transform, candidate: envelope.candidate, candidate_approval_state: envelope.candidate_approval_state, reference_layout_id: reference.projectId, reference_candidate: { project_id: reference.projectId, index: Math.max(0, candidates.findIndex((item) => item.project_id === reference.projectId)), count: candidates.length, quality_status: reference.qualityStatus, package_status: reference.packageStatus, approval_status: reference.approvalStatus, usage_scope: reference.usageScope, source_rights_status: reference.sourceRightsStatus, reconstruction_only: reference.reconstructionOnly, stair_review_required: reference.sourceStairReviewRequired }, reference_candidates: candidates, validation: { ...validation, synthetic_geometry_fallback: false, all_floors_reference_based: true, openings_retained: variant.floors.every((floor) => floor.referenceElements?.some((element) => element.type === "door") && floor.referenceElements?.some((element) => element.type === "window")), shared_stair_core: Boolean(variant.stairCore) }, jpeg, blender, geometry_hash: envelope.geometry_hash, geometry_sha256: envelope.geometry_hash, massing_geometry_sha256: envelope.geometry_hash, approval_status: "annotated_reference", usage_scope: "internal_reference_only", rights_watermark: "INTERNAL REVIEW – NOT FOR CUSTOMER DELIVERY", wordpress_eligible: false, external_delivery: "blocked" } };
}
export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const url = new URL(request.url); const transform = safeTransform(url.searchParams.get("transform")); if (!transform) return Response.json({ error: "Unsupported transform." }, { status: 400 });
  const response = await result(url.searchParams.get("reference") || DEFAULT_REFERENCE, transform); return Response.json(response.body, { status: response.status, headers: { "Cache-Control": "no-store" } });
}
export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  let body: any; try { body = await request.json(); } catch { return Response.json({ error: "Invalid JSON." }, { status: 400 }); }
  if (!body?.reference_id || body.entries || body.brief) return Response.json({ error: "reference_id and an allowlisted transform are required; free generation is disabled." }, { status: 400 });
  const transform = safeTransform(body.transform); if (!transform) return Response.json({ error: "Unsupported transform." }, { status: 400 });
  const response = await result(String(body.reference_id), transform); return Response.json(response.body, { status: response.status, headers: { "Cache-Control": "no-store" } });
}
