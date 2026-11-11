# Grundriss-Katalog: Filter oben nur Fragebogen + Name

Status: DONE, LIVE 2026-11-07 (Rainer: "Yes, replace it")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "can you redo the grundriss catalog so that the filters on the top just have me filter according to the questionaire + the name?"

## Implementation

- **scripts/katalog-fragebogen-snippet.py v2** (generator of Snippet 10):
  - Snippet 9's filter row and tags are hidden with CSS. Snippet 9 itself is untouched.
  - The new row at the very top: Name (ID or display name), Budget (bis 450.000 / 450–600.000 / mehr als 600.000), Hausart, Zimmer (EFH/DHH only 4/5), Gäste-WC mit Dusche, Zurücksetzen, count.
  - No checkbox; the filters always apply.
  - The card info line shows display name · rooms · price · Gäste-WC.
  - Data per house: [house type, rooms, price, shower WC, display name] from konfigurator-matrix.csv plus projects/<id>/anzeigename.json.
- **Budget** uses the current matrix price (3,000 €/m²). Once the boss decides on the price logic, regenerate the snippet.
- **Output:** wordpress/katalog-fragebogen-filter.php and .js (264 houses).
- **Test first:** scripts/katalog_fragebogen_snippet.test.py 3, red before, green after.
- **Backup:** the old generator was not in git and the shell had not made the copy. It was restored from this chat as `katalog-fragebogen-snippet.py.before-v2`; the old outputs were regenerated as `*.before-v2` (with today's data).
- **Try-out on the live page, in Claude's own Chrome tab only (nothing published):**
  - old row hidden;
  - "BAH" → bungalow_007 + twostorey_xvbah;
  - Bungalow + 450–600k → 5 houses;
  - reset → 346.

## Open

- Replace Snippet 10 in Code Snippets with wordpress/katalog-fragebogen-filter.php (Rainer's OK).
- Snippet 9's card badges come from the WordPress database and still say e.g. "Bungalow · 2 Geschosse" for bungalow_003. Not part of this change.

## Live (2026-11-07)

- Snippet 10 replaced in Code Snippets (code without the `<?php` line, as before) and saved („Snippet updated“). The stored code has the same length (18,112) and SHA-1 (a8b2cf7ef53f) as the local file.
- The previous live version had old data (166 houses, an older matrix run) and could only be read back truncated, so no exact backup of its data exists. Its code is identical to `katalog-fragebogen-filter.php.before-v2`: rollback = paste that file.
- **Live check:**
  - one filter row (Name, Budget, Hausart, Zimmer, Gäste-WC);
  - Snippet 9's row hidden;
  - "villa" → bungalow_034;
  - Doppelhaus → 4;
  - EFH + 4 rooms + up to 450k → 5;
  - reset → 346.

## Nachtrag 2026-11-07: "5 und mehr Zimmer"

- Rainer: "können wir 5 und mehr Zimmer nehmen anstatt nur 5 im Filter?"
- The data were already capped at 5 (`werte()`: `min(..., 5)`), so only the label changed: „5 und mehr Zimmer“.
- Test extended (red before, green after); backups `.before-5plus`.
- Live: the label was replaced in the Snippet 10 editor. Before: SHA a8b2cf7ef53f (= the previous version); after: 9b96fc9ed779 (= the local file). „Snippet updated“.
- Live check: options „egal / 3 / 4 / 5 und mehr Zimmer“; „5 und mehr“ gives 78 houses.
