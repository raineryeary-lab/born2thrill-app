# Approved floorplan to WordPress proof of concept

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Keep all ten ZuhauseFinder questionnaire experiences and connect their shared structured result to a reusable approved-plan catalogue. Prove the path first with the existing approximately 140 m?, 1.5-storey HausKlar request, with no bungalow or two-storey fallback. The same catalogue contract must support one-, 1.5-, and two-storey plans.

## Current evidence and behavior

- WordPress already has ten distinct routes and a shared dmh-floorplan-brief-v1 output.
- WordPress already requests a JPEG and 1024x1024 geometry guide, then gates floorplan approval, guide-based exterior generation, image approval, and customer email.
- The Workbench now exports sanitized dmh-floorplan-approved-package-v3 packages from validated millimetre geometry with a reproducible public geometry hash.
- Baseline verification passed: Workbench 11/11, corrected fixture 4/4, generator 7/7, and WordPress PHP lint.
- The deployable app still hard-codes onehalfstorey_020 as internal-only. Its false rights flags correctly block WordPress delivery.
- Real reconstructed plan plan-caaccb688174a403 now has an eligible version-3 export and local catalogue entry.

## Repository baselines

- C:\dev\born2thrill-app-repo: branch fix/customer-floorplan-output, SHA a595ae37d3d6a2e01a35468cb66e4eb6bc756ee5; preserve existing governance edits, logs, docs, and plans.
- C:\dev\born2thrill-local-workbench: branch agent/zuhausefinder-generator, SHA 0c3255fa3f4d4d9c53dd5a5735078dc07e89c633; preserve the large user-owned dirty worktree.
- C:\dev\zuhausefinder-wordpress: branch agent/restore-hausprofil-wohnharmonie, SHA d9df2b3ab3b70324d3bbe1b08e10a6ed6a296d84; preserve untracked governance, plans, and artifacts.

## Exact scope

1. Add a deterministic app-side importer for a Workbench approved-package directory.
2. Reject missing or unexpected files, changed checksums, source assets, invalid geometry hashes, non-approved geometry, or missing explicit commercial eligibility.
3. Store only sanitized canonical plan data and approved metadata in a reviewable deployable catalogue.
4. Replace the hard-coded corrected-plan choice with exact-storey catalogue matching. Require requested room features, then rank by area closeness. Never cross storey categories.
5. Render JPEG and PNG guide from the same canonical JSON and return one geometry hash through the unchanged WordPress contract.
6. Keep all questionnaire code and WordPress manual gates unchanged.
7. Use synthetic packages for positive and negative tests; test data never enters the runtime catalogue.
8. After local verification, stop for the user's explicit rights decision on the real plan. Only a fresh eligible export may enter the visible proof.

## Files in scope

- New importer and importer tests under C:\dev\born2thrill-app-repo\scripts
- New src\lib\generator\approved-floorplan-catalog.ts
- New deterministic registry and approved canonical JSON directory under src\lib\generator\fixtures\approved
- Existing corrected-floorplan.ts
- The floorplan API route only if the catalogue contract needs a small integration adjustment
- Existing generator tests, package.json, and plans\ROADMAP.md

The approved contract revision adds the Workbench correction export route, correction hash helper/declaration, and export test to scope. WordPress runtime files remain unchanged.

## Explicitly out of scope

- Changes to the ten questionnaire routes, questions, copy, or scoring
- Free generation, room invention, variants, learning, voice, or automatic publication
- Simplifier/original-annotation changes or automatic rights decisions
- Database migrations, deployment, Railway, live WordPress, OpenAI calls, or email
- Real one- and two-storey production imports in this first proof; the generic catalogue/tests support them, then approved plans use the same path

## API, schema, and data-contract effects

- Keep dmh-floorplan-brief-v1 and dmh-floorplan-result-v2 unchanged.
- Accept dmh-floorplan-approved-package-v3 only in the local import command and reject legacy v1/v2 packages.
- Runtime entries use dmh-floorplan-approved-canonical-v1 plus immutable plan ID, revision, geometry hash, storey type, area, room features, rights scope, and hashes.
- No runtime endpoint accepts filesystem paths or packages.
- Commercial delivery flags may be true only after importer and runtime assertions pass.

## Acceptance criteria

