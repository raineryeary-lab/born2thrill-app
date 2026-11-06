# Collinear wall merging must not depend on which endpoint is "start"

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer: "die Türen und wände sind 'off'" — bungalow_039's Möbel view shows
the wall between Schlafen/Wohnen-Essen and Diele (carrying two real doors)
sitting ~25mm off from the immediately adjacent wall between Schlafen and
Bad, even though both are the same continuous physical wall. Then: "egal ob
du das nochmal für alle machst oder nicht die Wände und Türen müssen
übereinstimmen" — fix the real cause, not just this one house.

Root cause, precisely measured (not the hand-drawing-imprecision
explanation first suspected and reported — that was wrong; re-verified
before writing this plan): `_merge_collinear_walls()`
(`scripts/build-simplifier-render-plan.py:612-`) is supposed to catch
exactly this case — two nearby, same-line wall segments — and unify them
onto one consistent centerline. It failed to here because its line-identity
key (`angle`, `offset`) is **not invariant under which endpoint of a wall
is stored as start vs end**.

## Current evidence and behavior

Measured directly on bungalow_039's real annotation data (both walls
`wall_type="interior"`, so they land in the same merge group):

```
wall-0 (Schlafen-Bad):   start [1328.5, 6441.7]  end [4336.8, 6441.7]  ux,uy=(+1, 0)
wall-8 (Schlafen/Wohnen-Essen - Diele): start [7283.7, 6416.3]  end [4359.8, 6416.3]  ux,uy=(-1, 0)
```

Both are horizontal, 25.4mm apart in y — well inside
`MERGE_LINE_OFFSET_TOLERANCE_MM = 150` (`:512`), and their x-spans are
23mm apart — well inside `MERGE_GAP_TOLERANCE_MM = 300` (`:513`). They
SHOULD merge. They don't, because:

```python
angle = math.atan2(uy, ux) % math.pi   # correctly direction-invariant: both give 0°
nx, ny = -uy, ux                        # NOT direction-invariant
offset = ax * nx + ay * ny
```

`nx, ny` is derived from the wall's own (possibly reversed) `ux, uy`, not
from the already-canonicalized `angle`. wall-0 (pointing +x) gets
`nx,ny=(0,1)` → `offset=+6441.7`. wall-8 (pointing -x, because whichever
room's edge-traversal produced it walked the opposite way) gets
`nx,ny=(0,-1)` → `offset=-6416.3`. Same physical line, offsets ~12,858mm
apart by sign alone — nowhere near the 150mm tolerance, so
`_merge_collinear_walls` treats them as unrelated lines and leaves both
their independently-computed centerlines standing, ~25mm apart.

This is the general case, not specific to bungalow_039: ANY two collinear
wall segments produced with opposite start/end direction (which side of a
shared room-boundary "wins" as `i` in `build_walls()`'s pairing loop is
incidental to room list order, per the existing pairing logic already read
this session) will fail to merge here regardless of how close their true
centerlines are. Confirmed by the door investigation: both real doors on
this line (`39265e` on wall-0's/wall-8's shared line, `8ece0b` also) sit
correctly per the DATA (verified against `nearest_wall`'s own matching,
zero unmatched openings) — it is specifically the WALL SEGMENTATION that's
inconsistent, not door placement.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `scripts/build-simplifier-render-plan.py`: already modified, uncommitted
  (this session's earlier walls/openings/area_m2 work, already
  implemented and verified). This plan's fix lands in the SAME file, a
  different function (`_merge_collinear_walls`, untouched so far this
  session).

## Exact scope

In `_merge_collinear_walls()` (`:612-`), replace the direction-dependent
normal computation with one derived from the already-canonical `angle`:

```python
angle = math.atan2(uy, ux) % math.pi
nx, ny = -math.sin(angle), math.cos(angle)
offset = ax * nx + ay * ny
```

This makes `(nx, ny)` — and therefore `offset` — identical for two
segments on the same infinite line regardless of which endpoint either one
calls "start". No other part of the function changes: grouping by
`wall_type`, the `PARALLEL_TOLERANCE_DEG`/`MERGE_LINE_OFFSET_TOLERANCE_MM`
comparison, and the span-merging/gap-tolerance logic below it are already
correct and untouched.

## Files in scope

- `scripts/build-simplifier-render-plan.py` only (one function).

## Explicitly out of scope

- No change to `build_walls()`'s pairing/centering logic itself (the
  `gap/2` centering per pairing) — that logic is correct in isolation; the
  bug is purely in the LATER merge step failing to unify what it should
  have unified.
