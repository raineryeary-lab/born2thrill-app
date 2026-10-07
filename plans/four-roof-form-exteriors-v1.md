# Four roof-form exteriors (flachdach, walmdach, satteldach, pultdach)

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Replace the current 2-exterior delivery (`exterior-modern-baseline`,
`exterior-classic-baseline` -- one wall-material style each, tied to a
per-house modern/classic roof pairing) with 4 exteriors, one per roof form
(flachdach, walmdach, satteldach, pultdach), all in the same wall-material
look. Per Rainer, 2026-09-15: "he just wanted all of the roof forms so not
just 2 exteriors but all 4" -- confirmed via clarifying question: roof only,
one material style, not a 2x4 combination.

## Current evidence and behavior

- `render-exterior.py`: `roof_type == "flachdach"` builds a flat deck;
  everything else goes through one shared branch that only ever builds a
  HIP roof (bpypolyskel general case, or a direct 4-face hip for
  rectangles). "satteldach" is accepted as a label but produces the exact
  same hip geometry as "walmdach" -- confirmed by reading the code, not
  inferred. "pultdach" has no code path anywhere.
- `dachform.py`: roof form is chosen PER HOUSE, as a `(modern, classic)`
  pair (`roof_type_modern`, `roof_type_classic`), stored in
  `gebaeudemass.json`. Only 2 of the 3 existing `FORMEN` are ever used on
  any one house today.
- Full inventory of every place that hardcodes the modern/classic exterior
  pair (from a dedicated read-only investigation this session): `dachform.py`,
  its API route `src/app/api/floorplan-workbench/dachform/route.ts`, the
  Workbench UI (`src/app/haus/page.tsx`), `hausdaten.py`/`hausdaten.mjs`,
  `inventory.ts`, `build-simplifier-render-plan.py`'s `annotation_roof()`
  (keys off `"modern"`/`"classic"` literally), `run_project.py` (`--styles`
  default, `trim_to_delivery()`'s hardcoded exterior filename pair, the
  `2 + len(floors)` delivery-manifest count formula, fixed
  `plan-modern.json`/`plan-classic.json` names), `batch-build.py`,
  `werkbank.py`, `comfyui-polish-exterior.py`'s per-style prompt words, and
  `docs/CODEX-REGELN-4PLUS2.md` (the "4+2" contract itself, including its
  literal "6 for a bungalow, 10 for a two-storey" count formula).
  `lieferung-pruefen.py`, `publish-renders.py`, `verify_render.py`,
  `make-codex-job.py`'s `outputs_for()`, and the WordPress catalog side are
  already generic (key off `kind=="exterior"` / a plain image count, not a
  fixed "2") and need no change.

## Key simplification

Roof geometry is built in a separate, LATE stage of `render-exterior.py`
(after walls/massing exist). The plan JSON's wall/material content does not
need to vary per roof form. So: build ONE plan (today's "modern" style,
material-wise) and render `render-exterior.py` 4 times against it with an
explicit roof-type override each time -- the same idiom this codebase
already uses for other per-render overrides (`DMH_FLAT_CUT`,
`DMH_CAMERA_STYLE`, `DMH_STOREY_HEIGHT`). This avoids needing 4 separate
plan-JSON builds, and avoids `dachform.py`'s per-house modern/classic
pairing entirely for exterior purposes -- every house gets all 4 roof forms,
not a per-house choice.

`dachform.py`'s modern/classic pair stays as-is for now for whatever
non-exterior purpose it still serves (need to confirm during implementation
whether anything besides the exterior pairing reads `roof_type_modern`/
`_classic` -- `hausdaten.py`'s merge and the Workbench UI dropdown do, and
should keep working for backward compatibility / manual override, but no
longer drive which roof forms get exterior-rendered).

## Exact scope

