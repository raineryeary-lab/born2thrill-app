# 1,5-Geschosser: Kniestock, steiles Satteldach, Quergiebel / Ziergiebel

Status: IMPLEMENTED 2026-10-20 -- verified in scratch on onehalfstorey_044; not committed

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-20 (onehalfstorey_044): "that has to be 1,5 story so the satteldach has to drop down" -- "the other satteldächer are binderdächer they are ok but the 1,5 story we have to create with kniestock and quergiebel and stuff this is just for 1,5 story houses".

1,5-Geschosser get a real Dachgeschoss: low outside walls (Kniestock), a steep Satteldach whose eave sits just above the upper floor, and the drawn Quer-/Ziergiebel. Bungalows and Zweigeschosser keep the flat Binderdach exactly as today.

## Current evidence and behavior

- All 44 `onehalfstorey_*` projects store the top floor as `upperfloor` (data.json house_type "1.5-storey"). The exterior builds it like any storey:
  - `render-exterior.py`: `EAVE_Z = STOREY_Z * STOREY_COUNT`, full-height walls on every storey;
  - the Satteldach comes from `roof_profile.py` at the 5 degree default (Rainer 2026-09-19 for the Binderdach).
  - So a 1,5-Geschosser renders as a full two-storey house with a flat roof on top.
- There is no Kniestock/Drempel logic anywhere in the scripts.
- **Gables are already drawn but ignored:**
  - The Annotator's "Giebel 1/2" + "Ausrichtung" store `architectural_features: [{type: "gable", subtype: "ziergiebel" | "quergiebel", orientation: north/east/south/west, floor_level}]`.
  - 15 of the 44 houses carry them, for example quergiebel/west/groundfloor 3x, quergiebel/north/upperfloor 3x, ziergiebel/north/upperfloor 5x.
  - Neither the plan builder nor the renderer reads them.
  - Stored: type and side only. Not stored: width and position along the facade.
- onehalfstorey_044: one `ziergiebel`, north, upperfloor; no roof form chosen yet (`roof_type_modern/classic` null).

## Exact scope (proposal -- values marked [?] need Rainer)

1. **Who:** house_type "1.5-storey" (id prefix `onehalfstorey`). Everybody else unchanged.
2. **Kniestock:**
   - On the top storey the EAVE-side exterior walls stop at Kniestock height above the upper floor's slab top: [?] default 1.00 m.
   - The gable-side walls rise to the roof line (gable triangle).
   - `EAVE_Z` = top of the storey below + slab + Kniestock.
3. **Steep roof:** for 1,5-Geschosser the Satteldach (and Walmdach) pitch defaults to [?] 40 degrees, unless the Dach tab holds a profile for the house.
   - Ridge along the long axis, as today.
   - The 5 degree default stays for everyone else.
4. **Quergiebel** (cross gable): on the drawn side, a gable roof at right angles to the main ridge, same pitch, ridge below the main ridge. Its front wall rises full height through the eave line (Zwerchhaus).
   - Position: centred on that facade [?].
   - Width: [?] one third of the facade, at least 2.5 m.
5. **Ziergiebel:** a small decorative gable on the drawn side, sitting on the roof slope with no wall through the eave.
   - Width [?] 2.0 m, centred.
6. **Orientation:** north/east/south/west map to the drawing's top/right/bottom/left, as the Annotator shows them. Verify on one house against the plan image before building all.
7. **Interior dollhouse of the upper floor:**
   - outside walls cut at Kniestock height where the roof comes down;
   - the existing partition cut (1.25 m) unchanged.
   - [?] If wanted: slanted roof planes shown as a thin edge. Proposal: out of this plan.

## Explicitly out of scope

- Gauben (dormers), Krüppelwalm, Pultdach variants on 1,5-Geschosser.
- Changing the drawn data of the 44 houses; drawing missing gables (29 houses have none -- they get the steep roof without gables).
- Bungalows, Zweigeschosser, Hanghaus work.

## Files in scope

- `scripts/render-exterior.py` (eave/wall heights, pitch default, gables)
- `scripts/build-simplifier-render-plan.py` (pass `architectural_features` gables and the house type into the plan)
- `scripts/render-furnished-dollhouse.py` (upper-floor outer wall height for 1,5-Geschosser)
- new tests `scripts/anderthalbgeschosser.test.py`

## Acceptance criteria

1. On onehalfstorey_044 and one house with a Quergiebel (e.g. a quergiebel/west one), measured in the exterior .blend:
   - eave height = upper floor + Kniestock (±0.05 m);
   - roof pitch = the default;
   - a gable object exists on the drawn side, centred, with the set width.
2. A Zweigeschosser and a bungalow build byte-identical roofs and walls to today (same eave, same 5 degree profile).
3. Renders checked by eye: the 1,5-Geschosser read as Dachgeschoss houses.

## Tests and verification commands

- Pure functions, tested:
  - `ist_anderthalb(plan)`
  - `traufhoehe(storeys, kniestock)`
  - `giebel_aus_features(features, footprint)` (side, centre, width, ridge height)
  - pitch default selection
- Rebuild onehalfstorey_044 plus one Quergiebel house plus one Zweigeschosser (control); probe heights in the .blend.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Only the 3D massing of already annotated houses changes; no publication or approval path is touched.

