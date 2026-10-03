# Furniture editor: missing walls/doors and rotated resize-axis fix

Status: IMPLEMENTED (2026-08-22)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, reporting from `localhost:3000/haus?plan=bungalow_039`, Möbel step:
"why can i not see the walls and doors when placing furniture and when i try
to scale the furniture i feel as if the x and y are mixed up."

Fix both symptoms in the furniture-placement view (`/floorplan-workbench`
embedded via `mode=furniture-embed`, iframed by `/haus`):

- **A. Walls/doors invisible.** The furniture step draws `render_geometry`
  (the geometry the renderer actually builds, via
  `build-simplifier-render-plan.py --geometry-only`), not the correction
  candidate. That geometry-only export only ever emitted `rooms` — walls and
  openings were hardcoded to empty arrays downstream. Not a visibility toggle
  or CSS bug: the data was never produced.
- **B. Resize feels axis-swapped.** The resize-handle drag handler computes
  new width/depth from the raw world-space pointer delta, without undoing the
  item's own rotation. For anything placed at ~90°/270° (very common —
  `snapStampToWalls` rotates pieces to match the wall they're snapped to), a
  horizontal drag changes what's visually the item's depth and vice versa.
  Invisible at 0°/180°, which is presumably why it wasn't caught earlier.

## Current evidence and behavior

- `src/app/floorplan-workbench/page.tsx:709-720` — `renderFloor` (used as
  `overrideFloor` in furniture mode) hardcodes `walls: [], openings: []`.
- `src/app/api/floorplan-workbench/corrections/route.ts:608-636` — the
  `render_geometry` action shells out to
  `python build-simplifier-render-plan.py --geometry-only <ref> <tmpfile>`
  and returns that file's JSON verbatim (no field filtering, no cache — a
  fresh temp file every call).
- `scripts/build-simplifier-render-plan.py:1122-1183` — `geometry_only()`
  builds only `rooms` per floor from the annotation polygons; its own
  docstring says "the room polygons of this plan … and nothing else."
- The SAME script's main render-plan path (not geometry-only) already builds
  real walls (`build_walls()`, line 863) and matches door/window annotation
  elements to them (`nearest_wall()`, line 1039, plus the matching loop at
  lines 1787-1839) — this logic exists and is exercised in production, just
  not reachable from `geometry_only()`.
- Field-naming trap confirmed by direct comparison: `build_walls()`'s raw
  output uses `start_mm`/`end_mm`/`thickness_mm`/`width_mm` (the
  annotation/render-plan world), but the CORRECTION-document schema that
  `page.tsx`'s SVG actually reads from `floor.walls`/`floor.openings` uses
  `start`/`end`/`thickness`/`width` (short names — confirmed against
  `src/lib/generator/correction-editor.mjs:177-181`,
  `src/app/floorplan-workbench/page.tsx:38-54` `openingPoint`/
  `openingEndpoints`, and `doorColour()` in
  `src/lib/generator/floorplan-rulebook.mjs:133-135`, which needs
  `opening.width` and `opening.role`). These are two distinct schemas in this
  codebase; geometry_only's new output must be translated into the SHORT
  form, not just copied from `build_walls()`.
- Opening `position` is a 0..1 fraction from `wall.start_mm` to `wall.end_mm`
  (`nearest_wall`, line 1058-1059) — reflecting both wall endpoints through
  the same axis (see below) preserves this fraction, so openings need no
  separate flip handling once their host wall is flipped.
- `geometry_only()` already Y-flips ROOM polygons only, right before writing
  output (`build-simplifier-render-plan.py:1157-1168`), with the comment
  explaining this is "the one place geometry leaves the renderer" — the
  screen-orientation fix for "why is the floorplan rotated" (Rainer,
  2026-08-21). Walls must get the identical reflection (both endpoints) or
  they will render offset/mirrored relative to the (already-flipped) rooms.
