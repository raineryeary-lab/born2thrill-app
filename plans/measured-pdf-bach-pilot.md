# Measured PDF Pilot - BV Bach

Status: APPROVED - user said "well lets get started then" on 2026-07-31 after the measured-PDF workflow was presented.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Create the first local editable millimetre house from the three user-supplied measured PDFs in `G:\My Drive\_____grundrisse\untitled folder 2`, then produce a clean JPEG and Blender preview from the same canonical geometry.

## Source evidence

- `BV Bach_03_Erdgeschoss.pdf`: one-page measured ground floor.
- `BV Bach_05_Obergeschoss.pdf`: one-page measured upper floor.
- `BV Bach_06_Schnitt_Ansichten.pdf`: one-page section with floor heights and 22-degree gable roof.
- PDFs contain drawings rather than extractable text. Visual/vector inspection is authoritative; unreadable values remain unresolved and are never guessed.

## Exact scope

1. Record source paths, SHA-256 hashes, page roles and provenance without copying PDFs into Git.
2. Transcribe explicit room areas, storey levels, stair dimensions, roof pitch, wall/opening dimensions and dimension chains into a local measurement worksheet.
3. Create one millimetre canonical working copy only after the footprint scale and all geometry anchors are supported by explicit drawing dimensions or calibrated vector geometry.
4. Validate rooms, walls, wall-linked openings, entrance reachability and stair alignment.
5. Render JPEG and a Blender `.blend` plus preview from the same geometry hash.
6. Save revisions append-only and keep the result internal-only until separate rights and output approval.

## Files in scope

- This plan.
- New local-only source/measurement/revision records under the configured Workbench data directory.
- New measured-PDF importer, canonical fixture builder, Blender adapter/exporter, and their tests in the local Workbench.
- Workbench page/API changes strictly required to open, validate and approve this pilot.
- Canonical roadmap tracking.

## Out of scope

- WordPress, email, deployment, database, image APIs and customer delivery.
- Editing or copying the source PDFs.
- Processing the other 35 measured houses.
- Free generation, invented geometry, room swaps, learning or automatic commercial approval.
- Commit or push.

## Acceptance criteria

1. Source PDF hashes remain identical.
2. Every millimetre value records its source page and evidence type.
3. No unresolved dimension enters canonical geometry.
4. EG and OG share one aligned footprint/stair model.
5. Hard validation passes before render.
6. JPEG, Blender manifest and Blender scene share one geometry hash.
7. Original source and earlier revisions remain immutable.
8. Result stays internal-only and non-WordPress.
9. Existing tests are not weakened or removed.

## Tests

- Source hash and provenance test.
- Reject unresolved/unsupported dimensions.
- Canonical geometry determinism and validation tests.
- JPEG/Blender common-hash test.
- Blender headless export test.
- Append-only revision and delivery-block tests.
- Type-check, lint, build and existing Workbench suites.

## Floorplan-suite invariant

Can a changed path generate, publish or email geometry without an approved corrected corpus reference? No. This pilot is local-only, requires supported measurements and hard validation, and cannot publish or send.

## Protected paths

All source PDFs, Simplifier projects, prior annotations/revisions, credentials, customer data, WordPress, deployments, backups and existing dirty Workbench files.

## Rollback

Remove only new pilot files and targeted changes named by the final diff. Never use broad reset, clean or destructive deletion.

## Approval record

Approved by the user on 2026-07-31. No commit, push, deployment or external delivery is authorized.
