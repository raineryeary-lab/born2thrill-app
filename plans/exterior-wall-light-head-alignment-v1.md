# Exterior wall-light head alignment

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make facade wall-light height deterministic: the horizontal centreline of each wall-light fixture must equal the top/head elevation of its associated exterior door or window.

## Current evidence and behavior

`scripts/comfyui-polish-exterior.py` contains exterior style and landscaping prompt rules but no wall-light placement rule. Image generation therefore improvises fixture height.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Pre-existing tracked change: `scripts/build-simplifier-render-plan.py`
- Pre-existing untracked paths: `scripts/bpypolyskel/`, `scripts/comfyui-polish-exterior.py`, `scripts/composite-mask-polish.py`, `scripts/render-exterior.py`
- These pre-existing changes remain preserved.

## Exact scope

Add one reusable exterior-light rule and require the exterior prompt builder to include it. The rule is numerical and unambiguous:

- `fixture_center_z_mm = associated_opening_head_z_mm`
- lamp body remains laterally beside the opening on solid facade
- never above the opening head, beneath the eaves, or at handle/mid-window height
- if no associated opening/head elevation exists, omit the decorative light instead of guessing

## Files in scope

- `scripts/comfyui-polish-exterior.py`
- one focused prompt/rule regression test under `scripts/`
- `plans/ROADMAP.md` only if required for follow-up tracking

## Explicitly out of scope

Building/opening geometry, Blender camera, cars, landscaping, WordPress, email, database, deployment, and customer delivery.

## API, schema, and data-contract effects

None. Prompt contract only.

## Acceptance criteria

1. Exterior prompt includes the exact centreline-to-opening-head rule.
2. The rule explicitly prohibits mounting above the frame or at handle/mid-window height.
3. Missing opening-head data produces omission, not a guessed height.
4. A regression test fails if any of these clauses disappear.
5. Current V23 image is regenerated using the rule and visually reviewed; it is not called correct unless lamp centres align with the visible frame-head datum.

## Tests and verification commands

- Add a focused test that loads the exterior prompt definition and asserts the three rule clauses.
- Run that test and Python syntax compilation.
- Existing tests are not changed, skipped, weakened, or deleted.

## Protected and risky paths

Do not overwrite the V23 Blender source or earlier renders. Save a new versioned output.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

No changed path can generate, publish, or email geometry. This change only constrains decorative light placement in the exterior polish prompt.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. Repeated natural-language image edits would reliably reposition lights. Result: the image editor left them too low or moved them above the frames. Conclusion: placement must be a persistent measurable pipeline rule and verified before acceptance.

## Rollback

Revert only the prompt-rule and focused test changes; retain all prior user work and generated versions.

## Unresolved questions

None. The user explicitly defined the datum as the top of doors/windows, not above them.

## Approval record

Not approved. Stop before implementation.
