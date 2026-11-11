# 3D-Vorschau von aussen vor dem Bau

Status: IMPLEMENTED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-03: "WOULD IT BE SUPER HARD TO DO A 3D PREVIEW OF SOME SORT of the outside before we really go into the build?" -- chose option 2: the real builder without render, exported as GLB, shown rotatable in the workbench.

## Current evidence and behavior

- Workbench only had a generic SVG massing (`floorplan-workbench/page.tsx:86`) and single Blender stills.
- `render-exterior.py` builds the full exterior scene, then renders at the first `bpy.ops.render.render(`.

## Baseline

Git HEAD `5be1a4e`, 640 dirty/untracked entries before this task (user-owned, untouched). Backups `*.before-vorschau-3d` of render-exterior.py, haus/page.tsx, package.json, package-lock.json.

## Exact scope

- `scripts/render-exterior.py`: `EXT_GLTF_OUT` switch right before the render setup -- exports GLB and exits; no PNG, no .blend, no camera file.
- `scripts/vorschau-3d.py`: plan (style "modern") + Blender with that switch; output `<data>/vorschau-3d/<id>/<dach>.glb` and `vorschau.json`.
- `src/app/api/floorplan-workbench/vorschau-3d/route.ts`: GET info/GLB, POST build. Local-only guard as other routes.
- `src/app/vorschau-3d/page.tsx`: three.js viewer (orbit, roof buttons, rebuild), neutral grey background.
- `src/app/haus/page.tsx`: link "3D-Vorschau" next to "Bauen".
- Dependency: `three@0.170.0`, dev `@types/three@0.170.0`.

## Explicitly out of scope

Interiors, materials beyond what the exterior scene carries, the real build/delivery, annotator integration.

## Acceptance criteria

Preview geometry equals the built exterior: measured on twostorey_xvv4 walmdach -- built .blend (2026-10-31) and preview GLB both 156 meshes, same roof objects, ridge 8.333 m.

## Tests and verification commands

`python scripts/vorschau-3d.test.py` (roof choice, switch before render/save). Exterior-related Python tests all OK; `npx tsc --noEmit` 0 errors; browser check /vorschau-3d?plan=twostorey_xvv4.

## Protected local data and risky paths

Writes only `<data>/vorschau-3d/`. Never go-baseline, renders, deliveries.

## Rights, provenance, privacy, and security impact

None; local-only route.

## Floorplan-suite invariant

No. Preview files are not published, uploaded or emailed.

## External effects

npm registry download of three.js.

## Failed-hypothesis log

## Rollback

Restore the `.before-vorschau-3d` copies, `npm install`, delete the new script, test, route and page, and `<data>/vorschau-3d/`.

## Approval record

Rainer, 2026-11-03: "2".
