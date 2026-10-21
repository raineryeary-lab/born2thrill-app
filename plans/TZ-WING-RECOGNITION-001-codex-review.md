# Design review (no implementation): recognizing a T/Z-shaped footprint as three roof wings

## Context

`born2thrill-local-workbench/scripts/roof_wings.py`'s
`recognize_two_wings(poly)` (full source below, this IS the entire current
file's core logic -- please read it directly, this isn't a paraphrase)
handles ONLY the simple-L case: a rectangular footprint with a bite taken
out of exactly one corner (exactly one reflex/concave vertex,
`_reflex_vertices(poly)` returns a list of length 1). It:
1. Finds the polygon's overall bounding box.
2. Requires exactly one reflex vertex, not too close to the bbox edges.
3. Checks exactly one of the bbox's four corners is "missing" (outside the
   polygon) -- confirming the shape really is an L, not some other
   one-reflex-point shape.
4. Constructs `wing_a` (spans the FULL x-extent of the bbox, partial y)
   and `wing_b` (spans the FULL y-extent, partial x) from the bbox and the
   reflex point.
5. Verifies the union of the two rectangles exactly covers the polygon via
   a sampled-grid check (`_grid_coverage_matches`), rejecting anything that
   doesn't match (guards against a shape that merely LOOKS like an L from
   the reflex-count alone but isn't actually decomposable that way).

The file's own header comment is explicit: "Nur EIN Reflexpunkt wird
unterstuetzt (ein einfaches L) -- T-Formen (zwei Reflexpunkte) sind
ausdruecklich ausserhalb von Version 1" -- a T or Z shape (exactly two
reflex vertices) is deliberately out of scope today; the caller
(`render-exterior.py`) falls back to building a plain hip roof (Walmdach)
over the whole footprint whenever this returns `None`, regardless of the
house's actually-configured roof type.

