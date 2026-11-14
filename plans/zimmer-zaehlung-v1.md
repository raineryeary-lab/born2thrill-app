# Zimmer zählen: Kinderbad, kaputtes Umlaut-Label (Codex + Claude)

Status: DONE, LIVE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "recheck this shit have codex recheck it bungalow_035 says it has 10 rooms and is under filter 4 Zimmer"; after the findings: "Yes, fix them".

## Findings (Codex read-only, independently checked by Claude)

- bungalow_035 = 4 Zimmer is correct. „10 Räumen“ on the card is Snippet 9's count of ALL rooms (bath, hallway, WC, HWR, pantry included).
- **Fixed:**
  1. „Kinderbad“ counted as a Zimmer: 8 houses.
  2. „BÃƒÂ¼ro“ (doubly mis-encoded) was not counted: 1 house.
- **Not a bug:** cubicasa_…_832 and other_1_5_story_with_cellar were missing because Rainer set their Haustyp at 11:55/11:56, after the matrix run.
- **Open, Rainer's decision:**
  - Hobbyraum (other_vito);
  - rooms under 10 m² count as half; 2.5 → no filter, 6 houses invisible;
  - Wohnen + Essen drawn separately = 2 (6 houses);
  - „Küche / Essen“ and „Essen / Kochen“ count as a Zimmer (4 houses);
  - Fitness and Sauna do not count.
- **Seen by Claude:**
  - twostorey_040 has no Wohnen label at all;
  - other_1_5_story_with_cellar has 626 m² / 1,878,000 €. Implausible, probably cellar or scale.

## Implementation

- **konfigurator-matrix.py:**
  - `label_reparieren()` (cp1252→utf-8, up to 3 times);
  - `ist_zimmer()`: wet rooms (bad, wc, dusch) never count, before the wohnen/schlafen/kind exception.
  - Backup `.before-zimmer`.
- **Test first:** konfigurator_matrix_zimmer.test.py 3, 2 red before, all green after. The other matrix and snippet tests stay green.
- **Matrix run:** exactly Codex's prediction:
  - Kinderbad houses: 5_6_3 5.5→5, xvitv1 7→6, tw040 4.5→4, xvv1 6→5, tw039 6.5→6, tw022 4.5→4, tw056 4.5→4, tw042 5.5→5;
  - 5_6_1 5→6;
  - 2 houses added.
  - CSV backup `.before-zimmer`.
- **Snippet 10:**
  - The filter groups of the Kinderbad houses do not change (rounded down / capped at 5).
  - New: 2 houses, bungalow_040_17's price.
  - Patched in the editor: SHA before 9b96fc9ed779, after ed23ce319a3f = local file; „Snippet updated“.
- **Live:** bungalow_035 under 4 Zimmer; other_1_5_story_with_cellar shows „5 Zimmer · ca. 1878 Tsd. €“.
