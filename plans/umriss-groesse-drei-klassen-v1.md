# Konfigurator-Matrix: Hausgröße aus dem Außenumriss, drei Klassen

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: room count is a poor yardstick for the budget (galleries, Lufträume, big rooms). Instead: "use the Außenumriss from each floor, add everything up ... multiplied by the floor height, but it is the same everywhere so it doesn't matter, we just have to divide it into three parts".

## Current evidence

- `scripts/konfigurator-matrix.py` `haus_werte()` 154-217: living area from the room polygons (`flaeche() × scale² × aspect`), rooms counted, budget window chosen by rooms (rule 37). No outline area.
- Outlines are in annotations.json:
  - `outer_outlines` holds one entry per floor;
  - older houses use a single `outer_outline` + `outer_outline_floor`.
- Survey 2026-11-07 (266 projects):
  - 165 have an outline on every floor that has rooms;
  - 56 are missing it on some floor (e.g. bungalow_003, onehalfstorey_003);
  - 44 have none;
  - 1 has no rooms.

## Exact scope

1. In `haus_werte()`: `umriss_m2` = sum over all floors with rooms of the floor's outline area. It uses the same scale and aspect as the rooms (`flaeche() × s² × aspect`).
2. A floor without its own outline uses the drawn one: the same rule as `outlineForFloor()` in annotate.js (Rainer, 2026-11-07: identical floors only need the EG outline). This covers 55 of 56 houses.
   - Exception: a Staffelgeschoss without its own outline is not copied; `umriss_fehlt` names it (1 house).
   - No outline at all (44 houses): `umriss_m2` stays empty and `umriss_fehlt` = "kein Außenumriss", unless Rainer decides otherwise.
3. New columns in the CSV and the Markdown table:
   - `umriss_m2`;
   - `umriss_fehlt`;
   - `groessenklasse` (1 small / 2 medium / 3 large).
4. Three classes:
   - first proposal: thirds by count over all houses with a value;
   - the two boundaries are written to EINST `groessenklassen_grenzen_m2`, so Rainer can set them by hand later.
5. Report listing:
   - the boundaries;
   - how many houses fall in each class;
   - the 100 houses whose outline is missing.

## Out of scope

- Price, budget window and rule 37 are untouched. Whether the budget follows the size class is Rainer's / the boss's decision after seeing the numbers.
- No upload to the website (Snippet 10).

## Tests (first)

`scripts/konfigurator_matrix_umriss.test.py`:
- two floors with a 10 × 10 m outline each give 200 m²;
- an old single outline counts for its floor;
- a missing floor outline gives no value and names the floor;
- the class split works on given boundaries.
- Existing matrix tests stay green.

Real: run the matrix and show the boundaries, the counts per class and 3 example houses (one per class) to Rainer BEFORE anything else (rule 8).

## Safety gate

Read-only on the houses; writes only the matrix output files.

## Rollback

`konfigurator-matrix.py.before-umriss`; remove the test.

## Approval record

Rainer in chat, 2026-11-07: "Mark them, I'll draw" (answer to the plan's open question; builds the plan as written).

## Implementation record (2026-11-07)

- konfigurator-matrix.py:
  - `umriss_flaeche()`, `drittel_grenzen()`, `groessenklasse()`;
  - `haus_werte` returns `umriss_m2` / `umriss_fehlt`;
  - CSV gets 3 columns at the END (`umriss_m2`, `umriss_fehlt`, `groessenklasse`), so existing readers are unaffected;
  - konfigurator-fehlt.md gets the class summary and the list without size;
  - konfigurator.json gets `groessenklassen_grenzen_m2` = [135, 187] (thirds proposal, editable).
- Tests first: konfigurator_matrix_umriss.test.py 7 (red before, green after); konfigurator_matrix_gebaeudemass 3 OK.
- Run 2026-11-07: 263 houses.
  - Small (under 135 m²): 69 houses, 77–134 m²; example bungalow_040_38, 119 m², 4 rooms.
  - Medium (135 to under 187 m²): 76 houses; example onehalfstorey_017, 162 m², 5 rooms.
  - Large (187 m² and up): 73 houses, up to 288 m²; example twostorey_xvi, 210 m², 5 rooms.
  - 45 without a size: 44 have no outline, 1 has a Staffelgeschoss.
- Finding: outline area ≈ room area (median ratio 1.00, 80% between 0.975 and 1.01). The rooms are drawn to the outer wall face, so the existing m² and price are already effectively gross area. Outliers worth a look:
  - smaller outline: twostorey_020 0.79, twostorey_023 0.80;
  - larger outline: twostorey_xvbah 1.32, twostorey_047 1.15.
- Open (Rainer / boss): whether the budget window follows the size class instead of the room count (rule 37).
