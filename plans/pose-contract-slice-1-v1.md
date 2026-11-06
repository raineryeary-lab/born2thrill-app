# Pose contract, slice 1: corrected-path double-transform, dead rotation override, door-pose extraction, R8 gate

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-08-22: "how can this happen again and again, the whole day was
just the same problems that i thought were fixed" — then explicitly: "ask
codex what the best corse of action is", and after two Codex consultation
rounds and a jointly agreed phased proposal: "Plan 1 all 4 points".

The shared failure class behind this week's bugs: two code paths silently
assuming different conventions (reference frame, point order, transform
order) for the same stored value. This slice is the first, deliberately
small structural response — chosen jointly with Codex (session
01a02a94-449f-78a0-997e-54b34fb3826d and follow-up) so that the very next
builds are more trustworthy, with the larger contract work in follow-up
plans.

## The four points (all approved together)

1. **Fix the `--corrected` build path's double pose transform**, pinned by
   golden pose vectors frozen from today's user-confirmed contact sheet.
2. **Delete `ROTATION_OVERRIDE["ecksofa"]`** so the editor's rotation for
   the corner sofa reaches the render again.
3. **Extract today's door hinge/swing normalization into a named pure
   function** with correctly-formulated metamorphic tests.
4. **New certificate rule R8** in `verify_render_blend.py`: opening
   features (jambs, leaf, glazing) must reach their intended heights in the
   built scene — the check that would have caught the dollhouse-cut bug
   before it ever reached a delivered file.

## Current evidence and behavior

### Point 1 — corrected path double-transforms the pose (verified in code)

`corrected_placements()` (`build-simplifier-render-plan.py:1358`) reads
furniture via `workbench_furniture()` (line 329), which for the current
`render-geometry-mm-y-down-v1` space ALREADY converts editor→render pose:
y-flips positions/points against the level room extent, negates
`rotation_deg`, deliberately does NOT invert `mirrored` (lines 378-412,
with the long warning comment). `corrected_placements()` then transforms
AGAIN: `flip()` on `position_mm` (1430) and `points_mm` (1392),
`(360 - rotation)` (1437), `not mirrored` (1438). Two y-flips and two
negations cancel; the net result is a pose still in the EDITOR's
convention — plus the second flip uses the CORRECTION document's extent,
not the annotation extent the first flip used, so positions don't even
cancel cleanly.