## Customer, email, database, deployment, and external effects

None. No upload.

## Rollback

Revert the hunks; rebuild affected houses.

## Unresolved questions

1. Kniestock height (proposed 1.00 m).
2. Roof pitch for 1,5-Geschosser (proposed 40 degrees).
3. Quergiebel width and position (proposed: centred, a third of the facade, at least 2.5 m), or should Rainer draw it (e.g. two clicks on the facade in the Dach tab)?
4. Ziergiebel width (proposed 2.0 m).

## Approval record

Approved by Rainer in chat, 2026-10-20: "Approved with Kniestock 1.0 m, 40°, Quergiebel centred a third of the facade (min 2.5 m), Ziergiebel 2.0 m. Implement anderthalbgeschosser-dach-v1, tests first, start with onehalfstorey_044."

## Amendment A1 (2026-10-20) -- Variante A

Measured on onehalfstorey_044 before building: upstairs there are two 2.10 m balcony doors on the north eave side (where Rainer marked a Ziergiebel) and a window (top 2.25 m) on the south eave side. Under a 1.0 m Kniestock they would stick through the roof. Rainer chose **A**: wherever a door or window stands in the low eave wall, a Zwerchgiebel stands over it, as wide as needed (openings closer than 1 m share one; 0.5 m margin each side; at least 2.5 m). A marked gable on an eave side without openings stays as approved (Quergiebel: centred, a third; Ziergiebel: 2.0 m). Walmdach: every side is an eave side.

## Implementation record (2026-10-20)

- `scripts/anderthalb.py` (new, pure): `ist_anderthalb`, `traufhoehe`, `traufseiten`, `seite_von_wand`, `giebel` (A), `zwerch_masse`. Test `scripts/anderthalb.test.py`: 10 OK. Honest note: module and test were written in one go, so the test did not fail first.
- `build-simplifier-render-plan.py`: the plan carries `house_type` (data.json) and `giebel_merkmale` (the marked gables).
- `render-exterior.py` (1,5-Geschosser, Satteldach/Walmdach, rectangular upper floor only):
  - The upper-floor walls are built tall with all their openings, then cut to the roof surfaces after the roof is built.
  - The roof machinery's own gable walls (`roof-walls*`) are dropped: the tall wall IS the gable, with its windows.
  - The roof height is MEASURED at the wall line (ray cast) and the roof is lowered so the slab middle sits exactly 1.0 m above the upper floor.
  - Zwerchgiebel: a rebuilt pentagon front wall with its openings, two 0.16 m roof slabs, triangular side cheeks, and the main eave opened in front.
  - 40 degree default for Satteldach (only without a saved Dach-tab profile) and Walmdach.
  - Non-rectangular upper floors: WARNUNG, roof as before.
- `render-furnished-dollhouse.py`: upper floor of a 1,5-Geschosser, eave-side outer walls capped at 1.0 m, except the Zwerchgiebel spans (same `anderthalb.giebel` rule).

Fixes found while measuring (all in the record because they changed the approach):
1. **Missing Zwerch side walls** (dark triangles) -> side cheeks added.
2. **Walmdach destroyed the upper walls.** The west cut volume, after a boolean that subtracted the gable area from it, was broken: wall vertices 269 -> 66. Cut volumes are no longer boolean-edited; the Zwerch fronts are rebuilt instead.
3. **A 14 cm slot between wall top and roof.** The profile measures its pitch from the overhang edge. Now the slab is measured at the wall.
4. **The Kniestock came out at 1.28 m** -> the roof is lowered by the measured difference (0.279 m Satteldach, 0.293 m Walmdach). Log: "Dachplatte an der Wand 3.750 m = Kniestock 1.00 m" on every side.
5. **The Zwerch front tops sat flush with the slab top** -> the small roof slab is raised 0.08 m.

Verification (scratch, onehalfstorey_044, classic plan built from the live project):
- Satteldach: 2 Zwerchgiebel (north 4.64-7.88 over both balcony doors, south 1.58-4.08 over the window); main ridge 7.77 m.
- Walmdach: 4 Zwerchgiebel (openings on all four upper sides).
- Probe:
  - wall points above 3 m with no roof above them: only the Zwerch front top edges (8 / 24 points), which touch their slab;
  - wall tops sit inside the roof slab (distance to slab top 0.13-0.14 m).
- Renders checked by eye.
- Interior upper floor: 4 outer walls capped, the 2 Zwerch spans kept (render checked).
- Control twostorey_059 exterior (Satteldach), old vs new code: 112 objects, all identical except the imported front-door model. That differs the same way between two runs of the OLD code (non-deterministic import).
- Suites: all workbench suites OK, except the known pre-existing door-hinge failure in build-simplifier-render-plan.test.py.

Not done / limits:
- L-shaped upper floors (e.g. onehalfstorey_027): roof as before, with a WARNUNG.
- No dormers.
- The Zwerch ridge shows a light seam where the two slabs meet: no ridge cap.
- 35 of the 44 houses currently fail to build a plan at all (scale/alignment/furniture), independent of this change.
- The real `go.py` build of onehalfstorey_044 is not run here: it has no roof form chosen (`roof_type` null) and the classic plan is unbuilt.
