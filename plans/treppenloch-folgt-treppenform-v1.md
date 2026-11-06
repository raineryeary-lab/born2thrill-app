# Treppenloch folgt der Treppenform, nicht ihrem Rechteck

Status: IMPLEMENTED 2026-10-20 -- verified on twostorey_059 (upper floor, scratch build); not committed

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

The opening in the upper floor slab should hug the stair. Rainer, 2026-10-20: "sometimes it differs from just hugging the stairs and if the treppenloch is bigger we could actually see what's downstairs."

## Current evidence and behavior

- `build-simplifier-render-plan.py::annotation_stair_core` (around line 3075) builds `shared_stair_core.polygon_mm` as the TRUE outline: the Lauflinie swept by the flight width, with mitred corners (`polygon_mm = left + reversed(right)`, around line 3190). For an L-shaped (viertelgewendelt) or U-shaped (halbgewendelt) stair this is an L or U polygon.
- `render-furnished-dollhouse.py` lines 2832-2838 throw that shape away:
  `_hole = (min x, max x, min y, max y)` of the polygon, i.e. its bounding RECTANGLE.
- `room_slabs()` (around line 2870) cuts that rectangle out of every room floor, as four axis-aligned regions (left / right / in front / beyond).
- Result:
  - Straight stair (2 path points): the polygon IS a rectangle, so the hole is exact. Correct today.
  - L stair: the empty quadrant beside the turn is cut open too, so a floor-sized hole shows the storey below.
  - U stair: the strip between the two flights (the Treppenauge) is cut open over its full length.
- The upstairs Geländer already follows the TRUE outline. Around lines 4155-4196 it splits `corners` (the same mitred `polygon_mm`) back into per-segment left/right edges plus the start and end edges, exactly as annotate.js's `stairRailingEdges()` does. On an L or U stair the railing and the floor cut therefore disagree today:
  - The railing stands on the real stair edge, but the floor on its far side (the over-cut bbox corner or the Treppenauge) is missing. It stands at the edge of a void, not of a floor, which breaks the render acceptance rule that nothing may float where its support was cut.
  - The over-cut void itself has no railing at all, so it is an open drop.
  - Fixing the floor cut fixes both: no railing code changes are needed.
- The ground-plane cut (around line 6890) also uses the rectangle. That plane lies a full storey down, so the rectangle is harmless there.

- Measured 2026-10-20 in `E:/born2thrill-local-workbench-data/corrections/twostorey_059/renders/go-baseline/interior-modern-upper-baseline.blend` (built 08:31). The stair is a U (halbgewendelt), path (5603,2645) -> (4484,2645) -> (4484,5378) -> (5999,5378), 900 mm wide:
  - The floor is open over the whole bbox, x 4034..5999, y 2195..5828 (log: "Treppenloch 1965 x 3633mm").
  - The Treppenauge, x 4934..5999 / y 3095..4928, is about 1.07 x 1.83 m of void. The railings 0-left, 1-left and 2-left stand along its edge with no floor under their balusters on the hole side. On the fourth side (x = 5999), the hallway floor ends at the void with NO railing: an open drop.
  - A notch, x 5603..5999 / y 2195..3095, is void too. `loch-rail-start` (x 5603) stands between two voids, and the 396 mm gap from it to the hallway floor has no railing.
  - With the polygon cut, both voids become floor. All six chosen railings then stand on a floor edge, and the Austritt (x 5999, y 4928..5828) stays open as intended.

## Repository baselines

- Repo `born2thrill-local-workbench`, branch `agent/furnished-render-and-annotation-schema`, HEAD `5be1a4e`.
- User-owned dirty worktree: 351 entries in `git status --short`. `scripts/render-furnished-dollhouse.py` already carries large uncommitted changes, including today's door-angle and bathtub edits (`plans/tuerwinkel-und-badewanne-v1.md`). Nothing is cleaned or reverted.