Everything downstream of this function already generalizes to "a list of
wings," not just a hardcoded pair: `roof_profile.combined_height_at()` and
`heightfield_roof_mesh()` both already take a `wings` LIST and iterate it;
`render-exterior.py`'s two-wing branch is the only place that assumes
`len(wings) == 2` specifically (e.g. `_smaller = 0 if area(wings[0]) <=
area(wings[1]) else 1`, and the whole wall-exposure-trimming work from
earlier today, which is pairwise: each wing's `other_wing` is simply "the
other one" out of exactly two).

## What the person I work for wants (confirmed today, not yet designed)

Real T-shaped (and Z-shaped) houses in the catalogue should get an actual
Satteldach/Pultdach/Doppelpultdach roof built as three wings meeting at
the T's two reflex corners, instead of silently becoming a Walmdach. This
is explicitly wanted NOW (not deferred), alongside (but as its own,
separate piece of work from) the per-wing ridge-override UI already
reviewed today (`plans/PER-WING-AXIS-OVERRIDE-001.md` and its paired
Codex review, L-shapes only, semantic "full-X wing"/"full-Y wing"
selectors) -- that review's own point 5 flagged that wing-count is not the
hard part, wing IDENTITY/ownership is, and that a genuinely new function
count is where new scope actually lives.

## What I actually need from this review

This is a DESIGN review only -- no code should be written or changed.
Read the actual current `roof_wings.py` (paste the full file below) and:

1. **Generalize the recognition algorithm itself.** For a polygon with
   EXACTLY TWO reflex vertices (a T or Z shape), what is the correct,
   general procedure to decompose it into exactly THREE axis-aligned,
   overlapping rectangles whose union exactly matches the polygon --
   analogous to what `recognize_two_wings()` does for one reflex vertex?
   Consider: a true T (the classic "letter T" -- one long bar, one stem
   perpendicular to its middle) and a Z/S shape (two offset rectangles
   connected by a third) are geometrically DIFFERENT cases even though
   both have exactly two reflex vertices -- does one general algorithm
   cover both, or do they need to be told apart and handled with different
   construction rules? Is there a case with exactly two reflex vertices
   that is NOT decomposable into exactly three rectangles at all (the T/Z
   analogue of `recognize_two_wings()`'s own "grid coverage doesn't match,
   return None" safety net) -- if so, characterize it.
2. **Does the existing per-wing "full-X-extent"/"full-Y-extent" naming
   convention survive with three wings?** `recognize_two_wings()`'s
   `wing_a`/`wing_b` naming works because with exactly two wings, exactly
   one can span the full bbox width and the other the full bbox height (of
   the OVERALL two-rectangle bounding box). With three wings, is there an
   equally clean, unambiguous naming/role scheme, or does correctness now
   require something more structural (e.g. an adjacency graph of which
   wings share which reflex corner)? This matters because
   `PER-WING-AXIS-OVERRIDE-001`'s reviewed design leans on exactly this
   kind of semantic-role naming for the two-wing case -- if three wings
   can't be named as cleanly, that plan's chosen approach may not
   generalize the way I assumed, and I'd rather know that now.
3. **What breaks in `render-exterior.py`'s current two-wing branch if
   `wings` has 3 elements**, beyond the obvious `_smaller =
   0 if area(wings[0])<=area(wings[1]) else 1` (clearly pairwise, would
   need a real per-pair-of-neighbours redesign, not just "iterate 3").
   Read the actual current wall-exposure-trimming code (`other_wing`
   parameter added earlier today, see
   `plans/WING-END-EXPOSURE-001-codex-review.md` for that context if
   useful) and state plainly whether it's pairwise-only by construction or
   could extend to "the union of every OTHER wing" reasonably.
4. **Height-field correctness with three wings.** `combined_height_at()`'s
   "z = max over every wing that covers this point" already generalizes
   mechanically to any wing count -- but does the REFLEX-corner handling
   used for a stepped (doppelpultdach-style) profile generalize, given a
   T/Z shape now has TWO reflex corners, potentially each needing its own
   valley-clip logic (`clip_wing_to_valley()`, `reflex_point()` -- both
   currently hardcoded to a SINGLE pair of wings/single reflex point)?
5. **Rough scope/complexity estimate** for JUST the recognition-and-
   decomposition piece (this file only, not the renderer or UI changes) --
   is this a contained, well-defined geometry problem, or does it have the
   same kind of hidden depth the per-wing override review found elsewhere
   today?

## Out of scope for this review

- Do not design or estimate the renderer wall/roof-building changes needed
  once 3 wings exist (covered partially by question 3/4, but don't design
  full solutions, just characterize what would need to change).
- Do not design the UI changes for a third drawable ridge line -- that's
  covered by `PER-WING-AXIS-OVERRIDE-001` once this recognition piece
  exists; only comment (question 2) on whether ITS chosen naming
  convention survives.
- Do not write any code.

## Current file, in full (`born2thrill-local-workbench/scripts/roof_wings.py`)

```python
<PASTE roof_wings.py FULL CONTENTS HERE -- Codex should read the real file
directly via its own file access rather than trust this brief's paraphrase
above; this note stands in for actually including it since Codex has read
access to the repo at C:\dev\Floorplan-tools\born2thrill-local-workbench>
```

## Output format

A short "assessment" section per numbered question above (confidence:
high/medium/low, whether inferred or directly verified against the code),
then a final "recommendation" section stating whether T/Z recognition is
worth attempting as a next step, and if so, the shape of the right first
milestone (e.g. "handle the true-T case only, reject Z/S explicitly, ship
that first" vs. "one general algorithm covers both from day one").

---

## Codex output

## 1. Assessment: recognition and decomposition

**Confidence: high for the geometry and current code; medium for the proposed architectural convention. Code findings directly verified; algorithm proposals are design inference.**

**One general geometry engine can cover T and Z/S, but “two reflex vertices means three roof wings” is not a geometric identity.** Three architectural wings require an explicit decomposition convention.

A classic T already has a **two-rectangle overlapping cover**: the whole bar and the whole stem, extended through the bar. This differs from a non-overlapping partition and from choosing three independently configurable roof wings. Rectangle covering explicitly allows overlap; partitioning does not. [Culberson and Reckhow’s rectangle-covering paper](https://doi.org/10.1016/S0019-9958(84)80012-1) treats that distinction.

For example, consider a T formed by:

- Bar: `[0,10] × [6,8]`
- Stem: `[4,6] × [0,8]`

A reasonable **three-wing convention** is:

- Left arm: `[0,6] × [6,8]`
- Right arm: `[4,10] × [6,8]`
- Stem: `[4,6] × [0,8]`

Their union is exactly the T; each contributes exclusive territory. But all three overlap in the junction `[4,6] × [6,8]`. The two arm rectangles deliberately are **not inclusion-maximal**: each could expand into the whole bar. Therefore, “find maximal rectangles and return three” is not sufficient.

A Z example has a different natural construction:

- Upper arm: `[0,6] × [4,6]`
- Connector: `[4,6] × [0,6]`
- Lower arm: `[4,10] × [0,2]`

Here the connector overlaps each arm, while the arms do not overlap each other.

**Recommended general procedure:**

1. **Validate and normalize the polygon.** Require a simple, nondegenerate, axis-aligned boundary without holes; remove duplicate/collinear vertices, normalize winding, and then require exactly two reflex vertices. The existing [_reflex_vertices()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:70) assumes these properties; its cross-product test does not establish them.
2. **Build the coordinate arrangement:** sorted unique polygon X and Y coordinates. Classify each rectangular cell as inside or outside.
3. **Enumerate contained candidate rectangles** whose boundaries lie on those coordinates. Include non-maximal candidates.
4. **Enumerate three-rectangle covers** and require exact cell coverage, positive dimensions, and an exclusive contribution from each wing. Define “overlapping” as a connected graph of positive-area overlaps—not necessarily overlap between every pair.
5. **Select according to explicit architectural roles.** For a T, use the two bar arms plus stem convention; for Z/S, use the terminal arms plus connector convention. Reject unsupported or ambiguous arrangements instead of choosing whichever triple enumeration encounters first.
6. **Return the selected rectangles together with their structural relationships and original reflex vertices.**

The geometry machinery is shared; **the selection contract must distinguish configurations**. It should not infer roof semantics from coverage alone.

The arrangement also gives a stronger safety check than the present [_grid_coverage_matches()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:84). Its uniform samples can miss thin discrepancies. Once all polygon and candidate boundaries are arrangement lines, occupancy is constant within each cell, so cell comparison establishes equality for validated orthogonal geometry, subject to numerical tolerance.

**Are there two-reflex exceptions?**

- Two reflex vertices do **not** uniquely identify T/Z: U-shaped notches and staircase outlines also qualify.
- For a valid simple orthogonal polygon with two reflex vertices, reflex cuts produce a partition into **at most three rectangles**. Thus there is no obstruction to three-rectangle coverage in the broad sense; subdivisions can supply exactly three.
- That does **not** guarantee three unique, maximal, irredundant, positively overlapping *architectural wings*. Those are additional requirements. In particular, a classic T has only two inclusion-maximal contained rectangles.
- Invalid, diagonal, self-touching, or degenerate input may pass a raw reflex-count check yet fail rectangle coverage. Narrow features may also warrant explicit tolerance-based rejection.

Do not equate failure of the chosen wing convention with mathematical impossibility of rectangle coverage.

## 2. Assessment: naming and identity

**Confidence: high — current guarantees verified; proposed replacement is design inference.**

**Full-X/full-Y does not survive as a universal three-wing naming scheme.**

In the three-wing T example, neither arm spans the whole X extent. In the Z example, neither terminal arm does. Other two-reflex configurations can have multiple rectangles sharing a full extent.

Keep the existing L selectors as valid **L-specific identities**. For three wings, use shape-specific roles backed by structural information, for example:

- T: stem, negative-direction bar arm, positive-direction bar arm.
- Z/S: connector and two terminal arms, distinguished in a defined coordinate frame.

These roles identify footprint components, independently of their selected ridge axes.

**An adjacency graph helps, but an unlabelled overlap graph is insufficient.** The T example has a three-way overlap and a triangular overlap graph, despite having two reflex corners. A graph therefore needs labels linking wings to actual reflex corners, incident boundary segments, and junction regions. “One overlap edge equals one reflex corner” is false.

The reviewed L naming approach remains sound within its stated scope; it does not automatically provide three-wing identity.

## 3. Assessment: current renderer and exposure trimming

**Confidence: high — directly verified against current code.**

Passing three rectangles would break assumptions beyond `_smaller`:

| Current code | Consequence with three wings |
|---|---|
| [_other_wing selection](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1877) supplies a neighbour only when `len(wings) == 2` | **All exposure trimming is disabled**, so internal wall/soffit portions can return. |
| [_bigger_wi](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1872) compares only entries 0 and 1 | The third wing cannot win ownership; one global dominant/subordinate distinction cannot represent all neighbour relationships. |
| [Valley clipping](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1704) is explicitly gated to two wings | Three-wing inputs skip it entirely. |
| [Vertical-step routing](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1407) enters the hand-built branch | It creates **two slabs with fixed locations, dimensions and rotations**, then derives wall coordinates from the first two wings. A third wing receives no corresponding general roof construction. |
| [Cap generation](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1830) builds both ends without neighbour-exposure trimming | Its loop accepts additional entries mechanically, but that does not establish correct exposed caps. It is currently bypassed for the ordinary vertical-step route. |

The actual exposure implementation is in `roof_profile.py`.

**Its interface is pairwise-only; its geometric core reasonably generalizes to the union of other wings.** [exposed_ranges()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:629) subtracts one covered interval from a boundary segment. Subtracting the union of all qualifying neighbours’ intervals—or successively subtracting them from the remaining intervals—extends that operation naturally.

Two qualifications matter:

- Use the **actual union**, never the neighbours’ bounding box.
- [dominant/tie_bias](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:747) is an ownership rule layered onto exposure. It needs consistent resolution wherever multiple wings share an exterior segment. Geometric interval subtraction alone does not settle which roof profile must close that segment.

Also, the existing overhang inset assumes the original rectangle construction. Newly introduced split boundaries cannot automatically inherit the L case’s “inset every side to recover wall coordinates” guarantee.

## 4. Assessment: height field and reflex-corner handling

**Confidence: high — directly verified; multi-junction consequences inferred.**

The basic maximum operation generalizes. [combined_height_at()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:260) iterates paired wings and profiles; [heightfield_roof_mesh()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:397) uses all rectangles for bounds, coverage, and boundary-grid insertion.

That establishes **mechanical wing-count support**, provided every wing has a corresponding profile. It does not establish architectural correctness.

The reflex helpers do not generalize unchanged:

- [reflex_point()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:194) reconstructs one L corner from two rectangles’ full-extent roles. A bar/stem pair representing a complete T has **two** reflex corners; that interface cannot describe it.
- [clip_wing_to_valley()](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:223) applies a one-sided rectangular restriction against one neighbour and one corner.
- Applying that restriction repeatedly does not preserve the current argument that “the untouched other wing covers everything removed.” Several clips can interact, and a wing’s valid height-contribution region need not remain a single rectangle.
- In a three-way overlap, pairwise decisions must agree jointly. Two reflex corners are not automatically two independent clipping operations.

Coverage rectangles, profile coordinates, and permitted height-contribution regions therefore need distinct contracts. An exact footprint union cannot validate valley ownership.

**Most importantly for today’s code:** vertical-step profiles bypass the shared height-field branch. Generalizing these helpers alone would not make current Doppelpultdach rendering support three wings.

## 5. Assessment: recognition-only scope

**Confidence: medium — estimate from inspection, without implementation or catalogue validation.**

This is a **contained geometry problem once the decomposition convention is settled**. It is not the same cross-system undertaking as persistence, UI, and renderer changes.

For recognition only, a reasonable allowance is **2–4 focused engineering days**, including geometry tests and representative catalogue checks. That assumes:

- T and Z/S three-wing conventions are fixed.
- Other two-reflex families are explicitly rejected initially.
- Input normalization and tolerance policy are bounded.
- The result includes enough structural metadata to avoid downstream reconstruction of identity.

The main uncertainty is **choosing meaningful, stable rectangles**, not finding some rectangular cover. Verification should include mirrored/rotated cases, winding and vertex-order changes, narrow features, T triple overlaps, Z connector variations, unsupported two-reflex families, and unchanged L behavior.

## Recommendation

**Proceed with a recognition-only milestone covering both T and Z/S from day one, using one validation/coverage engine and explicit shape-specific selection rules.** A true-T-only milestone would not avoid the central identity question.

Its deliverable should be three rectangles, deterministic roles, both reflex corners, junction relationships, and exact coverage verification. Keep it separate from renderer activation: returning three wings through today’s caller would immediately expose the failures above.

No code or files were changed. The next prerequisite is agreeing on the three-wing decomposition contract, especially the T bar split. The roadmap still describes T/Z as outside v1; your instruction supersedes that deferral, but this read-only review leaves the roadmap unchanged.