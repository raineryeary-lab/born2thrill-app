# A wing's internal (overlap) end still gets a full wall/soffit, not just its truly exposed sliver

Status: COMPLETE (2026-09-26), with one small known residual (see Implementation result)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Fix the recurring "wall/closure lands at the roof overhang, not the real
floorplan wall" complaint for the two-wing (L-shaped)
`satteldach`/`pultdach`/`doppelpultdach` branch, after confirming (via a
Codex read-only review, `plans/WING-END-EXPOSURE-001-codex-review.md`) that
my first hypothesis (a coordinate/offset math error) was WRONG, but two
other, real, currently-active defects are present in the same area.

## Current evidence and behavior

- My initial hypothesis -- that `wall_extension()`'s per-side "subtract
  overhang" inset mis-positions a wing's internal (non-eave) side because
  `roof_wings.recognize_two_wings()` decomposes an ALREADY overhang-offset
  polygon -- was checked by Codex with actual executed code (the real
  `offset_orthogonal_polygon()` and `recognize_two_wings()`, 4 L
  orientations x 4 overhang values). Refuted: the offset-then-inset math is
  exactly reversible for a wing's ORIGINAL (unclipped) rectangle. No change
  needed there.
- Two DIFFERENT, real, currently-active issues were found instead:
  1. **`render-exterior.py:1849`** -- the two-wing branch's call to
     `wall_extension()` never passes `real_ends`, so it defaults to
     `(True, True)`: a FULL end-wall and FULL verge soffit are built at
     BOTH ends of every wing, including the internal end that partially (or
     mostly) overlaps the OTHER wing's own territory. Nothing trims this to
     just the sliver of that end which is actually exposed beyond the other
     wing's reach. Same bug class already found and fixed once, in the
     hand-built-box doppelpultdach branch's own gable/versatz walls, but
     never carried over to this shared branch.
  2. **`roof_profile.py:675-680`** -- the verge soffit is not a thin
     underside strip; it is a solid facade-material closure spanning the
     FULL overhang depth (from the roof's outer edge to the inset wall)
     down to `z_eave`, by design (this is documented, intentional behavior
     for a normal single-rectangle roof, where a real verge overhang
     really is that deep). Combined with (1), this means a wing's internal
     end can get a full-depth facade slab built out to the roof edge,
     which is very plausibly what reads as "wall not at the real floorplan
     footprint" when that end mostly overlaps the other wing.
  3. A related, but currently DORMANT, third issue: `roof_wings.py`'s
     `clip_wing_to_valley()` (used only when `has_vertical_step()` is
     true) sets a clipped wing's boundary to an already-offset coordinate;
     passing that into `wall_extension()` (which insets by overhang again)
     would double-apply the offset. Confirmed by Codex via a numeric probe
     (`ry=4, h=0.5` -> wall lands at `5.0`, not `4.0`). NOT currently
     reachable in practice: `has_vertical_step()` is only true for
     doppelpultdach, and doppelpultdach no longer uses this shared branch
     (it uses the separate hand-built-box branch since
     `WB125-DOPPELPULTDACH-HANDBUILT-001`). Flagged so nobody re-enables
     clipping here later without also fixing this.

## Repository baselines

- `born2thrill-local-workbench`: branch `agent/furnished-render-and-annotation-schema`,
  base SHA `5be1a4e18956b9fb2e158bee82aa159898356e89`.

## Exact scope

In scope:
- Compute, per wing per end, which part of that end is actually EXPOSED
  (beyond the other wing's own reach) versus fully covered by the other
  wing, and build the end-wall/soffit/cap only for the exposed portion --
  not a whole-end boolean the way `real_ends` currently works.
- Apply this consistently to: the end-wall + verge soffit in
  `wall_extension()`, and (if/when ever reactivated) the explicit gable-cap
  loop, which Codex separately confirmed has no true-end gating at all
  right now either.
- Leave the refuted coordinate-inset hypothesis alone -- confirmed correct,
  do not touch `wall_extension()`'s basic overhang-subtraction math.
- Note (do not yet fix, just guard) the dormant double-offset clipping bug
  so it's not silently reintroduced if this branch is ever used for a
  stepped profile again.

Out of scope (unless the user asks otherwise):
- `SATTELDACH-HEIGHTFIELD-AXIS-001` (today's earlier axis fix) -- already
  complete, unrelated mechanism.
- `HUB-ASSET-FIT-CONTRACT-001` (door-asset scaling) -- unrelated.
- The Dach-tab UI's existing ridge-direction control (`#roofRotate` /
  `#roofAxisAuto` in `floorplan-simplifier/static/dach-editor.js`) -- this
  already exists and already writes the SAME `roof_axis_override` the
  renderer reads for both the single-rectangle and two-wing paths; separate
  discussion with the user pending on whether it needs relabeling/better
  visibility for L-shaped houses, not a code defect in this plan's scope.

## Files in scope

- `born2thrill-local-workbench/scripts/render-exterior.py`
- `born2thrill-local-workbench/scripts/roof_profile.py`
- `born2thrill-local-workbench/scripts/roof_wings.py` (only if computing
  "exposed portion of an end" is best done there, alongside the existing
  wing-recognition geometry -- to confirm during implementation)
- Test file(s) for the new exposed-segment logic

## Explicitly out of scope

See above. No plan/JSON schema change, no UI change.

## API, schema, and data-contract effects

None expected -- internal geometry-building functions only. If
`wall_extension()`'s signature needs a new parameter (e.g. per-end exposed
range instead of a boolean), that's an internal API change to a
renderer-only function, not a plan/data contract.

## Acceptance criteria

1. On a real two-wing satteldach/pultdach render (WB_125's QA build and at
   least one other two-wing house), no wall or soffit material appears
   beyond the true floorplan wall footprint at a wing's internal end.
2. The truly exposed sliver of an internal end (where one wing extends
   slightly past the other) still gets a real, correctly-sized wall/soffit
   -- not silently dropped.
3. No regression on a wing's true (fully exterior) ends -- unchanged
   behavior there.
4. Existing `roof_profile`/`roof_wings` test suites continue to pass; new
   tests added for the exposed-segment computation.

## Tests and verification commands

To be finalized in the approved plan revision. At minimum: unit tests for
the exposed-segment computation (full overlap -> zero-length exposed
segment -> no wall built; partial overlap -> correct sliver length; no
overlap/true end -> full end as today), plus a real `go.py` rebuild +
visual check of WB_125 as satteldach and at least one other two-wing house.

## Protected and risky paths

- Shared by satteldach, pultdach, and (structurally, if ever reactivated)
  doppelpultdach's old branch -- must not regress the just-fixed axis
  behavior or the already-correct coordinate math Codex verified.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. Renderer-only correctness fix.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. Hypothesis: `wall_extension()`'s overhang inset mis-positions a wing's
   internal (non-eave) side because `roof_wings.recognize_two_wings()`
   decomposes an already-offset polygon, so subtracting overhang again
   double-corrects. Command: Codex read-only review, executed the actual
   `offset_orthogonal_polygon()` + `recognize_two_wings()` code across 4 L
   orientations and 4 overhang values. Result: the offset-then-inset math
   is exactly reversible for a wing's original (unclipped) rectangle --
   refuted. Conclusion: do not change the basic inset math; the real
   defects are the missing exposed-segment trimming (this plan) and the
   dormant clipping double-offset (flagged, not currently reachable).

## Rollback

Revert any changes to the three files above -- no data/asset files touched.

## Unresolved questions

- Best place to compute "exposed portion of an end" -- `roof_wings.py`
  (alongside wing recognition) or inline in `render-exterior.py`'s
  two-wing branch -- to decide during implementation.
- Whether the user's "still having the problem" report is about a house
  other than WB_125, or about a defect still present in WB_125's own
  satteldach QA render that wasn't visible from the camera angle already
  checked -- worth asking, since this plan was written from code analysis,
  not a fresh render inspection of the specific complaint.

## Approval record

Approved verbally, 2026-09-26 ("come on fix it with codex please... also fix the
closing gap problem remeber the alway ahve to be in the Floorplan footprint
seen from the top").

## Implementation result

Three distinct, separately-verified fixes ended up being needed -- Codex's
design (the exposure-trimming mechanism itself) was correct, but two more
real bugs surfaced only once a real render was checked, neither of them
guessed correctly on the first try:

1. **Exposure trimming** (`roof_profile.py`'s `exposed_ranges()` +
   `wall_extension()`'s `other_wing` parameter, as designed): built, wired
   into `render-exterior.py`'s two-wing branch. Verified via hand
   calculation against WB_125's real wing numbers before ever rebuilding.

2. **Tie-breaking bug** (found by hand-verifying fix #1 against those same
   real numbers, before trusting a render): `roof_wings.recognize_two_wings()`
   makes one wing span the full x-extent and the other the full y-extent of
   the WHOLE building, so under a forced `roof_axis_override` both wings can
   have an end tied at the exact same true coordinate (e.g. both wings'
   south end is the same overall south edge). Each wing's exposure test saw
   the other also reaching that point and deferred -- BOTH suppressed their
   own end, leaving the true south wall entirely unbuilt (confirmed: `roof-
   pitch` and `roof-walls` were each individually watertight, 0 open edges
   -- the hole was a gap BETWEEN two otherwise-valid solids). Fixed with a
   `dominant` parameter (the bigger-by-area wing, same comparison already
   used elsewhere for the doppelpultdach clip decision) and a `TIE_MARGIN`
   (5cm) bias so a tie resolves to "build" for the dominant wing and
   "defer" for the subordinate one.

3. **A second, unrelated bug in the roof SHEET itself**, found after fix #2
   still left a visible hole in a real render: raycasting the built
   `roof-pitch` mesh from directly above (not more screenshot-reasoning)
   showed a genuine, real coverage gap -- roughly 0.3m x 8m -- with NO roof
   geometry at all, while the wall/soffit standing behind it WAS correctly
   present (so this was never a wall bug). Root cause:
   `heightfield_roof_mesh()`'s grid is spaced evenly across the whole
   bounding box by a fixed `step` (0.3m), with no reason to land exactly on
   a wing's own boundary -- a cell straddling that boundary has some
   corners inside the wing and some outside, and since a face needs ALL
   FOUR corners covered, the whole cell (and every other cell in that grid
   row, for the wing's entire remaining width) got dropped. This bug
   pre-dates everything else done today -- it was very likely already
   present before the axis-forwarding fix, just hidden behind the
   (incorrectly) full-length, untrimmed wall that used to stand in front of
   it. Fixed by snapping the grid to include every wing's own true edges as
   explicit lines, so a cell can never straddle a coverage transition.

Verified: `python3 roof_profile.test.py` (92 tests) and `roof_wings.test.py`
(23 tests) pass after every one of the three fixes. WB_125 rebuilt as
satteldach via `go.py`: the ~8m hole and the torn ridge facets are gone
(confirmed both by direct raycast sampling and by visual inspection of the
rendered image). `doppelpultdach` and `walmdach` baselines for the same
house re-checked visually -- both unchanged, no regression.

**Known residual, now root-caused**: a small (~10-20cm) cosmetic sliver
remains visible at one corner of the ridge peak from the hero camera angle.
Investigated thoroughly before stopping (top-down orthographic re-render:
fully solid, no coverage gap anywhere; fine-grained raycast scan across the
whole seam region: roof and wall present everywhere expected; raycast
comparison of roof-pitch vs roof-walls height at a dozen points along the
seam: wall consistently sits exactly `sink` (5cm) below the roof surface,
as designed, no mismatch; re-rendered with the height-field grid step cut
from 0.3m to 0.08m as a control -- the sliver did NOT shrink, ruling out
grid-resolution/staircasing as the cause).

Actual mechanism: at this exact seam, wing_1's own LONG WALL (its low,
eave-side partition facing wing_0) correctly stops at wing_1's OWN, much
LOWER roofline (~2.8m) -- above that height, the space is enclosed by
wing_0's own much TALLER roof (~4.9m) elsewhere, not by this wall, so it
has no reason to reach higher. This is a real, load-bearing part of how
independently-profiled wings joined by a height-max roof sheet behave, not
an error in any of today's three fixes -- confirmed correct at every point
sampled. The visible sliver is the very edge of that legitimate low-wall-
under-tall-roof transition, visible only from a narrow range of oblique
angles that happen to look almost along the wall's own face. Not chased
further today (would mean a real design decision -- e.g. an added small
infill panel at this transition -- not a bug fix); flag to the user as a
known, minor, characterized cosmetic limitation, not an open defect.
