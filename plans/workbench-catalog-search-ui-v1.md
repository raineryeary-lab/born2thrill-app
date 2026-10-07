# Workbench catalogue search UI v1

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Add a catalogue-driven filter/search panel and three fixed demo presets to the
port-3020 Floorplan Workbench so a questionnaire-style query (house type, floor
count, minimum room counts, program tags) can find and load a matching
already-approved reference, instead of only being able to step through
auto-derived "similar to whatever is currently loaded" candidates. This is
Phase 1 of a two-phase plan; Phase 2 (rule-based variant generation, automatic
scoring, and an external rendering API) is separate, future, and out of scope
here.

## Current evidence and behavior

- `src/app/floorplan-workbench/page.tsx` has no user-facing filter form. Its
  "Previous reference" / "Next reference" buttons cycle through
  `proof.reference_candidates`, which the `/api/floorplan-workbench/generate`
  route computes via `referenceLayoutCandidates()` in
  `src/lib/training/simplifier-reference.ts` — filtered by attributes of the
  *currently loaded* reference (house type, floors, bedroom/bathroom/office/
  guestWc/utilityRoom counts, basement, usage scope). There is no way to query
  by arbitrary criteria; you can only browse within whatever set the current
  reference happens to fall into. Confirmed live at
  `http://127.0.0.1:3020/floorplan-workbench` (read_page showed only
  Previous/Next, transform links, floor toggle, Better/Worse/Reject, and the
  geometry editor — no search/filter control).
- `src/app/api/floorplan-workbench/generate/route.ts` already accepts
  `?reference=<project_id>&transform=<t>` and independently re-validates
  `qualityStatus === "passed"`, `packageStatus === "training_ready"`, and
  `approvalStatus === "annotated_reference"` via `referenceLayoutById()`
  before returning a candidate (422 otherwise). This gate is the sole
  authority on what can render and will not be touched.
- `page.tsx`'s existing `selectReference(reference: string)` function already
  does everything needed to load an arbitrary `project_id`: it fetches
  `/api/floorplan-workbench/generate?reference=...`, loads any saved
  correction revision, and updates the URL — it just has no caller other than
  the Previous/Next buttons today.
- `src/lib/training/floorplan-search-catalog.ts` (Codex's verified, additive,
  untracked catalogue work — independently verified separately) exports
  `filterFloorplanCatalog(filters)` over 310 records with `houseType`,
  `habitableFloorCount`, `qualityStatus`, `usageScope`, `hasBasement`,
  `requiredTags`, `minimumRoomCounts`. It imports `data/simplifier-v2/
  search-catalog.json` (~1.5 MB) directly — fine server-side, too large to
  import into the existing `"use client"` page bundle as-is.
- `docs/HANDOFF-TO-CLAUDE-2026-08-02.md` (untracked, addressed to Claude)
  sets the exact next task as: preset/questionnaire input → match from the
  295 passed v2 references → selected reference + match explanation → JPEG
  preview → 3D preview → human review, explicitly forbidding free/variant
  generation. This plan implements that task using the already-verified
  catalogue as the query layer, with zero changes to the existing generation/
  rights gate.

## Repository baseline

