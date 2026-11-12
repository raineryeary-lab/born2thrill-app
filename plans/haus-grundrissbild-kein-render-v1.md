# /haus: das Grundrissbild ist kein Render

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "Yes, fix it". /haus shows 108 houses as „Bilder freigeben – 1 Bilder hochgeladen, 0 angehakt“. The one image is the catalogue floor plan (`<plan>-grundriss.png`, katalog-grundriss-bild-v1). The Codex images are what is actually missing there.

## Cause

`state/route.ts` `bilderStand()` counts EVERY image from `b2t/v1/bilder?plan=` as uploaded.

## Fix

- New `renderBilder(liste)` in house-state.mjs: drops images whose file name is `<plan>-grundriss(-N).png` (or a WordPress size variant of it).
- `bilderStand()` counts only those.
- Result: those houses show „warten_auf_codex“ (or „bilder_hochladen“ when finals are ready locally).
- Unchanged: the floor plan stays in the catalogue; `bilder`/`approved` are not touched.

## Tests (first)

house-state.test.mjs: `renderBilder` drops `x-grundriss.png`, `x-grundriss-1.png` and `x-grundriss-768x278.png`, and keeps renders.

## Rollback

`.before-grundrissbild` backups.

## Result

- Test was red before and is green after; house-state 29/29, all lib *.test.mjs 60/60. The tsc error at route.ts:385 is older (zimmerPruefen) and unchanged.
- Live state: before, 108 bilder_freigeben; now 108 warten_auf_codex („6 .blend zertifiziert, noch keine fertigen Bilder“). fertig 105 + fertig_update 14 unchanged.
