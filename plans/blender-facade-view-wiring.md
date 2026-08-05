# Blender Façade View Wiring

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make the Workbench façade selection control the deterministic Blender camera and produce view-specific artifacts, then regenerate the garden-side proof.

## Current evidence and behavior

- The UI stores `garden|street|east|west` but POST sends only action and document.
- The correction API does not accept a render view.
- The Blender exporter hard-codes one camera at `(14, -16, 12)`.
- The resulting garden-labelled render showed the entrance/street façade.

## Repository baselines

- Repository: `C:\dev\born2thrill-local-workbench`
- Branch: `agent/zuhausefinder-generator`
- Base SHA: `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`
- Existing dirty and untracked Workbench/corpus changes are user-owned and must be preserved.

## Exact scope

1. Add render-view acceptance tests first.
2. Allowlist `garden|street|east|west` in the Blender manifest builder.
3. Send the selected view from the UI to the local corrections endpoint.
4. Use that view to choose a deterministic Blender camera around the same canonical geometry.
5. Save view-specific PNG/BLEND/manifest files under the existing geometry-hash directory.
6. Rerender the garden guide and create one corrected photorealistic proof.

## Files in scope

- `scripts/blender-export.test.mjs`
- `src/lib/generator/blender-scene-manifest.mjs`
- `src/app/floorplan-workbench/page.tsx`
- `src/app/api/floorplan-workbench/corrections/route.ts`
- `scripts/export-floorplan-blender.py`
- `C:\dev\born2thrill-app-repo\plans\ROADMAP.md` (tracking only)
- View-specific derived artifacts under the existing local Workbench data geometry-hash directory.

## Explicitly out of scope

Geometry changes, room/window/door redesign, rights reclassification, WordPress, customer email, deployment, database changes, or automatic publication.

## API, schema, and data-contract effects

Local POST gains allowlisted `view`. Blender manifest gains `render_view`. Geometry hash remains unchanged because camera choice is presentation metadata, not geometry.

## Acceptance criteria

- Selected garden view reaches the Blender manifest and exporter.
- Unsupported view is rejected.
- Garden and street cameras are opposite views of the same geometry.
- Output filenames include the view and never overwrite another view.
- Blender metadata records geometry hash and render view.
- UI labels the rendered view.
- Existing geometry and rights gates remain unchanged.

## Tests and verification commands

- Extend `scripts/blender-export.test.mjs` for allowed/rejected views and metadata.
- `node --test scripts\blender-export.test.mjs`
- `.\node_modules\.bin\tsc.cmd --noEmit --pretty false`
- `git diff --check`

## Protected and risky paths

All source annotations, prior revisions, corpus data, rights metadata, credentials, WordPress, customer data, and unrelated dirty files.

## Rights, provenance, privacy, and security impact

None. Derived artifacts remain internal review only and linked to the same geometry hash.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. The change only selects a camera for the already validated canonical document; it does not publish or email anything.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

None.

## Rollback

Revert only the named files and remove only the newly generated view-specific artifacts after validating their exact paths.

## Unresolved questions

None blocking.

## Approval record

Approved by the user after the façade-wiring proposal: “ok how do we do that?” followed by “ok just marking something as wrong doesn’t fix it”.

