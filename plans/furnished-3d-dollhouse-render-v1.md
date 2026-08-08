# Furnished 3D dollhouse render pipeline

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Produce a furnished, isometric "dollhouse cutaway" 3D render per approved floorplan (matching the reference photos Rainer supplied on 2026-08-05: all rooms visible at once, roof and near walls removed, furniture placed per room), plus a matching exterior render, while the total number of distinct floorplans in the catalogue is being reduced per the business's new direction. Furniture is built once per (furniture type x style) as a reusable 3D asset, not regenerated per render, so image volume scales with (rooms x styles), not with an expensive per-render generation step.

## Current evidence and behavior

- `src/lib/generator/blender-scene-manifest.mjs` (`buildBlenderSceneManifest`) already converts a validated canonical floorplan into a schema'd 3D scene manifest: walls, openings (boolean-cut), slabs, deterministic gable roof, and an exterior camera (garden/street/east/west) driven by `facade-analysis.mjs`. Verified by reading the file 2026-08-05.
- `scripts/export-floorplan-blender.py` consumes that manifest inside Blender (`bpy`) and procedurally builds the exterior massing: box-primitive walls/slabs/roof, boolean-difference window/door cuts, six hardcoded materials. Verified by reading the file 2026-08-05 (first 80 lines).
- This pipeline is exterior-only today: no interior floor plates are rendered per room, no furniture exists, one fixed material palette (no styles), and the camera logic only covers the four exterior facade angles, not an interior isometric cutaway.
- `floorplan-simplifier` (separate repo, Python/PIL/reportlab) has no 3D or Blender capability and is out of scope as a build target for this feature per Rainer's 2026-08-05 decision.
- No furniture asset library, AI-3D-generation integration, or per-room placement logic exists anywhere in the codebase today (checked via grep for "furniture", "asset", "meshy", "tripo", "rodin" — no matches).

## Repository baselines

- `born2thrill-local-workbench`, branch `agent/zuhausefinder-generator`, local HEAD `8ada3ccd4b1e5e407ed34ac5c53dfd6437478388` as of 2026-08-05. Remote `origin/agent/zuhausefinder-generator` is ahead at `260a8c2` (a rebased/cherry-picked equivalent pushed via a separate clone earlier the same day — local branch has not yet been fast-forwarded to it). Working tree as of this plan: 1 modified file (`data/simplifier-v1/README.md`) and an untracked `tmp/` directory; otherwise clean.
- No other repository is in scope for implementation.

## Exact scope (Phase 1 — proposed, not approved)

