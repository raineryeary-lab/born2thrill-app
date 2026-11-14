# Annotation symbols: openings, fixtures and furniture groups

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Let the person annotating a floorplan record the architectural and furnishing
decisions the pipeline currently invents downstream, before the boss's 90–100
hand-picked plans are annotated. Every property below is nearly free to capture
while someone is already reading the plan, and expensive to add afterwards —
adding it later means re-opening 100 packages.

Two classes of change:

1. **Properties on openings that already exist** — window type, door swing,
   door width class.
2. **New placed symbols** — kitchen counter runs, sanitary fixtures, and
   furniture groups (dining group, L-couch, bed group), drawn by the annotator
   the same way stairs are drawn today.

The renderer then maps a symbol to a real 3D model at the annotated position.
No auto-placement, no inference.

## Current evidence and behavior

Verified by reading the code on 2026-08-08:

- **Every window in the corpus is a Brüstungsfenster.**
  `src/lib/generator/floorplan-rulebook.mjs:35-36` sets `defaultHeightMm: 1350`
  and `defaultSillHeightMm: 900`, and
  `src/lib/generator/blender-scene-manifest.mjs:53` applies `900` to any
  opening that is not a door. The Simplifier has no sill or window-type
  concept at all — grep for `sill`, `bruestung`, `bodentief` across
  `floorplan-simplifier` returns nothing.
- **A bodentiefes Fenster can only be faked as a glazed terrace door.**
  `src/lib/generator/correction-editor.mjs:334` forces terrace-door sill to 0.
  That is semantically wrong: fixed floor-height glazing is not traversable and
  is not a door, but facade analysis and every render currently treat it as one.
- **Door widths** are defined in `floorplan-rulebook.mjs:18-24` as
  `internalWidthMm: 880`, `smallWcWidthMm: 760`, `entranceWidthMm: 1100`,
  `terraceWidthMm: 1800`. Rainer states the entrance should be **1130**, not
  1100. Unresolved, see below.
- **Door swing is not recorded anywhere.** `scripts/render-furnished-dollhouse.py`
  (this session) infers swing side from room areas and hinge jamb from position
  along the wall. That is exactly the "silent geometry guessing" AGENTS.md
  prohibits, and it is the direct cause of this plan.
- **No kitchen or sanitary annotation exists.** In `plan-dc905efd8b1bbc28` the
  kitchen sits inside one open-plan `Wohnen / Essen / Kochen` polygon
  (52.14 m²) with nothing recording counter, sink, hob or appliances. Bathrooms
  carry no fixture data. This is why rendered kitchens and bathrooms are bare
  floor while the reference images Rainer supplied are fully fitted.
- **Furniture is currently auto-placed.** `src/lib/generator/furniture-placement.mjs`
  assigns one item per room-boundary edge by descending footprint. It produced
  22 items across 8 rooms with no sofa and no rug in the 2026-08-08 test render.
- Stairs already work the way this plan proposes: drawn by a human, stored as
  geometry, rendered deterministically. That is the pattern to copy.

## Repository baselines

- `born2thrill-local-workbench`, branch `agent/zuhausefinder-generator`.
  Working tree dirty with pre-existing uncommitted work (see
  `plans/HANDOFF-furnished-3d.md` §8) plus this session's new scripts. None of
  it may be reverted or cleaned by this plan.
- `floorplan-simplifier`, non-Git local project. Authoritative runtime data
  lives in its `projects/` directory and must not be moved or rewritten.
- `born2thrill-app-repo` — read-only for this plan.

## Exact scope

### A. Opening properties

1. `window_type`: `bruestungsfenster` (default) | `bodentief`. Drives sill
   height instead of the blanket 900 mm.
2. `sill_height_mm` and `height_mm` become explicitly annotatable, with the
   rulebook values applying only as the default for `bruestungsfenster`.
3. `swing_side`: which of the two adjoining spaces the leaf opens into.
4. `hinge_side`: which jamb it hinges on.
5. `width_class`: `entrance` | `internal` | `small` | `terrace`, resolving to
   the rulebook widths so a plan records intent rather than a raw number.
6. `door_type`: `hinged` (default) | `sliding` | `pocket` | `double`.

### B. New symbol types

Drawn as an oriented footprint with a type, exactly like stairs:

- **Kitchen**: counter run (straight / L / U), sink, hob, oven, fridge,
  tall-unit block.
- **Sanitary**: WC, washbasin, shower tray, bath.
- **Furniture groups**: dining seating group, L-shaped couch, sofa, bed group,
  wardrobe run.

Each symbol carries: type, footprint polygon (mm), orientation, and optional
free-text note. The renderer resolves type → 3D model; the annotation stores
position and intent only, never a model reference, so the model library can be
swapped without touching annotations.

### C. UI: a second tab, not more buttons

`floorplan-simplifier/static/annotate.html:22-29` is a single flat row of eight
tool buttons (Room area, Door, Opening, Window, Stairs, Balkon, Dachterrasse,
Align floors). The symbols above add roughly fifteen more. Twenty-three buttons
in one row is unusable.

Split into two tabs:

- **Architektur** — the existing eight tools. Feeds geometry of record and
  therefore `geometry_hash`.
