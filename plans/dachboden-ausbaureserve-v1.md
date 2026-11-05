# Bungalow with an unfinished attic (Ausbaureserve): roof slopes, no second storey

Status: DONE 2026-10-23

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-23, bungalow_generationat: "this one doesn't have a 2 geschoss but just an attic with dachschraegen no walls as ausbaureserve".

The source attic plan shows one open "Dachbodenflaeche ca. 99 m2". The roof slopes start at the eaves (no knee wall). There are two gable walls, west and east, with one window each, and a stair marked "vorbereitet". It is labelled "optionaler Ausbauvorschlag".

## Current evidence

- `floorplan-simplifier/projects/bungalow_generationat`: data.json `house_type: "bungalow"`. annotations: groundfloor has 8 rooms, 7 windows, 5 doors, 3 openings and 1 stair. A level `attic` has `luftraum` + `abstell`, 2 windows and 1 stair. floor_scale exists only for groundfloor. No roof type is set (no gebaeudemass.json), and it has never been built.
- `build-simplifier-render-plan.py` builds every annotated level as a storey (~3770 `levels = sorted(...)`). An `attic` level would become a full storey with walls, or stop on "attic has no calibrated scale" (~3806). There is an inheritance rule for upperfloor only (~436).
- `render-exterior.py` has a steep gable-roof path for 1,5-storey houses (`anderthalb.NEIGUNG_GRAD = 40`, `KNIESTOCK_M = 1.0`, ~1285-1330). It has no case "roof directly on the ground floor, with gable windows".

## Exact scope

1. **Level `attic` = Dachboden, not a storey.** The plan builder does not build walls, rooms or a dollhouse floor for it. The attic level takes the groundfloor scale (like upperfloor today). Its windows go into the plan as **gable windows** (`giebelfenster`), with position and size from the attic drawing.
2. **Exterior:** the ground-floor walls carry a steep Satteldach directly at the eaves: pitch 40 deg (same as 1,5-storey), knee wall 0. The ridge runs along the long axis, unless `roof_axis_override` is set. The gable windows sit in the gable triangles at attic floor height.
3. **Roof variants (default, Rainer may change):** modern and classic both get this Satteldach. A Flach/Pult/Walm picture would hide the attic, so none is made. Delivery = 2 exteriors + 4 interior styles. Recorded via gebaeudemass.json `roof_type_modern/classic = "satteldach"` plus a new flag `dachboden: true`.
4. **Stair (default, Rainer may change):** built in the ground floor as drawn, with its opening into the attic and a railing. The attic itself stays unbuilt in the dollhouse (cut plane as for a bungalow).
5. A house without an `attic` level is unchanged.

## Out of scope

- An interior picture of the attic; Ausbau variants; changes to price or living area (the attic does not count as living area).

## Tests (first)

- build-simplifier-render-plan: with a synthetic project that has groundfloor + attic, the plan has ONE floor, `dachboden: true`, the attic's windows in `giebelfenster` (scaled with the groundfloor scale), and no walls or rooms from `luftraum`/`abstell`.
- The same project without attic: identical plan to today.
- render-exterior (pure helpers): roof eave height = groundfloor wall top, pitch 40 deg, and gable windows placed in the gable triangle below the roof line.
- Existing tests unchanged.

Real check: build bungalow_generationat (no upload). Exterior: steep gable roof on the ground floor, two gable windows, no knee wall. Dollhouse: ground floor with stair. Nothing uploaded.

## Safety gate

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. Local build only; the roof is derived from the drawn ground floor and the drawn attic windows. Nothing is guessed beyond the stated 40 deg default.

## Rollback

`.before-dachboden` backups of the touched scripts; remove the new tests; delete the `dachboden` flag.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement dachboden-ausbaureserve-v1 with the defaults (Satteldach both styles, stair built), tests first, build bungalow_generationat (no upload)."

## Implementation record (2026-10-23)

- New `scripts/dachboden.py` (pure functions):
  - `abspalten(annotations)` moves level `attic` out of annotations/elements into `_dachboden` and sets roof_type_modern/classic = satteldach with herkunft "dachboden";
  - `fenster_mass()` follows the same sill/height rule as the ground floor;
  - `fenster_hoehe()` clips a gable window under the 40 deg slope (0.25 m margin; None below 0.5 m).
- build-simplifier-render-plan.py:
  - `load_annotations()` calls `dachboden.abspalten` LAST, after the scale inheritance;
  - new `dachboden_plan()` maps the gable windows via `frame_for_level` (alignment marks) to mm;
  - the plan carries `"dachboden": {giebelfenster, neigung_grad}`;
  - this also fixes the stair-core trap: "attic" sorted before "groundfloor".
- render-exterior.py, only for `plan.dachboden` + satteldach + not 1,5-storey:
  - the Satteldach default pitch is 40 deg (a drawn profile still wins);
  - after the roof, each gable window goes to the nearest ground-floor exterior wall at wall-top height. It is cut into the right loose part of `roof-walls` (a cut of the joined mesh deleted the west gable, so the mesh is split first, `_db_lose_teile`, then rejoined), then `build_window`;
  - the camera frames up to the real roof top.
- run_project.py `roof_types_for_plan`: a Dachboden plan returns ("satteldach",).
- Deviations from the draft:
  - **1** exterior instead of 2. One exterior picture is made per exterior .blend, and both styles use the identical Satteldach model.
  - No `dachboden` flag in gebaeudemass.json: it is derived from the drawn `attic` level.
- Tests first: scripts/dachboden.test.py, 13 cases, all red before and green after. All workbench Python suites OK, except the known red bungalow_039 door test.
- Live, bungalow_generationat built (exit 0, 2 artifacts certified, all verify checks PASS incl. stair/railing, no upload):
  - exterior: steep Satteldach on the ground floor, gable windows west (wall-8, 1.32 x 2.10 m) and east (wall-6, 1.09 x 2.10 m), whole house in frame;
  - interior: ground floor with stair and railing. No furniture yet: the Möbel step is not done.

## Nachtrag 2026-10-23 (go.py)

- Rainer's own go.py build failed: `storeys()` counted the `attic` level as a storey. It built with --floors 0,1, rendered a non-existent "upper" interior and expected 3 .blend ("the rule says 3"). The same run also hit a stale-plan refusal: the roof sidecar was written (20:17:10) while the build ran.
- Fix: `dachboden.geschoss_ebenen()` drops `attic` when another level exists; `go.py storeys()` uses it. Tests first: dachboden.test.py +3 (red before, 16/16 after). All Python suites as before (only the known bungalow_039 door test red).
- `python scripts/go.py bungalow_generationat` (no --hochladen): "fertig", 2/2 .blend certified. Codex job written: 1 exterior + 4 styles = 5 pictures, into codex-bungalow_generationat-2026-10-23.
