# bungalow_039 — six-image render package

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Create the complete presentation package for `bungalow_039` from the three newest Blender sources in `renders/go-baseline`: four geometry-locked interior style images and two geometry-locked exterior images, plus a searchable `catalog.json`. Do not upload or release anything to WordPress in this task.

## Current evidence and behavior

- Job: `bungalow_039-2026-08-20`
- Plan: `bungalow_039`
- Annotation hash: `69d37b4459e14b60629a4e4c797ac84248f48c8792ed412e774e5b280bf54176`
- The job contract lists exactly three sources for this one-storey house:
  - `interior-modern-baseline.blend`
  - `exterior-modern-baseline.blend`
  - `exterior-classic-baseline.blend`
- The readable contract requests one interior view and two exterior views. The approved complete handoff extends the interior source into four finish/style treatments while preserving one-floor geometry.
- Existing baseline PNG/depth/edge/mask files are references and technical passes, not the final presentation package.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Worktree is materially dirty with pre-existing modified and untracked files. They are user-owned and must not be cleaned, reformatted, committed, or overwritten by this task.
- Data/output tree: `C:\dev\Floorplan-tools\born2thrill-local-workbench-data` (separate durable project-data tree).

## Exact scope

1. Verify input SHA-256 values against `codex-job.json` immediately before rendering.
2. Render or extract clean reference frames from each Blender source without modifying the source `.blend` files.
3. Produce four interiors from the single `interior-modern-baseline.blend` geometry:
   - Warm Modern
   - Soft Scandinavian
   - Modern Architectural
   - Dark Modern
4. Produce two exterior hero images:
   - Modern
   - Contemporary Classic
5. Apply the prompt and hard-rule contract from `ZUHAUSEFINDER-COMPLETE-RENDER-AND-WORDPRESS-HANDOFF.md`.
6. Write a complete `catalog.json` with provenance and QC fields for all six images.
7. Preserve technical references and all existing files.

## Files in scope

Read-only inputs:

- `C:\dev\Floorplan-tools\born2thrill-local-workbench-data\corrections\bungalow_039\renders\go-baseline\codex-job.json`
- `...\interior-modern-baseline.blend`
- `...\exterior-modern-baseline.blend`
- `...\exterior-classic-baseline.blend`
- matching baseline PNG/depth/edge/mask files
- `C:\dev\publish-renders\ZUHAUSEFINDER-COMPLETE-RENDER-AND-WORDPRESS-HANDOFF.md`

New output directory only:

`C:\dev\Floorplan-tools\born2thrill-local-workbench-data\corrections\bungalow_039\renders\codex-final-2026-08-20\`

Expected new files:

- `01-interior-warm-modern.png`
- `02-interior-soft-scandinavian.png`
- `03-interior-modern-architectural.png`
- `04-interior-dark-modern.png`
- `05-exterior-modern.png`
- `06-exterior-classic.png`
- `catalog.json`
- `render-verification.md`

## Explicitly out of scope

- Editing source `.blend` files or canonical geometry.
- Creating an upper-floor image; this plan is a bungalow and has one interior source.
- Changing application code, scripts, tests, dependencies, configuration, database records, catalogue data, rights data, or approval state.
- WordPress upload, customer release, customer email, deployment, Git commit, or Git push.
- Using an older generated PNG as geometry source.

## API, schema, and data-contract effects

No API or application schema changes. `catalog.json` uses existing `visual-catalog-v1` fields and adds no new required field. Every asset records `geometry_source` and `geometry_reference_render`.

## Acceptance criteria

1. Exactly six final PNGs exist in the new output directory.
2. All six originate from the three job-listed Blender files whose hashes match `codex-job.json`.
3. The four interior images use the identical walls, openings, room layout, furniture function/placement envelope, camera and floor cut.
4. Interior images have a white/light-neutral studio ground with soft shadows and no exterior environment.
5. Dining furniture, kitchen, garderobe, sanitary elements and circulation comply with the handoff rules.
6. Both exterior images preserve building footprint, roof, openings, proportions and camera relationship.
7. Exterior paths/terraces connect logically; garden remains garden; lights and front door obey the handoff rules.
8. No black windows, floating elements, repeated-texture artifacts, displaced openings, invented entrances or cropped building parts.
9. `catalog.json` contains exactly six records with style, German description, palette, materials, features, QC, search text, geometry source and geometry reference.
10. No existing file is overwritten.

## Tests and verification commands

- Recompute input SHA-256 and compare with `codex-job.json`.
- Confirm source file timestamps before rendering.
- Confirm output file count is exactly six final PNGs plus the two sidecars.
- Confirm PNG files decode and have nonzero dimensions.
- Validate `catalog.json` parses and references six existing files.
- Compare every final image visually against its matching raw geometry reference for opening count/position, exterior silhouette and interior room boundaries.
- Record pass/fail per image in `render-verification.md`; do not label a failed image final.

No existing test will be changed, skipped, weakened or deleted.

## Protected and risky paths

- All existing files in `go-baseline` are protected and read-only.
- The dirty application worktree is protected and untouched.
- Existing generated images must not be silently reused as if they belong to this job.
- Image generation may hallucinate geometry; comparison against the raw Blender reference is mandatory.

## Rights, provenance, privacy, and security impact

No rights status changes. Rendering does not make a plan commercially eligible. The package remains internal until separately approved. No personal data or credentials enter prompts or output metadata.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. This task writes only a new internal render package tied to the explicit job sources and annotation hash. It makes no publishing, email, database, rights or application-code changes.

## Customer, email, database, deployment, and external effects

None. WordPress upload and customer release are explicitly excluded.

## Failed-hypothesis log

None at planning time. Stop after three distinct failed render/verification hypotheses and report the exact blocker.

## Rollback

The task is additive. Rollback consists only of moving the new `codex-final-2026-08-20` directory aside; no source file needs restoration.

## Unresolved questions

None. The output count and styles are fixed by the approved handoff.

## Approval record

Not approved. Stop before rendering.

