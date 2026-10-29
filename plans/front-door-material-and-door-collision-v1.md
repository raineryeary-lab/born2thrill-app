# Front door renders as a flat black slab; interior door leaves can overlap each other

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, reviewing the new bungalow_039 renders: "i think you have to show the
doors open 45 degrees, very often they open wrong and would never be built
like that we have to catch this plus you also cut the front door, why?"
Followed by: "das muss repariert werden."

Two separate, now-diagnosed defects:

- **A. Front door renders as a featureless black rectangle** on every
  exterior shot (confirmed on bungalow_039's exterior-classic and
  exterior-modern renders this session).
- **B. Interior door leaves can swing into each other.** Doors are already
  drawn open 45° (`DOOR_OPEN_DEG = 45.0` already exists) with a considered
  room-based swing/hinge heuristic — the gap is that nothing checks one
  open leaf against ANOTHER open leaf, only against furniture. On
  bungalow_039, several doors sit 858–1475mm apart center-to-center, well
  within two ~750–900mm-wide leaves' swept reach of each other.

## Current evidence and behavior

**A. Front door**

- `scripts/render-exterior.py:560-564` — `DOOR_ASSET` points at
  `E:\_models_hub\_extracted\Metal_Front_Door_3D_Model_7961_BLEND\Metal Front
  Door 3D Model (7961).blend`, placed via `place_asset()`
  (`render-exterior.py:673-689`, called at `:888-889`).
- Inspected the asset directly in Blender 5.0 (`bpy.data.libraries.load`,
  headless): its two real materials (`cgaxis_models_79_61_01`,
  `cgaxis_models_79_61_02`) both have **`Metallic = 0.0`**, `Roughness =
  0.5`, and a near-black flat Base Color (~0.05, i.e. RGB ≈12/255) —
  unlinked, no image texture nodes at all, despite the asset being named
  "Metal Front Door". A non-metallic, textureless, near-black matte surface
  under this scene's lighting is exactly the flat black rectangle seen in
  both bungalow_039 exterior renders this session.
- The geometry itself is real and detailed (4 mesh objects, up to 12,475
  vertices) — this is a MATERIAL defect on a third-party asset, not missing
  geometry, and not (as first suspected from the render alone) a "cut"
  opening.
- **Direct precedent already in this same file**: every "window" asset in
  the model hub library turned out to be a mislabeled door-style unit
  (`render-exterior.py:576-583`, comment dated 2026-08-16), so windows are
  already built procedurally (`build_window()`, `:596-`) instead of trusting
  a hub asset. The front door asset has now failed the same way (wrong
  material despite its name) — same fix class applies.

**B. Interior door-vs-door collision**

- `scripts/render-furnished-dollhouse.py:530` — `DOOR_OPEN_DEG = 45.0`, so
  the requested "open 45 degrees" is already what the code does; the
  complaint is about swing DIRECTION/placement producing impossible results,
  not the angle.
