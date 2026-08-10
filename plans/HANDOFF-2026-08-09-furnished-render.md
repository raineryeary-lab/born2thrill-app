# Handoff — furnished dollhouse render, 2026-08-09

Everything needed to build is on disk. No downloads outstanding, no open
questions. Start at "The run" and work down.

## What works today

`bungalow_040_66` renders end to end from Rainer's own annotations:

```bash
python scripts/build-simplifier-render-plan.py bungalow_040_66 modern tmp/render-plan-040_66-modern.json
"/c/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
  --python scripts/render-furnished-dollhouse.py -- tmp/render-plan-040_66-modern.json C:/tmp/out.png
```

- **Tilted cutaway** — one plane, 500 mm at the front rising to 2000 mm at the
  back, matching the reference images. Door and window frames, glazing and
  leaves are exempt from the cut, so an opening stays legible when its wall is
  knee-high. Frames are white and built only for doors and windows; a Durchgang
  gets none, because lining a hole in a wall invents trim the plan does not have.
- **All 34 hand-placed symbols** land. Kitchen runs, the island and the
  Vorwandinstallation are built from the drawn paths, not fetched as objects.
- **Furniture fits without distortion** — `fit_within_bbox` scales uniformly, so
  a three-seater in a corner-sofa footprint stays a three-seater instead of
  becoming a stretched slab.

## The two scale traps

Both cost hours today. Neither is subtle once known.

1. **`E:\_models_converted` measurements are not trustworthy.** The C4D->FBX
   conversion produced wrong scales for an unknown subset. The model recorded as
   432 x 414 x 881 mm is a full shower cabin. Any size-based reasoning against
   that library is built on sand — which is exactly how a vanity unit ended up
   where a bath belonged and an oven where a washing machine belonged.
   `tmp/symbol-model-shortlist.json` is therefore **unreliable and should not be
   used**. Prefer native `.blend` from `E:\_models_hub`, which sidesteps it.
2. **CGAxis kitchen sets are out by exactly 2.54.** Divide by it and everything
   lands: a 2.032 door becomes 800 mm, a 0.038 panel becomes 15 mm, a 6.375
   room becomes a 2510 mm ceiling. A clean constant, not a reason to distrust
   the asset.

Corollary that generalises: **verify a model's real size before trusting it**,
against the reference JPG each Hub archive ships with.

## Assets

`E:\_models_hub` — 89 named Blender archives, all zipped except the beige
corner sofa. Named, so no identification problem. Covers corner sofas, sofas,
armchairs, beds, WC, bidet, washbasins, baths (including `Corner_Bathtube`),
showers, washing machine, wardrobes, kitchen sets, TVs, coffee tables, dining
sets, desks, office chairs.

`tmp/cgaxis-renders` — 397 official renders pulled from the volume PDFs on F:,
one per model, numbered to match filenames. Extracted by
`scripts/extract-cgaxis-catalogues.py`. Useful if the old converted library ever
needs typing, which is now optional rather than blocking.

**Nothing left to buy.** Two corrections from Rainer that closed the list:
`Corner_Bathtube_BLEND.zip` is already on disk, and a Trockner is the same
600 x 600 x 850 box as a Waschmaschine — often stacked on it — so it reuses that
model rather than needing its own.

## Build boxes, don't shop

Rainer's rule, and it is the right one: simple rectilinear furniture is a scaled
cube with a material lifted off the real models. Only organic shapes need real
geometry. German sizes, W x D x H mm — the desk and worktop heights are norms:

