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

Current local snapshot (2026-07-27):

- 157 projects
- 242 floors
- 1,527 room polygons
- 3,451 elements

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

The full `dataset.json` is available to the server-side reference selector and
for adapter tests. It contains only normalized geometry and typed elements; it
does not contain source documents or contact data and is not a trained model.

## Storey migration status

The current snapshot is a normalized reference corpus, not yet a fully
dimensioned canonical template library. `storey-model-v1` preserves the source
geometry, groups floors into explicit storey types, and reports stair-core and
roof-data gaps without repairing or approving them automatically. See
`docs/storey-model-v1.md`.

Because the export has normalized coordinates but no reliable millimetre scale,
it cannot prove DIN stair dimensions or roof-storey headroom on its own. Those
fields require explicit source scale and human confirmation before a migrated
template can become customer-facing.

## ZuhauseFinder webhook

`POST /api/zuhausefinder/floorplan` accepts the versioned
`dmh-floorplan-brief-v1` contract. It rejects incomplete or personality-only
requests, selects a real annotated reference, applies only controlled
variations, and returns a self-contained SVG as base64 JSON. See
`docs/zuhausefinder-webhook.md`.

## Adapter contract

`src/lib/training/our-simplifier.ts` supports:

- old single-package imports for backwards compatibility
- `simplifier-annotations-v1` style `annotations[]` and `elements[]`
- privacy-safe exported `dataset.json`
- per-floor samples with preserved `floor_level`, `room_id`, `room_ids`, `area_m2`, `area_ratio`, `house_type`, and derived `has_cellar`
