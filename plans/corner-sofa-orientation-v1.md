# Corner sofa orientation — symbol frame vs model frame

Status: IMPLEMENTED — `MODEL_MIRROR_Y = {"ecksofa"}` landed, verified twice
(rotation measured before/after; render checked against the source drawing
in [plans/variant-pipeline-rollout-v1.md](variant-pipeline-rollout-v1.md)'s
Stage 1 pass). The quarter-turn part of the original plan (step 1-3, the
canvas-transpose idea) was tested on `doppelbett`, found wrong by Rainer's
own inspection, and reverted — see
[plans/remaining-render-defects-v1.md](remaining-render-defects-v1.md) and
tonight's session for the full trace. Do not re-attempt that quarter-turn
approach on real-model assets.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make the rendered furniture stand the way the annotation shows it. The reported
case is `ecksofa` in `bungalow_040_66`. The investigation below was run first,
read-only, as `plans/HANDOFF-2026-08-09-EVENING-START-HERE.md` demanded: open
the model, open the symbol, establish where the L goes, and only then propose a
change.

## Current evidence and behavior

Every number here is measured. Scripts used are in the session scratchpad
(`inspect_blend.py`, `occupancy.py`, `probe_scene.py`, `measure_source.py`,
`linked_bounds.py`); none of them touched the repository.

### 1. The L is in the geometry, and it survives the pipeline

Vertex-level top-down occupancy of
`cgaxis_grey_corner_modern_sofa_blender.blend` (9 mesh objects, 295,305 verts):
the 63,136-vert body `grey_corner_modern_sofa.001` is a full-width band plus a
leg running off one end. It is an L, not a straight sofa.

The prototype the renderer builds is also an L:

```
[proto] proto-ecksofa   dims 3.369 x 1.948 x 0.745 m   verts 295305
```

295,305 is exactly the sum of all nine mesh objects, so **the shell filter in
`import_model` removed nothing** — it was one of the four proposed causes and it
is excluded by count, not by argument. With `divisor=1.0` and a 3369 mm target
its limit is 6.74 m and every object is under it.

### 2. The recorded divisor of 1.0 is correct

`linked_bounds.py` measures each object twice — as stored, and after linking
into a scene and letting the depsgraph evaluate the parent empty:

```
group size stored    [138.72, 88.83, 32.66]     (parent transform not applied)
group size evaluated [3.52, 2.04, 0.78]         (metres)
```

3.524 x 2.037 x 0.779 m is exactly the catalogued `size_mm` [3524, 2037, 779].
The model is authored 1:1 in metres through its parent empty. `fit_within_bbox`
then scales it by 3.369 / 3.524 = 0.9560 — measured uniform on all three axes
(1.948/2.037 = 0.9560, 0.745/0.779 = 0.9563). No distortion, no bad divisor.
The handoff's suspicion about that divisor is closed.

### 3. What is actually wrong: the render is the vertical mirror of the annotation

Occupancy of the placed instance, world axes, +Y up (= up in the drawing):

| | main run (full width) | chaise leg |
|---|---|---|
| Drawing `original_preview.png`, measured | y 13722..14832 (top) | x 17220..18232 (right), y down to 12612 |
| Symbol as the Simplifier draws it | top | bottom-right |
| Render `ecksofa-2` | y 12771..13870 (**bottom**) | x ~16900..18263 (right), y up to 14719 |

Same footprint, same position, leg on the same side — and the back on the wrong
side. The rendered sofa faces the wall instead of the room.

That difference is a **reflection, not a rotation**. With its back at +Y this
model's chaise sits at the -X end; Rainer's symbol puts it at +X. No rotation of
this asset can reproduce his L, which is why four rotation-shaped hypotheses all
failed. `mirrored: false` in the annotation is about the symbol, not the asset,
so it is not the lever.

### 4. An independent defect the same measurement exposed

`static/ausstattung.js:1256-1269` (`drawSymbolArt`) turns the artwork a quarter
turn whenever the SVG's portrait/landscape orientation disagrees with the
footprint box:

```js
const artLandscape = artW >= artH;
const boxLandscape = w >= h;
if (artLandscape === boxLandscape) { ctx.drawImage(...); return true; }
ctx.rotate(Math.PI / 2);            // never written to annotations.json
```

`ecksofa.svg` is portrait (viewBox 49.740 x 71.120, w/h = 0.699); Rainer's
footprint is landscape (3369 x 2126, w/d = 1.585). So the symbol he sees is a
quarter turn away from the stored `rotation_deg: 180`, and nothing downstream
knows. Reconstructing the canvas transform with that quarter turn puts the run
along the top and the foot bottom-right — which is the sofa in the drawing,
measured at x 15840..18232 / y_img 740..1850 for the run and x 17220..18232 /
y_img to 2960 for the leg. Rainer's annotation is right; the pipeline's reading
of it is not.

**13 of the 35 placed symbols in this project are in that state**:
`badheizkoerper`, `couchtisch`, `doppelbett`, `dusche_klein`, `eckbadewanne`,
`ecksofa`, `fernseher`, `hochschrank_herd`, `kochfeld`, `lowboard`,
`schreibtisch`, `sofa_2sitzer`, `spuele`. Three of the entries on the handoff's
broken list — desk not against the wall, armchair facing, kitchen run — sit in
that set. `MODEL_FACING_DEG` was hand-tuned against renders that already carried
this error, so some of its values are probably compensating for it.

Near-square symbols make it fragile as well as wrong: `hochschrank_herd` is
0.944 against a 1.0 box, `dusche_klein` 0.688 against 1.0 — one pixel of drag
flips the artwork a quarter turn.

### 5. Not reproduced

"Renders as a straight sofa" is not literally what happens — the L is present
and measurable in the render. In the delivered perspective view it reads as
straight because the chaise is at the far end, mirrored, and blanket meshes
cover the step. The defect is real; the description of it was the symptom.

## Repository baselines

- `born2thrill-local-workbench` — branch `agent/furnished-render-and-annotation-schema`, base `7678d8e`.
  Dirty on entry: ` M scripts/render-furnished-dollhouse.py`; untracked
  `data/symbol-model-picks.json`, `plans/HANDOFF-2026-08-09-*.md`,
  `plans/WORKING-PROTOCOL.md`, `scripts/build-simplifier-render-plan.py`,
  `scripts/build-symbol-picks.py`, `scripts/catalog-hub-models.py`,
  `scripts/extract-cgaxis-catalogues.py`, `scripts/preview-symbol-shortlist.py`,
  `scripts/resolve-hub-scales.py`, `scripts/shortlist-symbol-models.py`.
  Preserved untouched.
- `floorplan-simplifier` — branch `agent/annotation-window-type-door-swing`, base `3bab52e`,
  dirty on entry (`app.py`, `static/*.js`, `symbol_footprints.json`, …). Preserved untouched.
- Investigation regenerated `tmp/plan.json` with the command the handoff
  documents. No other repository file was written.

## Exact scope

1. **Record the quarter turn.** `build-simplifier-render-plan.py` reads each
   symbol's SVG viewBox, compares its landscape-ness with the placed footprint's,
   and emits the rotation the user actually sees. The annotation is not edited —
   it stays the authority; the plan stops mis-reading it.
2. **Per-asset handedness.** A measured table beside `MODEL_FACING_DEG` marking
   assets whose chirality is opposite to their symbol (`ecksofa` confirmed),
   applied as a mesh mirror on the prototype. Entries are admitted only with a
   recorded occupancy measurement, never from a bounding box.
3. **Re-derive `MODEL_FACING_DEG`** against the symbol frame once 1 is in, since
   the current values were tuned against renders carrying the error.
4. **A test that would have caught this**: rasterise the symbol SVG at its
   annotated footprint and rotation, rasterise the placed prototype from above,
   and compare occupancy. It catches mirrors, quarter turns and squashes in one
   assertion, on all 35 placements rather than on the one somebody looked at.

