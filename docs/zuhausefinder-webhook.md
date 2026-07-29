# ZuhauseFinder floorplan webhook

## Endpoint

```text
POST /api/zuhausefinder/floorplan
Authorization: Bearer <ZUHAUSEFINDER_WEBHOOK_TOKEN>
Content-Type: application/json
```

The token is stored only as a server-side environment variable. A public
`GET` request returns service/schema health information but never generates a
floorplan.

## Input

The endpoint accepts only `dmh-floorplan-brief-v1`. Required planning evidence:

- public request ID,
- target living area between 70 and 400 m²,
- bungalow, 1.5-storey, or 2-storey candidate,
- household description,
- explicit room program,
- explicit public/living-zone description,
- `reference_first: true`,
- `invent_from_personality: false`.

Names, email addresses, birth dates, and other contact data are not accepted or
needed.

## Generation

The generator:

1. maps the explicit brief to the internal house constraints,
2. selects from the privacy-safe Simplifier reference corpus,
3. keeps annotated room, door, window, and stair geometry,
4. maps the selected house type to the shared `1_storey`, `1_5_storey`, or
   `2_storey` model,
5. derives one shared stair core for every multi-storey result,
6. applies only small controlled variations,
7. renders a self-contained SVG with scaled wall widths and wall openings,
8. rejects scripts, event handlers, external URLs, foreign objects, and other
   active SVG content.

The best available reference is checked before rendering. A candidate with a
critical geometry failure is never returned as a customer-facing result; the
authenticated caller receives HTTP 422 with the failed checks. Non-critical
findings remain visible as `check_recommended`.

Optional `reference_search.search_tags` from HausSpiegel are accepted only from
the versioned allow-list. They can refine kitchen openness, garden connection,
stair role, office need, zoning, compact service core, and flexible rooms.
Explicit area, storey, and room-program answers remain authoritative.

## Response

```json
{
  "schema": "dmh-floorplan-result-v1",
  "request_id": "ZF-20260727-ABCD1234",
  "mime_type": "image/svg+xml",
  "filename": "zuhausefinder-ZF-20260727-ABCD1234.svg",
  "file_base64": "PD94bWwgdmVyc2lvbj0iMS4wIi...",
  "generator": {
    "reference_layout_id": "twostorey_018",
    "score": 86,
    "floor_count": 2,
    "quality_status": "review_required",
    "failed_checks": []
  },
  "classification": {
    "schema": "dmh-floorplan-classification-v1",
    "house_type": "two_storeys",
    "storeys": 2,
    "living_area_m2": 145,
    "area_band": "family",
    "room_program_tags": ["office", "guest_wc", "utility_room"],
    "geometry_quality": "review_required",
    "data_origin": "structured_brief",
    "training_status": "reference_generated",
    "training_eligible": false
  }
}
```

WordPress validates the MIME signature and SVG safety a second time before
writing the file to its own media library.

## Structured data and later training

The API contract is independent of the questionnaire transport. The same
normalized brief can later come from a structured database without changing
the generator. Classification fields support indexing by house type, storeys,
area band, room program, reference, and geometry quality.

Generated customer files are never admitted to training automatically. New
examples remain `reference_generated` and `training_eligible: false` until a
separate human approval and privacy review promotes them to an approved
training dataset.

## Deployment

Set a long random value for `ZUHAUSEFINDER_WEBHOOK_TOKEN` in the Railway service
and use the same value as the WordPress **Grundriss-Token**. Configure the
WordPress **Grundriss-Webhook** as:

```text
https://<railway-domain>/api/zuhausefinder/floorplan
```