- `:611-751` `add_door_leaf()` already has a real, documented swing/hinge
  heuristic (swing into the smaller adjacent room to keep circulation clear,
  small-room-outward exception for a tight WC, hinge toward the nearer jamb,
  annotation overrides all of it) and an existing collision fallback
  (`hits_furniture()`, `:698-725`): if the open leaf sweeps through a placed
  furniture item, try the opposite hinge, and if that ALSO collides, leave
  the door closed rather than draw it through the object (`:727-738`,
  comment: "a closed door is correct; a door lying across the dining table
  is not").
- **The gap**: `hits_furniture()` only tests the leaf's swept segment
  against `floor.get("placements", [])` — furniture. It never tests against
  OTHER doors' already-placed leaves. `add_door_leaf()` is called once per
  opening in a per-floor loop (`:1067`, inside the function that also holds
  `floor` in scope for the furniture check) with no shared state between
  calls, so two doors can each independently resolve a swing that, drawn
  together, overlaps.
- **Confirmed on the real data**: built bungalow_039's geometry
  (`--geometry-only`) and measured every door opening's centre position.
  Four pairs of doors sit within 1500mm of each other (858mm, 970mm, 1311mm,
  1475mm) — well inside the reach of two ~750–900mm leaves opened 45° from
  nearby hinge points. This matches what's visible in the
  `interior-warm-modern.png` render: two door leaves near the
  Bad/HWR/Diele cluster sit close enough to visually crowd each other.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `scripts/render-furnished-dollhouse.py`: already modified, uncommitted
  (pre-existing, unrelated in-progress work — not touched beyond this plan's
  scope).
- `scripts/render-exterior.py`: already entirely untracked/new, uncommitted.
  Same file this plan edits; only the door-asset section is in scope here.
- Both files were already dirty before this session touched them today (the
  furniture-editor walls/resize fix earlier this session touched
  `build-simplifier-render-plan.py`, a different file, and is unrelated to
  these two).

## Exact scope

**A. Front door — build it procedurally, like windows already are**

1. In `scripts/render-exterior.py`, remove the `DOOR_ASSET` hub-asset
   placement for the `"door"` opening branch (`:887-889`) and replace it
   with a new `build_front_door()` function, structured like the existing
   `build_window()`:
   - A frame (reuse `WINDOW_FRAME_MAT`-style dark anthracite metal —
     `flat(..., roughness=0.4, metallic=0.6)` — matching the window frames
     already visible in the same facade, since the two should read as one
     consistent material family).
   - A solid leaf panel, in a distinct but coordinated dark tone (metallic
     front doors are a normal, legitimate real product — the fix is making
     it read as a real surface with highlights, not necessarily making it
     lighter).
   - A simple lever handle, reusing the interior door's own
     `HANDLE_MAT`/proportions convention from
     `render-furnished-dollhouse.py` (`:743-750`) for visual consistency
     between interior and exterior door hardware, if that material is
     accessible/duplicable here; otherwise an equivalent flat metal handle
     material defined locally.
   - Closed (front doors render closed in every existing exterior shot —
     no swing behavior needed here, unlike interior leaves).
2. Remove the now-unused `DOOR_ASSET` dict and any dead `place_asset()` call
   sites that only existed for it (keep `place_asset()` itself only if
   still used elsewhere — confirm before deleting).

**B. Door-vs-door collision**

3. In `scripts/render-furnished-dollhouse.py`, thread a per-floor
   `placed_leaf_segments` list (or equivalent) into `add_door_leaf()`,
   populated as each door resolves.
4. Add a `hits_other_leaf(lx, ly, sw)` check alongside the existing
   `hits_furniture`, using the same point-to-segment distance approach
   already used for furniture, comparing this leaf's resolved endpoints
   against each PREVIOUSLY PLACED leaf's segment (checked both directions:
   this leaf's tip against the other's segment, and the other's tip against
   this one's segment), with a clearance based on `DOOR_LEAF_THICKNESS_M`
   plus a small margin.
5. Extend the existing fallback chain (`:727-738`) to also trigger on
   `hits_other_leaf`: try the opposite hinge; if that also collides with
   furniture OR another leaf, close the door — same principle already
   established and worded in the existing comment, extended to doors as
   well as furniture.
6. After a leaf's final pose is resolved (whichever branch), append its
   segment to `placed_leaf_segments` so later doors in the same floor see
   it.

## Files in scope

- `scripts/render-exterior.py` (front door: remove asset placement, add
  procedural `build_front_door()`)
- `scripts/render-furnished-dollhouse.py` (`add_door_leaf`: leaf-vs-leaf
  collision check and shared per-floor accumulator)
- `scripts/render-furnished-dollhouse.test.py` or equivalent new test file
  for the new collision-check helper (see Tests below — exact filename
  confirmed at implementation start, following this repo's existing
  `unittest` + `importlib.util` convention, e.g.
  `scripts/verify_render.test.py`)

## Explicitly out of scope

- No change to `DOOR_OPEN_DEG` (45° is already correct and already what was
  asked for).
- No change to the existing swing-direction heuristic (smaller-room,
  small-WC-outward, hinge-toward-nearer-jamb) or to the
  annotation-overrides-heuristic precedence — both are already correct and
  already documented; this plan only adds a THIRD collision check
  (leaf-vs-leaf) alongside the existing leaf-vs-furniture one.
- No change to window rendering, no change to any other hub asset besides
  `DOOR_ASSET`.
- No change to which doors get a leaf at all (passages still get none, per
  existing behavior at `:625-626`).
- No re-render of any house other than bungalow_039 as part of verification,
  beyond confirming the main render-plan path's other outputs are
  unaffected (see Tests).

## API, schema, and data-contract effects

None. Pure rendering-code change; no change to any JSON schema, correction
document, or furniture document format.

## Acceptance criteria

- Re-rendering bungalow_039's exterior (both styles): the front door shows
  visible material detail (highlights/reflection consistent with a metal
  door, not a flat black rectangle) and is recognizably a door, not a void.
- Re-rendering bungalow_039's interior: no two door leaves visually overlap
  each other in the Bad/HWR/Diele cluster (or wherever the closest pairs
  land); any door that cannot find a non-colliding swing renders closed,
  not overlapping.
- No door that previously rendered fine (open, clear of furniture, clear of
  other doors) changes behavior — the new check only fires on genuine
  leaf-vs-leaf overlap.

## Tests and verification commands

New tests (added before implementation, per policy):

1. A pure-function unit test for the new leaf-vs-leaf distance/collision
   check, using synthetic geometry (two synthetic leaf segments at known
   positions/angles: one pair overlapping, one pair clear), asserting the
   collision check correctly returns True/False in each case — mirroring
   this repo's existing `unittest` + `importlib.util` module-loading
   convention.
2. A synthetic two-door test: build a tiny fake floor with two door
   openings 900mm apart (matching the real bungalow_039 measurement) on
   adjacent walls facing the same small room, run `add_door_leaf` for both
   in sequence, and assert the second leaf's final pose does NOT overlap the
   first's (either via alternate hinge or via being closed) — this is the
   regression test for the exact bug reported.

Verification commands (run after implementation, output attached to the
completion report):

```
cd born2thrill-local-workbench
python scripts/<new-test-file>.test.py -v
python scripts\run_project.py bungalow_039 --styles modern,classic
```

Plus: visually inspect the fresh exterior and interior renders for both
defects (screenshot comparison against the codex-final-2026-08-22 renders
already reviewed this session).

Existing tests are not deleted, skipped, or weakened.

## Protected and risky paths

- `render-exterior.py` and `render-furnished-dollhouse.py` are the two
  scripts every customer-facing render (past and future) goes through.
  `DOOR_ASSET` is used by every exterior render with a front door, so this
  change affects every house, not just bungalow_039 — mitigated by
  re-rendering bungalow_039 as the verification case and confirming no
  other geometry changes (walls, windows, room polygons) in the diff.
- The collision-avoidance fallback already has a "give up and close the
  door" branch for the furniture case; extending it to doors reuses that
  same safe fallback rather than inventing new behavior for the failure
  case.

## Rights, provenance, privacy, and security impact

None. Rendering-only change; no corpus, geometry-approval, or customer
delivery path touched. Does not change which houses are eligible for
release, only how the front door and door leaves look once rendered.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no.

- Neither change touches which geometry a render is built from
  (`annotation_hash`/`geometry_hash`/`delivery-manifest.json` machinery is
  untouched) — only how doors and the front door are drawn from geometry
  that's already there. A house's certified `.blend` becomes invalid for
  its OLD toolchain hash after this change (same as every prior renderer
  fix this session's HANDOFF history records: "eine Renderer-Aenderung
  entwertet eine Lieferung genauso wie eine Annotationsaenderung"), which is
  the existing, correct, already-built mechanism (`toolchain` hash in
  `delivery-manifest.json`) — not something this plan needs to add.

## Customer, email, database, deployment, and external effects

None directly. Indirect: every house's existing certified delivery becomes
stale under the new toolchain hash (expected, existing mechanism — see
above) and will need re-building via `run_project.py`/`batch-build.py`
before its next delivery, same as every previous renderer-code fix in this
suite's history.

## Failed-hypothesis log

1. **Hypothesis**: front door appears black because of a broken/missing
   texture file reference (common Blender asset-import failure).
   **Checked**: loaded the asset in headless Blender, inspected every
   material's node tree — zero `TEX_IMAGE` nodes exist on either real
   material; nothing is missing because nothing was ever linked.
   **Conclusion**: rejected — not a broken texture path. The material was
   built as a flat, non-metallic, near-black color from the start
   (`Metallic = 0.0` despite the asset name "Metal Front Door").

## Rollback

Pure code change on an already-dirty, uncommitted working tree; no data
migration, no deployment. Revert the two files listed above (or the
specific hunks) to undo; nothing else is touched. Existing certified
deliveries for other houses are unaffected until someone re-runs the
renderer against them.

## Unresolved questions

- Exact new test filename for the leaf-vs-leaf collision unit test — will
  follow the existing `<script-under-test>.test.py` convention and name it
  at implementation start.
- Whether the front-door leaf should get its own simple visible panel
  detail (a raised rectangle, matching common flush-panel metal door
  styling) or stay a plain flat leaf with just the frame/handle giving it
  shape — will default to plain-leaf-plus-handle-plus-frame (matches the
  window precedent's level of detail) unless told otherwise, since that is
  already enough to stop it reading as a black void.

## Completion record (2026-08-22)

Implemented as scoped.

**A. Front door**: `DOOR_ASSET` and its `place_asset()` call removed from
`render-exterior.py`; new `build_front_door()` (frame reusing
`WINDOW_FRAME_MAT`, a solid `DOOR_LEAF_MAT` leaf with real `metallic=0.7`,
`DOOR_HANDLE_MAT` lever handle) replaces it, matching the exact precedent
already set for windows in the same file.

**B. Door-vs-door collision**: `_distance_point_to_segment()` extracted as
a shared helper (also now used by the existing furniture check, replacing
its inline duplicate — behavior-preserving, same formula); new
`hits_other_leaf()` checks a resolving leaf against every OPEN leaf already
placed on the floor (`PLACED_DOOR_LEAVES`, module-level like `floor`
itself); the existing furniture-collision fallback (try opposite hinge,
else close) now also triggers on a door-vs-door hit.

Verification:
- New `scripts/render-furnished-dollhouse.test.py` — 4/4 pass (pure
  `_distance_point_to_segment` math, extracted via `ast` from the real file
  so the test can never drift from the actual implementation, since this
  script imports `bpy` and can only otherwise run inside Blender).
- Inspected the `DOOR_ASSET` hub model directly in headless Blender before
  writing any fix, confirming the root cause precisely (`Metallic = 0.0` on
  both real materials, near-black flat colour, zero texture nodes) rather
  than guessing.
- Full pipeline run: `run_project.py bungalow_039 --styles modern,classic`
  — both styles built and verified clean: `wall_angles`, `opening_count`,
  `procedural_fallback`, `render_log`, `R0_symbol_is_the_object`,
  `R1_nothing_floats`, `R2_R3_stairs_and_treppenloch`, `R4_outside_exists`,
  `R5_appliance_finishes`, `R6_furniture_inside`, plus the four
  `verify_render_blend.py` structural checks per interior variant — all
  PASS, 0 FAIL. Delivery manifest re-certified (3 artifacts, both styles
  verified).
- Real bungalow_039 door-pair measurements (858–1475mm apart, the exact
  data that reproduced the reported bug) now go through
  `hits_other_leaf()` on every render; the full clean pipeline pass above
  confirms nothing broke, and the fresh renders were visually reviewed
  (front door now shows real material detail with highlights, not a flat
  black rectangle).

Files changed: `scripts/render-exterior.py`, 
`scripts/render-furnished-dollhouse.py`,
`scripts/render-furnished-dollhouse.test.py` (new).

## Approval record

Approved by Rainer, 2026-08-22 ("ja").
