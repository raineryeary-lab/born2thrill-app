# Batch canonical promotion v1

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Convert the complete current saved Simplifier corpus in one deterministic batch into a current privacy-safe export and canonical-readiness report without changing original annotations.

## Current evidence and behavior

The checked-in handoff contains 160 projects while the live Simplifier contains 356 saved annotation files. The generator is reading a stale partial handoff.

## Repository baselines

C:\dev\born2thrill-local-workbench on agent/zuhausefinder-generator; dirty user-owned worktree preserved. Source corpus under the Simplifier runtime projects directory is immutable.

## Exact scope

Add tests and a batch audit command around the existing exporter; export every currently eligible saved project; account for every project as included or excluded with an exact reason; classify scale and canonical readiness; keep publication and delivery blocked.

## Files in scope

scripts/batch-canonical-promotion.mjs
scripts/batch-canonical-promotion.test.mjs
package.json
data/simplifier-v2/
plans/batch-canonical-promotion-v1.md
canonical roadmap status entry

## Explicitly out of scope

Source mutation, guessed dimensions, automatic commercial-rights approval, WordPress deployment, email, database changes, free generation, image generation, renderer/routes/UI changes.

## API, schema, and data-contract effects

Adds a local batch-report contract only. Existing runtime APIs remain unchanged.

## Acceptance criteria

Every project directory is accounted for exactly once. The current saved corpus is used. Every exclusion has a stable reason code. Source files remain unchanged. No output is WordPress-eligible or externally deliverable.

## Tests and verification commands

Synthetic tests cover missing files, draft status, empty floors, unassigned rooms, denied rights, and valid reviewed/training-ready plans. Run focused tests, existing importer/candidate tests, lint, type-check, live batch, and total reconciliation.

## Protected and risky paths

The complete Simplifier projects tree is read-only. Preserve all pre-existing changes.

## Rights, provenance, privacy, and security impact

Raw PDFs/previews and customer data remain excluded. Editing/import does not itself create commercial eligibility. Explicit rights and approvals are preserved.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. This path produces local audit/export data only and blocks publication and delivery.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

None.

## Rollback

Remove only the new script, test, plan, package command, and generated data/simplifier-v2 directory. Original annotations remain untouched.

## Unresolved questions

Plans without authoritative dimensions remain in the repair queue and receive no guessed scale.

## Approval record

Approved by the user on 2026-08-02 with direct instructions to run the complete batch now without one-by-one processing.