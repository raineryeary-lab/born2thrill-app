# Current Simplifier batch handoff

Status: COMPLETE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective
Connect the main generator's internal reference selector to the validated current 310-plan Simplifier v2 handoff.

## Current evidence and behavior
The main generator imports stale simplifier-v1 data. The validated v2 handoff contains 310 exportable plans, 295 quality-passed, and machine-readable exclusions for all other source folders.

## Repository baselines
C:\dev\born2thrill-app-repo, branch fix/customer-floorplan-output, base cbd4be4480aafc775ea390e3b1991eede9672fef. Preserve all pre-existing changes and untracked files.

## Exact scope
Import the validated v2 handoff, switch only the internal Simplifier reference module to v2, add a regression test, and verify generator/storey tests. No commercial approval is added.

## Files in scope
data/simplifier-v2/
src/lib/training/simplifier-reference.ts
scripts/current-corpus-handoff.test.mjs
plans/current-simplifier-batch-handoff.md
plans/ROADMAP.md

## Explicitly out of scope
Canonical millimetre reconstruction, approval, deployment, WordPress changes, email, image API, DB changes, and free generation.

## API, schema, and data-contract effects
The internal candidate pool grows from the stale v1 snapshot to the validated v2 snapshot. Public response schemas are unchanged.

## Acceptance criteria
The imported handoff passes existing dataset/ledger validators. The main selector imports v2. At least 295 quality-passed references exist across bungalow, 1.5-storey, and 2-storey groups. Non-passing plans remain ineligible. No v2 plan is granted commercial eligibility without unchanged prior explicit approval.

## Tests and verification commands
Add current-corpus-handoff.test.mjs first. Run it failing against v1, then pass after import/switch. Run importer, storey-model, generator tests, type-check, and diff check.

## Protected and risky paths
Do not overwrite v1, approved canonical catalogue, fixtures, deployment config, or unrelated dirty files.

## Rights, provenance, privacy, and security impact
The v2 handoff excludes raw assets/customer data. Newly changed records remain internal_reference_only. Customer delivery still requires a separately approved canonical package.

## Floorplan-suite invariant
Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. This only expands the internal reference pool; commercial/customer eligibility remains guarded by the approved canonical catalogue.

## Customer, email, database, deployment, and external effects
None.

## Rollback
Revert the three v2 import paths and remove data/simplifier-v2 plus the focused test/plan. v1 remains intact.

## Approval record
Approved by the user on 2026-08-02 through repeated direct instructions to batch-connect all current annotated floorplans now.