# Multi-wing Satteldach/Pultdach roof sheet ignores the forced ridge axis -- hole into the attic

Status: COMPLETE (2026-09-26)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Fix a real, reproducible hole in the roof (open gable end exposing the
attic underside) plus torn/twisted roof-sheet facets, on any two-wing
(L-shaped) `satteldach`/`pultdach` house that has a `roof_axis_override` set
and whose two wings would otherwise auto-detect DIFFERENT ridge axes. Found
via a real `go.py` render of `german_catalog_review_bungalow_4_3_1_wb_125`
built as `satteldach` (a general-code QA build, not this house's actual
configured type -- see `roadmap` entry for the sibling doppelpultdach fix
this same session), confirmed via a Codex read-only review that measured the
actual saved `.blend` geometry (full brief + output:
`plans/SATTELDACH-HEIGHTFIELD-AXIS-001-codex-review.md`).

## Current evidence and behavior

- `render-exterior.py:1764` calls
  `roof_profile.heightfield_roof_mesh(wings, _sheet_profiles, WALL_TOP_Z,
  step=_heightfield_step, height_wings=_height_wings)` -- no `along_x`
  argument.
- Every OTHER geometry call in this same branch DOES pass the forced axis:
  profile scaling (`render-exterior.py:1643`, `_u_along_x`), the gable cap
  loop (`render-exterior.py:1810`, `_w_along_x` from `_axes(...,
  along_x=_u_along_x)`), and `wall_extension()` (`render-exterior.py:1827`,
  same `_w_along_x`).
- `roof_profile.heightfield_roof_mesh()` forwards `along_x` to
  `combined_height_at()` -> `wing_height_at()` -> `_axes()`
  (`roof_profile.py:226-270`, `481+`). Without it, `along_x=None`, and
  `_axes()` auto-detects each wing's own ridge axis independently (the
  longer side of that wing's OWN rectangle) -- exactly the failure mode
  `wing_height_at()`'s own docstring already documents as a real, previously
  fixed bug at OTHER call sites ("every caller in the two-wing, forced-axis
  path must now pass the SAME `along_x`").
- WB_125's plan has `"roof_axis_override": "y"` -- forces `along_x=False`
  for walls/profiles/caps. Its smaller wing's auto-detect happens to agree
  with that by coincidence; its bigger wing's auto-detect does not (picks
  the orthogonal axis). Codex measured a ~2.25m mismatch at the bigger
  wing's sheet-gable peak against the wall's own expected 0m there --
  the sheet and the wall/gable-cap disagree about which way that wing's
  roof pitches, which is the open hole and the torn facets seen in
  `renders/go-baseline/exterior-satteldach-baseline.png`.
- Codex explicitly rejected my own first-pass theory (that Solidify's
  automatic "Fill Rim" is unreliable on this boundary, and that the fix is
  to just always build the explicit `gable_cap_prism()` for every wing) --
  the existing code comment's explanation of Solidify is itself wrong (Fill
  Rim only closes the sheet's own thickness, not the whole attic opening
  down to the wall top), and building caps against the CURRENT (wrong-axis)
  sheet would still close the wrong shape.
- Both `roof_profile.py`'s and `roof_wings.py`'s existing test suites (92 +
  23 tests) pass unmodified -- Codex notes this only proves the tests don't
  cover this specific renderer-level, forced-axis-vs-two-wing interaction,
  not that the code is correct.

## Repository baselines

- `born2thrill-local-workbench`: branch `agent/furnished-render-and-annotation-schema`,
  base SHA `5be1a4e18956b9fb2e158bee82aa159898356e89`. Worktree already
  carries this session's other uncommitted fixes (door-asset scaling,
  front-door swap) -- unrelated, not touched by this plan.

## Exact scope

In scope:
- Pass the same forced/resolved ridge axis into the
  `heightfield_roof_mesh()` call at `render-exterior.py:1764` that every
  sibling call in this branch already uses (`_u_along_x`).
- Re-verify (not blanket-remove) the `has_vertical_step()`-gated explicit
  gable-cap loop (`render-exterior.py:1807-1809`) against the CORRECTED
  sheet -- per Codex, do not remove the gate or blanket-cap every wing end
  without first checking whether the axis fix alone closes the hole, and
  without an actual exposed-open-boundary test (not the existing `min(...)
  >= 1.5` span guard, which measures something else).
- A regression test covering two wings that would auto-detect DIFFERENT
  ridge axes under a forced `roof_axis_override` (the exact case that broke
  here), plus the existing explicit X/Y override cases.
