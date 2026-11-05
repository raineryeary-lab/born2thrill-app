# Standing task: turn a verified baseline into final catalog images

Give this to Codex, filled in, every time `run_project.py` finishes a
project. It's the fixed instruction Rainer wants Codex to always execute —
fill in the blanks from that project's `handoff.json`, paste the rest
unchanged.

---

You are working from a VERIFIED geometry baseline. Do not add, remove, or
resize any wall, window, door, or room, and do not move furniture —
furniture position is part of the locked structure for this task (swapping
furniture is a separate, different workflow — see "explore vs. commit" in
`docs/CODEX-HANDOFF.md` — not this one). Only material, lighting, and
atmosphere are yours to change.

**Keep the same camera as the baseline render, unchanged, for every
variant.** This is what makes "structural preservation" checkable at all
— a changed camera makes an exact comparison against the baseline
impossible. Do not reframe or re-angle the shot.

**Blender**: `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`
(not on PATH — use the full path). To produce a variant: open the baseline
`.blend` (`blender <baseline.blend>`, GUI, or `--background --python
<script>` if scripting material/lighting changes), change ONLY materials/
lighting/world background, keep every mesh transform untouched, render,
save the variant as a new file (`<style-name>-variant.blend` /
`.png`) — never overwrite the baseline `.blend` or its PNG.

**Project**: `<project_id>` (from `handoff.json`)

**Baselines provided** (per style, from `handoff.json`'s `styles` object):
- Interior: `<interior_baseline_blend>` + its raw render `<interior_baseline_png>`
- Exterior: `<exterior_baseline_blend>` + its raw render `<exterior_baseline_png>`

**Produce:**
- 4 distinct interior style variants (different material/palette/lighting
  treatments of the SAME interior baseline — e.g. warm modern, soft
  scandinavian, modern architectural, dark modern, or your own choices)
- 2 exterior variants (different mood/lighting/time-of-day treatments of
  the SAME exterior baseline per style)

**`catalog.json` is exactly this shape** (top-level object, not a bare
array — `assets` is the array):

```json
{
  "schema_version": "visual-catalog-v1",
  "created_at": "<today, YYYY-MM-DD>",
  "plan_family_id": "<project_id>-<style>",
  "geometry_source": "<the baseline .blend this whole file's assets derive from>",
  "assets": [
    {
      "asset_id": "<unique across the whole file, e.g. interior-warm-modern-v1>",
      "file": "<image filename only, no path — it lives next to catalog.json>",
      "asset_type": "isometric_interior_concept | exterior_visualization | exterior_reference",
      "style": "<the NEW visual treatment name you gave it, e.g. warm_modern — not the source classic/modern>",
      "description_de": "<one sentence, German>",
      "palette": ["<3-5 short color/material tags>"],
      "materials": ["<3-5 short material tags>"],
      "rooms_visible": ["<room tags, interior only>"],
      "features": ["<notable features, exterior only, or in addition for interior>"],
      "qc_status": "<see rule below>",
      "search_text_de": "<space-separated German keywords, for free-text search>",
      "geometry_source": "<exact path to the baseline .blend, as given in handoff.json — copy verbatim>",
      "geometry_reference_render": "<exact path to the baseline raw .png, as given in handoff.json — copy verbatim>"
    }
  ]
}
```

Use the paths from `handoff.json` verbatim (same absolute-path style
already in that file) for `geometry_source`/`geometry_reference_render` —
don't normalize or re-relativize them.

`qc_status` rule, not a suggestion: **at most ONE entry across the entire
catalog.json may be `preferred_candidate`.** If nothing has been reviewed
carefully enough to actually recommend, zero entries get that status —
never default to it, and never mark more than one. Everything else gets a
specific, honest status (`draft_needs_review`, `visual_reference`, etc.),
plus a one-line reason in `description_de` or a `qc_notes` field if you
need to explain why.

**Save everything to**: `output_dir_for_images_and_catalog` from
`handoff.json` — images alongside one `catalog.json` covering all of them.
If `catalog.json` already exists there, load it, append your new entries
to its existing `assets` array (checking for `asset_id` collisions —
rename yours if one collides), and write the merged file back. Never
overwrite or drop existing entries. A `catalog.csv` export is optional —
`catalog.json` is the authoritative file, CSV is just a convenience mirror
if you want to produce one.

**Before calling anything final**, since the camera is unchanged (see
above), place your variant and its `geometry_reference_render` side by
side at the same resolution and check pixel-for-pixel: every window,
door, and wall edge must land in the same place in both. Any shift means
something moved — do not give that image a `catalog.json` entry; fix it
and re-render instead. Only material color/texture, lighting, and sky/
background may differ between the two images.

---
