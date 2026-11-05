# 1,5-Geschosser mit Erker: der Erker wird die Front des Quergiebels

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22: "something is wrong with onehalfstorey_vm2 it is set as a 1,5 story but the generated roof is totally off".

## Current evidence

- vm2 plan: house_type 1.5-storey, Satteldach. Upper floor has 8 exterior walls: main body x 1.78-10.92, y 1.03-11.83 (centre lines) plus an EAST bay (Erker) x 10.92-11.74 (0.82 m deep), y 4.52-8.24 (3.71 m wide). Ground floor has the same bay.
- `render-exterior.py` ~1262: the 1,5-Geschosser roof (Kniestock, 40 deg, Zwerch) only runs when the top floor has exactly 4 walls and one massing rectangle. vm2 logged "Obergeschoss ist kein Rechteck (8 Aussenwaende) -- Kniestock/Zwerchgiebel noch nicht, Dach wie bisher": full-height walls, low two-storey roof plus a separate small roof on the bay (render 2026-10-22 10:06).
- Rainer drew a Quergiebel on the bay front: plan `quergiebel` x=11.62, y 4.39-8.49 -- the bay is meant to be the Zwerch front.
- Main body 9.14 x 10.80 m -> ridge along y (north-south), eaves east/west -> the bay is on an eave side.

## Exact scope

1. `anderthalb.py`: new pure `rechteck_mit_erkern(walls_m)` -> `(bbox, erker)` for a top floor = one rectangle plus bays up to 1.5 m deep on its sides; `erker = [{seite, lo, hi, tiefe}]`. Anything else -> None (today's WARNUNG stays).
2. `anderthalb.giebel()`: takes `erker`. A drawn Quergiebel lying on a bay front belongs to that side. Without drawn ones, openings in a bay front count for that side, and every bay on an eave side gets a Zwerch at least as wide as the bay. Each Zwerch carries `vor` = the bay depth (0 without a bay).
3. `render-exterior.py`:
   - accept rectangle + bays: AH_BBOX = main body; the roof is built over the main body only (no separate bay roof);
   - Zwerch with `vor > 0`: front wall at the bay front (s = -vor), from the upper-floor floor up (classic) or from the ground (Kubus, grey, +0.10 m); side walls from the bay front back into the roof; roof slabs/flat roof and the eave opening start in front of the bay.
4. Bay on a GABLE side: built as today's bay walls, no Zwerch (out of scope to style).

## Out of scope

- L-shaped 1,5-Geschosser (two wings) -- roadmap.
- Bays deeper than 1.5 m (treated as a wing, not a bay).

## Tests (first)

- anderthalb.test.py: `rechteck_mit_erkern` on vm2's 8 walls -> bbox (1.777, 10.917, 1.025, 11.825), one east bay 4.52-8.24, depth 0.82; a plain rectangle -> no bays; an L -> None. `giebel()` with the bay: drawn bar on the bay front -> east, vor 0.82; no drawn bar -> east Zwerch covering 4.52-8.24.
- Seam: render-exterior uses `rechteck_mit_erkern(` and passes `erker=`.
- Real: rebuild vm2 (no upload): log shows Kniestock 1.00 on east/west, 1 Zwerch east; probe 0 wall points above the roof; look at both exteriors. onehalfstorey_044/045 scratch renders unchanged (same Zwerch extents, 0 points above the roof).

## Safety gate

Can any changed path publish geometry without an approved reference? No. Local builds only, nothing uploaded.

## Rollback

`.before-erker` backups of anderthalb.py, anderthalb.test.py, render-exterior.py.

## Approval record

Rainer in chat, 2026-10-22: "Approved: implement anderthalb-erker-zwerch-v1, tests first, then rebuild onehalfstorey_vm2 (no upload)."

## Implementation record (2026-10-22)

- `anderthalb.py`: `rechteck_mit_erkern`, `seite_mit_erker`, `_auf_erker`, `zwerch_seitenprofil`; `giebel(..., erker=)` and `gezogene_giebel(..., erker=)`; every giebel carries `vor`. A Zwerch over a bay takes the bay's exact width (a drawn bar wider than the bay is clipped to it -- vm2: drawn 4.39-8.49, built 4.52-8.24).
- `render-exterior.py`: rectangle OR rectangle with bays; with bays the roof footprint/massing is the main body only; openings on a bay front count for that side; Zwerch front at the bay front (classic from the upper-floor floor, Kubus from the ground), side walls on the bay edges from the bay front back into the roof, roof slabs/flat roof/eave opening start in front of the bay; Kubus flat roof widened by half a wall over a bay (first probe: 9 points uncovered at the bay corners -> 0).
- Tests first: anderthalb.test.py +9 (Erker 7, Seitenprofil 2), red before, green after; all script suites green except the known door-hinge failure.
- Scratch: 044 and 045 unchanged (same Zwerch extents, 0 points above the roof, both variants).
- vm2 rebuilt (no upload): Erker east 4.52-8.24, 0.82 m; Kniestock 1.00 m; 4/4 .blend, verifier R0-R6 PASS, 4 artifacts certified; probe 0 points above the roof in both exteriors; renders looked at (bay rises into Zwerchgiebel / grey Kubus).
