# Sauna, Fitness, Hobbyraum: eigene Raumtypen, Saunakabine als Möbel, Rest über "Stuff"

Status: IMPLEMENTED 2026-10-23 -- live-tested on bungalow_v1; Stuff-room wiring to Codex missing (needs plan revision)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

Touches floorplan-simplifier (room list) and born2thrill-local-workbench (furniture catalogue, plan builder, Codex job).

## Objective

Rainer, 2026-10-23: a bungalow with a sauna and a fitness area, sometimes hobby rooms -- "could we have a room with stuff we declare differently or should we make these different room types and just add 'stuff' so that codex decides what to put there?" Agreed: own room types + "Stuff" boxes that Codex fills by room name; the sauna is a **cabin in the room** ("cabin in the room") -> its own resizable furniture piece.

## Current evidence

- `make-codex-job.py` `STUFF_NACH_RAUM` (~430-465) + `stuff_inhalt(raumname)`: tells Codex per room name what a Stuff box becomes (Bad -> towel shelf, HWR -> storage shelf ...). No entry for sauna/fitness/hobby (falls back to "Regal mit Dingen, die in diesen Raum gehoeren").
- `src/lib/generator/symbol-catalog.mjs`: "stuff" is a rect symbol (drag to any size, 800 mm high), appended to every room list (`ROOM_SYMBOL_SETS`); no sauna/fitness/hobby lists.
- `build-simplifier-render-plan.py` `RECT_BUILD` / sizes (~103, ~141) know "stuff".
- The Annotator room list has no Sauna/Fitness/Hobby entry (to be confirmed in floorplan-simplifier room catalogue).

## Exact scope

1. Annotator room list: **Sauna / Wellness**, **Fitness**, **Hobbyraum**.
2. Furniture catalogue: new rect symbol **"saunakabine"** (drag to size, 2100 mm high) -- Codex renders it as a wooden sauna cabin with glass door, two bench levels and a stove inside its footprint. Room lists: wellness -> saunakabine, dusche, handwaschbecken, badheizkoerper (+stuff); fitness -> (only stuff for now); hobby -> schreibtisch, sideboard (+stuff).
3. Plan builder / dollhouse: saunakabine built as a box of its footprint (like stuff/kleiderschrank), so the room shows it in the raw build.
4. Codex job: object text for saunakabine; Stuff contents: Fitness -> "Fitnessgeräte: Laufband oder Ergometer, Hantelbank, Spiegelwand, Matte"; Hobby -> "Werkbank oder Basteltisch mit Regal voller Material"; Sauna/Wellness -> "Liegen, Handtuchregal, Pflanzen".
5. Room-type mapping for "Alle Räume einrichten" (`raumtypAusName`): these rooms are skipped (no automatic rule yet) -- stated in the status line.

## Out of scope

- Living-area/price rules for these rooms (unchanged: they count like any room).
- Automatic furnishing rules for them.

## Tests (first)

- make-codex-job.test.py: `stuff_inhalt("Fitness")`, `("Hobbyraum")`, `("Sauna")` give the new texts; saunakabine appears in the job's object list with its text.
- symbol-catalog test: "saunakabine" exists, rect placement, in the wellness list; stuff still in every list.
- build-simplifier-render-plan test: saunakabine is a RECT_BUILD symbol with height 2100.
- Annotator: new room names in the room list (Python test on the catalogue).
Real: draw one Sauna room with a cabin and one Fitness room with Stuff on a test copy or the bungalow Rainer names; build; look at the raw render and the Codex Auftrag text. Nothing uploaded.

## Safety gate

No geometry is published; catalogue/labels and local builds only.

## Rollback

`.before-sauna` backups of the touched files; remove the new test cases.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement sauna-fitness-hobby-v1, tests first; test it on the bungalow with the sauna (no upload)."

## Implementation record (2026-10-23)

- Annotator: app.py ROOM_CHECKLIST + annotate.js room list: sauna "Sauna / Wellness", fitness "Fitness", hobby "Hobbyraum". Cache annotate/zoom-pan/geometry-tools -> 20261023-2. Annotator restarted; served annotate.js shows the three rooms.
- symbol-catalog.mjs: rect symbol "saunakabine" (2100 mm, sanitaer); ROOM_SYMBOL_SETS sauna/fitness/hobby; label buckets sauna/wellness, fitness/sport, hobby/werkstatt. Reference copy legacy/symbol-catalog.js got the same key (as done for glasschiebetuer/playstation_gruppe), so the existing port test passes unchanged.
- build-simplifier-render-plan.py: saunakabine in RECT_BUILD, SYMBOL_3D 2100 wardrobe box.
- make-codex-job.py: NENNENSWERT saunakabine text; STUFF_NACH_RAUM fitness/sport, hobby, werkstatt, sauna/wellness.
- Tests first (red before, green after): floorplan-simplifier tests/test_raumtypen_sauna.py; 2 new cases in scripts/symbol-catalog.test.mjs (16/16); scripts/sauna_codex.test.py.
- Suites: simplifier 318 Python OK, all static/*.test.mjs green. Workbench scripts/*.test.mjs: 7 failures in furniture-placement (2), build-floorplan-search-catalog (1), local-floorplan-workbench (3), measured-pdf-pilot (1) -- identical with the pre-change catalogue swapped back in, so pre-existing, not caused here.
- Live test, bungalow_v1 (Rainer named it, 2026-10-23): Annotator area "Abstellraum" -> "Fitness" (the original plan labels it Fitness; saved via the Annotator UI). Furniture floor-0.json: the "badewanne" stand-in in the sauna corner -> saunakabine points_mm [[1800,1060],[5060,2600]]. Geometry identity unchanged. run_project.py --styles modern,classic --floors 0: exit 0, R2-R6 PASS, 5 .blend certified. interior-modern-baseline.png shows the cabin as a tall wooden box in the Bad corner and two Stuff boxes in Fitness. Backups: annotations.json.before-sauna-test, floor-0.json.before-sauna-test. Nothing uploaded.
- PLAN MISMATCH found: make-codex-job.py calls `_marker_liste(eigene, eigene_lagen, eigene_masse)` (~1602) without `raeume`, so `stuff_inhalt(raum)` never reaches a real job -- no Stuff box is ever told its room (also the older Bad/HWR/Kind texts). Saunakabine's NENNENSWERT text does reach the object list (~1902). Wiring the room per Stuff box needs a plan revision.
- Backups: *.before-sauna next to every touched file (incl. static/annotate.html, legacy/symbol-catalog.js).
