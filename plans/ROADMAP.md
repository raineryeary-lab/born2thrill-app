# ZuhauseFinder Suite Roadmap

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

This is the canonical persistent task list for the local Floorplan Simplifier, correction Workbench, deployable Born2Thrill service, and ZuhauseFinder WordPress integration.

Rules:
- Never remove a known follow-up merely because it is outside the current task.
- Mark COMPLETE only with evidence.
- Mark CANCELLED only after explicit user direction.
- Every implementation task uses its own approved plan.

## P0 - Recovery and current work

| ID | Status | Task | Plan/evidence | Next gate |
|---|---|---|---|---|
| RECOVERY-001 | COMPLETE | Source-only backup v5 created, restored, checksum-verified, 64 Simplifier tests passed, WordPress PHP/snippet lint passed, and 35-file Simplifier allowlist staged | `C:\dev\backups\2026-08-01-v5-zuhausefinder-source-baseline` | No commit/push; private corpus remains separate under CORPUS-BACKUP-001 |
| WORKBENCH-BASELINE-001 | PENDING | Review and intentionally preserve/commit the existing dirty Workbench implementation | Existing branch `agent/zuhausefinder-generator` | New inspect-only plan after RECOVERY-001 |
| CORPUS-BACKUP-001 | BLOCKED_DECISION | Protect the private structured floorplan corpus with confirmed at-rest encryption and an independent recovery destination | Existing unencrypted 30 July ZIP remains untouched | User chooses BitLocker-protected destination, encrypted archive, or approved encrypted offline storage |
| FLOORPLAN-CATALOG-001 | COMPLETE | Build a deterministic searchable catalogue over the Simplifier v2 export without altering annotations, geometry, rights, or approval state | 310 projects, 497 floors, 3,072 room polygons, and 7,205 elements reconcile with the manifest; six focused catalogue tests pass | Keep generated catalogue byte-stable with `node scripts/build-floorplan-search-catalog.mjs --check` |
| DATASET-EXPORT-001 | IN_PROGRESS | Produce a strictly quality-passed, privacy-safe generator export and keep draft/test records separate | 2026-08-02 v2 batch accounts for 370 folders: 310 exportable, 295 quality-passed (133 bungalow, 85 one-and-a-half-storey, 75 two-storey, 1 cellar, 1 other), 15 held for review, 60 excluded with reason codes; local workbench catalog now reads v2 and 31 focused tests pass | Promote the validated v2 handoff into the main generator, add the dimension-recovery stage, then run one end-to-end internal smoke test |
| WORKBENCH-CATALOG-SEARCH-001 | COMPLETE | Wire the FLOORPLAN-CATALOG-001 search catalogue into the port-3020 Floorplan Workbench as a filter panel + 3 demo presets, so a questionnaire-style query can find and load a matching approved reference instead of only browsing auto-derived "similar to current" candidates | New read-only `catalog-search` API route wraps `filterFloorplanCatalog()`; all 3 presets (1.5-storey homeoffice: 38 matches, bungalow homeoffice+child rooms: 12, twostorey garage: 7) verified live end to end through the existing unchanged quality/rights gate; Previous/Next and all existing Workbench functionality unaffected | Phase 2 (rule-based variant generation, automatic scoring, façade/rendering pipeline) is a separate future plan, not started |
| APPROVED-CATALOG-GROWTH-001 | PENDING | Grow the customer-facing `approved-floorplan-catalog.ts` (schema `dmh-floorplan-approved-package-v3`) past its current single record by approving/exporting more of the 310 annotated references through the Workbench and running the existing `import:approved-floorplan` script | `catalog.generated.mjs` currently holds exactly one `wordpress_eligible: true` record (`plan-caaccb688174a403`), matching the one questionnaire combination that currently works live; export/import mechanism already exists and needs no new code, only process | User decides whether to prioritize this (fast, no new code) ahead of GENERATION-PIPELINE-PHASE2-001 |
| GENERATION-PIPELINE-PHASE2-001 | PROPOSED | Rule-based variant generation, automatic scoring, Schokoladenseite façade/camera selection, geometry lock, external exterior-rendering API, and human-approved catalogue enrichment, per the 2026-08-02 Codex handoff's six-step target workflow | `plans/generation-pipeline-phase2-v1.md` (born2thrill-local-workbench) records scope, what's already reusable (façade view + geometry lock, both APPROVED elsewhere), and what's genuinely unbuilt (variant generation/scoring, rendering API) | Rendering-provider choice, cost, and exact variant-generation rule bounds are unresolved; not approved, nothing implemented |

