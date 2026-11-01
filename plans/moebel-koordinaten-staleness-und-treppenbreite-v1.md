# Möbel save-time staleness guard, legacy-space refusal, and stair-width unification

Status: COMPLETE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-09-18, after `twostorey_047`'s Möbel tab showed doubled/ghosted
room labels and every piece of furniture in the wrong room: *"i think there
are many flaws especially in the scaling between the different tabs i think
this has to be standardised and simplified."* Followed by an explicit
instruction to run a full Codex architecture review of the coordinate-space
handling, then: *"can you two guys do this and fix it and test it i have some
stuff to do, just get it to work."*

This is not a full rewrite to Codex's proposed single-canonical-space
architecture (that is a separate, larger follow-up — see `Unresolved
questions`). It closes the specific, evidence-backed gaps Codex found that
(a) actually caused `twostorey_047`'s furniture to end up reflected into the
wrong rooms and (b) let that corruption go undetected by an already-existing
safeguard, plus one independently-confirmed stair-geometry disagreement.

## Current evidence and behavior

Full Codex read-only audit: `C:\Users\Admin\AppData\Local\Temp\claude\...\
093f2b6e-b6aa-4a53-b9cc-8deb1ef9db0b\scratchpad\codex-out-coordinate-spaces.md`
(brief at the sibling `codex-brief-coordinate-spaces.md` in the same
directory). Ten findings; four are addressed here.

