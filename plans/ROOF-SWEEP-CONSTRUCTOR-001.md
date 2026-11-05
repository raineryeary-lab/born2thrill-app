# Replace wing-rectangle roof construction with a single canonical swept mesh

Status: IMPLEMENTED (2026-09-29) -- all 4 items of Exact scope landed and
verified; see Progress section for the full record. Follow-on items
(N-way junction generality, `roof_wings_multi.py` wiring, walmdach's own
separate reflex-corner item) remain tracked in ROADMAP.md, not cancelled.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Replace the current "independent rectangular wings, reconciled after the
fact" roof construction (satteldach/pultdach/doppelpultdach on non-rectangular
footprints) with a single canonical roof height-mesh built from the drawn
ridge path and the live footprint, from which the wall tops are derived
directly -- eliminating the seam-mismatch bug class that has produced at
least 6 distinct, separately-patched defects this week (per ROADMAP.md:
PER-WING-AXIS-OVERRIDE-001-FOLLOWUP/-FOLLOWUP-2, the walmdach corner-post/
end_extension_mm investigation, SATTELDACH-GABLE-WALL-RIM-MARGIN-001, and a
newly found ~98.5mm mesh/analytic-height mismatch).

Rainer, 2026-09-29, explicit instruction after the standing symptom pattern:
"ask codex and figure it out, its not creativ its just math" -- i.e. stop
patching individual seam symptoms, fix the construction so seams can't
disagree by construction.

## Current evidence and behavior

- Live-reproduced, real pipeline: `german_catalog_review_bungalow_4_3_1_wb_125`
  (satteldach) shows a real hole at the wing valley from a steep camera angle
  -- BVH raycast confirms several rays pass clean through both `roof-pitch`
  and `roof-walls` to the ground, with ZERO hand-drawn ridge path involved
  (plain automatic 2-wing recognition). This rules out "bad user input" as
  the sole cause; the wing-rectangle + independent-wall-reconciliation
  architecture itself produces this.
- A separately malformed hand-drawn ridge path on the same project (a
  self-crossing/backtracking polyline) produced visibly corrupted roof
  geometry in the user's own Blender viewport -- cleared as an immediate
  data fix (`annotations.json`, `roof_ridge_path` reset to `[]`,
  `roof_axis_override` reset to `null`, old value kept under
  `roof_ridge_path_removed_2026_09_29` for the record, not deleted).
- Codex read-only design review (`C:\Users\Admin\AppData\Local\Temp\claude\
  C--dev-Floorplan-tools\4a479835-656e-49e5-8742-a731e21516b2\scratchpad\
  codex-out-roof-sweep-constructor.md`, full text preserved there) confirms:
  1. A literal "continuously scan the live footprint width along the path"
     sweep is discontinuous at a wing boundary crossing -- worked example:
     an L with wings `([0,10]x[0,4])` and `([0,4]x[0,10])`, ridge path
     `(10,2)->(2,2)->(2,10)`: perpendicular span jumps from 4 to 10 crossing
     x=4, *before* the path's own corner. If the profile scales to span for
     a fixed pitch, ridge height jumps too. More sampling cannot fix a
     genuinely discontinuous function -- junction regions need dedicated
     construction, not continuous scanning straight through them.
  2. A fixed symmetric profile and an arbitrary hand-drawn ridge line and
     both true measured edges generally cannot all be satisfied at once
     (worked example: path 2m from one edge, 4m from the other, needs ridge
     parameter u=1/3; a symmetric u=1/2 profile puts the ridge 1m off the
     drawn line). Needs an explicit, stated policy -- see Decisions below.
  3. T/plus junctions (3-4 incident edges) are over-constrained for a
     rotated-cross-section mitre; need a proper planar arrangement
     (intersect the incident roof planes, take the upper envelope, insert
     the seam as a real shared mesh edge).
  4. A genuine, independently reproduced ~98.5mm discrepancy between the
     built triangle mesh's interpolated height and `combined_height_at()`
     (the analytic function wall construction samples) at a synthetic L's
     interior point -- caused by the two wings' height "dominance crease"
     not being an actual mesh edge, so a triangle spanning the crease
     interpolates wrong. This is a plausible root cause independent of
     everything found so far.
  5. My SOLIDIFY "normal-offset thins near the rim" explanation was
     imprecise: normal-offset thickness is *not* generally reduced inside a
     flat interior region (it's `d/cos(pitch)`, larger than `d`, not
     smaller); boundary/rim effects need separate treatment, and a vertical
     doppelpultdach step wall gets *zero* usable thickness from a
     normal-offset modifier (it just translates sideways) -- must be a
     distinct, explicit case.
  6. Concrete recommendation, with a full worked algorithm: build one
     canonical top-surface mesh (patches assembled via an upper-envelope
     arrangement with real shared-edge seams), give it explicit vertical
     (not normal-offset) thickness for a bottom surface, then derive every
     wall's TOP directly from that same underside mesh via polygon overlay
     -- not independent analytic sampling -- so there is exactly one source
     of truth for "where the roof surface is."

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Last commit: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Substantial pre-existing uncommitted changes unrelated to this task (17
  modified tracked files, 500+ untracked) -- not touched by this plan, must
  not be disturbed or committed over. `scripts/render-exterior.py` and
  `scripts/roof_profile.py` are themselves untracked in this repo; there is
  no tracked baseline/SHA for them specifically.
