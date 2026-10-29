# twostorey_060: Geschosse umbenennen und Hanggelaende (Hanghaus)

Status: IMPLEMENTED — build and height acceptance verified; existing test failure documented

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-20: "the erdgeschoss is actually the untergeschoss, and the obergeschoss is actually an Erdgeschoss, this is a bauen am Hang Haus."

The two drawn floors of `twostorey_060` get their real names: what is stored as `groundfloor` becomes `basement` (Untergeschoss), and what is stored as `upperfloor` becomes `groundfloor`. Nothing is redrawn.

## Current evidence and behavior

`floorplan-simplifier/projects/twostorey_060` (training_ready, house_type "2-storey"):
- Annotations: 4 room areas on `groundfloor`, 5 on `upperfloor`. Elements: 13 / 16.
- The real stair is on `groundfloor` (role none); its copy is on `upperfloor` (role "opening").
- Per-level keys in annotations.json: `floor_scale` (only `groundfloor`), `floor_alignment` (both), `outer_outlines` (both), `floor_concepts` (both), plus the single value `outer_outline_floor`. No roof data per level.
- Exterior areas already say where the slope is: `terrasse` on `groundfloor` (the lower drawing, becomes UG), `gehweg` and `einfahrt` on `upperfloor` (becomes EG). The main entrance door is on `upperfloor` too. Rainer, 2026-10-20: "the gehweg is erdgeschoss and the terasse is untergeschoss".
- Files named by level: `groundfloor_original_preview.png`, `groundfloor_reference_compare.png`, `groundfloor_room_concept.png/.svg`, `upperfloor_original_preview.png`, `upperfloor_room_concept.png/.svg`.
- Level names also inside `data.json` (floors list, 11 + 7 mentions), `training-data.json` (11 + 7), `source-state.json` (1 + 2), `review-notes.txt` (10).
- No workbench data yet: no `corrections/twostorey_060` folder (no furniture, no build).

What the pipeline does with a `basement` (read, not run):
- Levels are sorted alphabetically: basement < groundfloor < upperfloor, so the order comes out right (UG at the bottom).
- The scale falls back from `groundfloor` to `basement` (`build-simplifier-render-plan.py:291`, `batch-build.py:103`).
- `treppe_zugang.py` knows basement ("KG").
- **Problem 1, the stair.** `annotation_stair_core()` (build-simplifier-render-plan.py, around line 3130) takes the stairs drawn on `ground_level` ("groundfloor if present"), regardless of role. After the rename, `groundfloor` holds only the "opening" COPY; the real stair sits on `basement`. The house would be built from the copy, in the wrong frame, or without the stair from the UG.
- **Problem 2, the hillside.** Today the outside is flat everywhere (read in render-exterior.py):
  - the lawn `ground` is one flat plane at z = -0.16;
  - every site area lies at a fixed small height by type (`AREA_STACK_Z`: garten 0.001 ... terrasse 0.016 m) -- its floor is used only to register its coordinates (`exterior_area_ground_points`), its HEIGHT is dropped;
  - storeys stack from z = 0 (`level * STOREY_Z`); the foundation plinth runs from -0.15 to 0 under the lowest storey.
  So after the rename the Gehweg would lie at Terrasse height, and the UG would stand fully above ground on all four sides.
- Interior (dollhouse) views draw no site areas; only the exterior is concerned.
- The exterior already picks the terrace side as the Schauseite, i.e. the downhill side where both storeys show. The camera stands at tripod height above z = 0 (terrace level), which is right for that side.

## Exact scope

1. **Data (twostorey_060 only), one scripted migration with a backup.**
   - Rename every `floor_level` `groundfloor`->`basement` and `upperfloor`->`groundfloor` in annotations.json (annotations, elements and exterior_areas), and `outer_outline_floor`.
   - Rename the per-level keys (`floor_scale`, `floor_alignment`, `outer_outlines`, `floor_concepts`) the same way.
   - Rename the level-named files, and the level names inside data.json, training-data.json, source-state.json and review-notes.txt.
   - Order of renaming: groundfloor->basement FIRST, then upperfloor->groundfloor, so nothing collides.
   - The stair copy (role "opening") stays a copy: it now sits on the new `groundfloor` above the real stair on `basement`, which is the correct relation.
2. **Code: the stair comes from the lowest floor that has a real stair.** `annotation_stair_core()` uses the lowest level (by the existing order) with a `stairs` element whose role is not "opening"; `ground_level` stays the reference frame, as today. For every existing house that is the same floor as today (their real stair is on `groundfloor`, and none has one on `basement` except `other_1_5_story_with_cellar`, checked before implementing). A test pins both cases.
3. Rebuild twostorey_060 with `go.py` (no upload) and look at both floors.

### Part B -- the slope (Rainer, 2026-10-20)