Codex round 2 independently confirmed this (its words: "Der Fehler ist
umfassender als nur [mirrored] ... die Pose wird offenbar doppelt
gespiegelt") and confirmed the path is live: `correction_plan()` calls it
(line 1804), reachable via `run_project.py --corrected REVISION.json`
(line 475). Verified additionally this session: `go.py` never passes
`--corrected`, so current production builds do NOT go through this path —
it is an armed latent bug, not a corruption of today's outputs.

The workbench/annotation path (line 2036 area: `bool(symbol.get(
"mirrored"))`, rotation passed through) is the validated one: today's
4-combination contact sheet (real `ecksofa` mesh, real pipeline, rotation
0/90 x mirrored/not) was confirmed by Rainer — panels B and D (the
mirrored ones) are correct.

### Point 2 — the rotation override swallows editor rotation (verified)

`ROTATION_OVERRIDE` (`render-furnished-dollhouse.py:406-413`) REPLACES the
plan's `rotation_deg` entirely at the instance site (line ~3556), it does
not compose. Its own comment shows `"ecksofa": 0` was a repair for one
specific old annotation state (plan carried 180, contact-sheet pick said
0) — a placement-data repair, not a model-orientation property. That
furniture has since been re-placed in the workbench editor; the repaired
data no longer exists, but the override still eats every rotation Rainer
sets. Codex round 2, verbatim conclusion: "Für `ecksofa` ist Löschen die
richtige Lesart ... nicht einfach als MODEL_FACING_DEG verschieben."
Measured consequence check: bungalow_039's stored editor rotation for the
ecksofa is currently 0, so removing the override does not change that
house's render — it only un-deadens future rotations.

`sofa_1sitzer` (135) has a similar history but was NOT part of the
approved scope sentence; it stays, recorded as a roadmap follow-up.

### Point 3 — door normalization is inline, and the naive metamorphic
test would be wrong

Today's fix (the dot-product frame normalization) sits inline in
`build_floor_walls_and_openings()` (~line 1149-1163). Codex's correction
to my proposed test, adopted here: "swap the door's points → same output"
is only true if the door-relative labels are swapped WITH the points
(hinge_side is defined relative to point order — swapping points alone
describes the OTHER hinge, and the output must then differ). The correct
metamorphic relations are specified under Tests.

### Point 4 — no rule guards opening heights

`verify_render_blend.py` checks R0/R2/R3 but nothing about openings. The
dollhouse-cut bug (7 of 8 windows + 2 doors sliced) passed every gate and
reached Rainer's eyes in Blender. This session's ad-hoc probe (Z-extents
of every opening object) is exactly the right measurement; R8 formalizes
it with the component-specific expectations Codex insisted on (a frame
HEAD is only profile-tall; glazing is inset; height clamps to the wall).

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `scripts/build-simplifier-render-plan.py`, `scripts/render-furnished-
  dollhouse.py`, `scripts/build-simplifier-render-plan.test.py`: already
  modified, uncommitted (today's door-frame, dollhouse-exemption, area,
  wall-merge fixes). `scripts/verify_render_blend.py`: untouched so far.

## Exact scope

1. `corrected_placements()`: remove the second transform — `points_mm`
   and `position_mm` used as returned by `workbench_furniture()` (already
   render-space), `rotation_deg` passed through mod 360, `mirrored` passed
   through. The now-unused `flip` parameter is removed from the signature
   and from the single call site (`correction_plan()`, line 1804 — flip
   remains in use there for rooms/walls/openings, which genuinely are in
   the correction document's own space). Comment updated to record why.
2. New `scripts/pose-golden-vectors.json`: the editor→compiled pose
   contract as data — the four contact-sheet combinations plus position
   flip — with provenance ("confirmed by Rainer, 2026-08-22 contact
   sheet"). Python test reads it; a later slice adds the TS-side reader.
3. `ROTATION_OVERRIDE`: delete the `"ecksofa"` entry; comment records the
   deletion and why. `sofa_1sitzer` untouched (roadmap follow-up).
4. New pure function `door_pose_in_wall_frame(door_a, door_b, wall_start,
   wall_end, hinge_side, swing_side)` in `build-simplifier-render-plan.py`
   (points in, wall-frame labels out; no wall matching inside — Codex's
   "noch reiner" variant); `build_floor_walls_and_openings()` calls it.
   Behavior identical to today's inline fix.
5. `verify_render_blend.py`: new `check_opening_heights(plan, floor)`
   wired into `main()` as `R8_opening_heights`. Per wall (mapped by the
   wall's POSITION in `floor["walls"]` to the renderer's `wall-{index}-`
   naming, since the renderer names by enumerate index): every
   `wall-N-frame-jamb*` object's z-span must match one of that wall's
   expected opening spans `[sill, sill + min(height, 2400 - sill)]`
   (renderer's `wall_height` constant), every `wall-N-door` leaf (leaf
   only — `wall-N-door-*` handle/rose excluded) must span the door's
   effective height from 0, every `wall-N-glass-*`/`wall-N-mullion-*`
   must match a window's glazing span (15mm inset per the renderer's
   `glass_inset`), and every door/window opening must have its jambs and
   its leaf/glazing PRESENT. Tolerance 30mm. `opening_type == "opening"`
   (passages, frameless by design) exempt from presence checks.

## Files in scope

- `scripts/build-simplifier-render-plan.py`
- `scripts/build-simplifier-render-plan.test.py`
- `scripts/pose-golden-vectors.json` (new)
- `scripts/render-furnished-dollhouse.py` (one dict entry + comment)
- `scripts/verify_render_blend.py`

## Explicitly out of scope (agreed follow-up slices)

- R7 (door pose in scene vs plan): needs the renderer to stamp
  requested/resolved pose metadata into the .blend first (Plan 2).
- R9-as-certificate (mirror check): rejected by Codex as an
  implementation test, not a semantic invariant; the datablock check
  stays out of the certificate. A plain unit test may come with Plan 2's
  semantic chirality probe.
- Cutaway policy function + removal of the dead `cut_features` rail
  (Plan 3).
- TS-side golden-vector reader; conventions document (last).
- `sofa_1sitzer` override; residual question of whether corrected-path
  furniture positions (annotation extent) are even meaningful on
  correction-document geometry (pre-existing, documented in
  `workbench_furniture()`'s FURNITURE_COORDINATE_SPACE refusal).

## API, schema, and data-contract effects

None externally. The corrected-path plan output changes for
rotation/mirror/position of furniture — by design; that path's current
output is provably wrong. Certificate gains one rule; a build violating
R8 now fails certification (that is the point).

## Acceptance criteria

- Same furniture file compiled through BOTH paths yields identical pose
  fields (rotation_deg, mirrored, position_mm) — the regression test for
  the double transform.
- Golden vectors pass against `workbench_furniture()`.
- Removing the ecksofa override changes nothing on bungalow_039 (stored
  rotation 0) — byte-comparable placement identical; and a nonzero editor
  rotation now reaches `instance.rotation_euler` (unit-covered).
- Door metamorphic tests pass; the existing bungalow_039 door regression
  test still passes unchanged.
- R8 passes on the freshly built bungalow_039 blends; artificially
  re-enabling the old dollhouse-cut behavior (thought experiment recorded
  in the test comment, not an automated toggle) would fail it.
- Full existing test files pass; `run_project.py bungalow_039` certifies
  both styles with R8 in the chain.

## Tests and verification commands

Added to `scripts/build-simplifier-render-plan.test.py`:
- `test_pose_golden_vectors_hold_for_the_workbench_path` — reads
  `pose-golden-vectors.json`, runs each editor pose through
  `workbench_furniture()` (temp `FLOORPLAN_WORKBENCH_DATA_DIR`, real
  bungalow_039 extent), asserts compiled pose.
- `test_corrected_path_agrees_with_the_workbench_path` — same temp
  furniture file through `corrected_placements()`; pose fields must equal
  the `workbench_furniture()` output (fails on the old double transform).
- `test_door_pose_metamorphic_relations` — for
  `door_pose_in_wall_frame()`:
  (a) wall ends swapped → output labels swap (same physical door);
  (b) door points swapped WITH door-relative labels swapped → identical
  output; (c) door points swapped, labels unchanged → output flips (must
  NOT be identical — describes the other hinge).

R8 verification: rebuild bungalow_039 and confirm `PASS
R8_opening_heights` on all four interior blends, plus the full existing
PASS list.

```
cd born2thrill-local-workbench
python scripts/build-simplifier-render-plan.test.py -v
python scripts/go.test.py -v
FLOORPLAN_WORKBENCH_DATA_DIR=E:\born2thrill-local-workbench-data python scripts/run_project.py bungalow_039 --styles modern,classic
```

Existing tests are not deleted, skipped, or weakened.

## Protected and risky paths

- R8 enters the certificate gate, so a false alarm blocks production.
  Mitigations: component-specific expectations (not naive full-height),
  30mm tolerance, wall-height clamping honored, passages exempt, and the
  rule is validated against all four real bungalow_039 blends before this
  plan is closed. Codex's ordering (oracle proven → then gate) followed.
- Removing the corrected-path transforms changes that path's output;
  since no current production run uses `--corrected` (verified: go.py
  never passes it), no delivered artifact changes.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference? Required answer: no. Pose
plumbing, an override deletion, a pure-function extraction, and a
verification rule; no new geometry source, no publish/email path.

## Customer, email, database, deployment, and external effects

None. bungalow_039 goes stale under the toolchain hash and is rebuilt as
part of verification (expected).

## Failed-hypothesis log

Not applicable — every claim above verified in code this session, plus
independent confirmation by Codex.

## Rollback

All changes on the already-dirty uncommitted tree; revert per file.
Removing R8 from `verify_render_blend.py`'s check list restores the old
gate exactly.

## Unresolved questions

None for this slice.

## Completion record (2026-08-22)

All four points implemented, tests first (TDD baseline captured: 3 new
tests failing on old code, golden-vectors test already green on the
validated workbench path).

1. `corrected_placements()`: second transform removed (position, points,
   rotation, mirrored all pass through from `workbench_furniture()`);
   unused `flip` parameter removed from signature and call site. BONUS
   FIND during implementation: the corrected path could not even run for
   current-space furniture — `level_room_extent()` was called with the
   correction document's "floor-0" name, which `floor_scale` doesn't know,
   so `workbench_furniture()` hard-exited "cannot derive the room extent".
   Fixed by resolving the extent through the same alias list the file
   lookup already used.
2. `ROTATION_OVERRIDE["ecksofa"]` deleted; comment records why and the
   renderer-never-overrides-plan rule; `sofa_1sitzer` untouched, roadmap
   follow-up. Source-level guard test added (AST-parses the dict).
3. `door_pose_in_wall_frame()` extracted as a pure function (points +
   labels in, wall-frame labels out); call site slimmed; behavior
   identical (existing bungalow_039 door regression test unchanged and
   green). Metamorphic tests per Codex's corrected formulation.
4. `check_opening_heights()` (R8) added to `verify_render_blend.py` and
   wired into the check list. Oracle proven BOTH directions before
   gating, per the agreed ordering: PASS on the current fixed
   bungalow_039 blend; FAIL on the pre-cut-fix `.blend1` backup with
   failure lines naming exactly the defects Rainer saw (Küche leaf cut at
   1003mm vs expected 2010, glazing at 1558mm vs expected 2235). One
   oracle correction during proving: the storey-base anchor initially
   used the floor slab top (+220mm above wall feet) and failed a correct
   scene by exactly that offset; re-anchored on the wall bodies' minimum
   z.

Verification: `build-simplifier-render-plan.test.py` 11/11 OK;
`go.test.py` 4/4 OK (needs `FLOORPLAN_WORKBENCH_DATA_DIR`, pre-existing);
full `run_project.py bungalow_039 --styles modern,classic` rebuilt and
certified both styles with `PASS R8_opening_heights` on all four interior
blends and the full existing PASS list; fresh handoff.json written.

Files changed: `scripts/build-simplifier-render-plan.py`,
`scripts/build-simplifier-render-plan.test.py`,
`scripts/pose-golden-vectors.json` (new),
`scripts/render-furnished-dollhouse.py`, `scripts/verify_render_blend.py`.

## Correction record (2026-08-22, late evening)

After the completion record above, Rainer reported from the actual render:
"doors are still wrong and the couch is still not mirrored" → the fixes
had been verified for internal consistency but never against the
user-visible surface. Three further, real defects found by measuring the
annotator/editor visuals against the built .blend:

1. **Door swing is COUPLED to the hinge label.** drawDoorSwing() rotates
   the HINGE->FREE direction, which reverses when hinge_side="end"; the
   first fix flipped the labels independently, leaving every hinge="end"
   door (Schlafzimmertuer) opposite to its preview.
   `door_pose_in_wall_frame()` rewritten geometrically (compute the drawn
   side, express it in the wall frame); metamorphic tests corrected,
   including the new relation (d): flipping only the hinge label flips
   BOTH outputs. End-to-end probe (annotator side vs actual leaf in the
   blend): all 6 explicit doors STIMMT.
2. **Heuristic doors swung into the Diele.** "Smaller room wins"
   contradicted the docstring whenever the hallway was smaller; the
   Wohnzimmertuer opened into the Diele. add_door_leaf() now never swings
   into a `circulation` room when the other side is a real room
   ("livingroom door is still false").
3. **The couch mirror was wrong in TWO layers.** (a) Instance mirror
   flipped the depth axis (backrest swapped, chaise stayed) — changed to
   the LONG axis, matching the editor's scale(-1,1). (b) The editor's
   top-down symbol artwork is the MIRROR of the model's native
   orientation (documented since 2026-08-10 in the MODEL_FACING comment,
   never wired): fixed in the model-canonicalization layer by returning
   "ecksofa" to MODEL_MIRROR_Y, pinned by Rainer's in-situ contact-sheet
   pick (Panel 6 of the real living room, "6") plus his editor
   screenshot. Compiler contract and golden vectors UNCHANGED — the
   correction is per-model, exactly where the architecture says it
   belongs. Probe confirms: editor(rot 0, mirrored) == Panel 6 pose in
   the certified blend (chaise +X, backrest to the wall).

Also from this round: the "always exempt openings from the dollhouse cut"
decision (plans/dollhouse-cut-always-exempt-openings-v1.md) materialized
as its documented risk — full-height door towers in knee-high walls,
floating window frames on the front kerb ("look at your fucking blender
file"). A/B comparison rendered (DMH_OPENING_CUT env, default unchanged);
Rainer's pick pending — the loser gets deleted.

All tests green after all three fixes; bungalow_039 rebuilt and certified
both styles; every claim above verified against the built .blend, not
against code consistency.

## Approval record

Approved by Rainer, 2026-08-22: "Plan 1 all 4 points", following the
two-round Codex discussion and the phased proposal presented with exactly
these four points. Panel-6 couch pick and door corrections: Rainer,
2026-08-22 late evening, in-situ.