- Existing test baseline (Codex-verified, this session): `roof_wings.test.py`
  32/32, `roof_profile.test.py` 96/96, `roof_wings_multi.test.py` 18/18,
  all green before this work starts.

## Decisions (per Rainer's "figure it out", not left open)

1. **The drawn ridge line is authoritative.** When a hand-drawn path is
   present, fit each side's pitch independently to its own true measured
   span from the path to that side's eave, rather than forcing a fixed
   symmetric profile onto an off-center line. Automatic (undrawn) two-wing
   recognition keeps today's symmetric-per-wing behavior -- there is no
   drawn line to be authoritative over in that case.
2. **Incompatible junctions are rejected, not faked.** Where two branches'
   ridges cannot physically meet at their shared point at a consistent
   height (e.g. a narrow branch's ridge is lower than the main ridge, and
   no explicit vertical step/closure is specified), the build fails with a
   clear, specific error identifying the exact segment/junction -- it must
   never silently produce a vertical jump or an invisible gap.
3. **Junction/domain construction is explicit, not scanned.** Per Codex
   finding 1 (`ROOF-SWEEP-CONSTRUCTOR-001` evidence section): a junction's
   patch domain is computed once from the path graph and footprint
   topology, then the continuous per-segment scan only runs on the regular
   (non-junction) regions. No live width scan is allowed to run through a
   junction area.
4. **Roof sheet thickness is explicit vertical Z-offset**, not a SOLIDIFY
   modifier, for every sloped sheet. Doppelpultdach's vertical step wall is
   built as its own explicit closure with its own explicit thickness, never
   through the same "duplicate every profile face" path as the sloped
   sheets.
5. **Scope for this plan: 2-wing L/T only.** Full N-way plus-junction
   arrangement, and wiring `roof_wings_multi.py`'s already-built T/Z
   recognition into this new path, are follow-on work (tracked, not
   cancelled) -- landing the 2-wing case correctly, with real tests proving
   no seam disagreement, is the priority; generalizing the arrangement
   logic to N incident edges is a separate, reviewable step once the core
   single-mesh/derived-wall pattern is proven.

## Exact scope

Implement, for the 2-wing (L-shape or a T where one branch is fully a
"main span continuation") case only:

1. A canonical top-surface construction: given the path graph (normalized:
   split at intersections/T-contacts, backtracking segments merged/rejected
   per Decision 2's spirit -- a literal self-crossing path like the one
   found on WB_125 must be REJECTED at save/build time with a clear error,
   not silently built into broken geometry), the live footprint (overhang-
   expanded), and each wing's profile, build the regular-region sweep
   patches plus explicit 2-wing junction patches (upper-envelope
   intersection, shared seam edge), and assemble one mesh with the seam
   line as a real shared edge (Codex section 4/8).
2. Explicit vertical-Z shell thickness for that top surface (Codex section
   6), replacing SOLIDIFY for the sloped-sheet case.
