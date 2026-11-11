# Hausliste: Häuser ohne Gebäudemaße leuchtend rot

Status: DONE 2026-11-05

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-05 (http://localhost:3020/haus?plan=onehalfstorey_021): "can you make the ones that need the 2 numbers bright red or something".

## Current evidence

- `WEBSITE-FILTER-DATEN-2026-11-05.md`: 98 houses have rooms and a scale but no plan image (`*original_preview.png`) and no `annotation_space.aspect` -> area, rooms and price cannot be calculated (`konfigurator-matrix.py` `bildverhaeltnis()`).
- The fix per house is the Annotator button "Gebäudemaße eingeben" (width + depth).
- `/haus` list (`src/app/haus/page.tsx` ~1213) shows only plan and state; `state/route.ts` already reads `hausdaten()` (merged `annotation_space`, `floor_scale`) per house.

## Exact scope

1. Pure `masseFehlen({ dateien, annotation_space })` in `src/lib/floorplan-workbench/hausdaten.mjs`: true when no file `*original_preview.png` and no valid `annotation_space.aspect` -- the same rule as `konfigurator-matrix.py`.
2. `state/route.ts` adds `masse_fehlen` per house.
3. `/haus` list: such a row is bright red with the text "2 Maße fehlen"; the header of an open house shows the same red note "Gebäudemaße eingeben (Breite + Tiefe)".
4. Nothing else changes (states, order, buttons).

## Tests (first)

`scripts/masse-fehlen.test.mjs`: no preview + no aspect -> true; preview present -> false; aspect present -> false; seams: route sets `masse_fehlen`, page uses it.
Real: /haus list shows the red rows; count = 98; onehalfstorey_021 (has data) not red; bungalow_001 red.

## Safety gate

Display only; no data written.

## Rollback

`.before-masse-rot` backups of page.tsx, route.ts, hausdaten.mjs; remove the test.

## Approval record

Rainer in chat, 2026-11-05: "Approved, build it".

## Implementation record (2026-11-05)

- `hausdaten.mjs`: `masseFehlen({dateien, annotation_space})`; `state/route.ts`: `masse_fehlen` per house (merged annotation_space incl. gebaeudemass.json); `haus/page.tsx`: red row "2 Maße fehlen" + red hint in the header.
- Tests first: scripts/masse-fehlen.test.mjs 5 (red before, green after); tsc clean for the touched files.
- Live /haus: 105 red of 281 (bungalow_001 red, onehalfstorey_021 not). Differs from the 98 of the filter table: 9 german_catalog_review houses already carry the aspect in gebaeudemass.json (not red, correct); 16 more lack scale or were counted otherwise there, but also lack the aspect (red, correct).
- Found: `konfigurator-matrix.py` `bildverhaeltnis()` reads annotation_space only from annotations.json, not from gebaeudemass.json -- where "Gebäudemaße eingeben" stores it. Entered sizes would not reach the website filter. Roadmap.
- Follow-up fix 2026-11-05 (Rainer, onehalfstorey_029: "i put in both measurements and it is still red"): the sizes were saved, but the list only loaded once. Now the list reloads after every successful drawing save (step/house switch) and after "Finish project". Seam test +1 (6/6); live: switching Zeichnen -> Möbel refetches /state; 029 no longer red (104 red). Backup page.tsx.before-masse-neu-laden.
