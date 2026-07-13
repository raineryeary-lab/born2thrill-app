# Floorplan Generator handoff

This folder is a local, privacy-safe export from Floorplan Simplifier.

`simplifier-v1/dataset.json` contains normalized room polygons and door, window,
and stair elements grouped by project and floor. `knowledge.json` contains the
aggregate room-program statistics that the Generator can use immediately as a
reference baseline. `manifest.json` is the compact import check.

Raw PDFs, original previews, customer names, addresses, title blocks, and notes
are deliberately excluded.

Regenerate the bundle with:

```bash
python3 scripts/export_generator_dataset.py projects exports/floorplan-generator/simplifier-v1
```

The Generator should treat `dataset_version` and `source_schema` as versioned
contracts. It should reject unknown major versions instead of guessing.
