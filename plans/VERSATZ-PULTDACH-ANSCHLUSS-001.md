# VERSATZ-PULTDACH-ANSCHLUSS-001: step connection on the versetzte Pultdach

Status: DONE (2026-10-24): rectangles zinc + 056 built. L-houses stay plaster (Rainer: "no they are ok").
Request: Rainer via Codex, 2026-10-24.

## Where the generator does it

- **Rectangular houses (30 houses):** `scripts/roof_profile.py` → `profile_mesh()` builds the roof sheet from the cross-section of the Dach tab. The vertical step face is part of that sheet and gets the plaster material, called from `scripts/render-exterior.py` (`elif is_rectangle:`, call to `roof_profile.profile_mesh`).
  - **Error:** the step face ran from `a0` to `a1`, the roof outline including overhang, so out to the overhang edge. That made a vertical panel between the two roof edges in the overhang zone.
  - The upper roof had no overhang over the step.
- **L-shaped houses (33 houses):** a separate path, `VERSATZ-WHOLE-HOUSE-001` in `render-exterior.py`. The log already reports "step wall on the outer wall edge, upper roof with overhang above, walls flush with the outer edge". To be checked on one example before the closing report.

## Already changed today (on Rainer's direct instruction)

- `profile_mesh(..., step_wall_a_inset, step_overhang, step_wall_top_inset)`. All three default to 0, which gives identical output for every other form and caller (test `test_without_overhang_nothing_changes`).
- **Ends at the outer wall plane:** the step face ends at both gable ends at the wall's outer face. Inset = overhang − half the wall thickness; 0.38 m on 053.
- **Overhang over the step:** the upper roof runs past the step by the normal overhang, in its own pitch. The step face ends under the roof slab (0.22 m slab, measured vertically).
- Only passed for `roof_type == "doppelpultdach"`. Other roof types are unchanged.
- Tests: `roof_profile.test.py` (126 OK, 8 new), `roof_wings*.test.py` OK. Test render of 053 in the scratchpad.

## New from this request: zinc standing-seam cladding

- **New material `ZINK_MAT`:** titanium zinc, pre-weathered, a subtle blue-grey, metallic about 0.6, roughness about 0.45. Used only for the step face of the versetzte Pultdach (rectangle path, and the step wall in the L path if it exists there).
- **Standing seams as geometry:** one seam every 0.5 m (vertical, 20 mm wide, 25 mm proud), from the lower roof up to the underside of the upper roof, only within the step face (between the outer walls).
- **Unchanged:**
  - roof pitches, roof heights
  - the other overhangs
  - house geometry, openings, cameras
  - the other roof types

**Tests:**
- the step face carries `ZINK_MAT`
- seams only inside the step face, none in the overhang zone
- other roof forms: mesh and materials identical with and without the change

## Proof after approval

- **Build only `twostorey_056`:** its EG furniture has to be saved again first, otherwise the build stops at the furniture check.
- **Pictures:** a detail view of the roof step (extra camera, render only, not saved into the delivery) plus the normal exterior view.
- **No mass rebuild, no upload, no image replacement.**

## Uploaded projects with an affected Doppelpultdach view (26, 28 pictures)

Correction 2026-10-24: german_catalog_review_bungalow_3_3_3_b_100_2 only has a normal Pultdach picture online (`02-exterior-pultdach`), so it is not affected. Current list: `CODEX-RUECKMELDUNG-VERSATZ-PULTDACH-2026-10-24/betroffene-projekte.csv`.

All rectangular houses, built with the old step face, with a Pultdach picture in the catalogue:

| | |
|---|---|
| bungalow_007 | twostorey_046 |
| bungalow_039 | twostorey_048 |
| bungalow_040_185 | twostorey_049 |
| bungalow_040_200 | twostorey_051 |
| bungalow_040_24 | twostorey_052 |
| bungalow_m | twostorey_053 |
| german_catalog_review_bungalow_3_1_2_b_85 | twostorey_054 |
| german_catalog_review_bungalow_3_2_1_b_100_1 (2 pictures) | twostorey_055 (2 pictures) |
| german_catalog_review_bungalow_3_2_2_b_100_1 | twostorey_056 |
| german_catalog_review_bungalow_3_2_4_b_100_1 | twostorey_059 |
| german_catalog_review_bungalow_3_3_1_b_100_2 | twostorey_060 |
| german_catalog_review_bungalow_3_3_2_b_100_2 | |
| german_catalog_review_bungalow_3_3_3_b_100_2 | |
| german_catalog_review_bungalow_3_4_2_b_120 | |
| german_catalog_review_bungalow_3_4_6_b_120 | |
| german_catalog_review_bungalow_3_4_7_b_120 | |

Not affected (no Pultdach picture online):
- german_catalog_review_bungalow_3_2_5_b_100_1
- german_catalog_review_bungalow_3_3_4_b_100_2
- twostorey_030

**Note:** the following 8 were already rebuilt today (new step geometry, no zinc yet), before the "no mass rebuild" instruction:
- bungalow_007, bungalow_039, bungalow_040_185, bungalow_040_200, bungalow_040_24, bungalow_m
- german_catalog_review_bungalow_3_1_2_b_85, german_catalog_review_bungalow_3_2_1_b_100_1

Their pictures online are unchanged.

**Partial job:** `make-codex-job.py <plan> --nur doppelpult --grund "..."` orders only the Pultdach exterior; the other pictures count as done. Tested in `make-codex-job.test.py`.

## Rollback

`roof_profile.py.before-versatz-ueberstand`, `render-exterior.py.before-versatz-ueberstand`, `make-codex-job.py.before-nur`
