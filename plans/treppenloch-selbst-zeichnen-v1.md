# Treppenloch selbst zeichnen (Treppenöffnung-Fläche mit Geländer-Kanten)

Status: IMPLEMENTED 2026-10-20 -- verified in tests, Annotator (no save) and scratch builds; not committed

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-20: "we need a checkbox 'Treppenloch selbst zeichnen' and then be able to draw the Geländer".

The automatic Treppenloch (the stair's outline, `treppenloch-folgt-treppenform-v1`) stays the default. When Rainer draws the opening himself, his drawing wins, and he picks its railings edge by edge.

Chosen design (Rainer: "great idea"): no new tool and no separate checkbox state. The **drawn area is the switch**:

- Draw a room area of type **Treppenöffnung** on the upper floor, and that polygon is the Treppenloch.
- Railings work exactly like at the Luftraum: click an edge to toggle its railing; Alt+click returns to automatic.
- Delete the area, and the automatic cut is back. A separate checkbox could disagree with the drawing; this cannot.
- For findability, the stair's right-click menu gets an entry "Treppenloch selbst zeichnen". It only starts the room tool with Treppenöffnung preselected; it stores nothing.

## Current evidence and behavior

- The room type exists: `annotate.js:214` `{ id: "treppenoeffnung", label: "Treppenöffnung" }`, `app.py:313`.
- It is already excluded from living area: `app.py:4991` `non_room_ids = {"luftraum", "treppe", "treppenoeffnung", ...}`. `konfigurator-matrix.py:74` excludes labels containing "treppe" (to be confirmed by test that "Treppenöffnung" matches).
- `stairCopyRoom()` (`annotate.js:2892`) already turns a copied "Treppe" area into a "Treppenöffnung" area on the floor above.
- But no project uses it today. A scan of all `projects/*/annotations.json` on 2026-10-20 found 0 Treppenöffnung areas. (The 100 upper-floor `stairs` elements with `role: "opening"` are polylines, not areas; they are untouched.)
- The render chain ignores it. `build-simplifier-render-plan.py` gives it `room_kind()` "living" and the renderer lays floor over it. Only Luftraum is a hole (`is_luftraum`, line 198; kind "luftraum", `gelaender_kanten`, lines 3561-3567).
- Luftraum railings already exist end to end:
  - Annotator: `static/luftraum-gelaender.js`, edge click -> `gelaender_kanten` on the room.
  - Plan builder: removes interior walls between Luftraum and circulation/Galerie (lines 3570-3595).
  - Renderer: `render-furnished-dollhouse.py` around lines 4320-4395, no floor, `_lr_lauf` per chosen edge, automatic = every edge without a wall within 300 mm.
- The stair's own loch railings (`loch-rail-*`, `loch_railing_sides`) are built from the stair band and would double up with a drawn opening.

## Repository baselines

- `born2thrill-local-workbench`: branch `agent/furnished-render-and-annotation-schema`, HEAD `5be1a4e`, user-owned dirty worktree (351 entries), uncommitted work from today in `scripts/render-furnished-dollhouse.py` and untracked `scripts/render-persp-test.py`, `scripts/treppenloch_form.test.py`.
- `floorplan-simplifier`: branch `agent/annotation-window-type-door-swing`, HEAD `8a08d19`, 177 entries in `git status --short` (user-owned). Already dirty before this task: `app.py`, `static/annotate.html`, `static/annotate.js` (modified); `static/luftraum-gelaender.js` and `static/waende-einrasten.js` (untracked). Nothing is cleaned.

## Exact scope

### Annotator (floorplan-simplifier/static)

1. `luftraum-gelaender.js`: the edge-click railing applies to Treppenöffnung areas as well (`istLuftraum` -> `istDeckenloch`: label or `room_ids` contains luftraum or treppenoeffnung). Same field, `gelaender_kanten`; same drawing (chosen edges thick orange, others dashed).
2. Stair right-click menu: a new entry "Treppenloch selbst zeichnen". It switches to the room-area tool on the floor above with Treppenöffnung preselected. If one already exists there, the entry reads "Treppenloch: eigene Fläche aktiv" and selects it.
3. While a Treppenöffnung area exists on a floor, the stair's per-segment loch-railing edges on that floor are shown greyed, with the hint "ersetzt durch gezeichnetes Treppenloch". The stored `loch_railing_sides` are kept, not deleted, so removing the area brings them back.

### Plan builder (`build-simplifier-render-plan.py`)

4. An area whose label or ids say Treppenöffnung gets `kind: "treppenoeffnung"` and carries `gelaender_kanten`, like Luftraum.
5. The interior-wall removal towards circulation/Galerie that Luftraum gets also applies to Treppenöffnung. Otherwise the generated wall between the hole and the Flur would stand where the railing belongs.

### Renderer (`render-furnished-dollhouse.py`, `render-persp-test.py` kept in step)

6. If the floor has at least one `treppenoeffnung` room:
   - The automatic stair-outline cut is off (`_hole_quads = None`). These rooms get no floor, like Luftraum.
   - No `loch-rail-*` from the stair band. Instead, railings run on the drawn edges through the existing Luftraum railing routine (`_lr_lauf`), named `treppenloch-gelaender-<room>-<i>`.
   - Automatic edge choice (when `gelaender_kanten` is None) = the Luftraum rule (edges without a wall), MINUS the Austritt. Any edge the stair's arrival edge (`end` of the band) lies on, within 150 mm, stays open; the stair's `start` and side edges get no special treatment. A pure function `deckenloch_auto_kanten(poly, wall_near, austritt)` makes this testable. Manual `gelaender_kanten` always wins, including an Austritt edge if Rainer picks it.
   - The ground plane a storey down is cut by the bbox of all drawn openings plus the stair.
   - Checks (WARNUNG in the log, the build continues):
     - (a) the stair's arrival edge is not inside or on the drawn opening, i.e. the stair would come up under the floor;
     - (b) less than 50 % of the stair band's top 2 m-headroom zone lies inside the opening;
     - (c) the drawn opening overlaps a non-circulation room by more than 0.05 m2.
7. Without a Treppenöffnung area, nothing changes: today's automatic cut and loch railings.

### Einrasten: Lochkanten auf die Wand (Rainer, 2026-10-20)

"those walls where the stairs are have to align, otherwise we have floors peeking out in the middle of the walls, so somehow we need a snap in there."

Why it matters: when a hole edge stops a few centimetres short of a wall face, or runs inside the wall zone, the 220 mm slab shows as a strip in the middle of the wall. This happens on the upper floor, and, if the stairwell wall below sits elsewhere, also against the wall of the floor below.

8. Annotator, while drawing or editing a Treppenöffnung area: each edge snaps onto the nearest wall face it is roughly parallel to.
   - Rule: within 0.6 m and at most 20 degrees off.
   - Reuses `oeffnungEinrasten`'s rules and constants from `waende-einrasten.js`, but snaps to the FACE on the hole side, not the wall centre: the neighbouring room's edge is that face.
   - Snapped edges are drawn solid; unsnapped edges are drawn red and dashed, so a near-miss is visible.
9. Annotator, on the upper floor: the floor below's walls around the stair show as faint grey lines and are snap targets too, so the hole can follow the stairwell wall underneath.
10. Renderer safety net, for BOTH the drawn and the automatic (stair-outline) hole:
    - A hole edge within 150 mm of a parallel upper-floor wall face is moved onto that face before the slab is cut. No sliver of slab is left between hole and wall, and the hole never cuts into the wall zone.
    - This also fixes the same peeking on stairs drawn a few cm off a wall, without a drawn opening.
    - Logged per edge: `[dollhouse] Treppenloch Kante k auf Wand <id> gerastet (Δ 38 mm)`.
11. Renderer check: when a hole edge sits on an upper wall face, but the floor-below wall under it is offset by more than 30 mm (or missing), it prints `WARNUNG Treppenhauswand EG/OG versetzt um X mm`. It does not move walls; fixing that is a drawing decision.

Pure functions, so they can be tested:
- `lochkanten_einrasten(poly, wall_faces, max_mm=150, max_grad=20)` in the renderer;
- `lochEinrasten(...)` next to `oeffnungEinrasten` in the Annotator.

## Files in scope

- `floorplan-simplifier/static/luftraum-gelaender.js`, `floorplan-simplifier/static/annotate.js` (menu entry, greyed loch edges, ghost walls of the floor below), `floorplan-simplifier/static/waende-einrasten.js` (`lochEinrasten`), `annotate.html` only if the menu markup lives there.
- `born2thrill-local-workbench/scripts/build-simplifier-render-plan.py`
- `born2thrill-local-workbench/scripts/render-furnished-dollhouse.py`, `scripts/render-persp-test.py`
- New tests: `scripts/treppenloch_gezeichnet.test.py` (workbench), `floorplan-simplifier/tests/test_treppenoeffnung_flaeche.py`

## Explicitly out of scope

- Freehand railing lines not on an edge of a drawn opening. A railing always sits on a hole edge, so it cannot float.
- Changing the automatic cut from `treppenloch-folgt-treppenform-v1`.
- Migrating existing projects (there is nothing to migrate: 0 Treppenöffnung areas exist).
- The 100 upper-floor `stairs` opening polylines.
- Rebuilding or uploading any house.

## API, schema, and data-contract effects

- Annotation: no new field. `gelaender_kanten` already exists on rooms; it may now also sit on a Treppenöffnung area.
- Render plan: rooms may carry `kind: "treppenoeffnung"` (new kind value) with `gelaender_kanten`. Readers that switch on `kind` must treat an unknown kind like today's default. Checked by grep for `kind ==` / `.get("kind")` consumers before implementing (listed in the implementation report).
- Living area / price: Treppenöffnung stays excluded (`app.py:4991`; `konfigurator-matrix.py:74` confirmed by test).

## Acceptance criteria

1. Without a Treppenöffnung area, twostorey_059 builds byte-identically in slab and railing objects to the build after `treppenloch-folgt-treppenform-v1` (same object names, same vertex positions within 0.1 mm).
2. With a drawn Treppenöffnung on twostorey_059's upper floor:
   - there is no floor inside the drawn polygon and floor everywhere else outside it (probe as in the previous plan);
   - there is no `loch-rail-*`, and railings sit exactly on the chosen edges, with floor on their outer side;
   - in automatic mode the Austritt edge has no railing.
3. Clicking an edge in the Annotator toggles the railing and survives save and reload. Alt+click resets.
4. The right-click entry opens the room tool with Treppenöffnung on the floor above.
5. Living area and price are unchanged by drawing a Treppenöffnung area.
6. The checks (a)-(c) print when provoked (test fixtures).
7. Snap: an opening drawn 40 mm short of a wall face ends exactly on it, both in the Annotator (after release) and in the renderer (the safety net, tested with a drawing that was NOT snapped). After a rebuild of twostorey_059, no slab face lies between a hole edge and a wall face, and none lies inside the wall zone (probe: sample 20 mm off every hole edge that has a wall).
8. The offset check prints for a fixture with the stairwell wall below moved 60 mm.

## Tests and verification commands

- `python scripts/treppenloch_gezeichnet.test.py` (new, AST isolation, no Blender):
  - `deckenloch_auto_kanten`: Austritt edge excluded, wall edges excluded, manual choice wins;
  - kind and `gelaender_kanten` passthrough in the plan builder;
  - wall removal towards Flur;
  - konfigurator area exclusion.
- `python -m pytest floorplan-simplifier/tests/test_treppenoeffnung_flaeche.py` (new):
  - a Treppenöffnung area with `gelaender_kanten` survives save/reload through `app.py`;
  - it is excluded from living area.
- Snap: `lochkanten_einrasten` cases (40 mm short, 40 mm into the wall, 30 degrees off = no snap, 200 mm away = no snap, two walls at a corner); a JS case for `lochEinrasten` next to the existing `oeffnungEinrasten` checks, run the same way they are.
- Existing: `scripts/treppenloch_form.test.py`, `render-furnished-dollhouse.test.py`, `build-simplifier-render-plan.test.py` (known pre-existing failure `test_door_hinge_and_swing_are_normalized_into_the_walls_frame` stays reported, not touched), the floorplan-simplifier test suite.
- Browser: in the Annotator on twostorey_059 (upper floor), draw the area, toggle edges, save, reload.
- Blender: rebuild twostorey_059 upper floor into scratch (not go-baseline) with and without the drawn area; probe as in the previous plan; look at the render.
- No existing test is deleted, skipped or weakened.

## Protected and risky paths

- Toolchain hash: both renderer files and `build-simplifier-render-plan.py` are hashed, so every build counts as outdated (already the case today).
- Annotator edits change saved annotation hashes only when Rainer draws something. Code alone changes no project.
- `gelaender_kanten` edge indices are polygon-vertex order; the Luftraum path already relies on the same order through the plan builder, unchanged.
- The test drawing on twostorey_059 for acceptance 2 is made in a COPY of its annotations in scratch, never in the real project. Rainer draws the real one himself.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. The drawn opening is Rainer's own annotation, read like every other room polygon. No generation, approval, publication or email path is touched.

## Customer, email, database, deployment, and external effects

None. No upload, commit or push.

## Failed-hypothesis log

None yet.

## Rollback

Revert the hunks in the five files and delete the two new tests. Any Treppenöffnung areas Rainer has drawn meanwhile then render as ordinary floor again (the pre-change behaviour); they stay in the annotations and can be deleted in the Annotator.

## Unresolved questions

1. Should the wall between the drawn opening and a non-circulation room (bedroom, bath) stay? Proposed: yes, same as Luftraum.
2. Snap tolerance in the renderer: 150 mm proposed (the stair band is often drawn a hand's width off). Larger risks pulling an intentionally free edge onto a wall.
3. Railing height: Luftraum uses 0.90 m. Keep 0.90 m, or use the stair loch-rail height (it ends at z 3.545 m, so 0.90 m above the slab top too)? Proposed: 0.90 m, same as both today.

## Approval record

Approved by Rainer in chat, 2026-10-20: "Approved: implement treppenloch-selbst-zeichnen-v1 including the snapping, 150 mm renderer tolerance, 0.90 m railings, walls to bedrooms stay." Unresolved questions 1-3 are answered by that.


## Verification record (2026-10-20)

Tests:
- `scripts/treppenloch_gezeichnet.test.py`: 20 OK (9 cases x 2 renderers, incl. the Austritt distance, + 2 plan-builder). Failed before the implementation.
- `scripts/treppenloch_form.test.py` 14 OK, `render-furnished-dollhouse.test.py` 26 OK, `glasschiebetuer_render.test.py` 7 OK, `stair_access.test.py` 9 OK, `hausdaten.test.py` 37 OK.
- `build-simplifier-render-plan.test.py`: 72 run, 1 FAIL -- the known, pre-existing `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`, unrelated.
- floorplan-simplifier: `unittest discover` 312 OK (incl. new `test_treppenoeffnung_flaeche.py`, 4). All `static/*.test.mjs` pass (incl. new `loch-einrasten.test.mjs`, 5).
- One failure on the way: `test_cache_busting_stayed_in_step` failed after only some ?v= strings were bumped. All three now carry 20261020-1.

Annotator (browser, twostorey_059 upper floor, nothing saved; annotations.json unchanged at its 09:09 timestamp):
- All new functions load, no console errors.
- The right-click entry "Treppenloch selbst zeichnen" switches to the room tool with Treppenöffnung.
- The floor below's walls (31 edges) are drawn faint grey.
- A test hole drawn around the stair snapped its top edge onto the neighbouring wall face.

Scratch builds (session scratchpad, never go-baseline):
- **Drawn hole**: copy of the project + a Treppenöffnung 40 mm inside the stair band, plan built by a driver pointing the plan builder at the copy, no furniture.
  - The log: the hole replaces the automatic cut; edge 4 snapped onto wall-1 (it reached 62 mm into the wall); 3 automatic railings.
  - The probe: no floor inside the drawn hole (0/3036 samples); floor outside all 4 edges; 0 `loch-rail-*`; railings `treppenloch-gelaender-*` on 3 edges; the 4th is the wall.
- **The test drawing itself revealed a trap**: the hole ran 452 mm past the Austritt, so no edge was left open and the stair ended in front of air. Added check (d), `austritt_abstand_zur_kante`, with a test; the rebuild prints "der Austritt liegt 452 mm vor der Lochkante".
- **Automatic (no drawn hole)**, go-baseline plan with `DMH_ALLOW_STALE=1`: the snap moved one stair edge 1 mm onto wall-6. The probe is otherwise identical to the treppenloch-folgt-treppenform-v1 result (Treppenauge and notch are floor, all 6 railings on floor, 0 floor over the stair).

Deviations from this plan (reported, not hidden):
- Acceptance 1 ("byte-identical without a drawn hole") is NOT literally met. Item 10 applies the snap to the automatic cut as well, by design. Measured effect on twostorey_059: one edge, 1 mm; probe unchanged.
- Item 8: unsnapped edges are not drawn red. After the automatic snap there is no near-miss left to show, and wall-free edges are legitimate railing edges. Snapping runs when an area is finished, not when single points are dragged later.
- `render-persp-test.py` (test copy) has no Luftraum railing routine at all. It gets the cut, the snap, the checks' helpers and the no-floor rule, but builds no railings on a drawn hole.
- Acceptance 5 (price unchanged) is open. `app.py` treats Treppenöffnung as non-room, but `konfigurator-matrix.py` counts every area except garage/terrace/balcony/loggia/cellar, so a drawn Treppenöffnung adds its m2 to the price (as Luftraum does on purpose). If it is drawn on top of the Flur instead of cutting the Flur, it is counted twice. Not changed; needs Rainer's rule.

Noticed, not changed:
- twostorey_059 already has a "Luftraum" area on the upper floor (and one on the ground floor) next to the stair.
- CORRECTED 2026-10-20: the upper-floor stair `opening` copy is NOT 450 mm off. Measured through the registered upper-floor frame it matches the ground-floor stair within 40 mm (width 980 vs 900 mm). The overshoot came from the scratch driver (`sim_build.py`), which placed the test hole in raw image units without the upper floor's registration.

## Amendment A1 (2026-10-20) -- four fixes after the twostorey_059 build

Approved by Rainer in chat, 2026-10-20: "Yes: amend the plan with all four fixes (Luftraum cuts overlapping floors, railings run to the wall, snap only widens, verifier checks the real outline). Tests first, rebuild twostorey_059, probe until 0 open edges besides the Austritt."

Evidence (11:31 go-baseline build of twostorey_059, void probe):
- 87 unguarded drop-edge samples (50 mm each): about 3.3 m along the inner stair edges, plus about 1 m at the Austritt (intended).
- Both Luftraum railings stand with floor on BOTH sides (18/27 and 11/11 samples), because the Flur polygon covers the Luftraum and keeps its floor.
- One Luftraum railing is 1212 of 1616 mm: `_lr_wand_nah` leaves out everything within 300 mm of ANY wall, including a wall the railing runs into end-on.
- Verifier R3_treppenloch failed on 4 surfaces:
  - the Treppenauge floor (intended since treppenloch-folgt-treppenform-v1; R3 still tests the stair polygon's bounding box);
  - two 60 mm strips the snap laid over the stair's outer edge, which is drawn 59 mm into the wall.

Fixes:
1. **Luftraum cuts overlapping floors.** Every Luftraum polygon on an upper floor is added (via `konvexe_teile`) to the pieces cut from ALL room slabs, like the drawn Treppenöffnung. Its own floor stays off, as before.
2. **Railings run to the wall.** `_lr_lauf` leaves a gap only where a wall runs ALONGSIDE the railing (within 20 degrees and 300 mm of the line, overlapping it). A wall the railing meets end-on no longer shortens it; the run ends at that wall's face. Pure function `gelaender_freie_stuecke(a, b, walls)`, tested.
3. **The snap only widens the hole.** `lochkanten_einrasten` / `lochEinrasten` move an edge only when it stops SHORT of the wall face (the hole grows to the face). An edge already inside the wall zone stays, so no slab is laid over the stair.
   - This revises this session's own test `test_kante_in_der_wand_rastet_auch_auf_die_flaeche` (renderer) and `in der Wand: ebenfalls auf die naechste Flaeche` (JS). The expectation flips to "stays". These tests were written today under this plan and are revised here, not silently.
4. **Verifier R3 checks the real outline.** `verify_render_blend.py` cuts the same opening the renderer cuts (a drawn Treppenöffnung, else the stair band split into its quads) instead of the bounding box. A floor face fails when its area OVER that opening exceeds 0.01 m2, measured by clipping, not by bounding boxes. The geometry functions are loaded from render-furnished-dollhouse.py via ast (one source), not copied.

Acceptance A1, on a rebuild of twostorey_059 (upper floor):
- the void probe finds 0 unguarded drop-edge samples except at the Austritt;
- no railing has floor on both sides;
- every railing reaches the wall it runs into (within 50 mm);
- verifier R3 passes;
- all test suites pass.

### A1 verification record (2026-10-20)

Tests:
- `treppenloch_a1.test.py`: 10 OK (all failed before the fix). One fixture of my own was corrected during the work: it had mixed the 11:31 Treppenauge face with an older stair's coordinates.
- `treppenloch_gezeichnet.test.py` 20 OK. Its snap test is revised as stated in A1, fix 3.
- `treppenloch_form.test.py` 14 OK, `render-furnished-dollhouse.test.py` 26 OK, `verify_render_blend.test.py` 11 OK, glasschiebetuer 7, stair_access 9, hausdaten 37 OK.
- `build-simplifier-render-plan.test.py`: the known, pre-existing door-hinge failure only.
- floorplan-simplifier: unittest 312 OK; all `static/*.test.mjs` OK. `loch-einrasten` is revised as stated in A1, fix 3; `waende-einrasten` is unchanged at 5 OK.
- Cache version: waende-einrasten.js -> 20261020-2.

Rebuild: `go.py twostorey_059` (real go-baseline, no upload) -> "fertig".
- The verifier passes every rule, including R2_R3_stairs_and_treppenloch; 2 styles verified, delivery-manifest written 11:57.

Void probe of interior-modern-upper-baseline.blend (11:54) against plan-modern.json:
- Unguarded drop-edge samples: 87 -> 2. Guarded: wall-1 71, loch-rail-2-right 43, Luftraum railing (edge 2) 62, Luftraum railing (edge 3) 31; Austritt open as intended: 19.
- No railing has floor on both sides (before: 18/27 and 11/11). The Luftraum railing on edge 3 is now 1616 of 1616 mm (before 1212).
- **The remaining 2 samples are NOT zero.** They lie at (6070..6120, 5024), on the stair edge `2-left` between the Luftraum's corner (x 5904) and the Austritt corner (x 6315). That edge is about 41 cm long. The probe's tolerances (120 mm to a railing, 150 mm to the Austritt) cover its ends; physically the whole stretch has no railing.
  - It runs beside the top steps: about 0-19 cm below the floor there, a step down, not a fall.
  - Cause in the data: `loch_railing_sides` is `['2-right']` only, and the Luftraum ends at x 5904 while the stair reaches 6315.
  - Closing it is a drawing decision: extend the Luftraum to the stair's end, or a separate railing piece. Turning on `2-left` would put a railing over the Luftraum, void on both sides.

Noticed, not caused by A1:
- The upper render is framed off-centre (the house small in a corner). The build used a hand camera "rescued" from the 11:31 .blend (`corrections/twostorey_059/kamera-innen-1.json`, 11:53:59; lens 82, location 24.97/-14.10/51.22). The camera was probably moved while that file was open in Blender. Deleting that json returns the automatic framing on the next build; left untouched.
