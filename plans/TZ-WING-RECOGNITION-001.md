# Recognize a T/Z-shaped footprint as three roof wings (recognition only)

Status: COMPLETE (recognition only, 2026-09-26) -- NOT wired into the
renderer, per explicit scope below

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

`roof_wings.recognize_two_wings()` only understands a simple L (exactly one
reflex/concave vertex). Any T or Z-shaped footprint (exactly two reflex
vertices) returns `None` today, and the caller silently falls back to a
plain hip roof (Walmdach) regardless of the house's actually-configured
roof type. Rainer, 2026-09-26, wants real T-shaped houses to get an actual
Satteldach/Pultdach/Doppelpultdach roof, built as three wings -- confirmed
wanted now, not deferred, but explicitly scoped first as its own design
question (via a Codex read-only review,
`plans/TZ-WING-RECOGNITION-001-codex-review.md`) before any code is
written, given how much of today's OTHER work turned out to have hidden
depth once actually measured.

## Current evidence and behavior

- `roof_wings.py`'s own header comment already states the T/Z exclusion is
  deliberate ("T-Formen (zwei Reflexpunkte) sind ausdruecklich ausserhalb
  von Version 1"), not an oversight.
- Codex's review (full output in the paired file) found the real
  complexity is NOT "can two reflex vertices ever be covered by three
  rectangles" (they always can, mathematically) -- it's that **a T and a
  Z/S shape need genuinely DIFFERENT construction rules**, even though
  both have exactly two reflex vertices:
  - A classic T (one long bar, one stem through its middle) has only TWO
    inclusion-maximal contained rectangles (the whole bar, and the stem
    extended through the bar) -- the "three independently-roofed wings"
    a real T roof needs (left bar-arm, right bar-arm, stem) are
    DELIBERATELY NOT maximal, and all three share a three-way overlap at
    the junction. "Just find the maximal rectangles" does not produce the
    right answer.
  - A Z/S shape's natural three-wing split (two terminal arms + a
    connector) has a different overlap pattern (connector overlaps each
    arm; the arms don't overlap each other) -- a different case, not a
    variant of the T case.
  - Two reflex vertices alone do not even guarantee a T or Z specifically
    -- U-shaped notches and staircase outlines also have exactly two, and
    are NOT the same shape family; the algorithm needs to actively
    distinguish and explicitly reject those, not assume "2 reflex points
    -> T-or-Z."
- **The existing L-shape naming convention (`wing_a`="full-x", `wing_b`=
  "full-y") does not survive to three wings at all** -- in the T example
  above, NEITHER bar-arm spans the whole X extent. Three-wing roles need
  shape-specific names instead (e.g. T: stem / left-arm / right-arm; Z:
  connector / arm-1 / arm-2), confirmed by Codex as a real, not cosmetic,
  difference from `PER-WING-AXIS-OVERRIDE-001`'s reviewed L-only design.
- **Everything downstream of recognition ALSO has pairwise-only
  assumptions that would need separate, real fixes** -- not covered by
  this plan, listed here so they aren't lost: `render-exterior.py`'s
  `_bigger_wi`/dominance logic (today literally indexes `wings[0]`/
  `wings[1]`), the whole wall-exposure-trimming mechanism from
  `WING-END-EXPOSURE-001` (pairwise `other_wing`, would need "subtract the
  UNION of every qualifying neighbour" per Codex, not just a 3-way loop),
  `roof_wings.reflex_point()`/`clip_wing_to_valley()` (built for exactly
  one reflex point, a T/Z has two, and Codex explicitly warns that
  clipping against two reflex corners independently is NOT simply "do the
  same clip twice" -- pairwise decisions must agree jointly at a three-way
  junction), and the doppelpultdach hand-built-box branch (bypasses the
  shared height-field code entirely, so generalizing the SHARED functions
  would not make three-wing Doppelpultdach work regardless).
- Codex's explicit recommendation: build recognition as its OWN, separate
  milestone, covering BOTH T and Z from day one (a true-T-only first pass
  would not avoid the core identity question, since the T case is not
  simpler than the general case) -- but deliberately do NOT wire a
  3-element `wings` result into today's live renderer yet, since doing so
  would immediately hit every pairwise assumption listed above with no
  correctness guarantee at all.

## Baseline

`born2thrill-local-workbench`: branch `agent/furnished-render-and-annotation-schema`
(per earlier Codex reviews this session), `scripts/roof_wings.py` as read
in full today (260 lines, unchanged this session).

## Exact scope

Recognition and decomposition ONLY -- given the file/architecture is
already explicitly separated (pure functions, no bpy, tested independently
of the renderer per the file's own header comment), this can be scoped as
a standalone addition to `roof_wings.py` without touching the renderer at
all, matching how `recognize_two_wings()` itself was originally built and
verified before ever being wired into `render-exterior.py`.

Per Codex's recommended milestone shape, the deliverable is a function
(name TBD, e.g. `recognize_three_wings(poly)`) returning:
- The three rectangles.
- Deterministic, shape-specific roles (not the L case's full-x/full-y
  convention).
- Both reflex corners.
- Explicit junction/adjacency relationships between the wings (not just an
  unlabelled overlap graph -- Codex found a plain "which pairs overlap"
  graph is insufficient, since a T's three wings mutually overlap despite
  having only two real reflex corners).
- Exact coverage verification against the input polygon (Codex suggests a
  stronger, arrangement-based check than today's sampled-grid
  `_grid_coverage_matches()`, which can miss thin discrepancies).
- `None` for anything that isn't a genuine, supported T or Z (U-notches,
  staircases, and any two-reflex shape that doesn't match one of the two
  explicit construction rules, rejected explicitly rather than guessed
  at).

## Files in scope

- `born2thrill-local-workbench/scripts/roof_wings.py` (new function(s),
  alongside the existing, unmodified `recognize_two_wings()`)
- New test file/additions (mirroring `roof_wings.test.py`'s existing
  convention -- pure geometry, no Blender needed)

## Explicitly out of scope

- Wiring the new recognition function into `render-exterior.py` at all --
  per Codex's explicit recommendation, this stays disconnected from the
  live renderer until the pairwise assumptions elsewhere are separately,
  deliberately redesigned (dominance/exposure-trimming/valley-clipping for
  N>=2 wings, doppelpultdach's hand-built-box branch). That is real,
  separate follow-up work, not assumed complete by this plan.
- `PER-WING-AXIS-OVERRIDE-001`'s own UI/override work -- separate plan,
  L-shapes only, not blocked by this one (though its own naming convention
  was confirmed here to NOT directly extend to three wings, should this
  ever need to support T-shaped houses too).
- Any shape with MORE than two reflex vertices (a plus/cross shape, etc.)
  -- not requested, not reviewed.

## Schema and dataset-contract effects

None yet -- a new, additive function; no existing data format changes
until (if) a later plan wires this into the renderer.

## Acceptance criteria

TBD in a follow-up plan revision once the exact three-wing role-naming and
rejection rules are settled (this document records the DESIGN REVIEW's
findings; a revision should turn Codex's numbered recommendations into
concrete, testable rules before implementation starts).

## Tests and verification commands

Per Codex: mirrored/rotated T and Z cases, winding/vertex-order
insensitivity, narrow-feature tolerance edge cases, T's real three-way
overlap, Z's connector-vs-arms overlap pattern, explicit rejection of
unsupported two-reflex families (U-notches, staircases), and confirmation
that the EXISTING `recognize_two_wings()`'s own L-shape behavior and tests
are completely unaffected (new, separate function, not a modification of
the existing one).

## Protected local data and risky paths

None -- purely additive, no existing function modified.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no -- this plan is pure geometry recognition, explicitly
disconnected from the renderer/build/delivery path per scope above.

## External effects

None.

## Failed-hypothesis log

Not applicable -- design-review stage only, no implementation attempted
yet.

## Rollback

N/A -- nothing implemented.

## Unresolved questions

- Exact role-naming scheme for T vs. Z wings (Codex gave illustrative
  names -- stem/left-arm/right-arm; connector/arm-1/arm-2 -- final naming
  needs to be settled before implementation, ideally in a way that reads
  sensibly in the German-language annotator UI too, matching this
  codebase's existing bilingual-naming convention).
- Whether U-shaped-notch and staircase footprints (also two-reflex-vertex,
  but NOT T/Z) are worth a future third construction rule, or should
  simply stay on the Walmdach fallback indefinitely -- not raised by the
  user, not assumed in scope.
- Sequencing against `PER-WING-AXIS-OVERRIDE-001`: which should be
  implemented first, given neither strictly blocks the other (recognition
  can be built and tested standalone; the L-only override work doesn't
  need three-wing support at all) -- a scheduling question for the user,
  not a technical dependency.

## Implementation result

Built in a new, separate file (`scripts/roof_wings_multi.py` +
`scripts/roof_wings_multi.test.py`), exactly matching Codex's own
recommended shape:

- `recognize_multi_wing(poly)`: reads a polygon with exactly two reflex
  vertices, classifies it via which bounding-box corners are missing
  (adjacent -> T candidate; diagonal -> Z/S candidate), and constructs the
  wings directly from the two reflex points and the bbox -- never a
  generic "find rectangles" search, per Codex's warning that a T's real
  three roof wings are deliberately NOT its inclusion-maximal rectangles.
- A genuine discovery made only by actually tracing the repo's own
  existing `Z_SHAPE` test fixture (already present in `roof_wings.test.py`,
  used there to assert the ONE-reflex-only `recognize_two_wings()`
  correctly rejects it): "reflex points don't share a coordinate" is not
  one family but two -- some such shapes need only TWO overlapping
  rectangles (a diagonally-offset L, no bridging piece), others genuinely
  need THREE (Codex's own illustrative example, a narrow connector
  bridging two arms that don't touch each other). The function tries the
  simpler two-wing construction first, falls back to the three-wing
  connector construction only if that doesn't reproduce the polygon
  exactly.
- Every candidate construction is checked against `_arrangement_coverage_
  matches()`, an EXACT (not sampled) coverage check built from BOTH the
  input polygon's own vertex coordinates AND the candidate wings' own edge
  coordinates -- the second half of that was added only after this
  session's own test suite caught a real gap: building the arrangement
  from the polygon's vertices alone missed an under-coverage that only
  showed up at a wing's own boundary, not at any polygon vertex.
- Two real construction bugs were found and fixed by running the test
  suite, not by re-reading the algebra: the three-wing connector's
  y-banded case had `arm_lo`/`arm_hi` built from the WRONG reflex point's
  coordinate (swapped), and its originally hand-derived x-banded mirror
  case was wrong in a different way. Fixed by replacing the second,
  independently-derived formula with a coordinate-TRANSPOSE of the first,
  already-verified one (swap x/y, reuse the same construction, transpose
  the result back) -- removing an entire class of mirror-formula bugs
  rather than trying to get the second hand derivation right too.

Verified: 18 new tests (T in all 4 orientations via mirroring/rotation,
both Z sub-families in all their orientations, explicit rejection of a
U-notch/plain-rectangle/simple-L/too-few-points/four-reflex-point "plus"
shape, CW-vs-CCW winding insensitivity) all pass. Existing suites
re-run and confirmed unaffected: `roof_wings.test.py` (23 tests),
`roof_profile.test.py` (92 tests) -- 133 tests total, zero regressions.
`roof_wings.py` itself was NOT modified.

## Approval record

The user confirmed (via question) that T-shape support is wanted NOW
rather than deferred, asked for a Codex design review first (complete),
then said "do it" while stepping away -- read as approval to implement the
recognition-only milestone Codex itself recommended (explicitly NOT wiring
it into the live renderer, which remains its own, separate, not-yet-
approved follow-up per "Explicitly out of scope" above).
