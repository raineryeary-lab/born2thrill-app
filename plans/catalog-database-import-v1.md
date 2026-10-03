# Import floorplan search catalog into relational Postgres storage

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Complete roadmap item `CATALOG-DATABASE-001`: import the existing, verified
floorplan search catalog (JSON) into relational Postgres storage so it can be
queried operationally instead of loaded as a flat file. This plan covers
schema + import script + verification only. It does **not** wire the catalog
into the live `/questionnaire` matching flow — Rainer explicitly scoped this
round to "just get the catalog into a real DB." Matching logic itself already
exists elsewhere (see Current evidence); wiring saved questionnaire answers
into it is separate future work, and is the next roadmap item after this one.

## Current evidence and behavior

- `born2thrill-local-workbench/scripts/build-floorplan-search-catalog.mjs`
  already batch-builds `data/simplifier-v2/search-catalog.json` from all
  projects: 310 projects / 497 floors / 3,072 rooms / 7,205 elements,
  1,532,809 bytes on disk today. Each record (`projectRecord`, :122-183) has
  27 top-level fields including rights/provenance fields
  (`source_rights_status`, `usage_scope`, `commercial_generator_eligible`,
  `reconstruction_only`, `approval_status`, `quality_status`,
  `annotation_sha256`) plus nested `floors[]`, `derived_counts{}`,
  `program_tags[]`. The script has a `--check` mode (:262-267) that
  byte-compares regenerated output against disk — this is the existing
  "verified/deterministic" guarantee the roadmap refers to.
- `born2thrill-app-repo/plans/ROADMAP.md:37` — `CATALOG-DATABASE-001` is
  PENDING: *"Evaluate importing the verified JSON catalogue into relational
  persistence for operational searching... Next gate: Separate schema/
  migration plan and explicit approval."* This document is that gate.
- `born2thrill-app-repo` already has Postgres access two ways: a raw `pg`
  `Pool` reading `DATABASE_URL` (`src/lib/db/postgres.ts:1-32`, used by
  `src/app/questionnaire/actions.ts:99` to write the `projects` table), and
  a Supabase client (`src/lib/supabase/server.ts`) still used for auth reads.
  **Resolved (Codex-verified 2026-08-16):** `DATABASE_URL` and the Supabase
  Postgres instance are two separate databases, not the same one.
  `.env.example:5` labels `DATABASE_URL` explicitly "Railway PostgreSQL";
  `docs/railway-migration.md:51,105` documents a deliberate split — data
  writes (including `projects.requirements`) go through Railway Postgres via
  `DATABASE_URL`, Supabase is retained only for Auth/Storage. A parallel
  migration tree at `railway/migrations/` already exists specifically
  because Supabase's migrations depend on `auth.users`/`auth.uid()`/the
  `storage` schema, which don't exist on Railway
  (`docs/railway-migration.md:69,215`). The runner is
  `scripts/run-migration.mjs:7`, which applies against `DATABASE_URL` and
  defaults to `railway/migrations/001_initial_schema.sql`. Therefore this
  new table's migration belongs in `railway/migrations/`, run via
  `run-migration.mjs`, **not** `supabase/migrations/` — Unresolved Question
  #1 from the original draft is resolved.
- Existing migrations: Supabase side —
  `supabase/migrations/202606220001_initial_schema.sql` (profiles, projects,
  floorplan_uploads, generation_jobs, generated_outputs + RLS) and
  `202606300001_training_uploads.sql`. Railway side —
  `railway/migrations/001_initial_schema.sql` and
  `railway/migrations/002_training_upload_review.sql`. No existing table on
  either side resembles a catalog/search store.
