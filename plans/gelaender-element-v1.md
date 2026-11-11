# Annotator + build: a "Geländer" element, drawn like the Trennwand

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "i need to have a railing element like the trennwand, the treppenloch combine with the should work".

## Current evidence

- Trennwand = element `partition`:
  - annotate.html 36 has the tool button;
  - annotate.js 517 makes it deletable;
  - annotate.js 2004/2021 draw it;
  - annotate.js 3565 sets the default thickness;
  - element-edit.js 23 `LINE_ELEMENTS` (select/drag) and 395 (right-click menu).
- Build: `build-simplifier-render-plan.py` 2094 `partition_walls()` turns each partition into an interior wall per floor (`frame.point()` gives mm).
- Railings today come only from:
  - stair side (`railing_sides`);
  - Treppenloch (`loch_railing_sides`, or the auto rule 35);
  - Luftraum / Treppenöffnung rooms (`gelaender_kanten`);
  - balcony.
- All are built by `_lr_lauf(name, a_mm, b_mm)` in `render-furnished-dollhouse.py` 4977:
  - 0.90 m high, wooden handrail, steel bars;
  - a gap where a wall runs alongside (`gelaender_freie_stuecke`, rule 21).

## Exact scope

1. **Annotator: new tool „Geländer“** next to „Trennwand“.
   - Two clicks give a straight line (`type: "railing"`).
   - It can be selected, dragged and deleted like the Trennwand, and is drawn as a thin dashed line with bar ticks, so it is not mistaken for a wall.
   - Cache versions bumped.
2. **Plan:** `railing_segments(annotations, level, frame)` puts each drawn railing as `{start_mm, end_mm}` into `floor["railings"]`. It is NOT a wall: no wall cleanup and no room splitting.
3. **Dollhouse:** each `floor["railings"]` entry is built with `_lr_lauf()`, so it looks exactly like the Treppenloch railing. The wall gap stays (rule 21).
4. **Combining with the Treppenloch / Luftraum** (proposal, needs Rainer's answer):
   - a drawn railing that lies ON a Treppenloch or Luftraum edge (parallel, within 15 cm) replaces the automatic railing on that stretch, so no double railing stands there;
   - where a drawn railing ends within 15 cm of a Treppenloch corner, its end snaps to that corner so the two railings meet without a gap.
5. The `verify_render_blend.py check_gelaender` count includes the drawn railings.

## Out of scope

- No change to the auto rule 35, the stair railings, or existing houses (no data migration).
- No railing height setting (fixed at 0.90 m).

## Tests (first)

- static seam test: tool button, `railing` in `LINE_ELEMENTS` and deletable types, drawing branch.
- `scripts/gelaender-element.test.py`:
  - plan: one drawn railing gives 1 segment in mm, and no wall;
  - combining: a segment on a Treppenloch edge removes that edge from the auto list; an end near a corner snaps.
- The existing trennwand and railing tests stay green.

Real: draw one railing on a house with a Luftraum (Rainer picks the house), build it, then compare the editor against the .blend (rule 7). The test geometry is not saved into a house without Rainer.

## Safety gate

Adds a new drawn element and its build. It does not publish, email or upload anything.

## Rollback

`.before-gelaender-element` backups of the touched files; remove the tests.

## Approval record

Rainer in chat, 2026-11-07: "Yes, build it". This answered "drawn railing on a Treppenloch edge replaces the automatic one there and meets it at its corners".

## Implementation record (2026-11-07)

- **Annotator:**
  - annotate.html: button „Geländer“ (`data-tool="railing"`).
  - annotate.js: deletable; name „Geländer“; teal dashed line with bar ticks, 4 px.
  - element-edit.js: `LINE_ELEMENTS`.
  - Versions: annotate/zoom-pan/geometry-tools v=20261107-1, element-edit v=20261107-2.
  - The server keeps any element type (`normalize_element`), so no filter change was needed.
- **Plan builder:** `railing_segments()` writes `floor["railings"]` ({id, start_mm, end_mm}). It is not a wall.
- **New `scripts/gelaender_gezeichnet.py`:**
  - `abdeckung()`: parallel within 10° and within 150 mm;
  - `ohne_intervalle()`;
  - `einrasten()`: an end within 150 mm of a Treppenloch or Luftraum corner snaps to it.
- **render-furnished-dollhouse.py:**
  - drawn railings snap to stair-core, Luftraum and Treppenöffnung corners;
  - the stair Treppenloch edges and the Luftraum/Treppenöffnung edges leave out the covered stretch;
  - the drawn railings are built with `_lr_lauf()` as `gelaender-gezeichnet-*`, keeping the wall gap (rule 21).
  - render-persp-test.py is unchanged: it builds no Luftraum railings at all.
- **verify_render_blend.py:** R2 counts `gelaender-gezeichnet`, and the exit-block check includes it.
- **Tests first:**
  - scripts/gelaender_element.test.py: 8, red before, green after;
  - static/gelaender-element.test.mjs: 2, red before, green after.
- **Totals:**
  - static 450/450;
  - simplifier tests/ OK;
  - scripts/*.test.py all OK (dachboden, go and lieferung-pruefen need FLOORPLAN_WORKBENCH_DATA_DIR).
- **Pre-existing failures, the same with the files from before this change:**
  - build-simplifier-render-plan.test.py `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`;
  - 7 scripts/*.test.mjs (BV Bach PDFs, furniture placement, catalogue, reconstruction). None touches these files.
- **Build check on a COPY of twostorey_xvi** (scratchpad, the real house is untouched):
  - a railing was drawn 30 mm off and 70 mm short of the Luftraum edge 3 (the automatically chosen one);
  - .blend: `gelaender-gezeichnet-0-0` at y 9.438 m spans x 5.812–8.150 m, exactly corner to corner, with 9 bars;
  - the Luftraum edge itself now has 0 pieces (before: 1);
  - verify_render_blend: R2_gelaender and R9_stair_access PASS.
  - A drawn railing along a wall builds nothing, which is correct per rule 21.
- **Annotator live check, bungalow_003:** tool on, two clicks give 1 „Geländer · 2 points“ that can be selected; it was removed again and nothing saved.
