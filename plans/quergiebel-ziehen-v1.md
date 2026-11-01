# Quergiebel/Zwerchkubus: Breite und Lage im Annotator ziehen

Status: DONE 2026-10-21

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

Touches both subprojects: floorplan-simplifier (Annotator) and born2thrill-local-workbench (plan builder, renderer). Pointer file: `floorplan-simplifier/plans/quergiebel-ziehen-v1.md`.

## Objective

Rainer, 2026-10-21: "we have to fix the width of the quergiebel thingy, you make it as wide as the windows but we will need to be able to adjust the width". He chose option 2: the Quergiebel appears as a bar on the outer wall in the Annotator, and he drags its two ends (width AND position).

## Current evidence

- Width/position are computed only: `anderthalb.giebel()` takes the high openings of the eave side, adds `RAND_M`=0.5 m each side, at least `GIEBEL_MIN_M`=2.5 m; without openings 1/3 of the facade or 2.0 m (Ziergiebel). onehalfstorey_044 north: 4.64-7.88 m.
- The Annotator only stores gables as dropdowns (`annotate.js` 300-334: `architectural_features` `{type:"gable", subtype, orientation, floor_level}`), no geometry.
- Windows/doors/openings are 2-point elements on a wall (`elements[].points`); `build-simplifier-render-plan.py` (2238-2300) matches them to the nearest wall (<= 1200 mm) and turns them into `position` + `width_mm`. Line elements can be moved as a whole but their END POINTS cannot be dragged today.

## Exact scope

Annotator (floorplan-simplifier):
1. New tool button "Quergiebel" (Architektur panel, next to Window). Draw like a window: two clicks along an outer wall of the upper floor; snaps onto the wall line. Stored as element `{type: "quergiebel", floor_level, points: [a, b]}`.
2. Drawn as a thick orange bar with a round handle at each end; selecting it and dragging a handle moves that end along the wall (stays on the wall line). Delete like other elements.
3. "Vorschlag" button: places the bar where the renderer would put it today (same rule as `anderthalb.giebel`), so Rainer starts from the automatic width and only adjusts.
4. `app.py normalize_element`: `quergiebel` kept with its points (no silent filter -- test the seam).
5. Cache versions bumped together (annotate/zoom-pan/geometry-tools).

Plan builder + renderer (born2thrill-local-workbench):
6. `build-simplifier-render-plan.py`: `quergiebel` elements of the top floor -> `plan["quergiebel"] = [{a_mm, b_mm}]` (same frame as the walls).
7. `anderthalb.giebel()`: if drawn Quergiebel exist, they REPLACE the automatic ones -- side from `seite_von_wand`, lo/hi from the two end points along the facade; no minimum, no padding. Without drawn ones: unchanged automatic rule.
8. Both variants use it: classic Zwerchgiebel and modern Zwerchkubus get the same width.

## Out of scope

- The dropdowns Giebel 1/2 stay as they are.
- Bungalows/Zweigeschosser.

## Tests (first)

- floorplan-simplifier: normalize keeps a `quergiebel` element with points (Python); JS: a dragged end stays on the wall line; Vorschlag on 044's data gives 4.64-7.88 (within 1 cm).
- workbench: plan builder emits `quergiebel` in mm; `anderthalb.giebel()` with a drawn 3.0-8.0 m on north returns exactly that and nothing automatic on north; without drawn -> today's results (existing tests unchanged).
- Real check: draw on onehalfstorey_044 at another width, rebuild, measure the Zwerch in the .blend = drawn width (+-2 cm), both exteriors; look at the renders.

## Safety gate

Can any changed path publish geometry without an approved reference? No. Annotation and local builds only; nothing uploaded.

## Rollback

`.before-quergiebel` backups of the touched files; a drawn element can simply be deleted in the Annotator (falls back to automatic).

## Approval record

Rainer in chat, 2026-10-21: "Approved: implement quergiebel-ziehen-v1, tests first, then try it on onehalfstorey_044."

## Implementation record (2026-10-21)

- floorplan-simplifier: new `static/quergiebel.js` (`quergiebelVorschlag` = same rule as anderthalb.giebel, `quergiebelEnde`, `quergiebelVorschlagSetzen`); `annotate.html` buttons "Quergiebel" + "Quergiebel-Vorschlag", script tag, cache versions annotate/zoom-pan/geometry-tools/element-edit/waende-einrasten -> 20261021-1; `annotate.js` orange 14 px bar with round end handles, deletable, name "Quergiebel"; `element-edit.js` grab an END -> only that end moves, snaps back onto the wall on release; `waende-einrasten.js` snaps quergiebel like a window. app.py unchanged: normalize_element already keeps type + points (seam test green before and after).
- workbench: `build-simplifier-render-plan.quergiebel_m()` -> `plan["quergiebel"]` (top floor, registered frame, metres); `anderthalb.gezogene_giebel()` + `giebel(..., gezeichnet=)` -- drawn ones replace the automatic ones completely, exact ends, no padding/minimum; `render-exterior.py` passes `plan["quergiebel"]`. The existing "Oeffnung liegt in keinem Giebel" WARNUNG still fires if a drawn bar is narrower than the windows.
- Tests first: quergiebel.test.mjs 6, test_quergiebel_speichern 1, quergiebel_plan.test.py 6; all suites green (simplifier 316 py + all .mjs; workbench all except the known door-hinge failure).
- Real check on onehalfstorey_044 (NOT saved -- Codex is rendering from the current build): Vorschlag in the live Annotator -> 1 bar north; through the real RegisteredFrame 4.60-7.92 m (automatic was 4.64-7.88: 4 cm per end, from the OG registration x1.07 -- plan asked 1 cm, recorded as deviation; the build follows the drawing exactly). Scratch builds: drawn 4.604-7.916 -> extwall-zwerch 4.604-7.916 m; drawn wider 3.930-8.590 -> 3.930-8.590 m (to the mm), flat roof +-0.05 overhang. Annotator change discarded unsaved; annotations.json has 0 quergiebel.
