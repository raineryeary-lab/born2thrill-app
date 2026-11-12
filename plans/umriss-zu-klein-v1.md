# Außenumriss zu klein = fehlt (rot)

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Area check 2026-11-07: bungalow_040_17 has an outline that is a 1 × 8 px rectangle (0 m²), drawn by accident. It counted as an outline, so the house size came out as 0 m². Rainer: "Yes, mark them".

## Finding (jumps in room area since the morning)

- **43 of 44 houses changed because Rainer typed the real building dimensions.** `annotation_space.source = stated_building_size`. The scale comes from those dimensions, no longer from the door-width estimate in gebaeudemass.json („GESCHÄTZT … Kein Maß“). For bungalows the new area ≈ width × depth (e.g. 040_15: 15.31 × 10.03 = 154 vs 152 m²). The old values were up to 45 % too small, so this is a correction, not a bug.
- **bungalow_040_7:** rooms edited on 2026-11-07 at 01:36, 84 → 92 m².

## Implementation

- **hausdaten.mjs `umrissFehlt()`:** an own outline smaller than half the rooms on its floor (normalised image) returns "Außenumriss zu klein: <floor>". /haus shows it red as before.
- **konfigurator-matrix.py `umriss_flaeche()`:** same rule. No size, `umriss_fehlt` = "Außenumriss zu klein: …".
- **Tests first, red before and green after:**
  - umriss-fehlt.test.mjs +1;
  - konfigurator_matrix_umriss.test.py +1.
- **Backups:** `.before-umriss-klein`.
- **Live:** in both the matrix and /haus, exactly one house: bungalow_040_17.