## P1 - Floorplan corpus and correction workflow

| ID | Status | Task | Current evidence | Next gate |
|---|---|---|---|---|
| SIMPLIFIER-REVIEW-001 | PENDING | Finish the three remaining CubiCasa draft annotations | Draft projects 199, 832, and 904 | Annotate and validate |
| RECONSTRUCTION-001 | PENDING | Reconstruct and approve rights-limited references as separate canonical geometry without source artifacts | 55 normalized reconstruction references available; source status remains restricted | Human geometry and output approval |
| CORPUS-GROWTH-001 | PENDING | Add more 1.5-storey and 2-storey annotations before broad generation | User target includes 200 additional annotations | Separate corpus-growth plan |
| VARIANT-REVIEW-001 | PENDING | Produce safe variants only from approved corrected plans and compare better/worse results | Free generation remains prohibited | Reliable approved-plan correction workflow first |
| ENTRY-WARDROBE-VARIANT-001 | PENDING | Add a rule-based entrance Garderobennische variation: rectangular niche open to Diele, taken from adjacent HTR/HWR only while preserving roughly 9–10 m² HTR/HWR and valid entrance/door/circulation clearance | User rule clarified 2026-08-01; never treat the niche as an unnamed geometry gap | Implement only in a later approved reference-derived variation plan |
| GENERATOR-BLENDER-001 | PROPOSED | Build the local canonical reference-derived candidate pipeline and Blender vertical slice from one shared geometry hash | `C:\dev\born2thrill-local-workbench\plans\canonical-generator-blender-v1.md` | User approval of the Phase 1 plan |
| DIMENSION-RECOVERY-001 | PENDING | Enrich catalogue records with authoritative millimetre dimensions and square metres only where a verified scale source exists | Current normalized export deliberately reports metric area as unavailable | Separate inspect-and-plan task; never infer metric scale |
| CATALOG-DATABASE-001 | PENDING | Evaluate importing the verified JSON catalogue into relational persistence for operational searching | Deterministic local JSON catalogue exists; no database mutation performed | Separate schema/migration plan and explicit approval |
| MEASURED-PDF-001 | IN_PROGRESS | Build the first simplified canonical house from the BV Bach measured PDFs using verified scale, layout and opening evidence | Source hashes and vector evidence recorded; defaults fixed at 350 mm exterior, 100 mm interior and 900 mm usable stair; pilot tests 3/3 pass | User traces simplified room polygons, assigns ambiguous openings, and classifies the unlabeled OG rough-installation area; then hard validation and shared 2D/Blender output |

## P1 - Customer proof of concept

| ID | Status | Task | Current evidence | Next gate |
|---|---|---|---|---|
| WORDPRESS-POC-001 | IN_PROGRESS | Match questionnaire results to an approved corrected plan, generate safe JPEG artifacts, approve, and send through the manual WordPress email gate | Real reconstructed plan plan-caaccb688174a403 is approved as revision 4, exported/imported through v3, and returned by the local API as a verified 1.5-storey JPEG plus PNG guide; WordPress remains unchanged | Separately authorized deployment and live WordPress proof |
| EXTERIOR-POC-001 | PENDING | Generate a photorealistic exterior from the approved canonical plan and questionnaire styling without changing geometry | Stage 2 remains separate | Geometry-faithful guide and explicit approval |

## Completed governance

| ID | Status | Task | Evidence |
|---|---|---|---|
| GOVERNANCE-001 | COMPLETE | Install inspect-plan-approve-review workflow in all four roots | Policy `ZF-AGENT-WORKFLOW-v1.0.0`; Codex discovery passed; Claude review PASS |

