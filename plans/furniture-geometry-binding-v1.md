# Furniture is bound to the geometry it was placed on

Status: APPROVED (Ralph loop item 2 — plans/ralph-workflow-rebuild.md,
batch-approved by Rainer 2026-08-23: "do it then")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Codex audit P0 "Korrektur/Möbel und Build können verschiedene Geometrien
verwenden". Re-checked against today's code before implementing: the Möbel
editor draws `geometry_only()` (annotation-derived) and the /haus build
compiles the same annotation, so the two do NOT diverge by revision as the
audit described — that half is already true.

What IS still open is the same failure in time rather than in path: a
furniture layout carries no record of WHICH drawing it was placed on. Redraw
rooms, move a wall, re-measure the Gebäudemaß — the furniture files stay and
are silently re-used against a different geometry. `/staleness` even computes
this (`geometrieFremd`) and the page never shows it (audit P1). Bind the
furniture to its geometry and refuse the build on a mismatch.

## Exact scope

1. `scripts/haus-zustand.py`: add `geometrie` (the `annotation_state()`
   hash — drawing + Gebäudemaß, deliberately NOT furniture, so stamping
   cannot chase its own tail) to each house's record.
2. `corrections/route.ts` `saveFurniture()`: stamp
   `geometry_identity` (that hash, via the one Python oracle) onto the
   document when the Möbel editor saves. Save must still succeed if the
   identity cannot be determined — then the field stays absent.
3. `furniture-document.mjs` `normalizeFurnitureDocument()`: carry
   `geometry_identity` through instead of dropping it.
4. `build-simplifier-render-plan.py` `workbench_furniture()`: refuse
   (SystemExit, message naming the Möbel step) when a document carries a
   `geometry_identity` that differs from today's. A document WITHOUT the
   stamp is accepted — every existing layout predates it; legacy must keep
   building, exactly as with `floor_registration`.
5. `/haus`: show the `geometrieFremd` warning the staleness route already
   returns.

## Out of scope

`--corrected` build path binding (its own truth, item 3/6 territory),
auto-migrating furniture onto a changed geometry (never silently move a
layout), WordPress/publishing.

## Rights / suite invariant

Can any changed path generate, publish, or email geometry without an
approved reference? No — a stamp, a refusal and a warning; strictly
narrowing what may build.

## Acceptance

- Python test: stamped-and-different → SystemExit naming the Möbel step;
  stamped-and-equal → loads; unstamped (legacy) → loads.
- bungalow_039 / onehalfstorey_029 / twostorey_030 still build and certify.
- Saving furniture in the Möbel step writes the stamp; the following build
  accepts it.

## Rollback

Revert the five files; unstamped documents keep working either way.

## Approval record

Batch approval, Rainer 2026-08-23 ("do it then"), item 2 of 7.

## Completion record (2026-08-23)

Implemented as scoped, after re-checking the audit's premise against the
code: the Möbel editor and the /haus build already share one geometry
(`geometry_only()` vs `annotation_plan()`, both annotation-derived), so the
"different revision" half of the P0 was already closed by earlier work.
The open half — furniture carrying no record of WHICH drawing it was placed
on — is what this item binds.

- `workbench_furniture()` refuses a document whose `geometry_identity`
  differs from today's drawing, naming the Möbel step as the fix;
  unstamped documents (all existing layouts) keep building.
- The identity is `batch-build.annotation_state()` (drawing + Gebäudemaß,
  deliberately not furniture, so a save cannot chase its own hash),
  imported rather than re-derived.
- `saveFurniture()` stamps it via the one Python oracle; `haus-zustand.py`
  gained a `geometrie` field for that purpose.
- `/haus` now shows the `geometrieFremd` warning the staleness route has
  always computed and never displayed (audit P1).

Tests: 3 new cases (foreign stamp refused / matching stamp builds / legacy
unstamped builds), 17 Python tests green, go.test 4 green, house-state 7
green, tsc clean. (`test:local-floorplan-workbench` fails against a server
on :3020 — a pre-existing integration suite, untouched by this change.)

Verified on the real house: saving onehalfstorey_029's upper-floor
furniture through the API wrote the stamp; `go.py onehalfstorey_029` then
built and certified; corrupting the stamp on disk made the build stop with
"diese Moebel wurden auf einer anderen Zeichnung … gesetzt", and restoring
it let the build through again.

BUG FOUND AND FIXED IN PASSING: `normalizeFurnitureDocument()` drops
unknown fields, so any save from the Möbel editor would have ERASED the
`floor_registration` marker written by yesterday's migration — the next
build would then have demanded the migration again on already-migrated
furniture. The normalizer now carries both markers, and a save stamps
`floor_registration` because the editor draws registered geometry.

Files: `scripts/build-simplifier-render-plan.py`,
`scripts/build-simplifier-render-plan.test.py`, `scripts/haus-zustand.py`,
`src/lib/generator/furniture-document.mjs`,
`src/app/api/floorplan-workbench/corrections/route.ts`,
`src/app/haus/page.tsx`.
