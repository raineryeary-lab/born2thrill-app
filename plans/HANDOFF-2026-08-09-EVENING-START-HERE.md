# START HERE — furnished render pipeline, 2026-08-09 evening

Read `plans/WORKING-PROTOCOL.md` first. It was written by Codex after a day in
which I repeatedly used heuristics where the user's data already held the
answer, and repeatedly claimed fixes without verifying them. It is not advice;
follow it.

The single rule underneath everything here, in Rainer's words:

> **The annotation is the authority. A rule applies only where he has set
> nothing.**

Every significant failure today was a violation of that rule.

---

## Do this first

**The corner sofa renders as a straight sofa. Rainer's symbol clearly draws an
L.** This has been outstanding since the morning and I never once opened the
model to look at it. Four separate root causes were proposed and all four were
wrong.

Do it in this order and do not skip a step:

1. Open `E:\_models_hub\_extracted\cgaxis_grey_corner_modern_sofa_blender\...blend`
   and list every mesh object with its measured size.
2. Open `floorplan-simplifier/static/symbols/ecksofa.svg` and look at what he
   drew — an L, and which way it opens.
3. Establish whether the L exists in the geometry, or is being removed
   somewhere in the pipeline (the shell filter in `import_model` is a
   candidate: it deletes objects larger than 2x the target footprint).
4. Only then change code.

Do not propose a cause without a measurement that distinguishes it from the
alternatives.

---

## Verified state

Both variants render:

```bash
python scripts/build-simplifier-render-plan.py bungalow_040_66 modern tmp/plan.json
"/c/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
  --python scripts/render-furnished-dollhouse.py -- tmp/plan.json C:/tmp/out.png
```

Overlay on the source drawing — **use this before judging anything**:

```bash
DMH_UNDERLAY="C:/dev/Floorplan-tools/floorplan-simplifier/projects/bungalow_040_66/original_preview.png" \
DMH_TOPVIEW=1 blender --background --python scripts/render-furnished-dollhouse.py -- tmp/plan.json C:/tmp/overlay.png
```

Scene inventory by size, for finding a wrong object rather than guessing:
`DMH_INVENTORY=1`.

### Working, and checked

- Tilted cutaway, 500 mm front to 2000 mm back. Frames 70 x 70 mm, white, doors
  and windows only.
- `.blend` import with per-model scale divisors.
- 23 of 35 placements are real CGAxis models with their own materials.
- Rainer's 10 measured footprints drive sizes and outrank model dimensions.
- Glass is alpha-blended and reads as glass.
- Right-click no longer deletes. Verified on doors, windows and symbols, on both
  tabs: no prompt, nothing removed, correct menu opens.
- Window pane menu: 1 / 2 / 3 Fluegel, persisted through `normalize_element`,
  round-tripped through the server.
- Symbol resize handles: drag a corner to measure, Shift for uniform. Verified
  600 -> 1178 mm exactly.

### Broken, with counts

| Defect | Evidence |
|---|---|
| Corner sofa renders straight, not L | see above |
| Armchair faces wrong, no style coordination | white chair against grey sofa |
| Desk not against the wall, no chair placed | 7 chairs catalogued, 0 placed |
| 2 openings never cut into a wall | both at x 0.07-0.24; `nearest_wall` rejects beyond 1200 mm |
| Door swing ignores the annotation | 7/7 doors carry `swing_side`; a partial fix was in progress and is UNVERIFIED |
| Kuechenzeile pushed off its wall | `_towards_centre` uses the building centroid |
| 12 of 35 placements are plain white boxes | no finishes lifted from real models |
| Kitchen has worktops, no cabinet fronts | dressing method agreed, not built |
| Windows render as one sheet | `panes` now annotated; renderer ignores it |

---

## The thing I got most wrong

**1040 usable parts sit inside 13 set files I never opened.** Kitchen Furniture
Set 1 alone holds 187 objects.

I told Rainer four separate times that a model type was missing from his
library. Every time it was there: shower cabins, the corner bath, the stove, the
vanity unit. The last two are inside those sets. I catalogued that the sets
existed, wrote up the method for breaking them down, and then said "no stove
exists" without opening the file.

**Do not claim anything is missing until the sets are enumerated.**

`tmp/hub-model-catalog.json` already lists every part with its size. Start
there.

---

## Also unverified

- `add_door_leaf` was mid-edit to read `swing_side` / `hinge_side`. The code
  parses; it has never been rendered or checked. Treat as unfinished.
- Rainer's browser save failed once after a server restart while ten earlier
  saves worked. Never diagnosed. Confirm a save reaches
  `projects/bungalow_040_66/annotations.json` before trusting it.
