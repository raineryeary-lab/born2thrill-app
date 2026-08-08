# Handoff — 2026-08-07 evening

Supersedes the credit figures in `HANDOFF-furniture-generation-final.md`,
which are wrong. Read this one first.

---

## Do this first tomorrow

The render script was rewritten but **has not been run yet**. One command:

```
& "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" --background --python "C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\render-furnished-dollhouse.py" -- "C:\dev\Floorplan-tools\born2thrill-local-workbench\tmp\render-plan-dc905-modern.json" "C:\dev\Floorplan-tools\born2thrill-local-workbench\tmp\dollhouse-v2.png"
```

Compiles clean. Not executed — treat every runtime claim below as unverified.

---

## Credits: the real numbers

From Rainer's own Tripo export (`history_2026-08-01_2026-08-07.xlsx`),
93 successful generations, **2790 credits spent, ~10 remaining**.

| Run | Pieces | Credits |
|---|---|---|
| 06 Aug test batch | 6 | 180 |
| 06 Aug full run #1 | 27 | 810 |
| 06 Aug full run #2 | 27 | 810 |
| 07 Aug morning | 33 | 990 |
| 07 Aug 19:46 | 0 | 0 (died on empty balance) |

**Only 39 `.glb` files exist.** ~1620 credits (~$16) bought duplicates.

### Cause — fix before spending anything more

`scripts/tripo-generate-furniture-full.mjs:33` has a hardcoded
`ALREADY_GENERATED_TYPES` set of three test-batch names and **no disk check**.
Every run restarts from the top of the same 48-piece list and re-pays for
pieces already downloaded. Do not run it again until a `fs.existsSync` guard
is added.

Verified: files on disk are a contiguous prefix of the generation order,
positions 1–33. Position 34 onward never generated. Nothing was lost.

### Still missing — 15 pieces, ~450 credits (~$4.50)

`table_lamp__classic`, then potted_plant, shower, bathtub, sink, towel,
clothing_rack, shoe_rack (both styles each).

API credits, not Studio credits — separate pots.
Checkout: https://tripo3d.myshopify.com/collections/tripo-service

---

## What was built today

Both files are new and additive. Nothing existing was modified.

- `scripts/build-furnished-render-plan.mjs` — runs the existing tested
  placement engine against an approved canonical plan, resolves each
  placement to a real `.glb`, writes a render plan JSON. **Verified working:**
  22 items placed for `plan-dc905efd8b1bbc28`, 5 skipped for absent meshes.
- `scripts/render-furnished-dollhouse.py` — Blender: textured floor plates,
  walls, furniture instancing with scale normalisation, HDRI lighting,
  orthographic dollhouse camera.

Neither touches `geometry_hash`, the scene manifest, or the approved pipeline.

---

## First render (v1) and what was wrong

`tmp/dollhouse-dc905-modern.png` rendered successfully in 9s but looked bad.
Five defects, all parameters rather than asset problems:

1. Blown out — world 1.6 + sun 4.0.
2. Mirrors floated above walls — 1400mm mount height vs 1200mm cutaway walls.
3. Wardrobes speared through walls — 2100mm furniture vs 1200mm walls.
4. Near-white furniture palette — **`FURNITURE_FINISHES` in
   `furniture-catalog.mjs` was ignored entirely** and an invented flat palette
   used instead.
5. Sparse — 22 items over 8 rooms (placement is one item per wall edge).

v2 addresses 1–4. Density (5) would mean changing tested placement code and
was left alone deliberately.

---

## Rainer's asset libraries — the big lever

`E:\_models` (112 GB) and `E:\_maps` (691 GB). More on a second PC.

Wired into v2:
- HDRI: `E:\_maps\BG\hdr\spericalhdris\cloud_layers_4k.hdr`
- Wood floor: `E:\_maps\Floors\Oak_01\VizPeople_Oak_1_Diffuse_1.jpg`
- Tile floor: `E:\_maps\Arroway Textures - Tiles Volume One\Maps\tiles-21_d100.jpg`

Override the root with `DMH_TEXTURE_ROOT`. If a file is missing the script
falls back to flat colour and still completes, printing what it couldn't find.

**Not yet used: the 3DSky furniture.** ~1820 zips + 1763 loose models in
folders named by product ID (`1150048.59403f1cb2a47`), so nothing indicates
which is a sofa. `01_Preview_3DSky PRO models` likely holds thumbnails and is
the way in. Swapping 3DSky pieces for the untextured Tripo meshes is the
single change most likely to close the gap to Rainer's reference images —
those meshes contain **zero materials and zero textures** by design
(`texture:false, pbr:false`), which is why v1 read as white plastic.

### `F:\` — CGAxis volumes, mostly unusable

Organised by category (BATHROOMS, KITCHEN APPLIANCES, BEDROOMS, OFFICE
FURNITURE…), which is much better naming than E:\_models. But the format is
Cinema 4D: **1202 `.c4d` files, which Blender cannot import.** Converting
needs C4D itself.

The exception is worth having: **41 `.FBX` in `F:\02 BARTHROOMS\fbx`**
(5 bathroom sets). Blender imports FBX natively, and shower/bathtub/sink/towel
are 4 of the 8 types Tripo never generated. Each volume ships a PDF catalogue
(`cgaxis_models_volume_*.pdf`) to identify which `bathroomset_NN_NN` is which
fixture.

Next step there: import 2–3, check scale and polycount, identify against the
PDF, wire them in as the bathroom types. That would remove most of the reason
to buy the remaining Tripo pieces.

**Open rights question, unanswered.** Per AGENTS.md, license terms must be
recorded per asset and editing does not establish commercial rights. Fine for
internal proving; needs an answer before any of these assets appear in a
customer-facing render. Note the F:\ FBX filenames carry a `-CGPERSIA` tag,
which is a warez-site marker — stated as fact from the filename, not as a
conclusion about the whole library.

---

## Strategy question left open

Rainer questioned the 3D route versus an image-generation model. Position
reached, not settled: an image model cannot bind output to canonical JSON, so
it can't be the final renderer for interiors where the image represents a
buildable plan. The viable shape is 3D render as geometric control input,
image model as surface pass. The exterior is a far better candidate for the
image route than the dollhouse interior.

Decide with render v2 in hand, not before.

---

## Uncommitted

Everything from `HANDOFF-furnished-3d.md` §8, plus the two new scripts above
and this file. Still not on a real branch.
