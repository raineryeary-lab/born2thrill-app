# Konfigurator-Matrix liest die eingetippten Gebäudemaße

Status: DONE 2026-11-05

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-05: "Yes, fix it" -- on "Shall I fix the filter script so your entered sizes count?" (follow-up of masse-fehlen-rot-v1).

## Current evidence

- `scripts/konfigurator-matrix.py` `bildverhaeltnis()` reads `annotation_space.aspect` only from annotations.json; "Gebäudemaße eingeben" stores it in gebaeudemass.json (app.py `sidecar_beim_lesen`, not written back). 9 german_catalog_review houses already have it there and are missing from the matrix.
- The build and `/haus` use the merged value (`scripts/hausdaten.py` `hausdaten()`: annotations first, per field, else gebaeudemass.json; floor_scale merged per floor).

## Exact scope

1. `haus_werte()` takes `floor_scale` and `annotation_space` from `hausdaten.hausdaten(projekt)` (same rule as the build) instead of its own reading.
2. Nothing else (prices, room counting, output files) changes.

## Tests (first)

`scripts/konfigurator_matrix_gebaeudemass.test.py`: temp project with rooms, no preview, aspect + scale only in gebaeudemass.json -> haus_werte gives qm > 0 (was "kein Seitenverhaeltnis"); aspect in annotations wins over sidecar.
Real: rerun the matrix; count rises (expected +9 german_catalog_review houses); no house that had a value loses it.

## Safety gate

Reads only; writes the same two report files as before.

## Rollback

`konfigurator-matrix.py.before-matrix-gebaeudemass`.

## Approval record

Rainer in chat, 2026-11-05: "Yes, fix it".

## Implementation record (2026-11-05)

- `haus_werte()` takes floor_scale and annotation_space from `hausdaten.hausdaten()`.
- Tests first: konfigurator_matrix_gebaeudemass.test.py 3 (1 red before, all green after).
- Matrix rerun: 166 -> 175 houses (+9 german_catalog_review, none lost). twostorey_027 134 -> 163 m2 is NOT from this change (old code gives 163 too; its drawing was edited 2026-11-05 18:33).
- Not done: the website (Snippet 10) still has the old data until the matrix is uploaded -- no upload made.
