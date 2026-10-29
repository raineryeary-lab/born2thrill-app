# Stop guessing Hub-asset dimensions -- one shared, verified fit contract

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Every call site that scales an imported Hub asset (`.blend`/`.fbx`/`.glb`) to
a real-world target size currently re-derives that size itself, ad hoc, and
has twice produced a silently wrong result this session alone:

1. `render-furnished-dollhouse.py`'s `add_door_leaf()` scaled the 7976 front
   door against a hardcoded catalogue tuple (`1813, 572, 2180` mm) that does
   not match the model's real geometry (~`1120, 296, 2100` mm) -- caught by
   `R8_opening_heights` only because that one verifier happens to check door
   leaf height.
2. The fix for that (measure the object's own extent instead) introduced a
   units bug -- mixing a millimetre-scaled numerator against a metre-valued
   denominator -- caught only by rebuilding the house and reading the
   verifier output a second time. A Codex read-only review (brief and full
   output in `plans/HUB-ASSET-FIT-CONTRACT-001-codex-review.md`, saved
   alongside this plan) found the exact mechanism.
3. `render-exterior.py`'s `place_asset()`/`get_asset_template()` use the
   IDENTICAL catalogue-tuple pattern as failure #1, for the SAME asset
   (`FRONT_DOOR_ASSET`, same wrong `1813, 572, 2180` tuple) -- Codex confirms
   by direct code reading (not a rebuild) that this path produces the same
   ~1936mm-instead-of-requested-height defect on the exterior door. It has
   never been caught because no verifier checks exterior asset dimensions
   the way `R8_opening_heights` checks interior openings.

Objective: replace the ad hoc, per-call-site guessing with one shared,
measured, unit-consistent fit contract used by both renderers, so a wrong
catalogue number is caught loudly at build time instead of silently shipping
or being caught by accident.

## Current evidence and behavior

- `render-furnished-dollhouse.py:1952` `import_model()` -- appends/imports,
  discards junk reference cubes, joins, bakes a `divisor` unit correction via
  `transform_apply`. Returns an object with baked real-world-metre vertex
  data and identity transform. Does NOT return or expose measured
  dimensions.
- `render-furnished-dollhouse.py:2139` `rest_on_floor()` -- recentres X/Y,
  sits base at local Z=0. Correct and unaffected by this bug (recentring is
  a pure translation).
- `render-furnished-dollhouse.py:1941` `_object_extent()` -- returns
  `[hi-lo per axis]` in scene metres via `obj.bound_box` through
  `obj.matrix_world`. Correct in isolation; the bug was at the call site
  (`add_door_leaf`, ~line 1519-1527), which divided an already-metre value by
  `MM` (0.001) before using it against this metre-valued extent, inflating
  the ratio ~1000x. Fixed inline already (this session, verified: WB_125
  rebuilds clean, `R8_opening_heights` passes).
- `render-exterior.py:939` `place_asset()` / `render-exterior.py:897`
  `get_asset_template()` -- scale against `asset["size_mm"]`
  (`render-exterior.py:773`, the same `(1813, 572, 2180)` tuple), never
  measured against the actual imported object. Confirmed by Codex code
  reading to share failure #1's exact defect; not yet reproduced by an
  actual rebuild+verifier failure because no such verifier exists for the
  exterior path.
- Codex's systemic recommendation (full text in the paired review file):
  centralize import + measurement in the shared importer, have it return
  named, unit-explicit dimensions (`extent_m`, canonical axes, import
  provenance), treat catalogue figures as diagnostic expectations that raise
  loudly on disagreement beyond a tolerance rather than silently driving the
  scale math, and add regressions for this exact failure class (wrong
  catalogue size, unit mismatch, all three import formats, clamp-limit
  violations, exterior placement).

## Repository baselines

- `born2thrill-local-workbench`: branch `agent/furnished-render-and-annotation-schema`,
  base SHA `5be1a4e18956b9fb2e158bee82aa159898356e89` (per Codex's read at
  review time). Worktree already carries this session's uncommitted fixes to
  `render-exterior.py` (door asset swap) and
  `render-furnished-dollhouse.py` (door leaf import + two rounds of the fit
  bug above, now unit-corrected and verified against WB_125).
- `floorplan-simplifier`: not a git repo; uncommitted `app.py` and
  `tests/test_haustuer_zaehlt.py` changes from the same session (unrelated
  main-entrance validation warning, already tested, out of scope here).

## Exact scope

In scope:
- A single shared helper (exact home TBD at implementation time -- most
  likely alongside `import_model()` in whichever module both renderers
  already import from, or promoted to a small shared module if none exists)
  that: imports an asset, measures its real extent post-divisor, and returns
  a fit-scale for a requested target width/height in one unit-consistent
  call -- replacing the duplicated ad hoc scale math in both
  `add_door_leaf()` and `place_asset()`.
- A loud check comparing any caller-supplied catalogue `size_mm` against the
  measured extent, logging/raising when they disagree beyond an agreed
  tolerance (exact threshold and raise-vs-warn behavior: user's call, see
  Unresolved questions).
- Migrating `render-exterior.py`'s `place_asset()`/`get_asset_template()`
  and `render-furnished-dollhouse.py`'s `add_door_leaf()` (the 7976
  main-entrance path) onto the shared helper.
