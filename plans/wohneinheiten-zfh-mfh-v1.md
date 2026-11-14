# Wohneinheiten: Zweifamilienhaus und Mehrfamilienhaus

Status: DONE, LIVE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "we need haustype mehrfamilienhaus" (after the room type Treppenhaus).

## Current evidence

- `data.json` `house_type` encodes the number of floors: bungalow / 1.5-storey / 2-storey / 2-storey with cellar / other. The build reads it (Kniestock, heights).
- Doppelhaus is a separate field in the drawing (`doppelhaus`, Annotator Dach tab, doppelhaus.js). The matrix, catalogue row and build read it.
- The matrix has `ZIMMERSTUFEN["zfh"]`, but `haustyp()` never returns "zfh", so there are 0 Zweifamilienhäuser. The catalogue filter offers „Zweifamilienhaus“ anyway.

## Proposal

1. A new field `wohneinheiten` (1 / 2 / 3+) in the Annotator, Dach tab, next to Doppelhaus. Saved like `doppelhaus`, in the drawing.
2. Matrix `haustyp()`: wohneinheiten 2 → "zfh", ≥ 3 → "mfh" (takes precedence over efh/bungalow; Doppelhaus stays "dhh").
3. Catalogue filter (Snippet 10): Hausart += „Mehrfamilienhaus“. ZFH gets its data.
4. MFH room filter: open (by number of flats, or skip the room filter).
5. Questionnaire / configurator: MFH is not in the questionnaire. That stays the boss's decision (rule 37/38); only the catalogue filter changes.
6. The build is unchanged: the floors stay in `house_type`.

## Tests (first)

- Matrix: wohneinheiten 2 → zfh, 3 → mfh, 1 / missing → as before.
- Annotator: the field exists and survives Save (app.py normalisation).
- Snippet: the Hausart option Mehrfamilienhaus exists.

## Rollback

`.before-wohneinheiten` backups; remove the tests.

## Decisions and implementation (2026-11-07)

- Rainer: "doppelhaus hälfte is different from a mehr familienhaus"; MFH filter "By number of flats".
- **app.py:** `normalize_wohneinheiten()` (2..30, 1 = not stored); saved as `wohneinheiten` with the drawing.
- **annotate.html/js:** select „Wohneinheiten“ in the Dach tab (1, 2 = ZFH, 3–12 = MFH); load, save, notice. Versions v=20261107-4.
- **konfigurator-matrix.py:**
  - `wohneinheiten_von()`; `haustyp()` 2 → zfh, ≥3 → mfh (dhh stays dhh).
  - CSV column `wohneinheiten` before `kleine_zimmer` (the existing test wants kleine_zimmer last).
- **katalog-fragebogen-snippet.py:**
  - data field 6 = flats;
  - Hausart += Mehrfamilienhaus;
  - for MFH the Zimmer filter becomes „Wohnungen“ (3 / 4 / 5 und mehr);
  - info line shows the flats.
- **Tests first, red before and green after:**
  - tests/test_wohneinheiten.py 3;
  - matrix haustyp +1;
  - snippet +1 (data form extended).
  - tests/ OK, static 459/459, all matrix tests OK.
- **Backups:** `.before-wohneinheiten` (app.py, annotate.*, matrix, snippet generator, php, CSV).
- **Matrix run:** new house other_2_familienhaus (efh, 1 flat entered).

## Live (Rainer: "Yes, do both")

- Annotator restarted (Start-Alles.ps1); the „Wohneinheiten“ field is in the Dach tab (checked on other_2_familienhaus).
- **Snippet 10:** 7 code changes, data with flats plus other_2_familienhaus. SHA before 62a08ba71309, after ea090bf4d15a = local file; „Snippet updated“.
- **Live:**
  - Hausart offers Mehrfamilienhaus;
  - with MFH the filter reads „Wohnungen“ (3 / 4 / 5 und mehr) and finds 0 houses (none marked yet);
  - EFH reads „Zimmer“, 137;
  - all: 346.
- **Next:** Rainer marks houses in the Annotator (Dach tab → Wohneinheiten). After that, rerun the matrix and regenerate and replace Snippet 10.

## Katalog: die 2-Familienhäuser (Rainer: "Yes, add them", 2026-11-07)

