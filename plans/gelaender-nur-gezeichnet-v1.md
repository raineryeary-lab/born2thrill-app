# Treppenloch/Luftraum railings: suggestion in neon green, click on/off, right-click lock

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07:
- "your treppen aussparung and or luftraum dont let me place a railing so that it doesnt interrupt the stairs at the top; i also cant even click to activate the railing on the treppenloch tool";
- then: "instead of autorailing paint your railing-suggestion in neon green and turn on turn off on click with a right click lock".

## Current evidence (measured)

1. **Clicks get swallowed.**
   - `luftraum-gelaender.js` pointerdown gives an element under the pointer priority (`elementAtPoint`).
   - twostorey_022 upper floor, Treppenöffnung:
     - edges 1 and 2 hit the stair (role opening, wide grab band);
     - edge 4 hits a window;
     - only edge 3 toggles.
2. **Railing across the stair top.**
   - `render-furnished-dollhouse.py` 3146 `deckenloch_auto_kanten()` leaves the exit edge open only if it lies within 150 mm of the stair's end edge.
   - A hole drawn a bit larger gets a railing on every edge, the exit included.
3. **The automatic railing is invisible in the Annotator.** Untouched edges show pale-orange dashes; nothing says which ones get built.

## Exact scope

1. **One rule for "suggested"**, the same in the Annotator and the build:
   - Treppenöffnung: every edge except the exit edge. The exit edge is the edge nearest to and parallel with the stair's arrival end, with no 150 mm limit.
   - Luftraum and balcony: every edge.
   - The build keeps its wall gaps (rule 21).
2. **Annotator display**, on every upper floor without selecting anything:
   - suggested and undecided: neon green (#39ff14), dashed;
   - on: neon green, solid and thick;
   - off: grey, thin;
   - locked: a small lock symbol at the edge's midpoint.
3. **Left click** on an edge (Auswählen) toggles that edge on/off.
   - The edge wins over stairs, doors and windows under it, within 9 px.
   - The first click turns the suggestion into a real choice (suggestion minus or plus that edge).
4. **Right click** on an edge toggles its lock. A locked edge ignores left clicks.
   - Saved as `gelaender_gesperrt` [edge indices] on the room or balcony.
   - The `app.py` save allowlist is checked so it is not silently dropped.
5. Stair Treppenloch edges (house without a drawn Treppenöffnung) work the same way: always shown in neon green, click/lock without selecting the stair. Stored in `loch_railing_sides` / new `loch_railing_gesperrt`.
6. **Build:** an explicit choice is built as before. No choice means the suggestion from item 1, so what you see is what gets built.
7. The drawn Geländer element stays, for free railings.
8. Cache versions bumped.

## Tests (first)

- **Python:** a Treppenöffnung drawn 400 mm past the stair end still leaves the exit edge open.
- **JS:**
  - suggestion = every edge except the exit;
  - clicking an edge under a stair/window toggles the edge, not the element;
  - right click locks, then a left click changes nothing;
  - `gelaender_gesperrt` survives the save (app.py allowlist).
- **Real:**
  - twostorey_022 upper floor: all 4 edges clickable, the exit edge suggested off;
  - build on a copy: nothing across the top step (rule 7, editor vs .blend).

## Rules

REGELN.md rule 35 gets: "Vorschlag neongrün im Annotator, Klick an/aus, Rechtsklick sperrt" (Rainer's word, this chat).

## Rollback

`.before-gelaender-vorschlag` backups; remove the tests.

## Approval record

Rainer in chat, 2026-11-07: "Yes, build it".

## Implementation record (2026-11-07)

- **Build** (render-furnished-dollhouse.py `deckenloch_auto_kanten`): the exit edge is the nearest parallel hole edge, with no 150 mm limit.
- **app.py:** `gelaender_gesperrt` (room, balcony) and `loch_railing_gesperrt` (stairs) survive saving.
- **luftraum-gelaender.js:**
  - `vorschlagKanten()` / `gelaenderVorschlag()`;
  - neon-green display (solid when chosen, dashed when suggested, grey when off, lock symbol);
  - click/right-click run in capture on canvasWrap. element-edit.js already grabs in the canvas capture phase, which is why edge clicks used to select the stair.
  - The old "an element under the pointer wins" check is gone.
- **element-edit.js:**
  - upper-floor Treppenloch edges are clickable without a selection (unless a drawn Treppenöffnung replaces them);
  - the first click starts from the suggestion (all edges);
  - a locked edge ignores clicks;
  - right click locks it.
- **annotate.js:** upper-floor stair edges are always shown, in neon green.
- **Versions:**
  - annotate/zoom-pan/geometry-tools v=20261107-2;
  - element-edit v=20261107-3;
  - luftraum-gelaender v=20261107-2.
- **Tests first, red before and green after:**
  - gelaender_vorschlag.test.py 2;
  - tests/test_gelaender_gesperrt.py 3;
  - static/gelaender-vorschlag.test.mjs 3.
- **Totals:**
  - static 454/454;
  - simplifier tests/ OK;
  - scripts/*.test.py OK except the pre-existing door-swing test (roadmap).
- **Live check, twostorey_022 upper floor:**
  - suggestion = edges 1, 3, 4; edge 2 = exit, grey;
  - clicks on all 4 edges toggle, and the stair is NOT selected (before: edges 1 and 2 went to the stair, edge 4 to a window);
  - right click locks, the next click changes nothing, right click unlocks;
  - test state reset, nothing saved.
- **Build on a COPY of twostorey_022:**
  - railing on edge 1 (2.05 m);
  - the exit edge is open over the stair width; only the 0.44 m beyond the stair gets a railing (existing top-floor rule);
  - verify R2_gelaender, R3, R9_stair_access PASS.
- REGELN.md rule 35 extended (Rainer's word).

## Same turn: room list in two rows

Rainer, 2026-11-07: "put the Kochen 6 points 5,8 rel. stuff in one line ... and underneath the m2 edit remove so it is 2 rows".
- styles.css `.annotation-item-area`: the text spans the full width, and m², Edit, Remove sit in the row below. styles v=20261107-1.
- Test static/raumliste-zwei-zeilen.test.mjs: red before, green after.
- Checked live on twostorey_022.
