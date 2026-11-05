# Publish `onehalfstorey_020` visual catalogue package

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Create one searchable local visual-catalogue entry for the eight accepted `onehalfstorey_020` renders, preserve their Blender/reference provenance, and rebuild the existing aggregate visual index.

## Current evidence and behavior

- Eight final images are staged in `C:\dev\publish-renders`.
- No `catalog.json` currently exists below `born2thrill-local-workbench-data\corrections\onehalfstorey_020`.
- `scripts/build-visual-catalog-index.mjs` only indexes per-project `catalog.json` files below the durable corrections data repository.
- The current aggregate index contains five records from one unrelated project and flags missing per-asset provenance on those older records.
- `scripts/publish-renders.py` is a WordPress uploader, not the local visual-catalogue importer; it is out of scope.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Pre-existing tracked modifications: `scripts/build-simplifier-render-plan.py`, `scripts/render-furnished-dollhouse.py`, `src/app/api/floorplan-workbench/corrections/route.ts`, `src/app/floorplan-workbench/page.tsx`.
- Numerous pre-existing untracked files/directories exist, including `data/visual-catalog`, `exports`, rendering scripts and plans. They are user-owned and must not be cleaned, overwritten or swept into this task.
- Durable data repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench-data`; only a new versioned render-delivery directory under `corrections\onehalfstorey_020\renders` is in scope.

## Exact scope

1. Create a versioned delivery directory under `corrections\onehalfstorey_020\renders`.
2. Copy the eight final PNGs non-destructively into that directory with stable descriptive names.
3. Add `catalog.json` using schema `visual-catalog-v1` with searchable German descriptions, style, floor, asset type, palette, materials, visible rooms/features, QC state and per-asset provenance.
4. Point every asset to the exact authoritative Blender source and exact baseline reference render.
5. Add a focused test for collection of the new catalogue records and the absence of missing-image/missing-provenance issues for this project.
6. Rebuild `data/visual-catalog/visual-search-catalog.json` using the existing builder.
7. Record the completed local-catalogue step and remaining WordPress/database work in the canonical roadmap.

## Files in scope

- New: `C:\dev\Floorplan-tools\born2thrill-local-workbench-data\corrections\onehalfstorey_020\renders\visual-catalog-2026-08-18\catalog.json`
- New: eight PNG files in that same directory.
- New: `C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\build-visual-catalog-index.test.mjs`
- Generated update: `C:\dev\Floorplan-tools\born2thrill-local-workbench\data\visual-catalog\visual-search-catalog.json`
- Update: `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md`

## Explicitly out of scope

- No WordPress upload or publication.
- No customer email or automatic sending.
- No database migration or production catalogue update.
- No image regeneration, Blender modification, geometry change or render replacement.
- No changes to `scripts/publish-renders.py`, routes, UI, generator, questionnaire matching or approval gates.
- No claim that render acceptance changes source rights or commercial eligibility.

## API, schema, and data-contract effects

- Reuses existing `visual-catalog-v1` and `visual-catalog-index-v1` contracts.
- Adds optional searchable fields already preserved by the index builder: `floor`, `house_type`, `storeys`, `geometry_source`, `geometry_reference_render`, `geometry_lock`, and `rights_scope`.
- No runtime API shape changes.

## Acceptance criteria

- Eight `onehalfstorey_020` records appear in the aggregate index.
- Every record has a unique `asset_id`, existing image file, `geometry_source`, `geometry_reference_render`, description and QC status.
- Records are searchable by project, style, floor, room/features and exterior/garden terms through index data.
- The new project contributes zero missing-image, duplicate-ID or missing-provenance issues.
- Existing catalogue records remain unchanged except for deterministic aggregate-index regeneration.
- No geometry, email, WordPress or approval state is changed.

## Tests and verification commands

- Add `scripts/build-visual-catalog-index.test.mjs` covering the new catalogue collection and provenance checks.
- `node --test --test-isolation=none scripts/build-visual-catalog-index.test.mjs`
- `node scripts/build-visual-catalog-index.mjs`
- `node scripts/build-visual-catalog-index.mjs --check`
- `git diff --check`
- Inspect final `git status --short` and scoped diffs.

No existing test may be deleted, skipped, weakened or rewritten.

## Protected and risky paths

- All original annotations, canonical geometry, baseline Blender files and baseline PNGs are read-only.
- Existing dirty and untracked files are protected.
- The aggregate index is generated only by the existing deterministic builder.
- The WordPress uploader is protected and not executed.

## Rights, provenance, privacy, and security impact

- Each asset records exact Blender and reference-render provenance.
- `rights_scope` remains local/internal catalogue metadata unless an independent rights decision already exists elsewhere.
- No credentials, customer information or personal data are added.
- No source image or annotation is published.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. This task adds static render metadata and a deterministic local index only. It does not touch generation, publication, WordPress or email paths. Tests verify image/provenance integrity, while the authoritative Blender/reference paths remain tied to `onehalfstorey_020`.

## Customer, email, database, deployment, and external effects

None. WordPress publication, real database import, deployment and customer sending remain separate future actions requiring separate authorization.

## Failed-hypothesis log

- Hypothesis: `C:\dev\publish-renders` could be indexed directly. Evidence: index builder scans only durable corrections directories for `catalog.json`. Conclusion: stage a versioned per-project delivery instead.
- Hypothesis: `scripts/publish-renders.py` is the local importer. Evidence: it uploads media to WordPress using credentials. Conclusion: do not execute or modify it for this task.

## Rollback

Delete only the newly created versioned delivery directory, remove the new focused test, restore the generated aggregate index to its pre-task content, and revert only the roadmap lines added by this task. Do not touch any pre-existing files.

## Unresolved questions

None for the local catalogue step. WordPress publication and production database import remain explicitly out of scope.

## Approval record

Not approved. Stop before implementation.
