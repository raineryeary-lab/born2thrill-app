# Extract usable parts (worktops, door fronts) from the big furniture sets

Status: SUPERSEDED (partially) — step 1 (the classification render) was run
and confirmed correct by Rainer looking at the actual picture: the
height/thinness rule correctly separates door/drawer fronts from
countertops. But Rainer then redirected the OBJECTIVE this plan serves: at
final dollhouse-cutaway render distance, extracting and classifying precise
GEOMETRY across 13 files/~1040 objects (steps 2-4 below) is more than the
end render will ever show. What's actually needed is a door-front MATERIAL
and a countertop MATERIAL applied to the procedural cabinet/counter shapes
`render-furnished-dollhouse.py` already builds (`build_path_run`,
`build_rect`, already using `GRANITE_MAT` for counters) — not new imported
geometry. Steps 2-4 below are not being done as written. Follow-up work is
the materials-only version, not yet its own plan document.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer's own words: "we agreed on using the door fronts and countertops of
the kitchens." The 13 large set files (Kitchen Furniture Set 1 alone holds
187 objects) have never had their individual parts identified — only
counted. This plan is how to actually identify which objects are worktops,
which are door fronts, and which are the room shell around them, so those
parts become usable, without another guessed threshold.

## Why the catalog fix from tonight isn't enough by itself

The catalog no longer deletes anything and no longer treats "wide" as
suspect — correct, but it also means nothing is classified yet. `Kitchen
Furniture Set 1` still reports 188 undifferentiated objects. Knowing a
countertop is *supposed* to be wide (Rainer's correction, applied) doesn't
by itself say which of the 188 objects the countertop actually is.

## What was checked tonight, read-only, no classifier written

Object names carry no semantic information — every object in Kitchen
Furniture Set 1 is named like `cgaxis_models_86_01_03_2`, nothing like
"worktop" or "door". Name matching is not viable for this library.

Height off the floor (Z) does show a pattern, from one file, unverified
beyond this:

| Z range | thinness | plausible role |
|---|---|---|
| 1–151mm | thin (150mm) | plinth/kickboard, floor-level |
| 152–811mm, box-shaped (~900×450×160mm) | not thin | cabinet carcasses |
| 152–811mm, ~900×20mm | thin (20mm) | door fronts (plausible) |
| 814–844mm, thin (30mm), wide (1830–2618mm) | thin | worktop (plausible — this is standard counter height) |
| 1977–2210mm, thin (~46mm) | thin | wall-unit tops / cornice |

This is one file, eyeballed. It is a hypothesis, not a rule — exactly the
kind of thing that needs testing against a rendered picture before it
governs 13 files and ~1040 objects, per tonight's whole lesson.

## Exact scope

1. **Render one set (Kitchen Furniture Set 1) with objects colour-coded by
   the height/thinness buckets above**, top-down and a side elevation.
   Compare against what a kitchen actually looks like. This either confirms
   the pattern or breaks it immediately and cheaply — one render, before any
   rule is trusted.
2. **If confirmed:** turn it into a classifier function (height range +
   thinness + footprint), run it across all 13 sets, and produce a per-set
   report: N worktop candidates, N door-front candidates, N carcass, N
   shell/plinth, N unclassified. Unclassified stays unclassified — no
   catch-all bucket that silently mislabels something.
3. **If not confirmed**, or for whatever fraction doesn't fit the pattern:
   fall back to Rainer looking at a render of the flagged objects and naming
   them by hand for at least one set, so the classifier has real ground
   truth instead of a second guess.
4. **Only after classification**, decide what "extracted" means concretely
   — new standalone `.blend` files per part, or just catalog entries marking
   which existing object indices are worktop/door-front so the render
   pipeline can pick them out of the whole set without duplicating files.
   Not decided yet; needs your call before it's built either way.

## Files in scope

New script (name TBD, e.g. `scripts/classify-set-parts.py`), read-only
against the Hub library. `tmp/hub-model-catalog.json` gains classification
data only after step 2 is confirmed — not before.

## Explicitly out of scope

Placing these parts in an actual room. This plan stops at "identified and
catalogued," not "in the render."

## Acceptance criteria

Step 1's render is judged by you, not by me — I don't mark this confirmed
on my own read of a colour-coded picture.

## Tests and verification commands

```bash
blender --background --python scripts/classify-set-parts.py -- \
  "E:\_models_hub\_extracted\Kitchen_Furniture_Set_1_BLEND\Kitchen Furniture Set 1.blend" \
  tmp/kfs1-classified-render.png
```

## Protected and risky paths

None yet — this plan is entirely read-only investigation and one render
until step 2 is confirmed.

## Floorplan-suite invariant

No. Library classification only; nothing customer-facing.

## Rollback

N/A — no destructive step in this plan.

## Approval record

Step 1 approved and done (render sent, Rainer confirmed the classification
was visually correct). Steps 2-4 superseded by Rainer's redirect toward a
materials-only approach — see Status above. Not resumed as originally
written.
