# Kleine Zimmer zählen voll, grün zur Prüfung

Status: DONE, LIVE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07, on "count rooms under 10 m² as full rooms?": "yes but mark them as green and let me review them". 6 houses with 2.5 rooms appeared under no filter (finding by Codex).

## Implementation

- **konfigurator-matrix.py:**
  - `halbes_zimmer_unter_m2` = 0 (no half rooms) and the new `kleines_zimmer_pruefen_unter_m2` = 10, in STANDARD and in E:\…\konfigurator.json (backup `.before-kleine-zimmer`).
  - Zimmer from 6 to under 10 m² count fully and appear in the new last CSV column `kleine_zimmer`, e.g. "Büro 8,5 m² · Gast 7,0 m²". The separator is " · ", because ";" is the CSV separator.
- **hausdaten.mjs:**
  - `kleineZimmerAusCsv()` reads the column and handles quoted fields;
  - `zimmerPruefen()` stays green until exactly this list has been checked.
- **API** POST /api/floorplan-workbench/zimmer-geprueft (local only) writes only projects/<plan>/zimmer-geprueft.json. The drawing and data.json stay untouched. If the list changes later, the house turns green again.
- **/haus:**
  - green row „Zimmer prüfen“;
  - green note „Kleine Zimmer prüfen: …“ with the button „Zimmer geprüft“.
- **Tests first, red before and green after:**
  - konfigurator_matrix_kleine_zimmer.test.py 3;
  - zimmer-pruefen.test.mjs 3, including the quoted field.
  - The other matrix, snippet and /haus tests stay green.
- **Matrix:** 18 houses changed, e.g. bungalow_032 2.5→3, twostorey_012 4→5. No half rooms left. The same 18 are green.
- **Live /haus:**
  - 18 green;
  - the note on bungalow_040_36 checked;
  - the button tested: the mark disappears and stays gone after a reload;
  - Claude's test click then undone (zimmer-geprueft.json deleted).
- **Snippet 10:** room number for 17 entries. SHA before ed23ce319a3f, after f6516b40f0da = local file. Live: Bungalow + 3 Zimmer = 61, including bungalow_032 and bungalow_037.

## Nachtrag: Grenze wie angezeigt

- Rainer: "bungalow_037 fixed". His Büro now measures 9.99 m², shown as „10,0 m²“, but it was still listed as small.
- Now compared like the display: `round(m2, 1) < 10`. Test +1, red before and green after.
- Matrix: bungalow_037 clear. Also cleared: onehalfstorey_002, onehalfstorey_020, bungalow_032, and the Büro of bungalow_040_36 (all at „10,0 m²“).
- 14 houses left to check.
- The website filter is unaffected (room counts and prices unchanged).
- Rainer, 2026-11-07, reviewed:
  - bungalow_037, bungalow_040_26 and bungalow_040_3 fixed in the drawing;
  - onehalfstorey_018 "Büro only 9 but it's ok, count as a room";
  - "All but cubicasa" → 9 houses confirmed through the API (zimmer-geprueft.json).
  - Still green: only cubicasa_review_high_quality_architectural_832 (Essen 7,0 m²).
