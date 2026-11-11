# Grundriss-Katalog: Grundriss statt Haus-Symbol auf Karten ohne Render

Status: DONE, LIVE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07:
- "how about the icons swapping for the floorplans in the grundriss katalog?";
- after the example: "Yes, use it" → "Yes, draw them" → "Yes, do all";
- for the database step: "Yes, go ahead" (upload, and set `bilder` per house; `approved` stays with Rainer).

## Implementation

- **scripts/katalog-grundriss-bilder.py** draws each house itself from annotations.json, using matrix helpers for scale, aspect ratio and labels:
  - rooms coloured by type;
  - outer outline, windows (blue), doors (red), stairs;
  - room name with umlauts plus m²;
  - all floors side by side at the same scale (70 px/m, at most 2,400 px wide).
  - The Simplifier PNGs were not used: broken umlauts, tiny names.
- **Output:** E:\born2thrill-local-workbench-data\katalog-grundrisse\<plan>-grundriss.png. 145 houses, i.e. every catalogue card without a picture that has an annotation. 70 queue entries without an annotation got nothing.
- **Upload:** wp-admin/media-new.php in 4 steps (1 + 48 + 48 + 48), no errors. The catalogue links them by the prefix "<plan>-".
- **`bilder`:** set per house through the plugin's own route POST b2t/v1/katalog to the number of images per `b2t/v1/bilder`. `approved` was never sent; checked to stay „offen“.
- The first try at the database step was blocked by the safety check; Rainer then explicitly approved it.

## Open

- 70 catalogue entries without an annotation (queue) still show the symbol.
- If renders arrive later, the exterior picture becomes the cover automatically; the floor plan stays in the lightbox.

## Live result (2026-11-07)

- `bilder` set for 145 of 145 houses. `approved` stays „offen“ for all of them (checked against the public list).
- Catalogue: 346 cards, 264 with a picture, 82 with the symbol (queue entries without an annotation).
- **Side effect:** Snippet 9 now shows the badge „GERENDERT“ on these cards (shown whenever images exist but the house is not approved), although only the floor plan is there. The label is misleading. Fix possible in Snippet 10 (Rainer's decision).

## Badge fix (2026-11-07, Rainer: "Yes, fix it")

- **Snippet 10** (generator `katalog-fragebogen-snippet.py`, backup `.before-badge`): if a card's only image is its floor plan (cover `/<id>-grundriss`, pill „1 Bilder“), the badge „gerendert“ becomes „offen“ (data-done=offen). Snippet 9 is untouched.
- Test +1 (red before, green after). SHA before f6516b40f0da, after 62a08ba71309 = local file.
- **Live:** fertig 120, offen 216, gerendert 10.
- **The 10 „gerendert“ cards have real exterior renders (4–5 images each)** that were already in the media library but had `bilder` = 0. Setting the count made those renders visible as covers. Approval status unknown; Rainer decides whether they stay visible. The houses:
  - german_catalog_review_bungalow_3_1_1_b85;
  - onehalfstorey 1_1_1, 1_2_1, 1_5_16, 1_6_2;
  - twostorey 5_1_1, 5_1_2, 5_3_1, 5_4_1, 5_6_3.
- Rainer, 2026-11-07: "Yes, keep them". The 10 renders stay visible.
