# Innentueren 20 Grad offen, Badewanne Armaturen hinten

Status: IMPLEMENTED -- retroactive plan (edits made 2026-10-19/20 at Rainer's direct request, before this plan existed)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

1. Open interior doors 20 degrees instead of 45. Rainer, 2026-10-19: "45 degrees make the doors disappear with the camera perspective."
2. Put the bathtub's taps on the back of the symbol. Rainer, 2026-10-20: the symbol arrow runs back to front, but the rendered tub has its taps at the front: "it is backwards".

## Current evidence and behavior

- `DOOR_OPEN_DEG = 45.0` drove every open interior leaf (`leaf_pose(hinge_sign, DOOR_OPEN_DEG)`, also on the re-hinge fallback). The main entrance stays closed (`ist_haustuer` -> 0.0) and is unaffected.
- `MODEL_FACING_DEG` convention (comment above the table): after the long axis is turned to X, the BACK of the piece faces +Y. `"badewanne": 180` was justified by "Tap end points -Y".
- Measured 2026-10-20 in Blender 5.0, headless (`--factory-startup`), on `E:\_models_hub\_extracted\Large_Rounded_Bathtube_BLEND\Large Rounded Bathtube.blend` (the modern and classic pick in `data/symbol-model-picks.json`):
  - tub `cgaxis_models_84_01_02`: x -2.11..2.18, y -1.01..1.01 (long axis already along X, so `align_to_footprint` does not turn it)
  - standing mixer `cgaxis_models_84_01_01`: x -0.34..0.18, y -0.06..1.27, z up to 2.58
  - So the taps sit on the +Y long side, which is already the back. The 180 put them at the front.

## Repository baselines

- Repo `born2thrill-local-workbench`, branch `agent/furnished-render-and-annotation-schema`, HEAD `5be1a4e`.
- 351 entries in `git status --short` before and after; user-owned dirty worktree, left untouched.
- `scripts/render-furnished-dollhouse.py` was already modified (uncommitted, +4755/-148 against HEAD) before this task.
- `scripts/render-persp-test.py` is untracked.

## Exact scope

- `scripts/render-furnished-dollhouse.py`: `DOOR_OPEN_DEG` 45.0 -> 20.0; `MODEL_FACING_DEG["badewanne"]` 180 -> 0, with the measurement recorded in the comment.
- `scripts/render-persp-test.py` (test copy of the renderer): the same two values, kept consistent.

## Files in scope

- `scripts/render-furnished-dollhouse.py`
- `scripts/render-persp-test.py`

## Explicitly out of scope

- `eckbadewanne`, showers, the WC and every other `MODEL_FACING_DEG` entry.
- Door swing direction and hinge side (see the door-swing convention memo; that is for future auto-generation only).
- The main entrance (stays closed).
- Rebuilding or re-uploading any house.

## API, schema, and data-contract effects

None. No annotation, render-plan or catalogue schema changes. Placement data (`rotation_deg`) is unchanged; only the model's native-facing correction changes.

## Acceptance criteria

- On a rebuilt house, open interior doors stand at 20 degrees and stay visible from the dollhouse camera.
- On a rebuilt house with a `badewanne`, the mixer sits on the side opposite the symbol's arrowhead (back), against the wall.
- No other furniture changes orientation.

## Tests and verification commands

- Done: both files parse (`ast.parse`); no existing test references `DOOR_OPEN_DEG` or the badewanne facing value (grep over `scripts/*.test.py`, `scripts/blender-harness/*.py`).
- Pending: rebuild one house with a bathtub and open doors and check the build by eye and in the .blend (mixer y relative to the tub, leaf angle). No new automated test was added; a facing assertion for `badewanne` in the Blender harness would be the natural one.
- No existing test was deleted, skipped or weakened.

## Protected and risky paths

- **Toolchain hash:** `batch-build.py::toolchain_now()` hashes `render-furnished-dollhouse.py`. Any edit to it makes every existing build count as built with an old toolchain, so the Workbench overview will show houses as outdated until they are rebuilt. This is the intended mechanism, but it affects every house, not only ones with bathtubs.
- Already published WordPress images keep the old 45-degree doors and the reversed tub until those houses are rebuilt and re-uploaded.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Only two renderer constants changed (a door-leaf angle and a model-facing correction). No generation, approval, publication or email path was touched; geometry still comes only from the annotations.

## Customer, email, database, deployment, and external effects

None. Nothing rebuilt, uploaded, committed or pushed.

## Failed-hypothesis log

None. One hypothesis (the facing comment is wrong about the mesh), confirmed by measurement.

## Rollback

In both files, set `DOOR_OPEN_DEG` back to 45.0 and `"badewanne"` back to 180. Rebuilding then restores the old toolchain hash only if the file is byte-identical to before, so a rebuild is needed either way.

## Unresolved questions

- Should already published houses with bathtubs be rebuilt and re-uploaded now, or only when they come up again?

## Approval record

Requested directly by Rainer in chat (2026-10-19 door angle, 2026-10-20 bathtub). This plan was written afterwards at his request ("Yes, write the plan file and roadmap entry for the door-angle and bathtub changes"). The edits happened before the plan, contrary to AGENTS.md step 5.