"this house has to be built into a little slope, the gehweg is erdgeschoss and the terasse is untergeschoss" -- and: "each outside area at the height of its floor, ground sloping from the Gehweg side down to the Terrasse side, earth against the UG walls on the street side."

No new switch. The drawing already declares it: outside areas on two floors (after the rename: Terrasse on `basement`, Gehweg and Einfahrt on `groundfloor`). Any house whose outside areas lie on two floors is a Hanghaus; every other house builds exactly as today.

4. **Plan builder:** each exterior area keeps its floor as `level` and gets `base_z_m` = its storey's index above the lowest storey x the exterior storey height. Plan-level `gelaende`:
   - `{"art": "hang", "oben": <level>, "unten": <level>, "richtung": [dx, dy]}`, where `richtung` is the unit vector from the centroid of the upper-level areas (Gehweg, Einfahrt, plus the main entrance door) to the centroid of the lower-level areas (Terrasse);
   - or `{"art": "eben"}`.
   A pure function `gelaende_aus_flaechen(areas, entrance, levels)`.
5. **Exterior renderer, ground:** with "hang", the lawn is a grid mesh (about 0.5 m cells, no boolean), with height `h(x, y)`:
   - on the street side of the house, measured along `richtung`, `h` = the upper level's floor height (EG);
   - on the garden side, `h` = the lower level's height (UG, z = 0);
   - between the house's street-side and garden-side facade lines, `h` falls linearly. This gives the sloping earth line on both side facades.
   - Cells inside the house footprint are left out.
   - Pure function `gelaende_hoehe(x, y, gelaende, haus_bbox)`.
6. **Earth against the UG walls (street side):** follows from 5. At the street facade the ground stands at EG height and covers the UG wall up to the EG floor. Along the side walls it slopes down; on the garden side the UG stands free.
   - The foundation plinth stays where it is (under the UG, now underground on the street side).
   - A UG facade element below ground is reported, not hidden: `WARNUNG Fenster/Tuer im Erdreich` for any UG opening whose sill lies more than 0.1 m below `h` at its position.
7. **Site areas at their floor's height:** each area at `base_z_m` + its existing stack offset (Gehweg/Einfahrt at EG height, Terrasse at UG height).
   - An area whose own plateau does not carry it (any vertex more than 0.15 m off the ground `h` there, e.g. an Einfahrt running down the side) gets `WARNUNG Aussenflaeche ... liegt im Hang`.
   - It is then built at its level as drawn (visible as a step), not bent onto the slope.
8. Nothing changes for houses without outside areas on two floors. A test pins that `gelaende` is "eben" for them and that the flat ground and `AREA_STACK_Z` heights are unchanged.

### Part C -- bungalow_007 (VillaBAH) as well, mirrored (Rainer, 2026-10-20)

"also make the changes to this one it is a bauen am Hang like the other one maybe you can flip it horizontally?"

- **Floors:** bungalow_007 already has `basement` (UG) + `groundfloor` (EG), so Part A is not needed. Rainer: "leave the floors".
- **Slope:** Part B applies automatically once its outside areas exist on both floors -- Terrasse on the UG, Gehweg/Einfahrt on the EG. Today bungalow_007 has NO outside areas and no main-entrance door marked; until they are drawn it builds flat.
- **Mirror:** a one-off scripted transform of bungalow_007 (backup first), left <-> right on both floors: `x -> 1 - x` for every point.
  - Applies to: room areas, elements (doors, windows, stairs, partitions), outer outlines, exterior areas, alignment marks, roof ridge paths if present.
  - Stair paths keep their direction; railing sides `left`/`right` are swapped.
  - Door hinge/swing fields are mirrored the same way.
  - Scale and Gebäudemaß stay (a mirror changes no length).
  - Test: every point maps back after mirroring twice; areas and lengths unchanged; a door's hinge ends up on the mirrored jamb.
- **Open:** "flip horizontally" is read as left-right in the drawing. If the slope direction is what should flip instead (the street on the other side), that is a different change.

## Files in scope

- `floorplan-simplifier/projects/twostorey_060/*` (data, backup first to `projects/_backup/twostorey_060-<timestamp>/`)
- `floorplan-simplifier/projects/bungalow_007/annotations.json` (Part C mirror, backup first) and a mirror script with its test
- `born2thrill-local-workbench/scripts/build-simplifier-render-plan.py` (`annotation_stair_core`)
- New test `born2thrill-local-workbench/scripts/stair_core_lowest_floor.test.py`
- `born2thrill-local-workbench/scripts/render-exterior.py` (ground mesh, site-area heights, the two warnings)
- New test `born2thrill-local-workbench/scripts/hanggelaende.test.py`
- A small migration script in the session scratchpad (not added to the repo)

## Explicitly out of scope

