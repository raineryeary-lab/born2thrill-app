# Simplifier v1 integration

The Floorplan Simplifier handoff is imported locally as a privacy-safe reference dataset.

## Local import

```bash
node scripts/import-simplifier-handoff.mjs
```

Optional custom source:

```bash
node scripts/import-simplifier-handoff.mjs /path/to/floorplan-generator/simplifier-v1
```

The import writes:

- `data/simplifier-v1/dataset.json`
- `data/simplifier-v1/knowledge.json`
- `data/simplifier-v1/manifest.json`
- `data/simplifier-v1/README.md`

The command validates the current handoff counts:

- 15 projects
- 29 floors
- 162 room polygons
- 367 elements

It also checks that `other_1_5_story_with_cellar` keeps `house_type: "other"` and only derives cellar presence from a `basement` floor level.

## What is intentionally not imported

Raw PDFs, original previews, customer names, addresses, title blocks, and personal notes are not imported.

## Generator usage today

This is not model training.

The current rule-based generator consumes `knowledge.json` as a local reference for:

- room area target shares for EG living/kitchen, HWR/Technik, WC
- room area target shares for OG Eltern, Kinderzimmer, Bad, Flur
- visible quality-check labels showing the Simplifier reference basis
- common upper-floor room-program hints by derived reference house type
- element-count reference for doors, windows, and stairs

The full `dataset.json` is available for adapter tests and later normalization/training work, but it is not uploaded to cloud storage and not used as a trained model.

## Adapter contract

`src/lib/training/our-simplifier.ts` supports:

- old single-package imports for backwards compatibility
- `simplifier-annotations-v1` style `annotations[]` and `elements[]`
- privacy-safe exported `dataset.json`
- per-floor samples with preserved `floor_level`, `room_id`, `room_ids`, `area_m2`, `area_ratio`, `house_type`, and derived `has_cellar`
