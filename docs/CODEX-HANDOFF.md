# Claude → Codex render handoff manifest

What a separate, full-access Codex session needs to actually do furniture
and exterior render iteration on this project. This file is the thing
itself — not a description of a workflow, an actual manifest to hand off.

## 1. Model libraries (read-only, external drives)

| Path | Contents | Index |
|---|---|---|
| `E:\_models_hub\_extracted\` | 94 real `.blend` models (furniture, fixtures, the one real exterior door asset) | `born2thrill-local-workbench/tmp/hub-model-catalog.json` |
| `E:\_models_hub\Windows\` | 5 more window-family models as unextracted zips — **all 5 checked, all are door-style units, not real windows** (see §4) | none — extract with `unzip` before use |
| `E:\_models_converted\` | 1160 `.fbx` models, converted from the raw `F:\` CGAxis library | `born2thrill-local-workbench/tmp/fbx-library-catalog.json` |
| `E:\_maps\` | Texture root for external models | overridable via `DMH_TEXTURE_ROOT` env var |
| `C:\dev\Floorplan-tools\born2thrill-local-workbench\data\furniture-assets\full-catalog\` | 39 self-contained `.glb` models, repo-local | manifest in same folder |
| `data/furniture-model-overrides.json` | Furniture TYPE → real model path, only 3 entries today (shower, sink, bathtub) | this file itself |

Warning already learned the hard way: CGAxis volumes ship whole room SETS,
not single fixtures (`_caveat` in the overrides file). Verify object count
before assuming a match is one piece of furniture.

## 2. The pipeline entry points

- Interior plan: `scripts/build-furnished-render-plan.mjs` (Node) — reads
  approved canonical geometry, runs `src/lib/generator/furniture-
  placement.mjs`, resolves each placement to a real model via
  `furniture-catalog.mjs`, writes a render-plan JSON.
- Interior render: `scripts/render-furnished-dollhouse.py` (Blender
  `--background`) — consumes that JSON, rebuilds the ENTIRE scene from
  scratch every run, writes a PNG. No persistent scene by default.
- Exterior plan: `scripts/build-simplifier-render-plan.py` — **proof-only,
  `not_for_delivery: True`**, not canonical. Fine for internal/reference
  renders, must never be treated as customer-deliverable.
- Exterior render: `scripts/render-exterior.py` (Blender `--background`) —
  rebuilds the scene from scratch, DOES save a versioned `.blend` snapshot
  each run (`tmp/exterior-<style>-vN.blend`).

## 3. The working file (explore vs. commit)

**No single file is authoritative geometry.** JSON stays the source of
truth; a `.blend` is a reproducible derivative you may edit freely for
visual exploration, but:

- Structural edits (walls, openings, room shape) must go back through the
  JSON builders above, not stay only in a hand-edited `.blend`.
- Furniture swaps ARE fine to do directly in a working `.blend` for fast
  visual judgment. There is currently **no automated "commit" step** that
  reabsorbs an approved hand-edited placement back into the JSON pipeline
  — `furniture-placement.mjs` only generates placements, it has no input
  path for an edited list yet. Until that exists, record what you changed
  and why in the render's catalog entry (`description_de`/`features`) so a
  human can manually fold it back if it should become permanent.
- Do not treat any single `tmp/*.blend` as "the" project file. They are
  timestamped iteration snapshots. `tmp/kitchen-inspect.blend` is one such
  snapshot (interior), not a template.

## 4. Known asset gaps (don't rediscover these)

- **No real simple-window asset exists anywhere in the libraries.** All 5
  "Metal Window" models (1140×2100, 1180×1260, 1770×1800, 2214×2100,
  2824×2360) are door-style sliding/hinged units. `render-exterior.py`
  now builds windows procedurally (`build_window()`, 1/2/3 equal panes by
  width) instead of using these assets.
- Furniture asset coverage is uneven — many types fall back to
  `render-furnished-dollhouse.py`'s procedural box builder
  (`build_box`/`build_rect`/etc.), named `<asset_id>-<n>` in the scene so
  they're at least identifiable (e.g. `garderobe-14`).

## 5. Where output goes

Durable per-project location (same convention as 40 other projects, NOT
`tmp/`, NOT `born2thrill-local-workbench/exports/`):

```
born2thrill-local-workbench-data/corrections/<project_id>/renders/
  <batch-name>/
    catalog.json       <- schema: visual-catalog-v1, see below
    catalog.csv         <- flat export of the same records
    <image files>.png
```

### `catalog.json` record fields (required)

```
asset_id, file, asset_type, style, description_de, palette, materials,
rooms_visible / features, qc_status, search_text_de,
geometry_source              <- path to the source .blend
geometry_reference_render    <- path to the PRE-polish raw render, for
                                 provenance comparison. Do not omit this —
                                 without it a reviewer cannot verify the
                                 image wasn't hallucinated.
```

`qc_status` values in use so far: `preferred_candidate`,
`draft_needs_garderobe_alignment_review`,
`draft_needs_garderobe_design_review`, `visual_reference`. A controlled
enum + separate issue-code list is proposed but not yet built — for now,
be specific and honest in free text rather than defaulting to
"preferred_candidate."

**No aggregate catalog exists yet** merging per-project catalogs into one
searchable index. Each project's `catalog.json` is currently a standalone
file. Do not assume anything reads it automatically yet.

## 6. Hard rules that do not change regardless of who's driving

- Polish/generation passes must never alter window/door/wall layout —
  atmosphere and material only. Verify by comparing against
  `geometry_reference_render` before calling anything final.
- Nothing from the proof-only exterior path (`build-simplifier-render-
  plan.py`) may be marked customer-deliverable.
- No automatic customer delivery, ever — human approval + the WordPress
  manual gate, no exceptions, regardless of render quality.