## Files in scope

- `scripts/build-simplifier-render-plan.py`
- `scripts/render-furnished-dollhouse.py`
- `data/symbol-model-picks.json` (handedness field only, if that is where it belongs)
- a new test under `scripts/` following the existing `*.test.mjs` / unittest layout

## Explicitly out of scope

- `floorplan-simplifier` — no change. `drawSymbolArt` is what Rainer has been
  drawing against for weeks; the renderer must follow the app, not the reverse.
- The other eight defects in the handoff table.
- Anything about the annotation's own accuracy. Noted, not acted on: the
  `ecksofa` footprint is 3369 mm wide against a sofa measuring 2392 mm in the
  drawing, right/top/bottom aligned but ~950 mm long on the left. Rainer's
  measurement, Rainer's call.

## API, schema, and data-contract effects

Plan schema gains a derived rotation (and possibly a `symbol_quarter_turn` for
traceability). `annotations.json` unchanged; no annotation is rewritten.

## Acceptance criteria

1. `ecksofa` renders with the run along the top wall and the chaise at the
   bottom-right, matching the symbol and the drawing, shown by occupancy grid
   and by an overlay render.
2. All 13 transposed symbols land at the orientation the canvas draws.
3. The 22 untransposed placements are byte-identical in orientation to today.
4. Every fallback logs the object ID and the field it lacked.

## Tests and verification commands

```bash
python scripts/build-simplifier-render-plan.py bungalow_040_66 modern tmp/plan.json
DMH_UNDERLAY=".../original_preview.png" DMH_TOPVIEW=1 blender --background \
  --python scripts/render-furnished-dollhouse.py -- tmp/plan.json C:/tmp/overlay.png
```

New: symbol-vs-prototype occupancy comparison across all placements. No existing
test is deleted, skipped or weakened.

## Protected and risky paths

`MODEL_FACING_DEG` is load-bearing for 14 assets. Changing it and the rotation
source in one pass risks a compensating error moving rather than clearing, so
step 1 lands and is measured before step 3 begins.

## Rights, provenance, privacy, and security impact

None. Proof path only; no corpus, no export, no customer data.

## Floorplan-suite invariant

> Can any changed path generate, publish, or email geometry without matching an
> approved corrected corpus reference?

No. `bungalow_040_66` is `training_ready` with no canonical geometry, and
`build-simplifier-render-plan.py` marks its output `not_for_delivery`,
`source: simplifier_annotations_proof`, `source_geometry_hash: null`. Nothing in
scope touches promotion, export or email.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

Hypotheses recorded by the previous session (shell filter deleted the L; bad
divisor; footprint fit squashed it; rotation was wrong) are all excluded above by
measurement — vertex count, evaluated group size, per-axis scale factor, and the
occupancy grids respectively. This session opened no hypothesis it did not test.

## Rollback

Revert the listed files. No data migration, nothing persisted.

## Unresolved questions

1. Should the quarter turn be composed into `rotation_deg` in the plan, or
   emitted separately and applied by the renderer? Separate is more traceable;
   composed is harder to get wrong twice.
2. Mirror the left-handed model, or pick a right-handed corner sofa from the
   1040 unopened set parts before mirroring anything?
3. Near-square symbols sit one drag away from flipping. Do they need an explicit
   orientation on the annotation rather than an inferred one?

## Approval record

Approved by Rainer, mid-session, verbally ("you're right, fixing it") after
the side-by-side drawing/render comparison was shown. The mirror fix (this
plan's item 2, minus the mirror/dedicated-handedness-table framing —
implemented directly as `MODEL_MIRROR_Y`) is done. Items 1 (quarter-turn
composition) and 3 (re-derive `MODEL_FACING_DEG`) were tried, found wrong,
and abandoned — not merely deferred. Item 4 (a symbol-vs-prototype occupancy
test) not built.
