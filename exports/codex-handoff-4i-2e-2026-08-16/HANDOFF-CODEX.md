# Codex handoff: 4 interiors + 2 exteriors

## Objective

Import this self-contained visual set into the active Born2Thrill/Floorplan Tools project without overwriting existing approved assets. Preserve the six images exactly, store them in a durable project-owned folder, and make their metadata searchable.

## Required first action in the receiving Codex task

1. Read this file and `selected-catalog.json`.
2. Inspect the destination repository instructions and existing visual-catalog schema.
3. Do not regenerate, restyle, rename, delete, or overwrite any of the six images.
4. Copy the complete handoff folder to a versioned project path such as `exports/visual-catalog/<plan-family-id>/`.
5. Import or map `selected-catalog.json` into the existing catalogue. Preserve `qc_status` exactly.
6. Validate that all six referenced files exist and produce a report containing destination paths, asset IDs and import results.

## Geometry sources

- Interior source: `C:/dev/Floorplan-tools/born2thrill-local-workbench/tmp/kitchen-inspect.blend`
- Exterior source: `C:/dev/Floorplan-tools/born2thrill-local-workbench/tmp/exterior-classic-v19.blend`
- The exterior Blender file contains the updated rear-garden camera used for image 06.

## Selected assets

### 01 — Warm Modern

File: `01-interior-warm-modern.png`

Warm oak, taupe, oatmeal textiles and restrained black accents. This is a style candidate, not geometry-approved. The Garderobe still requires alignment review.

### 02 — Soft Scandinavian

File: `02-interior-soft-scandinavian.png`

Pale oak, off-white, muted sage and soft woven textiles. This is a style candidate; the Garderobe still requires alignment review.

### 03 — Modern Architectural

File: `03-interior-modern-architectural.png`

Smoked oak, limestone, charcoal and warm-grey upholstery. This is a style candidate; the Garderobe design still requires review.

### 04 — Dark Modern Final

File: `04-interior-dark-modern-final.png`

Preferred interior candidate. Dark timber flooring, matched cognac-leather sofa and armchair, open slatted Garderobe with hooks/bench/shoe storage/mirror, and a compact six-seat dining group.

### 05 — Classic v19 Front Exterior

File: `05-exterior-classic-v19-front.png`

Preferred front/entrance candidate generated from the v19 Blender geometry: warm-white render, clay hip roof, anthracite openings, connected paving and structured garden.

### 06 — Classic v19 Rear Terrace

File: `06-exterior-classic-v19-rear-terrace.png`

Preferred rear-garden candidate generated from the updated v19 rear camera. Coordinated six-seat outdoor dining, matching lounge collection, barbecue, planters and landscaped terrace.

## Non-negotiable rules for later work

- Blender/canonical geometry remains authoritative. Generated images are visual concepts, not a replacement for geometry.
- Never move, add or remove walls, roofs, windows or doors in a style-only operation.
- An object semantically named `garderobe` is a placeholder for a real concept-matching entrance Garderobe, not a generic closed closet.
- Garderobe replacements must stay wall-aligned, within the placeholder footprint, and must not block WC, Büro or circulation.
- Keep Büro and Ankleide cabinets unless explicitly targeted.
- Keep kitchen oven/high cabinet and fixed kitchen geometry.
- Dining groups must be realistically scaled and maintain circulation; six seats means exactly six chairs.
- Sofa and armchair should use the same upholstery family unless an explicit concept says otherwise.
- Save every derivative as a new version. Never overwrite these six handoff originals.
- Only assets marked `preferred_candidate` may be offered as preferred. Draft review flags must remain visible.

## Database/search contract

Use `asset_id` as the stable unique key. Index at minimum: `plan_family_id`, `asset_type`, `style`, `palette`, `materials`, `rooms_visible`, `features`, `camera_view`, `geometry_source`, `qc_status`, `description_de`, and `search_text_de`.

## Acceptance checks

- Exactly six PNG files are present.
- Each file has one matching `asset_id` in `selected-catalog.json`.
- JSON parses successfully.
- No existing asset is overwritten.
- The receiving task reports the final durable folder and any database rows created or updated.
