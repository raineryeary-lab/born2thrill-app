# Floorplan search catalog v1

Status: COMPLETE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Derive a deterministic, searchable local catalogue from the existing Simplifier v2 annotations without modifying any source annotation or inventing metric dimensions. The catalogue will expose room counts, house/floor types, program tags, relative room shares, elements, quality, approval, provenance, and rights eligibility for each plan.

## Current evidence and behavior

- `data/simplifier-v2/dataset.json` contains 310 projects, 497 floors, 3,072 named rooms, and 7,205 elements.
- Rooms already have `room_id`, expanded `room_ids`, labels, normalized polygons, and `area_ratio`.
- `src/lib/training/simplifier-reference.ts` already calculates in-memory room counts for matching but does not publish a durable catalogue or summary record per project.
- The export does not consistently contain authoritative `area_m2`; square metres must not be invented from normalized polygons.
- 55 restricted references remain separately identified in `reconstruction-dataset.json` and must remain non-commercial.

## Repository baseline

- Repository: `C:\dev\born2thrill-local-workbench`
- Branch: `agent/zuhausefinder-generator`
- Base SHA: `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`
- The worktree is heavily dirty with existing user work; every pre-existing modified and untracked file must be preserved.

## Exact scope

1. Add a deterministic catalogue builder that reads Simplifier v2 JSON only.
2. Produce one summary per project containing:
   - project and house type
   - floor count and floor levels
   - counts by normalized room ID
   - derived bedroom, child-room, bathroom, office, guest-WC, HWR/HTR, pantry, dressing, hobby, garage/carport, balcony, terrace, and roof-terrace counts
   - present room/program tags
   - door, opening, window, stair, balcony, and roof-terrace counts
   - per-floor room IDs and relative marked-area shares
   - quality, approval, usage scope, rights, reconstruction-only, commercial eligibility, and annotation hash
   - explicit metric-area status: `unavailable` unless an authoritative metric source exists
3. Add catalogue statistics and a discrepancy list for empty floors, unknown room IDs, mojibake labels, stair mismatches, and missing quality/rights metadata.
4. Write `data/simplifier-v2/search-catalog.json` deterministically.
5. Add a read-only TypeScript/JavaScript loader and filters for house type, floor count, minimum room counts, required tags, quality, and usage scope.
6. Add tests proving counts and rights filters against known dataset projects.
7. Track remaining metric-scale enrichment and relational-database import as separate roadmap follow-ups.

## Files in scope

- `scripts/build-floorplan-search-catalog.mjs`
- `scripts/build-floorplan-search-catalog.test.mjs`
- `src/lib/training/floorplan-search-catalog.ts`
- `data/simplifier-v2/search-catalog.json`
- `package.json` only to add build/test commands
- `C:\dev\born2thrill-app-repo\plans\ROADMAP.md` tracking only
- This plan file

## Explicitly out of scope

- Editing annotations, polygons, doors, windows, stairs, canonical geometry, JPEGs, 3D, Blender, WordPress, email, SMTP, Railway, Supabase, PostgreSQL, or live deployments
- Converting normalized coordinates to millimetres or square metres without an authoritative scale
- Changing approval or commercial-rights status
- Creative generation, plan variants, automatic publication, or customer delivery

## API, schema, and data-contract effects

Adds local schema `zf-floorplan-search-catalog-v1`. Existing Simplifier files and loaders remain unchanged. No database migration or public API change.

## Acceptance criteria

1. Exactly 310 project summaries are generated from the current v2 dataset.
2. Project, floor, room, and element totals reconcile with `manifest.json`.

## Completion record

Status completed on 2026-08-02.

- Generated catalogue totals: 310 projects, 497 floors, 3,072 room polygons, 7,205 elements.
- New catalogue tests: 6 passed.
- Existing focused generator/workbench regression tests: 21 passed.
- TypeScript: passed.
- Focused catalogue lint: passed.
- Full repository lint remains blocked by seven pre-existing `no-explicit-any` errors in `src/lib/generator/facade-analysis.d.ts` and `src/lib/generator/floorplan-rulebook.d.ts`; neither file was changed.
- Deterministic `--check`: passed.
3. Room counts are derived from normalized room IDs, including combined-room annotations without double-counting the same semantic room within one polygon.
4. Every catalogue record exposes rights and quality status; restricted references cannot pass a commercial-only filter.
5. No record contains invented `area_m2` values.
6. Output is byte-stable for unchanged source data.
7. Unknown or malformed labels are reported, not silently mapped.

## Tests and verification commands

- `node --test --test-isolation=none scripts/build-floorplan-search-catalog.test.mjs`
- `node scripts/build-floorplan-search-catalog.mjs --check`
- `pnpm exec tsc --noEmit --pretty false`
- `pnpm run lint`
- Existing focused Simplifier and generator tests remain unchanged and must still pass.

## Protected and risky paths

All original Simplifier runtime projects, source PDFs/images, annotations, current v1/v2 datasets, canonical candidates, generated artifacts, credentials, and dirty user files are protected. The builder may only read existing data and replace its own generated catalogue.

## Rights, provenance, privacy, and security impact

No rights upgrade. Every output record copies the source rights/provenance state. Restricted records remain internal-only and non-commercial. No customer identity or raw floorplan image is included.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. This task generates metadata only; tests prohibit geometry generation, publication, email, and rights changes.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

None.

## Rollback

Remove only the new builder, loader, test, generated search catalogue, package commands, and roadmap entry. Existing datasets remain untouched.

## Unresolved questions

Metric square metres require a later authoritative-scale pass. Relational database import is deliberately deferred until the JSON catalogue is verified.

## Approval record

Approved by the user on 2026-08-02: "Approved?implement the catalogue, dont screw it up".