1. **`twostorey_047`'s furniture was reflected, not just stale.** Point-in-
   polygon check (own script, cross-checked by Codex) against a fresh
   `geometry_only()` run: all 21 groundfloor items and all 17 upperfloor
   items landed in the wrong room — kitchen appliances in the WC/HWR, the
   dining table over the stairs, both living-room sofas + TV in the guest
   room, bathroom fixtures in a child's room, etc. Applying `y -> lo + hi -
   y` once (the SAME extents already in use, `groundfloor` 1373.2..11278.8,
   `upperfloor` 1613.2..11038.8 — **unchanged** from two days ago, so this
   is not a re-annotation) puts every single item back into a sensible
   room. This is exactly a double-reflection: the file was corrected once
   (2026-09-16, `MOEBEL-KOORDINATEN-DOPPELT-GESPIEGELT-001`) and has since
   been flipped again by a normal Save.
2. **Root cause: `saveFurniture()` (`corrections/route.ts`) always
   recomputed the CURRENT room-geometry identity at save time and stamped
   that**, regardless of what identity the Möbel tab actually had loaded and
   displayed when the furniture was placed. The existing staleness gate on
   the BUILD side (`workbench_furniture()`, comparing `geometry_identity`
   against `level_geometry_identity()`) can only ever catch a mismatch
   against what's ON DISK — a save that re-stamps a fresh, correct-looking
   identity onto coordinates that were actually placed against an older
   display defeats it completely. Confirmed: the file's stamped identity
   matched today's geometry exactly, so the existing check stayed silent
   while every item stood in the wrong room.
3. **`normalizeFurnitureDocument()` (`furniture-document.mjs`) unconditionally
   overwrote any incoming `coordinate_space` with the current one.** The
   client (`useFurniture()` in `furniture.tsx`) spreads the loaded document
   forward on every save (`{...current, symbols: ...}`), so a file still
   labelled `LEGACY_RENDER_SPACE` would survive to a save call and come back
   out mislabelled as fully migrated, without a single coordinate having
   been transformed — masking exactly the state
   `build-simplifier-render-plan.py`'s reader already refuses to build.
4. **Stair width disagreed between the Möbel tab and the real build on
   upper floors.** `geometry_only()` called `annotation_stair_core()` with
   the CURRENT floor's own frame (a `RegisteredFrame` for an upper storey)
   even though that function always reads the GROUND floor's own raw
   points — feeding ground-native normalized coordinates through a
   registration affine that was built to convert the OTHER direction.
   Measured: real build (`shared_stair_core`) 900mm / 1415.5mm (`_047`,
   this house's stair is not the 900mm default); Möbel tab's own
   upper-floor view showed 1049.4mm / 1021.6mm respectively — a real,
   silent disagreement between what the furniture editor shows you're
   clearing and what actually gets built.

## Repository baselines

* Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
* Branch: `agent/furnished-render-and-annotation-schema`
* Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
* Pre-existing dirty/untracked state: extensive (216 changed paths at start
  of this task per `git status --porcelain`), matches the state recorded in
  `plans/stair-geometry-rebuild-v1.md` and later plans in this directory.
  Files this task touches were already dirty (`build-simplifier-render-
  plan.py`, `corrections/route.ts`, `floorplan-workbench/page.tsx`) or
  already untracked (`furniture.tsx`, `furniture-document.mjs`,
  `furniture-document.test.mjs`) before this task started.
* Data repo: `E:\born2thrill-local-workbench-data` (furniture JSON, not
  under Git).

## Exact scope

1. `geometry_only()` emits a `geometry_identity` per floor (the SAME
   `level_geometry_identity()` the build's own staleness check already
   uses), and always sources its per-floor stair from the GROUND frame +
   `ground_level`, matching the full build's `shared_stair_core` exactly.
2. The client captures that per-floor identity the moment it loads/displays
   geometry and sends it back on save as `displayed_geometry_identity`.
3. `saveFurniture()` rejects (409) a save whose `displayed_geometry_identity`
   disagrees with the freshly-computed current one, instead of silently
   re-stamping.
4. `normalizeFurnitureDocument()` refuses (throws) a save whose incoming
   `coordinate_space` is set to anything other than the current
   `RENDER_COORDINATE_SPACE` — in particular the legacy space — instead of
   relabelling it.
5. `twostorey_047`'s two furniture files are corrected (re-flipped once) and
   verified back into their correct rooms.

## Files in scope

* `scripts/build-simplifier-render-plan.py` — `geometry_only()`: stair
  source frame fix, new `geometry_identity` field per floor.
* `src/app/api/floorplan-workbench/corrections/route.ts` — `saveFurniture()`
  staleness rejection.
* `src/lib/generator/furniture-document.mjs` — `normalizeFurnitureDocument()`
  legacy-space refusal.
* `src/app/floorplan-workbench/page.tsx` — feeds the displayed floor's
  `geometry_identity` into the furniture hook whenever it changes.
* `src/app/floorplan-workbench/furniture.tsx` — `useFurniture()`: ref +
  setter for the displayed identity, sent on save.
* `scripts/furniture-document.test.mjs` — new tests for the legacy-space
  refusal.
* `E:\born2thrill-local-workbench-data\corrections\twostorey_047\furniture\
  floor-0.json`, `floor-1.json` — data correction.
* This plan file; `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\
  ROADMAP.md` — completion record.

## Explicitly out of scope

* Codex's full proposed simplification (one canonical mm/y-up space, a
  `GeometrySnapshot` contract, removing `RENDER_GEOMETRY_SPACE`/
  `LEGACY_FURNITURE_SPACE` after a one-time migration of every project).
  That is a real, larger architecture project this review recommends but
  which needs its own scoped plan and a full-corpus migration strategy —
  attempting it unsupervised in this pass would risk every other house's
  furniture, not just `_047`'s.
* The other Codex findings not listed under "Exact scope" above: the
  `RegisteredFrame.point()` snapping-vs-affine deviation (#7), the
  correction-candidate/annotation frame mismatch on the `--corrected` path
  (#8), floor-identity-by-array-index for 3+ storey houses (#9), and the
  `moebel-registrieren.py` migration-policy gap (#10). Recorded on the
  roadmap as follow-ups.
* Any OTHER project's furniture. Only `twostorey_047` was measured and
  corrected; the roadmap follow-up flags that any project resaved through
  the OLD (pre-fix) code path is a candidate for the same corruption and
  should be spot-checked, not assumed fine.
* WordPress, publishing, uploading, approval, email, any external system.

## API, schema, and data-contract effects

* `geometry_only()`'s JSON output gains one new field per floor,
  `geometry_identity` (a string, or omitted if it cannot be derived) —
  additive, ignored by any consumer that doesn't know it.
* `save_furniture`'s request body gains one new OPTIONAL field,
  `displayed_geometry_identity`. Omitting it (an older client, or a caller
  other than the Möbel tab) falls back to the previous behavior
  unchanged — this is a strengthening for callers that opt in, not a
  breaking change to the endpoint's contract.
* `normalizeFurnitureDocument()` can now throw for a coordinate_space it
  previously accepted and silently relabelled. The only caller,
  `saveFurniture()`, already converts a thrown error into a 422 response —
  no new error-handling path needed.

## Acceptance criteria

1. `geometry_only(twostorey_047)` and `geometry_only(twostorey_049)` report
   the SAME stair width on ground and upper floor, matching the real build's
   `shared_stair_core` width exactly.
2. `render_geometry` for a project returns a non-empty `geometry_identity`
   per floor.
3. Saving furniture with a `displayed_geometry_identity` that disagrees with
   the current one is rejected with HTTP 409 and a message telling the user
   to reload.
4. Saving furniture with the CURRENT correct identity (or with the field
   omitted) still succeeds exactly as before.
5. Saving a document whose `coordinate_space` is the legacy space is
   rejected (throws), not silently relabelled.
6. Saving a document already in the current render space, or a brand-new
   document with no `coordinate_space` yet, is unaffected.
7. `twostorey_047`'s `floor-0.json` / `floor-1.json`: every item's position
   lands inside its semantically-correct room polygon under the CURRENT
   `geometry_only()` output (kitchen gear in the kitchen, bathroom fixtures
   in the bathroom, etc. — not just "inside some room").
8. `workbench_furniture("twostorey_047", level)` reads both floors without
   raising for either level.
9. `python scripts/build-simplifier-render-plan.test.py` and
   `node --test scripts/furniture-document.test.mjs` both pass, with the new
   tests included.
10. `npx tsc --noEmit` on the workbench passes.
11. `go.py twostorey_047` completes (`fertig`) and the resulting delivery
    render shows furniture in the rooms matching the reference photo.

## Tests and verification commands

New tests, added before committing to this fix:

* `scripts/furniture-document.test.mjs` — three new tests: legacy-space save
  refused with a message naming the migration script; a document already in
  the current space still saves; a brand-new document with no
  `coordinate_space` is still accepted.

Commands run:

```
python -m py_compile scripts/build-simplifier-render-plan.py
python scripts/build-simplifier-render-plan.test.py
node --test scripts/furniture-document.test.mjs
npx tsc --noEmit -p .
FLOORPLAN_WORKBENCH_DATA_DIR='E:\born2thrill-local-workbench-data' python scripts/go.py twostorey_047
```

Manual/live verification (via the running dev servers, not assumed):

* Fetched `render_geometry` for `twostorey_047` live and confirmed both
  floors return a 64-character `geometry_identity`.
* Called `save_furniture` live with a deliberately wrong
  `displayed_geometry_identity` → confirmed HTTP 409 with the expected
  message.
* Called `save_furniture` live with the correct full identity → confirmed
  HTTP 200, all 21 items round-tripped.
* Re-ran `geometry_only()` for `_047` and `_049` after the stair fix:
  `_047` 1415.5mm / 1415.5mm (ground/upper, was 1415.5 / 1049.4), `_049`
  900.0mm / 900.0mm (was 900.0 / 1021.6) — both now agree with the real
  build's `shared_stair_core` width, confirmed by directly computing that
  value from `annotation_stair_core()` with the ground frame.
* `build-simplifier-render-plan.test.py`: 72 tests, 1 pre-existing failure
  (`test_door_hinge_and_swing_are_normalized_into_the_walls_frame`, in
  `build_floor_walls_and_openings()` — unrelated door/wall code). Verified
  this failure is pre-existing and NOT caused by this change: reverted both
  of this task's edits to the file, re-ran that one test in isolation, and
  it fails identically. Restored the edits before continuing. Not fixed as
  part of this task (out of scope — door/wall opening code, not
  coordinate-space handling); recorded on the roadmap.

No existing test was deleted, skipped, weakened, or rewritten.

## Protected and risky paths

* `saveFurniture()`'s new rejection is a hard 409 by design (this is the
  exact "refuse, don't approximate" policy already used elsewhere in this
  file and in `build-simplifier-render-plan.py`) — a stale save now visibly
  fails instead of silently corrupting data, which is deliberately more
  friction than before. If this proves too strict in practice (e.g. minor,
  furniture-irrelevant annotation edits triggering rejections often), the
  fix is to narrow `level_geometry_identity()`'s own scope further, not to
  loosen this check.
* The stair-source-frame fix changes `geometry_only()`'s reported stair
  width/position for every project with an upper-storey stair, not just
  `_047`/`_049`. Verified both test houses now match the real build; not
  independently verified against the full corpus.

## Rights, provenance, privacy, and security impact

None. All changes are to local geometry computation, local save validation,
and local furniture data. No corpus record, provenance flag, or eligibility
state is touched.

## Floorplan-suite invariant

> Can any changed path generate, publish, or email geometry without matching
> an approved corrected corpus reference?

**No.** All changed code is the local plan builder, the local furniture save
API, and local furniture data. No publish, upload, or email path is touched.
`not_for_delivery` and `source_provenance` handling are unchanged.

## Customer, email, database, deployment, and external effects

None. `go.py twostorey_047` was run WITHOUT `--hochladen` — local build and
verification only.

## Failed-hypothesis log

1. *"The annotation must have changed since the furniture was placed —
   re-derive lo/hi from the current geometry and see if that alone explains
   it."* Measured: current `lo,hi` for both floors are byte-identical to the
   values used in the ORIGINAL 2026-09-16 fix. Conclusion: rejected — this
   is a re-reflection of already-corrected data, not a stale-extent problem,
   which is what pointed at the save-time re-stamping bug instead.
2. *"Maybe only the Möbel-tab's OWN save button re-stamps; a save through
   some other path might preserve the original identity."* Reviewed every
   furniture-file writer Codex found (`saveFurniture()`/route.ts,
   `moebel-migrieren.py`, `moebel-registrieren.py`,
   `moebel-vorderseite-richten.py`, `moebel-doppelpunkte.py`). Only
   `saveFurniture()` is reachable from the live web UI; the others are
   one-shot maintenance scripts not implicated in this specific
   corruption. Conclusion: `saveFurniture()` is the relevant path; fixed.

## Rollback

```
git checkout -- scripts/build-simplifier-render-plan.py \
  src/app/api/floorplan-workbench/corrections/route.ts \
  src/app/floorplan-workbench/page.tsx
