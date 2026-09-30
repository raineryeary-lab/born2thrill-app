# Persistent render contract v1

Status: APPROVED / IMPLEMENTING

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make every render job compile its hard rules, exact Blender revision, approved references, approval state, and output requirements into one immutable hashed contract. Stop relying on chat memory, timestamps, directory scanning, or old generated images.

## Current evidence and behavior

- `scripts/make-codex-job.py` already produces `codex-job.json` and human-readable instructions.
- `scripts/blender-harness/export_invariants.py`, `scripts/verify_render_blend.py`, object ID masks, and the Workbench preflight route already provide parts of the required verification.
- Today the render operator can still select stale images or reconstruct prompts from conversation context. Hard rules can therefore be omitted even though the Blender source is correct.
- The worktree is heavily dirty with pre-existing modified and untracked files. All unrelated changes must be preserved.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- HEAD: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Merge base with `origin/agent/zuhausefinder-generator`: `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`
- Status: dirty before this plan; application, scripts, data, exports, docs, and plans contain extensive pre-existing user work. No unrelated file may be cleaned, overwritten, staged, or reformatted.

## Exact scope

1. Add a versioned global hard-rule policy and JSON schema.
2. Add a content-addressed reference registry with explicit roles and approval status.
3. Extend job creation to pin exact `.blend` SHA-256 values and compile an `effective-contract.json` with its own SHA-256.
4. Export a Blender scene snapshot containing camera, architecture, openings, furniture IDs/count/transforms, material-rule anchors, and mesh counts.
5. Add a CLI preflight that rejects stale/mismatched sources, unapproved references, old images, altered furniture, and missing hard-rule fields.
6. Require an approved master per floor before variants may start. Bind approval to contract, scene, master, and reference hashes.
7. Package only approved outputs belonging to the active contract.

## Files in scope

- `schemas/render-job.v1.schema.json` (new)
- `policies/zuhausefinder-hard-rules.v1.json` (new)
- `references/index.json` (new)
- `src/lib/floorplan-workbench/render-contract.mjs` (new)
- `scripts/render-contract.py` (new CLI)
- `scripts/blender-harness/export_invariants.py`
- `scripts/make-codex-job.py`
- `scripts/lieferung-pruefen.py`
- corresponding new or existing focused tests for these paths
- `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md` for follow-up tracking only

## Explicitly out of scope

- Changing floorplan geometry, annotations, corpus data, rights status, WordPress, email, deployment, or production configuration.
- Automatically accepting semantic image quality.
- Replacing the existing renderer or changing the four approved style definitions.
- Cleaning the dirty worktree or editing unrelated files.

## API, schema, and data-contract effects

`codex-job.json` gains a versioned contract section with pinned scene assets, approved reference asset IDs, policy version, protected invariants, required outputs, and `contract_sha256`. Generated companion files are `effective-contract.json`, `scene-snapshot.json`, `preflight.json`, `approval.json`, `postflight.json`, and `package-manifest.json`. Existing jobs remain readable; new guarded rendering requires the v1 contract.

## Acceptance criteria

- A job cannot render when its `.blend` differs from the pinned SHA.
- No input is selected by mtime, glob, “latest image,” or chat context.
- Every reference is addressed by ID and SHA and must be approved for its declared role.
- Architecture, camera, furniture count/position/rotation, wall color family, roof color exclusion, entrance-door material, and wall-light anchor rules are present in the effective contract.
- Variants cannot start until a master for that floor is approved against the same contract hash.
- Any source, reference, policy, or master change invalidates approval.
- Packaging excludes old, rejected, foreign-job, or unapproved images.
- Deterministic checks are reported separately from `human_required` visual review.

## Tests and verification commands

Add tests first for:

- stale or wrong Blender SHA rejected;
- unapproved/wrong-role reference rejected;
- foreign/old image rejected;
- furniture count, translation, or rotation mismatch rejected;
- absent warm-white-wall, no-red-roof, anthracite-door, and lintel-aligned-light rules rejected;
- variants rejected before master approval;
- approval invalidated by any bound hash change;
- package contains only active approved outputs.

Run focused Python tests, relevant Node tests, `pnpm exec tsc --noEmit --pretty false`, `pnpm run lint`, and `git diff --check`. Existing failures must be reported and must not be hidden or weakened.

## Protected and risky paths

- All data under configured `FLOORPLAN_WORKBENCH_DATA_DIR`, especially approved renders and Blender revisions.
- Existing untracked render scripts and tests are user-owned work.
- `scripts/make-codex-job.py` and `scripts/lieferung-pruefen.py` affect the handoff/publish boundary and require backwards-compatibility tests.

## Rights, provenance, privacy, and security impact

The contract records provenance and hashes but never changes commercial-rights eligibility. It stores no secret values. Reference assets are included in packages only when their declared usage permits it.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Rendering requires a green preflight bound to the approved corrected scene/reference hashes; packaging requires approval bound to the same contract. Publishing and email remain unchanged and separately gated.

## Customer, email, database, deployment, and external effects

None. This plan does not upload, publish, email, deploy, migrate, or alter production data.

## Failed-hypothesis log

None. The observed failure is architectural: chat-only rules are not persistent execution state.

## Rollback

Remove the new contract/schema/policy/registry modules and tests, and revert only the scoped integrations in job creation, invariant export, and delivery verification. Existing jobs and all user data remain untouched.

## Unresolved questions

- Exact initial approved reference asset IDs will be populated from already accepted renders during implementation; no new creative selection is part of this plan.
- Free ImageGen output still requires human master review because pixel/CV validation cannot prove semantic correctness.

## Approval record

Approved by user on 2026-09-15 ("fix it"). Implementation authorized.