- Repository: `C:\dev\born2thrill-local-workbench`
- Branch: `agent/zuhausefinder-generator`
- Base SHA: `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`
- Worktree is heavily dirty; every pre-existing modified and untracked file
  (including `docs/HANDOFF-TO-CLAUDE-2026-08-02.md`,
  `data/simplifier-v2/search-catalog.json`, and all files listed in the
  catalogue's own completed plan) is preserved unchanged.

## Exact scope

1. Add a new server route `src/app/api/floorplan-workbench/catalog-search/route.ts`
   that accepts query params mirroring `FloorplanCatalogFilters` (houseType,
   habitableFloorCount, qualityStatus, hasBasement, requiredTags as a
   comma-separated list, minimumRoomCounts as `room:count` pairs), calls
   `filterFloorplanCatalog()` server-side, and returns a compact JSON list
   (`project_id`, `house_type`, `habitable_floor_count`, `room_counts`,
   `program_tags`, `quality_status`) — never the full 1.5 MB catalogue to the
   client.
2. Add a filter panel to `FloorplanWorkbenchPage` (house type select, floor
   count select, a few common room-count minimums, tag checkboxes) that calls
   the new route and lists matches with a one-line "why this matched"
   summary (which filters/tags it satisfied).
3. Clicking a result calls the *existing* `selectReference(project_id)` —
   unchanged — which still goes through the existing gated
   `/api/floorplan-workbench/generate` endpoint before anything renders.
4. Add exactly three fixed demo presets (per the Claude handoff's "three
   reliable demo presets" language), each a canned filter query that is
   known to return at least one match, e.g. the proven HausKlar/1.5-storey/
   office+guest-WC+HWR combination plus two others chosen from the catalogue
   statistics (bungalow and two-storey) once confirmed non-empty against the
   live catalogue.
5. Previous/Next behavior is unchanged (still cycles the auto-derived
   `reference_candidates` for the loaded reference) — the new panel is
   additive, not a replacement.
6. Add `data/simplifier-v2/search-catalog.json`, `filterFloorplanCatalog`, and
   the new route/panel as read-only inputs; no edits to annotations,
   geometry, rights, quality, or approval fields anywhere.
7. Add a tracked row to `C:\dev\born2thrill-app-repo\plans\ROADMAP.md` for
   this task.

## Files in scope

- `src/app/api/floorplan-workbench/catalog-search/route.ts` (new)
- `src/app/api/floorplan-workbench/catalog-search/route.test.mjs` (new)
- `src/app/floorplan-workbench/page.tsx` (edit: add filter panel + preset
  buttons only; no change to existing Previous/Next, editor, review, or
  approval logic)
- `C:\dev\born2thrill-app-repo\plans\ROADMAP.md` (tracking row only)
- This plan file

## Explicitly out of scope

- Steps 1, 2, and 5 of the six-step pipeline: rule-based variant generation,
  automatic validation/scoring of variants, and any external rendering API
  call. Deferred to a separate Phase 2 plan.
- Any change to `/api/floorplan-workbench/generate`,
  `src/lib/training/simplifier-reference.ts` matching/gating logic, or the
  `/corrections` and `/reviews` endpoints.
- Any WordPress, live-site, email, SMTP, or database change.
- Any change to rights, approval, or quality status of any record.
- Editing annotations, geometry, or the contents of `search-catalog.json`
  itself.
- Free/AI image generation of any kind.

## API, schema, database, and artifact-contract effects

Adds one new read-only local API route returning a subset of existing
catalogue fields. No schema change to the catalogue, no database, no new
external calls.

## Acceptance criteria

1. The new `catalog-search` route returns only records that satisfy every
   supplied filter, using the exact same filter semantics as
   `filterFloorplanCatalog()` (no reimplementation of matching logic).
2. Selecting any result from the panel loads it through the existing,
   unchanged gated `/generate` endpoint — a filter match that fails the
   gate's quality/package/approval check still surfaces the existing 422,
   not a bypass.
3. All three demo presets return at least one match against the live
   catalogue and successfully load a candidate end to end.
4. Previous/Next and all existing Workbench functionality (editor, JPEG,
   Blender massing views, approve/reject, corrections) behave identically to
   today.
5. No existing test is weakened, skipped, or deleted.

## Tests and verification commands

- New: `node --test src/app/api/floorplan-workbench/catalog-search/route.test.mjs`
  covering: empty filters return all 310; each filter field narrows results
  correctly; combined filters intersect; unknown house type / tag returns
  empty, not an error; response never includes the full catalogue payload.
- Re-run unchanged: `node scripts/build-floorplan-search-catalog.test.mjs`,
  `node --test scripts/zuhausefinder-generator.test.mjs`,
  `node --test scripts/storey-model.test.mjs`.
- Manual: load `http://127.0.0.1:3020/floorplan-workbench`, run each of the
  three presets, confirm a candidate loads with correct quality/rights badges
  and that Previous/Next still works afterward.

## Protected and risky paths

No live-site, credential, SMTP, or database effects. No change to the
existing generation/rights gate. Purely additive local read-only query
surface plus UI.

## Rights, provenance, privacy, and security impact

None. The new route only re-exposes fields the catalogue already publishes
(project id, house type, floor count, room counts, tags, quality status) —
no rights upgrade, no new PII, no customer data.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

No. This plan only adds a query/filter layer over the existing catalogue and
reuses the existing, unchanged gated rendering endpoint. It cannot select or
render anything the current gate would not already have allowed by direct
`?reference=` navigation.

## Customer, email, database, deployment, and external effects

None. Local Workbench UI/API only; no deployment, no email, no external
network calls beyond what already exists.

## Failed-hypothesis log

None at proposal.

## Rollback

`git checkout -- src/app/floorplan-workbench/page.tsx` and delete
`src/app/api/floorplan-workbench/catalog-search/` to fully revert; no other
files are touched.

## Unresolved questions

Phase 2 (rule-based variant generation, scoring, façade/rendering pipeline,
generated-result cataloguing) is intentionally deferred to its own plan,
written and approved separately, after this narrower matching UI is working.

## Approval record

Approved by the user in chat on 2026-08-02: "Both, but in that order" (asked
directly whether the Claude-addressed handoff's narrower matching task or the
six-step generate/score/render pipeline governs), followed by explicit
confirmation "sure go ahead, and i want the bigger pipeline but the smaller
would do for now" — Phase 1 (this plan) implemented now, Phase 2 (the bigger
pipeline) to follow as a separate plan.
