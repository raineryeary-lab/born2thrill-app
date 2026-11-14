# Fix: interior "step" edges get no wall at all when an outer_outline exists

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

`HWR/HTR`'s boundary against `Diele` on `twostorey_046` has a small step (the
room polygon jogs sideways by ~370mm partway down). After the `image_size()`
fix, the two wall segments on either side of that step are both present and
correctly placed -- but the short perpendicular segment that should connect
them (closing the jog) is missing entirely, leaving a ~185mm gap in the
wall. Rainer, 2026-09-15: "the wall to the htr still has a whole in it".

## Current evidence and behavior

- Fixed geometry for `twostorey_046` ground floor (`--geometry-only`):
  `wall-0` ends at `[5719.9, 8202.9]`; `wall-1` starts at `[5904.6, 8202.9]`
  -- same Y, X offset by 184.7mm, at exactly the room polygon's step corner.
  Both are correctly-derived, correctly-placed walls; nothing connects them.
- Root cause, in `build_walls()` (`scripts/build-simplifier-render-plan.py`):
  the room polygon's short horizontal "step" edge (~370mm, deep inside the
  building) never finds a facing partner (nothing else borders it edge-on
  within tolerance -- it's a jog, not a shared partition), so it falls
  through to the "uncovered edges" loop meant to backfill exterior walls.
  But that loop is entirely skipped whenever the plan has a drawn
  `outer_outline_mm` (`if outer_outline_mm: ... walls from outline / else:
  ... uncovered edges become exterior walls` -- twostorey_046 has an
  outline, so the `else` branch, and this edge, never run at all). The
  existing gap-closers don't cover this either:
  `_close_exterior_corners` only touches `wall_type == "exterior"`;
  `_close_interior_t_junctions` explicitly skips parallel walls ("parallel:
  kein T-Stoss") -- and `wall-0`/`wall-1` are both vertical, i.e. parallel,
  offset sideways. This is a third, genuinely different topology from
  either existing gap-closer's target case.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Builds on top of this session's already-applied, uncommitted
  `image_size()` fix in the same file (`plans/image-size-ground-floor-
  priority-v1.md`).

## Exact scope

In `build_walls()`, when `outer_outline_mm` is given, still run the
uncovered-edge loop, but only for edges that are genuinely interior (not
already represented by an outline-derived exterior wall): skip an edge
whose whole span (within a small tolerance) lies on/near an outline wall's
centreline. For a surviving uncovered edge, emit it as an **interior** wall
(`DEFAULT_PARTITION_THICKNESS_MM`, matching the "buendig"/step convention
already used elsewhere in this function), not `DEFAULT_WALL_THICKNESS_MM`/
`wall_type: "exterior"` -- these orphaned edges are, by construction, never
on the building's exterior when an outline exists (the outline already
produced every real exterior wall).

## Files in scope

- `scripts/build-simplifier-render-plan.py` (`build_walls()` only)
- `scripts/build-simplifier-render-plan.test.py` (new test)

## Explicitly out of scope

- `_close_exterior_corners` / `_close_interior_t_junctions` -- not modified;
  this is a third case they were never meant to cover.
- The `image_size()` fix from the prior plan -- already applied, unrelated.
- Re-running any other project's build. Fix is in shared code; picked up
  automatically next time a project's geometry is built.

## Acceptance criteria

- `--geometry-only twostorey_046` produces a wall connecting `[5719.9,
  8202.9]` and `[5904.6, 8202.9]` (or equivalent, closing the step), so the
  HWR/HTR right boundary has no gap along its full length.
- No change to any wall/room for a project whose rooms are all plain
  rectangles (no step edges) -- confirm via `twostorey_045`'s
  `--geometry-only` output being byte-identical before/after.
- Full test suite stays green except the already-documented, pre-existing,
  unrelated `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`
  failure (do not touch it).

## Tests and verification commands

Add to `build-simplifier-render-plan.test.py`: a synthetic 2-room fixture (an
L-shaped room next to a rectangle, sharing a stepped boundary, with an
`outer_outline_mm` supplied) asserting `build_walls()` produces a connecting
wall at the step, plus a regression check against the real `twostorey_046`
fixture (skippable if absent, matching this file's existing convention).

Existing tests: none deleted, skipped, or weakened.

## Protected and risky paths

`build_walls()` is used by every project's geometry build. Change only adds
walls for edges that currently produce NOTHING (an uncovered edge with an
outline present) -- it cannot remove or move any wall that exists today.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference? Required answer: no -- same as the
prior plan; this only completes wall derivation from already-approved room
polygons.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. **Hypothesis:** the gap is an orphaned room-polygon edge that never pairs
   with anything and gets dropped because the "uncovered edges" loop is
   skipped whenever `outer_outline_mm` is present. **Fix attempted:** always
   run that loop, emitting unmatched edges as interior walls when they're
   not on the outline. **Test:** rebuilt `twostorey_046` -- gap unchanged,
   byte-for-byte. **Conclusion:** wrong. Direct tracing showed the step edge
   DOES pair (HTR's and Diele's diagonal edges at that step are exactly
   coincident, gap=0) and DOES produce a wall; the loop-skip was never the
   problem here. Kept the fix anyway as a real, independent hardening (an
   edge that genuinely never pairs still shouldn't vanish when an outline
   exists), covered by its own reasoning in the code comment, but it is NOT
   what closed this particular gap.
2. **Hypothesis (confirmed):** `_orthogonalize_interior_walls` snaps a
   near-vertical/near-horizontal wall's BOTH ends to their mean axis value,
   which for this wall (8.85 degrees off vertical, but ~2400mm long) moves
   its top end sideways by 184.7mm -- off the neighbouring wall's end it was
   exactly touching before the snap. **Fix:** if either of a wall's ends
   already coincides (<=5mm) with another wall's end BEFORE snapping, anchor
   the whole wall onto that neighbour's axis value instead of the mean; only
   fall back to the mean when neither end is already anchored (preserving
   the function's original guarantee for a free-floating skewed wall, e.g.
   onehalfstorey_029's wall-4, which is untouched by this change). Caught
   and fixed a real bug in the first version of this fix during testing: the
   anchor-exclusion check used point VALUE equality to exclude a wall's own
   two ends, which also wrongly excluded a neighbour's end whenever it
   coincided with one of this wall's own ends -- i.e. it excluded exactly
   the case the function needed to find. Fixed by excluding by the owning
   wall's index instead of by point value; added a regression test for this
   exact confusion (`test_anchor_snap_does_not_confuse_a_touching_end_with_
   its_own`). **Test:** rebuilt `twostorey_046` -- the two walls now share
   the exact same endpoint and get merged into one continuous wall by the
   existing `_merge_collinear_walls` step; gap fully closed. Full test suite
   green except the pre-existing, unrelated door-normalization failure.

## Rollback

Revert the `build_walls()` change.

## Approval record

Approved by Rainer, 2026-09-15 ("yes", extended to this newly-found third
symptom of the wall/step topology).
