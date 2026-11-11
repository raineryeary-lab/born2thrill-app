# Raumtyp „Treppenhaus“ (Mehrfamilienhäuser)

Status: DONE 2026-11-07 (Annotator restarted, room type checked live)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "we need a new room type being for mehr familienhäuser 'treppenhaus'".

## Current evidence

- Room types are listed twice:
  - floorplan-simplifier/app.py `ROOM_CHECKLIST` (~line 270-320);
  - static/annotate.js room list (~line 180-225).
- **Build:** build-simplifier-render-plan.py `ROOM_KINDS` maps "treppe" → circulation, so "Treppenhaus" is already circulation (like Flur).
- **Matrix:** `KEIN_ZIMMER` contains "treppe", so it is never a Zimmer. It counts toward the area (not in `NICHT_WOHNFLAECHE`).
- **Window check:** app.py `no_window_required_ids` (~5122) does not list a stairwell.
- **House types:** bungalow / 1.5-storey / 2-storey / 2-storey with cellar / other. No Mehrfamilienhaus.

## Scope (once the answers are in)

1. Room type `treppenhaus` / „Treppenhaus“ in app.py `ROOM_CHECKLIST` and annotate.js; cache version bumped.
2. app.py `no_window_required_ids` += treppenhaus.
3. Catalogue drawing (katalog-grundriss-bilder.py): hallway colour.
4. Area: depending on the answer, either counted (like Flur) or added to `NICHT_WOHNFLAECHE`.
5. Optional: house type Mehrfamilienhaus (only if Rainer wants it).

## Tests (first)

- **static:** the room type exists in annotate.js.
- **tests/:** app.py `ROOM_CHECKLIST` contains treppenhaus, and the window check does not flag it.
- **Matrix:** a Treppenhaus is not a Zimmer, and the area follows the decision.

## Rollback

`.before-treppenhaus` backups; remove the tests.

## Decision and implementation (2026-11-07)

- Rainer: the area counts like Flur ("yes"), so the matrix is unchanged. The Mehrfamilienhaus house type is still open.
- **app.py:** `ROOM_CHECKLIST` += („treppenhaus“, „Treppenhaus“); `no_window_required_ids` += treppenhaus.
- **annotate.js:** room list += Treppenhaus (after Treppenöffnung).
- **annotate.html:** annotate/zoom-pan/geometry-tools v=20261107-3.
- **katalog-grundriss-bilder.py:** Treppenhaus in the hallway colour.
- **Build:** already circulation via "treppe" in ROOM_KINDS. **Matrix:** already not a Zimmer via "treppe" in KEIN_ZIMMER.
- **Tests first:** tests/test_raumtyp_treppenhaus.py 3, red before, green after (including the counter-check that an unknown room still gets the window warning). tests/ OK, static 459/459.
- Backups `.before-treppenhaus`.
