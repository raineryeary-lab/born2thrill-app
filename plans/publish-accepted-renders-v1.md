# Publish accepted renders to the ZuhauseFinder WordPress site

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Let the images Rainer has ACCEPTED in the overview reach the WordPress site,
without weakening the manual gate and without any push, credential or upload.

## Current evidence and behavior

- WordPress does not receive an upload. It **pulls**:
  `POST /api/zuhausefinder/floorplan` takes a questionnaire brief and returns
  JSON containing the plan JPEG and a guide PNG as **base64 in the response**
  (`route.ts` lines ~170 and ~205, `reference_images`).
- `reference_images` today carries exactly one entry, role
  `plan_geometry_guide`. Codex's rendered interiors/exteriors never reach it.
- The response already carries `manual_review_required`, driven by
  `customerReady` and `corrected.wordpressEligible`.
- Acceptance now exists and is recorded per image: `review.json`
  (`dmh-image-review-v1`) sits next to `catalog.json` in the delivery folder,
  written by the overview's Accept / Changes controls (built 2026-08-18).
- So the missing link is only: read `review.json` + `catalog.json` for the
  matched plan and add the accepted images to `reference_images`.

## Exact scope

1. A reader that, given a plan family / geometry hash, finds the delivery
   folder, loads `catalog.json` and `review.json`, and returns only assets
   whose verdict is `accepted`.
2. Extend `reference_images` with those assets (role from the catalogue's
   `asset_type`, plus `description_de`, `sha256`, and the `geometry_source`
   the catalogue already records).
3. Hard cap on count and total bytes so one response cannot balloon.

## Files in scope

- `src/app/api/zuhausefinder/floorplan/route.ts` (extend `reference_images`)
- new `src/lib/generator/accepted-renders.mjs` (reader + filter)
- new `scripts/accepted-renders.test.mjs`

## Explicitly out of scope

- Any push, POST, FTP or REST call TO WordPress. Nothing is uploaded.
- Any credential, token or new external endpoint.
- The manual email gate; `manual_review_required` logic is untouched.
- Writing, editing or approving `catalog.json` / `review.json`.
- Geometry, plans, revisions, the correction workflow, the renderers.

## API, schema, and data-contract effects

- `reference_images[]` gains entries. Existing consumers read it as a list and
  the `plan_geometry_guide` entry keeps its position and shape.
- No schema version bump needed; additive only.

## Acceptance criteria

- An image with no verdict, or verdict `changes_requested`, is NEVER returned.
- An accepted image is returned only when its catalogue entry's
  `geometry_source` resolves to a real `.blend` in the delivery folder.
- `manual_review_required` behaviour is unchanged, byte for byte, for a brief
  that has no accepted renders.
- Response stays under the existing size guard.

## Tests and verification commands

New `scripts/accepted-renders.test.mjs`:
- accepted-only filtering (accepted / changes_requested / missing verdict)
- refuses an entry whose `geometry_source` is absent
- byte and count caps enforced
- path-escape refusal on catalogue-supplied filenames

Run: `node --test scripts/accepted-renders.test.mjs`
plus the existing suite: `node --test scripts/*.test.mjs`

## Protected and risky paths

- `route.ts` is the live customer-facing endpoint. The change is additive and
  guarded; the existing early-return paths are not reordered.
- Catalogue filenames come from Codex, i.e. from outside this code: every one
  is treated as untrusted and resolved against the delivery folder only.

## Suite safety gate

> Can any changed path generate, publish, or email geometry without matching an
> approved corrected corpus reference?

**No.** The reader only surfaces images that (a) a human accepted in the
overview and (b) whose catalogue entry points at a `.blend` built from the
approved corrected revision. It adds nothing to the response for a plan that is
not already being returned, and it does not touch `manual_review_required` or
the email gate.

## Rollback

Delete `accepted-renders.mjs` and revert the single `reference_images` block in
`route.ts`. No data, schema or external state is changed by this task.
