# Haustyp: Treppe = kein Bungalow, unsichere Häuser grün auf /haus

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07:
- "Both are EFH" (bungalow_034, bungalow_generationat);
- "if there are stairs its not a bungalow you can also make everybody green where you are unsure and i will reclassify them".

## Approval record

Rainer's words above, in chat. data.json `house_type` is deliberately NOT changed by script, because it drives the build (roof, number of images) and the catalogue. Rainer changes it himself in the Annotator, Dach tab „Haustyp“.

## Implementation record

- **konfigurator-matrix.py** `haustyp()`: a stored "bungalow" with stairs, an upperfloor or an attic counts as efh. The old logic is now `haustyp_gespeichert()`. Backup `.before-haustyp`.
  - Matrix run: bungalow_034, bungalow_generationat and bungalow_007 (stairs) are now efh.
  - twostorey_057 appears for the first time.
  - CSV backup `konfigurator-matrix.csv.before-haustyp`.
- **hausdaten.mjs** `haustypPruefen()` gives a reason or "":
  - no house type set (also "other");
  - "Bungalow" with stairs or an upper/attic floor;
  - multi-storey with only one floor drawn.
  - There is no check against the file name: it often lies, and the house would stay green forever after Rainer confirms it.
- **state/route.ts:** `haustyp_pruefen` (reads data.json).
- **haus/page.tsx:** green row („Haustyp prüfen“) plus a green note at the top. Red (dimensions or outline missing) takes precedence.
- **Tests first, red before and green after:**
  - scripts/konfigurator_matrix_haustyp.test.py 5;
  - scripts/haustyp-pruefen.test.mjs 5.
  - The existing matrix tests stay green.
- **Live:** /haus shows 7 green houses:
  - bungalow_007 (stairs);
  - bungalow_034 and bungalow_generationat (upper floor / attic);
  - other_vito, other_xvitv1, cubicasa_review_high_quality_architectural_832, other_1_5_story_with_cellar (type "other").
  - The note on bungalow_034 checked.
- REGELN.md rule 15 extended.

## Seen in passing (not changed)

Since the morning run, many houses' room areas jumped up, e.g. bungalow_040_8 76→130 m², 040_15 87→152, 040_23 104→172. bungalow_040_17 has outline 0 m². Cause not checked: Rainer's new outlines or a scale/aspect change?