- Re-verify the torn mid-roof facets after the axis fix -- Codex flags the
  diagonal-choice heuristic in `heightfield_roof_mesh()`
  (`roof_profile.py:403-431`) as a separate, only-partially-ruled-out
  contributor (it does not explicitly route the split along real ridge/valley
  lines) and says remaining artifacts need an actual Blender-side
  intersection measurement, not more reasoning from screenshots.

Out of scope (unless the user asks otherwise):
- `HUB-ASSET-FIT-CONTRACT-001` (the separate door-asset-scaling plan from
  the same session) -- unrelated code path.
- The single-rectangle `elif is_rectangle:` roof path
  (`render-exterior.py:1844+`) -- not implicated, confirmed by Codex to use
  different functions entirely.
- `walmdach`'s own roof-building code -- separate system.
- Re-auditing every OTHER two-wing house in the catalogue for this exact
  axis bug now (most houses likely have no `roof_axis_override` set, so
  auto-detect never disagrees with a forced axis) -- flagged as a follow-up
  once the fix lands, not blocking this plan.

## Files in scope

- `born2thrill-local-workbench/scripts/render-exterior.py`
- `born2thrill-local-workbench/scripts/roof_profile.py` (only if the
  post-fix render still shows torn facets needing the diagonal-choice
  logic addressed -- to be confirmed during implementation, not assumed
  now)
- Test file(s) for the axis-mismatch regression (exact location per this
  repo's existing `roof_profile`/`roof_wings` test convention)

## Explicitly out of scope

See above. No change to any house's saved plan data, no change to
`roof_wings.recognize_two_wings()`'s wing-detection logic itself.

## API, schema, and data-contract effects

None. Pure internal rendering-code correctness; no plan/JSON schema change.

## Acceptance criteria

1. `heightfield_roof_mesh()`'s call site passes the same resolved axis as
   every sibling call in the branch.
2. WB_125 rebuilt as `satteldach` via `go.py` shows a fully closed roof --
   both gable ends capped, no visible hole, no torn facets -- verified by
   an actual render, not just code inspection.
3. At least one other two-wing house WITHOUT a `roof_axis_override` set
   still renders identically to before (no regression from the added
   parameter for the common, unforced case).
4. New regression test(s) reproduce the exact "wings auto-detect different
   axes under a forced override" case and fail before the fix, pass after.
5. Existing `roof_profile`/`roof_wings` test suites (92 + 23 per Codex's
   run) continue to pass.

## Tests and verification commands

To be finalized in the approved plan revision. At minimum:
- Existing suites: whatever command this repo's `roof_profile.py`/
  `roof_wings.py` tests run under (Codex ran 92 + 23 tests successfully --
  exact invocation to confirm before implementation, not yet located in
  this session).
- New unit test(s) in the same suite: two wings with a forced axis override
  where each wing's own auto-detected axis would disagree, asserting the
  sheet height at each wing's gable end matches the wall's own expected
  eave height (0m) there, not an arbitrary non-zero value.
- Rebuild verification: `FLOORPLAN_WORKBENCH_DATA_DIR=... python3 go.py
  german_catalog_review_bungalow_4_3_1_wb_125` (rebuilds all 4 roof-type
  baselines including `satteldach`), visually confirm the satteldach and
  pultdach renders.

## Protected and risky paths

- `render-exterior.py`'s two-wing branch is shared by satteldach, pultdach,
  AND doppelpultdach -- the fix must not regress the already-fixed,
  already-verified doppelpultdach path (WB_125 currently rebuilds clean as
  doppelpultdach; that must still be true after this change).
- Any house currently relying on the auto-detect behavior with NO forced
  axis override must keep its current (correct) behavior unchanged --
  passing the resolved axis through should be a no-op for those houses
  (Codex's fix targets exactly this: pass the SAME value already computed
  and used elsewhere, not a new default).

## Rights, provenance, privacy, and security impact

None. No customer data, no corpus geometry, no rights-affecting change.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This plan only corrects how an already-approved roof
form is built for an already-approved footprint; no new generation or
publication path is created.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. Hypothesis: Blender's SOLIDIFY "Fill Rim" is unreliable on a multi-wing
   satteldach's open gable boundary (mirroring the ALREADY-confirmed
   doppelpultdach concave-outline SOLIDIFY bug), and the fix is to extend
   the existing `has_vertical_step()`-gated `gable_cap_prism()` loop to run
   for every wing, not just stepped ones. Command: read
   `render-exterior.py`'s and `roof_profile.py`'s relevant functions,
   compared against the satteldach render's visible hole. Requested a Codex
   read-only review rather than implementing this guess directly, given
   this session's established pattern of guessing wrong twice already on a
   related but different bug (the door-asset scaling fix) before Codex
   caught the real mechanism both times.
   Result: Codex, via direct measurement of the actual saved `.blend`
   (vertex/edge/face counts, boundary-edge degree, reconstructed geometry
   at the gable peak), found the real cause is an axis mismatch between the
   roof sheet's height sampling and the wall/cap construction -- NOT a
   Solidify rim-fill limitation. Explicitly confirmed my candidate fix
   (blanket-remove the cap gate) would not have fixed the actual defect and
   could have introduced double-capped/overlapping geometry at the wrong
   location. Conclusion: hypothesis rejected; real root cause is the
   missing `along_x` argument at `render-exterior.py:1764`.