| Piece | Size |
|---|---|
| Couchtisch | 1200 x 600 x 420 |
| Lowboard | 1800 x 400 x 450 |
| Sideboard | 1600 x 450 x 800 |
| Schreibtisch | 1600 x 800 x **720** (DIN EN 527) |
| Schreibtisch Kind | 1200 x 600 x 700 |
| Garderobe | 1000 x 350 x 1900 |
| Trockner / Waschmaschine | 600 x 600 x 850 |
| Kuehlschrank | 600 x 600 x 1800 |
| Hochschrank/Herd | 600 x 600 x 2100 |
| Kochfeld | 600 x 520 x 45 |
| Schrank 40 / 60 | 400 / 600 x 600 x 2100 |
| Kleiderschrank | 2000 x 600 x 2100 |
| Fernseher | 1230 x 80 x 710 (55") |
| Esstisch | 1800 x 900 x **750** |

Kitchen: carcass 720 + plinth 140 + worktop 40 = **900** working height, 600
deep. Already what the Kuechenzeile path tool builds.

## Kitchens: dress the box, do not tile cabinets

Rainer's method, and it is better than disassembling sets. Take the LOOK from
the kitchen sets and apply it to the box built from the drawn path:

1. **Carcass** — box along the Kuechenzeile path, 600 deep, 720 high on a 140
   plinth, exactly as the path tool already builds it.
2. **Worktop** — 40 mm slab on top, taking its material from the set.
3. **Fronts** — tile door panels across the visible face at standard widths
   (600 / 450 / 300) with a 3 mm shadow gap, using the set's door material. The
   panels are flat rectangles, so this is geometry that always fits.
4. **Tall elements** — same treatment at 2100, copying the look of the set's
   tall units.
5. **Island** — identical, applied to the dragged rectangle.

Why this beats tiling real cabinets: the run is drawn to whatever length the
wall happens to be. Tiling authored units into an arbitrary length either leaves
a gap at the end or overlaps the last unit, and no amount of cleverness fixes
that — the units were modelled at fixed widths. Dressing a box that was built to
the drawn path fits by construction, every time.

The disassembly finding still holds and is still useful: `Kitchen Furniture
Set 9` holds **109 separate mesh objects**, so individual door panels and
worktops can be lifted out as source material. Apply the scale divisor first,
then discard the room shell — the sets are staged scenes including walls, floor
and ceiling. Rule: after scaling, anything taller than ~2300 mm or wider than
~3000 mm is shell, not cabinet.

## What AI does, and what it must never do

Settled with Rainer, and it shapes the whole quality strategy.

- **Must be real geometry** — walls, openings, room shapes, and the fixed
  fittings: bath, shower, WC, basin, kitchen run. These are claims about the
  property.
- **Must be real, for a different reason** — bed, sofa, dining set, wardrobe.
  Not sold with the house, but they prove the room *works* at that size, which
  is the entire point of a furnished plan. An image model cannot be trusted
  here: it will shrink a bed to make a room look generous.
- **Free for the AI** — plates, cushions, books, towels, plants, art, and
  general material realism. No factual claim, so synthesis is safe.

So Blender's job is to be **correct**; the ComfyUI pass makes it **attractive**.
That is why every render should also write depth and edge passes.

ComfyUI at `E:\_comfyUI\ComfyUI\ComfyUI`: RealVisXL V5 plus an SDXL canny
ControlNet. A depth ControlNet is missing and would meaningfully improve
structural lock — worth adding before the polish stage.

## The run

1. Extract all 89 archives; verify each against its reference JPG.
2. Wire named picks into `data/symbol-model-picks.json`, replacing the
   size-matched ones. Delete reliance on the shortlist.
3. Build the box furniture from the table above, finishes lifted off real models.
4. Kitchens as a kit of parts.
5. Four variants — two modern, two classic — differing by finish set, same
   layout and furniture.
6. Two exteriors, classic and modern. Needs roof and facade; no cutaway. Doors
   from the Hub's DOORS AND GATES; planting can be left to the AI pass.
7. Depth and edge passes alongside every beauty render.

## Known-open

- **Frames still read heavy** at 500 mm wall height. Rainer has seen it. Options
  are a slimmer profile, or letting glazing follow the cut while the frame
  stands. A look decision, not a bug.
- **Lighting is flat.** HDRI loads but shadows are nowhere near the references.
  Cycles instead of EEVEE is the next lever.
- **9 interior walls of 31** on this plan. Rooms are annotated as inner
  boundaries and unpaired edges fall back to exterior; acceptable, not perfect.
- **2 openings match no wall.**
- **Budget check before scaling up:** 100 plans x 4 variants = 400 images. At
  30 min each that is over a week of rendering; at 5 min, a weekend. Settle the
  per-image budget before tuning quality upward.

## Boundary that must not erode

`bungalow_040_66` has **no canonical geometry** — it is `training_ready`, not
promoted. `scripts/build-simplifier-render-plan.py` reads the Simplifier
annotations directly and marks its output `not_for_delivery` with
`source: "simplifier_annotations_proof"` and a null `source_geometry_hash`.

It is a proof path for judging the look. It is **not** a delivery route, and it
must never become one. Anything customer-facing goes through canonical JSON.

---

## UPDATE — library resolved

Supersedes "The two scale traps" above for the Hub library.

**94 archives extracted** to `E:\_models_hub\_extracted`, 95 `.blend` files
measured, **93 resolved to verified real-world sizes**.

### Three scales, not one

The library is not uniformly scaled. Two wrong answers preceded the right one:

1. A plausibility heuristic was **too weak** — it only corrected files whose
   longest dimension fell outside furniture range, so an 813 mm toilet measuring
   2066 passed as a wardrobe.
2. A fixed 2.54 divisor was **too strong** — it shrank a real 2010 mm sofa to
   791 mm.

Actual distribution: **73 at 2.54x** (title-case catalogue assets, inches read
as Blender units), **7 at 1:1** (files named `cgaxis_*_blender`), **2 at 10x**,
11 scenes resolved per part.

### What works: resolve scale from TYPE

`scripts/resolve-hub-scales.py`. The Hub names its assets, so the expected size
is known before measuring — a "Grey Three Seat Sofa" should be about
2100 x 900 x 800, and the right divisor is whichever lands closest. That is
verification against a known target, not inference from a bare number, and the
distinction is the lesson of the whole day: every failure came from trusting a
measurement with nothing to check it against.

Two details that mattered:

- **Match on words, not substrings.** "grey corner modern sofa" does not contain
  "corner sofa", so substring matching classed a corner sofa as a three-seater
  and then picked the scale that fitted a three-seater — a wrong answer arrived
  at confidently. Requiring every word of the key, in any order, fixes it.
- **Stated dimensions beat nominal ones.** CGAxis names windows
  "Metal Window 1180mm x 1260mm". Parsing that gives an exact target.

**Independent confirmation:** that window measures 1184 x 1260 after resolution
against a stated 1180 x 1260. Name and geometry agree to 4 mm.

### Coverage — every type has a model

`tmp/hub-models-resolved.json`. Sizes verified, W x D x H mm:

| Type | n | Example |
|---|---|---|
| corner_sofa | 2 | 3524 x 2037 x 779 |
| corner_bath | 1 | 1544 x 1544 x 755 |
| bathtub | 3 | 1802 x 866 x 786 |
| wc | 2 | 565 x 357 x 1011 |
| basin | 4 | 408 x 407 x 283 |
| shower | 3 | 1515 x 976 x 2105 |
| bed | 4 | 1120 x 2050 x 682 |
| sofa_3 / sofa_2 | 9 / 3 | 1779 x 760 x 906 |
| armchair | 5 | 1107 x 945 x 728 |
| coffee_table | 5 | 800 x 800 x 400 |
| dining_set | 1 | 2200 x 1310 x 924 |
| desk | 2 | 1870 x 812 x 825 |
| wardrobe | 1 | 3082 x 650 x 2384 |
| washer | 1 | 600 x 442 x 800 |
| tv | 2 | 1084 x 404 x 700 |
| front_door | 4 | 1120 x 296 x 2100 |
| door | 3 | 1080 x 236 x 2140 |
| window | 2 | 1184 x 109 x 1260 |
| towel_radiator | 1 | 600 x 51 x 1393 |
| kitchen_sink | 1 | 1000 x 500 x 506 |

Real doors and windows change the frame problem: the cut openings can carry
actual joinery instead of the white boxes that read as monoliths. Four front
doors also unblock the exteriors.

**Unresolved, 2:** `Bathroom Furniture Set` (a staged scene, resolve per part
like the kitchens) and `White Modern Sofa 13` (no candidate scale fits — inspect
before use).

### Next

Map `tmp/hub-models-resolved.json` types onto the Simplifier symbol keys and
write `data/symbol-model-picks.json` with the divisor alongside each path, so
the renderer scales correctly on import. Then the box furniture, the kitchen kit
of parts, four variants, two exteriors.

### Picks written — with a guard that still needs implementing

`scripts/build-symbol-picks.py` maps 28 symbol keys onto resolved models,
recording a modern and a classic choice for each plus the scale divisor.
`data/symbol-model-picks.json` is written. `doppelwaschtisch` has no model.

**A real model is only better than a box when its real size is near the
annotated footprint.** Reviewing the first output, four picks fail that test:

| Symbol | Footprint | Model | Problem |
|---|---|---|---|
| schrank_40 / schrank_60 / abstellschrank | 400 / 600 wide | White Rounded Cupboard, 1500 wide | uniform fit shrinks it to a doll's cupboard |
| schreibtisch_kind | 1200 x 600 | Office Desk Workstation 41, 1800 x 800 | adult desk in a child's footprint |
| dusche_gross | 990 x 1200 | Square Shower, 906 x 903 | Rectangular Shower is the right one |
| doppelwaschtisch | 1200 x 450 | none | box |

So the picker needs a size gate: if the model's real footprint is more than
~40 % from the symbol's, fall back to a box at the correct dimensions. Without
it, using real models simply trades the stretched-sofa distortion for a
shrunken-cupboard one — the same mistake pointing the other way.

Note this is only detectable because sizes are now verified. Under the old
size-match approach the model was *chosen* by size, so it always appeared to
fit, and the mismatch was invisible.

---

## UPDATE 2 — both variants rendering

`C:\tmp\dollhouse-modern-07.png` and `C:\tmp\dollhouse-classic-01.png`.

### The 138 m sofa: a bug in this file, not in the assets

`fit_within_bbox` called `local_dimensions(obj)`, which returns a THREE-TUPLE
`(mins, maxs, size)`, and zipped the target against the whole tuple — dividing
millimetres by the `mins` vector. The resulting scale factor was meaningless, so
the corner sofa was placed at 138 x 80 x 30 metres.

Three root-cause hypotheses failed before this one, all aimed downstream:

1. Fixed 3 m shell filter deleting the sofa body as architecture — no change.
2. Shell filter scoped too narrowly, other staged scenes keeping their rooms —
   no change.
3. Scale set on the prototype object being dropped when instances share
   `proto.data` — no change.

The render was byte-identical after each, which was itself the signal: the
object was not on the path being guessed about. A scene inventory dumped by
size named it in one run — `DMH_INVENTORY=1` on the render script, kept for
next time. **Measure before theorising**; three guesses cost more than the
diagnostic would have.

Note that hypothesis 3 was a real defect and its fix (baking scale into the mesh
before instancing) is correct and retained — it simply was not this symptom.

### Working now

- `.blend` import with per-model scale divisors
- Size gate: model used when within 60 % of the annotated footprint, otherwise
  a box. Deliberately crude — nobody measures a marketing render.
- 28 furniture instances from 14 meshes, real CGAxis materials throughout
- Modern and classic differ on 5 models: bed, armchair, coffee table, and both
  basins. Same layout, same positions.

### Next, in order of visible payoff

1. **Vorwandinstallation reads as a massive block.** 1500 x 150 along the drawn
   path is dimensionally right but dominates the bathroom. Needs a wall-like
   material, or to stop at the fixtures rather than running the full path.
2. **Boxes are untextured white.** They need finishes lifted off the real
   models — this is what makes a box read as furniture.
3. **Kitchen dressing** — worktop material, door panels tiled on the face.
4. **Lighting is flat.** Cycles instead of EEVEE is the lever.
5. Two more variants, then the exteriors.

---

## Next: window panes (Rainer, 2026-08-09)

Windows currently render as one sheet of glass whatever their width. Real ones
are divided. Add a right-click menu on a window element — the same pattern as
the door options already in `static/element-edit.js` — offering **1, 2 or 3
panes**.

- `panes` on the element, default 1
- whitelist it in `normalize_element` in `app.py` so it persists
- render mullions dividing the opening, glazing per pane rather than one sheet

Per plans/WORKING-PROTOCOL.md: the annotated value is authoritative. A window
with `panes` set uses it; only an unset window falls back to a default.
