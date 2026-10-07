# Floorplan Generator handoff to Claude Code - 2026-08-02

## Objective

Build a reliable LOCAL demonstration for the next four weeks. Do not deploy now.

Required flow: questionnaire or preset -> match validated annotated reference -> clean JPEG -> geometry-faithful 3D/massing from the same geometry -> human review/correction.

Do not return to free generation or the old prototype.

## Correct active surfaces

- Current workbench: http://127.0.0.1:3020/floorplan-workbench
- Workbench health: http://127.0.0.1:3020/api/floorplan-workbench/health
- http://127.0.0.1:3011/testlauf is the OLD legacy UI. Never present it as the current demo.
- Port 3011 still hosts the main generator API.

## Repositories

Primary workbench:
C:\dev\born2thrill-local-workbench
Branch: agent/zuhausefinder-generator

Main app:
C:\dev\born2thrill-app-repo
Branch: fix/customer-floorplan-output
Observed base: cbd4be4480aafc775ea390e3b1991eede9672fef

Simplifier source corpus:
C:\Users\Admin\.codex\visualizations\2026\07\23\019f8e46-2742-7862-830e-a5fd850f472e\floorplan-simplifier-runtime

WordPress:
C:\dev\zuhausefinder-wordpress

All worktrees are dirty. Inspect status, full diff, and untracked files first. Never clean, reset, or overwrite user work. Original annotation/project files are immutable source records.

## Current corpus

- 370 project folders audited
- 310 exportable
- 295 quality-passed
  - 133 bungalows
  - 85 one-and-a-half-storey
  - 75 two-storey
  - 1 two-storey with cellar
  - 1 other
- 15 held for quality review
- 60 excluded: 44 status, 14 missing annotations, 2 missing training metadata

Current batch:
C:\dev\born2thrill-local-workbench\data\simplifier-v2

Audit:
C:\dev\born2thrill-local-workbench\data\simplifier-v2\batch-audit.json

Validated main-app copy:
C:\dev\born2thrill-app-repo\data\simplifier-v2

## Verified

- v2 handoff validates: 310 projects, 497 floors, 3072 rooms, 7205 elements.
- Workbench focused tests: 31/31 passed.
- Main focused tests: 15/15 passed.
- Main TypeScript, lint, and production build passed.
- Workbench default 1.5-storey query exposes 81 candidates.
- Forced expanded-pool main API test selected onehalfstorey_052, returned HTTP 200, and produced a 124149-byte JPEG.
- Normal approved-fixture test produced a 111618-byte JPEG and geometry guide.

## Important unresolved mismatch

The corpus contains normalized annotation geometry, not authoritative millimetre canonical geometry. Saved metadata does not contain overall width/depth for the current export.

Newer source PDFs can expose printed dimensions through offline PDF text extraction. Example:
C:\dev\vorlagen\2-geschosse\5.5.3_sv_170-2.pdf
pdfplumber extracted 10.25 m horizontal and rotated 10.25 m vertical.

An automatic dimension-recovery pass is possible but not implemented. Never guess scale silently. Keep normalized reference, recovered scale, corrected millimetre geometry, and commercial approval distinct.

## Batch files

Local workbench:
- scripts\batch-canonical-promotion.mjs
- scripts\batch-canonical-promotion.test.mjs
- scripts\harden-simplifier-export.mjs
- scripts\harden-simplifier-export.test.mjs
- data\simplifier-v2
- src\lib\training\simplifier-reference.ts
- plans\batch-canonical-promotion-v1.md

Main app:
- data\simplifier-v2
- scripts\current-corpus-handoff.test.mjs
- src\lib\training\simplifier-reference.ts
- plans\current-simplifier-batch-handoff.md
- plans\ROADMAP.md

Simplifier:
- scripts\export_generator_dataset.py
- tests\test_export_generator_dataset_encoding.py

## Backup

C:\dev\backups\zuhausefinder-batch-20260802-160915.zip
SHA-256: 957CFC1B7F505308355FA9929EA47E389F42B4ED5D47E25F8F30DA596F30AAE7

No credentials or raw source images are included.

## Rules

Read AGENTS.md and CLAUDE.md. Challenge this handoff against the real code before editing.

Do not deploy, send real email, migrate a database, change WordPress, grant commercial approval automatically, overwrite annotations, use free generation, return to the legacy UI, or weaken tests.

## Exact next task

Inspect only first.

Plan the smallest safe change making port 3020 Floorplan Workbench the single local presentation surface for:

- questionnaire input or three reliable demo presets
- matching from the 295 passed v2 references
- selected reference and match explanation
- clean JPEG preview
- current geometry-faithful 3D/massing preview
- human correction/review state

2D and 3D must share the same geometry/hash. Keep internal demo labeling. No production/customer-delivery work.

Before editing, create a plan with acceptance tests and report where this handoff disagrees with the code.

## Durable end-to-end target workflow

This section is mandatory context. The searchable catalogue is only the selection foundation; it is not the finished generator.

### Implemented catalogue foundation

