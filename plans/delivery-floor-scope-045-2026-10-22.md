# Delivery verifier: isolate comparisons by source floor

Status: IMPLEMENTED AND VERIFIED (explicit user approval 2026-10-22)
Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective
Remove false cross-floor displacement reports for onehalfstorey_045 while preserving genuine same-floor displacement checks.

## Evidence and baseline
Branch agent/furnished-render-and-annotation-schema; HEAD 5be1a4e18956b9fb2e158bee82aa159898356e89. Working tree has many pre-existing changes and untracked files; preserve them. Target verifier and tests already exist as untracked files. Baseline recorded before implementation.
The delivered catalog used unsupported partial-occlusion statuses, incorrect replacement statuses, omitted source_blend and a nonparseable mesh total. These delivery metadata mistakes have been corrected under the existing delivery authorization; occlusion details retained separately. All 10 server originals were re-downloaded on 2026-10-22 and matched local SHA256.
Exact go.py lieferung_fehlt now reports only 12 false displacement errors for teppich-0, teppich-1 and wall-0-door. verschobene_objekte flattens both floor maps into name-keyed dictionaries; OG names overwrite EG names, and observations are pooled across floors.

## Exact scope / files
scripts/lieferung-pruefen.py: group both reference coordinates and sightings by matching source_blend/object-map floor plus object name. Preserve legacy single-map behavior. Keep no-source behavior conservative. Pass floor-specific reviewed identity into per-image checks.
New standalone scripts/lieferung-pruefen-floor-scope.test.py: regression tests. Existing tests remain unchanged.
This plan and central ROADMAP.md: record evidence and pending status.
Delivery catalog validation metadata only after final successful check.

## Out of scope
No image regeneration, geometry/source edits, upload logic, customer flags, rights ledger, email, database changes, commits or cleanup of unrelated work.

## Acceptance and tests (tests first)
- Identical names at different EG/OG positions must not be compared across floors.
- A moved object in two styles of the same floor must still fail.
- Single-floor and legacy missing-source cases retain existing checks.
- Existing lieferung-pruefen.test.py passes unchanged.
- Exact go.py lieferung_fehlt on the full delivery returns [] without disabling checks or altering images.

## Contracts, risks and invariant
No schema relaxation. Source floor is already specified by source_blend. Main risk: inadvertently suppressing a same-floor comparison; regression test must prove it remains active. Can changed paths generate, publish or email geometry without an approved corrected corpus reference? No: only read-only validation grouping changes; no generation/upload/email paths added or invoked.

## Rollback
Back up exact target files before editing (untracked existing work), restore only those snapshots. Delivery catalog backup exists in corrected-delivery-20261021-221008/catalog-before-schema-fix.json.

## Approval record
Approved explicitly by Rainer on 2026-10-22: "Ja, Pruefer-Fix umsetzen".

## Implementation and verification
Grouped style comparisons by unique source_blend/object-map match. Missing or ambiguous provenance retains conservative legacy behavior. Existing tests unchanged. Two new regressions failed before and pass after; 101 existing tests pass. Exact go.py lieferung_fehlt on all 10 delivered files returns []. No generation, publication or email path was added by the code change.

Only runtime diff: wrapper plus rename of original helper. New standalone regression test and documentation. Repository remains dirty from pre-existing work; no commit. Full final status and task diff saved beside the delivery audit. Rollback: restore exact verifier snapshot C:/Users/Admin/AppData/Local/Temp/lieferung-pruefen-before-floor-scope.py and remove only the newly added floor-scope test if requested.

Limitation: validation checks catalog evidence, not pixel-level physical dimensions. Four EG image cleanup/replacement actions are separately authorized delivery work.
