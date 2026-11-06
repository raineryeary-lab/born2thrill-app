# Hanghaus twostorey_060 — implementation and verification

Approved in chat by Rainer on 2026-10-20. No commits, uploads, rights approvals or email changes.

## Changes
- Source package backed up, then groundfloor -> basement, upperfloor -> groundfloor. Referenced preview/concept filenames, JSON level keys and sidecar scale migrated. Stable object IDs preserved.
- source-state annotation checksum refreshed from the actual migrated JSON; stale-plan guards unchanged.
- Explicit render_reference_level=basement preserves the original reference image, coordinate frame, room polygons, exact stair polygon, furniture placements and original furniture identity hashes. Furniture files untouched.
- Lowest real staircase (role != opening), with registration to the retained frame; indexed furniture aliases now resolve against actual ordered floors.
- Exterior area level/base_z_m and plan gelaende metadata. Two plateaus, lawn grid about 0.5 m with footprint cells excluded, no boolean.
- Area centroids plus EG exterior door select the opposing facade pair. Slope follows those facade lines, rather than a diagonal across a facade caused by the offset driveway. Axis-aligned rectangular footprint verified for this house; generalized oblique facades are not certified.
- UG openings >0.1 m below terrain and areas >0.15 m from terrain emit warnings.

## Tests
- Added tests FIRST: stair_core_lowest_floor.test.py (4 pass), hanggelaende.test.py (8 pass).
- Exterior registration: 13 pass.
- Existing stair wall/access, 3 treppenloch suites, camera stamp and floor overhang suites: all pass.
- Simplifier unittest suite: 312 pass. Furniture persistence: 6 pass.
- Existing builder suite: 72 run, 1 failure, 4 skips. Failure is test_door_hinge_and_swing_are_normalized_into_the_walls_frame. Confirmed identical failure on saved PRE-CHANGE builder. Existing tests untouched.
- 060 pre/post room polygons, furniture placements and staircase polygon EXACTLY identical. Furniture stamps retain their original values.
- bungalow_007 and twostorey_059: exterior floor geometry/openings/site points identical, gelaende=eben, zero new site offsets, original flat renderer branch retained. No other source package migrated.
- The old plan assumption that no other house has a basement stair is false: bungalow_007 has one. The required lowest-real-stair rule selects it instead of its groundfloor copy; ~2.4 mm edge difference. Exterior renderer does not consume this core, so exterior unchanged. No rebuild of that house performed.

## Blender measurements
0.3 m outside street facade: 2.749992 m (target 2.75).
0.3 m outside garden facade: 0.000008 m (target 0).
Terrace: 0.016 m; path: 2.761 m; driveway: 2.756 m (existing finish stacking offsets retained).
All within +/-0.05 m.

## Remaining drawing warnings / follow-ups
Four UG openings are below the proposed terrain; one driveway area extends onto the slope. Kept as drawn, as requested. Next decision: review these drawing warnings. No retaining walls or ramps added.
Known generic STALE PLAN mass-file timing defect and go.py error-banner reporting remain outside scope. During this migration the stale source-state cache was refreshed as required; no generic guard was bypassed or changed.
Interior terrain/sockel presentation, >2-level slopes, retaining walls/ramps, catalogue house-type/pricing and UG living-area treatment remain separate follow-ups.

## Evidence and repository state
Workbench base: 5be1a4e18956b9fb2e158bee82aa159898356e89, branch agent/furnished-render-and-annotation-schema.
Simplifier base: 8a08d19a09928f04585ceaf553b9ff1440eca33b, branch agent/annotation-window-type-door-swing.
Both repositories already dirty. Full original status/diff and task-only diff snapshots are in the evidence folder below. Pre-existing edits preserved.

## Rollback
Restore the saved 060 project backup and correction directory. Restore ONLY this task's hunks in the two renderer/builder files from their saved before copies (preserving any subsequent edits), remove the two new tests, and retain audit documentation. No Git reset/clean is appropriate for these dirty repositories.

Source backup: C:\dev\Floorplan-tools\floorplan-simplifier\projects\_backup\twostorey_060-20261020-145055

Correction backup: C:\Users\Admin\AppData\Local\Temp\hanghaus060\correction-before

Evidence: C:\Users\Admin\AppData\Local\Temp\hanghaus060

Final build with preserved IDs: PASSED. go.py twostorey_060 built both floors; 2 styles verified, 0 excluded, 6 artifacts certified (4 exterior roof variants and 2 floor models). Log: C:\Users\Admin\AppData\Local\Temp\hanghaus060\go-verified.log

Final git status including untracked files recorded in *-status-after.txt. Repository-wide diff --check reports pre-existing whitespace in unrelated knowledge.json/export_generator_dataset.py; those files were not edited by this task.