1. Furniture asset pipeline: for a small starter catalogue of furniture types (bed, sofa, dining table, dining chair, armchair, wardrobe, kitchen counter run, desk/office chair, shower/bath fixtures — final list to be confirmed), attempt text-to-3D generation (tool TBD — Meshy, Tripo, or Rodin, pending API access/cost check) once per (type x style) for 2 initial styles (modern, classic). Each generated mesh is reviewed for usable topology/scale/orientation before being accepted into the library. Any piece that fails review falls back to a sourced/licensed pre-made model for that specific piece (hybrid approach, per Rainer's decision). Accepted assets are stored as versioned `.glb`/`.blend` files with a small JSON manifest (type, style, real-world bounding box in mm, default orientation) so placement logic can reason about their footprint.
2. Room-type-driven automatic placement: extend the canonical room schema's existing `kind` field (already used by `floorplan-rulebook.mjs` for window/door rules) to drive a placement ruleset per room kind (e.g. "sleeping" -> bed against the longest unbroken wall + wardrobe, "living" -> sofa facing the largest window, etc.). Output is a per-room furniture placement list (asset id, position, rotation) appended to the Blender scene manifest.
3. "Rearrange this room" command: a scoped regeneration entry point (new API action, e.g. `rearrange_room` on the existing corrections route) that re-runs placement for one room only, producing a new candidate layout without touching other rooms' furniture or the underlying wall/opening geometry.
4. Manual override: extend the existing Workbench correction editor (same pattern used for walls/openings today) to let a person drag/rotate/swap an individual furniture item after auto-placement, persisted the same way corrections are persisted today (revision history, not silent overwrite).
5. Interior rendering: extend `export-floorplan-blender.py` to also build interior floor plates per room, apply per-room floor/wall finish materials per selected style, place the furniture assets from the manifest, and add a new isometric dollhouse camera (fixed elevation angle, roof and near-side walls hidden) alongside the existing four exterior cameras.
6. Exterior render: reuse the existing facade/camera pipeline as-is; extend only the material palette to vary by style (e.g. render exterior once per style if style affects exterior finishes, otherwise once total — needs Rainer's input, see Unresolved questions).

## Files in scope

- `src/lib/generator/blender-scene-manifest.mjs` (extend: add furniture placement list, interior floor plates, dollhouse camera)
- `scripts/export-floorplan-blender.py` (extend: interior geometry, furniture instancing, per-style materials, new camera)
- `src/lib/generator/floorplan-rulebook.mjs` (extend: room-kind -> furniture placement rules, additive only)
- New: `src/lib/generator/furniture-placement.mjs` (new module for placement logic, isolated from existing wall/opening logic)
- New: `src/lib/generator/furniture-catalog.mjs` or `data/furniture-catalog/` (asset manifest + metadata)
- `src/app/api/floorplan-workbench/corrections/route.ts` (extend: new `rearrange_room` action)
- `src/app/floorplan-workbench/page.tsx` (extend: manual override UI for furniture, following the existing opening-editor interaction pattern)
- New test files for every new/changed `.mjs` module, following the existing `scripts/*.test.mjs` convention.

## Explicitly out of scope

- Reducing/curating the floorplan catalogue itself (that is a separate, business-side decision/task, not a code change).
- Any AI-3D-generation vendor contract, billing, or API key provisioning (needs Rainer's account/payment action, prohibited for me to do per standing rules).
- Any change to the rights/approval workflow (`rights_decision`, `usage_scope`, "Approve locally") — unchanged, still exclusively Rainer's action.
- Purchasing or licensing any fallback pre-made asset pack (needs Rainer's explicit purchase approval).
- Styles beyond the initial 2 (modern, classic) — future phase.
- Any change to `floorplan-simplifier` or `born2thrill-app-repo`.

## API, schema, and data-contract effects

- `blender-scene-manifest.mjs`'s manifest schema gains new optional fields (`furniture`, interior floor plate data, `style`) — additive, must not break existing exterior-only consumers. Schema version bump required (`dmh-blender-scene-manifest-v1` -> `v2`) with a compatibility check.
- New `rearrange_room` action on the corrections API — additive, no change to existing `validate`/`save_draft`/`approve`/`reject`/`render_blender`/`export` actions.

## Acceptance criteria

- A validated canonical floorplan can produce a dollhouse-style interior render with furniture placed automatically, for both initial styles, with zero manual intervention.
- `rearrange_room` regenerates only the targeted room's furniture; a snapshot diff proves no other room or wall/opening data changes.
- Manual override of a single furniture item persists through save/reload exactly like existing wall/opening corrections.
- Exterior render output is unchanged in content for the existing 4 camera angles when no style-dependent exterior material change is requested (regression check against current `export-floorplan-blender.py` output).
- Furniture assets that fail AI-generation review are documented with the fallback asset's source/license.

## Tests and verification commands

- New: `scripts/furniture-placement.test.mjs` — room-kind -> placement rule coverage, including edge cases (room too small for default furniture set, missing room kind).
- New: `scripts/furniture-catalog.test.mjs` — manifest schema validation for every asset entry.
- Extend `scripts/blender-scene-manifest.test.mjs` (or equivalent) for the new schema fields, run via `node --test --test-isolation=none`.
- No existing test may be deleted, skipped, or weakened; this plan adds only.

## Protected and risky paths

- `export-floorplan-blender.py` boolean-cut logic (opening voids) — must not regress when interior floor plates are added; floor plates must not accidentally boolean-cut through openings.
- Geometry hash / validation gate (`validateCorrectionDocument`) — furniture data must not affect `geometry_hash` (furniture is presentation, not geometry-of-record) to avoid invalidating already-approved plans.

## Rights, provenance, privacy, and security impact

- AI-generated 3D furniture models: provenance/licensing of the generation tool's output needs explicit confirmation before commercial use (most text-to-3D services' commercial-use terms vary by plan tier) — flagged as an unresolved question below, not to be assumed.
- Fallback sourced/purchased assets: license terms must be recorded per asset in the catalogue manifest (attribution requirements, redistribution limits).
- No customer or personal data involved.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Required answer: no. Furniture/style rendering only runs against a canonical document that has already passed `validateCorrectionDocument`, identical to the existing `render_blender` gate. Furniture placement does not touch `geometry_hash`, so it cannot cause geometry to bypass the existing approval gate. `rearrange_room` writes a new revision through the same `saveRevision` path as every other correction action, so it stays inside the existing draft/approve history — no new export or publish path is introduced by this plan.

## Customer, email, database, deployment, and external effects

None. Any AI-3D-generation vendor sign-up, API billing, or asset-pack purchase needs separate explicit authorization from Rainer before Phase 1 implementation can start.

## Failed-hypothesis log

(none yet — plan not yet implemented)

## Rollback

All new code is additive (new files, new optional manifest fields, new API action). Rollback is a revert of the new files/diffs with no data migration required, since existing exterior-only renders and existing API actions are untouched.

## Unresolved questions

1. Which text-to-3D vendor (Meshy / Tripo / Rodin / other) — needs a quick quality/cost trial before committing, and needs Rainer to provision the account/API key.
2. Final starter furniture-type list per room kind (bedroom, living, kitchen, bathroom, office) — draft list above, needs confirmation.
3. Does "style" (modern/classic) affect exterior materials too, or interior only? Determines whether exterior needs to render once per style or once total.
4. Target render resolution/format and where finished images are delivered (same `artifacts/` pattern as today's proofs, or a new location) — assumed same pattern unless told otherwise.
5. What is the actual target count for the reduced floorplan catalogue? Not required to start Phase 1, but affects how much to invest in the furniture library up front.

## Approval record

Not approved. Stop before implementation.
