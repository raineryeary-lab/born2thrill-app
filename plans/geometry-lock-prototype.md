# Geometry Lock Prototype

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Turn one approved 1.5-storey canonical plan into a deterministic geometry-lock prototype: explainable physical-facade selection, real Blender wall openings and gable roof, and a tested 28–45 degree oblique camera.

## Current evidence and behavior

The canonical plan contains exterior wall linkage, main-entrance and terrace-door roles. Current Blender output uses solid wall boxes, wire opening markers, a flat roof placeholder and arbitrary named camera quadrants.

## Repository baselines

- Repository: `C:\dev\born2thrill-local-workbench`
- Branch: `agent/zuhausefinder-generator`
- Base SHA: `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`
- Preserve the substantial existing dirty/untracked user work.
- Canonical roadmap: `C:\dev\born2thrill-app-repo\plans\ROADMAP.md`.

## Exact scope

1. Add façade-analysis and Blender acceptance tests first.
2. Group physical exterior façades from canonical walls and footprint.
3. Score garden/street/visual evidence from terrace door, main entrance, glazing, balance and alignment.
4. Store score breakdown, selected physical façade, adjacent side and 35-degree camera contract.
5. Preserve opening roles, connections and wall semantics in the Blender manifest.
6. Replace wire-only openings with actual wall voids and simple deterministic frame/door/glazing assemblies.
7. Replace the flat roof placeholder with a deterministic gable roof mesh.
8. Render the selected façade at 35 degrees, constrained to 28–45 degrees, and store camera/render metadata.
9. Produce one local garden-side deterministic proof. No WordPress or customer delivery.

## Files in scope

- `src/lib/generator/facade-analysis.mjs` and declaration
- `scripts/facade-analysis.test.mjs`
- `src/lib/generator/blender-scene-manifest.mjs` and declaration
- `scripts/blender-export.test.mjs`
- `scripts/export-floorplan-blender.py`
- `src/app/api/floorplan-workbench/corrections/route.ts`
- `src/app/floorplan-workbench/page.tsx`
- `package.json` only if adding the focused test command
- Canonical roadmap tracking only
- View-specific derived artifacts under the existing local Workbench data directory

## Explicitly out of scope

Changing canonical floorplan geometry, creative variants, rights changes, WordPress, email, deployment, database changes, customer delivery, or broad corpus conversion.

## API, schema, and data-contract effects

Blender manifest gains derived façade analysis, preserved opening semantics, roof geometry parameters and camera contract. Geometry hash remains unchanged; camera/presentation metadata receives its own deterministic identity.

## Acceptance criteria

- Terrace-door façade is identified as garden and main-entrance façade as street.
- Every candidate façade has explainable metrics and score components.
- Camera angle is 35 degrees by default and rejects values outside 28–45 degrees.
- Left/right oblique choice follows adjacent-facade score with stable tie-breaking.
- Blender produces actual voids/assemblies for canonical openings.
- Blender produces a gable roof, not a rectangular roof block.
- Manifest, Blender metadata and artifact retain the source geometry hash.
- No output becomes WordPress/customer eligible.

## Tests and verification commands

- `node --test scripts\facade-analysis.test.mjs`
- `node --test scripts\blender-export.test.mjs`
- `.\node_modules\.bin\tsc.cmd --noEmit --pretty false`
- `git diff --check`

Existing tests remain intact and are only extended with new invariants.

## Protected and risky paths

All annotations, source assets, previous revisions, corpus files, credentials, customer data, WordPress, Railway, backups and unrelated dirty files.

## Rights, provenance, privacy, and security impact

None. The selected fixture remains internal review only. Derived artifacts remain local and traceable to the same geometry hash.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Rendering still requires the validated canonical document and remains local-only; publication and email are untouched.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

None at approval.

## Rollback

Revert only named files and remove only newly created view-specific derived artifacts after exact path verification.

## Unresolved questions

Conditioning depth/normal/semantic passes and automated post-generation comparison remain the next separate milestone after this visible geometry lock.

## Approval record

Approved explicitly by the user on 2026-08-01: “Approved—build the geometry lock.”

