# Annotator „Zeichnen“: Checkbox „Treppen einfrieren“

Status: DONE 2026-11-06

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-06: "can you add a freeze checkbox", asked what it should lock: "stairs in Zeichnen".

## Current evidence

Stairs can be grabbed and changed in four places:

- `floorplan-simplifier/static/element-edit.js` 89-114 `elementAtPoint`: stairs get a wide grab band (`treppenBandPx`), so clicks near them select and drag the stairs (142-209).
- `annotate.js` 1225: the older `elementAtPoint` (delete / hit test), with `stairs` in `deletableElementTypes` (517).
- `punkte-verschieben.js` 37 and `punkte-ausrichten.js` 76 (frame selection) include stairs.

## Exact scope

1. A checkbox „Treppen einfrieren“ in the Architektur tool panel, next to „Geschoss darunter zeigen“.
   - It is remembered per browser (localStorage), default off.
   - It is not saved into the house.
2. When ticked:
   - stairs on every floor can't be selected, dragged, deleted, point-moved or frame-selected;
   - a click goes through to whatever lies under the stairs (door, wall, room);
   - stairs stay drawn exactly as they are;
   - the status line says „Treppen eingefroren“ when a click would have hit them.
3. Railing clicks on the stair edges need the stairs selected first, so they are frozen too.
4. Cache versions of the touched scripts in annotate.html bumped.

## Out of scope

- No change to stair data, the build, or the stair rules.

## Tests (first)

`static/treppen-einfrieren.test.mjs`:
- seam test: both `elementAtPoint` versions, punkte-verschieben and punkte-ausrichten check `treppenEingefroren()`;
- the checkbox exists in annotate.html.

Real: in the Annotator, tick the box, then click and drag the stairs: nothing moves and a door next to them can still be picked. Untick: the stairs move again. Nothing saved.

## Safety gate

UI lock only. It writes no data and changes no geometry.

## Rollback

`.before-einfrieren` backups of the touched files; remove the test.

## Approval record

Rainer in chat, 2026-11-06: "Yes, build it".

## Implementation record (2026-11-06)

- annotate.html: checkbox `#treppenEinfrieren` under "Geschoss darunter zeigen".
- element-edit.js: `treppenEingefroren()` (localStorage `annotator.treppenEingefroren`); `elementAtPoint` skips stairs; `selectElement` refuses stairs; ticking drops a selected stair and stair points from the point selection.
- annotate.js `elementAtPoint` skips stairs. Drag, delete, nudge and railing all need the selection.
- punkte-ausrichten.js `punkteImRahmen` skips stairs.
- Cache versions: annotate/zoom-pan/geometry-tools v=20261106-1 (kept in step per test_annotator_has_no_furniture); element-edit v=20261106-2; punkte-ausrichten v=20261106-1.
- Tests first: static/treppen-einfrieren.test.mjs 4 (red before, green after); static 444/444; tests/ 393 OK.
- Live bungalow_003: unticked, the hit is the stairs; ticked: no hit, selection refused, frame select 0 stair points; unticked again, the hit is the stairs; stair points unchanged, nothing saved.

## Follow-up v1.1 (DONE 2026-11-07)

Rainer: "i cant activate the geländer on the treppenloch, why?" Cause: `stairRailingEdgeAtPoint()` (element-edit.js 65) needs the stairs SELECTED; freeze refuses selection, so railings were frozen too (scope item 3 -- wrong call).
Fix: while frozen, `stairRailingEdgeAtPoint()` tests the Treppenloch edges of EVERY stair on the active floor, without a selection, so an edge click toggles the railing; the stairs still cannot be selected or moved. Test first: seam -- the frozen branch loops over `elements` with type stairs. Live: ticked, click an edge -> railing on/off, stair points unchanged.

Approval: Rainer in chat, 2026-11-07: "Yes, build it".
Implementation:
- `stairRailingEdgeAtPoint()`: with a selection it works as before. Without one and frozen, it tests every stair on `activeFloor` and returns `gezeichnet` (the drawn stair).
- The wall prompt on switch-on uses `railingHit.gezeichnet` instead of the selection.
- element-edit v=20261107-1.
- Backups `.before-gelaender-eingefroren`.
- Tests: 1 new seam test was red before and green after; static 448/448.

Live check, bungalow_003, upper floor, frozen, nothing selected:
- edge click 1 turns loch_railing_sides ["0-left"] on;
- click 2 turns it off again (`[]`);
- the selection stays null and the stair points are unchanged;
- the state was reset and nothing saved.
