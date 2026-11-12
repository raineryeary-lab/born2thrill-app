# Annotator: „Aufschlagrichtung wechseln“ wirkt schon beim ersten Klick

Status: DONE 2026-11-06

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-06: "every time i click on Aufschlagrichtung ändern the dotted line turns solid but the Aufschlagrichtung stays the same, i have to click it again".

## Current evidence

- `floorplan-simplifier/static/annotate.js` 2142-2147: a door without `hinge_side`/`swing_side` is drawn dotted from `computeSwingPreview()` (1346-1382), which returns `hinge_side: "start"` and a guessed `swing_side`.
- `static/element-edit.js` 307-310 "Aufschlagrichtung wechseln": unset `swing_side` becomes `"second_room"`, unset hinge becomes `"start"`. When the guess was already second_room/start, the first click only records the guess (solid, same direction).
- 293-306 "Anschlag wechseln": unset swing becomes `"first_room"` without looking at the guess; same kind of surprise.

## Exact scope

1. Both menu items: if the door has no recorded swing, start from `computeSwingPreview(element)` (what Rainer sees dotted), then flip. Without a preview, behave as today.
2. Cache version of element-edit.js in annotate.html bumped.

## Tests (first)

`static/tuer-aufschlag-erster-klick.test.mjs`: seam test that both handlers read `computeSwingPreview` for unrecorded doors.
Real: a dotted door in the Annotator -> one click turns it solid AND flips the direction.

## Safety gate

Only the existing door fields; nothing generated or published.

## Rollback

`element-edit.js.before-aufschlag`, cache version back; remove the test.

## Approval record

Rainer in chat, 2026-11-06: "Yes, build it".

## Implementation record (2026-11-06)

- element-edit.js: `tuerSchwenkAusgangslage()` (recorded swing, else `computeSwingPreview()`, else start/first_room); both menu items flip from it. annotate.html element-edit.js v=20261106-1. Backups `.before-aufschlag`.
- Tests first: static/tuer-aufschlag-erster-klick.test.mjs 3 (red before, green after); all static tests 440/440.
- Live bungalow_003 (7 unrecorded doors, on copies, nothing saved): first click gives the opposite of the dotted preview for all 7 (before: the 3 "second_room" previews only turned solid).