- No change to `MERGE_LINE_OFFSET_TOLERANCE_MM`, `MERGE_GAP_TOLERANCE_MM`,
  or `PARALLEL_TOLERANCE_DEG` values — the existing tolerances (150mm,
  300mm, 12°) already comfortably cover the bungalow_039 case once the
  sign bug is fixed; no evidence they need to change.
- No new cross-room edge regularization (an earlier, WRONG hypothesis
  floated mid-investigation — hand-drawing imprecision between Bad's and
  Diele's edges — was ruled out by the precise measurement above; the
  actual cause is a pure sign bug, not source-data imprecision, so no such
  regularization is needed).
- No re-render of any house other than bungalow_039 as part of this plan's
  own verification (see Tests) beyond the required byte-identical-output
  regression check.

## API, schema, and data-contract effects

None. Pure internal geometry computation; no change to any output schema
key, only to which wall segments end up merged and their resulting
`start_mm`/`end_mm`.

## Acceptance criteria

- Rebuilding bungalow_039: the Schlafen-Bad wall and the
  Schlafen/Wohnen-Essen-Diele wall (previously wall-0 and wall-8) merge
  into one continuous, single-centerline wall (or remain correctly
  distinct if some OTHER, still-unmerged reason turns up — not expected,
  but the acceptance test is "no more ~25mm kink between adjacent
  same-line segments," not "these two specific IDs must merge").
- Both doors on that wall (`39265e`, `8ece0b`) still resolve to a single,
  correct wall id post-merge, with their `position` fractions still
  landing at the same real-world mm location as before (position is
  fraction-along-the-wall, and merging changes the wall's parametrization,
  so this needs to be checked, not assumed — see Tests).
- Every other already-built house's compiled render-plan output is
  BYTE-IDENTICAL before and after this change, OR any difference is
  inspected and confirmed to be a genuine same-class fix (an
  actually-collinear pair that now correctly merges), never a regression.
  This is the same verification discipline this file's own HANDOFF history
  already established for changes to this exact function family (miter
  limit, outline semantics, stair type — each proved byte-identical on the
  existing corpus before being trusted).
- The furniture-editor 2D view (this session's earlier fix) visually shows
  the wall as one continuous line with both doors correctly cut into it,
  no visible kink.

## Tests and verification commands

New test (added before implementation, per policy): extend
`scripts/build-simplifier-render-plan.test.py` (already exists this
session, currently tests `geometry_only()`'s wall/opening output against
real bungalow_039 data) with a case asserting NO two walls of the same
`wall_type` on the real bungalow_039 output sit within
`MERGE_LINE_OFFSET_TOLERANCE_MM` of each other in offset while remaining
unmerged (i.e., a direct regression guard for this exact bug class, not
just this one instance of it) — computed via the same direction-invariant
angle/offset formula as the fix itself, so the test would have failed
before this change and passes after.

Verification commands:

```
cd born2thrill-local-workbench
python scripts/build-simplifier-render-plan.test.py -v
python scripts\run_project.py bungalow_039 --styles modern,classic
```

Plus the byte-identical regression check already used earlier this
session for changes to this file: rebuild at least one other already-built
house's full render-plan (e.g. `bungalow_040_66` or `onehalfstorey_020`)
before and after, diff the JSON. Plus visual re-check of the furniture
editor's 2D plan for bungalow_039.

Existing tests are not deleted, skipped, or weakened.

## Protected and risky paths

- `_merge_collinear_walls()` runs for every house's every render (both the
  interior and exterior render passes, and now also the furniture editor's
  `geometry_only()` path) — the single most shared piece of geometry code
  touched this session. Mitigated by: the fix is a two-line, purely
  mathematical correction with a clear proof of correctness (angle is
  already direction-invariant; deriving the normal FROM that angle instead
  of from the raw direction vector makes the normal direction-invariant
  too, by construction); the byte-identical check on other houses catches
  any unintended behavior change; the new regression test guards this
  exact bug class going forward.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. Existing certified deliveries become stale under the
existing `toolchain` hash mechanism once this renderer code changes (same
established, correct behavior as every prior fix to this file this
session and in this suite's history) — not something this plan needs to
add, and not a new customer-facing publish path.

## Customer, email, database, deployment, and external effects

None directly. Indirect: bungalow_039's (and potentially other houses',
if the byte-identical check finds a real difference elsewhere) certified
delivery becomes stale and needs rebuilding before its next delivery —
expected, existing mechanism.

## Failed-hypothesis log

1. **Hypothesis**: the ~25mm offset is inherent hand-drawing imprecision
   between Bad's and Diele's room-boundary points relative to Schlafen's
   edge (reported to Rainer as the likely cause before this plan).
   **Checked**: measured wall-0's and wall-8's actual `(angle, offset)`
   values as `_merge_collinear_walls()` computes them: `+6441.7` vs
   `-6416.3` — a sign flip, not a ~25mm geometric discrepancy from
   imprecise drawing. Their true perpendicular distance is exactly the
   25.4mm the merge tolerance (150mm) already accommodates.
   **Conclusion**: rejected. The real cause is line-identity computed from
   a direction-dependent normal vector, not source-data imprecision.
   Corrected before implementing anything, rather than building a
   cross-room regularization fix for a problem that turned out not to be
   the real one.

## Rollback

Pure code change on an already-dirty, uncommitted working tree, one
function. Revert the two changed lines to undo; nothing else touched.

## Unresolved questions

None.

## Completion record (2026-08-22)

Implemented as scoped: `nx, ny` now derived from the canonical `angle`
instead of the raw (possibly reversed) direction vector, in
`_merge_collinear_walls()`.

Verification:
- New regression tests added to `build-simplifier-render-plan.test.py`:
  `test_no_two_same_type_walls_sit_on_the_same_line_unmerged` (the direct
  guard for this bug class) and `test_rooms_carry_a_real_area` (guards the
  earlier area_m2/NaN fix found in the same investigation) — 6/6 tests
  pass.
- bungalow_039: wall count for the ground floor dropped from 18 to 13
  (later 16→13 after the area_m2 fix was already in); the two previously
  misaligned segments (offsets `+6441.7` vs `-6416.3`) are now one wall
  spanning the full width at one consistent y. Both real doors on it still
  resolve correctly (0 unmatched openings), positions recompute correctly
  against the new merged wall's parametrization.
- Byte-identical regression check on two other already-built houses
  (`onehalfstorey_020`, `bungalow_040_66`): NOT byte-identical (expected —
  they had the same latent bug) — diffed and confirmed every difference is
  the same class of correct improvement (fewer, correctly-merged walls,
  identical opening counts, doors correctly re-pointed to merged wall
  ids). `verify_render.py`'s `wall_angles` and `opening_count` checks PASS
  on both after the change.
- Full `run_project.py bungalow_039 --styles modern,classic` pipeline run:
  all verifier checks PASS for both styles, fresh delivery certified.
- Live browser verification: reloaded `/haus?plan=bungalow_039`, switched
  to Möbel (which now correctly waits for the paired annotator-save
  handshake — takes a couple of seconds, which first looked like a hang
  until confirmed it was the real save round-trip completing, not a bug),
  and read the live SVG DOM directly: 13 wall lines, the north partition
  wall spans the full 1328.5–10239.5mm width at one consistent y=5774.7,
  both doors cut cleanly into it.

Files changed: `scripts/build-simplifier-render-plan.py`,
`scripts/build-simplifier-render-plan.test.py`.

Also fixed in the same investigation (small, separate, already reported
and completed): `room.area_m2` was missing from `geometry_only()`'s room
output, rendering "ca. NaN m²" for every room in the furniture editor
(`scripts/build-simplifier-render-plan.py`'s room-building loop now
computes it the same way the main render-plan path already does;
`src/app/floorplan-workbench/page.tsx`'s `renderFloor` now passes it
through).

## Approval record

Approved by Rainer, 2026-08-22 ("egal ob du das nochmal für alle machst
oder nicht die Wände und Türen müssen übereinstimmen" — read as approval
to fix the underlying mechanism now).
