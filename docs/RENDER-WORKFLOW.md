# End-to-end render workflow (as it actually exists, 2026-08-16)

This replaces earlier verbal summaries that were incomplete or wrong (missed
the review-loop mechanism, the patch/diagnostic scripts, and the one saved
interior `.blend`). Every stage below is verified against real files, not
inferred. Status tags: **LIVE** (working today) / **PROOF-ONLY** (runs, but
not deliverable) / **PROPOSED** (planned, not built) / **GAP** (missing).

## 1. Annotate — LIVE

`floorplan-simplifier`: draw rooms, walls, doors, windows, furniture
symbols, exterior outline, roof overhang. Saved per-project as
`floorplan-simplifier/projects/<id>/annotations.json`. Source of truth for
everything downstream — door swing, symbol rotation, footprint, are all
explicit fields here, never to be re-derived by a heuristic.

## 2. Canonical geometry — split, one gap

- **Interior — LIVE, canonical.** `scripts/build-furnished-render-plan.mjs`
  reads approved canonical geometry, runs the real furniture-placement
  engine, resolves each placement to a `.glb`, writes a render-plan JSON
  carrying a `source_geometry_hash`.
- **Exterior — PROOF-ONLY, GAP.** `scripts/build-simplifier-render-plan.py`
  reads `annotations.json` directly and emits a render-plan JSON, but its own
  header says its output must never be delivered (`not_for_delivery: True`,
  `source_geometry_hash: None`). `render-exterior.py` consumes this plan
  anyway and does not check that flag. **There is no canonical exterior-plan
  builder anywhere in the repo today** — every exterior render this project
  has produced structurally traces back to a non-deliverable proof document.
  Closing this gap needs its own plan before exterior renders can ever reach
  a customer.

## 3. Render — LIVE (headless, no saved scene by default)

- **Interior**: `blender --background --python scripts/render-furnished-dollhouse.py -- <plan.json> <out.png>`
  Outputs one PNG. Does not save a `.blend` unless someone explicitly does so.
- **Exterior**: `blender --background --python scripts/render-exterior.py -- <plan.json> <out.png>`
  Outputs color + depth + edge passes, plus a structure mask (white-emission
  render of everything except ground/site areas, used for polish masking).
  Modern (flachdach) or classic (walmdach) style from `plan["style"]`.

## 4. Diagnose + patch loop — LIVE, this is the real iteration engine

Nothing in this project gets fixed by guessing from an image. Each round:

1. **Measure** — small scratch scripts dump real object state:
   `tmp/measure_blend.py`, `tmp/inspect_kitchen.py`, `tmp/facing_sheet.py`,
   `tmp/sofa_contact_sheet.py`, `tmp/violet_contact_sheet.py`. These produce
   the "state proof" the evidence-first protocol (below) requires.
2. **Patch** — targeted fixes applied via `tmp/patch_renderer.py`,
   `tmp/patch_builder_v2.py`, `tmp/patch_blend_import.py`,
   `tmp/patch_fixes.py`, `tmp/patch_shell.py`, `tmp/patch_underlay.py`.
3. **Re-render and snapshot** — every round leaves a
   `tmp/kitchen-vN.manifest.json` + matching PNG (rounds 4–11 exist for the
   kitchen specifically; also `oven-face-0/90/180/270.manifest.json` for
   orientation trials). This is the audit trail.
4. Only one scene from this whole loop was ever saved as an editable
   `.blend`: **`tmp/kitchen-inspect.blend`** (331 MB, last saved 2026-08-11).
   Everything else is headless-only, regenerated from script + JSON each
   time. The exterior loop is different — see §6.

## 5. Review loop ("codex") — LIVE, read-only second opinion

This is what "give it to Codex" actually means in this project: NOT Codex
executing Blender, but a read-only review pass. Pattern used repeatedly
(`tmp/review-request.md` through `review-request-6.md`, plus the original
`tmp/ask-codex.md` → `tmp/codex-protocol.md` exchange):

1. Write a `review-request-N.md`: attach the render/description, name the
   exact files to read, state what's already been tried, ask a specific
   falsifiable question.
2. Run it through Codex read-only (`/codex` skill in this session, or a
   separate Codex CLI session).
3. Codex answers with file:line evidence, not vibes.
4. Findings get applied back into the actual scripts by Claude/whoever's
   driving, then loop back to step 4 above (re-render, re-verify).

The governing discipline (`tmp/codex-protocol.md`, written after a full day
of heuristic-guessing failures) is short and mechanical:
explicit user data > canonical source > measured property > documented
default > heuristic (only with approval). No "fixed" without input/path/
state/output proof. After 3 failed hypotheses, stop and reassess from the
data path, don't produce a 4th narrative.

