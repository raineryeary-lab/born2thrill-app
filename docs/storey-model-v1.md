# Storey model v1

`src/lib/generator/storey-model.mjs` is the shared, deterministic foundation for
multi-storey templates, stairs, and 1.5-storey headroom.

## Current reference corpus

The privacy-safe Simplifier snapshot contains:

- 157 projects,
- 75 labelled `bungalow`,
- 40 labelled `onehalfstorey`,
- 41 labelled `twostorey`,
- 1 labelled `other`,
- 83 projects with two habitable floors.

Two projects have a house-type/floor-count conflict. Of the 83 multi-storey
projects, 81 contain a stair annotation on both floors. None of these 81 pairs
is point-identical. The existing annotations therefore remain useful reference
geometry, but they do not yet satisfy the zero-tolerance shared-stair-core gate.

## Migration policy

The migration adapter:

- preserves every legacy room and element coordinate byte-for-byte,
- excludes basement floors from the new three-type model without deleting them,
- derives a provisional shared core from the ground-floor stair annotation,
- compares upper-floor slab openings with zero coordinate tolerance,
- marks every conflict for human review,
- never writes a migrated template into the production library.

Normalized legacy coordinates do not contain a reliable millimetre scale.
Consequently, stair dimensions and roof geometry are never guessed during
migration. Scale, floor-to-floor height, roof pitch, knee wall, ridge axis, and
dormers require explicit data or human confirmation.

## Storey types

- `1_storey`: ground floor only, no stair core.
- `1_5_storey`: ground floor plus roof storey, shared stair core and roof
  geometry required.
- `2_storey`: ground floor plus full upper storey, shared stair core required.

The selected storey type is an explicit planning input. A gable roof does not
silently turn a two-storey house into a 1.5-storey house.

## Stair solver

The default single-dwelling configuration uses:

- 900 mm clear width,
- maximum 200 mm rise,
- minimum 260 mm going,
- step measure from 590 to 650 mm, optimum 630 mm,
- minimum 2000 mm headroom,
- landing depth at least the clear flight width.

At 2800 mm floor-to-floor height the solver produces 16 risers at 175 mm,
280 mm going, and a 630 mm step measure. The default half-turn footprint is
2100 × 2860 mm. All values are configuration data so a future AT/CH or
state-specific profile can replace them without changing the solver.

## 1.5-storey area and room qualification

The module implements both independent calculations:

- WoFlV area bands: 100% at 2000 mm and above, 50% from 1000–1999 mm, and 0%
  below 1000 mm.
- Habitable-room gate: at least half of a bedroom polygon must have 2300 mm
  clear height under the configured roof.

The headroom geometry uses:

`distance = (height - kneeWallMm) / tan(pitchDeg)`

and clips room polygons against the resulting full-height band. A room that
fails the habitable-room gate must not be labelled as a bedroom.

## Customer-facing safety gate

The ZuhauseFinder webhook does not return a plan with critical geometry
failures. The authenticated caller receives HTTP 422 and the failed checks.
Generated customer files remain ineligible for training until a separate human
privacy and quality review approves them.

## Tests

Run:

```bash
node --test --test-isolation=none scripts/storey-model.test.mjs
```

The suite covers:

- every floor-to-floor height from 2400–3200 mm in 10 mm steps,
- the 2800 mm stair example,
- the 9 m / 40° / 1.2 m knee-wall headroom example,
- roof-bedroom qualification,
- deliberately misaligned, over-steep, and headroom-deficient stairs,
- lossless migration of all 157 current reference projects,
- review-only handling of legacy multi-storey stair conflicts.