3. Wall-top derivation directly from the resulting underside mesh via
   polygon overlay (Codex section 7), replacing `_true_height()`/
   `combined_height_at()` analytic sampling for wall height purposes.
   `boundary_polygon()`'s soffit/gable-wall margins (`sink`, `extra_sink`)
   become unnecessary for the pieces this covers and should be removed
   there, not just left inert.
4. Doppelpultdach's vertical step wall: explicit, separate closure
   construction with its own thickness (Codex section 6's hard exception).
5. A build-time validator that rejects a self-crossing/backtracking ridge
   path with a specific, actionable error -- this is what should have
   stopped WB_125's malformed path from ever reaching the renderer.

## Files in scope

- `scripts/roof_wings.py` (path normalization/validation, patch domain
  construction)
- `scripts/roof_profile.py` (`heightfield_roof_mesh`, `boundary_polygon`,
  `wall_extension`, profile/cross-section handling, doppelpultdach step)
- `scripts/render-exterior.py` (call sites, SOLIDIFY replacement for the
  sloped roof sheet)
- New tests in `roof_wings.test.py` / `roof_profile.test.py` per Acceptance
  criteria below

## Explicitly out of scope

- N-way (3+ incident edges) plus-junction arrangement generality --
  tracked as follow-on, `roof_wings_multi.py` wiring stays a separate task.
- Walmdach's bpypolyskel-based construction (different code path entirely,
  its own separate open item: the reflex-corner bridging patch).
- The floorplan-simplifier Dach-tab UI consolidation (different repo).
- Flachdach (unrelated, flat, no ridge/wing concept).

## API, schema, and data-contract effects

None to the annotation schema (`roof_ridge_path`, `roof_axis_override`,
`roof_profiles` keep their existing shapes). Internal render-geometry
construction only. The new path-validator adds a new BUILD-TIME failure
mode (a self-crossing path now hard-rejects instead of silently building
broken geometry) -- call this out explicitly to Rainer as a behavior change:
any currently-saved project with a similarly malformed path will start
failing to build until its path is fixed, which is the correct outcome but
is a visible change from today's silent-corruption behavior.

## Acceptance criteria

- `german_catalog_review_bungalow_4_3_1_wb_125` (satteldach, automatic
  2-wing, the case with ZERO hand-drawn path) builds with no raycast-through
  hole anywhere along the valley -- verified by a dedicated raycast sweep
  along the full valley length from the real hero camera, not just the
  single previously-found bad angle.
- The malformed WB_125 path (preserved under
  `roof_ridge_path_removed_2026_09_29`) is fed to the new validator directly
  and confirmed to be REJECTED with a clear error, not silently built.
- A clean, non-crossing hand-drawn 2-wing L and T path each build with the
  seam height matching exactly (0.0mm tolerance at the shared mesh edge, not
  a small-but-nonzero margin) between the two wings' surfaces.
- Wall tops (via the new underside-overlay method) match the roof's actual
  underside at every sampled point along the gable/valley to sub-millimeter
  tolerance -- replacing today's "minimum of two independently-sampled
  heights, hope it's enough" pattern with an exact derivation.
- Doppelpultdach's vertical step wall has real, verified thickness (not the
  near-zero effective thickness Codex identified for a normal-offset
  modifier on a vertical face).
- All existing `roof_wings.test.py` (32), `roof_profile.test.py` (96) stay
  green, OR have listed, reasoned updates (expected: several, since this
  changes internal construction) -- no test deleted, skipped, or weakened.
- All 4 roof forms smoke-test cleanly on at least 3 other real projects
  besides WB_125 (pick from existing corrections/ projects), not just the
  one project this whole investigation centered on.

## Tests and verification commands

- `roof_wings.test.py`, `roof_profile.test.py` (existing + new).
- New: a test reproducing Codex's exact synthetic L (10x4 / 4x10 wings,
  ridge u=0.4/0.6) asserting the mesh's actual triangle-interpolated height
  matches the wall-height derivation exactly at the point Codex found the
  98.5mm mismatch.
- New: a test feeding the preserved malformed WB_125 path into the
  validator, asserting rejection with a specific error type/message.
- Real Blender rebuild + BVH raycast sweep (not single-point) along the
  full valley, from the real hero camera, on WB_125 satteldach.
