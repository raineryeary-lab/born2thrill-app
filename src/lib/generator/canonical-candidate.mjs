import { validateCorrectionDocument, withUpdatedHash } from "./correction-editor.mjs";
export const ALLOWED_CANDIDATE_TRANSFORMS = Object.freeze(["identity", "mirror_horizontal", "mirror_vertical"]);
function assertReference(reference, source) {
  if (!reference || reference.projectId !== source?.source_reference_id) throw new Error("Candidate reference mismatch.");
  if (reference.qualityStatus !== "passed" || reference.packageStatus !== "training_ready") throw new Error("Candidate requires a quality-passed, training-ready reference.");
  if (reference.approvalStatus !== "annotated_reference" || reference.usageScope !== "internal_reference_only") throw new Error("Candidate requires an explicit approved internal reference.");
  if (source?.rights?.usage_scope !== "internal_reference_only") throw new Error("Candidate source must remain internal-only.");
}
function point(value, transform, width, depth) {
  if (transform === "mirror_horizontal") return [width - value[0], value[1]];
  if (transform === "mirror_vertical") return [value[0], depth - value[1]];
  return [...value];
}
export function createCanonicalCandidate({ source, reference, transform, validate = true }) {
  if (!ALLOWED_CANDIDATE_TRANSFORMS.includes(transform)) throw new Error(`Unsupported transform: ${transform}`);
  assertReference(reference, source);
  const before = JSON.stringify(source); const candidate = structuredClone(source);
  const width = Number(candidate.building.footprint_width_mm); const depth = Number(candidate.building.footprint_depth_mm);
  const map = (value) => point(value, transform, width, depth);
  for (const floor of candidate.floors || []) {
    floor.footprint = (floor.footprint || []).map(map);
    for (const room of floor.rooms || []) room.polygon = room.polygon.map(map);
    for (const wall of floor.walls || []) { wall.start = map(wall.start); wall.end = map(wall.end); }
  }
  if (candidate.shared_stair_core) {
    candidate.shared_stair_core.polygon = (candidate.shared_stair_core.polygon || []).map(map);
    candidate.shared_stair_core.path = (candidate.shared_stair_core.path || []).map(map);
  }
  candidate.revision = 0; candidate.status = "candidate"; candidate.wordpress_eligible = false;
  candidate.rights = { ...candidate.rights, usage_scope: "internal_reference_only", wordpress_eligible: false };
  candidate.provenance = { ...candidate.provenance, created_from: "quality_passed_annotated_reference", transformation: transform, source_mutated: false, publication_excludes_source_artifacts: true };
  const normalized = withUpdatedHash(candidate);
  if (JSON.stringify(source) !== before) throw new Error("Immutable candidate source was modified.");
  const validation = validate ? validateCorrectionDocument(normalized) : { valid: true, errors: [], warnings: [], geometry_hash: normalized.geometry_hash, hard_checks: {} };
  if (validate && !validation.valid) throw new Error(`Candidate failed hard validation: ${validation.errors.join(", ")}`);
  return { schema: "dmh-canonical-candidate-v1", schema_version: 1, parent_reference: { project_id: reference.projectId, quality_status: reference.qualityStatus, package_status: reference.packageStatus, approval_status: reference.approvalStatus, usage_scope: reference.usageScope, source_rights_status: reference.sourceRightsStatus }, transforms: [transform], candidate_approval_state: "pending_human_approval", geometry_hash: normalized.geometry_hash, validation, wordpress_eligible: false, external_delivery: "blocked", candidate: normalized };
}