- Resize bug, root cause:
  - `src/app/floorplan-workbench/furniture.tsx:533,544-551` — resize handles
    are children of `<g transform="translate(x y) rotate(rotation_deg)
    scale(mirrored?-1:1,1)">`, positioned at local `(±width/2, ±depth/2)`.
  - `src/app/floorplan-workbench/page.tsx` `onResizeGrab` stores only
    `{ id, centre: item.position_mm }` — no rotation.
  - The `onPointerMove` handler for `furnitureResize.current` computes
    `Math.abs(x - centre[0]) * 2` / `Math.abs(y - centre[1]) * 2` in WORLD
    coordinates and passes them straight to `onFurnitureResize` as
    width/depth — never undoing `rotate(item.rotation_deg)`.
  - `furniture.tsx` `useFurniture().resize(id, width, depth)`
    (`furniture.tsx:129-133`) writes those numbers directly into
    `footprint_mm.width_mm/depth_mm`, which are local-frame (pre-rotation)
    extents per `symbolBoundsMm()` (`src/lib/generator/
    furniture-document.mjs:157-172`, which already does the equivalent
    rotation math correctly for the read side — the bounding-box display).

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `git status` shows a large pre-existing dirty working tree (359 entries),
  including in-progress, uncommitted work on
  `src/app/floorplan-workbench/page.tsx` (the furniture-embed step itself —
  274 insertions, not yet committed) and `scripts/build-simplifier-render-plan.py`.
  This plan's diff lands ON TOP of that dirty tree. Nothing described here
  touches `data/simplifier-v2/*`, `scripts/render-furnished-dollhouse.py`,
  `scripts/start-floorplan-workbench.ps1`, or the `reviews/route.ts` changes
  already present — those stay exactly as they are.

## Exact scope

**A. Walls/doors in geometry-only mode**

1. In `scripts/build-simplifier-render-plan.py`, extract the wall-building +
   opening-matching block that the main render-plan path already runs
   (currently inlined around lines 1780-1839: `build_walls(...)` call plus
   the `for element in annotations.get("elements", [])` matching loop) into
   one shared helper function, parameterized by `(rooms, annotations, level,
   frame, is_ground_level)`, returning `(walls, openings)` in RAW
   (`_mm`-suffixed) form. Both the main path and `geometry_only()` call it.
   This avoids a second, drifting implementation of the same matching logic
   — the exact failure mode this file's own comments warn about elsewhere in
   this file (coordinate-system drift, "Nicht raten" comments).
2. In `geometry_only()`, call the shared helper per floor, then:
   - Apply the SAME Y-reflection (`lo + hi - y`, using the `lo/hi` already
     computed from room points) to both `start_mm` and `end_mm` of every
     wall.
   - Translate the raw wall dicts into the SHORT schema the frontend reads:
     `{id, start: start_mm, end: end_mm, thickness: thickness_mm}`.
   - Translate the raw opening dicts into
     `{id, wall_id, opening_type, position, width: width_mm, role}`
     (position is flip-invariant, per evidence above — no transform needed).
   - Add `"walls": walls_out, "openings": openings_out` to each floor's
     payload dict (next to the existing `"rooms": rooms`).
3. In `src/app/floorplan-workbench/page.tsx`, `renderFloor` (~line 709-720):
   replace the hardcoded `walls: [], openings: []` with `walls:
   (fl.walls || []), openings: (fl.openings || [])` read from the
   `render_geometry` API response.

**B. Resize axis fix**

4. Add one pure, exported helper to `src/lib/generator/furniture-document.mjs`
   (same module `symbolBoundsMm` already lives in, and already does the
   read-side equivalent of this rotation math):
   `worldDeltaToLocalMm(dx, dy, rotationDeg)` → `{x, y}`, applying the
   inverse of the `rotate(rotationDeg)` SVG transform (standard 2D inverse
   rotation: `x' = dx·cosθ + dy·sinθ`, `y' = -dx·sinθ + dy·cosθ`).
5. In `src/app/floorplan-workbench/page.tsx`:
   - `onResizeGrab` also stores `rotationDeg: item.rotation_deg`.
   - The `furnitureResize` branch of `onPointerMove` computes the world
     delta from the pointer to the stored centre, converts it to local
     coordinates via `worldDeltaToLocalMm`, and calls `onFurnitureResize`
     with `Math.abs(local.x) * 2` / `Math.abs(local.y) * 2` instead of the
     raw world-space `Math.abs(...)` values.

## Files in scope

- `scripts/build-simplifier-render-plan.py` (extract shared helper; wire it
  into `geometry_only()`; main render-plan path refactored to call the same
  helper instead of its inline block — behavior-preserving there, confirmed
  by test in "Tests and verification" below)
- `src/app/floorplan-workbench/page.tsx` (`renderFloor` wall/opening
  mapping; resize-grab ref gains `rotationDeg`; resize pointermove math)
- `src/lib/generator/furniture-document.mjs` (new exported
  `worldDeltaToLocalMm`)
- `scripts/furniture-document.test.mjs` (new test cases for the new helper)
- New: a small Python check for `geometry_only()`'s wall/opening output
  (see below) — file TBD at implementation time, likely
  `scripts/build-simplifier-render-plan.test.py` or a `--self-test` path if
  no Python test runner convention exists (none found in this repo for this
  script; will confirm and pick the lowest-friction option before writing
  it, and report the choice in the completion summary rather than guess
  silently)

## Explicitly out of scope

