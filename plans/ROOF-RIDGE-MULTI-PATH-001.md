# Multiple independent ridge lines (kuechenzeile-style), replacing the forced single connected path

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-01: "we said we would build a 'countertop' line maker, where
i can also draw independent lines" -- referring to kuechenzeile's own
drawing pattern (draw one run, finish it, draw another, each one its own
independent, individually-deletable element). `ROOF-RIDGE-PATH-TOOL-001`
explicitly deferred this ("Multiple SEPARATE paths are out of scope for
v1 -- ... two unconnected ridges on the same roof are a later
extension"). This plan is that extension: replace the single, forced-
continuous `roof_ridge_path` with a list of independent paths,
`roof_ridge_paths`, each drawn and finished on its own.

## Current evidence and behavior

- `floorplan-simplifier/static/dach-editor.js`: `ridgeDraft` (in-progress
  points) and `roofRidgePath` (the one finished path) are both single
  arrays. Finishing a path (double-click, line ~1044-1056) replaces
  `roofRidgePath` wholesale; there is no way to keep a first path and add
  a second, independent one.
- `annotate.js`: saves/loads one field, `roof_ridge_path` (singular),
  lines 564, 3066, 3084-3085, 3615, 3668, 4015.
- `born2thrill-local-workbench/scripts/roof_wings.py`:
  `roof_wings_from_ridge_path(path, footprint)` takes ONE path and derives
  one wing per orthogonal segment of it. `render-exterior.py` lines
  1420-1429 call it once with the plan's single `roof_ridge_path`.
- **Concrete, already-occurred failure this gap caused**: WB_125
  (`german_catalog_review_bungalow_4_3_1_wb_125`) has two wings whose
  ridges do not share a single joint point. Forced into one connected
  path, Rainer's own earlier attempt produced
  `WB_125_REAL_BROKEN_PATH_M` (preserved in `roof_wings.test.py`, and in
  `annotations.json` under `roof_ridge_path_removed_2026_09_29`):
  `[(3.5179, 12.0906), (3.5179, 6.0391), (0.9571, 6.0391), (14.0617,
  6.0391)]` -- the third segment doubles back past the second segment's
  own start point to fake a connection that isn't really there. Rainer's
  own verdict in Blender: "that doesnt look like a working roof" (a
  visibly crossed/jagged surface) -- he then deleted the path entirely
  and the house has run on automatic wing detection (`Fluegel-Erkennung`)
  ever since, which is what today's separate chevron-mitering session
  fixed. This plan directly targets that same house: two straight,
  INDEPENDENT 2-point paths (one per real wing) instead of one contorted
  4-point path.

## Exact scope

1. **UI** (`dach-editor.js`, `annotate.js`, `annotate.html`): generalize
   the existing mini-map ridge tool from one path to a list of paths.
   Finishing a path (double-click/Enter, same gesture as today) commits
   it and immediately allows starting a new, independent path -- same
   "draw one run, then draw the next" flow kuechenzeile/
   vorwandinstallation already give the user elsewhere in this app.
   `drawAxisMini()` draws every committed path plus the in-progress one.
   Deleting one path: click an existing path to select it (reuse the
   point-select convention `punkte-ausrichten.js` already has for
   `roof_ridge_path`), "Firstlinie loeschen" removes the SELECTED path
   when one is selected, or everything when none is (today's behavior,
   kept as the simple fallback).
2. **Persistence**: new field `roof_ridge_paths` (a list of point-lists,
   same `{x,y}` normalized coordinate space as today). The old singular
   `roof_ridge_path` is read for backward compatibility on load (wrapped
   into a one-element list) but never written again. Threaded through
   `annotate.js` (save payload + both load sites), `app.py`
   (`normalize_roof_ridge_path(s)`), `build-simplifier-render-plan.py`.
3. **Renderer**: generalize `roof_wings_from_ridge_path(path, footprint)`
   to `roof_wings_from_ridge_paths(paths, footprint)` -- same per-segment
   derivation math, run independently per path (no cross-path
   connectivity requirement), results concatenated into the single
   `wings`/`along_x` lists `heightfield_roof_mesh()`/`wall_extension()`
   already consume unchanged. Keep `roof_wings_from_ridge_path()` itself
   (singular) as a thin one-path wrapper so existing tests keep passing
   without modification.
4. Re-verify WB_125 end to end: draw its two real wings as two
   independent straight paths, confirm `build-simplifier-render-plan.py`
   -> `render-exterior.py` produces a correct (non-crossed) roof, via a
   real Blender build.

## Files in scope

`floorplan-simplifier/static/{annotate.html,annotate.js,dach-editor.js,
punkte-ausrichten.js}`, `floorplan-simplifier/app.py`,
`born2thrill-local-workbench/scripts/{roof_wings.py,roof_wings.test.py,
render-exterior.py,build-simplifier-render-plan.py}`.

## Explicitly out of scope

- The already-tracked N>2-wing wall-trimming limitation
  (`ROOF-RIDGE-PATH-TOOL-001-FOLLOWUP`, wall exposure hardcoded to
  `wings[0]`/`wings[1]`) -- unaffected by this plan, still open.
- Non-orthogonal ridge segments -- unchanged, still rejected/warned.
- Any change to automatic wing detection (`recognize_two_wings()`) or the
  per-wing axis-override mini-map fallback -- both untouched.

## Schema and dataset-contract effects

New, purely additive field `roof_ridge_paths` (default: absent/empty).
Old `roof_ridge_path` (singular) stays readable for any already-saved
project but is no longer written. No existing field's meaning changes.

## Acceptance criteria

1. WB_125: two independent straight paths (one per real wing) produce a
   correct, non-crossed roof in a real Blender build -- directly
   resolves the 2026-09-29 regression that made Rainer delete the path.
2. A project with an old-style single `roof_ridge_path` (no
   `roof_ridge_paths`) still renders exactly as before (backward compat).
3. UI: draw path 1, finish it, draw path 2 independently; both remain
   visible and individually selectable/deletable.
4. All existing `roof_wings.test.py`/`roof_profile.test.py` tests pass
   unchanged; new tests cover multi-path derivation including the WB_125
   two-independent-paths case.

## Tests and verification commands

- New `roof_wings.test.py` cases: two independent 2-point paths on
  `WB_125_REAL_ROOF_POLY_M` matching `recognize_two_wings()`'s own
  known-good wing numbers (proves the fix, not just a difference); a
  single-path case routed through the new plural function matches the
  old singular function's own output exactly (no regression).
- `python roof_wings.test.py`, `python roof_profile.test.py` (must stay
  green).
- Real `build-simplifier-render-plan.py` + `render-exterior.py` run
  against WB_125 with the two new paths drawn, visual check in Blender.

## Protected local data and risky paths

Must not change `heightfield_roof_mesh()`, `combined_height_at()`,
`wall_extension()`, or `recognize_two_wings()`. Must not delete or alter
`roof_ridge_path_removed_2026_09_29` (the preserved broken-path record in
WB_125's `annotations.json`).

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no -- purely a new input method (plural paths instead of
one) for already-existing, already-gated roof geometry; no new
generation/publication/email path.

## External effects

None.

## Failed-hypothesis log

N/A -- new plan, no implementation attempted yet.

## Rollback

Revert the files listed above. `roof_ridge_paths` is additive/optional;
reverting the renderer/persistence changes alone (leaving the UI) is also
safe since an absent field means unchanged (singular-path or automatic)
behavior.

## Unresolved questions

- Per-path delete needs a selection UX on the mini-map (160x160 canvas,
  small target). First cut: click near any point of a committed path
  selects that whole path; Escape or clicking empty space deselects.
  Revisit if that proves too fiddly at that canvas size.

## Approval record

Not approved. Stop before implementation.
