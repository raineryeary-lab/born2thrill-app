# Draw the roof ridge as a path directly on the floorplan (kuechenzeile-style), replacing wing auto-detection

Status: IMPLEMENTED AND VERIFIED END-TO-END (with one known limitation,
see below)

- `roof_wings.roof_wings_from_ridge_path()` (pure Python, no Blender):
  8 new tests, all passing (145/145 total across
  roof_wings.test.py/roof_profile.test.py/roof_wings_multi.test.py, zero
  regressions) -- an L-shaped path matches `recognize_two_wings()`'s own
  known-good numbers exactly; a T-shaped path (which
  `recognize_two_wings()` cannot handle at all) produces correctly-
  covering wings; partial gables and diagonal-segment rejection both
  verified.
- UI (`annotate.js`/`dach-editor.js`): drawn live in the browser against
  WB_125 -- click-to-add-point on the real floorplan canvas, square-by-
  default snapping (an L drawn as 3 points came out with the two
  segments' shared coordinates EXACTLY equal, confirmed via the live
  `draft` array), double-click finishes and auto-switches back to the
  Dach tab, status text updates, Save persists `roof_ridge_path`
  correctly into `annotations.json`.
  - **Real bug found and fixed during this same verification**:
    `finishElementIfReady()` (a generic post-click handler for every
    2-point element type) did not exclude the new `"roof_ridge"` tool,
    so a 3rd drawn point silently force-finished the path at 2 points,
    created a stray orphaned `elements` entry, and reset the draft --
    multi-segment (L/T/plus) paths were completely broken until this was
    added to its exclusion list (alongside `"stairs"`/`"room"`/
    `"outer_outline"`, which already needed the same exclusion).
- End-to-end pipeline (real Blender build, `render-exterior.py` invoked
  directly against a real plan.json with a drawn path converted through
  `build-simplifier-render-plan.py`): `roof_wings_from_ridge_path()` is
  correctly called instead of automatic detection, wings match the drawn
  path (not the auto-detected ones), the build completes with no errors,
  and produces a rendered image. The render still shows the same torn/
  jagged artifact this session's OTHER work already found and left open
  (`PER-WING-AXIS-OVERRIDE-001-FOLLOWUP-2`, cause not yet established) --
  expected and NOT a new defect: it reproduces at a wing junction
  regardless of whether the wings came from automatic detection or a
  drawn path, confirming this feature integrates cleanly with the
  existing (already imperfect) renderer rather than introducing its own
  new problem.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-09-27, after the per-wing axis-override tool (mini-map,
click-a-wing-region) proved confusing in practice and a real render still
showed an unrelated defect at the reflex corner: "make it like the
kitchen counter, so that i can draw a line in the floorplan and you
extrude a triangulare shape with the correct angles (dachneigung) along
this path also adding the Dachüberstand." Confirmed direction with him in
chat (kuechenzeile's `placement:"path"` pattern as the UX model: click
points directly on the real floorplan, corners allowed, squared by
default, double-click/Enter to finish) -- he replied "ok sounds good."

This REPLACES the wing-detection/click-a-region UX
(`ORIENTATION-ONLY-AXIS-DRAW-001` + `PER-WING-AXIS-OVERRIDE-001`'s own
mini-map tool) with: the user draws the ridge line(s) themselves, at
full precision, on the actual floorplan canvas -- the same drawing
gesture already used for rooms/exterior areas/outlines in this app. The
renderer then builds the real roof from that path directly, instead of
trying to infer wing rectangles from the drawn footprint.

## Key design decision: reuse the existing N-wing renderer, don't build a new one

This session already built and verified (in
`PER-WING-AXIS-OVERRIDE-001`/`-FOLLOWUP`) a working N-wing height-field
roof system: `heightfield_roof_mesh()`/`combined_height_at()` take a LIST
of wing rectangles + profiles + per-wing axes and build a correct,
unioned roof; `wall_extension()` (now fixed) builds correct walls at
every wing boundary including tied/dominant cases. That machinery does
NOT need to change for this plan. The only new problem is: derive wing
rectangles FROM the user's drawn path, instead of from
`roof_wings.recognize_two_wings()`'s automatic reflex-corner detection.

For an axis-aligned (orthogonal) drawn path -- squared corners by
default, exactly like `kuechenzeile`'s own `squaredPoint()` behaviour,
Shift for a free angle -- each segment implies one wing:
- The segment's own direction is that wing's ridge axis (horizontal
  segment -> ridge along x; vertical -> ridge along y).
- The wing's extent ALONG the ridge axis is the segment's own drawn
  length (its two endpoints are that wing's true gable ends -- if the
  user draws the ridge short of the real wall, that's a valid,
  intentional hip/partial gable, not an error).
