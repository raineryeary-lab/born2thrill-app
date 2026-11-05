# Move furniture out of the annotator into the workbench (workbench half)

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

The canonical plan lives in
`C:\dev\Floorplan-tools\floorplan-simplifier\plans\move-furniture-to-workbench.md`
— scope, acceptance criteria, tests, rollback, and the suite invariant are all
recorded there, for both repositories. This file exists so the workbench's own
plans directory points at it rather than holding a second copy that can drift.

Workbench half in one paragraph: the Simplifier annotator becomes 2D geometry
only and keeps no 3D asset references at all. Furniture editing lands here on
top of the existing tested placement engine
(`src/lib/generator/furniture-placement.mjs`) as a manual **override layer**
stored in the workbench data root and consumed by
`scripts/build-furnished-render-plan.mjs`. `bungalow_040_66`'s 35 hand-placed
annotator symbols — the only ones in all 234 projects — are migrated by a new
`scripts/import-annotator-symbols.mjs`.

Not approved. Stop before implementation.