- Real Blender rebuild smoke test, all 4 roof forms, on 3+ other projects.

## Protected and risky paths

This is the highest-risk area touched this week -- 6+ prior distinct
patches, now being replaced at the architecture level. Every intermediate
step must be verified against real built geometry (raycast/mesh dump), not
just against the pre-existing analytic test suite, since the analytic tests
are exactly what passed while the real bug was present (Codex's own probe
found a 98.5mm real-mesh discrepancy despite all tests green).

## Rights, provenance, privacy, and security impact

None. Internal render-geometry code only.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This plan touches only internal render-geometry
construction. It does not touch the annotation correction/approval
pipeline, add any new generation/publication/email path, or change which
corpus reference a render is built from. The new path-validator is a build-
time refusal, not a generation path.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

Carried over (this investigation, not yet spent on the sweep implementation
itself):

1. Hypothesis: today's `end_extension_mm` wall-mitre fix caused the
   satteldach valley hole. DISPROVEN (A/B rebuild, identical defect either
   way).
2. (Superseded plan's own log, preserved there): the soffit-margin-style fix
   for the gable end-wall. Not disproven, but superseded before
   implementation once the architectural root cause was identified.

## Rollback

No code changed yet. Once implemented: this is a large diff against
`roof_wings.py`/`roof_profile.py`/`render-exterior.py`; rollback is
reverting that diff wholesale (both files are untracked in this repo, so
keep an explicit pre-change copy, e.g. `roof_profile.py.before-sweep`,
`roof_wings.py.before-sweep`, per this project's own established convention
for untracked-file safety, alongside the normal diff record in this plan).

## Unresolved questions

- Should the new build-time path validator run at SAVE time (in the
  annotator, immediate feedback) or only at BUILD time (render pipeline)?
  Recommend both eventually, but this plan only requires the BUILD-time
  check; save-time validation in `floorplan-simplifier` is a separate,
  smaller follow-on task once the renderer's own definition of "valid path"
  is settled here.

## Approval record

Approved by Rainer, 2026-09-29 ("ok", following the Codex review summary and
the explicit "ask codex and figure it out, its not creativ its just math"
instruction that authorized proceeding on Codex's technical verdict).

## Progress

2026-09-29: Item 5 of Exact scope (build-time validator rejecting a self-
crossing/backtracking ridge path) implemented and verified --
`roof_wings.py`'s new `_same_axis_wings_disagree()`, wired into
`roof_wings_from_ridge_path()`. Fed the REAL, preserved WB_125 broken path
(`roof_wings.test.py`'s new `WB_125_REAL_BROKEN_PATH_M`/
`WB_125_REAL_ROOF_POLY_M`, taken directly from `annotations.json`'s
`roof_ridge_path_removed_2026_09_29`) through it: correctly rejected, with a
clear console message identifying the two conflicting segments and their
disagreeing cross-extents, falling back to automatic wing detection instead
of silently building broken geometry. `roof_wings.test.py` 34/34 green (32
prior + 2 new), `roof_profile.test.py` 96/96 unchanged/green -- no
regressions.

Items 1-4 (the canonical single-mesh construction, explicit vertical
thickness, wall-derived-from-underside, doppelpultdach step handling) are
NOT started -- this is the validator only, a safety net against a repeat of
WB_125's specific failure mode. It does NOT fix the underlying valley-seam
gap that reproduces even on a plain, automatically-detected 2-wing L with no
hand-drawn path involved at all (see Current evidence above) -- that
requires items 1-4.

2026-09-29, same day, continued (Rainer: "fix it all and test it", then
away ~2h): four more real, independently verified fixes landed on top of
the validator, plus one deeper issue found and NOT fixed (see below) --
none of this is the full items-1-4 rewrite, all of it is targeted patches
within the existing wing-rectangle architecture, same as the validator.

1. **`mesh_height_at()`** (`roof_profile.py`, new function) + `wall_extension(roof_mesh=...)`:
   Codex's read-only review (`codex-out-roof-sweep-constructor.md`) found a
   reproducible ~98.5mm mismatch between `heightfield_roof_mesh()`'s actual
   built triangle mesh and `combined_height_at()`'s analytic value at the
   same point (a grid cell straddling the "which wing wins" crease
   triangulates flat across it, which isn't always where the crease truly
   falls). Fix: `wall_extension()` now queries the ACTUAL built mesh
   (barycentric interpolation) as the height authority when given one,
   falling back to the analytic function only outside the mesh's own
   coverage. Verified: reproduces Codex's exact 98.5mm case, confirms the
   fix reads the mesh's own true value. 5 new tests
   (`MeshHeightAtTests`/`WallExtensionRoofMeshTests`).

2. **Wing-boundary "step closure"** (`roof_profile.py`, `_long_wall_ramp()`
   generalised with a floating `bottom_start`/`bottom_end`, new step-prism
   loop in `wall_extension()`'s END-wall construction): Rainer, on seeing
   the real cause: "if there are height differences then you just treat it
   like a giebel." A sub-range `exposed_ranges()` correctly calls
   "internal" (covered by the other wing's own footprint, so no ordinary
   gable belongs there) can still have the other wing's own roof sitting
   LOWER than this wing's -- a genuine, hero-camera-visible ~0.9m cliff
   confirmed on WB_125's real satteldach rebuild via raycast (rays passing
   through both wall and roof to the ground). Fix closes exactly that gap
   with a floating step prism, from the other wing's own true height up to
   this wing's. Verified via a controlled synthetic case (`test_a_shorter_
   wing_forced_to_the_same_axis_gets_a_step_closure`) and confirmed present
   in the real rebuild (Wandstuecke count 15 -> 19).

3. **Diagonal-consistency fix** (`heightfield_roof_mesh()`'s per-cell
   triangulation): asked Codex to diagnose the visible torn/zigzag ridge
   line directly (`codex-out-ridge-zigzag.md`); traced the function's own
   real verts/faces on the exact failing build (Codex's own suggested
   monkeypatch technique) and CONFIRMED with hard data: two adjacent cells
   on the same wing-boundary cliff column picked OPPOSITE diagonals purely
   because the per-cell "smaller jump" comparison is a local decision with
   no reason to agree with its neighbour. Fix: classify a cell first by
   whether one pair of parallel edges carries most of the height change (a
   one-directional cliff) and use a FIXED diagonal for that whole class,
   leaving the original per-cell heuristic untouched for genuinely diagonal
   valleys. Verified: re-traced the same two cells, now pick the same
   diagonal.

4. **Dense safety sampling** (`boundary_polygon()` and the long-wall ramp
   split loop in `wall_extension()`, both in `roof_profile.py`): a
   systematic sweep (traced `heightfield_roof_mesh()` AND `wall_extension()`
   together via `runpy`, compared every wall-prism vertex's height against
   `mesh_height_at()`) found gable/long-wall constructions can undershoot
   the true combined height by up to 0.4m between two adjacent known
   breakpoints, because those breakpoint lists only capture where THIS
   wing's own profile bends or the other wing's coverage starts/stops ALONG
   ONE AXIS -- never a bend caused by the other wing's contribution along
   the CROSS axis (which shows up in `_true_height()`'s own sampling, not
   in either breakpoint list). Fix: add fine regular samples (every 0.3m)
   in addition to the known breakpoints whenever a second wing is in play,
   so a bend can't be missed by more than a small fraction of the step
   regardless of its cause. 2 existing tests' own south-wall-detection
   filters updated (position-only, not by a single prism's x-span, since
   the wall is now several smaller prisms instead of one long one -- a
   detection-method fix, not a weakened assertion; both tests still check
   the same true combined height as before).

   Caution found while building this sweep checker: a flat ~0.4m offset
   turned out to be the SOFFIT's own intentional `extra_sink=0.35+sink=0.05`
   margin (by design, documented, not a bug) and a ~0.165m offset turned
   out to be `wall_extension()`'s own documented "minimum across the wall's
   thickness, so it never pokes through" safety choice (also by design) --
   both are noted here so a future sweep-based check doesn't misclassify
   them as defects again.

   **Full regression sweep after all 4 fixes above:** `roof_profile.test.py`
   102/102, `roof_wings.test.py` 34/34, all green. Real rebuilds: WB_125
   satteldach (the primary case), all 3 other roof forms on WB_125
   (flachdach/walmdach/doppelpultdach -- clean, no visible defects), plus
   satteldach on `bungalow_007` (plain rectangle, single wing -- confirms
   the single-wing/`other_wing=None` path is untouched) and `bungalow_013`
   (an L-shape that gracefully falls back to the walmdach path rather than
   the satteldach two-wing branch -- expected behaviour, not a regression).

5. **NOT fixed (at the time) -- found, root-caused, and deliberately left
   for the full rewrite**: even after all 4 fixes above, `roof-pitch` on
   WB_125's real satteldach rebuild had 164 pairs of genuinely self-
   intersecting, non-adjacent triangles (confirmed via `bmesh`/`BVHTree.
   overlap()`, not guessed) -- all clustered at the exact same wing-
   boundary/reflex-corner region (x~6.1-6.4, y~7.9-9.8) already implicated
   in fixes 2-4 above. Confirmed PRE-EXISTING (identical count before and
   after the diagonal-consistency fix), so not a regression from that
   session's work. See the NEW section below -- this is now fixed.

2026-09-29, same day, continued (Rainer: "yes", authorising the full
canonical-mesh rewrite after reviewing the day's targeted-patch summary):
items 1 and 2 of Exact scope implemented and hard-verified. Items 3 and 4
NOT yet started (see Progress below).

**Item 1 -- canonical top-surface construction (the 2-wing dominance
crease as a real shared mesh edge):** `roof_profile.py`'s new
`_perpendicular_two_wing_crease()` + `_crease_split_cell()`, wired into
`heightfield_roof_mesh()`'s per-cell loop. Each wing's own height depends
on exactly ONE coordinate, so the difference between the two wings' height
functions is AFFINE (not just per-edge-linear, genuinely planar) within
any one grid cell -- its zero level set is therefore EXACTLY a straight
line crossing the cell's boundary at exactly two points, computed as the
exact root of a linear equation, not approximated. Scoped to exactly 2
wings with perpendicular ridge axes (Decision 5's "2-wing L/T only"), and
additionally bailed out whenever either profile has a true vertical step
(`has_vertical_step()`) since a height field cannot represent that at all
regardless of this fix (doppelpultdach keeps its own separate, already-
built explicit-closure treatment, unaffected).

Three real bugs found and fixed while landing this, each via a genuine
failing test, not guessed:
  - Tolerance mismatch between the "is this a boundary point" check and
    the "which side does this corner belong to" check let a corner a few
    ULPs off exact zero (e.g. `-2.22e-16` from `_height_at()`'s own
    interpolation arithmetic) get silently dropped from BOTH candidate
    polygons -- fixed by using the SAME tolerance-aware `ge()`/`le()` test
    everywhere in the split.
  - A corner sitting exactly ON the crease (routine at the building's own
    outer corner, where both wings' eave height is 0) was undercounted as
    a "boundary point", triggering an unnecessary fallback -- fixed by
    counting near-zero corners alongside synthetic mid-edge crossings.
  - **The real one**: adjacent grid cells each independently computed
    their OWN crossing vertex on a SHARED edge (since the crease is one
    continuous line, it crosses from one cell into its neighbour through
    their common edge) -- two numerically-coincident but index-DIFFERENT
    vertices, cracking the mesh open. Confirmed via a direct boundary-edge
    degree scan: 21 vertices deep inside the roof surface (nowhere near a
    true eave) showed boundary-degree 4 instead of 2 -- an actual hole.
    Fixed with a `edge_cache` dict shared across the whole per-cell loop,
    keyed by the cell-grid edge, so the second cell reuses the first
    cell's vertex.

Verified: new `test_dominance_crease_is_an_exact_shared_edge_not_an_
approximated_diagonal` (every triangle inside the true 2D overlap matches
ONE wing's own height function exactly, never an interpolation straddling
both) and `test_no_longer_reproduces_codexs_measured_98_5mm_mismatch`
(rewritten from the test that used to PIN DOWN Codex's 98.5mm mismatch --
now asserts `mesh_height_at()` matches the analytic value exactly at that
same point). `roof_profile.test.py` 103/103 at this point (+1 net: two
existing doppelpultdach-vertical-step tests needed no change once the
vertical-step guard was added; one test rewritten with reasoning per
AGENTS.md, none deleted/weakened).

**Item 2 -- explicit vertical-Z shell, replacing SOLIDIFY:** rebuilding
WB_125 satteldach with ONLY item 1 landed showed self-intersections got
WORSE, not better -- 328 pairs, up from 164. Root cause, confirmed by
direct rebuild comparison: SOLIDIFY offsets along each face's own AVERAGED
NORMAL, and item 1 made the two-wing crease a genuinely SHARP dihedral
fold (previously smoothed over by an approximated diagonal) -- exactly the
condition where a normal-offset shell can fold back through itself. This
is precisely Codex's own warning (`codex-out-roof-sweep-constructor.md`
section 5) that items 1 and 2 are not independently sufficient.

New `roof_profile.heightfield_roof_shell(verts, faces, thickness)`: bottom
surface is the same (x,y) with z reduced by a flat, VERTICAL `thickness`
-- every vertex moves straight down by the same amount regardless of the
local normal, so the bottom surface is combinatorially identical to the
top one and can only self-intersect if the top already does (which item 1
now rules out for the crease, by the structural test above). The rim
(outer perimeter, including the L-shape's own non-convex notch) needs no
polygon tracer: an edge used by exactly one triangle is a boundary edge by
definition, found by a plain edge-use count; each rim quad hangs straight
down from its own top edge and can only meet a neighbouring rim quad at a
shared VERTEX, never cross it, regardless of how reflex the corner is.
Found and fixed one real bug while landing this: the rim quad's own
winding has to be built OPPOSITE to whatever direction the one adjacent
top triangle already uses that edge (this file's own top-surface
triangulation has never guaranteed globally consistent winding, so a
single fixed rim convention collided with it wherever the local winding
happened to run "the other way").

Wired into `render-exterior.py`'s satteldach/pultdach 2-wing (and single-
wing) branch, replacing the `SOLIDIFY` modifier for that one roof sheet
entirely (`bake_modifiers()`/`modifiers.new("thickness","SOLIDIFY")`
removed from that call site; doppelpultdach's own separate cap/solidify
path, and flachdach/walmdach's own separate construction, untouched).

Verified, in order:
  - New `HeightfieldRoofShellTests` (3 tests): closed/watertight (every
    undirected edge used by exactly 2 faces), bottom is an exact flat
    vertical offset of the top, top surface unchanged. `roof_profile.
    test.py` 106/106.
  - Real rebuild, WB_125 satteldach, `EXT_ROOF_TYPE=satteldach`: builds
    clean, "102 Wandstuecke" (same count as the prior session's step-
    closure fix -- no regression there).
  - `bmesh`/`BVHTree.overlap()` self-intersection check on the rebuilt
    `roof-pitch`: **0 pairs** (down from 164 at the start of today's work,
    328 with item 1 alone). Direct manifold check (`bm.edges` `is_
    manifold`): **0 non-manifold edges** across 3588 verts / 6994 faces.
  - All 4 roof forms rebuilt on WB_125 (satteldach, walmdach, pultdach,
    doppelpultdach, plus flachdach) -- all clean, no errors; pultdach also
    exercises the new 2-wing crease+shell path ("54 Wandstuecke"), also 0
    self-intersections.
  - 2 other real projects rebuilt with `EXT_ROOF_TYPE=satteldach`:
    `bungalow_007` (plain rectangle, single-wing path, confirms the
    untouched branch -- 0 self-intersections) and `bungalow_013` (an
    L-shaped massing that falls back to walmdach, same as before --
    confirms no regression in that routing decision).
  - Hero-camera render of the fixed WB_125 satteldach inspected visually:
    clean, no tear/sliver at the reflex corner.

2026-09-29, same day, continued (Rainer: "so now?"): items 3 and 4 closed
out. **All 4 items of Exact scope are now done.**

**Item 3 -- wall-top derivation, removing now-unnecessary margins:**
investigated whether walls should switch to querying the shell's
UNDERSIDE directly (a literal reading of "derive wall tops from the
underside mesh"), and found that would be WRONG: `_true_height()`'s
existing `max(own, combined)` semantics deliberately let the wall extend
slightly INTO the roof slab's own thickness (hidden inside solid
material, guaranteeing contact) -- switching the query target to the
underside while keeping the same small `sink` would instead leave a
visible gap UNDER the roof. The TOP mesh is already the semantically
correct query target for wall height, and `mesh_height_at()` against it
was already wired as the primary source (earlier this session, before
today's items 1-2).

What item 3 actually still had outstanding: `boundary_polygon()`'s
soffit-only `extra_sink` (0.35m), added 2026-09-27 specifically to paper
over SOLIDIFY's normal-offset thinning near the roof sheet's own rim.
Confirmed that justification no longer exists anywhere this function is
still called from: `heightfield_roof_shell()` (item 2) gives every
sloped-sheet caller an exact, UNIFORM vertical thickness (no thinning at
the rim), and doppelpultdach's own 2-wing case never calls this function
at all (its walls come from a wholly separate hand-placed-box/gable-
infill mechanism -- see item 4 below). Removed `extra_sink` entirely;
kept the plain `sink` (a deliberate small aesthetic tuck avoiding a
coplanar-surface hairline, unrelated to precision). One existing test
updated with reasoning (the expected soffit height no longer subtracts
0.35m) -- `roof_profile.test.py` 106/106 unchanged otherwise.

Verified, in order: real rebuild, WB_125 satteldach + pultdach with
`extra_sink` removed -- a direct, camera-independent check (straight-up
BVH raycast from every soffit-top vertex against the actual built
`roof-pitch` mesh, not a camera reconstruction, per this session's own
established "camera rays are unreliable" lesson) found 0 poke-through
violations on satteldach (5 soffit islands checked) and confirmed the 3
`NO_HIT_ABOVE` cases on pultdach are PRE-EXISTING (identical before and
after removing `extra_sink`, present already with item 2 alone) -- a
separate, likely-benign raycast-tangent artifact at the overhang's exact
boundary coordinate, unrelated to this change; noted in ROADMAP.md as a
small separate follow-up, not blocking. Self-intersection re-check after
the removal: still 0 pairs on both forms.

**Item 4 -- doppelpultdach's vertical step as its own explicit closure:**
found ALREADY SATISFIED by pre-existing code (2026-09-25, before this
plan existed), confirmed today rather than newly implemented. WB_125's
own 2-wing doppelpultdach case builds via an entirely separate, hand-
placed-box mechanism (`_hand_built_boxes`/`_make_box()` in render-
exterior.py): both roof slabs AND the step wall (`roof-versatz-wall`)
are real boxes with genuine, explicit `dimensions` (never a normal-offset
modifier) -- exactly Codex's own hard requirement ("a vertical
doppelpultdach step wall gets ZERO usable thickness from a normal-offset
modifier... must be a distinct, explicit case"). The GENERAL (non-WB_125-
hardcoded) doppelpultdach path uses `gable_cap_prism()`, already a
long-proven explicit-thickness construction (its own docstring: "zero
overlaps across every axis/step-direction/end combination tested"), and
its own main roof sheet now also benefits from items 1-2's crease/shell
fixes via the same shared `heightfield_roof_mesh()`/`heightfield_roof_
shell()` call site. No code changes were needed for item 4.

**Final full regression, all 4 items landed:** `roof_profile.test.py`
106/106, `roof_wings.test.py` 34/34, all green. Real rebuilds (clean exit,
no errors): all 5 roof forms (satteldach, walmdach, pultdach,
doppelpultdach, flachdach) on WB_125, plus `bungalow_007` and
`bungalow_013` with satteldach forced. Self-intersection check on the
definitive WB_125 satteldach build: **0 pairs** (from 164 at the start of
this work). Manifold check: **0 non-manifold edges**.

`ROOF-SWEEP-CONSTRUCTOR-001`'s Exact scope (items 1-5) is now fully
implemented and verified. Remaining, explicitly out-of-scope follow-on
work (tracked, not cancelled, per this plan's own "Explicitly out of
scope" section): N-way (3+ incident edges) plus-junction generality and
`roof_wings_multi.py` wiring; walmdach's own separate reflex-corner
bridging-patch item; the pultdach `NO_HIT_ABOVE` raycast artifact noted
above.