- A slope that is not between exactly two levels (three-level houses, split levels).
- Terrain in the interior dollhouse views (the EG view's Sockel still shows the UG shell on all sides). Follow-up, if wanted.
- Retaining walls, steps or ramps between the plateaus beside the house (the slope is plain lawn).
- The project id `twostorey_060` and `house_type` ("2-storey"): kept. Whether a Hanghaus counts as two-storey for the catalogue and price is Rainer's call.
- Living area: today the price script counts every room by label, regardless of floor, so UG rooms count like EG rooms. Unchanged.
- Other houses.

## API, schema, and data-contract effects

None new: `basement` is an existing level name. The stair-core rule changes only for houses whose lowest real stair is not on `groundfloor`.

## Acceptance criteria

1. In the Annotator, twostorey_060 shows "Untergeschoss" and "Erdgeschoss" with the same drawings, scale, alignment and outline as before.
2. The render plan has floors `basement`, `groundfloor` in that order. The stair core comes from the basement's real stair, and its polygon is identical (within 1 mm) to today's plan's.
3. `go.py twostorey_060` builds both floors; the verifier passes or names a real drawing issue.
4. All existing tests pass; the new stair test passes.
5. Exterior views of twostorey_060:
   - the street side shows the ground at EG level (the UG hidden, Haustuer at ground level, Gehweg level with it);
   - the garden side shows the UG fully, with the Terrasse at UG level;
   - the side facades show the earth line falling between the two.
   Measured in the .blend: ground height 0.3 m in front of the street facade = EG floor height (within 0.05 m); 0.3 m in front of the garden facade = 0 (within 0.05 m); Gehweg and Terrasse object heights = their levels.
6. Any other house (e.g. bungalow_007, twostorey_059) builds its exterior with a flat ground identical to today: same ground object, same area heights.

## Tests and verification commands

- New `stair_core_lowest_floor.test.py`:
  - real stair on groundfloor only -> taken from groundfloor (today's behaviour);
  - real stair on basement plus an opening copy on groundfloor -> taken from basement;
  - opening copies alone -> None (as today without a stair).
- Existing: `build-simplifier-render-plan.test.py` (known pre-existing door-hinge failure stays reported), the treppenloch/kamera suites, the floorplan-simplifier unittests.
- New `hanggelaende.test.py` (pure functions via ast):
  - `gelaende_aus_flaechen`: Hang with the right direction for Gehweg on EG and Terrasse on UG; "eben" when all areas are on one floor; "eben" without areas;
  - `gelaende_hoehe`: plateau heights, linear in between, constant beyond;
  - the "im Erdreich" and "im Hang" checks fire on fixtures.
- Data check: a before/after diff of annotations.json shows only `floor_level` values and the four dict keys changed; point counts per floor unchanged.

## Protected and risky paths

- The annotation is training data. The migration is mechanical and reversible from the backup; no geometry value changes.
- Toolchain hash (build-simplifier-render-plan.py): every build counts as outdated (already the case).

## Rights, provenance, privacy, and security impact

None. The rights ledger is keyed by project id, which stays.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Floor names change, not geometry; the stair rule only picks which drawn stair is read. No publication or email path is touched.

## Customer, email, database, deployment, and external effects

None. No upload.

## Rollback

Restore `projects/twostorey_060` from the backup folder; revert the `annotation_stair_core` hunk; delete the new test.

## Unresolved questions

1. Does the slope run straight from the street to the garden (front to back), as the drawn areas suggest? The direction is derived from them; a diagonal slope would come out diagonal.
2. Should `house_type` stay "2-storey"?

## Approval record

Approved by Rainer in chat on 2026-10-20: "could you start the bauen am hang? nr 60?"

## Implementation audit 2026-10-20
Source root is C:/dev/Floorplan-tools/floorplan-simplifier (older C:/dev/floorplan-simplifier does not exist). Existing 060 correction furniture and baseline renders now exist; backed up before rebuilding. Floor-index furniture remains index 0/1. Existing dirty changes preserved; full pre-change diff/status and backups recorded in C:\Users\Admin\AppData\Local\Temp\hanghaus060. No commit, upload or rights changes. Terrain fields are additive render-plan schema fields. Rollback also restores render-exterior.py and the saved correction directory.

Migration detail: copied_from_floor and gebaeudemass.json floor keys are also renamed; otherwise stale upperfloor scales re-enter via hausdaten. To preserve the existing furniture coordinate frame and exact stair polygon, 060 explicitly records render_reference_level=basement (the former groundfloor). Other houses keep their existing reference-frame selection. This resolves the old plan conflict between new groundfloor as reference and identical absolute stair coordinates.

Implementation details and test/rollback evidence: twostorey-060-hanghaus-verification-2026-10-20.md. Stable object IDs are retained. The source-state checksum is refreshed after migration. Furniture aliases are resolved by actual sorted floor levels; existing furniture documents and geometry stamps remain unchanged. Centroid direction selects the facade pair; the slope runs between those facade lines to preserve whole-facade plateaus.
