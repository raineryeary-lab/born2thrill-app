# Every Stuff box tells Codex which room it is in

Status: DONE 2026-10-23

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-23: "Yes: plan the fix so every Stuff box tells Codex which room it is in."
Found during the sauna-fitness-hobby-v1 live test on bungalow_v1: the two Stuff boxes in the Fitness room should become treadmill, bench, mirror. But Codex never hears that they are in Fitness.

## Current evidence

- `scripts/make-codex-job.py` `_marker_liste(objekte, lagen, masse=None, raeume=None)` (~1032): when `raeume` maps `stuff-N` to a room, the marker text becomes "... hier im Raum "Fitness": Fitnessgeraete: ...". This uses `stuff_inhalt()` / `STUFF_NACH_RAUM` (~446-490). The test `make-codex-job.test.py` ~1546 covers this.
- But the only real call (~1602) is `_marker_liste(eigene, eigene_lagen, eigene_masse)`, with **no `raeume`**. So every real job falls back to the general Stuff text. This affects all houses and rooms (Bad, HWR, Kind, Fitness, Sauna, Hobby).
- `scripts/render-furnished-dollhouse.py` (~6111-6157) already finds the room of each Stuff box by point-in-polygon on `floor_doc["rooms"]`. It uses the room to pick gaming station or shelf, then throws the room name away. The objects are named `stuff-<n>-gaming|utility|shelf...`.
- `objekte_und_lagen()` (~607) reads names, positions and sizes from the .blend in one Blender run. The .blend is the single source the job already trusts.

## Exact scope

1. Dollhouse builder: every object built for a Stuff box gets a custom property `raum` with the room's name as drawn (e.g. "Fitness", "HWR / HTR"). This is written where the room is already found. No change to geometry or materials.
2. `objekte_und_lagen()`: also reads `raum` per object, in the same Blender run. It returns it as an extra map `bauteil -> raum`, e.g. `stuff-3 -> Fitness`. The existing return values stay as they are. Callers that unpack five values get a sixth only through a new name, or a backward-compatible wrapper, so no existing caller or test changes meaning.
3. The real `_marker_liste(...)` call passes this map as `raeume`.
4. Old .blend files without `raum` keep the general Stuff text, exactly as today. Nothing is guessed.

## Out of scope

- New Stuff texts (they already exist), new geometry for Stuff, and changes to which shelf or gaming station gets built.
- Re-making old Codex jobs. That happens only when Rainer asks for a house.

## Tests (first)

- `make-codex-job.test.py`: the seam test. With a fake Blender result where `stuff-3` has `raum = "Fitness"`, the job's marker for `stuff-3` must contain "Laufband". With no `raum`, it must still contain "(ersetzen)". Also a source check that the real `_marker_liste(` call passes `raeume=`.
- Dollhouse test (`scripts/*dollhouse*.test.py`, or a new small one): a source or seam check that the Stuff branch writes `["raum"]`.
- All existing tests stay as they are.

Real check: rebuild bungalow_v1 (no upload), read `raum` from the .blend (`stuff-* -> Fitness`), and build the job in memory. The Fitness markers must say "Fitnessgeraete: Laufband ...". No job folder is written unless Rainer asks.

## Safety gate

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. Only a label on existing objects and the text of a local Codex job change. Nothing is uploaded or sent.

## Rollback

`.before-stuff-raum` backups of render-furnished-dollhouse.py and make-codex-job.py; remove the new test cases.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement stuff-raum-an-codex-v1, tests first, check it on bungalow_v1 (no upload)."

## Implementation record (2026-10-23)

- render-furnished-dollhouse.py `add_catalog_styling()`: after the Stuff loop, every MESH object whose stem is `stuff` gets `obj["raum"]` = the name of the room its bounding-box centre lies in (same point-in-polygon as the Stuff branch). Done by position because the plain boxes (`stuff-<placed>`) and the ensembles (`stuff-<stuff_index>-...`) are numbered differently. A first try tagged by name prefix and only reached the ensembles; replaced in the same session.
- make-codex-job.py: the Blender run prints `RAUM <obj> <name>`; the parser stores it as `masse[obj]["raum"]` (return shape unchanged); new `raeume_aus_massen(masse)` -> `{bauteil: raum}`; the real `_marker_liste(...)` call passes `raeume=raeume_aus_massen(eigene_masse)`.
- Tests first (red, then green): make-codex-job.test.py `StuffRaumNahtTests` (5), render-furnished-dollhouse.test.py `StuffTraegtRaumTests` (1). make-codex-job, render-furnished-dollhouse and sauna_codex suites OK. Other suites unchanged: build-simplifier-render-plan 1 failure (bungalow_039 door ids, also red with the pre-sauna file), and the 7 known red JS tests.
- Live, bungalow_v1 rebuilt (exit 0, no upload): interior-modern-baseline.blend gives a room for all 12 Stuff markers. stuff-2/3/31/32 are "Fitness", and their markers read "Fitnessgeraete: Laufband oder Ergometer, Hantelbank, Spiegelwand, Matte". No Codex job folder was written.
- Backups: `.before-stuff-raum` for both scripts and both test files.