- No customer-identifying fields exist in the catalog record schema (checked
  against AGENTS.md's rights/provenance rules).
- **Correction (Codex-verified 2026-08-16):** matching/filtering logic
  already exists in two places — `selectApprovedFloorplan()`
  (`src/lib/generator/approved-floorplan-catalog.ts:174`, matches a
  `HouseBrief` to approved plans by storey/bedrooms/office/guest-WC/utility +
  area ranking) and a filter API over the JSON catalog in
  `born2thrill-local-workbench`
  (`src/lib/training/floorplan-search-catalog.ts:57`,
  `src/app/api/floorplan-workbench/catalog-search/route.ts:19`). The actual
  gap is narrower than "build matching from scratch": nothing yet reads a
  saved `projects.requirements` row and feeds it into either matcher. That
  bridge, not a new matcher, is the real next roadmap item after this plan.

## Repository baselines

- `born2thrill-app-repo`: git repo, branch `fix/customer-floorplan-output`,
  HEAD `289d0946eb34819a4287fefaa3db705c867ffd3d`, clean working tree.
- `born2thrill-local-workbench`: git repo, branch
  `agent/furnished-render-and-annotation-schema`, HEAD
  `5be1a4e18956b9fb2e158bee82aa159898356e89`, **dirty** (pre-existing, from
  prior approved exterior-render work, not part of this task — must not be
  touched or cleaned):
  - modified: `scripts/build-simplifier-render-plan.py`
  - untracked: `plans/exterior-wall-light-head-alignment-v1.md`,
    `scripts/bpypolyskel/`, `scripts/comfyui-polish-exterior-rule.test.py`,
    `scripts/comfyui-polish-exterior.py`, `scripts/composite-mask-polish.py`,
    `scripts/render-exterior.py`

## Exact scope

1. New Postgres migration (Railway side, `railway/migrations/003_floorplan_catalog.sql`,
   applied via `scripts/run-migration.mjs`) creating one additive table,
   `floorplan_catalog_projects`, holding indexed scalar filter columns
   (house_type, floor_count, habitable_floor_count, has_basement,
   room_polygon_count, element_count, quality_status, approval_status,
   usage_scope, source_rights_status, commercial_generator_eligible,
   reconstruction_only, program_tags as text[]) plus the full per-project
   record as JSONB (`catalog_record`) and import metadata
   (`source_dataset_version`, `annotation_sha256`, `imported_at`).
   JSONB is canonical/source-of-truth per record; scalar columns are a
   queryable projection, matching the suite's "canonical JSON is the single
   geometry source" rule extended to catalog metadata.
2. New idempotent Node script,
   `born2thrill-app-repo/scripts/import-floorplan-catalog.mjs`, that reads
   `search-catalog.json` from a given path, validates `schema` and `totals`
   against the file's own header, and upserts rows
   (`INSERT ... ON CONFLICT (project_id) DO UPDATE`) inside one transaction
   via `DATABASE_URL`. Supports `--dry-run` (report planned
   inserts/updates/removals, write nothing) and `--check` (fail if DB row
   count / dataset version doesn't match the source file, mirroring the
   existing catalog script's `--check` convention).
3. New verification script/test asserting: row count equals
   `totals.projects` in the source JSON; for a sample of project_ids, every
   rights/provenance field in the DB matches the JSON byte-for-byte; a
   second run of the import script is a no-op (idempotency).
4. Update `ROADMAP.md` `CATALOG-DATABASE-001` row to COMPLETE with evidence
   once verified.

## Files in scope

- NEW `born2thrill-app-repo/railway/migrations/003_floorplan_catalog.sql`
- NEW `born2thrill-app-repo/scripts/import-floorplan-catalog.mjs`
- NEW `born2thrill-app-repo/scripts/import-floorplan-catalog.test.mjs`
- MODIFY `born2thrill-app-repo/plans/ROADMAP.md` (status line only, after verification)
- READ-ONLY: `born2thrill-local-workbench/data/simplifier-v2/search-catalog.json`,
  `born2thrill-local-workbench/scripts/build-floorplan-search-catalog.mjs`
  (neither is modified by this plan)

## Explicitly out of scope

- Wiring the catalog to the live `/questionnaire` matching flow, its UI, or
  `actions.ts` (separate future plan, per Rainer's explicit scope choice)
- Any change to `projects` table, auth, or RLS beyond the new table's own policy
- Resolving the Supabase-vs-Railway-Postgres hybrid architecture generally —
  this plan only places one new table on the Railway side, which the wider
  `docs/railway-migration.md` migration already establishes as where data
  tables (including `projects`) live
- Building a new questionnaire-to-catalog matcher — two matchers already
  exist (`selectApprovedFloorplan()` and the workbench catalog-search API);
  wiring saved `projects.requirements` into one of them is separate future work
- Actually running the migration or import script against the real/production
  database — see "Customer, email, database, deployment, and external effects"
- Recurring/automated sync (cron, webhook) of the catalog into the DB; this is
  a manually-rerun script only
- Deleting or archiving the JSON catalog file (it remains the source of truth
  the DB is imported from and re-verified against)

## API, schema, and data-contract effects

Purely additive: one new table, no changes to existing tables, no new or
changed API routes. No breaking change to any existing contract.

## Acceptance criteria

- Migration applies cleanly to a local/scratch Postgres instance and has a
  documented, tested rollback (`DROP TABLE floorplan_catalog_projects`).
- `import-floorplan-catalog.mjs` run against the current
  `search-catalog.json` produces exactly 310 rows.
- Spot-check of 10 sampled `project_id`s: rights/provenance fields identical
  between JSON source and DB row.
- Re-running the import script twice in a row leaves row count and content
  unchanged (idempotent upsert, not duplicate rows).
- `--dry-run` reports counts without writing; `--check` exits non-zero on
  drift between DB and source file.

## Tests and verification commands

New tests:
- `scripts/import-floorplan-catalog.test.mjs` — schema validation, upsert
  idempotency, rights-field fidelity, dry-run no-op behavior (run against a
  local/scratch Postgres, not production).

Manual verification commands (documented in the script's own `--help`):
- `node scripts/run-migration.mjs railway/migrations/003_floorplan_catalog.sql` (against scratch DB only during this phase)
- `node scripts/import-floorplan-catalog.mjs --dry-run <path-to-catalog.json>`
- `node scripts/import-floorplan-catalog.mjs <path-to-catalog.json>` (against scratch DB only during this phase)
- `node scripts/import-floorplan-catalog.mjs --check <path-to-catalog.json>`

No existing tests are touched.

## Protected and risky paths

- `railway/migrations/` — schema changes are hard to reverse once applied
  to a live database; migration must be reviewed before any real
  `run-migration.mjs` run against the production `DATABASE_URL`.
- `DATABASE_URL` / `.env` — script must read from environment only, never
  log or print the connection string or credentials.

## Rights, provenance, privacy, and security impact

No customer-identifying fields exist in the catalog schema. Rights/
provenance fields (`source_rights_status`, `usage_scope`,
`commercial_generator_eligible`, `reconstruction_only`, `approval_status`,
`quality_status`) must be copied verbatim, never recomputed or defaulted by
the import script. Per AGENTS.md: importing a record into this table does
not itself grant or change commercial eligibility — `commercial_generator_
eligible` stays whatever the source JSON already says.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

**No.** This path only copies already-verified catalog metadata (produced
by the existing, separately-governed `build-floorplan-search-catalog.mjs`)
into a differently-shaped read store. It generates no new geometry, performs
no publication, and sends no email.

## Customer, email, database, deployment, and external effects

**Database: yes, by design** — this plan's entire purpose is a new table and
an import script that writes to Postgres. Per AGENTS.md item 10 ("do not...
migrate a database... unless separately authorized"), approving this plan
document authorizes **writing and testing** the migration/script against a
local or scratch Postgres instance only. Actually applying the migration or
running the import against the real `DATABASE_URL` used by the live app
requires a **separate, explicit go-ahead at that moment** — this plan does
not pre-authorize that step.

No customer email, no deployment, no other external system touched.

## Failed-hypothesis log

None yet — pre-implementation.

## Rollback

- `DROP TABLE IF EXISTS floorplan_catalog_projects;` (migration is additive
  only; no other table is altered).
- Delete `scripts/import-floorplan-catalog.mjs` and its test file.
- Revert the `ROADMAP.md` status-line edit.

## Unresolved questions

1. ~~Which Postgres does this table belong in?~~ **Resolved** (Codex-verified
   2026-08-16, see Current evidence): `DATABASE_URL` is Railway Postgres,
   separate from Supabase. Migration goes in `railway/migrations/`, applied
   via `scripts/run-migration.mjs`.
2. Proposed table name `floorplan_catalog_projects` — confirm or rename.
3. Scalar column choice assumes future filters will mirror what the
   read-only Workbench catalog UI already filters on (house_type,
   floor_count, room counts, program_tags) — flagging in case that's wrong.
   Now reinforced by evidence: this is exactly what
   `floorplan-search-catalog.ts:57` already filters on, and what
   `selectApprovedFloorplan()` needs (storey type, bedroom/office/guest-WC/
   utility counts, area) — so the scalar columns should cover the union of
   both matchers' filter fields, not just the Workbench UI's.

## Approval record

Not approved. Stop before implementation.