- `White Modern Sofa 13` and `Bathroom Furniture Set` resolve to no scale.
- The grey corner sofa's recorded size (3524 mm) was measured after the
  cataloguer silently discarded an object over 100 m. Its divisor of 1.0 is not
  trustworthy.

---

## Not started

Four colour variants, the two exteriors (classic and modern), and the ComfyUI
polish pass. ComfyUI is at `E:\_comfyUI\ComfyUI\ComfyUI` with RealVisXL V5 and
an SDXL canny ControlNet; a depth ControlNet is missing. Every render should
write depth and edge passes for it.

Agreed division of labour, and it matters:

- **Real geometry:** walls, openings, room shapes, fixed fittings. Claims about
  the property.
- **Real, for a different reason:** bed, sofa, dining set, wardrobe. They prove
  the room works at that size. An image model will shrink a bed to make a room
  look generous.
- **Free for the AI:** plates, cushions, books, towels, plants, art, materials,
  light. No factual claim.

Blender's job is to be correct. The AI pass makes it attractive.

---

## Boundary

`bungalow_040_66` has no canonical geometry — it is `training_ready`.
`build-simplifier-render-plan.py` reads the Simplifier annotations directly and
marks its output `not_for_delivery`, `source: simplifier_annotations_proof`,
null `source_geometry_hash`. It is a proof path for judging the look. It is not
a delivery route and must not become one.

---

## To whoever picks this up

Rainer gave clear, correct instructions early — compare the symbols to the 3D
models — and I worked on proxies for six hours instead. He has hand-drawn every
symbol, downloaded every model, placed and measured them. The input is good.
The failures are all downstream of it, in this code.

Open the thing he names. Measure before you explain. Do not say "fixed" without
showing the measurement.

---

## The deliverable, in full

Per home, six images:

| # | Image | Notes |
|---|---|---|
| 1-2 | Interior dollhouse cutaway, **modern** x2 | same layout and furniture, different finish set |
| 3-4 | Interior dollhouse cutaway, **classic** x2 | as above |
| 5 | Exterior, **modern** | no cutaway |
| 6 | Exterior, **classic** | no cutaway |

Variants differ by **finish set only** — floor, wall tone, upholstery, joinery.
Same layout, same positions, same furniture. Rainer's reason: two people who
view the same home should not see the identical picture twice.

The modern/classic model split already exists in `data/symbol-model-picks.json`
(each key carries a `modern` and a `classic` entry). What does NOT exist is a
second variant within each style — that is a finish palette, not a second model.

### Exteriors — not started at all

Different build from the interiors: no cutaway, and it needs geometry that does
not exist yet.

- **Roof.** Nothing in the pipeline builds one. `bungalow_040_66` is a bungalow,
  so a hipped or gabled roof over the building footprint.
- **Facade.** Exterior walls currently carry the same flat interior material.
- **Front door.** Four `Metal Front Door` models are catalogued at
  1120 x 296 x 2100, unused. The annotation marks the main entrance
  (`role: main_entrance`) — use it, do not guess which opening is the front door.
- **Windows** from outside: the `panes` value now annotated should show.
- **Ground and planting.** Leave planting to the AI pass; it carries no claim
  about the property.

### ComfyUI polish pass — not started

At `E:\_comfyUI\ComfyUI\ComfyUI`. Present: **RealVisXL V5** checkpoint,
**SDXL canny ControlNet**. Missing: a **depth ControlNet**, which is worth
adding — canny locks edges, depth stops the model reinventing room volume.

Every Blender render should also write **depth and edge passes**. They cost
nothing at render time and they are exactly what the img2img stage conditions
on. Not yet implemented.

Hard limit on that pass: it may touch **materials, light and atmosphere only**.
Never structure, never furniture size. These are real houses.

### Budget

100 plans x 6 images = 600 renders. At 30 min each that is weeks; at 5 min, a
long weekend. Settle the per-image budget BEFORE tuning quality upward.

---

## Have Codex review the work

Rainer's instruction, and it should be standing practice — not a one-off.

```bash
codex exec --skip-git-repo-check "$(cat tmp/review-request.md)"
```

Use it at these points:

1. **Before implementing** anything non-trivial: state what you intend to change
   and which authoritative value it reads. Codex catches "you are about to
   invent a rule for something already in the data" — the single failure mode
   that cost this project a day.
2. **After a fix that did not change the output.** Byte-identical output
   disproves the hypothesis. Do not produce a second narrative; ask.
3. **After three rejected hypotheses.** Stop and hand over the measurements.

`plans/WORKING-PROTOCOL.md` is Codex's answer to "how do I stop guessing". The
short form:

> Trace, measure, change, measure again. If you cannot name the authoritative
> source and show the before/after measurement, you are not ready to code or to
> claim success.
