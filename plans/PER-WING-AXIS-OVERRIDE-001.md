# Per-wing ridge-axis override, drawn one line per wing on the Dach-tab mini-map

Status: IMPLEMENTED -- UI, persistence, and renderer wiring all shipped
and verified end-to-end. The wall-height defect this plan's own
verification first found (a dominant wing's wall falling short of the
true combined roof at a shared/tied boundary) is now FIXED and verified
in `PER-WING-AXIS-OVERRIDE-001-FOLLOWUP.md`. That same verification also
found a THIRD, separate, still-open bug
(`PER-WING-AXIS-OVERRIDE-001-FOLLOWUP-2`, SOLIDIFY's automatic rim-fill
mishandling the L-shaped roof sheet's own non-convex perimeter) that
produces a torn/jagged patch near the reflex corner of ANY L-shaped
satteldach/pultdach house -- confirmed present regardless of whether the
two wings' axes agree or disagree, so it is not specific to this
feature's own per-wing override at all, but it does mean an L-shaped
house will still not render cleanly until it's fixed too.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Today's Dach-tab draw tool (`ORIENTATION-ONLY-AXIS-DRAW-001`, complete and
shipped 2026-09-26) originally set only ONE `roof_axis_override` for the
whole house. For an L-shaped (two-wing) house, Rainer wants to draw TWO
separate ridge lines, one per wing, each independently forcing just that
wing's own ridge direction: "doesnt work i need to make the first b< han
and even add a new one if needed" / "Dach tab still only draws one line."
Confirmed scope: L-shapes (two wings) only -- T/Z-shape (three-wing)
support stays out of scope (`TZ-WING-RECOGNITION-001` built recognition
only, deliberately not wired into this).

## What shipped

The four open decisions from the design-review phase are now settled by
implementation:

1. **Unambiguous wing selection**: semantic L-roles, exactly as Codex
   recommended -- `wingA` (the full-X-span wing) / `wingB` (the full-Y-span
   wing), the SAME naming `roof_wings.recognize_two_wings()` already
   guarantees. A JS port (`recognizeTwoWings()`/`pointInPolygon()`/
   `_reflexVertices()` in `dach-referenz.js`) lets the annotator UI
   recognize the same two wings for click-targeting, independent of the
   renderer.
2. **Shared reference span**: left untouched, per Codex's own
   recommendation (point 2 of the original review) -- `_design_profile`/
   `_design_span_m` in `render-exterior.py` stay a single whole-building
   reference; only ridge DIRECTION is per-wing, not profile scaling.
3. **Doppelpultdach hand-built-box branch**: confirmed still untouched --
   it never calls `heightfield_roof_mesh()`/`combined_height_at()`, so it
   is unaffected by this whole feature, same as originally assumed.
4. **Mixed-axis wall closure**: not given a NEW bespoke rule. The existing
   dominant-wing wall-exposure logic (`WING-END-EXPOSURE-001`) is
   independent of ridge axis already (it trims by exposed footprint range,
   not by which axis the roof above happens to use) and did not need to
   change. Real verification of this specific risk (a dominant wing's low
   eave meeting a subordinate wing's tall gable) is the one item still
   pending a measured render -- see "Verification" below.

## Implementation summary

- **UI (`floorplan-simplifier/static/`)**:
  - `dach-referenz.js`: added `recognizeTwoWings()`, `wingAt()`,
    `pointInPolygon()`, `_reflexVertices()`, `_signedArea()`,
    `_gridCoverageMatches()` -- a faithful JS port of
    `roof_wings.py::recognize_two_wings()`. 8 new tests (27/27 total in
    `dach-referenz.test.mjs`, including an exact-number match against
    Python's own `roof_wings.test.py` fixture).
  - `dach-editor.js`: the Dach-tab mini-map now recognizes an L-shaped top
    floor's two wings and draws them as distinct colour-coded, labelled
    (A/B) rectangles. Clicking + dragging + double-click inside a wing's
    area draws THAT wing's own ridge line, written to
    `roofAxisOverrides[wingA|wingB]`; clicking outside both (or on a
    rectangular/non-L house, where no wings are recognized at all) keeps
    the original whole-house behaviour (`roofAxisOverride`). Right-click
    resets whichever wing (or, outside both, the whole house) is under the
    cursor back to automatic.
  - **Overlap-click fix found live-testing WB_125**: `wingAt()`'s own
    contract deliberately answers `null` in the wings' geometric overlap
    (correct for a shared pure function with no visual stacking to lean
    on -- recognize_two_wings() always gives each wing its full bbox along
    one axis, so the smaller wing's box is mostly INSIDE the bigger one).
    But this canvas draws wingB last (visually on top in the overlap), so
    a first pass reusing `wingAt()` directly made most of the visibly-green
    "wingB" box silently fall through to "whole house" on click -- confirmed
    live (clicking inside the solid-looking green area cleared the
    whole-house override instead of touching wingB). Fixed by giving
    `dach-editor.js` its own stacking-aware target resolver
    (`axisDrawWingAt()`): last-drawn wing wins the overlap, matching what
    the user actually sees. `wingAt()` itself is untouched -- its
    conservative "don't guess" contract is still correct for any OTHER
    caller without a visual stacking order to fall back on.
- **Persistence**: `annotate.js` (save payload + both load sites),
  `app.py` (`normalize_roof_axis_overrides()`, save/serialize),
  `build-simplifier-render-plan.py` (annotation -> plan transfer) all
  carry `roof_axis_overrides` (`{wingA?: "x"|"y", wingB?: "x"|"y"}`)
  end-to-end, alongside the untouched legacy `roof_axis_override`.
- **Renderer (`born2thrill-local-workbench/scripts/`)**:
  - `roof_profile.py::combined_height_at()` now accepts EITHER a scalar
    `along_x` (old behaviour, unchanged) OR a list/tuple, one entry per
    wing -- letting each wing resolve height against a genuinely different
    forced axis at the same time. 93/93 tests pass (92 existing + 1 new:
    `test_combined_height_at_accepts_a_per_wing_axis_list`).
  - `render-exterior.py`: builds `_wing_along_x` (one resolved axis per
    wing: that wing's own override, else the whole-house override, else
    automatic) right after `_design_profile` is resolved, and threads it
    through every per-wing geometry call that used to share one
    `_u_along_x` for the whole roof: the wing/sheet profile loops, the
    `heightfield_roof_mesh()` call, the gable-cap loop, and the
    wall-extension loop.

## Verification

- `roof_profile.test.py`, `roof_wings.test.py`, `roof_wings_multi.test.py`:
  134/134 pass, zero regressions.
- `dach-referenz.test.mjs`: 27/27 pass.
- Live browser test against WB_125 (a real L-shaped house,
  `german_catalog_review_bungalow_4_3_1_wb_125`): wings correctly
  recognized and drawn; a click in wingA's unique area, wingB's unique
  area, AND the wings' deliberate overlap all correctly targeted the
  right wing (after the overlap-click fix above); right-click reset
  verified via a dispatched `contextmenu` event (the Browser pane's own
  `right_click` action does not reliably dispatch one in this sandbox --
  a tooling limitation, not a product bug).
- **Found and fixed during this same verification**: the
  `floorplan-simplifier` dev server (`app.py`, a plain
  `BaseHTTPRequestHandler`, no autoreload) had been running since
  2026-09-26 09:23 -- BEFORE today's `roof_axis_overrides` server-side
  changes were written to disk. Every save through it silently dropped
  the new field (present in the save payload, present in `write_annotations()`'s
  in-memory `saved` dict, absent from the file actually written) with NO
  error, because the code computing it had simply never been loaded into
  the running process. Restarted the server; a save immediately afterward
  persisted `roof_axis_overrides` to `annotations.json` correctly, and
  `build-simplifier-render-plan.py` was confirmed to carry it into the
  render plan JSON unchanged. This class of bug (stale long-running dev
  server silently serving pre-edit code with no error) is worth an
  explicit note for future sessions against this repo.
- **Real mixed-axis render, result: CONFIRMED DEFECT, not a false alarm.**
  Ran `run_project.py german_catalog_review_bungalow_4_3_1_wb_125 --styles
  classic --finishes classic-a` with `roof_axis_overrides: {wingA: "x",
  wingB: "y"}` actually saved (deliberately opposing axes -- the exact
  worst case Codex's original review described). The build completed with
  exit code 0 and every automated check passed (`R1_nothing_floats`,
  `wall_angles`, `opening_count`, `render_log`, etc. -- none of these
  checks happen to look at roof-sheet continuity specifically). The
  rendered `exterior-satteldach-baseline.png` shows the predicted failure
  visually: at the wings' shared boundary the two roof sheets do not meet
  -- a jagged, torn edge and overlapping/mismatched facets where wingA's
  ridge (running one way) and wingB's ridge (running the other way) hit
  each other, instead of a clean hip/valley line. This is the same failure
  shape as Codex's worked example (12x4 wing with an X ridge against a
  4x10 wing with a Y ridge, central gable left unclosed) -- confirmed with
  a REAL measured render on REAL house geometry, not just re-stated as a
  theoretical risk.
  - This means: the data plumbing (UI -> save -> plan -> renderer) is
    correct and complete, but per-wing axis override is only
    GEOMETRICALLY SAFE today when the resolved axes for both wings agree
    (same override, or one/both left automatic and auto-detection happens
    to agree -- the situation every house built before this feature
    already relied on). Deliberately forcing two wings to DISAGREE
    reliably breaks the roof.
  - Not fixed in this round: doing so needs the actual design decision
    Codex's original review asked for (open decision 4) -- e.g. an
    explicit hip/valley seam construction at the wings' shared boundary
    when axes disagree, not just independent per-wing sheets that
    assume they'll happen to line up. Tracked as a follow-up below.
  - WB_125's saved annotation was reset back to `roof_axis_overrides: {}`
    (its pre-existing, clean state) after this test -- the deliberately
    broken configuration was not left saved on this QA house.

## Follow-up (recorded in the canonical ROADMAP.md too)

**PER-WING-AXIS-OVERRIDE-001-FOLLOWUP: mixed-axis roof-junction closure.**
When `roof_axis_overrides.wingA` and `.wingB` are both set and disagree,
`render-exterior.py` currently builds each wing's roof sheet/wall
independently against its own forced axis and does not construct an
explicit seam where they meet -- confirmed by a real render (see
"Verification" above) to leave a torn, unclosed junction. Needs an actual
design decision (Codex's original open decision 4), likely an explicit
hip/valley construction at the wings' shared boundary specifically for
the disagreeing-axis case, not just more independent-sheet tuning. Until
fixed, `dach-editor.js` shows a visible warning in the Dach-tab when both
wings' overrides disagree, but does not block saving that combination.

## Files in scope (final)

`floorplan-simplifier/static/{dach-editor.js,annotate.js,dach-referenz.js,dach-referenz.test.mjs}`,
`floorplan-simplifier/app.py`,
`born2thrill-local-workbench/scripts/{render-exterior.py,roof_profile.py,roof_profile.test.py,build-simplifier-render-plan.py}`.

## Explicitly out of scope

- T/Z-shape (three-wing) roof support -- recognition-only groundwork exists
  (`TZ-WING-RECOGNITION-001`, complete but disconnected from the renderer),
  wiring it into per-wing overrides is a separate future task.
- The doppelpultdach hand-built-box branch -- confirmed unaffected, not
  extended.

## Rights, provenance, privacy, and security impact

None. WB_125 is an internal QA test house already used throughout this
session for render verification, not a customer-delivery candidate.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. Confirmed -- this only changes which ridge axis a
wing's own roof geometry is built with; it adds no new
generation/publication/email path, and every change stays behind the
existing manual save/build/review gates.

## Rollback

Revert the files listed above. The new `roof_axis_overrides` field is
purely additive and defaults to `{}` (behaves exactly like before) for
every project that never uses the new per-wing draw tool, so a partial
rollback of only the UI (leaving the renderer/persistence changes in
place) is also safe.

## Approval record

Implementation explicitly requested by the user ("do it i will be out
with the dogs for a walk", after design review + open-decisions review),
continued and completed following "still doesnt work" / "Dach tab still
only draws one line" feedback that identified the concrete remaining gap.