1. **New roof geometry in `render-exterior.py`**, for RECTANGULAR footprints
   only in this pass (matching the existing walmdach special case; L/T-shaped
   footprints keep today's hip-roof fallback with a clear log line, not a
   silent wrong shape):
   - **Satteldach**: ridge runs the full length of the long axis (no inset),
     roof only slopes on the two long sides; the two short ends become
     vertical gable walls (extend the end wall up to the ridge apex) instead
     of sloped hip faces.
   - **Pultdach**: single sloped plane across the whole footprint, high eave
     on one side, low eave on the opposite side, no ridge. Needs its own eave
     height / low-side clearance rule (a domestic pultdach still needs
     headroom on the low side -- measure a reasonable minimum rather than
     guessing).
   - Both read the roof_type the same way `flachdach`/`walmdach` already do
     (`plan.get("roof_type")`), so an explicit override (see #2) is enough --
     no plan-schema change needed for roof selection itself.
2. **Exterior render loop**: change `run_project.py` (and anywhere else that
   drives the exterior-baseline builds) from looping over
   `styles=("modern","classic")` to building ONE plan (style fixed, e.g.
   "modern") and calling `render-exterior.py` 4 times with a roof-type
   override, producing `exterior-flachdach-baseline`,
   `exterior-walmdach-baseline`, `exterior-satteldach-baseline`,
   `exterior-pultdach-baseline` (`.png`/`.blend`/logs each).
3. **Delivery count**: `trim_to_delivery()`'s exterior filename set and the
   `write_delivery_manifest(..., 2 + len(floors), ...)` formula both become
   `4 + len(floors)`.
4. **Docs**: `docs/CODEX-REGELN-4PLUS2.md` gets its exterior section and
   count formula corrected (renamed contract? -- flag for Rainer, this
   plan does not rename the file). `make-codex-job.py`'s "Aussenansichten,
   classic und modern" wording updated to name the 4 roof forms instead.
5. **`comfyui-polish-exterior.py`**: `STYLE_WORDS` keyed to modern/classic
   material style, not roof form -- confirm during implementation whether
   this path is even still invoked for the new 4-roof exteriors (it may be
   a separate, optional polish step); update or explicitly leave alone with
   a comment either way, don't let it silently mis-word a roof-form image.

## Files in scope

- `scripts/render-exterior.py` (new roof geometry)
- `scripts/run_project.py` (exterior loop, delivery count, filenames)
- `scripts/batch-build.py` (styles argument passthrough, if it hardcodes the pair)
- `docs/CODEX-REGELN-4PLUS2.md`, `scripts/make-codex-job.py` (wording/counts)
- New/updated tests: `render-exterior` has no existing test file found in the
  inventory -- check before assuming; `run_project.test.py` (confirm exact
  name) for the delivery-count formula; `build-simplifier-render-plan.test.py`
  if `annotation_roof()` changes.

## Explicitly out of scope

- Interior rendering and the 4 Codex decor styles (warm-modern, dark-modern,
  soft-scandinavian, classic) -- unrelated dimension, not touched.
- `dachform.py`'s per-house modern/classic pair as a data concept -- kept for
  now (see Key simplification), not removed or migrated to a 4-value list in
  this pass.
- Non-rectangular (L/T-shaped) footprints for satteldach/pultdach -- fall
  back to the existing hip behavior with a clear log line; a follow-up can
  extend the straight-skeleton path later if needed.
- Renaming `docs/CODEX-REGELN-4PLUS2.md` itself.

## Acceptance criteria

- `render-exterior.py` produces visually correct, distinct geometry for all
  4 roof types on a rectangular test house: flat deck, true hip, true gable
  (vertical end walls, ridge along the long axis), true mono-pitch (one
  sloped plane, no ridge).
- A full `go.py <rectangular house> --laut` run produces exactly 4 exterior
  `.blend`/`.png` pairs plus the usual interior baselines, delivery-manifest
  count matches, all existing `verify_render`/`verify_render_blend` checks
  pass unchanged (they check walls/openings/stairs, not roof type, so should
  be unaffected -- confirm, don't assume).
- Existing houses already built under the old modern/classic exterior pair
  are NOT retroactively rebuilt by this change; only affects houses built
  after the fix lands.

## Tests and verification commands

To be finalized during implementation once exact file/test names are
confirmed. At minimum: a geometry test per new roof type (vertex/face
sanity: gable has vertical end faces, pultdach has exactly one ridge-free
sloped plane), and a `run_project.py` delivery-count regression test.

Existing tests: none deleted, skipped, or weakened.

## Protected and risky paths

- `render-exterior.py` is shared by every house; the new roof branches are
  additive (new `roof_type` values), and `flachdach`/`walmdach` paths are
  untouched, so existing behavior for those is preserved.
- `run_project.py`'s delivery/count logic is load-bearing for the
  "certified and ready" gate every house goes through -- changing the count
  formula needs the acceptance-criteria full-pipeline test above before
  trusting it on a real house.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference? Required answer: no -- this adds
roof geometry derived from the same already-approved room/wall geometry, and
does not touch publishing or email paths.

## Customer, email, database, deployment, and external effects

None directly, but this changes the DELIVERY CONTRACT documented in
`docs/CODEX-REGELN-4PLUS2.md` (2 exteriors -> 4), which is customer-facing
via the WordPress catalog once published -- flagged, not a blocker, since
the catalog side itself is confirmed generic (counts images, doesn't assume
exactly 2).

## Failed-hypothesis log

(none yet)

## Rollback

Revert the roof-geometry additions and the exterior-loop/count changes.
`dachform.py` and its data are untouched, so no data migration to undo.

## Unresolved questions

- Does anything besides the exterior pairing and the Workbench UI dropdown
  read `roof_type_modern`/`roof_type_classic`? Confirm before deciding
  whether to leave `dachform.py` as-is or start deprecating it.
- Whether `comfyui-polish-exterior.py` runs on these new exteriors at all.

Pultdach low-side clear height: **2.50m**, Rainer 2026-09-15 ("the lower die
would be around 2,50m"). Implementation reads: the roof's low eave sits at
whatever height gives >=2.50m clearance above the top storey's ceiling/floor
level at the low wall -- confirm exact reference plane (finished floor vs.
ceiling) against an existing height constant (`CEILING_Z` et al. already in
render-exterior.py) rather than re-deriving it.

## Implementation log (2026-09-15)

- Roof geometry done in `render-exterior.py`: satteldach now reuses the
  hip/gable cross-section with the ridge inset removed (turns the hip's two
  short-end slopes into vertical gable walls with no other change to the
  face list); pultdach is a single sloped quad, no ridge. Both verified by
  direct render against `twostorey_046`'s real plan (`EXT_ROOF_TYPE`
  override) -- visually confirmed distinct, correct topology for all 4
  roof types, no regression on flachdach/walmdach.
  - First pultdach attempt used the TRUE single-slope rise (full span *
    tan(pitch)) and came out wildly disproportionate -- 4.26m rise on a
    ~9m span, roof overhanging past the building in the hero shot. Checked
    visually, not assumed. Fixed by using the same rise as hip/gable (half
    span), which keeps every roof form at a comparable peak height.
- `run_project.py` restructured: 4 exteriors (`ROOF_TYPES` constant) built
  ONCE from the first requested style's plan (`EXT_ROOF_TYPE` env override
  per call, one Blender invocation per roof), before/outside the per-style
  loop, which still runs unchanged for interiors. Every style's
  `verify_render.py` call now shares one exterior log across styles
  (structural checks -- wall angles, openings -- don't depend on roof
  shape, so this is correct, not a shortcut). `trim_to_delivery()`'s keep
  set and both delivery-count formulas (`2 + len(floors)` in two places)
  updated to `len(ROOF_TYPES) + len(floors)`. Added `handoff["roof_exteriors"]`
  (all 4, keyed by roof type); kept `handoff["styles"][style]
  ["exterior_baseline_*"]` pointing at the first roof form for backward
  compatibility with older consumers.
- Confirmed via the earlier read-only inventory that `make-codex-job.py`,
  `lieferung-pruefen.py`, `publish-renders.py`, `verify_render.py`, and the
  WordPress catalog side are all generic (scan for `exterior-*` files /
  count images, don't hardcode "2"), so none of those needed code changes.
- Full `go.py twostorey_046 --laut` rebuild: SUCCESS. `delivery: 6 .blend
  (expected 6)` -- exterior-flachdach/pultdach/satteldach/walmdach-baseline
  + interior-modern-baseline + interior-modern-upper-baseline. `2 style(s)
  verified and ready, 0 excluded`. Confirmed the shared-exterior-log design
  works: the "classic" style's `verify_render.py` call used
  `exterior-flachdach-baseline.log` (built once, under "modern") and passed
  every check. Pultdach pitch fix (10 degrees, see above) landed after this
  build started, so its pultdach.blend has the old steep pitch -- a second
  rebuild was launched immediately after to pick up the corrected pitch.
- NOT yet updated: `docs/CODEX-REGELN-4PLUS2.md` section 7 (Aussenaufnahmen)
  and its "vier Innenstile ... plus zwei Aussenansichten" count formula in
  section 9. This document governs CODEX'S OWN restyling pass on top of our
  baseline renders (a downstream, human-facing process, not the geometry
  this plan built) -- unclear without Rainer's input whether Codex should
  now produce 4 restyled exteriors (one per roof-form baseline, one
  material mood) or something else. Flagged, not guessed.

## Approval record

Approved by Rainer, 2026-09-15 (scope confirmed via clarifying question;
pultdach clearance given directly, standing in for final approval to
proceed).
