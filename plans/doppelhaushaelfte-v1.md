# Doppelhaushälfte: mark on top of the storey type, searchable as Haustyp, neighbour half outside

Status: DONE 2026-10-23 (plugin deploy = Rainer)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

Touches floorplan-simplifier (Annotator mark), born2thrill-local-workbench (plan builder, exterior, Codex job, catalogue row) and the WordPress plugin file in this repo (deploy is Rainer's step).

## Objective

Rainer, 2026-10-23, onehalfstorey_046: "could we create a new class of house this is a doppelhaushälfte so what do you suggest?" -- and: "we have to also declare the doppelhaushälfte als haustyp durchsuchbar".

## Current evidence

- onehalfstorey_046: data.json `house_type: "1.5-storey"`, 6.99 x 11.49 m. Nothing is drawn yet (0 rooms, 0 elements). The east outer wall has no windows on either floor (party wall); the west side has the entrance and the upstairs windows.
- Catalogue: `scripts/katalogzeile.py HAUSTYPEN` maps house_type to ONE `haustyp` text. `wordpress/b2t-katalog-freigabe.php` (~212) only accepts `Bungalow, Zweigeschosser, 1,5-Geschosser, Sonstige, Zweigeschosser mit Keller` and rejects anything else with HTTP 400. The search filters on this one column.
- Storeys, roof rules and the 1,5-storey knee wall all hang on house_type (anderthalb.ist_anderthalb, run_project.roof_types_for_plan). A NEW house_type would switch them off.

## Exact scope

1. **Mark, not a new storey class.** New field `doppelhaus: {"trennwand": "east"|"west"|"north"|"south"}` beside the drawing (annotations.json, set in the Annotator). house_type stays (1.5-storey, bungalow, 2-storey), so roof and storey rules keep working.
2. **Annotator:** a "Doppelhaushälfte" switch with the party-wall side. It suggests the longest outer side without windows; Rainer confirms. Saved with the drawing.
3. **Searchable:** `katalogzeile.py`: a Doppelhaushälfte gets `haustyp = "Doppelhaushälfte"`. The storey count stays visible through `geschosse`. The WordPress plugin accepts the value "Doppelhaushälfte" (one line in the list). **Deploying the plugin is Rainer's step**; I only change the file and say so.
4. **Party wall:** the plan builder marks that outer wall `wall_type: "trennwand"`, 365 mm, no openings (a drawn opening there gets a warning, not silently dropped). Inside, it is drawn like an outer wall.
5. **Outside picture (default: mirrored twin):** render-exterior builds the **mirrored neighbour half** across the party wall. It has the same body, walls, windows and roof, and the roof continues as one piece over both halves. The camera stands on the free corner, so "our" half is in front. The neighbour gets a marker in the .blend (`nachbar`).
6. **Codex job:** says that the neighbour half belongs to the picture, gets the same material, stays plain and gets no extra detail. "Our" half is the product.
7. **Living area and price:** only our own half (unchanged: only drawn rooms count).

## Out of scope

- Reihenhaus (more than two units); different neighbour designs; WordPress search UI changes beyond accepting the value (if the site's filter list is hard-coded elsewhere, it is noted as a follow-up).

## Tests (first)

- katalogzeile: a project with `doppelhaus` gives haustyp "Doppelhaushälfte"; without it, unchanged.
- PHP list contains "Doppelhaushälfte" (source check, like the existing plugin tests).
- Plan builder: on a synthetic 1,5-storey project with `doppelhaus.trennwand = "east"`, the east outer wall is `trennwand`, 365 mm, and the plan carries `doppelhaus`; without the mark, identical to today.
- render-exterior (pure helpers): mirroring the footprint and openings across the party-wall line; the combined roof footprint is the union of both halves.
- Annotator: the suggestion picks the windowless long side (pure helper test).
- Existing tests unchanged.

Real check: Rainer draws onehalfstorey_046 and sets the mark (or I test on a copy that is not saved). Build (no upload): the exterior shows a double house with one roof, our half in front; the dollhouse is unchanged except for the thicker party wall.

## Safety gate

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. The neighbour half is a mirrored copy of the drawn half, marked as such. Nothing is uploaded; the plugin change takes effect only when Rainer deploys it.

## Rollback

`.before-doppelhaus` backups; remove the new tests; drop the `doppelhaus` field.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement doppelhaushaelfte-v1 (mirrored twin, Haustyp Doppelhaushälfte), tests first, test on a copy without saving (no upload)."

## Implementation record (2026-10-23)

- floorplan-simplifier:
  - `app.py normalize_doppelhaus()` + `write_annotations` stores `doppelhaus`;
  - `static/doppelhaus.js trennwandVorschlag()` suggests the longest outer side without windows/doors on any floor;
  - annotate.html has the "Doppelhaushälfte" select (Nein / Trennwand Ost/West/Nord/Süd) with a suggestion hint;
  - annotate.js state/load/save/change;
  - cache: annotate/zoom-pan/geometry-tools -> 20261023-3, doppelhaus.js 20261023-1. Annotator restarted.
- workbench `scripts/doppelhaus.py` (pure): `normalisieren`, `trennwand_markieren` (exterior walls on that side get `trennwand: true` and 365 mm; wall_type stays "exterior" -- deviation from the draft's `wall_type: "trennwand"`, which would have broken the exterior loop tracing), `ebene_mm`, `dachachse`, `kamera_seite`.
- build-simplifier-render-plan.py:
  - `doppelhaus_plan()` marks every floor and warns on openings in the party wall;
  - the plan carries `doppelhaus: {trennwand, ebene_mm}`;
  - `roof_axis_override` defaults to the axis across the party wall.
- render-exterior.py:
  - every Exterior mesh crossing the party-wall plane is cut there with `bmesh.ops.bisect_plane` (no boolean), then a mirrored linked copy `nachbar-*` (custom prop `nachbar`) is added;
  - the camera never looks from the party-wall side (L-notch logic off), and the whole double house is framed;
  - the ground pad is widened.
- make-codex-job.py: `aussen_regel(plan_doc)` adds DOPPELHAUS_REGEL (neighbour half in the picture, same material, plain, roof runs through).
- Catalogue:
  - `katalogzeile.py` gives haustyp "Doppelhaushälfte" for a marked house;
  - the plugin `b2t_haustypen()` includes it, and the `/katalog` route accepts an optional `haustyp` for EXISTING rows (onehalfstorey_046 is live as "1,5-Geschosser");
  - `publish-renders.py haustyp_nachziehen()` switches an existing row to "Doppelhaushälfte" at upload time (only this change; respects --dry-run);
  - plugin version 1.2.0 and wordpress/b2t-katalog-freigabe.zip rebuilt (backup .before-doppelhaus). **Not deployed.**
- Tests first:
  - scripts/doppelhaus.test.py: 17, red before, green after;
  - floorplan-simplifier tests/test_doppelhaus.py: 3, red before, green after;
  - static/doppelhaus.test.mjs: 4. One case had an ambiguous tie and was corrected before the code existed.
  - Suites: simplifier all green. Workbench: only the known red bungalow_039 door test and the 7 known red JS tests.
- Real check (copy, not saved): temp project `zz_doppelhaus_test` = copy of onehalfstorey_044 with `doppelhaus.trennwand = east`, plan + exterior rendered into the scratch folder:
  - party walls wall-6/wall-7 at 365 mm, plane at 11179 mm; warning for the one window 044 has there;
  - "83 Objekte" mirrored;
  - picture: one double house, roof continuous, our half in front with its free gable;
  - the copy was deleted afterwards, and nothing went to E: or the live site.
- Annotator check on onehalfstorey_044: the switch is shown, choosing "Ost" sets `{"trennwand":"east"}`, the page was reloaded without saving, and annotations.json is unchanged.

## Nachtrag 2026-10-23 (Giebel offen)

- Rainer, onehalfstorey_046 (Blender screenshot): "the giebel is not quite closed".
- Cause: the Doppelhaus rule turns the ridge across the party wall, here along the SHORT side (x). `render-exterior.py` (1,5-storey path) always took the short side for the ridge height (`_ah_kurz = min(...)`), so the gable walls were cut ~0.9 m too low.
- Fix: new `anderthalb.spannweite(bbox, along_x)` gives the width across the actual ridge. render-exterior uses it. For every house without a turned ridge, the value is unchanged (span = short side).
- Tests first: doppelhaus.test.py `FirstHoeheTests` (2): red before, green after (19/19). Suites: only the known bungalow_039 door test red.
- go.py onehalfstorey_046: "fertig". The log shows "First ~8.45 m" (before ~6.7), and the render shows the gable closed to the ridge. Codex job remade (10 pictures). No upload.
