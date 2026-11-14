# Design review (no implementation): per-wing ridge-axis override for L-shaped roofs

## Context

Two repos, sibling folders under `C:\dev\Floorplan-tools\`:
- `floorplan-simplifier`: the annotator web app (Flask + vanilla JS). The
  Dach tab (`static/dach-editor.js`, `static/annotate.html`,
  `static/dach-referenz.js`) lets a user edit a roof cross-section profile
  and, as of today, draw a ridge-direction line on a small top-down mini-map
  of the building outline. That line's dominant direction (mostly
  horizontal vs. mostly vertical) sets a plan-level field
  `roof_axis_override` ("x"/"y"/null) -- ONE value for the WHOLE house.
- `born2thrill-local-workbench`: the Blender renderer
  (`scripts/render-exterior.py`, `scripts/roof_profile.py`,
  `scripts/roof_wings.py`). For an L-shaped (two-wing) footprint,
  `roof_wings.recognize_two_wings(polygon)` decomposes the real built
  footprint into exactly two overlapping axis-aligned rectangles ("wings")
  -- `wing_a` always spans the FULL x-extent of the whole building,
  `wing_b` always spans the FULL y-extent -- or returns `None` if the
  footprint isn't a simple L (a T/Z, two reflex points, currently falls
  back to a plain hip roof/Walmdach regardless of configured type -- a
  separate, already-known, NOT-in-scope gap; this review is about the
  two-wing L case only).

  Today, `roof_axis_override` is read ONCE and applied UNIFORMLY: every
  wing's own ridge direction is forced to the SAME axis
  (`_u_along_x` in `render-exterior.py`, forwarded into `_axes()` for
  profile scaling, into `wall_extension()` for walls/caps, and into
  `roof_profile.heightfield_roof_mesh()` for the combined roof sheet).
  Without an override, each wing auto-detects its OWN ridge axis
  independently (`_axes(x0,x1,y0,y1, along_x=None)`: whichever of that
  wing's own width/depth is larger).

## What the person I work for wants (confirmed today, not yet built)

Draw TWO separate ridge lines on the mini-map for an L-shaped house -- one
per wing -- each independently forcing that ONE wing's ridge axis, instead
of one setting for the whole house. Confirmed scope: L-shapes only for now
(exactly two wings); T/Z-shape (three-wing) support is explicitly OUT of
scope for this round, tracked separately.

## My own candidate design (UNVALIDATED -- please critique, don't assume it's right)

1. **Data format**: replace/augment the single `roof_axis_override` with a
   list of override points, e.g. `roof_axis_overrides: [{u, v, axis}, ...]`
   where `u,v` are normalized (0..1) coordinates against the DRAWN
   outline's own bounding box, in IMAGE space (x right, y down, matching
   how `dach-editor.js`'s `ctxInfo.outlineBounds` already works), and
   `axis` is "x"/"y". Each point means "wherever this normalized position
   lands, override THAT wing's axis." Rationale: avoids needing the JS
   side and the Python side to agree on an arbitrary "wing index"
   convention (`recognize_two_wings()`'s wing_a/wing_b ordering is an
   internal implementation detail) -- instead, the Python renderer matches
   each REAL wing rectangle to whichever override point falls inside it,
   at render time.
2. **Coordinate mapping**: `dach-referenz.js`'s own existing comment says
   the builder's world Y is a FLIPPED version of the annotator's image Y
   (`Frame.point()`'s `(1-y) * height_mm`), while X is NOT flipped. So a
   drawn point's normalized image `(u,v)` would need to become world-space
   `(u, 1-v)` before being compared against a wing's real
   `(x0,x1,y0,y1)` (itself normalized against the whole footprint's own
   world bounding box) to test containment.
3. **Renderer restructuring (the part I'm least sure is minimal)**:
   `roof_profile.combined_height_at(x,y,wings,profiles,*,along_x=None)`
   currently takes ONE `along_x` and forwards it to EVERY wing's own
   `wing_height_at()` call uniformly. To let two wings have genuinely
   different ridge axes AT THE SAME TIME (needed for the height-field
   sheet to sample each wing's profile correctly), `along_x` would need to
   become a PER-WING list instead of a scalar, threaded through
   `heightfield_roof_mesh()` too (which forwards its own `along_x` into
   `combined_height_at()`). Every other call site in `render-exterior.py`'s
   two-wing branch (profile scaling via `_axes()`, `wall_extension()`,
   the gable-cap loop) is ALREADY per-wing (each already gets its own
   `_axes(*wings[_wi], along_x=...)` call) -- only the shared height-field
   sampling functions are the architectural bottleneck.
4. **Visualization**: to let the user click "this wing" vs. "that wing" on
   the mini-map, `dach-editor.js` would need to know where the two wings
   actually are -- i.e., a JS port of (at least the simple two-rectangle
   case of) `roof_wings.recognize_two_wings()`'s algorithm, so the drawn
   picture matches what the renderer will actually build. This duplicates
   real geometry logic across languages, which is a pattern this same
   codebase already accepts elsewhere (`dach-referenz.js`'s own header
   comment says it deliberately mirrors `roof_profile.py`'s conventions),
   but is real duplication-maintenance risk nonetheless.
5. **Backward compatibility**: existing houses with a single, already-set
   `roof_axis_override` should keep working unchanged -- used as the
   fallback for any wing that has no matching override point in the new
   list, or when the list is absent/empty entirely.

## What I actually need from this review

This is a DESIGN review only -- no code should be written or changed. I
have NOT implemented any of the above; I want your assessment BEFORE
committing to it, since past a certain point today (documented in
`born2thrill-local-workbench/plans/WING-END-EXPOSURE-001.md` and
`SATTELDACH-HEIGHTFIELD-AXIS-001.md`) hand-guessed fixes in this exact
"per-wing axis" area went wrong more than once before being corrected by
actual measurement. Please:

1. **Confirm or correct point 3** -- is `along_x` really only a bottleneck
   in `combined_height_at()`/`heightfield_roof_mesh()`, or are there other
   call sites/assumptions in `roof_profile.py` or `render-exterior.py`
   that implicitly assume a single, uniform axis across all wings that I
   have missed? Read the actual current code, don't take my summary on
   faith.
2. **Is the normalized-point-matched-by-containment data design (point 1)
   actually the simplest robust option**, or is there a cleaner one (e.g.
   should the JS side just be authoritative about wing geometry and send
   real wing rectangles rather than points)?
3. **Any real correctness risk in the coordinate flip (point 2)** -- is
   there an existing tested helper I should reuse instead of hand-deriving
   the `(u, 1-v)` mapping again (this exact "y flip" class of bug has bitten
   this codebase before, per that file's own comments)?
4. **Rough scope/complexity estimate**: does this look like a contained,
   single-session change, or does it have hidden depth (e.g. interaction
   with floor registration/`registriertePunkte()`, the doppelpultdach
   hand-built-box branch, or the wall-exposure-trimming work from earlier
   today) that would make it materially bigger than it looks?
5. **Anything about T/Z-shape support (out of scope for implementation, but
   in scope for this design)** that this design would accidentally make
   HARDER later if built the way I'm proposing -- i.e., does the
   normalized-point format generalize to three wings later, or would it
   need to be redesigned again?

## Out of scope for this review

- Do not propose or write any actual code changes.
- Do not attempt to also design T/Z-shape (three-wing) roof-building itself
  -- only comment on whether today's per-wing-override design would need
  rework to extend there later (point 5 above).
- The already-fixed axis-forwarding bug, the wall-exposure-trimming fix,
  and the heightfield grid-snap fix from earlier today are DONE and
  verified -- not in scope to re-review.

## Output format

A short "assessment" section per numbered question above (confidence:
high/medium/low, and whether you're inferring or have directly verified
against the real code), then a final "recommendation" section: proceed
with this design as-is, proceed with named modifications, or reconsider
the approach entirely -- with your reasoning, not just a verdict.

---

## Codex output

## 1. Assessment: per-wing axis plumbing

**Confidence: high — directly verified against current code; wall example below is analytical, not render-tested.**

Your point 3 is correct about the **shared sampling API**, but incomplete about the overall change. [`combined_height_at()`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:260) forwards one scalar to every wing; `heightfield_roof_mesh()` forwards that same scalar. Both need per-wing axis information. Single-wing functions can retain scalar arguments.

Four additional considerations matter:

- **The current renderer does not auto-detect independently per wing when the override is absent.** [`_u_along_x`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1380) falls back to the **whole-building** automatic axis, then passes that boolean everywhere. The helpers support independent automatic axes, but this renderer path does not exercise that behavior. Preserve this actual legacy behavior unless changing it is explicitly intended.
- **The shared profile has an axis-dependent reference span.** The same block resolves `_design_profile` against `_design_span_m`, then scales it to each wing. Independent wing directions still need one clearly defined reference span for the editor’s saved heights and slopes. Keeping the existing whole-building reference is a contained choice; silently switching its axis when either wing changes would alter both wings’ pitch.
- **Vertical-step profiles bypass the proposed plumbing entirely.** [`has_vertical_step(_design_profile)`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1407) enters the hard-coded box branch, with fixed positions, dimensions and Y rotations. This is not gated to one house. Per-wing axis forwarding would not make those roofs respond.
- **Wall ownership needs validation for the newly allowed mixed-axis combinations.** The current area-based dominance rule chooses which wing builds a coincident exterior boundary, without comparing their roof heights. Mixed axes can make the dominant wing’s low eave coincide with the subordinate wing’s tall gable.

A concrete example of that last issue: wing A spans `12 × 4`, wing B spans `4 × 10`, both anchored at `(0,0)`. Give A an X ridge and B a Y ridge. A wins dominance by area. Along their shared south boundary, A has an eave while B has a gable. The current trimming can suppress B’s central gable while A contributes no comparable closure. This follows from [`wall_extension()`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:771) and its tie handling; it is a **new-combination concern**, not a re-review of today’s verified fix.

One subtlety: `_axes(*other_wing, along_x=along_x)` inside that function is **correct coordinate projection into the current wing’s frame**. It should not automatically receive the other wing’s roof axis.

## 2. Assessment: point containment versus alternatives

**Confidence: high on containment ambiguity; medium on the preferred product contract.**

**Unrestricted point containment is not robust as proposed.** The rectangles deliberately overlap. A point in the overlap belongs to both wings; even a wing’s rectangle centre can lie there. Two points can also select the same wing.

If retaining points, the contract needs:

- An anchor strictly inside the selected wing’s **exclusive region**, with clearance from boundaries.
- Exactly one matching wing; ambiguous, unmatched or duplicate assignments must not silently choose a winner.
- Defined handling when outline edits invalidate an assignment.
- A distinction between the selection anchor and the drawn line’s midpoint. A valid ridge-direction gesture can cross the overlap.

For L-shapes alone, semantic identifiers such as **“full-X-span wing” and “full-Y-span wing”** are actually simpler than containment. They express the documented decomposition contract, rather than exposing arbitrary array indices. [`recognize_two_wings()`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:118) already guarantees these roles.

**I would not make JS-supplied rectangles authoritative for construction.** They could disagree with the renderer’s registered, regularized geometry. A JS preview can be useful, but duplicating just the recognizer does not guarantee matching results: the input geometry and tolerances must agree too.

My preference: semantic selectors for this strictly two-wing feature, or constrained anchors if avoiding an L-specific persisted identifier is the stronger priority. Both are cleaner than arbitrary containment.

## 3. Assessment: coordinate flip and existing helpers

**Confidence: high — directly verified; normalization invariance is mathematical inference.**

The Y flip is correct **when both bounding boxes describe corresponding geometry**:

`worldX = xmin + u × width`  
`worldY = ymin + (1 − v) × depth`

[`Frame.point()`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/build-simplifier-render-plan.py:648) confirms X is preserved and Y is flipped. Reflection does not exchange the `"x"` and `"y"` axis labels.

The qualifications are more significant than the flip itself:

- [`computeContext()`](/C:/dev/Floorplan-tools/floorplan-simplifier/static/dach-editor.js:155) calculates dimensions from registered points but returns **raw `points`** for `outlinePoints` and `outlineBounds`. Its nearby comment overstates what the returned mini-map geometry represents.
- Current registration uses positive, separate X/Y scale-and-translation transforms. Bounding-box-normalized positions survive those transforms, so registration **alone** does not invalidate `(u, 1-v)`.
- `RegisteredFrame` also snaps geometry; the renderer traces and regularizes the top-storey wall loop. These operations can change relative boundaries.
- Recognition actually receives the **overhang-offset roof polygon**, not the unexpanded drawn outline. See [`roof_poly`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1265). Normalizing a drawn-wall anchor directly against that roof bounding box shifts its physical interpretation.

Existing reusable pieces are `registriertePunkte()` and its alignment helpers on the JS side, and `Frame`/`RegisteredFrame` in the builder. Their behavior has test coverage. **I found no existing end-to-end helper that maps an outline-relative anchor to a rendered wing.** `dachKanten()` supplies edge labels, not that mapping.

Define the source floor, reference outline and wall-versus-roof bounds explicitly before adopting anchor coordinates.

## 4. Assessment: scope and complexity

**Confidence: medium — estimate based on verified dependencies, without implementation or new renders.**

This is **larger than a two-function threading change**, and I would not promise a complete single-session implementation.

Persistence also crosses:

- [`annotate.js`](/C:/dev/Floorplan-tools/floorplan-simplifier/static/annotate.js:3488): save and load paths.
- [`app.py`](/C:/dev/Floorplan-tools/floorplan-simplifier/app.py:5875): normalization and serialization.
- [`build-simplifier-render-plan.py`](/C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/build-simplifier-render-plan.py:3857): annotation-to-plan transfer.

For the generic height-field branch, **roughly 2–4 focused engineering days** is a more credible planning allowance for UI, persistence, contracts and measured verification. That estimate assumes the reference-span decision is settled and mixed-axis boundary closure remains contained.

Supporting the hand-built vertical-step branch could materially exceed that allowance; it requires a separate design decision before estimating.

Verification should cover all four axis pairs, mirrored L orientations, unequal wings, legacy fallback, registered upper floors, and roof/wall agreement at coincident exterior edges. Passing existing helper tests alone would not establish that agreement.

## 5. Assessment: future T/Z compatibility

**Confidence: medium — design inference grounded in the current interfaces.**

A list of anchors can accommodate three entries, but **list length is not the difficult part**. Future decompositions may have different overlaps, ambiguous ownership or unstable rectangle identities. Unique containment needs an explicit contract regardless of wing count.

Semantic full-X/full-Y selectors are deliberately L-specific and would need an additional identification scheme later. They need not invalidate existing L records.

The internal representation should associate each resolved wing with its own axis and profile, independently of how the UI identifies it. That preserves an N-wing sampling path. The existing single-`other_wing` exposure interface and two-wing dominance logic will require separate future work regardless of the persisted override format.

## Recommendation

**Proceed with named modifications, not as-is.**

Before committing, settle:

1. Unambiguous wing selection: semantic L roles or exclusive-region anchors.
2. The profile’s shared reference span and actual legacy fallback behavior.
3. Whether vertical-step roofs are supported in this round; current box geometry will ignore the proposed axis plumbing.
4. Mixed-axis wall closure at coincident exterior boundaries.

The per-wing sampling extension is sound. The larger risks are **wing identity, coordinate provenance and exterior closure**, rather than passing a list through two functions.

No files were changed, and I did not re-run or reopen today’s completed fixes. The next implementation prerequisite is resolving those four decisions; T/Z support remains the separately tracked follow-up.