- Generated catalogue: `C:\dev\born2thrill-local-workbench\data\simplifier-v2\search-catalog.json`
- Builder: `C:\dev\born2thrill-local-workbench\scripts\build-floorplan-search-catalog.mjs`
- Runtime loader/filter: `C:\dev\born2thrill-local-workbench\src\lib\training\floorplan-search-catalog.ts`
- Tests: `C:\dev\born2thrill-local-workbench\scripts\build-floorplan-search-catalog.test.mjs`
- Exact totals: 310 projects, 497 floors, 3,072 room polygons, 7,205 elements.
- Quality: 295 passed, 15 review-required.
- Current export rights remain unchanged: all 310 are internal-reference-only and zero are commercially eligible.
- Metric area remains explicitly unavailable until a verified scale source exists.

### Required local generation and evaluation chain

1. Match questionnaire or demo requirements against the catalogue.
2. Select an approved canonical plan before creating any variant.
3. Generate only constrained, rule-based variants derived from that plan:
   - room swaps or boundary adjustments within defined limits
   - approved entrance/Garderobennische and shower-niche rules
   - safe window/door adjustments
   - no free or prompt-only geometry generation
4. Validate every variant deterministically:
   - closed, connected walls
   - wall-linked doors and windows
   - valid room containment, coverage and circulation
   - aligned shared stair core
   - room-size, door-width and glazing rules
5. Score only valid variants with explainable criteria and expose the scoring details.
6. Require human selection and approval before any plan becomes reusable.
7. Store every revision separately; never overwrite the source annotation or an older approved revision.

### Schokoladenseite and camera contract

After floorplan approval, evaluate every exterior fa?ade from the approved geometry.

Score using:

- garden and terrace access
- importance and number of living/dining/kitchen openings
- useful symmetry and window alignment
- entrance composition
- balance of solid wall and glazing
- avoidance of utility-dominated fa?ades

Return:

- selected primary fa?ade
- neighbouring secondary fa?ade visible in perspective
- camera azimuth derived from those fa?ades
- horizontal viewing angle between approximately 28 and 45 degrees, never a flat 90-degree elevation
- camera height, target point and field of view
- explanation of why this fa?ade is the Schokoladenseite

The selection must be deterministic and stored, not only described in a text prompt.

### Geometry lock

The approved canonical JSON is the sole geometry source for:

- floorplan JPEG
- editable 2D view
- 3D/massing guide
- Blender scene or equivalent guide
- photorealistic exterior request

Create and retain one geometry hash covering footprint, storeys, walls, roof, doors, windows, stairs and relevant fa?ade openings. The 2D plan, 3D guide and exterior-rendering request must carry the same hash.

Do not maintain guessed 2D and 3D geometry separately.

### Exterior-rendering API payload

The rendering request must include structured data, not only prose:

- plan and revision IDs
- geometry hash
- locked footprint and storey heights
- roof type, pitch and orientation
- exact exterior doors and windows with fa?ade, position and dimensions
- selected Schokoladenseite and camera contract
- geometry-faithful guide image or scene
- questionnaire-derived style, materials, colours, landscape and mood
- explicit instruction that realism may improve but architecture must not change

The rendering response must retain the request ID, model/provider, prompt version, seed when available and geometry hash.

### Automatic exterior verification and human approval

Before catalogue publication:

1. Compare the rendered exterior with the geometry lock.
2. Reject or flag changed window/door counts, displaced openings, changed roof/building proportions or an incorrect camera side.
3. Present floorplan, 3D guide and exterior together for human review.
4. Require explicit approval.

### Catalogue enrichment after approval

Add an approved-result asset record to the catalogue containing:

- canonical plan ID and revision
- questionnaire/match profile
- floorplan JPEG path and checksum
- exterior JPEG path and checksum
- 3D/guide artifact path and checksum
- geometry hash shared by all artifacts
- Schokoladenseite fa?ade and camera parameters
- prompt/style version and rendering provenance
- validation and human-approval state
- rights and allowed usage scope

Never replace the searchable source-plan record. Link approved generated assets as revisions/derivatives.

### Later WordPress/customer flow

Only after the local chain is reliable:

1. WordPress questionnaire requests a catalogue match.
2. Service selects an approved plan/result or sends a new candidate to human review.
3. Only approved safe JPEG artifacts are returned.
4. Customer email receives floorplan and exterior JPEGs, not SVG or internal editing files.

### Current status versus target

Implemented now:

- v2 annotations and searchable catalogue
- reference matching foundations
- local correction/revision model
- shared geometry hash and deterministic 3D/massing foundation
- local validation and approval gates

Still pending:

- catalogue-driven selector in the Workbench UI
- reliable canonical millimetre conversion for the broad corpus
- constrained variant-generation/review interface
- automatic Schokoladenseite scoring and stored camera contract
- exterior API integration
- automatic geometry-faithfulness comparison
- approved asset records written back to the catalogue
- production WordPress delivery

Do not claim those pending stages are complete merely because prototype functions or an old renderer exist.

### Repeated non-negotiable presentation guardrails

- current geometry-faithful 3D/massing preview
- human correction/review state

2D and 3D must share the same geometry/hash. Keep internal demo labeling. No production/customer-delivery work.

Before editing, create a plan with acceptance tests and report where this handoff disagrees with the code.