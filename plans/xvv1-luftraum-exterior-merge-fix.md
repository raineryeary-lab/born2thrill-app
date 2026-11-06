# xvv1: preserve explicit exterior outline beside overlapping stairwell void
Status: APPROVED - user approved runtime fix and regression tests on 2026-10-30
## Objective and evidence
Finish approved xvv1 delivery. Both furniture layouts corrected and saved; normal build now fails roof preflight with7 exterior wall segments. Explicit closed8-vertex OG outline exists and annotations unchanged. _merge_overlapping_parallel_walls merges room-derived interior edges with explicit exterior outline, retains interior type when drinnen=False and averages boundary location; later Luftraum removal deletes the misclassified edge.
## Repository baseline
Workbench agent/furnished-render-and-annotation-schema base5be1a4e18956b9fb2e158bee82aa159898356e89. Existing dirty scripts must be preserved; no checkout/reset. Existing status recorded in xvv1 workspace.
## Scope
Narrow correction in scripts/build-simplifier-render-plan.py: preserve authoritative explicit outer-outline geometry/type when overlapping room-derived pseudo-partitions merge; retain real interior partitions. Add targeted regression in scripts/doppelwand_teil.test.py or dedicated equivalent test. No annotation/furniture-size/roof-design changes, no bypassflags, no validator weakening. Rebuild only xvv1 then resume image package/upload.
## Acceptance and tests
Regression fails before fix. Verify both merge input orders, exact exterior reference line/thickness, partial-overlap remnants, true interiorwall behavior, Luftraum circulation opening remains open and genuine exterior stays closed. Run existing doppelwand and Luftraum tests plus full relevant generator tests. xvv1 normal roof preflight and model validation pass. Freshly inspect Blender and recheck fitted furniture against final wall faces.
## Contracts and risks
Existing schema and gates unchanged; code change cannot generate/publish without existing approved-reference checks. No rights/release changes or customer sends. Risk: merge interactions; cover with existing tests and exact outline regression.
## External effects and rollback
Only later authorized complete image upload without send. Runtime fix isolated diff, do not revert preexisting user changes. Preserve furniture backups and model audit. No commit/push/deploy.
## Approval
Runtime-fix approval received under AGENTS.md step5. Furniture adjustment approval already fulfilled; no further upload permission required after completing package.

## Approval received
2026-10-30 user explicitly: Yes—fix the generator and finish xvv1. Narrow runtime fix and regression tests authorized; rebuild and full-package internal upload authorized. No separate upload approval needed.

