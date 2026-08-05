# Canonical Local Generator and Blender Vertical Slice

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Replace the mixed proof workflow with one local deterministic chain:

`quality-passed annotated reference -> immutable source snapshot -> millimetre canonical revision -> safe reference-derived candidate -> validation -> JPEG and Blender from the same geometry hash -> human approval`

The first slice proves this architecture with one 1.5-storey internal reference. It does not deliver to WordPress and does not use free floorplan generation.

## Current evidence and behavior

- The protected Simplifier corpus contains 236 project folders and 233 `annotations.json` files. This plan does not edit, move, delete, or reclassify them.
- `src/app/api/floorplan-workbench/generate/route.ts` still calls legacy `generateVariants()` for reference conversion and POST generation.
- `src/app/floorplan-workbench/page.tsx` already has a local correction UI, validation, revision actions, JPEG preview, and schematic massing view.
- `src/lib/generator/correction-editor.mjs` already provides immutable source hashing, millimetre corrections, geometry hashing, editor history, and hard validation.
- The corrections route stores append-only revisions and exports JPEG/PNG plus `massing.json`; that massing file is metadata, not a Blender model.
- The repository has both `dmh-canonical-floorplan-v1` and exported `dmh-floorplan-approved-canonical-v1`. This slice must not create a third geometry dialect.
- No Blender exporter exists.
- Blender 5.0.0 is installed at `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe` and runs headlessly.
- First candidate: `german_catalog_review_onehalfstorey_1_1_1_efh_120`. Code data says `quality_status=passed`, `package_status=training_ready`, `approval_status=annotated_reference`, `usage_scope=internal_reference_only`, and `source_rights_status=restricted_reference`. It remains internal-only.

## Repository baselines

### Local Workbench

- Path: `C:\dev\born2thrill-local-workbench`
- Branch: `agent/zuhausefinder-generator`
- Base SHA: `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`
- Existing state: substantial tracked and untracked Workbench, corpus-index, correction-editor, rulebook, launcher, and test changes. Preserve all. No cleanup, reset, stash, checkout, broad restore, or unrelated formatting.

### Deployable app (context only; no runtime changes)

- Path: `C:\dev\born2thrill-app-repo`
- Branch: `fix/customer-floorplan-output`
- Base SHA: `cbd4be4480aafc775ea390e3b1991eede9672fef`
- Existing state: modified `AGENTS.md` and `CLAUDE.md`; untracked server logs, workflow documentation, and plans.

## Exact scope

1. Add acceptance tests first.
2. Make one millimetre canonical plan the only geometry input for both 2D and Blender.
3. Add deterministic candidate operations: identity, whole-building horizontal mirror, and whole-building vertical mirror.
4. Record parent reference, ordered transforms, schema version, geometry hash, validation report, and candidate approval state. Source and previous revisions stay immutable.
5. Replace Workbench POST free generation with a named quality-passed reference and allowlisted transform. Reject missing/unknown references, unsupported transforms, and synthetic fallback.
6. Keep manual room/wall/opening/stair correction. Room resizing and swapping wait for a separate plan because they can break topology.
7. Derive a Blender scene manifest—slabs, wall solids, wall-linked openings, shared stair core, storey heights, and roof placeholder—from the same canonical plan. Copy the canonical geometry hash unchanged.
8. Add a headless Blender Python exporter that reads only the manifest, creates a `.blend`, and renders one deterministic PNG. It may not infer or redraw room geometry.
9. Add local-only API actions for Blender artifacts. Hard-invalid geometry cannot render.
10. Show the same candidate as JPEG and Blender preview with transform, validation state, revision, and common geometry hash. Approval appends a revision; it never overwrites anything.
11. Track the task in the canonical roadmap.

## Files in scope

Likely existing changes:

- `C:\dev\born2thrill-local-workbench\src\app\api\floorplan-workbench\generate\route.ts`
- `C:\dev\born2thrill-local-workbench\src\app\api\floorplan-workbench\corrections\route.ts`
- `C:\dev\born2thrill-local-workbench\src\app\floorplan-workbench\page.tsx`
- `C:\dev\born2thrill-local-workbench\src\lib\generator\correction-editor.mjs`
- `C:\dev\born2thrill-local-workbench\src\lib\generator\correction-editor.d.ts`
- `C:\dev\born2thrill-local-workbench\scripts\local-floorplan-workbench.test.mjs`
- `C:\dev\born2thrill-local-workbench\package.json`
- `C:\dev\born2thrill-app-repo\plans\ROADMAP.md` (tracking only)

Likely new files:

- `src/lib/generator/canonical-candidate.mjs`
- `src/lib/generator/canonical-candidate.d.ts`
- `src/lib/generator/blender-scene-manifest.mjs`
- `src/lib/generator/blender-scene-manifest.d.ts`
- `scripts/export-floorplan-blender.py`
- `scripts/canonical-candidate.test.mjs`
- `scripts/blender-export.test.mjs`

If another runtime, data, schema, or configuration file is required, stop and revise the plan.

## Explicitly out of scope

