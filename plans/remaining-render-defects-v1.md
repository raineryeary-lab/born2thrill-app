# Remaining render defects — fix plan

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Clear the rest of the broken-items list from
`plans/HANDOFF-2026-08-09-EVENING-START-HERE.md`, now that furniture
orientation is checked and closed (13/14 real-model pieces confirmed
correct against the drawing tonight; corner sofa mirror fix verified;
`sofa_1sitzer` rotation is an annotation value, not code — flagged for you
to fix in the app, not touched here).

## Current evidence and behavior

Carried over from the handoff, each still unverified by this session except
where noted:

| # | Defect | Evidence on file | Status |
|---|---|---|---|
| 1 | 2 openings never cut into a wall | **RESOLVED 2026-08-10**: both are the Carport's open sides (3.4m/3.3m passages); Carport is an excluded room with no walls — nothing to cut. Plan builder now classifies openings inside excluded-room polygons (300mm boundary tolerance) and reports them as intentional, not as errors. Measured: midpoints 2.0m+ from any rendered wall | ✅ done |
| 2 | Door swing ignores the annotation | **VERIFIED WORKING 2026-08-10**: overlay renders (drawing underlay + rendered leaf) confirm 6/7 leaves lie inside their drawn arcs (`tmp/door-overlay-verify*.png`); the annotated swing/hinge values flow annotation → plan JSON → `add_door_leaf` correctly. 7th (f7a23209, Bad) renders at the right opening trending into the correct room but the verification crop is not crisp — re-check when next full render is inspected | ✅ done (1 soft) |
| 3 | Kuechenzeile pushed off its wall | **VERIFIED FIXED 2026-08-10**: the room-centroid fix was already in `_towards_centre` (docstring records it); overlay crop `tmp/kuechenzeile-verify.png` shows the run flush on its wall along the drawn path, hob in place. Units checked: `point_in_polygon` converts m→mm internally | ✅ done |
| 4 | No chair at the desk | 7 chairs catalogued, 0 placed | confirmed tonight — desk itself is correctly placed and oriented; only the chair is missing |
| 5 | 12 of 35 placements are plain white boxes | **RESOLVED 2026-08-10.** Inventory: 4 intended procedural (counter runs/island/Vorwand — already dressed in granite/black), 4 size-mismatch stand-ins (kleiderschrank×2, schrank_40×2), 3 library gaps (garderobe, hochschrank_herd, lowboard), +1 flag lie (fixed earlier today). Carcass boxes for storage types now get thin dark door reveals (~600mm door rhythm, both long faces) in `build_box` — verified on render `tmp/stage1-dollhouse2.png`: wardrobe banks read as cabinetry, no regressions elsewhere | ✅ done |
| 6 | Kitchen has worktops, no cabinet fronts | dressing method agreed, not built | unverified |
| 7 | Windows render as one sheet | `panes` now annotated; renderer ignores it | unverified |

Dropped from the original list, resolved tonight:
- Corner sofa — fixed (`MODEL_MIRROR_Y`), verified twice.
- "Armchair faces wrong" — not a rotation bug; `rotation_deg: 315` is Rainer's
  own stored annotation value. If wrong, it's an app-side data fix, not this
  pipeline.
- 13 other real-model pieces — checked against the drawing, all correct, no
  action needed.

## Repository baselines

`born2thrill-local-workbench` — branch `agent/furnished-render-and-annotation-schema`.
Current dirty state includes tonight's changes: the ecksofa mirror fix and
its comment cleanup in `scripts/render-furnished-dollhouse.py` (net effect:
one small addition, the earlier failed quarter-turn experiment fully
reverted and removed). `floorplan-simplifier` untouched all session.

## Exact scope, in priority order

Priority follows what blocks a usable render fastest, and what's cheapest to
verify wrong before spending time on it.

**1. Openings not cut into walls (#1).** Investigate first — likely a single
threshold constant (`nearest_wall`'s 1200mm rejection). Measure the actual
distance for both failing openings before changing the constant; if they're
just outside 1200mm, that's a data question (is the opening really that far
from any wall, or is wall-matching using the wrong wall's geometry) before
it's a threshold question.

**2. Door swing (#2).** The prior session left `add_door_leaf` parsing
`swing_side`/`hinge_side` but never rendered or checked. First step: render
current state, inventory what all 7 doors actually do now, only then decide
if the "partial fix" is worth finishing or should be redone.

**3. Kuechenzeile off its wall (#3).** `_towards_centre` uses building
centroid — check whether the actual room's own centroid (not the whole
building's) is available and would fix this without a new heuristic.

**4. Dead `preserve_materials` flag (#5, tooling).** Small, mechanical:
either make `build-simplifier-render-plan.py` stop setting
`preserve_materials: true` on items that also get a `build` kind, or make it
clear in the plan schema that `build` always wins. Prevents the next session
from being misled the way tonight's crop tooling was.

**5. Plain white boxes / missing finishes (#5, the real content).** Needs its
own inventory: which of the 12 are missing because no model was matched at
all (library gap) vs. matched but the finish-lifting step was never built.

**6. Kitchen cabinet fronts (#6).** Method already agreed per the handoff;
this is implementation, not investigation.

**7. Window panes (#7).** `panes` is annotated and carried through the
schema already (per the "working, and checked" list) — this is purely the
renderer not reading a field that exists. Should be quick once picked up.

**8. Desk chair (#4).** Lowest priority of what's left — cosmetic completion,
not a correctness bug. Place one of the 7 catalogued chairs near the desk.

## Files in scope

`scripts/build-simplifier-render-plan.py`, `scripts/render-furnished-dollhouse.py`.
No `floorplan-simplifier` changes anticipated; will flag explicitly if one
turns out to be needed (e.g. if #1's root cause is actually in wall-matching
on the Simplifier side).

## Explicitly out of scope

Colour variants, exteriors (roof/facade/front door), ComfyUI polish pass —
these are the "Not started" section of the handoff, a separate and much
larger phase. Not part of this plan.

## Acceptance criteria

Per item: a fresh render showing the fix, compared against the drawing the
same way tonight's furniture check was done (crop pair, or full overlay),
plus the measurement that identified the root cause. No item marked done
without both.

## Tests and verification commands

```bash
python scripts/build-simplifier-render-plan.py bungalow_040_66 modern tmp/plan.json
DMH_UNDERLAY=".../original_preview.png" DMH_TOPVIEW=1 blender --background \
  --python scripts/render-furnished-dollhouse.py -- tmp/plan.json C:/tmp/overlay.png
```

## Protected and risky paths

Same lesson as tonight: no change lands without a before/after render and a
number, not just a claim. After 3 rejected hypotheses on any one item, stop
and hand it to Codex or to you rather than trying a 4th.

## Floorplan-suite invariant

No. `bungalow_040_66` stays `not_for_delivery`, `source:
simplifier_annotations_proof`. Nothing in this plan touches promotion,
export, or email.

## Rollback

Each item is a small, isolated code change; revert per-file if needed. No
data migration.

## Approval record

Not approved. Tell me which item to start on — I'd start with #1 or #2
(openings, door swing) since they're both about wall geometry and might
share a root cause. Or tell me to just go in the order above.