## Exact scope

Cut the actual stair polygon out of the upper floor slab instead of its bounding box. Still no Blender boolean (the file records two silent boolean failures).

Method:

1. Keep the polygon. Split it into the per-segment quads it was built from: for n path points the polygon has 2n vertices, and quad i = `left[i], left[i+1], right[i+1], right[i]`, with `right[i] = poly[2n-1-i]`. Because the corners are mitred, these quads tile the outline exactly. Each quad is convex; on the usual orthogonalised path each one is an axis-aligned rectangle.
2. Generalise `_clip_axis` into a half-plane clip (Sutherland-Hodgman against an arbitrary line). The axis-aligned case is then one call of it, giving the same exact result as today.
3. Cut each quad out of the room pieces in turn. "Room minus convex quad" = for each quad edge k, the part of the room outside edge k and inside edges 0..k-1. That gives up to 4 disjoint pieces, exact, and the same idea as today's four regions. Apply quad after quad to all pieces. Keep the existing sliver filter (< 0.01 m2).
4. Fallback: if the polygon does not have an even vertex count of at least 4 (for example a stair core from a correction document with another shape), keep today's bounding-box cut and print a `[dollhouse] Treppenloch WARNUNG` line naming the reason. Never silently no hole.
5. The log line reports the true opening area in m2 next to the bounding-box size, so a build log shows the difference.

## Files in scope

- `scripts/render-furnished-dollhouse.py`: `_hole` set-up, `_clip_axis` / new half-plane clip, `room_slabs()`, the Treppenloch log line.
- `scripts/render-persp-test.py`: the same change, only if Rainer wants the test copy kept in step (it was kept in step for the door and bathtub edits).
- New test `scripts/treppenloch_form.test.py`.

## Explicitly out of scope

- The ground plane a storey down (stays a rectangle, harmless).
- The railing logic itself (already shape-aware; it starts standing on floor once the cut matches).
- Shortening the hole to headroom (in reality only the upper part of a flight needs an opening). Possible later; not asked for.
- `luftraum` rooms (drawn on purpose, intentionally have no floor).
- The Annotator, the render plan builder and the stair polygon itself.
- Rebuilding, re-rendering or re-uploading any house.

## API, schema, and data-contract effects

None. `shared_stair_core.polygon_mm` is read as it already is. No annotation, plan or catalogue schema change.

## Acceptance criteria

1. Straight stair: identical slab pieces to today (same hole, same area, within 1 mm2).
2. L stair: total slab area = room area minus stair-polygon area (not minus bounding-box area). The empty bbox quadrant is floor.
3. U stair: the Treppenauge between the flights is floor.
4. No floor piece overlaps the stair polygon by more than 0.01 m2.
5. Unknown polygon shape: bbox fallback plus the WARNUNG line, never an uncut floor.
6. Every upstairs `loch-rail-*` segment has slab on its outer side along its whole length (sampled every 100 mm, 50 mm outside the edge). No railing borders a void, and no void edge lacks either a railing or a wall.
7. One rebuilt house with a gewendelte stair (candidate: twostorey_059, then onehalfstorey_029), checked in the .blend: no slab face inside the stair outline, slab present in the old over-cut corner. Then the render checked by eye.

## Tests and verification commands

- New `scripts/treppenloch_form.test.py`, pure Python. It loads `_clip_axis` / the new clip and `room_slabs` from the renderer by AST isolation, the way the existing renderer cases are tested, so no Blender is needed. Cases 1-5 above, with shoelace areas. Plus case 6 as a pure-geometry check: the railing edges, derived from the polygon the same way the renderer does, lie on slab-piece boundaries with slab outside.
- `python scripts/treppenloch_form.test.py`
- Existing tests must still pass. In particular, run `python scripts/build-simplifier-render-plan.test.py`; it has stair-polygon cases, untouched.
- Syntax check of the edited files.
- Rebuild of the one house (acceptance 7) only after the tests pass. Only that house, no upload.
- No existing test is deleted, skipped or weakened.