- No change to the main (non-geometry-only) render-plan path's OUTPUT — only
  its internal structure (calling the extracted helper). Its existing
  behavior for actual renders must be unchanged; verified by re-running it
  against a known project and diffing output before/after.
- No change to `data/simplifier-v2/*`, the sink/oven polish work, or any
  other already-dirty file not listed above.
- No change to how furniture is SAVED (`save_furniture`,
  `send_to_render`) — only how it is DISPLAYED and RESIZED in the editor.
- No change to wall/opening editing (there is none in furniture mode today —
  `showHandles` drag handles for walls only apply in geometry-edit mode, not
  furniture mode, and this plan does not add any).
- No attempt to fix the pre-existing large uncommitted diff already in
  `page.tsx`/`build-simplifier-render-plan.py` — only to build correctly on
  top of it.

## API, schema, and data-contract effects

- `render_geometry` API response gains `walls`/`openings` per floor (currently
  absent). Purely additive — no existing consumer reads those keys today
  (confirmed: `renderFloor` in page.tsx is the only consumer of this
  endpoint's response, and it currently discards those fields by not
  reading them).
- No change to the correction-document schema, the furniture-document schema,
  or any saved file format. `worldDeltaToLocalMm` is a pure function with no
  storage effect.

## Acceptance criteria

- Opening `/haus?plan=bungalow_039`, entering the Möbel step: walls and
  doors/windows render in the plan, in the same positions/orientation as the
  Korrektur-Editor's own view of the same house (sanity: exterior outline
  matches; door swing positions land in the same walls).
- Placing or selecting a piece of furniture rotated to 90° or 270° (e.g. via
  wall-snap or the 90° rotate button) and dragging a corner resize handle:
  dragging left/right changes the item's on-screen WIDTH, dragging up/down
  changes its on-screen DEPTH — matching what happens at 0°, not swapped.
- The main (non-furniture) render-plan path's JSON output for at least one
  already-built project is byte-identical before and after the refactor
  (walls/openings extraction) — confirms the refactor is behavior-preserving
  there.

## Tests and verification commands

New tests (added before implementation, per policy):

