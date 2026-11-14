# Möbel: ein Knopf richtet alle Räume nach ihrem Namen ein

Status: DONE 2026-10-23

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-23: "you know how we autointegrate the furniture with area selection? could we create a new button that does it completely automatically? the room names are there why not just populate automatically?"

## Current evidence

- `src/lib/generator/moebel-vorschlag.mjs`: `richteBereichEin(bereich, raumtyp)` furnishes ONE area with the rules for 12 room types (Wohnzimmer, Esszimmer, Küche, Diele, HWR, Kinderzimmer, Gast, Büro, Schlafzimmer, Du/Bad, WC, Bad), keeping clear of doors (900 mm) and windows (600 mm) and of furniture already there. `raumtypAusName(name)` already maps a room name to its type -- and returns null for combined rooms ("Wohnen / Essen / Kochen").
- `src/app/floorplan-workbench/page.tsx` ~1773 (`onEinrichten`): today Rainer draws an area, picks the type, and it runs once; it asks first if furniture already stands there.

## Exact scope

1. New button **"✦ Alle Räume einrichten"** in the Möbel step, for the floor shown.
2. For every room of that floor: type from `raumtypAusName(room.name)`; area = the room polygon; same openings and existing-furniture input as `onEinrichten`; all placed in one step (one Undo takes it all back).
3. Skipped, and listed in the status line afterwards:
   - rooms that already have furniture (nothing is added on top, nothing removed);
   - rooms without a clear type, above all combined "Wohnen / Essen / Kochen" -- those stay for "✦ Bereich einrichten" by hand, as today;
   - Luftraum / Treppenöffnung / Terrasse and other non-rooms.
4. Nothing is saved automatically: Rainer looks, adjusts, presses Speichern.

## Out of scope

- Splitting combined rooms automatically (possible v2: kitchen/dining/living zones by size and position -- needs its own rule).
- Changing the furniture rules themselves.

## Tests (first)

`scripts/moebel-vorschlag.test.mjs` (+ new): pure `richteAlleRaeumeEin(raeume, oeffnungen, vorhandene)` -> furniture for single-type rooms; combined room skipped with reason; a room with existing furniture skipped; Luftraum skipped; result reproducible (same input -> same output). Seam: page.tsx button calls it.
Real: one house in the browser (e.g. onehalfstorey_vv3 or a fresh one): press the button, look at both floors, nothing saved by me.

## Safety gate

Can any changed path publish geometry without an approved reference? No -- furniture suggestions in the editor only; saving stays Rainer's click.

## Rollback

`.before-alles-einrichten` backups of page.tsx and moebel-vorschlag.mjs; remove the new test cases.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement moebel-alles-einrichten-v1, tests first, try it on one house without saving."

## Implementation record (2026-10-23)

- `moebel-vorschlag.mjs`: new `richteAlleRaeumeEin({raeume, oeffnungen, vorhandene, raumKanten, hindernisse})` -> `{moebel, eingerichtet, uebersprungen, weggelassen}`; type from `raumtypAusName`; skips non-rooms (Luftraum/Treppe/Terrasse/Balkon), rooms without a clear type, rooms already furnished; furniture of earlier rooms counts as occupied for later rooms.
- Addition found in the live check: the stair was not an obstacle -- the Diele's Garderobe landed on the steps. The button now passes the stair outline as `hindernisse` (occupies space, does not count as "already furnished"). Same flaw exists for manual "Bereich einrichten" (not changed here, roadmap).
- `page.tsx`: button "✦ Alle Räume einrichten" above "✦ Bereich einrichten"; same openings/existing/room-edge input as `onEinrichten`; one `placeMany` (one Undo); status lists eingerichtet / ausgelassen / nicht untergebracht; blocked while geometry loads.
- Tests first: moebel-vorschlag.test.mjs +7 (red before, 37/37 after). tsc: no errors in the touched files. Other scripts/*.test.mjs: 4 files fail (build-floorplan-search-catalog, furniture-placement, local-floorplan-workbench, measured-pdf-pilot) -- none imports the changed files; not caused by this change.
- Live, onehalfstorey_ve (no furniture yet), nothing saved: EG 9 pieces (WC, Gast, HWR/HTR, Diele; Wohnen/Essen/Kochen skipped; not placed: Gast one nightstand, Diele Schrank), OG 17 pieces (Kind, Kind, Eltern/Schlafen, Bad, Flur; Abstellraum skipped -- no room type for it). Reloaded afterwards; ve still has no furniture file.
