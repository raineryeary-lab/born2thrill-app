# Interior studio background rule

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make the furnished 2D-to-3D floorplan presentation permanently use a clean white studio ground/background with soft contact shadows and no exterior environment.

## Current evidence and behavior

The saved ground-floor Blender scene contains a `ground` mesh and an opaque world. The current direct render can still visually read as an exterior site/environment. The user-provided reference establishes the required isolated dollhouse presentation.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Existing worktree is dirty and contains user-owned modified and untracked files. They must remain untouched except for the approved in-scope files.

## Exact scope

- Add an explicit interior-only studio-presentation rule.
- Enforce a neutral white ground and camera-visible white/light-neutral world.
- Preserve soft ambient/contact shadows.
- Suppress all landscape, garden, driveway, path, terrain, sky scenery and exterior-site objects in interior dollhouse renders.
- Re-render only the `onehalfstorey_020` ground and upper floor for review.

## Files in scope

- `scripts/render-furnished-dollhouse.py`
- `scripts/furniture-document.test.mjs` or one new focused render-rule test
- `docs/RENDER-WORKFLOW.md`
- Versioned review PNGs under `exports/onehalfstorey_020-exact-blender-2026-08-17/`

## Explicitly out of scope

- Floorplan geometry, room polygons, walls, openings, stairs, cameras, furniture placement and object selection.
- Exterior renders and their landscaping.
- Other interior finish variants.
- Database, WordPress, email, deployment and customer delivery.

## API, schema, and data-contract effects

None. This changes presentation only.

## Acceptance criteria

1. Ground-floor and upper-floor images retain the exact saved geometry, camera and furniture placement.
2. The visible ground/background is white or very light neutral.
3. Soft contact shadows remain visible under walls and furniture.
4. No garden, grass, plants, driveway, path, terrain, horizon or outdoor environment is visible.
5. Exterior-render behavior remains unchanged.
6. The rule is documented as a persistent default, not a per-render prompt preference.

## Tests and verification commands

- Add a focused test that asserts the interior studio rule disables exterior-site collections/objects and configures opaque neutral background plus shadow-catching ground.
- Run the focused test.
- Render both supplied interior Blender scenes.
- Visually verify geometry/furniture identity and studio background.

## Protected and risky paths

- Do not modify the four source `.blend` files.
- Do not overwrite prior PNGs; create versioned replacements.
- Preserve all unrelated dirty-worktree changes.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. The change is presentation-only and cannot alter or publish geometry.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

None.

## Rollback

Revert the isolated studio-environment logic and remove only the new versioned review PNGs.

## Unresolved questions

None.

## Approval record

Not approved. Stop before implementation.
