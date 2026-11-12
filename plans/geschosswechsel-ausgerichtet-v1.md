# Annotator: floor switch keeps the aligned building in place

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "when I align floors and use the floor switcher they are not aligned in the view".

## Current evidence (measured)

- `annotate.js` `loadFloor()` (~3803) only swaps the image. `zoom-pan.js` keeps zoom and scroll on image load (123), or resets to 0 at zoom 1.
- `floor_alignment` (two opposite corners per floor) is only used for drawing and building, never for the view.
- twostorey_022, at 100 %:
  - EG marks at (28,27)–(317,368) px in the image area;
  - OG marks at (37,31)–(314,355) px;
  - so the building moves about 9 px and is about 4 % smaller/larger.

## Exact scope

1. On a floor switch where BOTH floors have their two alignment marks:
   - remember where the old floor's marks are on screen;
   - after the new image loads, set the zoom so the new marks are the same size on screen (mean of the x and y factors);
   - scroll so the first mark lands on the same screen spot.
   - The building stays put; only the drawing around it changes.
2. Where scrolling cannot go far enough (image edge), the image area gets the needed extra margin. The margin is purely visual and changes no coordinates. If that proves not cleanly possible, it falls back to "as close as possible" plus a status line.
3. Without marks on one of the two floors, nothing changes (as today), with the status line „Geschosse nicht ausgerichtet – Werkzeug Floor alignment“.
4. Cache versions bumped.

## Out of scope

- No change to saved data, alignment marks, or the build.

## Tests (first)

- Pure function `ansichtFuerGeschoss(alteMarkenBildschirm, neueMarkenBild, …)` → zoom and scroll; a test with the twostorey_022 numbers.
- Seam: `loadFloor` / image load calls it.

Real: twostorey_022, switch EG → OG → EG at 100 % and zoomed in. The marks stay within 2 px on screen. Before/after screenshot.

## Rollback

`.before-geschosswechsel` backups; remove the test.

## Approval record

Rainer in chat, 2026-11-07: "Yes, build it".

## Implementation record (2026-11-07)

- **New static/geschoss-ansicht.js** (loaded after zoom-pan.js, v=20261107-2):
  - `ansichtFaktor()` / `ansichtVersatz()`: the centre of the marks is placed on the centre of the old marks;
  - a capture `change` listener on floorSelect remembers the old mark box;
  - after `load` OR `error`: zoom to the same size, then shift the image with CSS `translate`. The canvas follows through syncCanvasSize.
  - A house without a source image only fires `error`; that is how the first try stayed without effect.
  - „Einpassen“ and „100%“ clear the shift.
  - Only the view changes; no data does.
- The step-3 extra margin is not needed: `translate` shifts in every direction without scrolling.
- **Test first:** static/geschoss-ansicht.test.mjs 3, red before, green after. Totals: static 457/457, simplifier tests/ OK.
- **Live check** (mark box in px, relative to the drawing area):
  - twostorey_022, no source image, at 100 %: EG (35.5, 89, 324.6, 430.7) → OG (34.9, 90, 325.2, 429.6). Before: shifted about 9 px and about 4 % in size.
  - twostorey_022 zoomed: within 2.2 px over EG→OG→EG.
  - twostorey_xvi, real images: EG (51.3, 132.3, 312.1, 393.2) → OG (51.6, 132.2, 311.7, 393.2), within 0.4 px.
- The zoom label shows the actual factor after a switch (e.g. 34 % instead of 100 % in fit mode).
