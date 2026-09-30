# Furniture live bootstrap for 053

Status: APPROVED — user requested “fix it” after catalogue diagnosis.

## Objective / evidence
Furniture embed calls generate, which returns Unknown explicit reference for 053;
render_geometry succeeds for both saved floors. Bootstrap furniture from that live
geometry, not the generator catalogue. Do not alter annotations or corpus status.

## Baseline and scope
Branch agent/furnished-render-and-annotation-schema, HEAD 5be1a4e18956b9fb2e158bee82aa159898356e89.
Existing extensive dirty tree preserved, including page.tsx and simplifier-reference.ts.
Only furniture embed initialization, a pure adapter and its new test are in scope.
No generator, publishing, approval, data, Blender or email changes.

## Contracts / acceptance
Use existing render_geometry API; floor-N IDs and millimetres unchanged. Both floors
load without corpus membership; errors remain visible. Internal UI document is not
an approved correction and cannot be used to publish. No new generation path.

## Verification
Add adapter tests first: floor IDs, polygons, identity, empty/mismatched rejection.
Run Node tests, TypeScript and live geometry endpoint. No existing tests weakened.

## Risks / rollback
Follow-up runtime review: CSS-hidden correction panels still evaluated rights and
Massing fields absent from the UI document. Correction-only panels/actions now
conditionally unmount in embed mode; this also prevents Save draft persisting a
UI-only document. FurniturePalette retains its own Speichern action. Three tests
pass and TypeScript passes. Browser interaction confirmation remains pending.
Verification: two new tests pass, TypeScript exits 0, live 053 geometry contains
groundfloor (4 rooms) and upperfloor (6 rooms), furniture page HTTP 200.
Browser placement/save interaction not verified. Roadmap FURNITURE-LIVE-053 tracks it.
Diff for this task: new adapter/test/plan plus 18-line embed initialization and
one import in existing dirty page; pre-existing page modifications preserved.

Furniture bootstrap uses a separate UI-only schema; existing normal correction
mode remains untouched. Rollback only this adapter, test and embed branch.
No rights/provenance escalation, external effects, customer sending or deployment.