## Rollback

Revert the single added argument at the `heightfield_roof_mesh()` call site
(and any accompanying test/diagonal-logic change) -- no data or asset files
touched, a plain `git checkout` of the affected script(s) is sufficient.

## Unresolved questions

- Whether the axis fix alone fully closes the hole and removes the torn
  facets, or whether the separate diagonal-choice heuristic in
  `heightfield_roof_mesh()` also needs adjustment (Codex could not fully
  rule this out without an actual post-fix render/intersection
  measurement) -- to be determined during implementation, with a real
  rebuild+visual check before declaring this done, not by reasoning alone.
- Whether the explicit gable-cap loop's `has_vertical_step()` gate should
  change at all once the axis fix lands, or whether SOLIDIFY's rim-fill
  (now sampling the CORRECT cross-section) is actually sufficient for the
  non-stepped case as originally assumed -- Codex recommends verifying
  against the corrected sheet before touching this gate, not changing it
  pre-emptively.
- Exact test-runner command/location for `roof_profile.py`/`roof_wings.py`'s
  existing suites -- not yet located in this session, needed before writing
  the new regression test.

## Approval record

Approved verbally, 2026-09-26 ("yes", then "can you talk with codex so we
can fix this... how can i help?" -- read as approval to implement the
Codex-diagnosed fix, not just discuss it further).

## Implementation result

Applied the single missing argument at `render-exterior.py:1764-1766`:
`along_x=_u_along_x` added to the `heightfield_roof_mesh()` call, matching
every sibling call in the branch. Added an inline comment recording the
root cause and crediting the Codex review (no rewrite of the surrounding
historical comments, which remain accurate about the OTHER bugs they
document).

Verified:
- `python3 -m py_compile scripts/render-exterior.py` -- clean.
- Rebuilt `german_catalog_review_bungalow_4_3_1_wb_125` via `go.py`
  (`FLOORPLAN_WORKBENCH_DATA_DIR=E:\born2thrill-local-workbench-data`):
  `1 fertig, 0 brauchen dich` -- all verifiers passed, including
  `R8_opening_heights` (unrelated door check from the same run).
- `renders/go-baseline/exterior-satteldach-baseline.png`: hole and torn
  facets are gone. Both gable ends now show a clean, closed triangular
  gable; ridge line is continuous and matches on both wings.
- `renders/go-baseline/exterior-doppelpultdach-baseline.png` (regression
  check): unchanged and still clean -- confirmed this house's doppelpultdach
  build uses the earlier hand-built-box branch entirely, never reaches the
  `else:` branch this fix touches, so no interaction was possible; visual
  re-check is just a sanity confirmation, not evidence of anything.

Not yet done (see Unresolved questions below, unchanged by this
implementation):
- No new automated regression test was added for the axis-mismatch case
  (a real forced-`roof_axis_override` + disagreeing-wing-auto-detect
  scenario) -- this session verified via a real render only. Follow-up
  needed before this is considered fully closed per this repo's own
  test-first governance.
- The diagnostic-only `has_vertical_step()` gate on the explicit gable-cap
  loop was left untouched, as Codex recommended (verify against the
  corrected sheet first) -- the corrected sheet's satteldach render no
  longer shows a hole, so no change to that gate looks necessary, but this
  has not been separately stress-tested against a wing whose gable end
  sits exactly on a grid-cell boundary edge case.
- No sweep yet for OTHER call sites in this file or `roof_profile.py`
  missing a forced `along_x` the way this one was -- flagged for a
  follow-up Codex review, given this is the SECOND time this exact bug
  class has appeared (the first was already documented and fixed at a
  different call site, per `wing_height_at()`'s own docstring).