1. `scripts/furniture-document.test.mjs` — new `test(...)` cases for
   `worldDeltaToLocalMm`:
   - `rotationDeg = 0`: world delta passes through unchanged.
   - `rotationDeg = 90`: a pure-X world delta becomes a pure-Y local delta
     (and vice versa) — this is the exact case that reproduces bug B today
     and must be fixed by this change.
   - `rotationDeg = 45`: matches a hand-computed expected value (documents
     the convention so a future reader doesn't have to re-derive the sign).
2. A Python-side check that `geometry_only()`'s output for a real project
   (bungalow_039 or another already-annotated, scale-calibrated project)
   contains non-empty `walls` and `openings` arrays per floor with the short
   field names (`start`/`end`/`thickness`/`width`), and that every
   `opening.wall_id` resolves to a wall `id` present in that floor's `walls`
   list. Exact file/harness to be confirmed at implementation start (see
   "Files in scope"); reported in the completion summary.

Verification commands (run after implementation, output attached to the
completion report):

```
cd born2thrill-local-workbench
node --test scripts/furniture-document.test.mjs
python scripts/build-simplifier-render-plan.py --geometry-only bungalow_039 <tmp>.json
python scripts/build-simplifier-render-plan.py <project-already-built> <tmp-full>.json   # or whatever the main-path invocation is; exact command confirmed from existing usage before running
```

Plus manual verification in the browser (dev server via `start-
floorplan-workbench.ps1`, already running per the user's message):
`localhost:3000/haus?plan=bungalow_039` → Möbel step → visual check of
walls/doors, and a resize-handle drag on a 90°-rotated item.

Existing tests are not deleted, skipped, or weakened. If the byte-identical
diff check for the main render-plan path fails, the refactor stops and is
reported as a blocker rather than silently adjusted.

## Protected and risky paths

- `build-simplifier-render-plan.py`'s main render-plan path feeds real
  customer-facing renders. The refactor in step 1 touches code that path
  depends on — mitigated by the byte-identical-output check above before
  this is considered done.
- `geometry_only()` output feeds directly into what a human sees and places
  furniture against; wrong wall geometry would let furniture get placed
  through a wall that's actually there, or floating past a wall that
  render_geometry omitted. Mitigated by using the SAME wall-derivation code
  the renderer itself uses (via the extracted shared helper), not a new
  approximation.

## Rights, provenance, privacy, and security impact

None. No corpus, corrected-geometry, or customer-delivery path is touched —
this is purely the internal review/furniture-placement UI's own display and
interaction code. No new external effect, no email, no publish.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no.

- `geometry_only()` continues to read only from the Simplifier annotation
  source for the given project (same as today) — it does not read or write
  any correction revision, does not touch `approved_correction_revision()`,
  and is not part of any render/publish/send_to_render code path (confirmed:
  `send_to_render` in `furniture.tsx:192-207` calls a separate `action:
  "send_to_render"` API action, untouched by this plan).
- The resize fix only changes numbers written to the FURNITURE document
  (`footprint_mm`), which is explicitly presentation data stored beside
  revisions and never inside the correction document (per this file's own
  header comment, `furniture.tsx:13-15`) — it cannot move `geometry_hash`.

## Customer, email, database, deployment, and external effects

None. Local dev-only Next.js app (`localhost:3000`), no deployment, no
database write beyond the existing local furniture-document JSON files on
disk (unchanged file format, unchanged save path).

## Failed-hypothesis log

Not applicable yet — investigation this round used static code reading only,
converged on a single well-evidenced root cause for each symptom (cited
above), no failed hypotheses to log.

## Rollback

Pure code change on a dirty-but-uncommitted working tree; no data migration,
no deployment. Rollback is `git diff` of exactly the files listed in "Files
in scope" reverted (or `git stash`/`git checkout -- <file>` per file) —
leaves the rest of the pre-existing uncommitted work untouched.

## Unresolved questions

- Exact filename/harness for the Python-side geometry_only check (item 2
  under "Tests and verification") — will confirm the lowest-friction
  approach (standalone `assert`-based script vs. adopting a test runner) at
  implementation start rather than guess now.
- Whether any OTHER already-annotated project besides bungalow_039 should
  also be spot-checked for the byte-identical main-path-output requirement —
  defaulting to one project unless told otherwise, since the refactor is
  structural (extracting an existing block verbatim into a function), not a
  logic change.

## Approval record

Approved by Rainer, 2026-08-22 ("ok").

## Completion record (2026-08-22)

All items implemented as scoped. Verification:

- `node --test scripts/furniture-document.test.mjs` — 12/12 pass, including
  the 3 new `worldDeltaToLocalMm` cases.
- `python scripts/build-simplifier-render-plan.test.py -v` — 4/4 pass
  against the real `bungalow_039` project (walls/openings present, short
  field names, every `opening.wall_id` resolves, wall/room coordinate
  frames agree).
- Byte-identical check: ran the main render-plan path for `bungalow_039`
  `modern` through the pre-refactor inline block and the post-refactor
  shared-helper call side by side (`diff` of the two output JSON files) —
  identical. Confirms the extraction changed nothing for the path real
  renders depend on.
- Manual browser verification at `localhost:3000/haus?plan=bungalow_039` →
  Möbel step: walls and door openings now render (previously blank). Selected
  the Badewanne, rotated it to 90°, dragged a corner handle purely
  horizontally — the on-screen horizontal extent (depth) changed and the
  vertical extent (width) stayed put, i.e. no longer swapped. This test edit
  was NOT saved (no "Speichern" click; page was reloaded afterward) — the
  real `bungalow_039` furniture document on disk is unchanged.
- Console/network check during manual verification: only two pre-existing
  404s for `lowboard.png`/`garderobe.png` (procedurally-generated symbols
  with no catalogue image — unrelated to this change, present before and
  after).

Files changed (all within the scope declared above):

- `scripts/build-simplifier-render-plan.py` — new
  `build_floor_walls_and_openings()` helper; main render-plan path now calls
  it instead of an inline block (behavior-preserving, confirmed above);
  `geometry_only()` now calls it too, Y-flips wall endpoints alongside room
  polygons, and translates walls/openings into the short field-name schema.
- `src/app/floorplan-workbench/page.tsx` — `renderFloor` reads
  `fl.walls`/`fl.openings` instead of hardcoding `[]`; resize-grab ref
  gains `rotationDeg`; the resize pointermove handler converts the world
  pointer delta into the item's local frame via `worldDeltaToLocalMm`
  before computing width/depth.
- `src/lib/generator/furniture-document.mjs` — new exported
  `worldDeltaToLocalMm(dx, dy, rotationDeg)`.
- `scripts/furniture-document.test.mjs` — 3 new test cases.
- `scripts/build-simplifier-render-plan.test.py` — new file, 4 test cases
  (skips itself if `bungalow_039`'s Simplifier data isn't present in a given
  checkout, per the plan's fixture choice).

Unresolved-questions resolution: used the existing `unittest` +
`importlib.util` module-loading convention (matching
`scripts/verify_render.test.py`) for the Python test rather than adopting a
new runner — no `pytest` is installed in this environment. Tested against
the real `bungalow_039` project only, per the plan's stated default (the
refactor is structural, not a logic change).

No rollback was needed. If one becomes necessary: revert the 5 files listed
above; nothing else was touched.