## 6. Exterior versioning — LIVE, different from interior

Unlike interior, the exterior loop **does** save a numbered `.blend` per
iteration: `tmp/exterior-modern-v1.blend` through `v23.blend`,
`tmp/exterior-classic-v1.blend` through `v13.blend` (plus matching
`-depth.png` / `-edge.png` / `-mask.png` per version from v10 onward). This
is the actual audit trail behind "codex did a much better job on the
exterior" — it's a longer, better-instrumented version of the same loop as
§4/§5, just with persisted scene snapshots at every step.

## 7. Exterior polish — LIVE, geometry-locked by hard rule

Two scripts, not one:
- `scripts/comfyui-polish-exterior.py` — canny + depth ControlNet img2img
  pass, three mood variants (`morning` / `golden_hour` / `midday`, each with
  its own fixed seed), style-aware prompt.
- `scripts/composite-mask-polish.py` — combines a low-denoise "safe" building
  pass with a high-freedom "atmospheric" pass using the structure mask from
  §3, feathered blend.

**Hard rule** (memory: `comfyui_polish_geometry_lock`): polish must never
alter window/door/wall layout — only atmosphere. Verified 2026-08-16 by
direct crop comparison: opening count/position/size are preserved correctly.
What the polish *does* legitimately invent on top of real openings: door
handle hardware, material finish, glazing reflections, window mullion
pattern — treated as acceptable material-level embellishment, same class as
the prompt's own frame-color direction, not a layout violation. Also worth
checking separately: the raw Blender door render shows zero relief detail
despite using a real named asset (`DOOR_ASSET`,
`Metal_Front_Door_3D_Model_7961`) — unconfirmed whether that's a load
fallback bug or just flat preview lighting.

## 8. Quality/rights gate — LIVE

Every catalog project carries `quality_status`, `approval_status`,
`source_rights_status`, `commercial_generator_eligible`,
`reconstruction_only`. Nothing downstream may treat a project as
customer-eligible without these. Importing/rendering a project does not
itself change these values.

## 9. Catalog — LIVE

`scripts/build-floorplan-search-catalog.mjs` batch-processes all projects →
`data/simplifier-v2/search-catalog.json` (310 projects today). Deterministic,
`--check` mode byte-compares against disk.

**GAP**: render output files (PNGs) are not referenced anywhere in this
catalog or in any database. Every render, interior or exterior, is a loose
file in `tmp/`, disconnected from the searchable project record.

## 10. DB import — PROPOSED, not built

`born2thrill-app-repo/plans/catalog-database-import-v1.md`. Additive
Postgres table on the Railway side (`railway/migrations/`, not
`supabase/migrations/` — confirmed two separate database instances).
Status: PROPOSED, not approved, nothing has run against any database.

## 11. Customer questionnaire — LIVE, conditional persistence

`born2thrill-app-repo/src/app/questionnaire/`. Saves structured requirements.
Three actual behaviors depending on state:
- Unauthenticated submission → prototype result, **not persisted at all**.
- Authenticated + `DATABASE_URL` set → Railway Postgres `projects.requirements`.
- Authenticated + no `DATABASE_URL` → Supabase fallback insert.

## 12. Matching — LIVE, just not wired to the questionnaire

Two matchers already exist:
- `selectApprovedFloorplan()` (`src/lib/generator/approved-floorplan-catalog.ts`)
  — matches a `HouseBrief` to approved plans by storey/bedrooms/office/
  guest-WC/utility + area ranking.
- Workbench catalog-search API — filters `search-catalog.json` by house
  type, floor count, basement, rights/usage, tags, room minima.

**GAP**: nothing reads a saved `projects.requirements` row and feeds it into
either matcher automatically. That bridge, not a new matcher, is the real
next piece.

## 13. Delivery — manual only, by hard policy, permanently

`AGENTS.md` (both repos, identical wording): customer delivery requires
valid geometry, explicit human approval, safe JPEG artifacts, and the
WordPress manual email gate. Automatic customer sending "cannot enter as
incidental changes." This does not change regardless of what gets automated
upstream — matching can propose candidates, a human still sends them.

---

## Storage inventory — verified 2026-08-16 (Codex read-only filesystem walk)

### Outside the repo (external drives)