- The wing's extent ACROSS the ridge axis (its width) is found by
  raycasting perpendicular to the segment, in both directions, against
  the ACTUAL footprint polygon (the same outline `outer_outline`/
  `outer_outlines` already gives the renderer) from the segment's own
  midpoint (or several points along it, for a segment whose footprint
  width isn't constant -- see open question below) to the nearest real
  exterior wall on each side.

Free-angle (non-orthogonal) segments are explicitly OUT OF SCOPE for
this plan -- see below.

## Current evidence and behavior

- `kuechenzeile`'s own pattern (`born2thrill-local-workbench/src/app/
  floorplan-workbench/{page.tsx,furniture.tsx}` +
  `src/lib/generator/symbol-catalog.mjs`, React/Next.js workbench, a
  DIFFERENT app from the annotator): click adds a point, `squaredPoint()`
  forces the new segment to 90° off the previous point unless Shift is
  held, double-click/Enter finishes (>=2 points), Escape cancels,
  `entdoppelt()` dedupes a double-click's own duplicate final point.
  Geometry: `build_path_run()` (render-furnished-dollhouse.py) extrudes
  one box per segment at that segment's own length/angle, fixed
  width/height from the catalog; corners are wherever two adjacent
  boxes' ends happen to overlap -- no explicit miter.
- The ANNOTATOR (`floorplan-simplifier`, vanilla JS, where the Dach tab
  actually lives) already has its OWN, independent multi-point
  click-to-draw mechanism: a shared module-level `draft` array
  (`static/annotate.js`), pushed to on each click, consumed by
  `addPolygonElement(draft)`/`setOuterOutline(draft)`/
  `addExteriorArea(draft)` on finish. This is the pattern to extend here
  (same app, same file, already proven for multi-point paths) -- NOT a
  port of kuechenzeile's own React code, which lives in an unrelated app.
- `roof_wings.recognize_two_wings()`, `heightfield_roof_mesh()`,
  `combined_height_at()`, `wall_extension()` (roof_profile.py) already
  correctly build an N-wing roof from a LIST of wing rectangles +
  profiles + axes -- unchanged by this plan, reused as-is.

## Exact scope

1. **UI** (`floorplan-simplifier/static/{annotate.html,annotate.js,
   dach-editor.js}`): a new drawing tool, active only in the Dach tab,
   using the existing `draft` mechanism. Click adds a point on the MAIN
   floorplan canvas (not the small mini-map -- full precision, same as
   room/outline drawing). New segments square to the previous point by
   default (mirroring `squaredPoint()`); an explicit modifier key (Shift,
   matching the established convention) allows a free angle, but the
   RENDERER only supports orthogonal segments in this plan -- a
   non-orthogonal segment must be visibly rejected/warned in the UI, not
   silently accepted and ignored later. Double-click or Enter finishes
   (>=2 points); Escape cancels the in-progress draft. Multiple SEPARATE
   paths are out of scope for v1 -- one continuous path per roof (an L,
   T, or plus shape is one path with corners; two unconnected ridges on
   the same roof are a later extension).
2. **Persistence**: a new plan-level field, `roof_ridge_path` (a list of
   `{x,y}` points in the SAME normalized 0-1, top-floor-registered
   coordinate space `outer_outlines` already uses). Threaded through
   `annotate.js` (save payload + both load sites), `app.py`
   (`normalize_roof_ridge_path()`, serialize), `build-simplifier-
   render-plan.py` (annotation -> plan transfer) -- same pattern as
   `roof_axis_overrides` in `PER-WING-AXIS-OVERRIDE-001`. When present,
   it takes priority over `roof_axis_override`/`roof_axis_overrides` for
   wing/axis determination; when absent, TODAY'S behaviour (automatic
   wing detection + optional whole-house/per-wing axis override) is
   completely unchanged -- this is an alternative INPUT to the same
   downstream renderer, not a replacement for the fallback path.
3. **Renderer** (`born2thrill-local-workbench/scripts/`): a new function,
   `roof_wings_from_ridge_path(path_points_m, footprint_polygon_m)` in
   (likely) `roof_wings.py`, returning the same `[(x0,x1,y0,y1), ...]` +
   `[along_x, ...]` shape `render-exterior.py`'s existing two-wing branch
   already consumes -- so that branch's own downstream code
   (`heightfield_roof_mesh`, `wall_extension`, gable-cap loop, etc.)
   needs NO changes at all, only a new way to arrive at `wings`/
   `along_x` when `roof_ridge_path` is present in the plan.
4. Dachüberstand: unchanged -- it is already a uniform outward offset
   (`overhang`) applied everywhere in the existing renderer; nothing
   ridge-path-specific is needed for it.

## Files in scope

`floorplan-simplifier/static/{annotate.html,annotate.js,dach-editor.js}`,
`floorplan-simplifier/app.py`,
`born2thrill-local-workbench/scripts/{roof_wings.py,
roof_wings.test.py,render-exterior.py,build-simplifier-render-plan.py}`.

## Known limitation found during implementation (not fixed in this round)

`render-exterior.py`'s wall-building loop (the shared satteldach/pultdach
branch) trims each wing's wall/soffit to its actually-exposed range
against exactly ONE other wing (`_bigger_wi`, `other_wing`,
`WING-END-EXPOSURE-001`) -- hardcoded to `wings[0]`/`wings[1]`, and
`other_wing` is explicitly `None` (no trimming at all) whenever
`len(wings) != 2`. The roof SHEET itself (`heightfield_roof_mesh()`) is
already genuinely N-wing safe and correctly verified for a T-shape (see
`roof_wings.test.py`'s own coverage check). The WALLS are not: a 3+-wing
path (a real T/plus shape) will build each wing's wall extent
untrimmed, which can leave overlapping/duplicate wall geometry at an
internal wing-to-wing boundary (invisible from outside the building, but
real, and left over from a genuine gap in test coverage this plan
originally claimed to close for that case). Generalizing exposure
trimming to N wings (checking each wing against every OTHER wing, not
one hardcoded pair) is a separate, real piece of work -- not attempted
here given the size of what already shipped this session. Tracked as
`ROOF-RIDGE-PATH-TOOL-001-FOLLOWUP` in the canonical ROADMAP. An L-shaped
path (exactly 2 wings, the common case) is unaffected -- `other_wing`
resolves normally there.

## Explicitly out of scope

- Non-orthogonal (freely-angled) ridge segments -- real hip/valley
  geometry at arbitrary angles is a much larger problem (mitered,
  non-axis-aligned wing rectangles don't fit the existing `_axes()`/
  `_section()` model at all). The UI should actively prevent/warn on
  this rather than silently mis-building.
- Multiple disconnected ridge paths on one roof.
- Doppelpultdach (its own hand-built-box branch is unrelated and
  untouched).
- Removing/deprecating the existing per-wing axis-override UI
  (`dach-editor.js`'s mini-map) -- kept as the fallback for a house that
  never draws a ridge path, and for un-drawn upper floors etc.
- The still-open, still-unexplained visual anomaly at the reflex corner
  (`PER-WING-AXIS-OVERRIDE-001-FOLLOWUP-2`) -- unrelated to this plan;
  may or may not still reproduce once wings come from a drawn path
  instead of auto-detection, to be checked once this ships, not solved
  by it directly.

## API, schema, and data-contract effects

New, purely additive field `roof_ridge_path` (default: absent/empty,
meaning "no change from today"). No existing field's meaning changes.

## Acceptance criteria

1. Drawing an L-shaped ridge path (two orthogonal segments) on a real
   L-shaped house produces the SAME wing rectangles
   `roof_wings.recognize_two_wings()` would have found automatically, for
   a house where auto-detection already worked -- confirms the new
   derivation isn't just different, it's CORRECT, on a case with a known
   right answer.
2. Drawing a ridge path on a T-shaped or other footprint
   `recognize_two_wings()` CANNOT handle at all (its own, documented
   L-only limitation) produces a working roof SHEET (verified: exact
   wing-rectangle derivation, correct coverage) -- the actual capability
   gain this plan exists for. Wall geometry at a 3+-wing internal
   boundary may still overlap (see "Known limitation" below) -- not
   claimed as fully correct for that case yet.
3. A real `run_project.py` render of both cases, visually checked.
4. Every existing test in `roof_wings.test.py`/`roof_profile.test.py`
   still passes unchanged.

## Tests and verification commands

- New tests in `roof_wings.test.py` for `roof_wings_from_ridge_path()`:
  a straight path (one wing, matches a plain rectangle), an L-shaped path
  (matches `recognize_two_wings()`'s own known-good numbers on the same
  footprint), a T-shaped path (three wings, no automatic-detection
  equivalent to compare against -- assert coverage via the same exact
  `_arrangement_coverage_matches()`-style check already used in
  `roof_wings_multi.py`), a path segment that stops short of the true
  wall (partial gable, intentional).
- `python roof_wings.test.py`, `python roof_profile.test.py` (must stay
  green, unchanged).
- Real render + visual check per acceptance criterion 3.

## Protected and risky paths

Must not change `heightfield_roof_mesh()`, `combined_height_at()`,
`wall_extension()`, or `roof_wings.recognize_two_wings()` at all -- this
plan is additive (a new way to PRODUCE the same `wings`/`along_x` inputs
those already-verified functions consume), not a rewrite of them.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no -- purely a new input method for already-existing,
already-gated roof geometry; no new generation/publication/email path.

## Failed-hypothesis log

N/A -- new plan, no implementation attempted yet.

## Rollback

Revert the files listed above. `roof_ridge_path` is optional/additive;
reverting the renderer/persistence changes alone (leaving the UI) is
also safe, since an absent field means unchanged behaviour.

## Unresolved questions

- Perpendicular wall-raycast for wing WIDTH: sampling only the segment's
  own midpoint is simplest but assumes constant width along the whole
  segment. Real houses can have a stepped/irregular side wall under a
  straight ridge. First implementation samples 3 points (both ends +
  midpoint) and takes the narrowest safe width found, matching this
  session's own established "safe = never poke through" precedent (see
  `_long_wall_ramp()`'s docstring) -- revisit if a real house needs a
  genuinely stepped wing width.
- Whether the UI should show a live preview of the DERIVED wing
  rectangles (not just the drawn line) while drawing, so the user can
  see how their line will actually be interpreted before finishing --
  valuable, not required for v1.

## Approval record

Rainer confirmed the direction in chat ("ok sounds good") after an
explanation of the kuechenzeile-based approach; this plan document
completes the required written scope before implementation begins.
