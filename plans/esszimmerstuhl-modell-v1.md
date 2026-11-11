# Single "Esszimmerstuhl" gets the same 3D model as the Essgruppe chairs

Status: DONE 2026-10-23

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-23, onehalfstorey_046: go.py stopped with "Verifier R5_appliance_finishes: procedural types with no explicit finish (will use the catch-all): dining_chair".

## Current evidence

- bau.log: `FAIL R5_appliance_finishes -- dining_chair` in both styles; all other checks PASS. Delivery: 4/4 .blend, but 0 styles verified.
- plan-modern.json: 4 placements `asset_id: esszimmerstuhl`, `type: dining_chair`, `build: box`, `mesh_path: None` (the round table in Kochen).
- `data/symbol-model-picks.json` has a pick for `essgruppe_stuhl` ("cgaxis dark grey velvet dining chair", 563 x 593 mm), but none for `esszimmerstuhl`. So the single chair falls back to a procedural box. `verify_render.py check_finish_coverage` (~470) rightly refuses a box of an unknown type.
- No other built house uses the single `esszimmerstuhl` (checked all plan-modern.json files), so this never came up before.

## Exact scope

1. `data/symbol-model-picks.json`: add `esszimmerstuhl` with the same pick as `essgruppe_stuhl` (same file, label, size, divisor). The pick is for the modern style; classic falls back exactly as the Essgruppe chairs do.
2. No change to the verifier (its rule stays: no unknown procedural boxes).

## Out of scope

- Other symbols without a pick (the next house that uses one will show it the same way).

## Tests (first)

- New `scripts/esszimmerstuhl.test.py`: `load_model_picks("modern")["esszimmerstuhl"]` exists and equals the `essgruppe_stuhl` path. On a synthetic plan, `check_finish_coverage` is still FAIL for a box `dining_chair` (rule unchanged), but a placement with a `mesh_path` is not built as a box.
- Existing tests unchanged.

Real check: `python scripts/go.py onehalfstorey_046` (no --hochladen) -> "fertig", R5 PASS. The chairs are real chairs in the dollhouse.

## Safety gate

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. Only a furniture model pick changes; local build only.

## Rollback

`symbol-model-picks.json.before-esszimmerstuhl`; delete the new test.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement esszimmerstuhl-modell-v1, tests first, then go.py onehalfstorey_046 (no upload)."

## Implementation record (2026-10-23)

- data/symbol-model-picks.json: `esszimmerstuhl` appended. It is a copy of the `essgruppe_stuhl` pick, plus a note; no other entry moved (a first try sorted the keys and was reverted).
- Tests first: scripts/esszimmerstuhl.test.py.
  - The pick exists in both styles and equals essgruppe_stuhl. This case was red before and green after.
  - The verifier's R5 rule is unchanged: a box dining_chair still fails. Green before and after.
  - Planned test not written: a placement with a model is not built as a box. The live build below covers it.
- Suites: all workbench Python suites OK, except the known red bungalow_039 door test.
- Live: `python scripts/go.py onehalfstorey_046` (no --hochladen) -> "fertig", 4/4 .blend certified, R5 PASS. The dollhouse shows four real chairs at the round table. The exterior shows the Doppelhaushälfte with its mirrored neighbour (64 objects) and one roof.
