# 1,5-Geschosser: moderne Variante mit Zwerchkubus

Status: DONE 2026-10-21

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-21, with a reference picture (Satteldach house, the cross gable is a grey flat-roofed box): "this would actually be a kind of a modern form for our 1,5 story houses". Answer to "how many exteriors": **2: classic + modern**.

- **Classic** = today: Satteldach, Kniestock 1.0 m, Zwerchgiebel with a pointed roof (anderthalbgeschosser-dach-v1).
- **Modern** = same Satteldach and Kniestock, but each Zwerchgiebel becomes a **Zwerchkubus**: a box with a flat roof that rises from the facade through the eave, in a different render colour (grey).

Delivery for a two-floor 1,5-Geschosser: 2 exteriors + 4 styles x 2 floors = **10 pictures** (anderthalb-eine-dachform-v1 said 9).

## Current evidence

- `run_project.py roof_types_for_plan()` returns `("satteldach",)` for a 1,5-Geschosser; each entry becomes one exterior via `EXT_ROOF_TYPE` (line 534-537) and one `exterior-<roof>-baseline.blend`.
- `render-exterior.py` builds the Zwerchgiebel at lines ~3366-3457: pentagon front wall with its openings (`extwall-zwerch-*`), two roof slabs (`roof-zwerch-*`), triangular cheeks, main eave opened by a boolean. Position and width come from `anderthalb.giebel()`, unchanged.
- The Codex job takes its exterior list from the .blend files (make-codex-job.py `outputs_for`), so a second exterior .blend appears in the Auftrag by itself; `anzahl_satz` will say "2 Aussenansichten".

## Exact scope

1. `run_project.py`: a 1,5-Geschosser gets `("satteldach", "satteldach-kubus")`. `satteldach-kubus` renders the same Satteldach with env `AH_ZWERCH_FORM=kubus`; file `exterior-satteldach-kubus-baseline.blend`. Delivery count follows (2 + floors).
2. `anderthalb.py`: new pure `kubus_masse(lo, hi, traufe_z, wand_oben_z)` -> front wall rectangle up to the flat roof, roof top z = front wall top + 0.30 m Attika, depth = where that height meets the main roof slope (40 deg).
3. `render-exterior.py`, Zwerch block: when `AH_ZWERCH_FORM=kubus` build instead of the pentagon + roof slabs:
   - front wall as a rectangle with its openings (same opening cut as today);
   - two side walls (rectangles, trimmed to the main roof plane);
   - flat roof slab with a 0.30 m Attika edge, slight overhang 0.05 m;
   - the box walls get their own material `zwerchkubus-putz` (grey), so Codex can colour it like the reference;
   - main eave opened by the same boolean as today.
4. `make-codex-job.py`: the exterior line for `satteldach-kubus` says "moderne Variante: Zwerchkubus mit Flachdach, Putz grau abgesetzt"; the plain `satteldach` says "klassisch: Zwerchgiebel mit Satteldach".
5. Memory/roadmap: 1,5-Geschosser = 2 exteriors (10 pictures).

## Out of scope

- Roof covering material (Tegalit reference + roof rule = separate plan, still open).
- L-shaped 1,5-Geschosser (still no Kniestock, roadmap).
- Bungalows, Zweigeschosser.

## Tests (first)

- `anderthalb.test.py`: `kubus_masse` for onehalfstorey_044's north Zwerch (4.64-7.88): flat roof z, depth into the roof, Attika height.
- `eine_dachform.test.py`: 1,5-Geschosser -> `("satteldach", "satteldach-kubus")` (the existing case changes from 1 to 2 -- this is a plan revision of anderthalb-eine-dachform-v1, recorded here; the 2-storey and doppelpult cases stay unchanged).
- Blender probe on onehalfstorey_044: kubus .blend has `extwall-zwerch*` with 4 vertical faces, a flat roof at the computed z, no wall point above the roofs (dach_probe.py), Kniestock still 1.00 m.
- `go.py onehalfstorey_044` (no upload): 4 blends (2 exterior + 2 interior), verifier green; look at both exteriors.

## Safety gate

Can any changed path publish geometry without an approved reference? No. Local build only; upload stays Rainer's / Codex's step as today.

## Rollback

Restore `.before-zwerchkubus` backups of the four scripts; revert the test case.

## Approval record

Rainer in chat, 2026-10-21: "Approved: implement anderthalb-zwerchkubus-modern-v1, tests first, then go.py onehalfstorey_044 (no upload)."

## Implementation record (2026-10-21)

- `anderthalb.py`: `ATTIKA_M=0.30`, `KUBUS_SUFFIX`, `KUBUS_VOR_M=0.10`, `kubus_masse()`, `dachform_und_zwerch()`.
- `run_project.py`: 1,5-Geschosser -> `("satteldach", "satteldach-kubus")`.
- `render-exterior.py`: EXT_ROOF_TYPE read via `dachform_und_zwerch`; material `zwerchkubus-putz` (grey); Kubus = front wall from the ground to the flat roof, 0.10 m proud of the facade (after a first test render only grey above the eave -- changed to match Rainer's reference, where the grey body runs over both storeys), openings of ALL storeys cut into it, side walls above the main roof, flat roof slab with 0.30 m Attika reaching under the main roof, main roof removed below the slab top.
- `make-codex-job.py`: exterior entries carry `variante` (klassisch Zwerchgiebel / modern Zwerchkubus) when both exist; printed under "Rueckgabe".
- Tests first: anderthalb.test.py +3, eine_dachform 1,5 case now 2 roofs (plan revision), make-codex-job.test.py +3; red before, green after. All script suites green except the known door-hinge failure.
- Build onehalfstorey_044 (run_project directly -- go.py considered the old certificate current): 4/4 .blend (exterior-satteldach, exterior-satteldach-kubus, interior EG/OG), verifier R1-R6 PASS, 4 artifacts certified. Probe: 96 wall points above 3 m, 0 without roof above. Kniestock 1.00 m on both eaves in both exteriors.
- Not done here: the Codex job for 044 still describes the 9-image set; pressing "An Codex" rewrites it for 10.
