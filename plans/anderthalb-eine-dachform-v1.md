# 1,5-Geschosser: nur eine Dachform (Satteldach)

Status: DONE 2026-10-20

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-20: "we dont need the 4 roof forms just the one with the 1,5 story houses".

A 1,5-Geschosser is delivered with ONE exterior, the Satteldach with Kniestock and Zwerchgiebel (anderthalbgeschosser-dach-v1), instead of Flach/Walm/Sattel/Pult. Bungalows and Zweigeschosser keep their 4 roof forms.

## Current evidence

- `run_project.py`: `ROOF_TYPES = ("flachdach", "walmdach", "satteldach", "pultdach")`. `roof_types_for_plan()` returns those 4 (or the versetztes Pult as the 4th) for every house; one exterior render per entry. The delivery count `expected = len(roof_types) + len(floors)` follows from that list.
- `dachform.py` (called by go.py when no roof is chosen) sets "modern flach, classic Walm" for every house. onehalfstorey_044 has no roof chosen yet.
- No other script hard-codes 4 exteriors or 12 images (searched make-codex-job.py, lieferung-pruefen.py, go.py, hausdaten.py, freigeben.py, the state route, house-state.mjs). The Codex job lists what is in the delivery folder.

## Exact scope

1. `run_project.py roof_types_for_plan()`: a 1,5-Geschosser -> `("satteldach",)`. Detection: `anderthalb.ist_anderthalb(plan)` -- the plan carries `house_type` since anderthalbgeschosser-dach-v1. Everyone else unchanged.
2. `dachform.py`: when it has to choose for a 1,5-Geschosser, it sets Satteldach for modern AND classic (`dachform_herkunft` says so). A roof form set by hand is never overwritten (as today).
3. Delivery: for a two-floor 1,5-Geschosser, 1 exterior + 2 interior .blend = 3 expected (follows from 1); images 1 + 4 styles x 2 floors = 9.

## Out of scope

- Bungalows, Zweigeschosser, Hanghaus.
- Houses already built and published with 4 roofs (they stay; a rebuild delivers 1).
- Interior styles (still 4 per floor).

## Tests

New `scripts/eine_dachform.test.py`:
- `roof_types_for_plan` on a plan file with house_type 1.5-storey -> ("satteldach",);
- 2-storey -> the 4;
- roof_fourth doppelpultdach still swaps for others;
- dachform.py's choice for a 1,5-Geschosser -> satteldach/satteldach, others unchanged.

Existing run_project/dachform tests stay green.

Verification: `go.py onehalfstorey_044` (no upload) -> 1 exterior, 2 interiors, verifier green. Then look at the renders.

## Effects / rollback

No upload. Rollback: revert the two hunks, delete the test.

## Approval record

Approved by Rainer in chat, 2026-10-20: "Approved: implement anderthalb-eine-dachform-v1, tests first, then go.py onehalfstorey_044 (no upload)."

## Implementation record (2026-10-20)

- `scripts/run_project.py roof_types_for_plan()`: loads the plan once; `anderthalb.ist_anderthalb(plan)` -> `("satteldach",)`; otherwise unchanged.
- `scripts/dachform.py`: new `standard_fuer(name)` (id prefix or data.json house_type); `--modern/--classic` default to None and fall back to the house's standard, single plan and `--alle`; `dachform_herkunft` names the 1,5 rule. A hand-set roof form is never overwritten (unchanged code path).
- Tests: `eine_dachform.test.py` OK (was red before the change); `anderthalb.test.py`, `hausdaten.test.py`, `lieferung-pruefen.test.py` OK; `go.test.py` OK with `FLOORPLAN_WORKBENCH_DATA_DIR` set (17 errors without it are only the missing env var, unrelated).
- Build `go.py onehalfstorey_044` (no upload): "1 fertig, 0 brauchen dich". delivery-manifest: expected_blends 3 = exterior-satteldach + interior-modern + interior-modern-upper; verified_styles classic+modern. Exterior log: Kniestock 1.00 m north and south, 40 Grad, 1 Zwerchgiebel north. Render looked at: one Satteldach, Zwerchgiebel over the two tall windows.
