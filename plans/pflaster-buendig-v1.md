# Außenflächen bündig mit dem Rasen

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22: "something is really off with the exterior blender models" -> "huge slabs of stuff"; choice: **"Flush with the lawn"**.

## Current evidence

- `render-exterior.py` ~3651: on flat ground (`gelaende.art != "hang"`) the lawn is a plane at z = -0.16 m.
- ~3670-3673: terrace/path/driveway/garden are flat polygons WITHOUT sides at z = 0.001-0.016 m -> they hover 16-17 cm above the lawn and cast a shadow underneath (vv2 render 2026-10-22).
- Hang houses use `base_z_m` per area on the terrain mesh -- correct, untouched.

## Exact scope

1. Pure `flaechen_z(typ, art, base_z_m)` in render-exterior.py: flat ground -> RASEN_Z (-0.16) + the existing stacking offset (1-16 mm, so overlapping areas don't flicker); hang -> unchanged (base_z_m + offset).
2. The area loop uses it. Nothing else changes (house, plinth, lawn).

## Tests (first)

`scripts/pflaster_buendig.test.py` (AST-load): eben terrasse -> -0.16 + 0.016; eben garten -> -0.16 + 0.001; hang -> base + offset; seam check.
Real: vv2 exterior rebuild; look at it -- paving lies in the lawn, no floating shadow.

## Rollback

`render-exterior.py.before-pflaster`.

## Approval record

Rainer in chat, 2026-10-22: answer "Flush with the lawn (Recommended)" to "How should terrace, path and driveway sit on the ground?".

## Implementation record (2026-10-22)

- `RASEN_Z`, `flaechen_z()` in render-exterior.py; lawn plane and area loop use them.
- Tests first: pflaster_buendig.test.py 4 (red before, green after); hanggelaende and exterior_registration green.
- vv2: scratch render looked at (paving lies in the lawn, no shadow gap); full rebuild see below.
