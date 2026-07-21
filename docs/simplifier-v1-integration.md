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

The command calculates the current handoff counts and requires exact agreement
between `dataset.json`, `manifest.json`, and the `knowledge.json` basis. Counts
are intentionally not hardcoded, so a larger valid v1 dataset can be imported
without changing application code.

Current local snapshot (2026-07-19):

- 110 projects
- 194 floors
- 1,149 room polygons
- 2,593 elements

The importer rejects unknown dataset/schema versions, missing or unsafe privacy
flags, malformed element counts, and any manifest/knowledge count mismatch.
Cellars are identified only by the typed `floor_level: "basement"` field; no
specific project ID or localized room name is required.

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