rm src/app/floorplan-workbench/furniture.tsx \
   src/lib/generator/furniture-document.mjs \
   scripts/furniture-document.test.mjs
```
(the three `rm` targets were untracked before this task — confirm with
`git status` before deleting, since other untracked work may have landed in
them meanwhile). Restore `twostorey_047`'s furniture files from
`E:\born2thrill-local-workbench-data\corrections\twostorey_047\furniture\
floor-0.json`/`floor-1.json`'s prior content if needed — NOT recommended,
since the prior content was the corrupted (reflected) state this task fixed.

## Unresolved questions

* The full single-canonical-space simplification Codex proposed is real and
  recommended, but is its own project: it needs a corpus-wide migration
  strategy (Codex: "Legacy correction-candidate furniture cannot be
  converted exactly using a global flip or scale"), acceptance tests across
  basement/3-floor houses, and should not be attempted without a dedicated
  plan and Rainer's sign-off on the migration approach for existing houses.
* Whether any OTHER project besides `_047` was re-saved through the old
  (pre-fix) code path after its own furniture was placed, and is therefore
  also currently reflected. Not checked — flagged on the roadmap as a
  spot-check task, not assumed.
* `build_floor_walls_and_openings()`'s pre-existing, unrelated test failure
  (door ids not found) — not investigated, out of scope for this task.

## Approval record

Task delegated with explicit instruction ("just get it to work") after the
Codex architecture review's findings were presented and discussed; treated
as approval for the scope written above (the four confirmed, narrowly-scoped
fixes — not Codex's larger proposed rewrite, which is explicitly deferred).

## Completion record

Implemented and verified 2026-09-18.

### What changed

`scripts/build-simplifier-render-plan.py`
* `geometry_only()`: per-floor stair now always sourced via the GROUND
  frame + `ground_level`, matching `shared_stair_core`'s own construction,
  with the existing per-floor y-flip still applied afterward for display.
* `geometry_only()`: each floor's output dict gains `"geometry_identity":
  level_geometry_identity(project_id, level)`.

`src/app/api/floorplan-workbench/corrections/route.ts`
* `saveFurniture()` takes a new optional `displayedGeometryIdentity`
  parameter; rejects with 409 when it disagrees with the freshly-computed
  current identity.
* The `save_furniture` action handler passes `source.displayed_geometry_identity`
  through.

`src/lib/generator/furniture-document.mjs`
* `normalizeFurnitureDocument()` throws when the incoming document's
  `coordinate_space` is set and differs from `RENDER_COORDINATE_SPACE`,
  naming the legacy-migration script when that's the specific space found.

`src/app/floorplan-workbench/page.tsx`
* New effect: calls `furniture.setDisplayedGeometryIdentity(renderGeo?.
  floors?.[floorIndex]?.geometry_identity)` whenever the displayed geometry
  or floor changes.

`src/app/floorplan-workbench/furniture.tsx`
* `useFurniture()`: new ref + `setDisplayedGeometryIdentity` setter; `save()`
  sends the ref's current value as `displayed_geometry_identity`.

`scripts/furniture-document.test.mjs`
* Three new tests for the legacy-space refusal (see Tests section).

`E:\...\corrections\twostorey_047\furniture\floor-0.json` / `floor-1.json`
* All `position_mm`/`points_mm` y-values re-flipped once (`y -> lo+hi-y`,
  same extents as the untouched room geometry) and `rotation_deg` negated
  per item, `mirrored` left untouched per the existing documented policy.
  `updated_at` bumped; `geometry_identity` unchanged (the room layout itself
  never moved — only the furniture had been re-reflected).

### Verification

```
python -m py_compile scripts/build-simplifier-render-plan.py   -> OK
python scripts/build-simplifier-render-plan.test.py             -> 72 tests, 1 PRE-EXISTING unrelated failure
node --test scripts/furniture-document.test.mjs                 -> 15/15 pass (3 new)
npx tsc --noEmit -p .                                            -> clean
```

Live, against the running dev servers:
* `render_geometry` for `twostorey_047`: both floors return a
  `geometry_identity` (64 hex chars).
* `save_furniture` with a wrong identity → 409, expected message.
* `save_furniture` with the correct full identity → 200, 21 items.
* `workbench_furniture()` reads both corrected floors without raising.
* Stair width: `_047` now 1415.5mm on both floors (was 1415.5 / 1049.4mm);
  `_049` now 900.0mm on both floors (was 900.0 / 1021.6mm); both match the
  real build's `shared_stair_core` exactly.
* `go.py twostorey_047` re-run end to end with the corrected furniture
  (see delivery output for the visual confirmation).

### Remaining risks

* Other projects may carry the same reflection from a stale save made
  before this fix existed — not scanned. Roadmap follow-up:
  spot-check/audit the corpus.
* The full architectural simplification Codex proposed remains undone;
  this fix closes the specific hole that caused `_047`'s corruption and
  prevents a recurrence of THAT failure mode, but the underlying multiple-
  coordinate-space design is still as complex as Codex described.

## Addendum, same day: the flip BASIS itself, corpus-wide

Rainer, after the above was delivered: "well do it the other stuff doesn't
seem to be working, but it is the only logical thing to do" -- authorizing
Codex's core architectural recommendation, not just the point patches above.
Implemented the highest-value, lowest-blast-radius piece of it: replacing
the MOVING-TARGET flip basis (`lo, hi` — this floor's own room polygons,
recomputed independently by geometry_only() and by workbench_furniture()
at different times) with a STABLE one (`frame.height_mm` — a pure function
of the floor's scale and image aspect ratio, identical for a
RegisteredFrame and its own ground Frame). This is the root property Codex
identified as dangerous ("coordinate labels and geometry stamps can be
changed without transforming... the coordinates they describe") without
attempting the full canonical-space rewrite (new storage schema, removing
flips from storage entirely, a `GeometrySnapshot` contract) in one
unsupervised pass.

### What changed

`scripts/build-simplifier-render-plan.py`
* `geometry_only()`: the room/wall/stair/image-corner flip now uses
  `frame.height_mm` unconditionally (previously `lo, hi = min/max(room
  polygon y)`, skipped entirely when a floor had no rooms).
* `workbench_furniture()`: the furniture-position flip uses the SAME
  `_frame.height_mm` already computed a few lines above for the
  registration check (previously a second, independent
  `level_room_extent()` call). Also fixed a LATENT alias bug this exposed:
  `_frame` was computed from the raw `level` argument without translating
  `"floor-0"` -> `"groundfloor"` the way `level_geometry_identity()`
  already did -- harmless before (only used for an `isinstance` check that
  degrades gracefully to `None`), fatal now that `_frame.height_mm` is
  required. Fixed by resolving through the same `aliases` list the
  function already builds for itself.
* `level_room_extent()` is no longer called by the main flip logic (kept,
  still used by the new migration script and still under direct test).

`scripts/build-simplifier-render-plan.test.py`
* `test_pose_golden_vectors_hold_for_the_workbench_path`: updated to
  compute and assert against `frame.height_mm` instead of
  `level_room_extent()`'s `lo, hi`, matching the new implementation. The
  golden-vector file's OWN internal-consistency assertion (against its
  frozen `lo_plus_hi` contract value) is untouched — that is testing the
  historical contract data, not this function's live formula.

`scripts/moebel-flip-basis-migrieren.py` (new)
* One-time migration: since both conventions are "reflect around a single
  constant", converting is a pure per-floor SHIFT
  (`y_new = y_old + (frame.height_mm - lo - hi)`), not a re-derivation from
  room polygons. `--dry-run` reports without writing; a project-id argument
  scopes to one project. Writes a `flip_basis: "frame-height-v1"` stamp so
  a second run is a no-op instead of re-shifting already-migrated data.

### A mistake made and caught during this same task

Ran the migration once for `twostorey_047`/`twostorey_049` specifically
(to verify before trusting the whole corpus), then ran it AGAIN for the
whole corpus without excluding them -- the script had no stamp yet at that
point, so it silently shifted both projects a SECOND time. Caught
immediately by the same point-in-polygon check used throughout this task
(the fridge landed in the utility room instead of the kitchen). Corrected
by hand (subtracted the known delta once from both projects), re-verified
clean via point-in-polygon and `workbench_furniture()`, THEN added the
`flip_basis` stamp to the script so this exact mistake can't repeat. This
is precisely the class of bug this whole task exists to eliminate --
recorded here rather than quietly fixed, since it is the most concrete
demonstration in this session of why "recompute and reapply" is dangerous
and "stamp and refuse to reapply" is the correct pattern.

### Verification

```
python build-simplifier-render-plan.test.py   -> 72 tests, same 1 pre-existing unrelated failure
```

* Migration dry-run across the full corpus (61 furniture files, 103
  projects) reviewed before any write; deltas sane and, notably, identical
  between a project's own ground and upper floor every time (consistent
  with `RegisteredFrame.height_mm` always equalling its `ground_frame`'s).
* Point-in-polygon re-verified for `twostorey_047` (21+17 items) and
  `twostorey_049` (20+14 items) against FRESH `geometry_only()` output
  using the new flip basis: zero items outside any room, same correct
  room assignments as the earlier fix.
* `workbench_furniture()` re-confirmed reading both projects, both floors,
  without raising.
* Spot-checked three more migrated projects
  (`onehalfstorey_020`, `onehalfstorey_029`, `bungalow_001`):
  `workbench_furniture()` reads them without error (one unrelated,
  PRE-EXISTING staleness rejection on `onehalfstorey_020`'s groundfloor --
  its ROOM annotation genuinely changed at some prior, unrelated point;
  its upperfloor and every other checked floor read clean).
* `go.py twostorey_047` re-run end to end after the full migration (see
  delivery output).

### Remaining risk from this addendum

* The 57 non-`_047`/`_049` corpus files were migrated in a single batch
  and spot-checked (3 of ~30 projects), not individually point-in-polygon
  verified like the two houses this session focused on. If one of those
  projects' rooms had already drifted from its furniture in some OTHER way
  before today, this migration preserves that pre-existing relationship
  (a pure shift) rather than fixing it -- this only guarantees "as correct
  after as before", not "verified correct" for the un-spot-checked ones.
* The full "remove flips from storage entirely" rewrite Codex proposed is
  still not attempted. What changed today removes the DRIFT risk (two
  independent recomputations disagreeing) without removing the flip
  itself; Codex's further recommendations (stable floor IDs everywhere,
  unifying the `--corrected` path's separate flip, a `GeometrySnapshot`
  contract) remain open follow-ups.