- WordPress, email, SMTP, DNS, Railway, deployment, database, OpenAI image generation, photorealistic exteriors, or customer data.
- Patching the old bungalow or previous 1.5-storey proof.
- Importing all 233 annotations in this first slice.
- Free generation, AI geometry, voice, learning, ranking, genetic search, invented rooms, room resizing/swapping, window redesign, furniture, materials, landscaping, or final rendering.
- Rights reclassification or customer publication of the restricted first reference.
- Changing or deleting original annotations, source images/PDFs, prior revisions, or approved artifacts.
- Commit, push, PR, deployment, migration, dependency installation, or external message.

## API, schema, and data-contract effects

- Workbench POST changes from `{entries} -> {brief, variants}` to `{reference_id, transform} -> {source, candidate, validation, jpeg, blender}`.
- GET reference inspection must stop converting through free `generateVariants()`; it uses the explicit reference-to-correction adapter.
- `dmh-canonical-floorplan-v1` remains the geometry contract. Revision metadata is an envelope, not a competing geometry source.
- The Blender manifest is derived output and contains `source_geometry_hash`; mismatch is fatal.
- Candidate and Blender artifacts remain local, review-only, and `wordpress_eligible=false`.

## Acceptance criteria

1. All 233 annotation files have identical paths, sizes, and SHA-256 hashes before and after.
2. The chosen 1.5-storey reference is immutable and internal-only; source assets are excluded from candidate exports.
3. Identity and mirrors are deterministic and produce stable canonical JSON/hashes.
4. Mirrors preserve room areas, wall thicknesses, opening dimensions/linkage, entrance reachability, storeys, and shared stair alignment; stair direction remains `up`.
5. Candidates pass existing hard validation before JPEG or Blender export.
6. Candidate paths call no `generateVariants()`, `selectQualityVariant()`, or synthetic fallback.
7. JPEG and Blender manifest report the same canonical geometry hash.
8. Headless Blender creates a non-empty `.blend` and PNG, exits 0, and embeds the geometry hash as scene metadata.
9. Changed geometry invalidates stale Blender output.
10. Approval appends a numbered revision; sources and earlier revisions remain byte-identical.
11. The restricted reference remains internal-only, non-WordPress, and non-customer.
12. The UI labels source, transform, validation, revision, and common hash beside 2D/3D.
13. Existing tests are not deleted, skipped, weakened, or silently rewritten.

## Tests and verification commands

New tests:

- `scripts/canonical-candidate.test.mjs`: deterministic identity/mirrors, immutable source, topology invariants, reject unsupported transforms and synthetic/unapproved sources.
- `scripts/blender-export.test.mjs`: manifest hash equality, stale-manifest rejection, headless Blender `.blend`/PNG output, and embedded hash.
- Extend `scripts/local-floorplan-workbench.test.mjs`: explicit reference plus transform only, no free variants, invalid candidate cannot render/approve, append-only revisions, delivery block.

Verification after approval:

- `pnpm test:canonical-floorplan`
- `pnpm test:local-floorplan-workbench`
- new candidate and Blender test commands
- `pnpm exec tsc --noEmit --pretty false`
- `pnpm run lint`
- `pnpm run build`
- `git diff --check`
- before/after corpus SHA-256 comparison
- final status and full diff summary

## Protected and risky paths

- Simplifier projects, source assets, PDFs, previews, annotations, exports, and private corpus.
- Workbench data, corrections, revisions, exports, local runtime data, `tmp`, and all existing dirty/untracked files.
- All environment files, credentials, customer data, WordPress uploads, live endpoints, backups, and Git metadata.
- Blender outputs go only to a task-specific local artifact directory.

## Rights, provenance, privacy, and security impact

- Mirroring/reconstruction does not establish commercial rights. The first reference stays restricted/internal.
- Sources remain local and immutable. Candidate exports record parent/transform but exclude original assets.
- Endpoints remain loopback-only with size limits, safe IDs, fixed output roots, and no shell interpolation.
- Blender uses a fixed executable/script path; requests choose only allowlisted references/transforms.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Required answer: **no**.

Evidence required: explicit quality-passed source loading, hard validation, equal 2D/3D hashes, internal-only delivery gates, and tests proving no legacy free generator or synthetic fallback.

## Customer, email, database, deployment, and external effects

None. Local-only. No email, WordPress, database, image API, push, or deploy.

## Failed-hypothesis log

1. Recursive metadata-count PowerShell command had a parser error from piping directly after `foreach`. Corrected by collecting results before formatting. No files changed.

Stop after three distinct failed implementation hypotheses.

## Rollback

Revert only named files and remove only named new files. Remove only task-generated Blender artifact directories after validating exact paths. Never use `git clean`, `git reset --hard`, broad restore, or deletion of Workbench/Simplifier data roots.

## Unresolved questions

No blocking design question. Identity/mirrors are intentionally the first slice. Room swaps/resizing require a later approved plan. The internal reference is not commercially eligible; a later task must choose or reconstruct a rights-cleared plan before WordPress use.

## Approval record

Not approved. Stop before implementation.
