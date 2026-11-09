# /haus: Häuser ohne Außenumriss rot

Status: DONE 2026-11-07 (see record)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07, after umriss-groesse-drei-klassen-v1: "mark the ones without the Umriss please, make them red".

## Scope

- `hausdaten.mjs` `umrissFehlt(annotationen)`: the same rule as `umriss_flaeche()` in konfigurator-matrix.py.
  - No `outer_outlines` entry and no old `outer_outline` → "kein Außenumriss".
  - A Staffelgeschoss with rooms but no own outline → "Umriss fehlt: staffelgeschoss".
  - Otherwise "".
- `state/route.ts`: `umriss_fehlt` per house.
- `/haus`: such a row is red with "Außenumriss fehlt", plus a red header note "Außenumriss fehlt: im Annotator „Außenumriss“ zeichnen".
- "2 Maße fehlen" keeps priority in the row text when both apply.

## Tests (first)

`scripts/umriss-fehlt.test.mjs`:
- none → kein Außenumriss;
- per-floor outline → "";
- old single outline → "";
- a Staffelgeschoss without its own outline → named;
- seams in the route and the page.

Real: /haus shows 45 red-for-Umriss houses, e.g. bungalow_040_3.

## Safety gate

Display only.

## Rollback

`.before-umriss-rot` backups of the three files; remove the test.

## Approval record

Rainer in chat, 2026-11-07: "mark the ones without the Umriss please, make them red" (direct instruction, same pattern as the approved masse-fehlen-rot-v1).

## Implementation record (2026-11-07)

- hausdaten.mjs `umrissFehlt()`; state route `umriss_fehlt`; /haus row red "Außenumriss fehlt" (shares the `.masse` red), header note.
- Tests first: scripts/umriss-fehlt.test.mjs 4 (red before, green after); masse-fehlen and haus-verwerfen green; tsc clean for touched files.
- Live /haus: 46 rows red "Außenumriss fehlt".
  - 45 match the matrix list, including twostorey_xvit (Staffelgeschoss).
  - The extra one is twostorey_057: it has 0 rooms drawn, so the matrix skips it.
  - No house is missing both its sizes and its outline.
  - bungalow_040_3 header shows the note.
