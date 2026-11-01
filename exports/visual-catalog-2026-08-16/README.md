# Visual catalog export

This folder contains four selected isometric interior concepts and one exterior reference image.

- `catalog.json` is the canonical machine-readable catalogue for database import.
- `catalog.csv` is the flat searchable index for spreadsheets or a simple importer.
- `interior-dark-modern-final.png` is the current preferred interior candidate.
- The other three interiors remain style candidates; their open-Garderobe review is recorded in `qc_status`.
- `exterior-gabled-garden-reference.png` is a visual-quality reference. Its geometry is not verified against the current floor plan.

Source Blender file: `C:/dev/Floorplan-tools/born2thrill-local-workbench/tmp/kitchen-inspect.blend`

Recommended database fields: `asset_id`, `file`, `asset_type`, `style`, `palette`, `materials`, `rooms_visible`, `features`, `view`, `geometry_lock`, `qc_status`, `description_de`, and `search_text_de`.
