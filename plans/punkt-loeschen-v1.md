# Punkt statt ganzer Küchenzeile löschen

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-03: "if one point on a küchenzeile is active and not the whole zeile and i press on delete please just delete that one pont and not the whole küchenzeile".

## Current evidence and behavior

- `furniture.tsx:1030` "Löschen" calls `onRemove` -> `page.tsx:1908-1911` removes the whole symbol, ignoring `punktAuswahl`.
- No Delete/Backspace key handler exists in the Möbel step (`page.tsx` keydown at 1103-1147 handles arrows, Strg+Z, Esc only).
- Single-point delete exists only in the right-click menu (`loeschePunkt`, page.tsx:1763-1771).

## Baseline

Git HEAD `5be1a4e`, 640 dirty/untracked entries before this task (user-owned, untouched). Backups `*.before-punkt-loeschen` of page.tsx and furniture.tsx.

## Exact scope

- New pure `src/lib/floorplan-workbench/punkte-loeschen.mjs`: `loeschZiel(punkte, auswahl)`.
- "Löschen" button and new Delete/Backspace key: with selected points on a drawn run -> delete only those points (run keeps at least 2, else refuse with a message); without point selection -> unchanged (whole symbol / group).
- Button label reads "Punkt löschen" / "N Punkte löschen" while points are selected.

## Files in scope

`src/lib/floorplan-workbench/punkte-loeschen.mjs`, `src/lib/floorplan-workbench/punkte-loeschen.test.mjs`, `src/app/floorplan-workbench/page.tsx`, `src/app/floorplan-workbench/furniture.tsx`.

## Explicitly out of scope

Annotator, renderer, saved data format.

## Schema and dataset-contract effects

None.

## Acceptance criteria

One selected point + Löschen/Delete removes that point only; no selection removes the whole symbol as before; a 2-point run is never reduced below 2.

## Tests and verification commands

`node --test src/lib/floorplan-workbench/punkte-loeschen.test.mjs`; `node --test scripts/moebel-punkte.test.mjs`; `npx tsc --noEmit` (no new errors); browser check at localhost:3020 without saving.

## Protected local data and risky paths

No data written by the change; furniture saves only on the user's Save.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

No. Editor interaction only.

## External effects

None.

## Failed-hypothesis log

## Rollback

Restore the `.before-punkt-loeschen` copies and delete the two new files.

## Unresolved questions

## Approval record

Rainer, 2026-11-03 (request above, REGELN 5).