- Regression tests for: the exact 2100mm-actual/2180mm-catalogue mismatch
  case, a deliberately wrong catalogue tuple, a unit-mismatched caller
  (mm vs m), and the exterior `place_asset()` path.

Out of scope (unless the user asks otherwise):
- Re-deriving or fixing the OTHER catalogue `size_mm` entries already in use
  for other assets (windows, ovens, etc.) beyond the front door -- flagged as
  a known risk (any of them could carry the same defect) but not
  individually re-verified here.
- `import_model()`'s junk-cube/shell-discard heuristics themselves (Codex
  finding 4 -- a real, separate risk that a bad `target_mm` could affect
  which geometry survives the join, not just the later scale denominator).
  Worth its own follow-up, not folded into this one.
- Any change to `verify_render_blend.py`'s existing checks other than
  possibly adding a new one for exterior asset sizing (see acceptance
  criteria).

## Files in scope

- `born2thrill-local-workbench/scripts/render-furnished-dollhouse.py`
- `born2thrill-local-workbench/scripts/render-exterior.py`
- `born2thrill-local-workbench/scripts/verify_render_blend.py` (new check,
  additive only)
- New test file(s) for the shared fit helper (location per repo convention,
  TBD at implementation)

## Explicitly out of scope

See above. Also: no change to any asset's actual `.blend`/`.fbx`/`.glb`
file, no change to the annotator/simplifier, no re-verification of assets
other than the 7976 front door.

## API, schema, and data-contract effects

None to the plan/JSON schema. Internal Python function signatures change
(new shared helper; `place_asset()`/`add_door_leaf()` call sites updated),
no external contract affected.

## Acceptance criteria

1. `add_door_leaf()`'s main-entrance path and `place_asset()` both call the
   same shared fit helper -- no duplicated scale-ratio math remains in
   either file for this asset class.
2. Feeding the helper a deliberately wrong catalogue size (e.g. reintroduce
   the `1813, 572, 2180` tuple against the real ~`1120, 296, 2100` geometry)
   produces a loud, visible failure/warning at build time, not a silent
   wrong render.
3. WB_125 rebuilds clean end to end (`go.py`, all verifiers) using the
   shared helper.
4. A new exterior-side check (either a new `verify_render_blend.py`-style
   check against the exterior `.blend`, or an equivalent assertion inside
   `place_asset()` itself) exists so a future exterior sizing regression is
   caught the way `R8_opening_heights` already catches interior ones.
5. All existing tests continue to pass; new tests added per below.

## Tests and verification commands

To be finalized in the approved plan revision, at minimum:
- Unit test(s) for the shared fit helper: correct ratio for matching
  catalogue/measured sizes, loud failure for a mismatched catalogue size,
  unit-consistency (mm target vs metre-returned extent) handled internally
  so no call site can repeat this session's `/ MM` mistake.
