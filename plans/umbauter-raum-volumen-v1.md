# Konfigurator-Matrix: umbauter Raum (Volumen) statt Umrissfläche, Klassen je Haustyp

Status: TEIL 1 DONE 2026-11-07 (Volumen je Haus + Regler); Klassen je Typ offen

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07:
- "und wenn du nach Volumen statt Fläche machst und rechnest?";
- "doch, die Dachschrägen werden somit berücksichtigt, und die Lufträume kann man ja grundsätzlich nicht als m² Wohnfläche angeben";
- earlier: split the classes by Bungalow / 1,5-Geschosser / 2-Geschosser, with limits from the market (günstig / normal / exklusiv).

## Current evidence

- `scripts/konfigurator-matrix.py` `umriss_flaeche()` 157: sum of the outlines per floor in m². There is no volume.
- Heights in the build:
  - storey 2.62 m (`build-simplifier-render-plan.py` 3180 `STOREY_HEIGHT_MM`; dollhouse wall 2.40 m + slab 0.22 m);
  - 1,5-Geschosser: Kniestock 1.0 m, 40° (`anderthalb.py` 17–18), the same for every house.
- Every house has 4 roof forms (rule 19), so a volume that includes the roof would depend on the roof form.
- Market (page "Hausgrößen nach Marktklassen"):
  - classes in m² Wohnfläche: Bungalow 100/130, 1,5: 125/155, 2-G: 140/175;
  - €/m³ only from forums (roughly 280–520 €/m³ for KG 300+400), not reliable.

## Exact scope

1. **New `volumen_m3` per house:**
   - every full storey: outline × 2.62 m. A Luftraum counts, because the outline includes it.
   - Top floor of a 1,5-Geschosser and every attic: outline × usable height under the roof: Kniestock 1.0 m, rising at 40°, capped at 2.62 m (the Spitzboden does not count). The span is the short side of the outline's bounding box. This gives about 2.2–2.3 m for spans of 8–10 m.
   - The roof above the last full storey does not count (4 roof forms).
   - A floor without its own outline uses the EG outline, as today. A Staffelgeschoss is never copied.
2. **Classes per type** (`groessenklasse` 1/2/3 = günstig/normal/exklusiv):
   - Bungalow, 1,5-Geschosser and 2-Geschosser separately (DHH as 2-Geschosser, ZFH by storeys).
   - The limits in m³ come from the market m² limits: m³ = Wohnfläche / 0.8 × 2.62.
     - Bungalow 328 / 426 m³;
     - 1,5-Geschosser 409 / 508 m³;
     - 2-Geschosser 458 / 573 m³.
   - They are stored in konfigurator.json as `groessenklassen_m3` per type, editable.
   - The factor 0.8 stays marked as an estimate.
3. **CSV/report:** new columns `volumen_m3` and `groessenklasse_typ`; the old `umriss_m2` column stays.
4. **Page "Hausgrößen nach Marktklassen":** recomputed from the matrix, in m³ with the m² equivalent. Two open questions for the boss go at the top: size class instead of room count? 3,000 €/m² or the market price?

## Out of scope

- Prices, rule 37 and the price windows stay unchanged (the boss decides).
- No upload to the website.

## Tests (first)

`scripts/konfigurator_matrix_volumen.test.py`:
- a bungalow 10 × 10 m gives 262 m³;
- a 2-Geschosser 10 × 10 m on each floor gives 524 m³;
- the 1,5 upper floor 10 × 8 m: usable height checked by hand (2.23 m);
- a Luftraum does not reduce the volume;
- class limits per type.
- Existing matrix tests stay green.

Real: matrix run. Report the counts per type and class, plus 3 houses with numbers checked by hand.

## Rollback

`konfigurator-matrix.py.before-volumen`; remove the test.

## Done 2026-11-07 (Rainer: "make a second slider with the volume please")

- konfigurator-matrix.py:
  - `nutzhoehe_dach()`, `umbauter_raum()`;
  - CSV column `volumen_m3`, placed before kleine_zimmer;
  - backup .before-volumen.
- konfigurator_matrix_volumen.test.py, 6 tests: red before, green after. All 6 matrix test files OK.
- Matrix run: 270/270 houses have a volume. Median m³ per m²: Bungalow 2.62, EFH 2.55, DHH 2.48.
- Checked by hand:
  - bungalow_013: 105 m² × 2.62 = 275 m³;
  - twostorey_059: 523 m³ (≈ 200 × 2.62);
  - onehalfstorey_046: 400 m³ (2.40 m³/m², upper floor under the slope).
- Price table (Snippet 12, d5b3aa855e96): second slider „€ je m³ umbauter Raum“ (600–1400 €, default 1.080 ≈ factor 1,30, where 830 ≈ market). The table follows the slider moved last. Live check OK.
- Open: size classes per type in m³ (point 2) and the market-classes page in m³ (point 4); the boss page has no m³ slider yet.
- Boss page (preislogik-konfigurator, artifact v4): €/m³ slider added, same logic as Snippet 12. The counts at 1.080 €/m³ match the catalogue exactly.
