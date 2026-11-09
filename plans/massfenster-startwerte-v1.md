# Maßstab-Fenster: startet mit den heutigen Maßen statt 10 × 10

Status: DONE 2026-11-06

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-06: "the Massstab Gebäudemaße should reflect these guesses, it always shows 10 x 10 which is almost never correct".

## Current evidence

- `floorplan-simplifier/static/massstab-fenster.js` ~342/348: `#massBreite` and `#massHoehe` are created with `value="10"`; `oeffnen()` (~605) never sets them. So the window always opens at 10 × 10 (or the last typed value).
- The room m² in the editor already use a size: scale `floorScaleMetresPerUnit()` × ratio `fallbackAspectRatio()` (annotate.js ~57: aspect_by_floor, aspect, else concept-image ratio = a guess).
- `annotation_space` may carry stated `width_m` / `depth_m` (houses where sizes were entered).

## Exact scope

1. Pure `massStartwerte({ umriss, mProEinheit, breiteZuHoehe, angegeben })` in massstab-fenster.js (before `massFensterAnlegen`):
   - stated `width_m` + `depth_m` -> those, `geschaetzt: false`;
   - else scale known -> width = outline width × scale, depth = outline height × scale ÷ (width/height ratio), rounded to 0.01 m, `geschaetzt: true`;
   - else null -> fields stay as they are.
2. `oeffnen()` fills both fields from it before `neuRechnen()`.
3. When `geschaetzt`, the hint starts with "Schätzung aus dem heutigen Stand – bitte mit dem Beiblatt prüfen." The red "2 Maße fehlen" stays until Rainer presses Anwenden.
4. Cache version of massstab-fenster.js in annotate.html bumped.

## Out of scope

Applying anything automatically; nothing is saved by opening the window.

## Tests (first)

`static/massstab-startwerte.test.mjs` (same loading as massstab-fenster.test.mjs): stated sizes win; scale + ratio -> width/depth; no scale -> null; seam: `oeffnen()` calls `massStartwerte`.
Real: open bungalow_001 (red) -> window shows the same size the m² are based on, not 10 × 10; open a house with entered sizes -> shows those.

## Safety gate

Display only; geometry changes only on Rainer's Anwenden, as today.

## Rollback

`massstab-fenster.js.before-startwerte`, annotate.html cache version back; remove the test.

## Approval record

Rainer in chat, 2026-11-06: "Approved, build it".

## Implementation record (2026-11-06)

- `massStartwerte()` in massstab-fenster.js; `oeffnen()` fills width/depth from it (outline x `floorScaleMetresPerUnit()`, depth with `gezeichnetesVerhaeltnis()` -- the same ratio the room m2 use); hint "Schätzung aus dem heutigen Stand – bitte mit dem Beiblatt prüfen." until Rainer types; annotate.html massstab-fenster.js v=20261106-1.
- Tests first: static/massstab-startwerte.test.mjs 4 (red before, green after); massstab-fenster/-seitenverhaeltnis/-groesse-halten/gebaeudemass-zielgeschoss green; tests/ 393 OK.
- Live: bungalow_001 (no sizes) opens 10.92 x 10.63 m, "Schätzung ...", image width 19.68 m = stored scale, "Die Zeichnung bleibt"; onehalfstorey_029 (entered 11 x 11) opens 11.00 x 11.00, no estimate note. Closed with Abbrechen, nothing saved.