## Protected and risky paths

- **Toolchain hash:** `batch-build.py::toolchain_now()` hashes `render-furnished-dollhouse.py`, so every existing build will count as outdated (already true after today's door and bathtub edits).
- Concave room plus several quads gives more slab pieces per room. They are separate objects, `floor-<room>-<k>`. Anything that counts or names floor objects (verifier R3, `holes_cut`) must still pass; checked in the rebuild.
- A diagonal (non-orthogonalised) flight gives non-axis-aligned quads. The half-plane clip handles that; test case 5b covers it.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. The change only decides which part of an existing floor slab is left out, using the stair polygon already in the render plan. It adds no geometry source and touches no approval, publication or email path.

## Customer, email, database, deployment, and external effects

None. No upload, no commit, no push.

## Failed-hypothesis log

None yet. The cause was found by reading the code: bbox at render-furnished-dollhouse.py:2837 against the true polygon at build-simplifier-render-plan.py:3190.

## Rollback

Revert the `_hole` / `room_slabs` / clip hunks in the two renderer files and delete `scripts/treppenloch_form.test.py`. Rebuild affected houses.

## Unresolved questions

1. Keep `render-persp-test.py` in step, yes or no?
2. Test house for acceptance 7: twostorey_059 (U stair, measured above) is now the natural first choice; onehalfstorey_029 second.
3. Should already published houses with L or U stairs be rebuilt afterwards (separate decision, separate upload approval)?

## Approval record

Approved by Rainer in chat, 2026-10-20: "Approved: implement treppenloch-folgt-treppenform-v1, test on twostorey_059, keep render-persp-test.py in step." Unresolved questions 1 and 2 are answered by that (persp-test kept in step; test house twostorey_059). Question 3 stays open.


## Verification record (2026-10-20)

- `python scripts/treppenloch_form.test.py`: 14 tests OK, the 7 cases run against both renderers. All 14 failed before the implementation.
- `render-furnished-dollhouse.test.py` 26 OK, `glasschiebetuer_render.test.py` 7 OK, `stair_access.test.py` 9 OK, `hausdaten.test.py` 37 OK.
- `build-simplifier-render-plan.test.py`: 72 run, 1 FAIL, 6 skipped. The failure is `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`: six expected door ids are missing from a live project's annotations. That file and the code it tests were not touched by this change, so the failure is pre-existing and unrelated.
- Rebuild: twostorey_059 upper floor only, into the session scratch folder, NOT into go-baseline. `DMH_FLOOR=upperfloor DMH_FINISH=modern-a`, plus `DMH_ALLOW_STALE=1`: the drawing changed after the 08:31 plan, and the same plan was wanted to compare like with like.
- Probe (top faces of all `floor-*` and `slab-under-wall-*` objects, point-in-polygon), 08:31 baseline -> new:
  - Treppenauge (5400,4000): VOID -> floor. Notch (5800,2600): VOID -> floor.
  - Floor over the stair (grid of 50 mm samples inside the outline): 0 -> 0.
  - Railing outer side, void samples: 1-left 17/17 -> 0/17, 0-left 5/5 -> 0/5, 2-left 9/9 -> 0/9, start 8/8 -> 0/8, 2-right 0 -> 0, 0-right 0 -> 0. The Austritt (`end`) has no railing and floor beyond it, as intended.
- Render checked by eye: the U opening hugs the flights, there is floor between them, and the railings run on floor edges.
- `render-persp-test.py`: untracked, no prior copy exists. Its replaced `room_slabs` tail was 3 lines shorter than the main renderer's (an older variant); the floor loop after it is untouched. The same tests pass against it.
- Not done: no full `go.py` rebuild, no verifier (`verify_render_blend.py`) run, no upload. Every existing build is now outdated by the toolchain hash.
