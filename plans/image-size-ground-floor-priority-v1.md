# Fix image_size() picking the wrong file for multi-floor projects

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Fix `image_size()` in `build-simplifier-render-plan.py` so it returns the
ground floor's real photo dimensions instead of a generic, unprefixed
`room_concept.png` placeholder whenever one happens to exist on disk. This one
fix resolves BOTH defects Rainer found on `twostorey_046`: the room areas/
proportions being squashed ("aspect ratio totally off") and the missing wall
between HWR/HTR and Diele.

## Current evidence and behavior

- `twostorey_046`'s Möbel-step geometry showed every ground-floor room at
  ~68% of its true area (`Küche/Essen` 30.1m² → 20.4m², `Wohnen` 21.1m² →
  14.3m², `HWR/HTR` 14.5m² → 9.8m² — all the same ~0.677 ratio), and the
  interior wall between `HWR/HTR` and `Diele` was entirely absent from the
  built geometry, even though it's clearly drawn in the source scan and both
  rooms' annotated polygons share the exact same vertices there.
- Root cause, confirmed by reading `image_size()`
  (`scripts/build-simplifier-render-plan.py:292`): for a project with no
  `annotation_space.aspect` override, the file search checks a bare,
  unprefixed `"room_concept.png"` (line 310, `names = ["original_preview.png",
  "room_concept.png"]`) BEFORE any per-floor-prefixed file
  (`"groundfloor_original_preview.png"`, appended later via
  `name.endswith("_room_concept.png")`, which doesn't even match
  `_original_preview.png` names at all). `twostorey_046` has a leftover
  unprefixed `room_concept.png` (1600×1130... actually 1600×1390 px, a
  generic/shared placeholder) that wins over its real
  `groundfloor_original_preview.png` (1130×1448 px) — real aspect 0.780 vs.
  the file that's actually used, 1.151: a 47.5% error on the building's
  height.
- Confirmed by direct reproduction (`Frame` + `build_walls()` called
  directly, bypassing the app): with the CORRECT frame (1130×1448) the
  `HWR/HTR` ↔ `Diele` wall is produced exactly as expected
  (`rooms: ['Diele', 'HWR / HTR']`). With the BUGGY frame (1600×1390) that
  exact wall never appears — the vertical-edge pairing algorithm in
  `build_walls()` instead pairs a *different*, competing pair of edges
  (`Küche/Essen`↔`Wohnen`↔`Diele` merge into one long run), because the
  Y-only compression changes how much various near-coincident edges overlap
  along their length, which is what the pairing algorithm optimizes on. So
  the missing wall is a second symptom of the SAME bug, not an independent
  wall-matcher defect — confirmed empirically, not assumed.
- Impact check across the whole corpus: every project with no
  `annotation_space.aspect` AND a leftover unprefixed `room_concept.png` is
  affected. Checked all 48 such projects: 37 lack the aspect override and are
  therefore actually hit, with errors from 0.2% (imperceptible) up to 47.5%
  (`twostorey_046`) and 47.3%/44.4%/34.6% on three other two-storey catalog
  houses. Checked every one of the 37 for existing `.blend` output: **none
  have been built yet**, so nothing already delivered is affected.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `git status --short` already shows this session's earlier, unrelated
  changes to `render-furnished-dollhouse.py`, `objektmaske.py`, and new files
  `schuetze-garderobe.py`/`.test.py` — this plan adds one more independent,
  small change to `build-simplifier-render-plan.py`.

## Exact scope

In `scripts/build-simplifier-render-plan.py`, `image_size()`: after the
existing `annotation_space.aspect` short-circuit, determine `ground_level`
the same way `geometry_only()` already does, and search for that floor's own
`_original_preview.png` (then its own `_room_concept.png`) BEFORE falling
back to the existing generic/unprefixed names and the other floors'
`_room_concept.png` files. Only the ground floor's dimensions are ever
actually used for the built geometry (`RegisteredFrame` routes every upper
storey through `ground_frame.point()`, per its own docstring and
`frame_for_level()` — the upper floor's own `Frame` is constructed but
unused for non-ground levels), so this alone is sufficient; no change to
`RegisteredFrame`/`frame_for_level()` is needed.

