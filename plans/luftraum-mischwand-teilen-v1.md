# Luftraum: eine durchgehende Wand nur am offenen Stueck aufschneiden

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22, onehalfstorey_vv1: "the Luftraum has no railing even though it is in the editor".

## Current evidence

- vv1 annotation: Luftraum (upper floor) with `gelaender_kanten: [3]` = its west edge, x 4.47 m, y 5.30-7.77 m, towards the Flur.
- Last upper-floor build log: "luftraum Luftraum: kein Boden, 0 Gelaenderstueck(e) (Kanten 4)".
- plan-modern.json: interior `wall-2` runs x 4.50, y 5.29 -> 11.05 m with rooms {Bad, Luftraum, Flur} -- the wall builder merged the Luftraum|Flur stretch and the Bad|Flur stretch into ONE wall.
- `build-simplifier-render-plan.py offene_deckenloch_waende()` (line 258) removes a wall only if ALL its rooms are hole/circulation; {Bad, Luftraum, Flur} is not, so the whole wall stays -- including the stretch along the Luftraum.
- `render-furnished-dollhouse.py _lr_lauf()` leaves a gap wherever a wall runs ALONG the railing -> 0 pieces.

## Exact scope (build-simplifier-render-plan.py)

1. New pure `offene_wandstuecke(rooms, walls)`: for an interior wall that touches a hole (luftraum/treppenoeffnung) but is not removed whole, find the stretch that lies along a hole edge AND has an open room (Flur/Galerie/other hole) on the other side (point test half a wall thickness beside the wall). Return `{wall_id: [(t0, t1), ...]}`.
2. Those walls are split: the open stretch is removed, the rest stays as `wall-2a`/`wall-2b` (same type, thickness, rooms). Openings on the wall: remapped onto the remaining piece they sit on; on the removed stretch -> listed as excluded "Luftraum/Treppenloch" like today.
3. Log line names the cut: "Luftraum: wall-2 an 2.47 m zum Luftraum geoeffnet (dort Gelaender)".

## Out of scope

- The railing builder itself; walls to bedrooms/baths stay (rule from 2026-10-16).

## Tests (first)

- `offene_wandstuecke` on a synthetic plan like vv1: wall x=4.5, y 5.3-11.0 with Luftraum east of 5.3-7.8, Bad east of 7.8-11.0, Flur west of all -> one stretch (5.3, 7.8); Bad stretch kept.
- A wall Luftraum|Bad only -> nothing cut (stays a real wall).
- Opening remapping: an opening at y 9.0 stays on the remaining piece with the right position.
- Real: vv1 rebuild -> log "1 Gelaenderstueck" (or more) on edge 4; render shows the railing. Existing houses with a Luftraum (twostorey_059) keep their wall counts.

## Note (not code)

vv1 build is also blocked right now by stale furniture on the upper floor (rooms redrawn after placing) -- Rainer saves the Möbel step once. And the upper floor is registered with x scale 0.82 (y 0.98): the alignment marks are probably not on the same two corners on both floors.

## Safety gate

Can any changed path publish geometry without an approved reference? No. Local plan building only.

## Rollback

`build-simplifier-render-plan.py.before-mischwand`, delete the new test.

## Approval record

Rainer in chat, 2026-10-22: "Approved: implement luftraum-mischwand-teilen-v1, tests first, then rebuild onehalfstorey_vv1 once I saved the furniture."

## Implementation record (2026-10-22)

- `build-simplifier-render-plan.py`: `offene_wandstuecke(rooms, walls)` + `waende_teilen(walls, openings, stuecke)`, called right after the whole-wall removal; log line per opened wall.
- Tests first: `scripts/luftraum_mischwand.test.py` (4, red before, green after); build-simplifier-render-plan.test.py unchanged (only the known door-hinge failure).
- Regression: plans of every house that builds today (~110 incl. twostorey_059, onehalfstorey_044/045/vm2) built with old and new builder -> identical wall ids on every floor.
- vv1 (last plan, 15:46): wall-2 opened 0.002-0.432 (y 5.30-7.77 m along the Luftraum); rest wall-2a (y 7.77-11.05, Bad) keeps the Bad door; the drawn 2.56 m Durchgang lay in the opened stretch -> excluded.
- vv1 rebuilt after the upper-floor furniture was saved (Speichern now enabled by moebel-speichern-bei-neuen-raeumen-v1; saved from the editor at Rainer's request, 11 pieces unchanged, stamp 5c295aa91b8a): "[plan] Luftraum: wall-2 an 0.00-0.43 zum Luftraum geoeffnet", "[dollhouse] luftraum Luftraum: kein Boden, 1 Gelaenderstueck(e) (Kanten 4)"; verifier all PASS incl. R2_gelaender, 4 artifacts certified; render shows the railing between Flur and Luftraum.
