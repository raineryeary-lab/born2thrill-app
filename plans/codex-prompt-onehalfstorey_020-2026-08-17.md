# Codex prompt — onehalfstorey_020, 2026-08-17

`docs/CODEX-STANDING-TASK.md` filled in from
`…\corrections\onehalfstorey_020\renders\go-baseline\handoff.json`
(written 2026-08-17 18:50, `2 style(s) verified and ready, 0 excluded`).
Paste everything below the line.

Two things differ from the standing task and are called out inside the prompt:
this house has **two storeys** and both are now rendered, and Rainer wants the
**staircase to fade out toward the top**.

---

You are working from a VERIFIED geometry baseline. Do not add, remove, or
resize any wall, window, door, or room, and do not move furniture —
furniture position is part of the locked structure for this task (swapping
furniture is a separate, different workflow — see "explore vs. commit" in
`docs/CODEX-HANDOFF.md` — not this one). Only material, lighting, and
atmosphere are yours to change.

**Keep the same camera as the baseline render, unchanged, for every
variant.** This is what makes "structural preservation" checkable at all —
a changed camera makes an exact comparison against the baseline impossible.
Do not reframe or re-angle the shot.

**Blender**: `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`
(not on PATH — use the full path). To produce a variant: open the baseline
`.blend` (`blender <baseline.blend>`, GUI, or `--background --python
<script>` if scripting material/lighting changes), change ONLY materials/
lighting/world background, keep every mesh transform untouched, render,
save the variant as a new file (`<style-name>-variant.blend` / `.png`) —
never overwrite the baseline `.blend` or its PNG.

**Project**: `onehalfstorey_020`

**This house has TWO full storeys.** Its stored metadata says
`1_5_storey` / `gable` and the project id says "onehalfstorey" — all three
are known-wrong records, not a description of the building. It is a full
two-storey with a Walmdach. Erdgeschoss and Obergeschoss are BOTH rendered
below and both belong in the package.

**ONE THING YOU MAY CHANGE BEYOND MATERIALS — the staircase.** The stair in
the Erdgeschoss baselines is a real flight (14 of 16 risers fit the drawn
core; it is truncated where the dollhouse cut plane crosses it, so it ends
on a hard step edge). Rainer wants it to **fade out toward the top**
instead of stopping abruptly — a soft dissolve of the upper steps rather
than a cut edge. Do this with material/alpha (a height-driven transparency
ramp on the stair objects), NOT by moving or deleting stair geometry. If
alpha cannot be made to read well in this scene, say so and leave the stair
as it is; do not improvise a geometry change.

**Baselines provided** (from `handoff.json`):

Erdgeschoss (`floor-0`) interiors, in `…\renders\go-baseline\`:
- modern, finish `modern-a` — `interior-modern-baseline.blend` / `.png`
- modern, finish `modern-b` — `interior-modern-b-baseline.blend` / `.png`
- classic, finish `classic-a` — `interior-classic-baseline.blend` / `.png`
- classic, finish `classic-b` — `interior-classic-b-baseline.blend` / `.png`

Obergeschoss (`floor-1`) interiors, same folder:
- modern `modern-a` — `interior-modern-upper-baseline.blend` / `.png`
- modern `modern-b` — `interior-modern-b-upper-baseline.blend` / `.png`
- classic `classic-a` — `interior-classic-upper-baseline.blend` / `.png`
- classic `classic-b` — `interior-classic-b-upper-baseline.blend` / `.png`

Exteriors (one per style, roof style is the only difference):
- modern — `exterior-modern-baseline.blend` / `.png`
- classic — `exterior-classic-baseline.blend` / `.png`

Full absolute paths for every one of these are in `handoff.json` under
`styles.<style>.interior_finishes` (keys ending `@floor-1` are the
Obergeschoss) and `styles.<style>.exterior_baseline_*`. Copy them verbatim.

**Produce:**
- 4 distinct interior style variants (different material/palette/lighting
  treatments — e.g. warm modern, soft scandinavian, modern architectural,
  dark modern, or your own choices). Cover BOTH storeys; do not deliver
  four Erdgeschoss images.
- 2 exterior variants (different mood/lighting/time-of-day treatments of
  the SAME exterior baseline per style)

**`catalog.json` is exactly this shape** (top-level object, not a bare
array — `assets` is the array):

```json
{
  "schema_version": "visual-catalog-v1",
  "created_at": "<today, YYYY-MM-DD>",
  "plan_family_id": "onehalfstorey_020-<style>",
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

State the storey in `rooms_visible` (Erdgeschoss rooms: Wohnen/Essen/Kochen,
Büro, WC, HWR/HTR, Diele — Obergeschoss: Bad, 2× Kind, Eltern/Schlafen,
Flur), so a package built from this catalog cannot silently ship two copies
of the same floor.

`qc_status` rule, not a suggestion: **at most ONE entry across the entire
catalog.json may be `preferred_candidate`.** If nothing has been reviewed
carefully enough to actually recommend, zero entries get that status — never
default to it, and never mark more than one. Everything else gets a
specific, honest status (`draft_needs_review`, `visual_reference`, etc.),
plus a one-line reason in `description_de` or a `qc_notes` field if you need
to explain why.

**Save everything to**:
`C:\dev\Floorplan-tools\born2thrill-local-workbench-data\corrections\onehalfstorey_020\renders\go-baseline`
— images alongside one `catalog.json` covering all of them. If
`catalog.json` already exists there, load it, append your new entries to its
existing `assets` array (checking for `asset_id` collisions — rename yours
if one collides), and write the merged file back. Never overwrite or drop
existing entries.

**Before calling anything final**, since the camera is unchanged (see
above), place your variant and its `geometry_reference_render` side by side
at the same resolution and check pixel-for-pixel: every window, door, and
wall edge must land in the same place in both. Any shift means something
moved — do not give that image a `catalog.json` entry; fix it and re-render
instead. Only material color/texture, lighting, sky/background, and the
stair's alpha fade may differ between the two images.