```python
def image_size(project_dir, annotations=None):
    ...
    space = (annotations or {}).get("annotation_space") or {}
    aspect = space.get("aspect")
    if isinstance(aspect, (int, float)) and 0.01 <= float(aspect) <= 100:
        return 1000.0, 1000.0 * float(aspect)

    # RegisteredFrame routes every storey's geometry through the ground
    # floor's Frame (frame_for_level() only ever uses an upper storey's own
    # Frame to build it, then discards it -- see RegisteredFrame.point()),
    # so THIS is the one file whose aspect ratio the whole building's
    # geometry depends on. A bare, unprefixed "room_concept.png" -- a
    # generic leftover many projects still have on disk -- used to be
    # checked FIRST and silently won here for every multi-floor project.
    # Confirmed on twostorey_046: real aspect 0.780 vs the generic file's
    # 1.151, a 47.5% height error, which also silently broke wall-pairing
    # for one HWR/HTR wall (Rainer, 2026-09-15: "the right wall in the htr
    # is missing and the aspect ratio is totally off").
    levels = sorted({item.get("floor_level")
                     for item in (annotations or {}).get("annotations", [])
                     if item.get("floor_level")})
    ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    names = []
    if ground_level:
        names += [f"{ground_level}_original_preview.png",
                  f"{ground_level}_room_concept.png"]
    names += ["original_preview.png", "room_concept.png"]
    names += sorted(
        name for name in os.listdir(project_dir)
        if name.endswith("_room_concept.png") and name not in names)
    for name in names:
        ...  # unchanged from here
```

## Files in scope

- `scripts/build-simplifier-render-plan.py` (`image_size()` only)
- `scripts/build-simplifier-render-plan.test.py` (add cases — see below;
  confirm this file exists and its exact test-runner convention before
  editing)

## Explicitly out of scope

- `build_walls()` / the edge-pairing algorithm itself — not touched, since
  the missing-wall symptom is fully explained by the frame bug above.
- Re-running or re-annotating any of the 37 affected projects. The fix is in
  shared code; each project picks it up automatically the next time its
  geometry is built (Möbel step, `go.py`, `--geometry-only`). No project has
  been built yet, so there is nothing to retroactively repair.
- `annotation_space.aspect`-driven projects (e.g. `twostorey_045`) — already
  unaffected, no change in behavior for them.
- Any change to which file the Annotator itself (`annotate.js`,
  floorplan-simplifier) uses for display — that path was already correct
  (its area labels matched the true per-floor image throughout this
  investigation).

## API, schema, and data-contract effects

None. Pure internal function behavior change; no schema, no new fields.

## Acceptance criteria

- `python build-simplifier-render-plan.py --geometry-only twostorey_046
  <out.json>` produces ground-floor room areas matching the Annotator's own
  displayed areas (30.1, 21.1, 14.5, ... m², not the ~68%-scaled values).
- The same output includes an interior wall between `HWR / HTR` and `Diele`.
- Re-run the same command for `twostorey_045` (an `annotation_space.aspect`
  project) and confirm byte-for-byte identical output before/after (proof
  the fix doesn't touch already-correct projects).
- Spot-check 2-3 of the other 36 affected projects' `--geometry-only` output
  before/after to confirm the aspect ratio corrects there too.

## Tests and verification commands

Add to `scripts/build-simplifier-render-plan.test.py` (confirm exact
runner/import convention from the file itself before writing — likely
`importlib` from the hyphenated filename, `unittest`, matching
`lieferung-pruefen.test.py`'s pattern):
- `image_size()` prefers `"<ground_level>_original_preview.png"` over a
  co-existing unprefixed `"room_concept.png"` of different dimensions, using
  temp-directory fixtures with real minimal PNGs (same PNG-header-writing
  helper pattern as `lieferung-pruefen.test.py`'s `png()` helper).
- `image_size()` still honors `annotation_space.aspect` when present,
  ignoring any files on disk (existing behavior, must not regress).
- `image_size()` still falls back to the old generic names when no
  per-floor-prefixed file exists (existing behavior for older/simpler
  projects, must not regress).

Existing tests: none deleted, skipped, or weakened.

## Protected and risky paths

- `image_size()` is called from 6 sites across the ground-truth geometry
  builder, including the main plan-build path used by `go.py` for every
  house. Change is additive (new preferred names checked first; every
  existing fallback path stays intact and reachable in the same order as
  before), so behavior for any project that doesn't hit the specific bug
  (has `annotation_space.aspect`, or has no ambiguous unprefixed file) is
  unchanged.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This fixes which SOURCE IMAGE DIMENSIONS feed the
existing, already-approved geometry pipeline; it generates no new geometry
concept and touches no publishing/email path. No project has been built with
the old buggy behavior, so there is no previously-published geometry this
could contradict.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. **Hypothesis:** the missing HWR/HTR↔Diele wall is an independent
   wall-matcher defect (edges not exactly coincident / tolerance too
   strict). **Test:** extracted both rooms' real polygons, converted with
   the CORRECT frame, called `build_walls()` directly. **Result:** the wall
   IS produced correctly — this hypothesis is wrong on its own; the wall
   only goes missing when the buggy (wrong-aspect) frame is used instead.
   **Conclusion:** not a separate bug; folded into the single `image_size()`
   fix above (see Current evidence).

## Rollback

Revert the `image_size()` change. No data files are touched by this fix.

## Unresolved questions

None.

## Approval record

Approved by Rainer, 2026-09-15 ("yes").
