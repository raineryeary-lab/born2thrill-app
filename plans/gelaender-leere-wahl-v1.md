# Geländer: eine leere Wahl heißt "kein Geländer"

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22, onehalfstorey_vv2: "your railing and shit are wrong with this model fix it please".

## Current evidence

- vv2: the ground-floor stair carries `loch_railing_sides: []` -- every Treppenloch railing switched off in the editor (the hole is enclosed by walls; open only at the Austritt).
- Upper-floor log: "stair NOTE railing_sides=[] matches no segment edge (old Nord/Sued/West/Ost format?) -- falling back to automatic wall detection" -> "7 Gelaender am Treppenloch".
- `render-furnished-dollhouse.py` ~4705: the comment says "a list (even an empty one, meaning no railing at all) is taken as-is", but the stale-format test `not (set(manual_sides) & edges)` is also true for an EMPTY list, so [] falls back to automatic.

## Exact scope

1. Pure top-level `manuelle_gelaenderseiten(wahl, kanten)` in render-furnished-dollhouse.py: None -> None (automatic); [] -> [] (no railing); a non-empty list matching no edge -> None (old format, automatic, as today); otherwise the list.
2. The stair block uses it (same log line for the old-format case).

## Tests (first)

`scripts/gelaender_leer.test.py` (AST-loaded like treppenloch_a1.test.py): the four cases above; seam check that the block calls it.
Real: rebuild vv2 -> log no longer says "falling back", 0 automatic Treppenloch railings; look at the render.

## Rollback

`render-furnished-dollhouse.py.before-leere-wahl`.

## Approval record

Rainer in chat, 2026-10-22: "your railing and shit are wrong with this model fix it please" (bug fix of an existing rule; the comment in the code already states the intended behaviour).

## Implementation record (2026-10-22)

- `manuelle_gelaenderseiten()` top-level in render-furnished-dollhouse.py; the stair block uses it (old-format note only for a NON-empty list).
- Tests first: gelaender_leer.test.py 5 (red before, green after); treppenloch_a1 and render-furnished-dollhouse tests green.
- vv2 rebuilt: "0 Gelaender am Treppenloch" (was 7), Luftraum (stair eye) 1 piece, 2 styles verified, 4 artifacts certified; render looked at.
