# Fix: wall/gable height at a shared wing boundary must reflect the TRUE combined roof, not just the dominant wing's own

Status: IMPLEMENTED AND VERIFIED FOR THIS PLAN'S OWN TARGET (the
`wall_extension()` height defect, Codex's own confirmed finding) -- fixed
with an exact sloped-ramp wall, confirmed via real renders + Blender-
headless raycast agreement to within 0.6-3.6mm at every previously-broken
point. A THIRD visual anomaly remains visible at the reflex corner in
every real render, cause NOT YET IDENTIFIED -- my own first theory for it
(SOLIDIFY's automatic rim-fill) was checked by a second Codex review and
REFUTED with a real numeric Blender reproduction (see "Follow-up 2"
below, which records the failed hypothesis rather than deleting it).
Tracked as `PER-WING-AXIS-OVERRIDE-001-FOLLOWUP-2`, status OPEN.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Follow-up to `PER-WING-AXIS-OVERRIDE-001` (implemented, per-wing ridge-axis
drawing shipped). A real render of WB_125 with `roof_axis_overrides:
{wingA: "x", wingB: "y"}` (perpendicular ridges — the NORMAL look of any
L-shaped gable-roofed house, not an edge case) showed a torn, gapped roof
at the wings' shared boundary. Rainer: "if were to draw a horizontal line
through A and extend it to the middle A/B and have a vertical line go
through the middle of B ... it would also be a Satteldach but this can't
be drawn here" — confirming this is the primary use case, not a corner
case to defer.

## Root cause (confirmed by direct code trace + a hand-worked numeric example)

`wall_extension()` decides, per boundary (long wall, end wall, soffit),
WHICH wing gets to build wall material there via `exposed_ranges()` +
`dominant` (from `WING-END-EXPOSURE-001`) — correctly avoiding
double-built/redundant geometry at a boundary two wings share. But once a
wing "wins" that decision, its wall's HEIGHT is computed purely from that
wing's OWN cross-section (`_height_at(section, ...)`, `section` built only
from that wing's own resolved profile) — never checking whether the
OTHER wing's rectangle *also* covers that exact world point with a
genuinely taller roof there.

Worked example (mirrors Codex's own synthetic reproduction): wingA =
(0,12,0,4), ridge along X, centered 2m gable. wingB = (0,4,0,10), ridge
along Y, centered 2m gable. Both wings share the true south edge (y=0).
At that tied boundary, `dominant` correctly lets wingA (bigger area) build
its own south wall in full instead of both deferring to each other
(the earlier, already-fixed "neither builds" bug). But wingA's own wall
height there depends only on Y (near the eave, ~0.3m) — while wingB's
rectangle ALSO covers e.g. (x=2, y=0.3), and wingB's own ridge (which runs
along Y, so its peak height applies at every Y including 0.3) is 2m
there. `combined_height_at(2, 0.3, ...)` = max(0.3, 2) = 2m — the TRUE
roof is 2m tall at that point, but the only wall built there (wingA's) is
0.3m. The remaining ~1.7m is the gap/torn look in the render — wingB's
own true gable, which should stand there, was correctly suppressed by
`dominant` (avoiding a double-built wall) but nothing built the height its
own ridge actually needs.

Confirmed separately (Blender headless inspection, this session): the
roof SHEET itself (`heightfield_roof_mesh()`/`combined_height_at()`'s
per-vertex max()) is fully closed/watertight (0 boundary edges, 0
abnormal-Z-spread faces) — the roof surface is not the defect. `roof-walls`
(this function's own output) is the one that doesn't reach it.

## Repository baselines

- `born2thrill-local-workbench`: branch `agent/furnished-render-and-annotation-schema`,
  HEAD `5be1a4e18956b9fb2e158bee82aa159898356e89`. Working tree already has
  247 pre-existing changed/untracked paths from earlier, unrelated work
  this session and before — none touched by this plan; only the files
  listed below will be edited.
- `floorplan-simplifier`: unrelated to this plan (UI/persistence already
  shipped and verified in `PER-WING-AXIS-OVERRIDE-001`).

## Exact scope

Fix `wall_extension()` (and only where the same mechanism applies) so
that wherever it builds wall/soffit geometry at a boundary decided by
`exposed_ranges()`/`dominant`, the height used is the TRUE combined roof
height (`combined_height_at()` across ALL wings, matching what the roof
sheet itself already uses) wherever that information is available,
falling back to today's own-wing-only height for every existing
single-wing caller (doppelpultdach hand-built-box, any caller that
doesn't pass the new parameters) — zero behaviour change there.

Concretely:
1. Add optional parameters to `wall_extension()`: `all_wings=None,
   all_profiles=None, all_along_x=None` — the same three inputs
   `heightfield_roof_mesh()` already receives, so a caller that has them
   (the shared two-wing satteldach/pultdach branch in render-exterior.py)
   can pass them straight through.
2. A local `_true_height(a_val, c_val)` helper: when the new params are
   given, converts (a_val, c_val) to world (x, y) using the SAME
   convention `_prism()`/`boundary_polygon()` already use, calls
   `combined_height_at()`, and falls back to this wing's own
   `_height_at(section, c_val)` only if that returns `None` (shouldn't
   happen for a point on this wing's own boundary, kept as a safety net,
   not a silent behaviour change).
3. End-wall/soffit polygon construction (`boundary_polygon()`): use
   `_true_height(a_wall, c)` instead of `_height_at(section, c)` for the
   two endpoints AND this wing's own interior breakpoints. Does NOT
   inject the other wing's own breakpoints into the polygon shape itself
   (out of scope — the confirmed defect mechanism above is a long-wall
   issue at a tied boundary, not an end-wall interior-breakpoint issue;
   noted as a known simplification below).
4. Long-wall height (today: one constant height per already-exposed
   `(a_start, a_end)` sub-range): additionally split each sub-range at
   the other wing's own ridge-axis extent boundary/boundaries
   (`other_a_true`) wherever one falls strictly inside it — these are the
   genuine "the other wing's own coverage may change here" points. For
   each resulting sub-segment, sample `_true_height()` at a few points
   along its length (not just the center — Codex's own caution) and take
   the safe (tallest) height so the wall is never SHORTER than the true
   roof anywhere in that sub-segment. This is a deliberate, documented
   trade-off: a small amount of possible over-height (a wall very
   slightly taller than the roof at one exact spot, mostly hidden by the
   roof's own overhang/solidify thickness) in exchange for eliminating
   the dramatic, visible under-height gap that is today's actual,
   confirmed, user-visible defect. Recorded explicitly so a future reader
   does not mistake this for an oversight.
5. Thread the three new parameters through from `render-exterior.py`'s
   wall-building loop (currently building `_wall_pieces`) — pass
   `_height_wings`, `_sheet_profiles`, `_wing_along_x` (the SAME three
   values already given to `heightfield_roof_mesh()`), so the wall's own
   idea of "the true roof" is identical to what the roof sheet itself
   was built from.

## Files in scope

- `born2thrill-local-workbench/scripts/roof_profile.py` — `wall_extension()`
  only.
- `born2thrill-local-workbench/scripts/render-exterior.py` — the wall-building
  loop's call to `wall_extension()` only (thread the 3 new args).
- `born2thrill-local-workbench/scripts/roof_profile.test.py` — new tests
  only (existing tests unchanged).

## Explicitly out of scope

- `gable_cap_prism()` / the gable-cap loop — dead code for plain
  satteldach (`has_vertical_step()` is false), not reproduced as broken
  for any form this session; left untouched per Codex's own explicit
  advice ("leave it outside this fix unless separately reproduced").
- The height-field mesh triangulation itself
  (`heightfield_roof_mesh()`/`combined_height_at()`) — confirmed
  watertight; Codex's Finding #1 (grid triangles can locally dip below
  the analytic surface near a true diagonal valley) is a real, separate,
  lower-confidence risk that was NOT confirmed as the WB_125 cause and is
  NOT being changed here. If the fix in this plan does not fully close
  the visible gap on re-render, Finding #1 is the next thing to chase —
  recorded here so that isn't lost.
- Injecting the other wing's own profile breakpoints into
  `boundary_polygon()`'s interior shape (item 3 above) — the confirmed
  defect is a long-wall issue; end-wall interior fidelity is a smaller,
  separate refinement if a future render shows it's still needed.
- Any UI change (`dach-editor.js`) — already shipped, not touched here.
- The doppelpultdach hand-built-box branch — unaffected, uses neither
  `wall_extension()`'s two-wing path nor this fix.

## API, schema, and data-contract effects

None. Purely additive, optional parameters on an internal Python
function; no change to `annotations.json`, the render-plan JSON schema,
or any persisted data.

## Acceptance criteria

1. `roof_profile.test.py`'s existing 93 tests still pass unchanged.
2. A new test reproduces the worked example above (two perpendicular-axis
   wings sharing a tied boundary) and asserts the built wall's height at
   the shared boundary is now >= the true combined height there (within
   `sink` tolerance) — i.e. no longer silently 0.3m against a true 2m.
3. A real `run_project.py` build+render of WB_125 with
   `roof_axis_overrides: {wingA: "x", wingB: "y"}` no longer shows the
   torn/gapped seam in the rendered image (visual confirmation, not just
   unit tests — this is the same "verify against the user-visible
   surface" standard the rest of this session's work was held to).
4. The SAME house's existing, already-verified satteldach QA baseline
   (both wings automatic / axes agreeing) is re-rendered and shows no
   regression.

## Tests and verification commands

- `python roof_profile.test.py` (repo: `born2thrill-local-workbench/scripts`)
- `python roof_wings.test.py`, `python roof_wings_multi.test.py` (same dir,
  unaffected but re-run to confirm zero cross-contamination)
- `FLOORPLAN_WORKBENCH_DATA_DIR=<...> python run_project.py
  german_catalog_review_bungalow_4_3_1_wb_125 --styles classic
  --finishes classic-a` with the mixed override actually saved, then
  visually inspect `exterior-satteldach-baseline.png`.

## Protected and risky paths

- `wall_extension()` is called by every satteldach/pultdach/doppelpultdach
  build, not just the two-wing case — the new parameters MUST default to
  `None` and produce byte-identical output to today whenever the caller
  doesn't pass them (every single-wing/whole-house-axis-agrees caller).
  This is the primary regression risk; covered by re-running the full
  existing suite unchanged.
- `WING-END-EXPOSURE-001`'s own fix (the `dominant`/tie-break mechanism)
  must not be altered — this plan only changes what HEIGHT is used once
  that mechanism has already decided WHO builds, never the decision
  itself.

## Rights, provenance, privacy, and security impact

None. WB_125 is an internal QA test house, not a customer-delivery
candidate (see `PER-WING-AXIS-OVERRIDE-001`'s own note).

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This only changes wall/gable HEIGHT geometry computed
from already-approved plan data; no new generation, publication, or email
path is added, and nothing here bypasses the existing manual save/build/
review gates.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. Hypothesis (mine, before this session's Codex review): the wall/gable
   panel was built TOO TALL relative to the roof (a "poke-through"), from
   watching the rendered silhouette and jagged shading. Command: visual
   inspection of `exterior-satteldach-baseline.png` + a top-down Blender
   headless re-render. Result: rejected by Codex's own numeric
   counter-example (`max(hA,hB) >= hA` can only raise a wall, never
   explain a gap) and confirmed wrong once the actual mechanism (dominant
   wing building a too-SHORT wall at a tied boundary while deferring the
   subordinate wing's own taller feature) was traced through the real
   code with real numbers. Conclusion: it is an underfill (gap), not an
   overfill (poke-through) — the fix direction in this plan follows from
   that.

## Rollback

Revert the files listed above. The new parameters are additive and
optional; reverting is a plain file revert with no data migration.

## Unresolved questions

Superseded by the render-verification result below: item 4's original
"safe/tallest sample" trade-off was replaced during implementation by an
EXACT sloped-ramp wall (`_long_wall_ramp()`) once a real render showed
the flat/tallest-sample box could poke through the true roof across most
of a metre-wide segment, not a negligible sliver. The ramp is exact for
piecewise-linear profiles (proven, not just measured close), so this
question is resolved, not deferred.

## Render verification result (2026-09-27) — fix confirmed correct; a DIFFERENT, separate bug found

Two full `run_project.py` rebuilds of WB_125 (mixed `roof_axis_overrides:
{wingA: "x", wingB: "y"}`) were run after implementing this fix — one
after the first (flat, tallest-endpoint) version, one after replacing it
with the exact sloped ramp. Both exited 0 with every automated check
passing. Direct Blender-headless inspection (raycasting `roof-walls`
against `roof-pitch` at every previously-flagged point) confirmed:

- The flat version DID measurably poke through the true roof line across
  a roughly 1m-wide segment (a real, visible-sized defect, not a
  rounding error) -- exactly the risk Codex warned about.
- The sloped-ramp version closed that: at the same points, `roof-walls`
  and `roof-pitch` now agree to within 0.6-3.6mm (pure floating-point/
  interpolation noise, invisible at any render resolution). The wall
  fix itself is CORRECT and DONE.

**However, the rendered image still shows a torn/jagged area in the same
place as before either fix** -- confirmed, by direct investigation, to be
a COMPLETELY SEPARATE, THIRD bug, not this plan's target and not Codex's
Finding #1 (the heightfield grid's own resolution) either:

- A fine raycast scan of the ENTIRE built footprint found the `roof-pitch`
  mesh itself has NO real gaps or dips anywhere (0 flagged anomalies) --
  ruling out both a wall problem (now fixed) and a heightfield-resolution
  problem (Finding #1, never actually reproduced on this house).
- Directly calling `heightfield_roof_mesh()` in isolation (pure Python, no
  Blender) at the exact reflex-corner boundary row (wingA's true y1 edge,
  y=9.8514) confirms its OWN raw output is perfectly smooth and matches
  `combined_height_at()` exactly at every vertex it produces.
- But the FINAL BAKED `roof-pitch` object (after SOLIDIFY) has EXTRA
  vertices at this same row that are NOT in `heightfield_roof_mesh()`'s
  own output at all, interleaved between the correct ones, with
  substantially wrong (too-low) heights -- e.g. a real vertex at
  (4.7470, 9.8514) reads z=2.950 (height 0.200m above eave) where the
  analytic/correct value is 0.428m (z=3.178), a ~0.23m error.
- Root cause: `roof-pitch`'s `SOLIDIFY` modifier is added with its
  default `use_rim_fill=True` and never explicitly built around by this
  branch (unlike `gable_cap_prism()`, which exists SPECIFICALLY because
  Blender's own auto rim-fill/tessellation is not reliable on a
  NON-CONVEX boundary loop -- see that function's own docstring, about
  doppelpultdach's concave CROSS-SECTION). The height-field mesh's own
  perimeter, for an L-shaped two-wing footprint, is ALSO non-convex (the
  reflex corner) -- a non-convexity nothing has built an explicit
  workaround for yet, because every previous fix in this area addressed
  the cross-section's own convexity (fine for satteldach) or the wing
  wall/gable geometry (this plan), never the height-field SHEET's own
  outer perimeter shape. SOLIDIFY's automatic rim-fill is producing bad,
  wrong-height fill triangles right at that reflex corner, exactly
  matching the visible torn/jagged appearance.

This is real, distinctly diagnosed, and NOT fixed in this round --
tracked as its own follow-up below. WB_125's saved annotation was reset
back to `roof_axis_overrides: {}` again after this verification.

## Follow-up 2: STILL UNCONFIRMED -- a visible artifact remains at the reflex corner, but my own "SOLIDIFY rim-fill" theory for it was WRONG

**PER-WING-AXIS-OVERRIDE-001-FOLLOWUP-2**, recorded in the canonical
ROADMAP.md too -- CORRECTED after a second Codex read-only review, 2026-
09-27. The original write-up of this follow-up (below, kept for the
record rather than deleted, since the failed hypothesis itself is worth
keeping) claimed SOLIDIFY's automatic rim-fill was inserting extra,
wrong-height vertices near the reflex corner. **That specific claim is
WRONG, confirmed by Codex with a real, numeric Blender reproduction**:
the "extra vertices" I found by reading `roof-pitch`'s raw
`mesh.vertices` directly were simply the SOLIDIFY modifier's own
BOTTOM-shell vertices -- for a sloped surface, SOLIDIFY offsets each
vertex along its FACE NORMAL, not straight down in Z, so the underside
sits at a different (x,y) than the corresponding top vertex, not just a
lower z. Codex's own worked numbers (thickness 0.22m, slope 0.27) predict
a horizontal shift of 0.057m and a vertical separation of 0.228m at the
displaced XY -- matching my own found "0.057m interleaving" and "~0.23m
height error" almost exactly. I had mistaken the shell's own known,
correct underside for a defect. Toggling `use_rim=False` (the correct
Blender 5.0 property name -- my originally-proposed `use_rim_fill` does
not exist on this modifier and would raise `AttributeError`, so it was
never actually tested) left the top-surface vertices completely
unchanged in Codex's own A/B, confirming rim-fill is not the source of
whatever the real remaining issue is.

**A real visual anomaly DOES still appear at the same spot in the
rendered image** (re-confirmed at full, non-upscaled resolution: a
bright near-white sliver right along the ridge, plus dark notches cut
into the gable-end wall, at the same reflex-corner area) -- but my two
Blender-headless raycast scans of `roof-pitch`'s own TOP (outward-facing)
surface, across the ENTIRE building footprint, found ZERO real gaps or
height anomalies anywhere (matched to the mm against the analytic
`combined_height_at()`). That evidence, plus Codex's own rebuttal, means
the roof-pitch top surface itself is very likely CORRECT, and the visible
artifact's true cause is NOT YET IDENTIFIED. Codex's own suggested next
line of investigation (not yet done): look at the SOLIDIFY shell's rim/
bridge faces (the thin edge connecting top and bottom shells) for
folding or self-intersection specifically where the slope changes
abruptly at the valley -- a steep enough slope change combined with a
0.22m thickness could expose a sliver of that normally-hidden edge
geometry from certain camera angles, which would look exactly like what
was seen without being a height-field or wall defect at all.

**Status: OPEN, cause not established.** Do not re-attempt the
rim-fill/use_rim_fill theory above -- it is refuted. Next step should
follow Codex's own suggestion (rim/bridge-face geometry near the valley)
or a fresh, independent look, not a repeat of this round's approach.

## Approval record

Requested by the user ("ok", following the Codex review and an explicit
"write up a plan doc for this now and start on it, or hold it as the
recorded follow-up for later?" question) — approval to proceed with
implementation now, not defer.