| Path | Referenced by | What it is | Confirmed |
|---|---|---|---|
| `F:\` | `c4d-batch-export-fbx.py:23`, `extract-cgaxis-catalogues.py:79` | Source CGAxis/Cinema4D library (bathroom/kitchen/bedroom/furniture categories) | yes |
| `E:\_models_converted` | `c4d-batch-export-fbx.py:24` | FBX library converted from F:\ — indexed by `tmp/fbx-library-catalog.json` (1,160 entries) | yes |
| `E:\_models_hub\_extracted` | `render-furnished-dollhouse.py:263` | Extracted `.blend` furniture/door/window library — indexed by `tmp/hub-model-catalog.json` (94 entries) | yes |
| `E:\_maps` | `render-furnished-dollhouse.py:41` | Default texture-map root (`DMH_TEXTURE_ROOT` overridable) | yes |

These external libraries are **only indexed**, not copied — `full-catalog`/
`test-batch` under `data/furniture-assets/` are the one exception (39 `.glb`
models, self-contained inside the repo, not backed by E:\).

### Inside the repo — `.blend` scene files

**36 files total, 1.27 GiB.** Almost all of it (34 files, 1.269 GiB) is flat
scratch space in `born2thrill-local-workbench/tmp/`:
- `exterior-modern-v3` through `v23` (20 files) + `exterior-classic-v2`
  through `v13` (12 files) — sequential iteration snapshots, no `v1`/`v2`
  saved for modern.
- `kitchen-inspect.blend` — 331.9 MB, the one interior debug scene, saved
  2026-08-11.

The remaining 2 `.blend` files live in the **separate**
`born2thrill-local-workbench-data` repo, under
`corrections/onehalfstorey_020/blender/<hash>/` — and belong to a different
project entirely (`onehalfstorey_020`, not `bungalow_040_66`).

### Inside the repo — render output images

`born2thrill-local-workbench/tmp/` holds **364 PNGs, 697 MB** — the single
flat dump for every dollhouse render, exterior pass, ComfyUI polish output,
comparison crop, and debug probe this whole project has produced. No
subfolder-per-project convention; everything is one directory. Breakdown:
exterior-modern (92 files), exterior-classic (34), depth passes (27), edge
passes (27), structure masks (10), image-gen/polish variants (30), "final"
renders (33), plus interior dollhouse/kitchen iterations making up the rest.

**No render for `bungalow_040_66` exists anywhere outside this scratch
folder.** The one durable, versioned image store in the whole suite —
`born2thrill-local-workbench-data/corrections/*/exports/` (94 export images
across 47 revisions, for `bungalow_040_15`, `onehalfstorey_020`,
`twostorey_030`, `twostorey_051`, and test projects) — **has never held
anything for `bungalow_040_66`.**

### Inside the repo — plan JSON and manifests

All scratch, all in `tmp/`, nothing durable exists anywhere else:
- **17 render-plan JSONs** (`plan.json`, `plan-classic*.json`,
  `plan-debug*.json`, `render-plan-040_66-*.json`, etc.) — 16 for
  `bungalow_040_66`, 1 for a different plan.
- **53 `*.manifest.json` review-loop sidecars** (kitchen/oven/chair/probe/
  morning-fix rounds).
- Both plan-builder scripts (`build-furnished-render-plan.mjs:149`,
  `build-simplifier-render-plan.py:954`) accept an arbitrary output path from
  the caller — they don't enforce or default to any canonical location.
  Every caller so far has chosen `tmp/`.

### The actual bottom line

For the project this whole session has worked on, **every render, every
plan JSON, every manifest, and every saved scene lives only in
`born2thrill-local-workbench/tmp/` — flat, ephemeral, zero durable storage.**
The one durable/versioned storage convention that exists in this suite
(`born2thrill-local-workbench-data/corrections/`) has simply never been
pointed at this project. That's the real gap behind "I don't know if this is
saved anywhere" — it isn't, durably, for this project, anywhere.

## Open gaps, in priority order

1. **No durable storage for this project's output at all** — every `.blend`,
   PNG, plan JSON, and manifest for `bungalow_040_66` lives only in
   `tmp/` scratch space. The suite's one durable image/scene store
   (`born2thrill-local-workbench-data/corrections/`) has never been used for
   it. This is upstream of every other gap below — nothing is safe from
   being lost or overwritten until this exists.
2. **Exterior canonical geometry** (§2) — no non-proof builder exists; this
   blocks exterior renders from ever being customer-deliverable.
3. **Render-to-catalog link** (§9) — no render file is tracked anywhere.
4. **Questionnaire-to-matcher bridge** (§12) — smaller than it sounds, both
   matchers already exist.
5. **DB import** (§10) — plan written, awaiting approval to build against a
   scratch database.
6. Task #9 (window glass material still bad) — next candidate for the
   diagnose/review loop in §4/§5.
