# Satteldach/pultdach gable end-wall pokes through roof at steep rim

Status: SUPERSEDED by ROOF-SWEEP-CONSTRUCTOR-001 (2026-09-29) -- Rainer asked
for the wing-rectangle architecture itself to be replaced (path-sweep with
live footprint width), not another seam patch. Codex's read-only design
review independently confirmed the seam-reconciliation pattern this plan
would have patched is the recurring root cause across multiple distinct
bugs this week, including a newly found ~98.5mm mesh/analytic-height
mismatch unrelated to this plan's own margin-vs-gap tradeoff. Keeping this
document for its evidence trail; do not implement it standalone -- the
replacement plan subsumes this exact defect.

Status (original): PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Fix a confirmed, live-reproduced defect: on `german_catalog_review_bungalow_4_3_1_wb_125`
(satteldach/classic), the gable end-wall (`roof-walls`) is visibly in front of
(closer to camera than) `roof-pitch` near the ridge peak, from the production
hero camera angle. Fix it without reopening the gap-under-roof failure mode
that a documented prior decision deliberately avoided at this exact spot.

## Current evidence and behavior

- Live rebuild of the project (real pipeline, `run_project.py ... --styles
  classic`, `EXT_ROOF_TYPE=satteldach`) reproduces a visible tear/poke-through
  at the gable ridge peak in the production hero-camera render
  (`exterior-satteldach-baseline.png`).
- Ruled out: my same-day `end_extension_mm` wall-mitre fix
  (`render-exterior.py`) is NOT the cause — rebuilt with that fix reverted in
  a scratch copy, identical defect at identical pixels.
- Color-ID diagnostic (`roof-pitch` red / `roof-walls` green, the same
  technique that found the prior "GELOEST" verge-soffit bug) shows the gable
  end-wall clearly in front of the roof surface near the peak, plus small
  sky-colored gaps at the very ridge tip.
- Direct measurement (BVH raycast, straight down) at the highest `roof-walls`
  vertices near the peak (`roof_profile.py` boundary_polygon output) shows the
  wall is ALWAYS below the roof surface vertically — clearance of 0.05m to
  0.4m, never a true overlap. This is a grazing/oblique-angle visibility
  artifact at a thin rim margin, not a straight polygon intersection — same
  mechanism already diagnosed and fixed for the verge soffit
  (`ROOF-RIDGE-PATH-TOOL-001-FOLLOWUP-2`, `roof_profile.py:1001-1030`):
  SOLIDIFY extrudes along the roof's face normal, not straight down in Z, so
  its true vertical thickness shrinks near a steep rim.
- The relevant code already anticipated this exact tension and chose NOT to
  fix it the same way: `roof_profile.py:1027-1030` — "The END WALL's own call
  (no `extra_sink`) is untouched -- unlike the soffit, an end wall built too
  short leaves a real, visible gap under the roof, so it keeps the tight,
  already-correct margin above." The soffit's `extra_sink=0.35` is safe
  specifically because `roof-pitch`'s own solidified shell already covers
  that space from above (soffit is decorative trim); the gable end-wall is
  the real, load-bearing-looking exterior facade, so nothing else covers the
  space that shrinking it would open up.
- This is a real usability regression risk area: `roof_profile.py` and this
  exact ridge/gable junction have a long documented history of repeated
  false-start hypotheses this same week (`ROADMAP.md`,
  `PER-WING-AXIS-OVERRIDE-001-FOLLOWUP` through `-FOLLOWUP-2`, 5 hypotheses
  logged, 2 disproven, 1 real-but-unrelated bug fixed en route).

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Last commit: `5be1a4e` "Sink polish round: junk-cube filter, real worktop
  height, steel apron attempt"
- `git status` shows substantial PRE-EXISTING uncommitted changes unrelated to
  this task (furnished-render/annotation-schema work: `scripts/
  render-furnished-dollhouse.py`, `scripts/build-simplifier-render-plan.py`,
  `src/app/floorplan-workbench/page.tsx`, and others) — not touched by this
  plan, must not be disturbed or committed over.
- `scripts/render-exterior.py` and `scripts/roof_profile.py` are themselves
  untracked (`??`) in this repo — there is no tracked baseline/SHA for them
  specifically; "current state" is the working-tree file as it stands today,
  including today's already-applied and verified `end_extension_mm` wall-
  mitre fix in `render-exterior.py` (kept, unrelated to this task).

## Exact scope

Find a way to keep the gable end-wall's top edge visually under the roof
surface from realistic camera angles, WITHOUT opening a real gap between the
wall's top edge and the roof's underside anywhere along that edge. Candidate
directions to evaluate (in order of preference):

1. Replace the flat, empirically-tuned margin approach (`sink`/`extra_sink`
   constants) with an exact calculation: derive the true vertical drop of the
   solidified roof's underside at a given (x,y) analytically from the roof
   pitch and the SOLIDIFY thickness (the project already has one predictive
   formula from a prior Codex analysis: thickness 0.22, pitch 0.27 ->
   horizontal offset 0.057m, height difference 0.23m — verify this
   generalizes across pitches before trusting it), then size the end wall's
   safe margin from that instead of a guessed constant.