- **Ausstattung** — kitchen, sanitary and furniture-group symbols.
  Presentation only, never enters `geometry_hash`.

The split is worth more than screen space: it puts the geometry/presentation
boundary into the interface, so the two cannot be confused by whoever is
annotating, and the invariant is visible rather than merely documented.

### D. Consumers

- Simplifier UI: tools to place and edit the above, on the Ausstattung tab.
- `annotations.json`: new optional fields and a new `symbols[]` array, additive
  under `simplifier-annotations-v1`.
- Workbench canonical conversion: map window type to sill height; carry symbols
  through.
- Renderer: place models from symbols; fall back to `furniture-placement.mjs`
  only where a room has no symbols.

## Files in scope

- `floorplan-simplifier` — annotation UI, save/load, `annotations.json` writer,
  `REFERENCE_STYLE.md` and `README.md` schema documentation.
- `born2thrill-local-workbench`:
  - `src/lib/generator/floorplan-rulebook.mjs` (width/sill defaults, additive)
  - `src/lib/generator/canonical-floorplan.mjs` + `.d.ts` (schema + validation)
  - `src/lib/generator/blender-scene-manifest.mjs` (stop defaulting sill to 900)
  - `src/lib/generator/correction-editor.mjs` (terrace-door sill rule vs the new
    `bodentief` type)
  - `scripts/render-furnished-dollhouse.py` (consume symbols; drop inferred swing)
  - New tests alongside each changed `.mjs`.

## Explicitly out of scope

- Re-annotating the existing 310 packages. They stay as they are; this plan
  serves the new 90–100.
- Any change to `geometry_hash`, the approval gate, or rights handling.
- Choosing or licensing 3D models for the symbol types.
- Removing `furniture-placement.mjs`. It stays as the no-symbol fallback.
- The second-tier items listed as unresolved below.

## API, schema, and data-contract effects

- `simplifier-annotations-v1` gains optional opening fields and an optional
  `symbols[]` array. Additive — existing packages remain valid and existing
  consumers keep working.
- Canonical floorplan schema gains the same, requiring a version bump and a
  compatibility check.
- `dmh-blender-scene-manifest` gains symbol placements — additive, version bump.

## Acceptance criteria

- A window annotated `bodentief` renders with sill 0 and full height, and is
  not classified as a door by facade analysis.
- A door renders with the annotated swing and hinge. No code path infers either.
- A kitchen symbol produces a counter run in the render at the annotated
  position and orientation.
- A package annotated before this change still loads, validates and renders.
- `geometry_hash` for an existing approved plan is byte-identical before and
  after this change.

## Tests and verification commands

- New: `scripts/annotation-symbols.test.mjs` — schema validation for every new
  field and symbol type, including rejection of unknown enum values.
- New: window-type → sill-height mapping cases, including the `bodentief` and
  terrace-door interaction.
- New: door swing/hinge round-trip through save → load → canonical → manifest.
- Extend the canonical schema tests for the version bump.
- Regression: `geometry_hash` unchanged for `plan-dc905efd8b1bbc28`.
- `node --test --test-isolation=none scripts/*.test.mjs`
- Simplifier: `python -m unittest discover -s tests -p "test_*.py"`

No existing test is deleted, skipped or weakened by this plan.

## Protected and risky paths

- `geometry_hash` and `validateCorrectionDocument` — symbols and furniture are
  presentation data and must not enter the hash, or every already-approved plan
  is invalidated.
- `correction-editor.mjs:334` terrace-door sill rule — must keep working while
  `bodentief` windows are introduced alongside it.
- The Simplifier's `projects/` directory is authoritative local data. Schema
  changes must be read-compatible with every package already in it.

## Rights, provenance, privacy, and security impact

None directly. Symbols record intent, not model references, so no third-party
asset licensing enters the annotation data. The separate open question about
commercial rights in the CGAxis/3DSky/Arroway libraries is unaffected by this
plan and remains unanswered.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Required answer: no. Symbols and opening properties are annotation inputs
consumed only after `validateCorrectionDocument`, identical to today's gate.
Symbols do not enter `geometry_hash`, so nothing here lets geometry bypass
approval. No new export, publish or send path is introduced.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

(none yet — not implemented)

## Rollback

All schema additions are optional fields plus one new array. Rollback is
reverting the diffs; packages annotated with the new fields still load under the
old code, which ignores unknown keys.

## Unresolved questions

1. **Entrance door width: 1100 or 1130 mm?** The rulebook says 1100. Rainer
   says 113. Must be settled before annotation begins — it is baked into every
   plan otherwise.
2. Second-tier properties, to include now or defer: storey height, per-room
   floor finish, niches/built-ins (roadmap ENTRY-WARDROBE-VARIANT-001),
   load-bearing vs non-load-bearing walls.
3. How much fixture detail is worth annotating — is a bathroom "shower tray +
   WC + basin" enough, or does tap/fitting placement matter for the render?
4. Delivery date for the 90–100 plans. If days rather than weeks, cut scope to
   §A plus kitchen and sanitary symbols only.

## Approval record

Not approved. Stop before implementation.
