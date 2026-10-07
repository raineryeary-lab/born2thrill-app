# Kitchen inspect reference-style render

Status: COMPLETE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Render `tmp/kitchen-inspect.blend` in the clean isometric cutaway style of `C:\Users\Admin\Downloads\persp_v8-marked.png`, ignoring its red review markup.

## Current evidence and behavior

The Blender source exists, is 331,870,323 bytes, and Blender 5.0 is installed.

## Repository baselines

Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`. Preserve all existing dirty and untracked work.

## Exact scope

Read the saved scene, preserve its geometry and object placement, use its saved camera when suitable, and create one new versioned PNG with white/light-grey walls, warm natural wood, restrained grey surfaces, soft neutral lighting, ambient contact shadows, and clean isometric presentation.

## Files in scope

- Read only: `tmp/kitchen-inspect.blend`
- New artifact: `tmp/kitchen-inspect-reference-style-v1.png`

## Explicitly out of scope

No source `.blend` overwrite, geometry edits, furniture movement, floorplan changes, code changes, database, WordPress, email, or deployment.

## API, schema, and data-contract effects

None.

## Acceptance criteria

1. PNG renders successfully and is visually inspectable.
2. Geometry and furnishing placement match the Blender source.
3. Style resembles the reference without reproducing red annotations.
4. No source file is modified.

## Tests and verification commands

Verify file timestamps, Blender exit code, PNG dimensions, and inspect the rendered image.

## Protected and risky paths

The 332 MB `.blend` is read-only and must not be saved or overwritten.

## Rights, provenance, privacy, and security impact

None identified; local user-provided source and reference only.

## Floorplan-suite invariant

No changed path can generate, publish, or email geometry. This is a local preview render only.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

None.

## Rollback

Delete only the new versioned PNG.

## Unresolved questions

None; fall back to the saved camera and neutral isometric settings if the scene lacks a complete render setup.

## Approval record

Approved by the user on 2026-08-16: “approved”. Render completed successfully with the saved EEVEE scene and camera; source `.blend` was not overwritten.