- katalogzeile.py: wohneinheiten 2 → „Zweifamilienhaus“, ≥3 → „Mehrfamilienhaus“ (after the DHH check). Test `test_zwei_und_mehrfamilienhaus` was red before and is green after; all katalogzeile tests OK. Backup `.before-wohneinheiten`.
- Live rows 347–350 were created via grundriss-anlegen: bungalow_2_familienhaus, other_2_familienhaus, other_2_famlilienhaus, twostorey_2_familien.
  - All four went in as haustyp „Zweigeschosser“: the server plugin (b2t_haustypen) does not accept Zweifamilienhaus/Mehrfamilienhaus yet.
- Floor plans for bungalow_2_familienhaus and other_2_familienhaus: media 1727/1728, `bilder`=1, approved untouched.
  - other_2_famlilienhaus and twostorey_2_familien have no scale (gebaeudemass), so there is no drawing and no matrix row.
- Snippet 10: ea090bf4d15a → 0a547a3c2da4, 268 houses. Live: Hausart Zweifamilienhaus → 1 house (other_2_familienhaus, 2 Wohnungen).
- OPEN:
  - Plugin b2t_haustypen += Zweifamilienhaus, Mehrfamilienhaus. Until then, publish-renders.py `check_plan` gets HTTP 400 on a NEW ZFH/MFH house.
  - Wohneinheiten=2 for bungalow_2_familienhaus and twostorey_2_familien (Rainer, Annotator).
  - Scale for the two houses without one.
- 2026-11-07, Rainer "Yes, update plugin": plugin B2T Katalog-Freigabe 1.3.0 → 1.3.1 (b2t_haustypen += Zweifamilienhaus, Mehrfamilienhaus), uploaded via Plugins → Plugin hochladen → replace. „Erfolgreich aktualisiert“.
  - Test `test_plugin_kennt_zfh_und_mfh` was red before and is green after.
  - publish-renders.py `haustyp_nachziehen` now also switches rows to ZFH/MFH.
  - katalogzeile, doppelhaus and publish-renders tests OK.
  - Backups `.before-zfh`.
- Live: other_2_familienhaus and other_2_famlilienhaus set to haustyp „Zweifamilienhaus“ (200, `bilder` and approved unchanged).
- 2026-11-07, Rainer: "WHY ARE MY 2 FAMILIENHÄUSER NOT BEING SHOWN". The Hausart filter only knew other_2_familienhaus.
  - Snippet generator `ohne_matrix_nach_wohneinheiten()`: houses without a matrix row but with 2+ Wohneinheiten now come under ZFH/MFH. The info line reads „Maße folgen“.
  - Test was red before and is green after.
- twostorey_2_familien: wohneinheiten=2 set (two Wohnen/Essen/Kochen and a Treppenhaus on both floors). Backup annotations.json.before-wohneinheiten. Catalogue haustyp set to Zweifamilienhaus.
- Snippet 10: 0a547a3c2da4 → 63c0eab987fe, 270 houses. Live: Hausart Zweifamilienhaus → 3 houses (other_2_familienhaus, other_2_famlilienhaus, twostorey_2_familien).
- bungalow_2_familienhaus stays EFH: the drawing has one kitchen and one flat. Rainer decides.
- 2026-11-07, Rainer "Make it ZFH": bungalow_2_familienhaus wohneinheiten=2 (backup annotations.json.before-wohneinheiten); catalogue haustyp Zweifamilienhaus; Snippet 10 63c0eab987fe → 61baaa7aa338. Live: Hausart Zweifamilienhaus → 4 houses.
- 2026-11-07 Rainer: "if there are m² in the rooms there has to be a Maßstab" -- correct: other_2_famlilienhaus was saved with floor_scale at 15:42, after my read. Matrix rerun; floor plans for other_2_famlilienhaus and twostorey_2_familien uploaded (bilder=1); Snippet 10 61baaa7aa338 → 62d25709586e. Live: all 4 ZFH with floor plan, rooms and price.
- 2026-11-07 Rainer: "why doesn't your list reflect the 2 Familienhäuser". They were not in the mass build (the list predates them). bungalow_2_familienhaus is built; Codex job ready (27 files). First failure: STALE PLAN because I wrote wohneinheiten straight into annotations.json without source-state; fixed with app.write_source_state (backup source-state.json.before-wohneinheiten). other_2_familienhaus, other_2_famlilienhaus and twostorey_2_familien: floor alignment missing (Rainer, Annotator).