- Rebuild verification: `FLOORPLAN_WORKBENCH_DATA_DIR=... python3 go.py
  german_catalog_review_bungalow_4_3_1_wb_125` plus at least one other house
  with a main-entrance door on a different wall angle/opening size.
- Existing suite: whatever this repo's test runner is (no `tests/` review
  done yet for this repo in this session -- to be confirmed before
  implementation).

## Protected and risky paths

- `render-exterior.py` and `render-furnished-dollhouse.py` are both live,
  heavily-annotated production renderers with many unrelated call sites --
  changes must not touch any asset-placement code path other than the two
  named functions.
- `FRONT_DOOR_METALLIC_FIX` and the Specular-IOR clamp inside
  `get_asset_template()` (render-exterior.py:906-928) are unrelated material
  fixes on the same object -- must survive untouched.

## Rights, provenance, privacy, and security impact

None. No customer data, no corpus geometry, no rights-affecting change --
pure internal rendering-code correctness.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This plan only changes how an already-approved,
already-placed asset is SCALED to fit an already-approved opening; it
creates no new geometry-generation or publication path, and does not touch
`validate_annotation_quality()`, export, or the WordPress delivery gate.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. Hypothesis: the catalogue `size_mm` tuple for the 7976 door was correct
   and something else in the height math was wrong. Command: rebuilt WB_125
   with the catalogue-based scale unchanged. Result:
   `R8_opening_heights` failed, leaf spans 0-1936mm vs expected 0-2010mm.
   Conclusion: catalogue tuple's height (2180mm) does not match the model's
   real converted height (~2100mm); confirmed by the exact arithmetic match
   (2100 * 2010/2180 = 1936.3).
2. Hypothesis: measuring the object's own real extent (instead of trusting
   the catalogue) and using it as the scale denominator would fix this with
   no other change needed. Command: edited `add_door_leaf()` to call
   `rest_on_floor()` + `_object_extent()`, rebuilt WB_125. Result:
   `R8_opening_heights` failed worse -- leaf spans 0-2835mm (825mm too
   tall, hit the 1.35 scale clamp). Conclusion (via Codex read-only review):
   `width`/`leaf_height` at this call site are already in metres, but the
   code still divided them by `MM` (0.001) before comparing against the
   metre-valued `_object_extent()` result, producing a ~1000x-inflated
   ratio. Not a measurement-cache or axis-order bug as I'd first suspected
   -- a straightforward unit mismatch, verified by Codex re-executing the
   literal expression from the source.
3. (Not needed -- root cause found and fixed within two hypotheses via the
   Codex review; this plan is the requested follow-up to stop a third
   recurrence.)

## Rollback

Revert the shared-helper migration in both files back to their current
(already-fixed, unit-correct) per-call-site scale math -- no data or asset
files are touched, a plain `git checkout` of the two renderer scripts is
sufficient.

## Unresolved questions

- Exact tolerance for "catalogue disagrees with measured extent" (Codex
  suggests "a documented tolerance blocks unreviewed assets" but does not
  propose a number) -- needs the user's call, likely something like 15-20mm
  given the existing 30mm geometry tolerance used elsewhere
  (`verify_render_blend.py`'s `TOL`).
- Raise (hard-fail the build) vs. warn (log and continue with the measured,
  correct value) when a catalogue figure disagrees -- a hard fail is safer
  but could block an otherwise-fine build over a cosmetic catalogue-typo;
  the user should decide the failure mode.
- Whether to also re-verify the OTHER existing `size_mm` catalogue entries
  (windows, kitchen assets, etc.) for the same defect now, or leave that as
  a separate follow-up once the shared helper exists to check them with.
- Exact location/name for the new shared helper -- no existing shared
  "assets" module was identified between the two renderer scripts; this
  needs a quick look at whether one already exists before deciding to add a
  new file.

## Approval record

Not approved. Stop before implementation.