2. If an exact formula proves unreliable near the rim/cap geometry
   specifically (the comment at `roof_profile.py:1013-1016` suggests the cap
   geometry, not the simple interior case, governs the shape there), keep the
   wall's height calculation exactly as today (no shrinking) and instead
   extend `roof-pitch`'s own coverage locally at the rim so its underside
   reliably reaches at least as low as the wall's true top edge — mirroring
   how the verge soffit was reasoned about (the covering surface gets
   pushed, not the load-bearing wall).
3. Empirical bisection (the method that found the soffit's 0.35m value) is
   acceptable ONLY if paired with an explicit, automated check in the
   verification step that confirms no gap opens between wall-top and
   roof-underside anywhere along the shrunk edge (not just "poke-through
   gone") — a margin found by eye without that check is exactly how the
   avoided failure mode could reappear silently.

## Files in scope

- `C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\roof_profile.py`
  (`boundary_polygon()`, the end-wall prism call at line ~1060, possibly
  `heightfield_roof_mesh()` if direction 2 is chosen)
- `C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\roof_profile.test.py`
  (new/updated tests)

## Explicitly out of scope

- The separate, already-open WALMDACH reflex-corner bridging-patch item
  (different roof form, different code path, tracked separately).
- The floorplan-simplifier Dach-tab UI consolidation work (different repo,
  different problem, tracked separately).
- Any change to the verge-soffit's own `extra_sink=0.35` (already correct,
  not implicated).
- Any change to `end_extension_mm` (today's separate, already-verified fix).

## API, schema, and data-contract effects

None. Pure 3D geometry construction in a render script; no annotation schema,
API, or stored-data format changes.

## Acceptance criteria

- The satteldach/pultdach gable end-wall no longer appears in front of
  `roof-pitch` at the ridge peak on `german_catalog_review_bungalow_4_3_1_wb_125`
  (classic style), verified via the same color-ID render technique used to
  find the bug (green `roof-walls` vs red `roof-pitch`, real hero camera).
- No NEW gap appears between the gable wall's top edge and the roof's
  underside anywhere along that edge, on the same project, verified via a
  dedicated raycast check comparing wall-top height against roof-underside
  height at multiple points along the gable's width (not just the peak).
- All 4 other roof forms (flachdach, walmdach, doppelpultdach, and the
  satteldach/pultdach rectangle case) smoke-test cleanly with no regression.
- `roof_profile.test.py`'s full suite stays green; any assertion changes are
  listed here with reason before implementation, not discovered after.

## Tests and verification commands

- `roof_profile.test.py` (existing suite) — must stay green or have listed,
  reasoned updates.
- New test(s) covering the exact safe-margin calculation for a steep-pitch
  gable end wall, asserting the wall's computed height never exceeds the
  roof's true underside height at the same (x,y) by more than a tight
  tolerance, AND never falls more than a tight tolerance below it either
  (the "no gap" half of the acceptance criteria, not just "no poke-through").
- Real Blender rebuild of `german_catalog_review_bungalow_4_3_1_wb_125`
  (classic, `EXT_ROOF_TYPE=satteldach`) + color-ID render, compared
  before/after.
- Smoke rebuild of all 4 other roof forms on the same project.

## Protected and risky paths

`roof_profile.py`'s ridge/gable-wall height calculations are a repeatedly
reinvestigated, easy-to-regress area (5+ documented hypotheses this week
alone). Treat any change here as high-risk: verify against the real built
mesh, not just the pre-solidify analytic geometry, before considering it
done.

## Rights, provenance, privacy, and security impact

None. Internal render-geometry code only.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Required answer: no. This plan touches only internal render-geometry
construction (`roof_profile.py`). It does not touch the annotation
correction/approval pipeline, does not add any new generation, publication,
or email path, and does not change which corpus reference a render is built
from.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

(Carried over from this investigation, for continuity — not yet 3 NEW
hypotheses spent on the fix itself.)

1. Hypothesis: today's `end_extension_mm` wall-mitre fix caused this defect.
   Command: rebuilt with that fix reverted in a scratch copy
   (`render-exterior-pre-mitre-fix-AB-TEST.py`, deleted after use).
   Result: identical defect, identical pixels.
   Conclusion: DISPROVEN — unrelated to today's mitre fix.

## Rollback

No code changed yet (investigation only). Once implemented: revert the
specific `roof_profile.py` diff; no data migration, no external state.

## Unresolved questions

- Does the prior Codex normal-offset formula (thickness 0.22, pitch 0.27 ->
  0.057m horizontal / 0.23m vertical) generalize to other pitches, or was it
  specific to that one measured case? Needs verification before relying on
  it for direction 1.
- Is the end wall ever actually load-bearing/structural in the delivered
  model, or purely visual facade? Confirms whether "gap under roof" would
  read as a structural-looking defect or purely cosmetic — affects how tight
  the "no gap" tolerance in acceptance criteria needs to be.

## Approval record

Not approved. Stop before implementation.