1. All ten questionnaire routes remain present and unchanged.
2. Import is deterministic, rejects every invalid/unsafe case, and never copies annotations, PDFs, originals, or active content.
3. A 1.5-storey request selects only an eligible 1.5-storey plan; synthetic tests enforce the same for one and two storeys.
4. Bedrooms, office, guest WC, and HWR match before area ranking.
5. Output is a bounded valid JPEG with readable German labels; no customer SVG.
6. The 1024x1024 PNG guide and JPEG share the canonical geometry hash.
7. Internal-only geometry cannot pass the WordPress customer-delivery contract.
8. After separately authorized deployment, request ZF-20260730-8YIXG1LQ reaches floorplan_ready; exterior and email stay behind existing manual buttons.

## Tests and verification commands

Add import-contract tests, exact-storey/room/area/no-fallback tests, and JPEG/PNG/hash/UTF-8 tests. Preserve every existing test.

Run:
- node --test --test-isolation=none scripts\approved-floorplan-package.test.mjs
- node --test --test-isolation=none scripts\corrected-floorplan-fixture.test.mjs
- node --test --test-isolation=none scripts\zuhausefinder-generator.test.mjs
- pnpm exec tsc --noEmit --pretty false
- pnpm run lint
- pnpm run build
- WordPress PHP lint and a read-only ten-route check

## Protected and risky paths

Preserve every dirty/untracked file. Workbench data and annotations stay read-only except for a later explicit user export. The importer writes only to the approved-catalogue directory and rejects traversal, symlinks, unexpected or oversized files, and active content. WordPress code, media, database, SMTP, keys, and live site remain untouched.

## Rights, provenance, privacy, and security impact

No customer data enters the catalogue. Eligibility must be explicit in manifest and canonical plan and is never inferred from editing. Source assets stay local. Plan ID, revision, geometry hash, and artifact hashes remain auditable.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Import tests, runtime assertions, exact-storey matching, the existing WordPress contract validator, and all three manual gates enforce this.

## Customer, email, database, deployment, and external effects

None during implementation. Deployment, OpenAI generation, WordPress media import, and any internal test email need separate authorization after diff review.

## Failed-hypothesis log

- pnpm exec tsx --test was the wrong baseline command because tsx is absent; the existing Workbench command passed 11/11.
- App pnpm run tests hit sandbox EPERM during a pnpm status write; direct node --test passed.

## Rollback

Remove only the new importer/catalogue/tests and reverse the specifically approved edits. Never use broad reset, clean, or checkout. Workbench data and WordPress state are not altered.

## Unresolved questions

- Deployment and a live WordPress proof remain separately gated.
- Deployment and an internal email recipient are deferred.

## Approval record

Approved by the user on 2026-07-31: "Approved?implement the plan."
## Exact implementation blocker

The Workbench correction hash includes both the internal source reference ID and the correction schema. Export then removes that source ID and changes the schema while retaining the old hash. The sanitized receiver therefore lacks the inputs needed to recompute and verify the advertised geometry hash. Implementing the approved importer as written would either reject every real package or trust an unverifiable hash.

## Proposed contract revision

1. Add the Workbench export route and its existing export test to the in-scope files.
2. Export a new dmh-floorplan-approved-package-v3 contract.
3. Compute a public canonical geometry hash only from building, floors, and shared stair geometry after source fields are removed.
4. Use that same public hash in canonical-plan.json, massing.json, the JPEG footer, manifest.json, and the deployable runtime response.
5. Derive the public plan ID from the public hash.
6. Keep the internal correction hash and original annotation unchanged in local revision storage.
7. Make the deployable importer accept version 3 and reject legacy v1/v2 packages because their advertised geometry hash is not independently reproducible.
8. Add tests proving identical public hashes across Workbench export and deployable import, plus rejection when any geometry or artifact changes.

Historical blocker resolved by the approved version-3 public hash contract.
Contract revision approved by the user on 2026-07-31: "ok".

## Local implementation result

- COMPLETE: Workbench v3 public geometry hash and export contract.
- COMPLETE: deterministic package inspection/import with exact files, hashes, image formats, rights, approval, and sanitized-source gates.
- COMPLETE: deployable approved catalogue and exact 1/1.5/2-storey plus room-program matching.
- COMPLETE: existing JPEG and 1024x1024 PNG guide renderer now consumes the selected approved canonical JSON.
- COMPLETE: app type-check, app lint/build, Workbench focused lint/build, 8 package/matcher tests, 11 Workbench tests, 4 restricted-fixture tests, and 7 generator tests.
- UNCHANGED: all ten WordPress experiences and all manual floorplan, exterior, and email approval gates.
- COMPLETE: user-approved real reconstruction onehalfstorey_020 revision 4 exported/imported as plan-caaccb688174a403.
- COMPLETE: local API proof returned HTTP 200, exact 1.5-storey match, two floors, commercial eligibility, verified JPEG and PNG hashes.
