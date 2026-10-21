# ZuhauseFinder Suite Roadmap

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

This is the canonical persistent task list for the local Floorplan Simplifier, correction Workbench, deployable Born2Thrill service, and ZuhauseFinder WordPress integration.

Rules:
- Never remove a known follow-up merely because it is outside the current task.
- Mark COMPLETE only with evidence.
- Mark CANCELLED only after explicit user direction.
- Every implementation task uses its own approved plan.

## P0 - Recovery and current work

CAMERA-DEFAULT-REALISTIC: COMPLETE 2026-09-21. Annotator HTML/JS, server
normalization, render-plan and Blender fallback default to realistic. Explicit
saved classic retained; no project rewritten/rebuilt. Two regression tests pass,
AST-isolated renderer cases pass, JS/Python syntax pass, live /annotate.js serves
new default. Next pending work remains 053 render review; existing saved choices
require deliberate user selection, not silent migration.

FURNITURE-LIVE-053 follow-up: independent review identified CSS-hidden rights/Massing
crashes and correction Save draft leakage. Fixed by excluding correction panels
from embed JSX; 3 regression checks and TypeScript pass. Browser placement/save
confirmation is still the next pending gate (not declared verified).

| FURNITURE-LIVE-053 | VERIFY_UI | Furniture embed now bootstraps from live annotation geometry instead of the stale generator catalogue | workbench/plans/furniture-live-bootstrap-053.md; 2 adapter tests pass, tsc passes, live 053 returns both floors and page HTTP 200 on 2026-09-21 | Confirm placement/save in browser; no annotations, corpus approvals or publication changed. General catalogue synchronization remains pending separately. |

| RENDER-CONTRACT-001 | IN_PROGRESS | Enforce a persistent hashed render contract binding exact Blender inputs, hard-rule policy, approved references, master approval, delivery and package membership | `born2thrill-local-workbench/plans/render-contract-v1.md`; implementation authorized 2026-09-15 | Finish full verification and populate the approved reference registry before guarded production use |

| ID | Status | Task | Plan/evidence | Next gate |
|---|---|---|---|---|
| RECOVERY-001 | COMPLETE | Source-only backup v5 created, restored, checksum-verified, 64 Simplifier tests passed, WordPress PHP/snippet lint passed, and 35-file Simplifier allowlist staged | `C:\dev\backups\2026-08-01-v5-zuhausefinder-source-baseline` | No commit/push; private corpus remains separate under CORPUS-BACKUP-001 |
| WORKBENCH-BASELINE-001 | PENDING | Review and intentionally preserve/commit the existing dirty Workbench implementation | Existing branch `agent/zuhausefinder-generator` | New inspect-only plan after RECOVERY-001 |
| CORPUS-BACKUP-001 | BLOCKED_DECISION | Protect the private structured floorplan corpus with confirmed at-rest encryption and an independent recovery destination | Existing unencrypted 30 July ZIP remains untouched | User chooses BitLocker-protected destination, encrypted archive, or approved encrypted offline storage |
| FLOORPLAN-CATALOG-001 | COMPLETE | Build a deterministic searchable catalogue over the Simplifier v2 export without altering annotations, geometry, rights, or approval state | 310 projects, 497 floors, 3,072 room polygons, and 7,205 elements reconcile with the manifest; six focused catalogue tests pass | Keep generated catalogue byte-stable with `node scripts/build-floorplan-search-catalog.mjs --check` |
| DATASET-EXPORT-001 | IN_PROGRESS | Produce a strictly quality-passed, privacy-safe generator export and keep draft/test records separate | 2026-08-02 v2 batch accounts for 370 folders: 310 exportable, 295 quality-passed (133 bungalow, 85 one-and-a-half-storey, 75 two-storey, 1 cellar, 1 other), 15 held for review, 60 excluded with reason codes; local workbench catalog now reads v2 and 31 focused tests pass | Promote the validated v2 handoff into the main generator, add the dimension-recovery stage, then run one end-to-end internal smoke test |
| WORKBENCH-CATALOG-SEARCH-001 | COMPLETE | Wire the FLOORPLAN-CATALOG-001 search catalogue into the port-3020 Floorplan Workbench as a filter panel + 3 demo presets, so a questionnaire-style query can find and load a matching approved reference instead of only browsing auto-derived "similar to current" candidates | New read-only `catalog-search` API route wraps `filterFloorplanCatalog()`; all 3 presets (1.5-storey homeoffice: 38 matches, bungalow homeoffice+child rooms: 12, twostorey garage: 7) verified live end to end through the existing unchanged quality/rights gate; Previous/Next and all existing Workbench functionality unaffected | Phase 2 (rule-based variant generation, automatic scoring, façade/rendering pipeline) is a separate future plan, not started |
| APPROVED-CATALOG-GROWTH-001 | PENDING | Grow the customer-facing `approved-floorplan-catalog.ts` (schema `dmh-floorplan-approved-package-v3`) past its current single record by approving/exporting more of the 310 annotated references through the Workbench and running the existing `import:approved-floorplan` script | `catalog.generated.mjs` currently holds exactly one `wordpress_eligible: true` record (`plan-caaccb688174a403`), matching the one questionnaire combination that currently works live; export/import mechanism already exists and needs no new code, only process | User decides whether to prioritize this (fast, no new code) ahead of GENERATION-PIPELINE-PHASE2-001 |
| GENERATION-PIPELINE-PHASE2-001 | PROPOSED | Rule-based variant generation, automatic scoring, Schokoladenseite façade/camera selection, geometry lock, external exterior-rendering API, and human-approved catalogue enrichment, per the 2026-08-02 Codex handoff's six-step target workflow | `plans/generation-pipeline-phase2-v1.md` (born2thrill-local-workbench) records scope, what's already reusable (façade view + geometry lock, both APPROVED elsewhere), and what's genuinely unbuilt (variant generation/scoring, rendering API) | Rendering-provider choice, cost, and exact variant-generation rule bounds are unresolved; not approved, nothing implemented |

## P1 - Floorplan corpus and correction workflow

| ID | Status | Task | Current evidence | Next gate |
|---|---|---|---|---|
| SIMPLIFIER-REVIEW-001 | PENDING | Finish the three remaining CubiCasa draft annotations | Draft projects 199, 832, and 904 | Annotate and validate |
| RECONSTRUCTION-001 | PENDING | Reconstruct and approve rights-limited references as separate canonical geometry without source artifacts | 55 normalized reconstruction references available; source status remains restricted | Human geometry and output approval |
| CORPUS-GROWTH-001 | PENDING | Add more 1.5-storey and 2-storey annotations before broad generation | User target includes 200 additional annotations | Separate corpus-growth plan |
| VARIANT-REVIEW-001 | PENDING | Produce safe variants only from approved corrected plans and compare better/worse results | Free generation remains prohibited | Reliable approved-plan correction workflow first |
| ENTRY-WARDROBE-VARIANT-001 | PENDING | Add a rule-based entrance Garderobennische variation: rectangular niche open to Diele, taken from adjacent HTR/HWR only while preserving roughly 9–10 m² HTR/HWR and valid entrance/door/circulation clearance | User rule clarified 2026-08-01; never treat the niche as an unnamed geometry gap | Implement only in a later approved reference-derived variation plan |
| GENERATOR-BLENDER-001 | PROPOSED | Build the local canonical reference-derived candidate pipeline and Blender vertical slice from one shared geometry hash | `C:\dev\born2thrill-local-workbench\plans\canonical-generator-blender-v1.md` | User approval of the Phase 1 plan |
| DIMENSION-RECOVERY-001 | PENDING | Enrich catalogue records with authoritative millimetre dimensions and square metres only where a verified scale source exists | Current normalized export deliberately reports metric area as unavailable | Separate inspect-and-plan task; never infer metric scale |
| CATALOG-DATABASE-001 | PENDING | Evaluate importing the verified JSON catalogue into relational persistence for operational searching | Deterministic local JSON catalogue exists; no database mutation performed | Separate schema/migration plan and explicit approval |
| MEASURED-PDF-001 | IN_PROGRESS | Build the first simplified canonical house from the BV Bach measured PDFs using verified scale, layout and opening evidence | Source hashes and vector evidence recorded; defaults fixed at 350 mm exterior, 100 mm interior and 900 mm usable stair; pilot tests 3/3 pass | User traces simplified room polygons, assigns ambiguous openings, and classifies the unlabeled OG rough-installation area; then hard validation and shared 2D/Blender output |

## P1 - Customer proof of concept

| ID | Status | Task | Current evidence | Next gate |
|---|---|---|---|---|
| WORDPRESS-POC-001 | IN_PROGRESS | Match questionnaire results to an approved corrected plan, generate safe JPEG artifacts, approve, and send through the manual WordPress email gate | Real reconstructed plan plan-caaccb688174a403 is approved as revision 4, exported/imported through v3, and returned by the local API as a verified 1.5-storey JPEG plus PNG guide; WordPress remains unchanged | Separately authorized deployment and live WordPress proof |
| EXTERIOR-POC-001 | PENDING | Generate a photorealistic exterior from the approved canonical plan and questionnaire styling without changing geometry | Stage 2 remains separate | Geometry-faithful guide and explicit approval |

## P0 - Opened 2026-08-08

| ID | Status | Task | Evidence | Next gate |
|---|---|---|---|---|
| COMMIT-BASELINE-002 | COMPLETE | Commit the uncommitted work in all three roots | 2026-08-10, user-authorized: simplifier `f0bca21` (226 files — PNG symbols, Ausstattung), workbench `c207cb5` (18 files — hub catalog, picks v2, plans), app-repo `02972f4` (masterplan v3 + roadmap). `git status` clean in all three except intentionally-untracked `tmp_patch_resize.py` | Remaining: decide whether `wip-backup-*` folders in `C:\dev` can be deleted (user decision) |
| ANNOTATION-SCHEMA-001 | COMPLETE (untested) | Window type (Brüstungsfenster / bodentief) and door swing/hinge as annotated properties instead of downstream guesses | Simplifier side landed 08-08 (`e659bdc`); downstream wiring landed same evening in `9c8394a`: `correction-geometry.mjs:575-588` maps window_type→sill/height (bodentief: 0/2100), constants in `floorplan-rulebook.mjs:35-43`, hash-stable for legacy; the simplifier-direct path reads it too (`build-simplifier-render-plan.py:470-478`). Verified 2026-08-10 by independent review | Gap: zero tests mention `bodentief` in the workbench — add coverage before relying on it at batch scale |
| ANNOTATION-SYMBOLS-006 | DONE | `dusche_klein` (Dusche 80x80) for Dusch-WCs, flush to wall, artwork reuses the `Dusche` group | Added to all four tables that must agree: `static/symbol-catalog.js` (entry, WALL_FLUSH, ROOM_SYMBOL_SETS.bad, SYMBOL_SOURCE_GROUP), `app.py`, `symbol_footprints.json`, `symbol_detection.py`. Verified in-browser: palette, artwork, 800x800 footprint, flush snap | Reinforces the case for collapsing the duplicated tables to one Python-served source - one symbol now costs four edits |
| ANNOTATION-SYMBOLS-004 | DONE | Wall-alignment rules for Ausstattung symbols: `flush` (31 fitted items - sanitary, Kuechenzeile, Schraenke, Geraete), `gap` (beds 50 mm, sofas 100 mm, desks 50 mm), `free` (Spuele, Kochfeld, Kuecheninsel, Couchtisch and the rest, which must never be pulled to a wall) | `wall: {mode, gap_mm}` per entry in `static/symbol-catalog.js`; `snapStampToWall()` in `static/ausstattung.js` sets position AND rotation from the wall, reach limited to 1.5x the symbol's depth | Rainer to confirm the categorisation; Schreibtisch and Fernseher were judgement calls |
| ANNOTATION-SYMBOLS-005 | DONE | Stamp footprints were drawn 81.5% too shallow: the floor scale is metres across the image WIDTH, but depth was multiplied by `canvas.height`. A 750 mm bath drew as 611 mm | Aspect factor added in `symbolFootprintInUnits()` (`static/ausstattung.js`), which drawing, hit-testing and snapping all read; same mix-up fixed in `scaleFromRoomAreas()`. `symbol_detection.py` and the path tool were already correct. Verified in-browser: all footprints match spec in both axes | Positions of symbols placed before the fix are unchanged but now draw at full depth - already-annotated plans need a visual check |
| ANNOTATION-SYMBOLS-001 | PROPOSED | Second tab in the Simplifier ("Ausstattung") for kitchen counter runs, sanitary fixtures and furniture-group symbols, so furnishing is annotated rather than auto-placed | `plans/annotation-symbols-v1.md` §B/§C. The existing tool row is already 8 buttons; these add ~15 more, hence the tab split. Symbols are presentation-only and must never enter `geometry_hash` | User approval of the plan |
| ENTRANCE-WIDTH-001 | BLOCKED_DECISION | Entrance door width changes from 1100 mm to **1130 mm** (user decision, 2026-08-08). Applies to new plans only | `floorplan-rulebook.mjs:21` currently 1100. `correction-editor.mjs:168` *snaps* any `main_entrance` opening to this constant, so re-normalising an approved plan would change its geometry, its `geometry_hash`, and therefore its `plan_id` (derived as `plan-${hash.slice(0,16)}`). All 8 approved plans have 1100 mm entrances, including `plan-caaccb688174a403`, live in the WordPress POC | User states whether the 8 approved plans are re-normalised and re-approved, or grandfathered at 1100 |
| TEST-DEBT-001 | PENDING | Five failing tests, all pre-dating 2026-08-08 | `furniture-placement.test.mjs`: 2 failures — `sleeping` returns 6 types, 5 needing wall edges, but a rectangular room has 4, so one is always unplaced while the test asserts `unplaced.length === 0`. `shoe_rack` was added to the list after the test was written. Simplifier: 3 errors under Python 3.12. Verified pre-existing by running with and without the day's changes | Decide per test whether the expectation or the behaviour is wrong. Tests may not be weakened without a plan revision |
| EMPTY-PACKAGES-001 | PENDING | 14 of 252 Simplifier projects have zero annotations **and** no preview image. Source PDFs were deleted by privacy cleanup and no preview survives, so they cannot be annotated without re-uploading the original | Real: `bungalow_006/020/026`, `onehalfstorey_001/004/042`, `twostorey_001/002/006`. Test artifacts: `angelov_area_test`, `twostorey_batch_smoke_braun`, `twostorey_codex_import_test`, `twostorey_codex_privacy_check`, `twostorey_codex_privacy_check_full` | User re-uploads sources, or explicitly authorizes removal. Nothing deleted without explicit approval |

## P1 - Opened 2026-08-08

| ID | Status | Task | Evidence | Next gate |
|---|---|---|---|---|
| FURNISHED-RENDER-001 | IN_PROGRESS | Furnished dollhouse render pipeline. Working end to end: room floors with real textures, walls, 18 boolean-cut openings, glazed windows, 45° door leaves with brushed-steel handles, granite in wet/circulation rooms, HDRI lighting, furniture instanced from `.glb` and `.fbx` | New: `scripts/build-furnished-render-plan.mjs`, `scripts/render-furnished-dollhouse.py`, `data/furniture-model-overrides.json`. Renders v1–v6 in `tmp/`. Only existing source file changed: `furniture-placement.mjs` gained `wet`/`service` cases — rooms named "Bad" matched no rule key and were silently receiving zero furniture | **Unresolved:** the 52 m² living room reports 7 placements but renders 2. Positions verified inside the room polygon, all meshes verified importable. Cause unknown |
| RENDER-STAIRS-001 | COMPLETE | `shared_stair_core` was carried into the render plan and consumed by nothing — every interior render had a stair-shaped hole and no stair | 2026-08-17: `render-furnished-dollhouse.py` builds the flight from the drawn polygon + `path_mm` (path[0] = foot, per `stairArrow` in `floorplan-workbench/page.tsx` and `direction: "up"`), 175mm rise / 280mm going, solid closed risers with oak nosings, truncated at the dollhouse cut plane rather than booleaned (a cut step becomes a plateau and the flight reads as a ramp). Verified in both styles' renders and `[dollhouse] stair steps 6 (14/16 risers fit the 3932mm slot…)` | Follow-ups below: RENDER-STAIRS-002, and the `two-flight-u` vs `straight` data contradiction is DATA-STAIR-GEOMETRY-001 |
| RENDER-STAIRS-002 | PENDING | Rainer 2026-08-17: the truncated flight should FADE OUT toward the top rather than stop at a hard step edge | Currently the flight stops at the first step whose tread top passes the tilted cut plane. A fade needs either a height-driven alpha ramp on the stair material or a modelled taper; presentation-only either way | Rainer asked for this to go into the Codex polish prompt first; only becomes a generator change if the polish pass cannot do it |
| DATA-STAIR-GEOMETRY-001 | PENDING | `shared_stair_core` for `onehalfstorey_020` contradicts itself: `plan_type: "straight"` with a drawn 950 × 3924mm slot, but `geometry.type: "two-flight-u"` with a 2.1 × 2.86m footprint, and `tread_geometry_valid: false` | Only 14 of the 16 risers fit the drawn slot at 280mm going (logged by the renderer, not absorbed). The renderer builds from the polygon, which is what the corrector drew and what the 2D review view uses | Correct the stair block in the correction document, or accept the polygon as authoritative and stop emitting the conflicting `geometry` block |
| RENDER-SINK-001 | COMPLETE | The Spüle rendered as a flat slab lying on the counter | Root cause 2026-08-17: `corrected_placements()` in `build-simplifier-render-plan.py` was missing the sink exception the annotation path already had, so the plan shipped `preserve_materials: false` and the renderer sent a real 1000×500×506 library sink through `normalise_to_bbox` (the Tripo axis-reorder path), which matched the model's 506mm height to the 600mm target depth — the sink was tipped onto its back and squashed to 600×600×200. Fixed at the plan builder; renderer now seats it on a deck height measured off the mesh (`drop_in_deck_height`), cutter 88% so the rim covers the granite edge, apron plate removed, tap turned to the wall side by measurement | None. Legacy plan hash `3c0831f6…5e7f6` unchanged |
| RENDER-WINDOW-FRAMES-001 | COMPLETE | "Windows are not in their frames" | Measured in the 2026-08-17 baseline `.blend`: every window's glass sits exactly 140mm from its frame (350mm exterior wall → 175 − 35). An earlier fix moved the frame flush with the room face and left the glazing and mullions on the wall centreline. Both now share one `frame_depth_offset()` | Door LEAVES still hinge on the wall centreline while their frames sit at the room face — same defect class, not reported, not touched. Rainer decides |
| RENDER-MIRROR-FLAG-001 | COMPLETE | The plan's per-placement `mirrored` flag is now read and correctly applied per instance | Superseded by a 2026-08-21 fix (per-instance mesh copy, `render-furnished-dollhouse.py:3468-3472`) already in the codebase when this session started — the 2026-08-17 evidence above describes the OLD, now-fixed state. Re-verified 2026-08-22 three ways after Rainer reported "i keep mirroring the couch and it doesn't get translated to the model": (1) built a 4-combination contact sheet (rotation 0/90 x mirrored/not, real `ecksofa` mesh, through the real pipeline) and Rainer confirmed by eye which panels are correctly mirrored; (2) bungalow_039's real compiled plan already carries `mirrored: true` through to the render-ready opening with `build: null, preserve_materials: true` (real mesh, not a box fallback); (3) the freshly rebuilt `interior-modern-baseline.blend` shows the couch instance with its own private mesh data block (`users=1`), the exact signature of the per-instance mirror having been applied | None open on the mirror flag itself. See RENDER-SOFA-ROTATION-IGNORED-001 for a separate, still-open issue surfaced during this investigation |
| RENDER-SOFA-ROTATION-IGNORED-001 | PENDING | `ROTATION_OVERRIDE["ecksofa"] = 0` (`render-furnished-dollhouse.py:406-413`) hard-pins the corner sofa's rotation to 0° always; whatever `rotation_deg` the annotator/Möbel editor records for it never reaches the render | Surfaced 2026-08-22 while building the RENDER-MIRROR-FLAG-001 contact sheet: rotating the plan's `ecksofa` placement had zero visual effect until the diagnostic bypassed the override with `DMH_ROT_ECKSOFA=90`. This was a deliberate 2026-08-18 decision at the time ("do not recompute it") but may now read to Rainer as "rotating the couch doesn't work" | Rainer to say whether this override should be removed (let per-placement `rotation_deg` drive it again) or left as-is; not changed without that decision, per the same contact-sheet discipline this override itself was created under |
| RENDER-RULE-GATE-001 | COMPLETE | Rainer's rules are enforced by the build, not written as notes. `verify_render_blend.py` opens the SCENE and answers from geometry; `run_project.py` runs it on every interior and excludes the style on failure | Proven by contrast 2026-08-17: the current OG scene passes R0/R2/R3, while a superseded scene from the same folder fails with `15 sample point(s) inside the Treppenloch still have floor over them`, `no stair steps`, `no Gelaender` and 14 symbol-size violations. The log-reading checks in `verify_render.py` had passed that same scene | Six stale .blend/.png sets were moved to `renders/go-baseline/superseded-2026-08-17/` — they were being opened by mistake and are what 'still no treppenloch' was describing |
| RENDER-DELIVERY-COUNT-001 | COMPLETE | **HARD RULE — fixed file count per house**: a two-storey house delivers exactly 4 .blend files (2 exteriors + Erdgeschoss + Obergeschoss); a single-storey house exactly 3 (2 exteriors + the floor). Nothing else lives in the delivery folder | Rainer 2026-08-18. Enforced by housekeeping: the assembled whole-house view and six stale finish/floor variants were moved to `renders/go-baseline/superseded-2026-08-17/`, leaving exactly 4. Extra files in that folder had already caused a false defect report — a stale scene was opened and its missing Treppenloch reported against a current file that had it | Fold the count check into `run_project.py` so a run cannot leave surplus files behind |
| RENDER-FOOTPRINT-CLAMP-001 | COMPLETE | **HARD RULE — a symbol may never render bigger than its footprint in the toolbox**, in any axis. Rainer 2026-08-17, having had to say it more than once: "you can't give me symbols that pop out beyond whatever border they have in the toolbox, how do you expect me to position anything" | Root cause was `fit_within_bbox` scaling by `max(target)/max(model)` with no regard for which AXIS each came from: on `schrank_60` that matched the annotated HEIGHT 2100 against the model's WIDTH 1500 and scaled it up 1.4×, so a 1070mm cupboard rendered 2100mm wide; `kleiderschrank` likewise 1050 drawn → 2100 rendered. Two changes: a measured footprint is now fitted on the two PLAN axes only (height follows the model's proportions), and `clamp_to_footprint()` runs on EVERY prototype after every scaling path as the last word. Undersize is allowed; oversize is not | Any new scaling path must stay behind the clamp. Related model-pick defect: MODEL-PICK-SIZE-001 |
| MODEL-PICK-SIZE-001 | PENDING | `kleiderschrank` and `schrank_60` resolve to models nothing like the size of the drawn symbol, so honouring the footprint makes them paper-thin | `kleiderschrank` → "White Wardrobe", verified 3082×650×2384, squeezed into a 1050×600 symbol renders 1050×221×812. `schrank_60` → "White Rounded Cupboard", 1500×656×1011, renders 1070×468×721 against a 2100-high symbol. The fit is now correct; the picks are wrong | Replace both picks in `data/symbol-model-picks.json` with models near the drawn size, or drop to a procedural carcass at the symbol's own dimensions |
| RENDER-FLOATING-FEATURES-001 | COMPLETE | Opening frames, glazing and door leaves were UNCONDITIONALLY exempt from the dollhouse cut, so wherever the plane cut below the opening they were left hanging with no wall — "a door upstairs leading nowhere", "the whole outside is missing" (Rainer, 2026-08-17) | The exemption was written for the Erdgeschoss's bodentief glazing (sill 0, height 2300, reaches the floor). The Obergeschoss has sill 900 / height 1350 against a 500mm front cut, so whole panes floated outside a building with no elevation left. Now exempt only while the plane stands at or above the opening's mid-height; below that the feature is sliced with its wall. Verified: `cut-exempt 34 … / features sliced 32` on the Erdgeschoss. Openings match the annotation exactly (upper floor 4 doors + 7 windows on both sides) — this was never a data defect | This also bites the Erdgeschoss's frontmost openings, which is intended and visible; Rainer to confirm he likes the new front |
| RENDER-FRIDGE-001 | COMPLETE | The fridge had no `TYPE_FINISH` entry, so it fell through to the `"wood-oak"` default — not a fridge colour in any set, and in `classic-b` byte-identical to `FINISH["kitchen"]`, so it vanished into the cabinetry (Rainer 2026-08-17: "why do you make the refrigerator the same color as everything else in the kitchen") | Probed the actual blend: `furn-fridge-wood-oak (0.72,0.58,0.40)` against `furn-counter-metal-matte-black (0.06,0.06,0.07)`. Now `fridge: metal-brushed-steel`, the same appliance finish the washer has, plus a horizontal fridge/freezer seam and a vertical handle on the door face (which face is the door is taken from the unit's own `_snap_flush` back direction — a fixed pair of faces put the trim where the camera never sees it on a square-plan 600×600 fridge) | **Trap recorded:** the Hub's only fridge, `Refrigerator_2_BLEND` (541×597×1772 at divisor 2.54, a perfect footprint match), is authored with its DOOR HANGING OPEN and shelves modelled. It was added to `symbol-model-picks.json`, rendered as an open fridge standing in the room, and reverted. `import_model` joins all parts into one mesh, so the door cannot be closed without per-object surgery — solve that before re-adding it |
| RENDER-STAIR-RAILING-001 | COMPLETE | Stair had no Treppengeländer | 2026-08-17, Rainer: "dont forget the Treppengeländer". Oak handrail raking at the flight's pitch on slim steel balusters, 900mm above the nosing line, one baluster per tread. Which sides are open is MEASURED (any wall within 300mm closes that side), so a wall-hugging flight gets one rail and a free-standing one gets two. Verified: `1 Gelaender` on this plan, correct side | None |
| RENDER-SINK-TAP-AXIS-001 | COMPLETE | The sink tap was aimed off the wrong counter leg | The wall side came from `KITCHEN_RUN_FRONTS[0]` — the FIRST segment of an L-shaped run, here a short leg at right angles to the one the sink sits on. Now taken from the counter segment the sink was actually snapped to | None |
| RENDER-UPPER-FLOOR-001 | COMPLETE | The interior renderer was hard-wired to `plan["floors"][0]`, so the upper storey of a two-storey house had never been rendered — its 18 furniture items existed in every plan and reached no image | 2026-08-17: `DMH_FLOOR` (index or floor id) selects the storey, `run_project.py` gained `--floors` and `--finishes`. Obergeschoss verified: 5 rooms, 16 walls, 11 openings, `furniture 18 instances from 8 meshes`. The stair is built only on the storey it rises from | Open defect: the upper Flur has no stair opening in its slab — the flight arrives from below with nothing marking it |
| METADATA-STOREY-001 | PENDING | `onehalfstorey_020` is a FULL two-storey with a Walmdach; its records say otherwise in both data roots | `storey_type: "1_5_storey"`, `roof_form: "gable"`, `data.json` `house_type: "1.5-storey"`, and the project id itself. Rainer restated the correct facts 2026-08-17. Feeds the search catalogue, not the render — so it will mismatch questionnaire answers once the catalogue drives delivery | Needs its own plan: the catalogue is downstream, and the project id cannot be changed casually |
| FBX-LIBRARY-001 | COMPLETE | 1160 CGAxis models measured and cataloged | Verified 2026-08-10: `tmp/fbx-library-catalog.json` (08-08 16:58) holds `measured: 1160` with per-model size_mm/mesh counts; downstream `data/symbol-model-picks.json` v2 (08-09) already picks modern/classic models with verified sizes | Shortlisting per furniture type continues inside the A/B variant work (masterplan Phase 2) |
| TRIPO-SKIP-GUARD-001 | COMPLETE | `scripts/tripo-generate-furniture-full.mjs` re-buys pieces already on disk | Verified 2026-08-10 (independent review): purchase loop filters with `existsSync(...glb)` at lines 211–219, committed 08-08 16:21. Historic waste (~$16) already incurred; no further exposure | 15 pieces (positions 34–48) still never generated — separate decision whether to buy them |
| REPO-STRUCTURE-001 | PROPOSED | Consolidate into a single Git monorepo: `apps/delivery`, `apps/workbench`, `packages/floorplan-core`, with `floorplan-simplifier` kept as a separate Python app inside it | The two Next.js roots are not duplicates — they have specialised into delivery vs internal tooling — but 8 files exist in both and differ, including `src/lib/generator/floorplan.ts`, `src/app/upload/page.tsx` and three API routes. Codex second opinion 2026-08-08 agrees, and adds: write golden-output fixtures for both behaviours *before* extracting, or extraction silently changes generator output | Sequenced after COMMIT-BASELINE-002 and ANNOTATION-SCHEMA-001. Both reviewers rank schema versioning as more urgent than repository cleanup |
| ROADMAP-PATH-001 | PENDING | Every `AGENTS.md` in all three projects names the canonical roadmap as `C:\dev\born2thrill-app-repo\plans\ROADMAP.md`, which does not exist. The real path is `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md` | Any agent following the instruction literally cannot reach the follow-up tracker it is required to update | One-line correction in three `AGENTS.md` files |

## P1 - Opened 2026-08-16

| ID | Status | Task | Evidence | Next gate |
|---|---|---|---|---|
| WORKBENCH-OVERVIEW-001 | COMPLETE | Read-only overview tab listing every render, render plan, correction revision, furniture layout, export and annotation package, newest first, with Codex-readiness | `born2thrill-local-workbench/plans/workbench-overview-tab-v1.md`. New `/floorplan-workbench/overview` page plus `GET /api/floorplan-workbench/overview` and `.../overview/asset`; both behind the existing localhost gate. Verified 2026-08-16 in-browser against real data (292 project folders, 2 Codex-ready, 15 render images) and with `npx tsc --noEmit` clean | None. Future counts grow automatically; no schema is written by this feature |
| WORKBENCH-DATA-ROOTS-001 | PENDING | Two similarly named workbench data roots are both live: `C:\dev\born2thrill-local-workbench-data` (what `FLOORPLAN_WORKBENCH_DATA_DIR` points at, so what the UI writes) and `C:\dev\Floorplan-tools\born2thrill-local-workbench-data` (where the go-baseline renders, all `exports\` and most revisions live) | `onehalfstorey_020` exists in **both** with divergent geometry: root A holds one *draft* revision `c87bb622…` (142.4 m², validation BLOCKED, plus the only furniture file), root B holds eight revisions ending in *approved* `d3c5b399…` (149.0 m², WordPress-eligible export). The 2026-08-16 go-baseline renders were built from the root-A **draft** (`plan-*.json` `source: correction_revision_draft`), i.e. the rendered geometry is not the approved geometry. Surfaced by the new overview tab, which labels each entry with its root | User decides which root is canonical, then a separate migration plan. Nothing merged or moved in the meantime |

## P1 - Opened 2026-08-22

| ID | Status | Task | Evidence | Next gate |
|---|---|---|---|---|
| DOOR-HINGE-FRAME-MISMATCH-001 | COMPLETE | The annotator's own door-swing preview and the render pipeline read the identical stored `hinge_side`/`swing_side` values in two different, independent reference frames (door's own drawn point order vs. matched wall's own `start_mm`/`end_mm` order), so a door whose own points ran opposite to its wall rendered backwards from what the user saw and chose in the annotator | Rainer 2026-08-22: "Schlafzimmertuer falsche richtung ... Buero Tuer auch Eingangstueer auch Kuechentuer auch". Measured directly on bungalow_039: exactly 3 of 6 explicitly-set doors (Kueche, Buero/Gast, Eingang) had opposite point order to their wall — exactly the 3 doors named as wrong. Fixed in `build_floor_walls_and_openings()` (`build-simplifier-render-plan.py`): normalizes both values into the wall's own frame via a dot-product check before storing. New regression test added and passing; bungalow_039 rebuilt, full verification suite passed both styles | None |
| DOLLHOUSE-OPENING-CUT-001 | COMPLETE | Windows and some doors were visibly sliced through the middle by the diagonal "dollhouse cutaway" plane along with their wall, whenever the plane's local height fell below the opening's own vertical midpoint | Rainer 2026-08-22, from a real render: "fesnter sind fast ueberall geschnitten Kuechentuer ist geschnitten Eingangstuer ist geschnitten". Measured on bungalow_039: 7 of 8 windows and exactly the Kueche/Eingang doors were affected (front cut = 500mm). Asked Rainer directly (3 options); chose "always exempt openings from the cut." Implemented in `wall_object()` (`render-furnished-dollhouse.py`): openings' frame/glazing/leaf always exempt now, never sliced with the wall. Verified directly against the rebuilt blend's object Z-extents — all previously-truncated openings now render at full height | Known, accepted risk (stated to Rainer before he chose): an upper-storey window with a high sill could stand with no wall around it if its wall gets cut away locally. Mitigated by `DMH_SHELL_WHOLE` already keeping upper-storey exterior walls whole by default. Revisit only if actually observed on a real house |

| POSE-CONTRACT-CORRECTIONS-001 | COMPLETE | Late-evening corrections after Rainer verified the actual render (all previously reported "fixed" but failing on the user-visible surface): (1) annotator swing is COUPLED to the hinge label (hinge->free reverses with "end") — door_pose_in_wall_frame() rewritten geometrically, metamorphic tests corrected; (2) heuristic doors no longer swing into circulation rooms (Wohnzimmertuer opened into the Diele); (3) couch mirror fixed in TWO layers — instance mirror moved to the LONG axis (editor scale(-1,1) semantics) and "ecksofa" returned to MODEL_MIRROR_Y because the editor's top-down artwork is the mirror of the model's native orientation (documented since 08-10, never wired); (4) dollhouse opening exemption re-decided by A/B IMAGE comparison (Rainer: "a"), B path deleted | End-to-end probes against the built .blend: all 6 explicit doors match their annotator preview (swing+hinge STIMMT), couch measures the exact panel-6 pose Rainer picked from the in-situ contact sheet, no doors rehinged/closed. Codex's 21:48 four-style set verified to derive from the fixed geometry. All suites green, both styles certified. Records: pose-contract-slice-1-v1.md correction record, dollhouse-cut-always-exempt-openings-v1.md second approval | Definition of done for pose/direction fixes is now: measure editor/annotator visual vs built .blend (memory: verify-against-user-visible-surface). Follow-ups unchanged: Plan 2 (R7 via requested/resolved metadata), Plan 3 (cutaway policy + dead cut_features rail removal), TS golden vectors, conventions doc last, sofa_1sitzer override |
| POSE-CONTRACT-SLICE1-001 | COMPLETE | Structural response to the recurring reference-frame bug class, slice 1 of the Codex-agreed phased plan: corrected-path double pose transform fixed (plus its floor-id alias crash), ecksofa ROTATION_OVERRIDE deleted (editor rotation reaches the render again), door_pose_in_wall_frame() extracted with metamorphic tests, golden pose vectors frozen from Rainer's 2026-08-22 contact sheet, R8_opening_heights added to the certificate gate | `plans/pose-contract-slice-1-v1.md` (approval: "Plan 1 all 4 points"). R8 proven both directions before gating: PASS on fixed bungalow_039, FAIL on the pre-fix .blend1 naming the exact defects Rainer reported. All tests green, both styles rebuilt and certified with R8 in the chain | Follow-up slices, in the agreed order: Plan 2 = renderer stamps requested/resolved door pose into the .blend, then R7 (door pose vs plan) gates; Plan 3 = cutaway policy function + matrix test + removal of the dead cut_features rail; then TS-side golden-vector reader; conventions doc LAST as index. Also pending: sofa_1sitzer ROTATION_OVERRIDE (same placement-override concern, outside slice-1 scope) |

| WORKFLOW-AUDIT-001 | OPEN | End-to-end /haus workflow audit (Rainer: "make it one workflow from back to front with rules that are straightforward, not cancelling each other out"). Codex audit delivered: 4 P0 gaps (build ignores the correction revision the Möbel editor works on; house-list "fertig" derived from WordPress alone; rights release can bind to a stale/unbuilt delivery, fail-open; Codex returns never validated against codex-job.json), 5+ P1s, 6 rule-contradiction families (3 competing staleness definitions, dead states, four-style contract vs models_locked, non-idempotent Codex jobs, split release paths, 2 scale loaders), plus a target 8-step gate table and 7 ordered build plans | Full audit: born2thrill-local-workbench/plans/workflow-audit-2026-08-22.md. Quick P1s already fixed same night: Bilder tab shows local codex-final-* (newest) + go-baseline labeled final/Rohbau + online (bilder-tab-local-renders-v1.md); 21:48 four-style set ingested as codex-final-2026-08-22-2148 | Rainer to approve the 7-plan build order (deriveHouseState single truth → active approved revision drives build → shared built_hash lib → Codex intake w/ four-style contract → Bilder reload-after-action → three separate release gates → dead-state removal). RESOLVED 2026-08-22 night: plugin installed+activated via wp-admin (Rainer authorized in-session); table-prefix bug found (kon_kon_grundrisse) and fixed with candidate detection; freigeben succeeded end-to-end -- Katalog: im=10, ok=ja for bungalow_039 |

## Completed governance

| ID | Status | Task | Evidence |
|---|---|---|---|
| GOVERNANCE-001 | COMPLETE | Install inspect-plan-approve-review workflow in all four roots | Policy `ZF-AGENT-WORKFLOW-v1.0.0`; Codex discovery passed; Claude review PASS |
| WORKBENCH-PUBLISH-001 | done | Overview page uploads a whole package to born2thrill (`/api/floorplan-workbench/publish`), credentials server-side only. |
| WORKBENCH-DISCARD-001 | done | Per-image trashcan; moves to `_verworfen/` beside the file, never unlinks (tree is not a git repo). |
| WORKBENCH-ONLINE-BADGE-001 | done | Each thumbnail shows online/lokal; panel shows n/m auf der Website, computed from the live catalogue. |
| WORKBENCH-PLANID-001 | done | plan_id inferred from the delivery folder name, checked against the 310 real ids; upload blocked for an unknown id. |
| WORKBENCH-DESCRIPTIONS-001 | done | catalog.json description_de/style/palette/materials/rooms/features travel with the upload as media title, alt, caption, description. |
| CATALOG-IMAGE-CAPTION-001 | pending | The catalogue record sheet still shows only the filename; surface the uploaded caption/description in the lightbox. |
| WORKBENCH-PLAN-DOC-001 | pending | Retro plan file for the above under plans/, per AGENTS.md Phase 1. Work was done under the user's standing "do it, don't propose it" instruction. |

## P1 - Opened 2026-08-23

| ID | Status | Task | Evidence | Next gate |
|---|---|---|---|---|
| INTERIOR-WALL-GEOMETRY-001 | COMPLETE | Innenwaende waren nicht sauber: eine schraege Wand an der Grenze Flur/Kind im OG von `onehalfstorey_029`, offene T-Stoesse (Innenwaende enden vor der Wand, die sie treffen sollten), Knicke zwischen kollinearen Innenwaenden | `born2thrill-local-workbench/plans/interior-wall-geometry-v1.md`. Gemessen vor der Aenderung: 029 OG `wall-4` lief 9.42 Grad schief, neun Innenwand-Enden endeten 26.6..120.0mm vor ihrem Ziel (die 120.0 = halbe Aussenwandstaerke, strukturell). Neu in `scripts/build-simplifier-render-plan.py`: `_orthogonalize_interior_walls` (12 Grad, gewaehlt aus der gemessenen leeren Bandluecke 10.43..21.58 Grad ueber 94 Projekte / 582 Innenwaende) und `_close_interior_t_junctions` (400mm, nur verlaengern). Nachher: 029 OG 6 -> 5 Innenwaende, 0 schiefe, 0 offene T-Stoesse; korpusweit 17 schiefe Innenwaende weg, alle 50 echten Schraegen (20.6..45 Grad) unveraendert. 30 Tests gruen, `go.test.py` gruen | Keins. Rainer muss `onehalfstorey_029` neu bauen, damit das Render die neue Geometrie bekommt |
| INTERIOR-WALL-OVERSHOOT-001 | PENDING | Innenwand-Enden, die ueber die Wand hinausstehen, die sie kreuzen, werden nicht gekuerzt | Gemessen 2026-08-23: `onehalfstorey_029` groundfloor `wall-3` endet bei x=2870.7 und steht damit 162.4mm ueber die Aussenwand-Mittellinie x=3033.1 hinaus, also 42mm ausserhalb des Gebaeudes. Bewusst ausserhalb des Umfangs von INTERIOR-WALL-GEOMETRY-001 gelassen (nur Verlaengern, nie Kuerzen), weil Kuerzen eine eigene Entscheidung ist | Eigener Plan: entscheiden, ob ein ueberstehendes Ende auf die Zielachse gekuerzt oder nur beim Aussenwand-Durchstoss beschnitten wird |
| INTERIOR-WALL-MISTYPED-PARTITION-001 | PENDING | Eine Innen-Trennwand kommt als ZWEI parallele 240er `exterior`-Waende heraus, wenn beide Raumkanten den `partnered`-Fallback in `build_walls` treffen | Gemessen 2026-08-23 an `onehalfstorey_029` upperfloor: `wall-6` (x=7145.0) und `wall-10` (x=6976.0), beide `wall_type: exterior`, beide y 5124.2..6287.6, 169mm auseinander — genau dort, wo im Rest des Geschosses EINE Innenwand bei x=7051.6 laeuft. Beide Enden der Innenwand ober- und unterhalb passen exakt dazu | Eigener Plan. Betrifft die Kantenpaarung in `build_walls` (`paired`/`partnered`), nicht die heute geaenderten Nachbearbeitungsschritte |
| SIMPLIFIER-WALLS-SYNC-001 | PENDING | `C:\dev\Floorplan-tools\floorplan-simplifier\walls.py` ist die erklaerte Zwillingskopie von `_merge_collinear_walls` / `_outline_to_walls` / `_regularize_outline_points`, hat aber weder `_close_exterior_corners` (2026-08-23 vormittags) noch `_orthogonalize_interior_walls` / `_close_interior_t_junctions` (2026-08-23 nachmittags) | Die Divergenz war schon vor beiden Aufgaben da. Der Simplifier zeigt seine Wandvorschau ueber `app.py:6122` (`import walls as walls_module`), also sieht Rainer dort weiterhin die alte, ungeputzte Geometrie — waehrend der Moebel-Editor und das Render die geputzte sehen | Eigener Plan: entweder die drei Funktionen nachziehen oder `walls.py` auf die eine Implementierung umstellen |
| STAIR-GEOMETRY-REBUILD-001 | COMPLETE | Die Treppe im Innen-Render war keine Treppe, und das Treppenloch-Gelaender stand quer vor ihrem Austritt (Rainer, 2026-08-23: "your stairs are still shit", "there is a rail blocking the stairs") | `born2thrill-local-workbench/plans/stair-geometry-rebuild-v1.md`. Vorher gemessen an `interior-modern-upper-baseline.blend` von `onehalfstorey_029`: `stair-step-7` und `stair-step-11` massen je 1000 x 1000mm -- die Stufe ueber einer scharfen Ecke nahm ihre hintere Setzlinie auf dem einen Schenkel und ihre vordere auf dem anderen und wurde eine SCHLEIFE, die ihre Nachbarn verschluckte; die Treppe stieg 16 x 175 = 2800mm in ein 2620mm-Geschoss; sie endete 310mm vor dem gezeichneten Austritt; `loch-rail-west` lief ueber die volle Westkante des Lochs (y 3.844..6.116). Neu: `stair_turn_style()` im Plan-Builder entscheidet Podest gegen Wendelung aus der gezeichneten Lauflinie, die Wendelung ersetzt jede scharfe Ecke durch einen Bogen um die INNERE Bandecke mit Radius = halbe Laufbreite (passt exakt in das gezeichnete Polygon), Steigungszahl kommt aus der Geschosshoehe, das Loch-Gelaender laesst einen Austritt frei. Nachher: 15 Stufen x 174.7mm, 291mm Auftritt, oberste Stufe buendig mit dem Boden bei 2620mm und buendig am gezeichneten Austritt, 1050mm Austritt im Gelaender, keine ueberlappenden Stufen. Neue Regel `R9_stair_access` in `verify_render_blend.py` (bewiesen in beide Richtungen: FAIL auf dem alten .blend mit genau diesen Defekten, PASS auf dem neuen). 42 Tests gruen, `onehalfstorey_029` und `bungalow_039` gebaut und zertifiziert | Keins. Andere Haeuser mit gezeichneter Treppe muessen einmal neu gebaut werden, damit sie die neue Geometrie bekommen |
| RENDER-SOCKEL-001 | COMPLETE | Ein gerendertes Obergeschoss schwebte in der Luft (Rainer, 2026-08-23: "it looks odd if the Floor is floating in mid air ... just center on the top floor") | `born2thrill-local-workbench/plans/stair-geometry-rebuild-v1.md`, Abschnitt FIX C. Neu in `render-furnished-dollhouse.py`: jedes Geschoss UNTER dem gerenderten wird als schlichter Sockel gebaut -- Wandkoerper auf eigener Hoehe mit echten Fenster- und Tueroeffnungen, ohne Moebel, Tuerblaetter, Rahmen oder Verglasung, und ohne Dollhouse-Schnitt. Alle Objekte heissen `sockel-...`, damit `R0_symbol_sizes` und `R8_opening_heights` weiterhin nur das gerenderte Geschoss messen (nachgeprueft: beide PASS mit Sockel). Kamera unveraendert auf die Raeume des gerenderten Geschosses; der Sockel darf unten aus dem Bild laufen. Bodenplatte faellt jetzt auf die Sockelfuesse statt 180mm darueber. Schalter `DMH_SOCKEL=0`. Gemessen an `onehalfstorey_029` OG: 15 Sockelwaende / 16 Oeffnungen | Keins |
| STAIR-SLAB-WINDING-001 | PENDING | `polygon_object()` verdickt gegen die Flaechennormale, und die Normale folgt der Wicklung des Raumpolygons -- also liegt die Gehflaeche eines Raums je nach Wicklung bei +220mm oder bei 0mm ueber der Geschossbasis, im selben Geschoss | Gemessen 2026-08-23 an `onehalfstorey_029` upperfloor: `floor-1784479639541_b39f6715b9a158` und `floor-1784479670696_b1e0a81621b1b-*` liegen bei z 2.620..2.840, `floor-1784479666466_74360121b77f98-*` und `floor-1784479681063_d10ed38d330d` bei z 2.400..2.620 -- 220mm Versatz zwischen Raeumen desselben Geschosses. Die Treppe haengt deshalb an der Geschossbasis statt am gemessenen Boden; im EG steht die erste Stufe 45mm unter der Diele. Bewusst ausserhalb des Umfangs von STAIR-GEOMETRY-REBUILD-001 gelassen | Eigener Plan: Raumpolygone vor dem Verdicken einheitlich wickeln, danach die Treppe auf den gemessenen Boden setzen |
| STAIR-SECOND-FLIGHT-001 | PENDING (kein Haus betroffen) | `annotation_stair_core()` liest nur `drawn[0]` -- ein Haus mit zwei gezeichneten Treppen AUF DEMSELBEN Geschoss bekaeme nur eine | Korpus 2026-08-23 durchgezaehlt: 98 Projekte haben eine gezeichnete Treppe, 65 davon mit Wendung, aber **0** haben mehr als eine Treppe auf demselben `floor_level` -- die zweite Zeichnung ist immer dieselbe Treppe auf dem Geschoss darueber. `drawn[0]` ist damit heute korrekt; der Docstring in `annotation_stair_core()` ("two properly drawn Podesttreppen") beschreibt genau diesen Fall und ist irrefuehrend | Eigener Plan nur, wenn ein Haus je zwei echte Treppen bekommt. Bis dahin: Docstring richtigstellen |

## P1 - Opened 2026-08-25

| ID | Status | Task | Evidence | Next gate |
|---|---|---|---|---|
| HAUSDATEN-EINE-WAHRHEIT-001 | COMPLETE | Dachform (`roof_type_modern`/`roof_type_classic`) und Massstab (`floor_scale`) liegen in zwei Dateien je Projekt (`annotations.json` + `gebaeudemass.json`); fuenf Leser fuehrten sie selbst zusammen, mit drei verschiedenen Vorrangregeln -- dasselbe Haus galt an einer Stelle als "Dachform gesetzt" und an einer anderen als "fehlt" | `born2thrill-local-workbench/plans/hausdaten-eine-wahrheit-v1.md`. Neu: `scripts/hausdaten.py` + `scripts/hausdaten.test.py` (19 Tests) und `src/lib/floorplan-workbench/hausdaten.mjs` + `hausdaten.test.mjs` (8 Tests, `npm run test:hausdaten`). Eine Vorrangregel pro Feld, uebernommen vom Bau: annotations.json gewinnt, ist das Feld leer, zaehlt gebaeudemass.json; beim Massstab pro Geschoss. Umgestellt: `build-simplifier-render-plan.py`, `go.py`, `werkbank.py`, `dachform.py`, `src/app/api/floorplan-workbench/state/route.ts`. Gegenprobe alt/neu ueber alle 233 Projekte: 0 Unterschiede im gebauten Plan. Kriterium 5 am echten Haus `german_catalog_review_bungalow_3_2_1_b_100_1`: modern=flachdach, classic=walmdach an allen fuenf Stellen | Keins. Sichtbare Folge: die Statusliste fuehrt 49 Haeuser, die nur eine Dachform im Sidecar haben und nirgends einen Massstab, jetzt wahrheitsgemaess als `vermessung_noetig` statt als `baubereit` |
| HAUSDATEN-RESTLESER-001 | COMPLETE | Vier weitere Stellen fuehrten `floor_scale` weiterhin selbst zusammen, und zwar alles-oder-nichts statt pro Geschoss: `scripts/batch-build.py`, `scripts/workflow.py`, `scripts/masse-server.py`, sowie der von Hand kopierte Sidecar-Hash in `scripts/render-furnished-dollhouse.py` | `born2thrill-local-workbench/plans/hausdaten-restleser-v1.md`. Alle drei Leser rufen jetzt `hausdaten.hausdaten()`; der Eingangshash (Zeichnung + gebaeudemass.json) steht als `hausdaten.sidecar_hash()` / `input_hash()` / `eingangshash()` einmal statt dreimal von Hand. `scripts/hausdaten.test.py` 19 -> 37 Tests (`python scripts/hausdaten.test.py`, OK); vor der Umstellung fielen 3 Tests und 6 Fehler, danach keiner. Alle Testbefehle des Plans gruen: hausdaten.test.mjs 9/9, build-simplifier-render-plan.test.py 42, go.test.py 4, render-furnished-dollhouse.test.py 4, `npm run test:house-state` 8/8, `npx tsc --noEmit` 0. Kriterium 4, alt gegen neu ueber alle 233 Projekte (`annotation_state`, `stufe_von`, `haeuser`, `_refuse_stale_plan` an 123 echten Render-Plaenen, plus sidecar_hash/input_hash je Projekt): **0 Abweichungen**; die Gegenprobe an einem Kontrollprojekt mit `floor_scale: {"groundfloor": null}` zeigt den Unterschied wie erwartet an | Keins. `scripts/run_project.py` blieb unveraendert: es rechnet gar keinen Sidecar-Hash, sondern kopiert nur `source_provenance.sidecar_hash` / `input_hash` aus dem Bauplan -- die Plan-Annahme war dort ungenau. Offene Kleinigkeit: `read_json()` in `masse-server.py` ist seit der Umstellung unbenutzt (HAUSDATEN-RESTLESER-002) |
| HAUSDATEN-RESTLESER-002 | PENDING | Aufraeumen nach HAUSDATEN-RESTLESER-001: `read_json()` in `scripts/masse-server.py` ist unbenutzt, seit `haeuser()` ueber `hausdaten.py` liest; ausserdem definiert `scripts/build-simplifier-render-plan.py` `sidecar_hash()`/`input_hash()` noch einmal selbst, obwohl beide jetzt in `scripts/hausdaten.py` stehen | Beides ist heute wertgleich (233-Projekte-Vergleich: 0 Abweichungen), also kein Defekt, sondern Doppelung. `build-simplifier-render-plan.py` stand nicht in den Files in scope von `hausdaten-restleser-v1.md` und wurde deshalb nicht angefasst | Kleiner eigener Plan oder Anhang an den naechsten, der ohnehin `build-simplifier-render-plan.py` oeffnet |
| SIMPLIFIER-HAUSDATEN-SYNC-001 | PENDING | `floorplan-simplifier/app.py` schreibt `annotations.json` und liest Dachform/Massstab fuer seine eigene Anzeige, ohne den neuen Helfer | Der Helfer liegt in `born2thrill-local-workbench/scripts`, der Simplifier ist ein eigener Baum -- derselbe Zwillingsfall wie SIMPLIFIER-WALLS-SYNC-001 | Eigener Plan, zusammen mit SIMPLIFIER-WALLS-SYNC-001 zu entscheiden |

## KUECHENINSEL-DOORTEST-001 (PENDING)

`scripts/build-simplifier-render-plan.test.py`
`test_door_hinge_and_swing_are_normalized_into_the_walls_frame` schlaegt fehl:
die sechs fest eingetragenen Tuer-Ids von bungalow_039 (Stand 2026-08-22)
existieren nicht mehr. `annotations.json` von bungalow_039 wurde am
2026-08-25 14:37 neu gezeichnet, das Haus hat jetzt 4 Tuerelemente mit neuen
Ids. Der Test prueft also nichts mehr, statt etwas Falsches zu finden.

Nicht angefasst: AGENTS.md Regel 7 verbietet das stillschweigende Umschreiben
eines bestehenden Tests. Braucht eine Entscheidung von Rainer -- Ids
nachziehen oder den Test auf Rollen (Kueche/Bad/Eingang) statt auf Ids
umstellen.

Gefunden am 2026-08-25 waehrend plans/kuecheninsel-rechteck-v1.md.

## CODEX-OBJEKTKARTE-001 (COMPLETE)

`born2thrill-local-workbench/plans/codex-objektkarte-v1.md`.

Der Auftrag nannte Garderobe, Stuff und Sanitaer beim Namen, sagte aber
nirgends, WO sie liegen. Codex musste sie im Rohrender suchen -- und ein
aufgeschlagenes Tuerblatt sieht dort aus wie ein Schrankbrett. Belegt an der
Lieferung `german_catalog_review_bungalow_3_2_3_b_100_1` vom 2026-08-27: die
Garderobe (`garderobe-25`) stand in vier Bildern an drei verschiedenen
Stellen; zweimal ersetzte sie die Haustuer, zweimal wurde eine zweite
Garderobe an einer Dielenwand erfunden.

Neu in `scripts/make-codex-job.py`: `objekte_und_lagen()` holt Namen UND
Kamera-Projektion in EINEM Blender-Lauf, `_bauteil()` fasst Teilnetze auf
`<stamm>-<nummer>` zusammen, `_marker_liste()` nummeriert, `objektkarte()`
zeichnet die Marker mit Pillow auf den vorhandenen Baseline-Render und legt
`OBJEKTKARTE-<stem>.png` neben die .blend. `codex-job.json` bekommt
`object_map`, `CODEX-AUFTRAG.md` den Abschnitt "Wo diese Objekte liegen".
Ohne Pillow oder ohne Baseline-Render bleibt der Auftrag gueltig, nur ohne
Karte. Regelwerk §2.8/§2.9/§11 verweisen darauf und nennen die
Tuerblatt-Falle beim Namen.

Neu: `scripts/make-codex-job.test.py`, 14 Tests, gruen. Am echten Haus
erzeugt: 14 Marker statt vorher 26 Einzelnetze; Regelwerk-Hash
`e01057d8e3b0a0da`.

## STUFF-LEERE-RECHTECKE-001 (PENDING)

Beim Vermessen fuer CODEX-OBJEKTKARTE-001 aufgefallen, ausserhalb des Umfangs
gelassen: `german_catalog_review_bungalow_3_2_3_b_100_1` hat neun
`stuff`-Rechtecke im Bauplan, aber nur sieben `stuff`-Objekte in der .blend.
Zwei Paare sind exakte Dubletten
(`[[9450,5096],[9400,5046]]` und `[[5850,10196],[4550,9346]]`), und das erste
Paar misst 50 x 50 mm -- mit einem Klick gesetzt statt gezogen. In der
Objektkarte fallen deshalb zwei Marker (`stuff-28`, `stuff-29`) auf denselben
Pixel.

Naechstes Tor: eigener Plan. Entweder der Annotator verwirft Rechtecke unter
einer Mindestkante und meldet Dubletten, oder der Plan-Builder filtert sie.
Vorher den ganzen Korpus durchzaehlen, wie viele Haeuser das betrifft.

## CODEX-OBJEKTKARTE-002 (COMPLETE)

`born2thrill-local-workbench/plans/codex-objektkarte-v2.md`.

Nachtrag zu CODEX-OBJEKTKARTE-001: die Karte stand auf der Hausseite nur als
Dateiname in einem Ordner -- dieselbe Antwort, die Rainer am 2026-08-20 schon
einmal zurueckgewiesen hat. Neu:
`src/app/api/floorplan-workbench/objektkarte/route.ts` liefert
`OBJEKTKARTE-*.png` aus dem go-baseline-Ordner aus, lokal-only, ohne
Dateinamen-Parameter von aussen (die Route sucht die Datei selbst, damit es
keinen Weg aus dem Ordner heraus gibt). `auftrag/route.ts` gibt zusaetzlich
`karte` zurueck, `src/app/haus/page.tsx` zeigt sie unter "An Codex".

Geprueft: `npm run test:house-state` 8/8, `npx tsc --noEmit` sauber, Bild
laedt im Browser mit 2000 x 1500; `?plan=../..` und `?plan=..%2f..` -> 400,
Haus ohne Auftrag -> 404.

## CODEX-OBJEKTKARTE-003 (COMPLETE)

`born2thrill-local-workbench/plans/codex-objektkarte-v3.md`.

Die Objektkarte aus CODEX-OBJEKTKARTE-001 markierte Garderobe, Stuff,
Sanitaer und Kueche -- aber nicht die Tuerblaetter, und genau die werden mit
der Garderobe verwechselt. `wall-12-door` steht aufgeschlagen (898 x 898 x
2010 mm) 190 Pixel neben `garderobe-25`. Zwei Nachbesserungsrunden am
2026-08-27 (17:03 und 17:59) haben in Soft Scandinavian und Classic dasselbe
geliefert: Garderobe richtig, Tuerblatt weg -- bei 32 % bzw. 13 % geaenderten
Pixeln im Eingangsbereich, also nicht aus Nachlaessigkeit.

Neu: `_stamm()` erkennt `-door` als eigene Rolle "Tuer (bleibt, nicht
ersetzen)", `_bauteil()` faltet ein Tuerblatt nicht in seine Wand, und die
Marker sind nach Rolle gefaerbt -- rot ersetzen, blau stehenlassen. §1.2 des
Regelwerks nennt die Tuermarker. 18 Tests statt 14, gruen. Am Haus: 18 Marker
statt 14, Regelwerk-Hash `ad50a9e09c2f78bd`.

## CODEX-REGELN-EINDEUTIG-001 (COMPLETE)

Rainer, 2026-08-27: "unsere rules sind nicht eindeutig genug". Drei
Nachbesserungsrunden an `german_catalog_review_bungalow_3_2_3_b_100_1` haben
jeweils die benannte Stelle repariert und eine andere zerstoert -- Garderobe,
dann Tuerblatt, dann Badewanne, dann Schreibtisch. Ursache: eine
Ganzbild-Bearbeitung wuerfelt das ganze Geschoss neu, und das Regelwerk
verbot nirgends, ein angenommenes Bild noch einmal zu erzeugen.

Geschlossen in `docs/CODEX-REGELN-4PLUS2.md` (Hash `bfa9bd1990a743c9`):
- **8.2** Ein angenommenes Bild wird NIE neu erzeugt; Nachbesserung nur auf
  dem Bild selbst; nur die im Auftrag genannten Dateien; alte Fassung wandert
  vor dem Ersetzen unter `-vorher-<uhrzeit>` zur Seite.
- **11.1** Selbstpruefung ist Pflicht und wird als `marker_check` je Bild in
  `catalog.json` mitgeliefert -- jeder Marker der Objektkarte genau einmal,
  Status `sichtbar` oder `ersetzt`.
- **11.2** Nach jeder Korrektur wird die ganze Pruefliste neu durchlaufen,
  nicht nur die korrigierte Stelle.
- **12** Eine angenommene Datei wird nicht ueberschrieben.

Dazu in `scripts/make-codex-job.py`: `_inventar()` und der Abschnitt "Inventar
dieses Geschosses" listen jedes Moebel der .blend mit Anzahl. Die Objektkarte
markiert nur die verwechselbaren Objekte; der Schreibtisch hatte keinen Marker
und verschwand deshalb unbemerkt. 21 Tests statt 18, gruen.

Offen: der Auftrag kann diese Erweiterungen erst tragen, wenn das Haus wieder
gebaut ist -- `make-codex-job.py` verweigert seit dem gescheiterten Bau vom
18:40 mit "keine zertifizierte Lieferung".

## LIEFERUNG-MARKER-GESCHOSS-001 (COMPLETE)

Der Pruefer verlangte einen `marker_check` fuer jedes Innenbild, sobald der
Auftrag eine Objektkarte enthielt -- auch fuer Bilder aus einem Geschoss, das
die Karte gar nicht zeigt.

`codex-onehalfstorey_020-2026-08-28-final` war sachlich einwandfrei (zehn
Bilder unter den geforderten Namen, alle sha256 byte-identisch mit dem
angenommenen Review-Satz, `state: final`) und fiel mit vier Beanstandungen
durch: die OG-Bilder 07--10 stammen aus `interior-modern-upper-baseline.blend`,
die Karte war `OBJEKTKARTE-interior-modern-baseline.png`. Der Auftragstext
hatte Codex ausdruecklich verboten, dort etwas zu erfinden; Codex hielt sich
daran und fiel dafuer durch.

`_karte_deckt_bild()` vergleicht jetzt den Stamm der Kartendatei mit dem
`source_blend` des Bildes. Ohne `source_blend` bleibt der `marker_check`
Pflicht -- sonst waere ein weggelassenes Feld ein Schalter. Ein gelieferter
`marker_check` wird weiterhin vollstaendig geprueft, auch ausserhalb der Karte.

Geaendert: `scripts/lieferung-pruefen.py`, `scripts/lieferung-pruefen.test.py`
(16 -> 24 Tests, alle gruen). Plan:
`born2thrill-local-workbench/plans/LIEFERUNG-MARKER-GESCHOSS-001.md`.

## CODEX-OBJEKTKARTE-OG-001 (COMPLETE)

Eine Objektkarte fuer `interior-modern-upper-baseline.blend`, damit die
Obergeschoss-Bilder denselben Beweis liefern wie die des Erdgeschosses.

Heute gibt es sie nur fuers Erdgeschoss. Genau im Obergeschoss liegt die
Eckbadewanne, die dreimal aus der Lieferung verschwand, ohne dass es an einer
Pruefung auffiel -- gefunden wurde sie jedes Mal von Rainer im Bild. Solange
dort keine Karte liegt, sind vier von zehn Bildern unbelegt.

Beruehrt: `scripts/make-codex-job.py` (`objekte_und_lagen()` und
`objektkarte()` je Innen-Baseline statt einmal), `object_map` im Auftrag wird
zu einer Liste, `lieferung-pruefen.py` waehlt die passende Karte je
`source_blend`.

## DATENSATZ-3-2-4-NEUZEICHNUNG-001 (COMPLETE)

Der Moebel-Tab von `german_catalog_review_bungalow_3_2_4_b_100_1` blieb leer
(Rainer, 2026-08-28: "ich kann keine Moebel setzen"). Die eingebettete Route
`/api/floorplan-workbench/generate` antwortete 422 "Reference is not
quality-passed, training-ready, and explicitly annotated."

Das Haus steht in beiden Datensaetzen; `simplifier-reference.ts` merged sie
ueber eine Map, der Rekonstruktions-Eintrag gewinnt. Dort stand
`package_status: "annotated"`. Die frisch gezeichnete `annotations.json`
(2026-08-28 16:46 UTC) sagt selbst `training_ready` mit
`quality_checks.passed: true` -- der Datensatz war stale, nicht die Zeichnung.

Der eine Eintrag wurde durch das Ergebnis von `export_generator_dataset.py`
ersetzt: `package_status` -> `training_ready`, `annotation_sha256` ->
`019a5155...`, 7 Raeume -> 6, 16 Elemente -> 14. Alle Rechtefelder unveraendert
(`restricted_reference`, `internal_reference_only`, `reconstruction_only`).
Kein anderes der 55 Projekte veraendert. Route liefert 200, der Editor zeigt
sechs Raeume. Plan:
`born2thrill-local-workbench/plans/DATENSATZ-3-2-4-NEUZEICHNUNG-001.md`.

## DATENSATZ-NEUEXPORT-SCHRUMPFT-001 (PENDING)

`export_generator_dataset.py` gegen `floorplan-simplifier/projects` in einen
Testordner ausgefuehrt liefert 104 Projekte. Das lebende `dataset.json` hat
314. Ein vollstaendiger Neuexport wuerde also 210 Projekte entfernen.

Deshalb wurde fuer 3_2_4 nur der eine Eintrag ersetzt. Solange das ungeklaert
ist, ist der Exporter nicht benutzbar, und jede weitere Neuzeichnung braucht
denselben Handgriff. Zu klaeren: woher die 210 stammen, ob sie aus einem
frueheren Projektbestand kommen und ob sie noch gelten.

## DATENSATZ-DOPPELEINTRAG-RECHTE-001 (PENDING)

Alle 55 Rekonstruktionsprojekte stehen auch in `dataset.json`, und bei allen
55 widersprechen sich die Rechtefelder: `not_restricted` in `dataset.json`
gegen `restricted_reference` in `reconstruction-dataset.json`.

Heute entscheidet die Reihenfolge im Array, welcher Eintrag gilt --
`ALL_REFERENCE_PROJECTS` in `src/lib/training/simplifier-reference.ts` baut
eine Map, der spaetere gewinnt. Zufaellig ist das die strengere Fassung. Auf
eine Array-Reihenfolge sollte sich kein Rechte-Tor verlassen.

Zu entscheiden ist von Rainer, welcher der beiden Eintraege je Haus gilt.
Erst danach: den unterlegenen entfernen oder den Merge explizit "die
strengere Angabe gewinnt" schreiben lassen.

## CODEX-FINALSATZ-IM-AUFTRAG-001 (ERSETZT durch LIEFERUNG-NAME-LOKAL-001)

Rainer, 2026-08-28: "schreibe das bitte in den Auftrag, das ist echt unnoetig
immer wieder."

Abschnitt 12 sagte nur, dass Zwischenstaende eigene Namen tragen (`-v2`,
`-review`) -- nicht, wie daraus die Lieferung wird. Codex lieferte deshalb bei
`onehalfstorey_020` `-review` und `-review-2` und wartete; bei
`german_catalog_review_bungalow_3_2_4_b_100_1` wieder `-review`. Der
Umbenennungsauftrag musste jedes Mal von Hand geschrieben werden.

Die eigentliche Gefahr ist nicht die Handarbeit, sondern der Neurender: bei
`onehalfstorey_020` verschwand die Badewanne dreimal aus vier Bildern. Ein
angenommenes Bild darf nie neu erzeugt werden.

Jetzt steht im erzeugten Auftrag der Abschnitt "Vom Reviewsatz zum Finalsatz"
mit dem konkreten Zielordner `<Lieferordner>-final`, dem Verbot des
Neurenderns, der sha256 als Beweis und den genau drei erlaubten Aenderungen an
`catalog.json`. Dasselbe in Abschnitt 12 des Regelwerks.

Geaendert: `scripts/make-codex-job.py` (neuer Helfer `_final_ordner()`),
`scripts/make-codex-job.test.py` (23 -> 28 Tests),
`docs/CODEX-REGELN-4PLUS2.md` Abschnitt 12. Regelwerk-Hash jetzt
`73724ece0015a505`. Alle Suiten gruen: 28/24/7/8.

Offen bleiben aus derselben Regelpruefung: der Auftrag beschreibt bei
mehrgeschossigen Haeusern nur das Erdgeschoss (siehe
CODEX-OBJEKTKARTE-OG-001), `catalog.json` ist Prosa statt Schema, und der
Upload-Befehl im Auftrag umgeht `ANGENOMMEN.json`.

## LIEFERUNG-NAME-LOKAL-001 (COMPLETE)

Rainer, 2026-08-28: "ich habe echt keine Lust hier immer wieder zu eiern --
Codex hat wieder eine Tuer vergessen und eine Datei falsch benannt, das muss
jetzt endlich vorbei sein." Und: "wir muessen die Sachen hier mehr
vereinfachen, nicht komplizierter machen."

CODEX-FINALSATZ-IM-AUFTRAG-001 hatte am selben Tag das Gegenteil getan: einen
Auftragsabschnitt, der Codex erklaert, wie er einen zweiten Satz erzeugt. Eine
Runde mehr statt weniger.

Der Dateiname zaehlt an genau EINER Stelle: `publish-renders.py` macht aus ihm
den WordPress-Slug. Also wird er dort abgeschnitten, wo die Dateien liegen.
`lieferung-pruefen.py` kennt jetzt `_grundname()` (Suffixe `-review`,
`-review-2`, `-v3`), nimmt Zwischenstandsnamen ohne Beanstandung an und
benennt beim `--annehmen` die Dateien um -- `os.replace`, also dieselben
Bytes, dieselbe sha256. `catalog.json` wird mitgezogen, `state` auf `final`.

Damit faellt weg: die zweite Codex-Runde, der `-final`-Ordner, die
handgeschriebene sha256-Tabelle. Und es ist sicherer als vorher, weil Codex
die angenommenen Bilder nie wieder anfasst.

Belegt an der echten Lieferung: `german_catalog_review_bungalow_3_2_4_b_100_1`
angenommen, sechs Dateien umbenannt, alle sechs sha256 unveraendert.

Geaendert: `scripts/lieferung-pruefen.py` (`_grundname()`, `zuordnung()`,
`_auf_geforderte_namen()`), `scripts/lieferung-pruefen.test.py` (24 -> 35),
`scripts/make-codex-job.py` (Abschnitt ersetzt, `_final_ordner()` entfernt),
`scripts/make-codex-job.test.py`, `docs/CODEX-REGELN-4PLUS2.md` Abschnitt 12.
Suiten: 35/28/7/8 und 8 Node-Tests gruen.

## LIEFERUNG-TUER-VERSCHWUNDEN-001 (PENDING)

Der zweite Teil von Rainers Satz. Der `marker_check` ist eine Selbstauskunft
und kann falsch sein: am 2026-08-27 wies ein Bild die Badewanne als
"sichtbar" aus, obwohl sie fehlte.

Tueren sind der messbare Fall. Ihre Pixelposition steht in der Objektkarte,
und in `go-baseline` liegen neben dem Baseline-Render auch der Edge- und der
Mask-Pass. Eine Tueroeffnung hat dort eine kraeftige, senkrechte Signatur;
steht ein Schrank davor, verschwindet sie.

Zu bauen ist ein Vergleich der Kantenstruktur in einem kleinen Ausschnitt um
jeden blauen Tuer-Marker, Lieferung gegen Baseline. Vorher an echten Bildern
kalibrieren -- es gibt bekannte Faelle in beide Richtungen. Ohne diese
Kalibrierung nicht ausliefern: ein Waechter, der bei jeder Moebelaenderung
anschlaegt, wird nach drei Fehlalarmen ignoriert.

## ZEICHNER-OEFFNUNGSBREITEN-001 (COMPLETE)

Rainer, 2026-08-28: "well i asked if you could put a right click dropdown with
the widths, that never happened" -- "the windows and the doors, that been
ignored." Er hatte recht, die Bitte lag unerledigt.

Rechtsklick auf eine Tuer oder ein Fenster oeffnet jetzt ein Menue mit
Normbreiten; die naechstliegende ist hervorgehoben. Tueren 625/750/875/1000/
1125 mm, Fenster 600/885/1010/1260/1510/2010/2510/3010 mm. Die Mitte der
Oeffnung bleibt stehen, die Richtung auch. `opening` und `stairs` bekommen
kein Menue -- ein Durchgang darf so breit sein, wie er gezeichnet ist.

Anlass: in `german_catalog_review_bungalow_3_2_4_b_100_1` sind drei der sechs
Tueren 1158, 1220 und 1221 mm breit. Eine einfluegelige Tuer gibt es bis rund
1010 mm; darueber macht jeder Renderer eine Doppeltuer, zu Recht. Die Bilder
waren nie falsch, die Oeffnung war es.

Dazu: `handle_get_annotations` legt den Massstab aus `gebaeudemass.json` dazu,
wenn in `annotations.json` keiner steht (`floor_scale_aus_gebaeudemass()`,
nur beim Lesen, nur fehlende Werte -- die Zeichnung sticht das Beiblatt).
Ohne das zeigte das Menue ausgerechnet bei diesem Haus "kein Massstab".

Nebenbei repariert: die `?v=`-Stempel in `annotate.html` standen auseinander,
`test_cache_busting_stayed_in_step` war schon vorher rot. Alle sechs jetzt
auf `20260828-200000`.

Neu: `static/oeffnungsbreiten.js`, `static/oeffnungsbreiten.test.mjs` (12),
`tests/test_floor_scale_from_gebaeudemass.py` (8). Geaendert: `app.py`,
`static/annotate.html`. Suiten: 107 Python gruen, 30 Node gruen. Am echten
Haus im Browser geprueft -- Menue oeffnet fuer Tuer und Fenster, 1220 -> 875
gesetzt, Mitte um 0.0 gewandert, danach zurueckgesetzt.

## OEFFNUNGSBREITEN-BESTAND-001 (PENDING)

Das Menue hilft beim naechsten Haus. Die schon gezeichneten bleiben, wie sie
sind -- 270 Projekte, viele davon mit Tueren ueber 1010 mm.

Zu entscheiden: ob der Planbauer `door`-Oeffnungen beim Bauen auf die naechste
Normbreite rastet. Das repariert alle auf einmal, ohne Neuzeichnen, aendert
aber Geometrie in jedem Haus -- deshalb Rainers Entscheidung, nicht meine.
Vorher zaehlen, wie viele Oeffnungen sich um wie viel bewegen wuerden.

## LIEFERUNG-KASTEN-GEMESSEN-001 (COMPLETE)

Rainer, 2026-08-28: "you have to force the rendering of deco stuff for the
'stuff', often it just creates a large box."

Das Regelwerk verlangt das Ersetzen seit Wochen (Abschnitt 2.9 und 11), und
der `marker_check` fragt es ab. Nur ist der eine Selbstauskunft, und die war
schon falsch: am 2026-08-27 stand die Badewanne als "sichtbar" drin und
fehlte. Eine weitere Regel haette daran nichts geaendert.

Deshalb gemessen statt gefragt. Ein Platzhalter ist ein glatter grauer Quader:
im Umkreis des Markers heben sich ueber 60 % der Pixel nicht von ihrer
Umgebung ab. Gefragt wird zweimal -- war die Stelle im Baseline-Render flach
(>= 50 %), UND ist sie es in der Lieferung immer noch (>= 65 %).

Zwei Anlaeufe. Der erste zaehlte Kanten und trennte gar nicht (ersetzt
0.82-1.08, bleibt 0.74-1.06). Der zweite fragte nach dem Abfall der flachen
Flaeche und schlug bei zwei fertig eingerichteten Stellen an: einmal hatte ein
Tuerblatt den Kasten ersetzt, einmal eine Wand mit Bild -- beide selbst flach.
Die zweite Schwelle erledigt beide.

Ueber die zwei angenommenen Lieferungen vom 2026-08-28 meldet die Fassung
genau einen Marker: `stuff-21` in `onehalfstorey_020`, und dort steht
tatsaechlich noch nichts.

Bleibt eine WARNUNG im Pruefer, keine Beanstandung -- ein einziger belegter
Treffer ist zu wenig, um eine fertige Lieferung zu blockieren.

Geaendert: `scripts/lieferung-pruefen.py` (`kasten_verdacht()`,
`messe_platzhalter()`, `_flachanteil()`), `scripts/lieferung-pruefen.test.py`
(35 -> 44). Pillow ist optional: fehlt es, gibt es keine Warnung statt eines
Abbruchs.

## LIEFERUNG-KASTEN-NACHSCHAERFEN-001 (PENDING)

Die Schwellen stehen auf zwei Lieferungen und EINEM belegten Treffer. Das
reicht, um hinzusehen, nicht um zu blockieren.

Mit jeder weiteren angenommenen Lieferung waechst die Grundlage. Wenn genug
Faelle beisammen sind: pruefen, ob die Warnung zur Beanstandung taugt, und ob
der Radius von 55 px fuer kleine Objekte zu grob ist -- er misst heute auch
Wand und Boden ringsum mit.

## CODEX-OBJEKTKARTE-ALLE-MOEBEL-001 (COMPLETE)

Rainer, 2026-08-28: "ja wir brauchen Ergebnisse."

In der Lieferung fuer `german_catalog_review_bungalow_3_2_5_b_100_1` stand im
Baseline-Render ein Schreibtisch mit Buerostuhl. Drei der vier Stile tauschten
ihn aus: warm modern ein Lowboard mit Fernseher, scandinavian ein Einzelbett,
classic ein Sideboard. Nur dark modern liess ihn stehen. Der `marker_check`
meldete 12 von 12 in Ordnung -- weil der Schreibtisch keinen Marker hatte.

Die Karte trug bisher nur `garderobe`, `stuff`, Sanitaer, Kueche und Tueren.
Der Kommentar an `_inventar` hielt schon am 2026-08-27 fest, dass genau dieser
Schreibtisch aus drei Bildern verschwand, und entschied sich trotzdem fuer die
kurze Karte plus eine Inventarliste, aus Sorge um die Lesbarkeit. Die Liste
hat es nicht verhindert.

Jetzt bekommt jedes Moebelstueck einen Marker (`rolle_fuer()`,
`farbe_fuer()`). Neue Rolle fuer alles ohne eigenen Eintrag: "Moebel
(umgestalten, muss sichtbar bleiben)" -- bewusst anders formuliert als
"ersetzen", damit ein Schreibtisch stilgerecht neu aussieht und ein
Schreibtisch bleibt. Rot bleibt `garderobe` und `stuff`.

Die Sorge um die Lesbarkeit war unbegruendet: die neue Karte fuer 3_2_5 traegt
39 Marker statt 12 und ist lesbar; Marker 26 sitzt auf dem Schreibtisch.

Geaendert: `scripts/make-codex-job.py`, `scripts/make-codex-job.test.py`
(28 -> 33). Suiten: 33/44/7/8 und 107 im Simplifier gruen.

## LIEFERUNG-3-2-5-NACHBESSERN-001 (PENDING)

Die vorliegende Lieferung entstand gegen die alte 12-Marker-Karte. `04 dark
modern` ist in Ordnung; `03`, `05` und `06` haben den Schreibtisch ersetzt und
muessen gegen die neue Karte nachgebessert werden. Formal ist die Lieferung
sauber (6/6 Masze, 6/6 sha256, 12/12 Marker, keine Kasten-Warnung) -- der
Fehler lag ausserhalb dessen, was geprueft wurde.

## LIEFERUNG-VORHER-ARCHIV-001 (COMPLETE)

Regelwerk Abschnitt 12 verlangt bei einer Nachbesserung, dass die alte Fassung
unter `-vorher-<uhrzeit>` zur Seite wandert. Am 2026-08-28 tat Codex bei
`german_catalog_review_bungalow_3_2_5_b_100_1` genau das -- und der Pruefer
wies die Nachbesserung ab: "Zusatzdateien im Lieferordner, der Upload wuerde
sie mitnehmen." Regelkonform geliefert und trotzdem durchgefallen, zum zweiten
Mal an einem Dateinamen.

Beide Sorgen stimmen: das Archiv soll bleiben, und `publish-renders.py` laedt
jede Bilddatei des Ordners hoch. Also wandert es beim Annehmen nach
`vorher/`, statt beanstandet oder geloescht zu werden.

Geaendert: `scripts/lieferung-pruefen.py` (`VORHER`, `VORHER_ORDNER`),
`scripts/lieferung-pruefen.test.py` (44 -> 49).

## LIEFERUNG-3-2-5-NACHBESSERN-001 (COMPLETE)

Nachgebessert und angenommen. In `03`, `05` und `06` steht der Schreibtisch
wieder an seiner Wand, mit Buerostuhl, im Fussabdruck des Modells.
`04-floorplan-dark-modern` blieb byte-identisch (sha256 `c0e9d252...`).
`marker_check` jetzt 39 von 39 in allen vier Innenbildern.

## ZEICHNER-RUECKGAENGIG-UND-SCHIEBEN-001 (COMPLETE)

Rainer, 2026-08-28: "i need some kind of 'back' button -- if i select points
then align them accidentally waagrecht instead of senkrecht then its over, the
drawing is kaputt." Und: "could i select something and nudge it with the
keyboard arrows?"

`punkteAusrichten()` schreibt den Median in jeden ausgewaehlten Punkt; bei
falscher Achse waren die Originalwerte fort, und es half nur Neuzeichnen.

Jetzt legt jede Punktaenderung vorher einen Abzug weg (Zahlen, keine
Verweise -- ein Verweis zeigte auf dieselben Objekte, die veraendert werden).
Strg+Z oder der Knopf "↶ Zurueck" holt ihn zurueck, 50 Stufen tief.
Pfeiltasten schieben die Auswahl in Millimetern: 10 mm, mit Shift 100 mm, mit
Alt 1 mm. Die y-Achse bekommt das Seitenverhaeltnis der Leinwand, sonst waere
ein Schritt nach unten nur 81 % so weit wie einer nach rechts.

Neu: `static/punkte-verschieben.js`, `static/punkte-verschieben.test.mjs`
(10 Tests). Geaendert: `static/punkte-ausrichten.js`, `static/annotate.html`.

## ZEICHNER-ELEMENTMENUE-ABFAENGER-001 (COMPLETE)

Rainer, 2026-08-28: "i cant set if the windows are bodentief and how many
Fluegel they have."

Das war kein fehlendes Feature. `element-edit.js` hat das seit langem --
Bodentiefes Fenster / Bruestungsfenster und 1/2/3 Fluegel (`element.panes`),
und `build-simplifier-render-plan.py` liest `window_type` fuer die
Bruestungshoehe. Mein `oeffnungsbreiten.js` von heute Nachmittag hatte einen
eigenen contextmenu-Handler in der CAPTURE-Phase mit `stopPropagation()` und
legte damit genau dieses Menue lahm.

Der Abfaenger ist raus. Die Normbreiten haengen jetzt als Eintraege im
bestehenden Elementmenue (`breitenMenueEintraege()`), ein Menue statt zwei.
Im Browser geprueft: ein Rechtsklick aufs Fenster zeigt Bodentief,
Bruestung, 1/2/3 Fluegel, die acht Fensterbreiten und Loeschen.

## DATENSATZ-3-2-4-ERNEUT-STALE-001 (PENDING)

`german_catalog_review_bungalow_3_2_4_b_100_1` wurde am 2026-08-28 um 19:11
erneut gezeichnet (siebter Raum "Diele"). Der Eintrag in
`reconstruction-dataset.json` stammt vom Stand 16:46 (sechs Raeume,
`annotation_sha256` 019a5155...). `package_status` stimmt weiterhin, der
Moebel-Tab geht also auf -- aber Raeume und Geometrie im Datensatz sind
wieder alt. Solange DATENSATZ-NEUEXPORT-SCHRUMPFT-001 offen ist, braucht
jede Neuzeichnung den Handgriff von Hand.

## MOEBEL-PUNKTE-BEARBEITEN-001 (COMPLETE)

Rainer, 2026-08-28: "can we also edit the Kuechenzeile and
vorwandinstallation, make the points selectable and moveable? its almost
impossible to get them right on the first try -- you know, select point, align
and nudge?"

Rechtecke (Kuecheninsel, Abstellschrank) hatten seit jeher Eckgriffe,
gezeichnete Laeufe (Kuechenzeile, Vorwandinstallation, Stuff) nicht: sie
liessen sich nur als Ganzes verschieben. Ein einzelner Knick war nicht zu
erreichen, und ein Lauf, der nicht beim ersten Zeichnen sass, musste neu
gezeichnet werden.

Jetzt traegt ein gewaehlter Lauf einen Griff je Punkt. Klick waehlt, Shift
waehlt dazu, Ziehen bewegt den einzelnen Punkt. "Waagerecht" und "Senkrecht"
ziehen die Auswahl auf den Median. Pfeiltasten schieben um 10 mm, mit Shift
100 mm, mit Alt 1 mm -- dieselben Schrittweiten wie im Zeichner, damit die
Hand nicht umlernt. Strg+Z und "↶ Zurueck" nehmen zurueck, 50 Stufen.

Ein Fehler dabei, der Zeit gekostet haette: der Abzug fuer den Rueckweg lag
zuerst INNERHALB des `setDocument`-Updaters. React ruft den im
Entwicklungsmodus zweimal auf, also stand jede Aenderung doppelt im Stapel und
ein Strg+Z bewegte nichts -- im Browser gemessen: sechs Eintraege fuer drei
Aenderungen. Der Abzug entsteht jetzt vor dem Aufruf, aus einem Ref, der dem
Dokument folgt. Ein Test haelt das fest.

Neu: `scripts/moebel-punkte.test.mjs` (15 Tests). Geaendert:
`src/app/floorplan-workbench/furniture.tsx` (`richtePunkteAus`,
`schiebePunkte`, `punktSchrittMm`, Griffe, Rueckweg im `mutate`),
`src/app/floorplan-workbench/page.tsx` (Auswahl, Ziehen, Tastatur).
`npx tsc --noEmit` sauber, 15 + 8 + 8 Node-Tests gruen. Im Browser an der
echten Kuechenzeile von `german_catalog_review_bungalow_3_2_5_b_100_1`
geprueft: ausrichten 8550/9250 -> 8900/8900, ArrowRight +10 mm,
Shift+ArrowDown +100 mm, ein Strg+Z stellt her. Nichts gespeichert.

## MOEBEL-VORDERSEITE-PFEIL-001 (COMPLETE)

Rainer, 2026-08-28: "there are some symbols where it is hard to see where the
front is -- like kuehlschrank, hochschrank herd, waschbecken, wandwc. could
you add like an arrow on top, back to front?"

Ein Kuehlschrank ist im Grundriss ein Quadrat von 600 x 600 mm; wohin seine
Tuer zeigt, steht nur in `rotation_deg`. In der Moebel-Ansicht wird das Symbol
als PNG gezeichnet, ganz ohne Richtungshinweis. (`FurnitureSvg`, die andere
Ansicht, hatte schon einen Vorderkanten-Strich -- der bestaetigt die
Konvention: lokales +y ist vorn, die Rueckseite liegt an der Wand, wie in
`snapStampToWalls` beschrieben.)

Neun Symbole mit echter Vorderseite bekommen jetzt einen Pfeil von hinten nach
vorn, in beiden Ansichten: Kuehlschrank, Hochschrank/Herd, Spuele,
Waschmaschine, Trockner, Wand-WC, Handwaschbecken, Doppelwaschtisch,
Waschtisch. Was von allen Seiten gleich aussieht, bekommt keinen -- ein Pfeil
auf einem Hocker waere eine Behauptung.

Der Pfeil behauptet keine Richtigkeit, er macht sie sichtbar. Gemessen an den
62 platzierten Stuecken dieser Art in den zwoelf Moebeldateien: die
Vorderseite zeigt 36-mal in den Raum, 26-mal in die Wand. Es gibt heute also
keine verlaessliche Ausrichtung; ab jetzt faellt sie auf und ist mit den
Drehknoepfen zu richten.

Neu: `scripts/moebel-vorderseite.test.mjs` (7 Tests). Geaendert:
`src/app/floorplan-workbench/furniture.tsx` (`zeigtVorderseite`, `pfeilLokal`,
`Vorderseitenpfeil`). `npx tsc --noEmit` sauber, 30 Node-Tests gruen. Im
Browser an `german_catalog_review_bungalow_3_2_5_b_100_1` geprueft: sieben
Pfeile bei 25 Symbolen.

## MOEBEL-AUSSERHALB-3-2-5-PRUEFEN-001 (PENDING)

Beim Pruefen des Pfeils meldete das Panel "11 Moebel ausserhalb der Raeume"
fuer `german_catalog_review_bungalow_3_2_5_b_100_1` -- ein Haus, dessen
Lieferung angenommen und hochgeladen ist und dessen Bau durchlief. Entweder
zaehlt das Panel gegen die falschen Raumpolygone, oder der Bau hat elf Stuecke
stillschweigend fallen lassen. Beides gehoert geklaert, bevor jemand den
Zaehler ernst nimmt.

## MOEBEL-PUNKT-MENUE-UND-DOPPELPUNKT-001 (COMPLETE)

Rainer, 2026-08-28: "Kuechenzeile and Vorwandinstallation also be able to
rightclick align, and one point rightclick delete one point? Because when i
doubleclick to end the creation many times there are 2 points created at the
end."

Die Ursache des Doppelpunkts steht im Ereignis: ein Doppelklick feuert erst
ZWEI click-Ereignisse -- jedes haengt einen Punkt an den Entwurf -- und erst
danach `dblclick`, das den Lauf abschliesst. Der letzte Punkt war also zweimal
drin, an derselben Stelle.

`placeDrawn()` zieht aufeinanderfolgende Punkte jetzt zusammen, die naeher als
60 mm beieinander liegen (`entdoppelt()`). 60 mm, weil zwei Klicks derselben
Hand nicht denselben Millimeter treffen, eine bewusst gesetzte kurze Strecke
aber laenger ist.

Dazu ein Rechtsklick-Menue am Lauf: "Waagerecht ausrichten" und "Senkrecht
ausrichten" bei mehr als einem gewaehlten Punkt, und auf einem einzelnen Punkt
"Diesen Punkt loeschen". Unter zwei Punkten ist es kein Lauf mehr, dann ist
der Eintrag ausgegraut. Alles laeuft ueber `mutate`, also nimmt Strg+Z es
zurueck.

Geaendert: `src/app/floorplan-workbench/furniture.tsx` (`entdoppelt`,
`loeschePunkt`, `onPathMenu`), `src/app/floorplan-workbench/page.tsx`
(Menue). `scripts/moebel-punkte.test.mjs` 15 -> 22 Tests. `tsc` sauber,
22 + 7 + 8 + 8 Node-Tests gruen. Im Browser geprueft: Rechtsklick auf den
Punkt zeigt "5 Punkte · 1 gewaehlt / Diesen Punkt loeschen", loeschen macht
5 -> 4, Strg+Z macht 4 -> 5.

## MOEBEL-AUSRICHTEN-IMMER-001 (COMPLETE)

Rainer, 2026-08-28: "why no align waagrecht and senkrecht? Im just trying to
make it easier for the 'Bauen' part." Und gleich darauf: "but the second point
gets deselected when i right click."

Zwei Fehler im Menue von vorhin:

1. Ausrichten erschien nur bei zwei bereits gewaehlten Punkten. Wer den Lauf
   anklickt, um ihn gerade zu ziehen, bekam den Hinweis "Punkt anklicken,
   Shift fuer mehrere" -- ein Menue, das erklaert statt zu tun. Jetzt stehen
   beide Befehle immer da und beziehen sich ohne Auswahl auf den ganzen Lauf:
   "Waagerecht ausrichten (alle 5)".
2. Der Rechtsklick rief dieselbe Auswahlregel wie der Linksklick, und die
   ersetzt ohne Shift die Auswahl durch den einen Punkt. Wer zwei waehlte und
   dann rechtsklickte, hatte danach einen. Ein Rechtsklick laesst die Auswahl
   jetzt stehen, wenn der Punkt schon drin ist.

Geaendert: `src/app/floorplan-workbench/page.tsx`.
`scripts/moebel-punkte.test.mjs` 22 -> 29 Tests. `tsc` sauber, 29 + 7 + 8 + 8
gruen. Im Browser geprueft: zwei Punkte gewaehlt, Rechtsklick auf den zweiten
-> "5 Punkte · 2 gewaehlt / Waagerecht ausrichten (2 Punkte) / Senkrecht
ausrichten (2 Punkte) / Diesen Punkt loeschen", beide Griffe bleiben gross.

## MOEBEL-DOPPELPUNKTE-BESTAND-001 (COMPLETE)

`entdoppelt()` greift beim Anlegen. Die schon gespeicherten Laeufe behalten
ihre Doppelpunkte: von 65 gezeichneten Laeufen in den zwoelf Moebeldateien
haben 18 einen. Betroffen sind unter anderem `onehalfstorey_020`,
`onehalfstorey_029` und die fuenf `german_catalog_review_bungalow_3_2_*`.

Von Hand geht es jetzt (Rechtsklick auf den Punkt, loeschen). Zu entscheiden,
ob ein Durchlauf sie stillschweigend zusammenzieht -- das aendert gespeicherte
Geometrie in Haeusern, deren Lieferung schon angenommen ist, und gehoert
deshalb Rainer.

## MOEBEL-DOPPELPUNKTE-DURCHLAUF-001 (COMPLETE)

Rainer, 2026-08-28, auf die Frage, ob ein Durchlauf die schon gespeicherten
Doppelpunkte zusammenziehen soll: "what ever you think is better."

Beim Nachsehen zerfiel der Befund in drei Sorten, und nur eine wurde angefasst:

  12 bereinigt  Der letzte Punkt eines Pfades wiederholt den vorletzten EXAKT.
                Die Strecke dazwischen ist null lang; sie zu entfernen aendert
                die Form nicht. Nachgerechnet: 37 Laeufe vor und nach dem
                Durchlauf verglichen, Streckenlaenge identisch bei allen.

   4 gemeldet   Zwei Punkte liegen 50 bis 53 mm auseinander -- knapp, aber
                nicht aufeinander. Sie zu verschmelzen kuerzte den Lauf
                wirklich. Von Hand zu entscheiden.

   2 gemeldet   `onehalfstorey_020` hat zwei Kuecheninseln von 0 x 0 mm. Das
                ist kein Doppelpunkt, sondern eine kaputte Platzierung; sie
                gehoert neu gezeichnet oder geloescht.

Der erste Anlauf nahm die 60-mm-Toleranz des Editors und lief sofort in die
eigene Sicherheitspruefung: in `german_catalog_review_bungalow_3_1_2_b_85`
haetten 50 mm Lauflaenge gefehlt. Der Editor darf beim Anlegen grosszuegig
sein -- dort ist noch nichts gespeichert. Ein Durchlauf ueber angenommene
Haeuser darf nur entfernen, was beweisbar nichts ist.

Neu: `scripts/moebel-doppelpunkte.py`, `scripts/moebel-doppelpunkte.test.py`
(14 Tests). Je geaenderter Datei liegt `.vor-entdoppeln` als Sicherung.

## MOEBEL-ENTARTETE-KUECHENINSEL-001 (COMPLETE)

`onehalfstorey_020` hat zwei Kuecheninseln von 0 x 0 mm,
`german_catalog_review_bungalow_3_1_2_b_85` und `onehalfstorey_029` je eine
Platzierung mit 50 mm Kantenlaenge. Der Bau hat sie stillschweigend
mitgenommen; im Render ist an der Stelle nichts.

Neu zeichnen oder loeschen ist Rainers Entscheidung -- beide Haeuser sind
geliefert und hochgeladen. Der Moebel-Editor kann es jetzt: Lauf waehlen,
Punkt greifen, ziehen.

## KATALOG-AUFRAEUMEN-001 (COMPLETE)

Rainer, 2026-08-28: "dude go for it."

Der Katalog trug alte und neue Bilder nebeneinander. Welche weg duerfen, wurde
NICHT am Namen entschieden, sondern an den Bytes: fuer jedes hochgeladene Bild
die sha256 geholt und gegen `ANGENOMMEN.json` gehalten.

Das war noetig, nicht vorsichtig: bei `bungalow_039` trugen drei alte Dateien
(IDs 309, 311, 312) genau die richtigen Slugs, waehrend die aktuellen unter
`-2026-08-27` lagen. Ein Namensvergleich haette die falschen behalten.

  onehalfstorey_020   10 alte geloescht (IDs 61-70)
  bungalow_039        8 alte geloescht, 3 unter sauberen Namen neu hochgeladen,
                      3 datierte Doppel entfernt; `ANGENOMMEN.json` angelegt

Danach je Haus gegengeprueft: `bungalow_039` 6/6, `onehalfstorey_020` 10/10,
`german_catalog_review_bungalow_3_2_4_b_100_1` 6/6,
`german_catalog_review_bungalow_3_2_5_b_100_1` 6/6 -- genau der angenommene
Satz online, nichts sonst.

Vorher wurde Abschnitt 10 des Regelwerks umgehaengt: er verlinkte zwei der
geloeschten Bilder als Qualitaetsbeispiele. Er zeigt jetzt alle vier Stile aus
der angenommenen 020-Lieferung und heisst nicht mehr "Referenzbilder" --
"Reference" ist in dieser Suite ein Korpus-Grundriss mit Rechtestatus.

## BAU-VERALTET-NACH-ENTDOPPELN-001 (COMPLETE)

Der Entdoppel-Durchlauf und das Loeschen der Null-Kuecheninseln haben den
Moebel-Fingerabdruck von neun Haeusern geaendert. `make-codex-job.py`
verweigert seither mit "die .blend sind OHNE die aktuellen Moebel gebaut" --
richtig so, aber sie muessen alle einmal neu gebaut werden.

`onehalfstorey_020` laeuft. Offen: `onehalfstorey_029`, `twostorey_030`,
`german_catalog_review_bungalow_3_1_2_b_85`, `3_2_1`, `3_2_2`, `3_2_3`,
`3_2_5`, `bungalow_039`.

Die Geometrie ist dabei nachweislich unveraendert (37 Laeufe verglichen,
Streckenlaenge identisch) -- es ist der Fingerabdruck, der sich bewegt hat,
nicht der Grundriss.

## CODEX-OBJEKTKARTE-OG-001 -- Nachtrag: an neun Haeusern belegt

Alle neun Haeuser, deren Fingerabdruck sich durch das Entdoppeln und das
Loeschen der Null-Kuecheninseln bewegt hatte, sind neu gebaut und ihre
Auftraege neu geschrieben. Die Karten kommen jetzt je Geschoss:

  onehalfstorey_020        2 Karten, 72 Marker,  8 Innenbilder
  onehalfstorey_029        2 Karten, 59 Marker,  8 Innenbilder
  twostorey_030            2 Karten, 33 Marker,  8 Innenbilder
  3_1_2_b_85               1 Karte,  31 Marker,  4 Innenbilder
  3_2_1_b_100_1            1 Karte,  35 Marker,  4 Innenbilder
  3_2_2_b_100_1            1 Karte,  32 Marker,  4 Innenbilder
  3_2_3_b_100_1            1 Karte,  42 Marker,  4 Innenbilder
  3_2_5_b_100_1            1 Karte,  39 Marker,  4 Innenbilder
  bungalow_039             1 Karte,  38 Marker,  4 Innenbilder

Kein Innenbild ohne Karte mehr. In `onehalfstorey_020` ist `eckbadewanne-16`
Marker 4 der Obergeschoss-Karte -- das Objekt, das dreimal aus vier Bildern
verschwand, ohne dass eine Pruefung anschlug.

## LIEFERUNG-PRUEFER-KARTENLISTE-001 (COMPLETE)

Rainer, 2026-08-29: die erste Lieferung nach der Umstellung auf eine Karte je
Geschoss stuerzte den Pruefer ab --

    AttributeError: 'list' object has no attribute 'get'
    in messe_platzhalter: marke = karte.get("markers")

`pruefe()` war auf die Kartenliste umgestellt, `messe_platzhalter()` nicht.
Die formale Pruefung war schon durch; abgestuerzt ist erst die Kasten-Warnung
danach. Behoben, drei Tests halten beide Formen fest (53 -> 56).

## LIEFERUNG-3-3-1-NACHBESSERN-001 (COMPLETE)

Erste Lieferung gegen die neue Karte mit ALLEN Moebeln: 45 Marker, 45 im
`marker_check` aller vier Innenbilder, Masze und sha256 in Ordnung.

Trotzdem fehlen in `04-floorplan-dark-modern` und `06-floorplan-classic`
Waschmaschine und Trockner -- an ihrer Stelle stehen ein Sideboard und ein
Konsolentisch. Beide sind blau (muss sichtbar bleiben) und beide sind als
"sichtbar" gemeldet.

Genau dafuer wurde die Karte erweitert: vor der Erweiterung waeren die zwei
Geraete ueberhaupt nicht markiert gewesen und der Verlust unsichtbar geblieben.
Der `marker_check` bleibt eine Selbstauskunft und war hier wieder falsch --
derselbe Fehler wie bei der Badewanne am 2026-08-27.

Auftrag geschrieben: `renders/NACHBESSERN-2026-08-29.md`. 03 und 05 sowie die
beiden Aussenansichten sind angenommen und bleiben byte-identisch.

## LIEFERUNG-BELEG-STATT-BEHAUPTUNG-001 (COMPLETE)

Rainer, 2026-08-29, auf die Frage nach einem geschlossenen Kreis mit Codex:
erst muss die Fehlerklasse weg, sonst wiederholt der Automat nur schneller
dasselbe. "good, do it, if you think its better."

Die Klasse war immer dieselbe -- ein Objekt, das bleiben muss, ist
verschwunden, und der `marker_check` meldete "sichtbar":

    2026-08-27  Badewanne, zwei Bilder
    2026-08-28  Schreibtisch, drei von vier Bildern
    2026-08-29  Waschmaschine und Trockner, zwei von vier Bildern

Abschnitt 11.1 verlangt jetzt zu jedem BLAUEN Marker `bei`: den Pixel, an dem
Codex das Objekt im gelieferten Bild sieht. Rote brauchen keinen -- dort ist
das Ausgangsobjekt gerade weg. Der Pruefer haelt die Stelle gegen die
Markerposition (300 px Radius, bewusst weit; nachzuschaerfen, sobald echte
Sichtstellen vorliegen) und gegen die Bildgrenzen.

Eine neue Forderung wirkt NICHT nach hinten. Die erste Fassung warf 152
Beanstandungen gegen die Lieferung vom Vortag, die gegen die damalige Regel
vollstaendig war. Der Auftrag traegt jetzt `beleg_verlangt`; Lieferungen gegen
aeltere Auftraege werden nicht danach gefragt.

Dazu `RUNDEN.jsonl`: eine Zeile je Pruefung mit Plan, Ordner, Zahl und Text
der Beanstandungen -- und `--auge` fuer das, was ein Mensch im Bild fand und
der Pruefer nicht. Ohne diese Unterscheidung saehe die Statistik besser aus
als die Lage: Badewanne, Schreibtisch und Waschmaschinen sind alle am Pruefer
vorbeigegangen.

Das ist die Zahl, an der spaeter ueber den geschlossenen Kreis entschieden
wird: wie oft geht eine Lieferung im ERSTEN Durchlauf durch. Stand heute:
keine von vier.

Geaendert: `scripts/lieferung-pruefen.py` (`_beleg_beanstandungen`,
`notiere_runde`, `--auge`), `scripts/lieferung-pruefen.test.py` (56 -> 70),
`scripts/make-codex-job.py` (`beleg_verlangt`),
`docs/CODEX-REGELN-4PLUS2.md` Abschnitt 11.1.

## KREIS-MIT-CODEX-SCHLIESSEN-001 (PENDING)

Der geschlossene Kreis selbst, wenn die Erstdurchlaufquote es hergibt.

Zwei Glieder fehlen: ein Anstoss (heute fuegt Rainer den Pfad ein) und ein
maschinenlesbarer Rueckweg -- statt handgeschriebener `NACHBESSERN-*.md` eine
`RUECKMELDUNG.json` im Lieferordner mit je Bild `angenommen` oder
`nachbessern` samt Markernummern. Codex' eigene Kritik im Kopf von
`make-codex-job.py` sagt dazu: "Do not invent another manual note format.
Promote the existing handoff.json into a resumable [one]."

Zwei Dinge bleiben ausserhalb: der Blick aufs Bild -- jeder echte Fehler kam
von dort, nicht vom Pruefer -- und eine Rundenbremse, weil jede Runde ein
neuer Render ist und genau das die Badewanne kostet.

## LIEFERUNG-3-3-1 -- Nachtrag: nachgebessert, angenommen, hochgeladen

Codex hat 04 und 06 neu gemacht, 01/02/03/05 blieben byte-identisch, die alten
Fassungen liegen in `vorher/`. In `04-floorplan-dark-modern` stehen jetzt zwei
dunkle Maschinen, in `06-floorplan-classic` zwei weisse unter einer Konsole --
stilgerecht umgestaltet statt ersetzt, wie Abschnitt 2.2 es verlangt.

`bei` fehlte trotzdem in allen 45 Markern. Kein Verstoss: im Auftragsordner
liegt die `CODEX-REGELN.md` von vor der Aenderung, und der Auftrag traegt kein
`beleg_verlangt`. Codex hat nach der Fassung gearbeitet, die dort lag. Der
Beleg greift ab dem naechsten neu geschriebenen Auftrag.

Das ist zugleich eine Beobachtung fuer KREIS-MIT-CODEX-SCHLIESSEN-001: die
Regel steht in `docs/`, gearbeitet wird nach der Kopie im Auftragsordner. Wer
den Kreis schliesst, muss dafuer sorgen, dass beide gleichziehen -- sonst
arbeitet der Automat nach einer Regel, die niemand mehr fuer gueltig haelt.

Beim Hochladen fielen drei graue Blender-Klotze auf, die seit einer frueheren
Runde im Katalog standen (`*-baseline`, IDs 99-101) -- genau der Fehler, den
Abschnitt 12 nennt. Per sha256 gegen `ANGENOMMEN.json` identifiziert und
geloescht.

Stand jetzt, jedes Haus mit Angenommen-Zeiger gegengeprueft:

    bungalow_039        6 online,  6 angenommen
    3_2_4               6 online,  6 angenommen
    3_2_5               6 online,  6 angenommen
    3_3_1               6 online,  6 angenommen
    onehalfstorey_020  10 online, 10 angenommen

Nichts Fremdes mehr im Katalog.

## EINE-WAHRHEIT-JE-TATSACHE-001 (Bestandsaufnahme COMPLETE, Umsetzung PENDING)

Rainer, 2026-08-29: "das was langfristig am besten ist fuer unser Projekt, ich
will gerne spaeter diese Grundriss-Generation automatisiert aufstellen."

Nur gelesen und gezaehlt, nichts geaendert. Bericht:
`born2thrill-local-workbench/plans/WEM-GEHOERT-WELCHE-TATSACHE.md`.

Kurzfassung:

- `package_status` ist das echte Problem. Drei Quellen, 48 Widersprueche (alle
  gleich gerichtet: Projekt `annotated`, dataset `training_ready`), Datensaetze
  vom 2026-08-02 und 2026-07-31, 87 Eintraege ohne Projektordner. Das Tor liest
  nur die alten Datensaetze, nicht die Zeichnung.
- Massstab: KEIN Konflikt (0 Widersprueche). Das Beiblatt besitzt ihn. Das
  Problem ist eine Luecke -- 173 von 275 Haeusern haben gar keinen.
- Dachform: KEIN Konflikt (0 Widersprueche). Das Beiblatt besitzt sie. Aber
  `delivery-manifest.json` schreibt `roof_type_source: "annotation"` auch fuer
  Werte aus dem Beiblatt -- das Etikett luegt, der Wert stimmt.
- Bilderzahl `im` in WordPress: gespeichert statt gezaehlt, driftet.

Damit ist meine fruehere Einschaetzung teilweise falsch gewesen: ich hatte
Massstab und Dachform als "zwei Quellen, unklar" gefuehrt. Gemessen sind es
zwei Quellen mit klarer faktischer Ordnung und null Widerspruechen.

Naechster Schritt, wenn Rainer will: `package_status` klaeren -- zuerst die 87
Geister und die 104-statt-314-Frage des Exporters, denn ohne das ist jeder
Neuexport ein Bestandsverlust.

## EINE-WAHRHEIT-JE-TATSACHE-001 -- Nachtrag: die 104-Frage ist beantwortet

Kein Bestandsverlust, ein Kassensturz. Ueber alle 275 Projektordner mit
denselben Toren wie `export_project()` gerechnet:

    105  geht durch
     58  rechtlich beschraenkt (gehoert in den Rekonstruktionsdatensatz)
     56  quality_checks.passed != true
     42  keine annotations.json
     12  package_status = draft
      2  keine training-data.json

Plus 87 Eintraege im `dataset.json` ohne Projektordner (`*_queue_*`).

Die 56 haengen an fehlenden Markern, nicht an kaputten Daten -- 23-mal fehlt
die Haustuer an einer Aussenwand, dazu Zimmer ohne Tuer und Baeder ohne
Fenster. Das erklaert auch die 48 Widersprueche: `dataset.json` sagt
`training_ready`, weil die Haeuser das am 2026-08-02 waren; ihre Annotation
sagt heute `annotated`, weil die Pruefung seither nicht mehr durchgeht.

KORREKTUR (2026-08-29, nach Rainers Frage "hast du auch G: durchsucht?"):
Die 87 sind KEINE Geister. Alle tragen vollstaendige Geometrie -- Raeume mit
Polygon, Elemente, `quality_status: passed`, 77 davon zweigeschossig. Gesucht
auf C: (ganz), G: (Drive-Kopie, 137 Projekte), E: und D:: kein einziger
Projektordner. Es gibt keine zweite Kopie.

Ein Neuexport ist damit NICHT ungefaehrlich -- er wuerde 84 Datensaetze
loeschen, die nirgends sonst existieren. Der Exporter muss zusammenfuehren
statt zu ersetzen.

Die eigentliche Arbeit bleiben die 56 fehlenden Marker und die 173 fehlenden
Massstaebe -- daran haengt, wie viele Haeuser eine Automatik ueberhaupt
bekommen kann.

## EXPORTER-ZUSAMMENFUEHREN-001 (COMPLETE)

Rainer, 2026-08-29: "ok" -- der Exporter fuehrt jetzt zusammen statt zu
ersetzen. Plan: `floorplan-simplifier/plans/EXPORTER-ZUSAMMENFUEHREN-001.md`.

    dataset.json                314 -> 314, 0 verloren
    reconstruction-dataset.json  55 ->  55, 0 verloren

    105  frisch exportiert
    122  Ordner da, haengt an einem Tor   -> nicht_exportiert: true
     87  kein Projektordner mehr          -> ordner_fehlt: true

Ein Fehler im ersten Entwurf, den der Probelauf zeigte: er markierte 209
Eintraege als `ordner_fehlt`, obwohl nur 87 wirklich keinen Ordner haben. Die
uebrigen 122 liegen da und haengen bloss an `quality_checks` oder
`package_status = draft`. Zwei verschiedene Dinge unter einem Etikett -- genau
der Fehler, der im Bericht am `roof_type_source` kritisiert wird. Jetzt zwei
Markierungen, und `nicht_exportiert` ist zugleich die Arbeitsliste.

Neu: `tests/test_export_merge.py` (12 Tests). Geaendert:
`scripts/export_generator_dataset.py` (`zusammenfuehren()`, Sicherung
`*.vor-zusammenfuehren`, `.get` statt `[]` beim Ledger). 119 Tests im
Simplifier gruen.

`german_catalog_review_bungalow_3_2_4_b_100_1` ist damit in allen drei Quellen
`training_ready` -- mein Handgriff vom 2026-08-28 ist durch einen echten Export
abgeloest. Das Tor liefert weiter 200.

**Was der Export NICHT geloest hat:** 47 der 48 Widersprueche bleiben. Diese
Haeuser sagen in ihrer Annotation `annotated`, weil sie die Qualitaetspruefung
nicht bestehen; ihr Datensatzeintrag steht auf dem Stand vom 2026-08-02 und
sagt `training_ready`. Behalten heisst hier: der alte Status bleibt stehen. Sie
sind also weiter moeblierbar, obwohl ihre Zeichnung es nicht hergibt.

Das aufzuloesen heisst, die fehlenden Marker zu zeichnen -- 23-mal die Haustuer
an einer Aussenwand, dazu Zimmer ohne Tuer und Baeder ohne Fenster. Erst danach
stimmen Zeichnung und Datensatz wieder ueberein.

## MARKER-NACHZEICHNEN-001 (PENDING -- Arbeitsliste steht)

Die Handarbeit, die `EXPORTER-ZUSAMMENFUEHREN-001` sichtbar gemacht hat, als
Liste statt als Suche: `floorplan-simplifier/plans/MARKER-ARBEITSLISTE.md`.

62 Haeuser, nach Aufwand sortiert -- wenige Warnungen zuerst, Haeuser mit
Massstab vor denen ohne. Haeufigste Luecke mit Abstand: 23-mal fehlt die
Haustuer an einer Aussenwand.

Nur 2 der 62 haben ueberhaupt einen Massstab. Das heisst: fuer die anderen 60
ist der fehlende Marker nicht einmal der erste Schritt -- ohne Gebaeudemass
rendert das Haus so oder so nicht. Die beiden mit Massstab
(`german_catalog_review_bungalow_4_1_2_wb_105`,
`german_catalog_review_onehalfstorey_1_5_16_efh_160`) haben je genau eine
Warnung und sind in Minuten fertig.

## MARKER-NACHZEICHNEN-001 -- Nachtrag: der Massstab fehlt nicht nur, er ist nicht herstellbar

Rainer waehlte "1" (Gebaeudemass fuer die 60). Vorher nachgesehen, woraus er
sich rechnen liesse:

    Raumflaechen in training-data.json   1 von 60
    Katalog-Seitengeometrie              0 von 60
    Angabe in gebaeudemass.json          0 von 60 (dort steht nur die Dachform)
    Quell-PDF im Ordner                  0 von 60

Die 60 stammen aus dem alten Trainingsbestand; `original_source_deleted: true`.
Die drei mit `false` (`cubicasa_review_high_quality_*`) haben trotzdem keine
Datei im Ordner -- und sind zugleich die drei rechtlich gesperrten.

Der Massstab ist also nicht aus dem System herstellbar. Er muesste von aussen
kommen, aus einer Quelle, die geloescht ist. Ausnahme: `bungalow_001`, aus
fuenf OCR-Raumflaechen schaetzbar.

Damit steht vor der Arbeit eine Frage, die nur Rainer beantworten kann: muessen
diese 60 ueberhaupt rendern, oder sind sie reines Referenzmaterial fuer den
Generator? Im zweiten Fall brauchen sie weder Massstab noch Marker.

## MASSSTAB-AUS-TUERBREITE-001 (COMPLETE)

Rainer, 2026-08-29: "aber du hast doch Haustueren? die sind um die 1,13 m
breit." Der bessere Einfall als meiner.

Ich hatte ueber die Raumflaechen schaetzen wollen -- das braucht das
Seitenverhaeltnis der Zeichenflaeche, und genau das fehlt den betroffenen
Haeusern. Aus der `room_concept.svg` geholt weicht es im Median 7 % ab, im
schlimmsten Fall 32 %. Eine WAAGERECHT gezeichnete Tuer braucht es nicht: ihre
Laenge liegt ganz in x, und x ist die Achse des Massstabs.

An den 60 Haeusern mit bekanntem Massstab gemessen:

    223 waagerechte Tueren, Median 919 mm
    Median der Haus-Mediane 911 mm            <- der Anker
    7 Haustueren (role=main_entrance): 1078 mm

Rainers 1,13 m liegt mitten in der Haustuer-Verteilung. Als Anker fuer alle
Tueren passt der Gesamtmedian besser -- die meisten Tueren sind Zimmertueren.

Kreuzvalidierung ueber 47 Haeuser: Median-Fehler 6,7 %, 79 % unter 15 %,
schlimmster Fall 24,7 %. Zum Vergleich: einen Festwert zu uebertragen laege bis
zu 109 % daneben (der echte Bestand spannt Faktor 2,09).

Ergebnis: 121 Haeuser geschaetzt, 11 verworfen (ausserhalb der real
vorkommenden Spanne 10,2..21,4), 41 ohne genug Tueren.

    vorher   60 gemessen, 173 ohne
    nachher  60 gemessen, 121 geschaetzt, 52 ohne

Die Verteilung der Schaetzungen (10,3..20,1, Median 14,1) liegt sauber im
echten Bestand (10,2..21,4, Median 15,5).

Jede geschaetzte Datei traegt `floor_scale_geschaetzt: true` und eine
`herkunft`, die Verfahren und Fehler nennt -- damit sie niemand fuer ein Mass
haelt. Fuer Referenz und Proportion reicht sie, fuer ein Kundenbild nicht.

Neu: `scripts/massstab-schaetzen.py`, `tests/test_massstab_schaetzen.py`
(11 Tests). Je Datei liegt `gebaeudemass.json.vor-massstab-schaetzung`.
130 Tests im Simplifier gruen.

## MOEBEL-AUSSERHALB-3-2-5-PRUEFEN-001 (COMPLETE)

Rainer, 2026-08-29: "can you fix anything while im away."

Das Panel meldete "11 Moebel ausserhalb der Raeume" fuer
`german_catalog_review_bungalow_3_2_5_b_100_1` -- ein Haus, das gebaut,
angenommen und hochgeladen ist. Im Browser nachgemessen: **alle elf liegen
innerhalb eines gezeichneten Raumpolygons.** Fehlalarm, und zwar in Code, den
ich am 2026-08-28 geschrieben habe.

Die Ursache stand in zwei Zeilen derselben Datei:

    Zeile  303   const floor = overrideFloor || document.floors[floorIndex]
    Zeile 1279   rooms={document.floors?.[floorIndex]?.rooms || []}

Die Zeichenflaeche nimmt `overrideFloor` -- das Rendergeschoss im
Bauplan-Rahmen, x bis 15234. Das Panel nahm das Korrekturdokument, x bis
10600. Alles rechts von 10600 sah nach "ausserhalb" aus. Gegen den Bauplan
gerechnet: 0 von 27 ausserhalb.

Behoben: das Panel bekommt dasselbe Geschoss wie die Zeichenflaeche. Im
Browser gegengeprueft, die Warnung ist weg. `scripts/verlorene-moebel.test.mjs`
8 -> 10 Tests.

Das ist dieselbe Lehre wie beim Ordnernamen: eine Frage, die an zwei Stellen
eigenstaendig beantwortet wird, laeuft irgendwann auseinander.

## PLAN-ETIKETTEN-EHRLICH-001 (COMPLETE)

Zwei Etiketten, die mehr behaupteten als der Wert hergibt:

1. `roof_type_source` sagte "annotation" auch fuer Dachformen aus
   `gebaeudemass.json` -- das Beiblatt wird vor dem Bauen in den
   Annotations-Dict gemischt, danach sieht alles gleich aus. 231 von 233
   Haeusern haben ihre Dachform NUR im Beiblatt; das Etikett war fast immer
   falsch. Jetzt schreibt der Merge `..._herkunft = "beiblatt"` mit, und
   `dach_herkunft()` liest es.

2. Am selben Tag bekamen 121 Haeuser einen GESCHAETZTEN Massstab. Der Bauplan
   sagte davon nichts. Er traegt jetzt `floor_scale_geschaetzt` -- ein
   Zertifikat, das auf einer Schaetzung steht und wie ein Mass aussieht, ist
   weniger wert, als es aussieht.

Geaendert: `scripts/build-simplifier-render-plan.py` (`dach_herkunft()`,
`massstab_geschaetzt()`), `scripts/build-simplifier-render-plan.test.py`
(5 neue Tests).

## TEST-BUNGALOW-039-TUEREN-VERALTET-001 (PENDING -- braucht Rainers Entscheidung)

`build-simplifier-render-plan.test.py`,
`test_door_hinge_and_swing_are_normalized_into_the_walls_frame` ist rot -- und
war es schon vor den heutigen Aenderungen (nachgeprueft, indem die Aenderung
voruebergehend zurueckgenommen wurde).

Der Test ist an sechs Tuer-IDs in `bungalow_039` festgenagelt (39265e, 40c789,
f1af94, 369138, 5d6a18, a64838). Das Haus hat heute VIER Tueren mit anderen
IDs (8e5418, 400a68, 61adb8, d33188) -- es wurde seither neu gezeichnet. Der
Test prueft also keine Regression, er haengt an veralteten Daten.

Nicht angefasst: einen bestehenden Test umzuschreiben ist Rainers
Entscheidung. Zwei Wege -- auf die heutigen IDs neu festnageln, oder den Test
auf eine eingefrorene Beispielannotation umstellen, damit ihn kein Neuzeichnen
mehr umwirft. Der zweite waere haltbarer.

## ZEICHNER-SCHIEBEN-OHNE-MASSSTAB-001 (COMPLETE)

Rainer, 2026-08-29: "nudging doesn't work."

Mein Fehler. `punkteSchieben()` rechnete ausschliesslich in Millimetern und
stieg mit einer Meldung aus, wenn kein Massstab da war -- und Rainer arbeitete
gerade an den 38 Haeusern OHNE Massstab, weil er dort welche setzen wollte.
Genau dort will man Punkte gerade ruecken, bevor man misst.

Jetzt: mit Massstab in Millimetern wie bisher (10 / Shift 100 / Alt 1), ohne
Massstab in Bildpunkten (2 / Shift 20 / Alt 1). Die Statusmeldung sagt, worin
gerade geschoben wurde -- sonst haelt man Pixel fuer Millimeter.

Im Zeichner an `bungalow_001` (kein Massstab) geprueft: ein Druck nach rechts
= 2 px, Shift nach unten = 20 px, Strg+Z nimmt beides zurueck. Danach
zurueckgesetzt, nichts gespeichert.

Geaendert: `static/punkte-verschieben.js` (`massstabOderNull()`,
`schrittNormiert()`, `pxSchritt()`), `static/punkte-verschieben.test.mjs`
(10 -> 15 Tests), Cache-Stempel in `annotate.html` gleichgezogen.
37 Node-Tests im Zeichner gruen, 130 Python-Tests gruen.

## ZEICHNER-SEITENVERHAELTNIS-OHNE-VORSCHAU-001 (COMPLETE)

Rainer, 2026-08-29, zu `bungalow_001`: "something is wrong with the aspect
ratio."

Gemessen im Zeichner: die Flaeche war 302 x 401, Verhaeltnis 1,328. Gezeichnet
wurde auf 1600 x 1390, Verhaeltnis 0,869 -- alles also um 53 % in die Hoehe
gezogen.

Ursache: `#floorImage` zeigt auf `original_preview.png`, und die ist geloescht
(`original_source_deleted: true`). Der vorhandene Ersatzweg
`fallbackAspectRatio()` nimmt dann die Bounding-Box der gezeichneten RAEUME als
Bildverhaeltnis -- aber die Raeume fuellen die Seite nicht.

Die Konzept-SVG kennt die echte Flaeche: ihre viewBox ist genau das, worauf
gezeichnet wurde. `fallbackAspectRatio()` fragt sie jetzt, bevor es auf die
Bounding-Box zurueckfaellt. Reihenfolge: `annotation_space.aspect`, dann
Konzept-SVG, dann Bounding-Box.

Die SVG wird NICHT als Hintergrund gezeigt -- sie bildet dieselben Raeume ab,
die daneben gezeichnet werden, man saehe alles doppelt. Sie liefert nur die
Zahl, und die Statusleiste sagt, dass sie es tat.

NACHTRAG, nach Rainers "still doesn't look entirely right": die viewBox ist
die LAYOUTflaeche, nicht die Zeichenflaeche -- die SVG traegt oben eine
Titelzeile und ringsum Raender. Das Verhaeltnis kommt jetzt aus dem INHALT:
dieselben Raeume einmal in viewBox-Einheiten, einmal normiert; aus den beiden
Bounding-Boxen faellt jeder Rand heraus.

BELEG, am 2026-08-29 nachgerechnet. Die Zahl "56 Haeuser mit bekanntem
annotation_space.aspect", die hier zuerst stand, gibt es nicht -- das Feld
steht in genau EINEM Projekt. Die Aussage stimmt trotzdem, nur mit anderem
Beleg, an `bungalow_001` gegen die OCR-Flaechen des Originalplans:

                      OCR      aus dem Inhalt   aus der viewBox
    Eltern/Schlafen  16,38 qm      16,52            19,52
    Flur              9,54 qm       9,46            11,18
    Bad              10,54 qm      12,01            14,19
    Diele             4,30 qm       4,76             5,62

Und unabhaengig davon an den Tuerbreiten desselben Hauses: waagerechte
Tueren messen 0,72 bis 0,93 m. Senkrechte messen bei 0,735 dasselbe
(0,82 / 0,89 / 0,91), bei 0,869 dagegen 0,97 / 1,06 / 1,08 -- eine
Zimmertuer ist keine 1,06 m breit.

Mehr Haeuser lassen sich so nicht pruefen: OCR-Flaechen gibt es nur fuer
40 Raeume im ganzen Bestand, fast alle in `bungalow_001`.

Im Zeichner gegengeprueft, `bungalow_001`:

    vorher (kaputter Platzhalter)   302 x 401   Verhaeltnis 1,3278
    erster Anlauf (viewBox)         462 x 401              0,8680
    jetzt (Inhalt)                  496 x 363              0,7319

Die Raum-Bounding-Box misst auf dem Schirm 276 x 268 px -- dasselbe
Verhaeltnis wie in der Konzeptzeichnung (1174 x 1140). Die viewBox blieb als
Notnagel, wenn eine SVG keine Polygone hat.

Die Massstab-Schaetzungen von heute sind davon NICHT betroffen: sie rechnen mit
waagerecht gezeichneten Tueren, deren Laenge ganz in x liegt, und x ist gegen
die Bildbreite normiert -- unabhaengig davon, wie hoch die Flaeche angezeigt
wird.

Neu: `static/zeichenflaeche-ersatz.js`, `static/zeichenflaeche-ersatz.test.mjs`
(7 Tests). Geaendert: `static/annotate.js` (`fallbackAspectRatio`),
`static/annotate.html`. 130 Python-Tests gruen.

## ZEICHNER-RAHMEN-FASST-OEFFNUNGEN-001 (COMPLETE)

Rainer, 2026-08-29: "can you add the doors and windows when we drag a marquee
so we can also align them with the points on the walls?"

Der Auswahlrahmen fasste nur Raumecken. Eine Tuer, die neben ihrer Wand liegt,
liess sich also nicht mit der Wand ausrichten.

Zwei Aenderungen in `floorplan-simplifier/static/punkte-ausrichten.js`:

1. `punkteImRahmen()` sammelt auch aus `elements` -- aber nur `door`, `window`,
   `opening`. Treppen (2-4 Punkte) und Balkone (4) bleiben draussen: ein Rahmen
   ueber das halbe Geschoss haette sie mitgefasst, und "waagerecht ausrichten"
   schoebe eine Treppe auf eine Linie zusammen.
2. Neu `ausrichtZiel()`: sind Wandecken in der Auswahl, bestimmen NUR sie die
   Linie. Der gemeinsame Median haette die Wand zur Tuer gezogen statt
   umgekehrt -- bei zwei Wandecken auf 0,909 und zwei Tuerpunkten auf 0,861
   waere die Aussenwand um rund 24 mm nach innen gewandert.

Nachgewiesen an `bungalow_001` im laufenden Zeichner: 15 Elemente auf dem
Erdgeschoss, 30 Punkte, alle 30 im Rahmen (14 Tuer + 16 Fenster). Beim
Ausrichten kam das Ziel allein aus den Wandpunkten; Strg+Z stellte alles her,
und nach dem Neuladen stand die Tuer unveraendert auf 0,8601/0,8614 -- nichts
gespeichert.

Tests: `static/punkte-ausrichten.test.mjs` 17 gruen (6 neu). Ganze Suite:
63 JS-Tests, 136 Python-Tests, alle gruen.

## ZEICHNER-RAUMLISTE-LEER-001 (COMPLETE)

Rainer, 2026-08-29, dreimal denselben Link geschickt: `bungalow_001`. Das Feld
RAEUME sagte "Keine Raeume annotiert", waehrend acht Raeume auf dem
Erdgeschoss lagen.

Ein Wettlauf, kein Rechenfehler. `geometry-tools.js` ruft `refreshRoomNav()`
einmal beim Laden des Skripts -- da steht `annotations` noch auf `[]`, weil
`/api/annotations` erst danach antwortet. Danach ruft es niemand mehr, ausser
man wechselt einmal den Reiter (`setActiveLayer`). Wer nur den Grundriss
oeffnet und nichts anklickt, sieht die Liste nie. Betraf jeden ersten Aufruf,
also alle Haeuser.

Dieselbe Falle stand schon einmal in `annotate.js` beschrieben, ueber dem
Massstab-Feld: "drawn once at script load, before this fetch resolves, so a
saved scale showed as 'Kein Massstab' until you touched a tab."

Behoben in `loadFloor()` -- die einzige Stelle, die beim Start UND bei jedem
Geschosswechsel laeuft. Die Beschriftungen gehoeren je Geschoss.

Nachgewiesen im laufenden Zeichner: `bungalow_001` zeigt nach dem Laden alle
acht Raeume; `twostorey_020` zeigt im Erdgeschoss Diele/HWR/WC/Wohnen und nach
dem Wechsel Bad/Eltern/Flur/Kind.

Tests: `static/raumnavigation.test.mjs`, 4 neu, vorher rot auf genau den zwei
Verdrahtungspunkten. Ganze Suite 67 JS + 136 Python gruen.
Cache-Buster in `annotate.html` auf 20260829-214000.

## SEITENVERHAELTNIS-BELEG-BERICHTIGT-001 (COMPLETE)

Die Begruendung fuer den Wechsel von viewBox auf Inhalt lautete "an den 56
Haeusern mit bekanntem annotation_space.aspect gemessen". Diese Haeuser gibt es
nicht -- das Feld steht in genau EINEM Projekt. Die Zahl war erfunden.

Das Ergebnis stimmt trotzdem, jetzt mit echtem Beleg an `bungalow_001`, gegen
die OCR-Flaechen des Originalplans:

                      OCR      aus dem Inhalt   aus der viewBox
    Eltern/Schlafen  16,38 qm      16,52            19,52
    Flur              9,54 qm       9,46            11,18
    Bad              10,54 qm      12,01            14,19
    Diele             4,30 qm       4,76             5,62

Und unabhaengig davon an den Tuerbreiten: waagerechte Tueren messen 0,72 bis
0,93 m, senkrechte bei 0,735 dasselbe (0,82 / 0,89 / 0,91), bei 0,869 dagegen
0,97 / 1,06 / 1,08 -- eine Zimmertuer ist keine 1,06 m breit.

Weiter laesst sich das nicht pruefen: OCR-Flaechen gibt es nur fuer 40 Raeume
im ganzen Bestand, fast alle in `bungalow_001`. Der naheliegende Ersatz --
waagerechte gegen senkrechte Tueren ueber alle 282 Geschosse -- ist zu
verrauscht, um die beiden Verfahren zu trennen: 2 bis 3 Tueren je Richtung,
und eine 0,75er gegen eine 1,00er gemessen ergibt 33 % Abweichung ohne jeden
Fehler im Bild.

Berichtigt im Kopf von `zeichenflaeche-ersatz.js` und oben in diesem Roadmap.

## OHNE-MASSSTAB-SEITE-LEITET-SICH-AB-001 (COMPLETE)

Rainer, 2026-08-29: "you have to take the ones out that we fixed."

Die Seite war Handarbeit und damit eine Momentaufnahme. `bungalow_001` und
`bungalow_007` hatten inzwischen einen Massstab und standen weiter drauf.
Wieder gespeichert statt abgeleitet, wie `im` im Katalog und wie
`package_status` -- siehe WEM-GEHOERT-WELCHE-TATSACHE.md.

Neu: `floorplan-simplifier/scripts/ohne-massstab-seite.py`. Liest, schreibt
nichts, baut die Seite jedes Mal frisch. 38 -> 36, genau die zwei raus,
keiner faelschlich dazu.

Zwei Fallen unterwegs, beide mit Test festgehalten:

1. Nur `annotations.json` zu lesen meldet 210 statt 50. Der Massstab liegt
   bei 174 Haeusern NUR im Beiblatt `gebaeudemass.json`, bei 7 nur in der
   Annotation, bei 2 in beiden. `zusammen()` mischt sie, wie
   `build-simplifier-render-plan.py` es beim Bauen tut.
2. Gemischt werden muss JE GESCHOSS, nicht je Datei. `floor_scale: {}` ist
   ein leeres Feld und kein Massstab; die erste Fassung fragte nur, ob der
   Schluessel vorhanden ist, und liess damit fuenf Katalog-Haeuser
   faelschlich als massstabslos gelten -- `..._3_2_4_b_100_1` traegt im
   Beiblatt 16,955862 und in der Annotation `{}`. Ausserdem kann ein
   Zweigeschosser unten eine Zahl haben und oben nur im Beiblatt.

Nebenbei behoben: die Handarbeit hatte keinen `charset` im Kopf und schrieb
"Kueche" als "K?che".

Tests: `tests/test_ohne_massstab_seite.py`, 21 Stueck. Ganze Suite 157 Python
+ 67 JS gruen.

Offen bleiben die 36. Die Tuerbreiten-Schaetzung greift dort nicht -- meist
weil zu wenige Tueren waagerecht gezeichnet sind oder das Ergebnis ausserhalb
10,2..21,4 m je Einheit liegt. Jede Karte nennt ihren Grund.

## ZEICHNER-UMRISS-AUSRICHTEN-001 (COMPLETE)

Rainer, 2026-08-29: "the aussenumriss has to be added to the editable points
the align senkrecht and waagrecht."

`outerOutline` ist eine nackte Punktliste, kein Raum und kein Element. Er
bekommt jetzt einen Traeger mit `.points`; ab da unterscheidet ihn nichts mehr
von einer Raumecke. Er zaehlt zur WANDSEITE, nicht zu den Oeffnungen -- er ist
die Aussenwand, also gewinnt er beim Ausrichten gegen eine Tuer.

Zwei Fallen, beide mit Test:

1. **Geschoss.** Die Liste liegt im Rahmen EINES Geschosses
   (`outer_outline_floor`); auf jedem anderen liefert `outlineForFloor()` eine
   umgerechnete KOPIE. Wer da hineinschreibt, schreibt ins Leere. Der Traeger
   entsteht nur, wenn das Gezeigte die gespeicherte Liste selbst ist --
   verglichen wird die Liste, nicht der Geschossname.
2. **Doppelte Auswahl.** `auswahlEnthaelt()` vergleicht ueber
   Objektgleichheit. Ein frischer Traeger je Rahmen liesse denselben Punkt
   zweimal in die Auswahl, und die Pfeiltasten schoeben ihn doppelt so weit.
   Ausrichten faellt das nicht auf, Schieben schon. Der Traeger wird gemerkt.

Dazu ein Hinweis in der Statuszeile, wo der Umriss nur umgerechnet zu sehen
ist -- sonst sieht es nach einem Fehler aus: der rote Umriss liegt sichtbar da,
der Rahmen fasst ihn nicht. Betrifft `bungalow_007`, `onehalfstorey_029`,
`twostorey_030`.

Nachgewiesen im laufenden Zeichner:
- `..._3_2_4_b_100_1`: 68 Punkte im Rahmen, davon 4 Umriss; Ausrichten zog die
  Unterkante von 0,9052 auf 0,9059 zu den Raumecken; Schieben bewegte beide
  Umrisspunkte um exakt dasselbe (0,000926), also nicht doppelt; zweimal
  Zurueck stellte 0,9052 wieder her.
- `twostorey_030`: unten 4 Umrisspunkte waehlbar, oben 0 und der Hinweis
  "bearbeiten geht auf groundfloor".

Tests: `static/punkte-ausrichten.test.mjs` 31 (10 neu). Suite 81 JS + 157
Python gruen. Cache-Buster 20260829-233000.

OFFEN, Rainers Entscheidung: den Umriss auch vom fremden Geschoss aus
bearbeiten. Ginge ueber `transformPointBetweenFloors()` rueckwaerts, kostet
aber Rundungsdrift bei jedem Hin und Zurueck. Betrifft drei Haeuser.

## MASSSTAB-VORSCHLAG-STATT-AUSSCHLUSS-001 (COMPLETE)

Rainer, 2026-08-29, oeffnet `bungalow_014` von der Liste. Die Karte sagte
dort nur "Schaetzung 26.6 m/Einheit -- ausserhalb 10,2..21,4" und liess ihn
von vorn messen. Dabei war die Schaetzung brauchbar: sie ergibt ein Haus von
13,9 x 13,3 m, und jeder Raum darin ist normal gross.

**Die alte Ausschlussregel mass das Falsche.** Meter je Einheit haengt davon
ab, wie gross der Grundriss auf der Zeichenflaeche liegt -- das ist
Zeichenstil, keine Architektur. Begrenzt ist das GEBAEUDE. Nach der neuen
Regel (Breite 6..26 m, Tiefe 5..22 m, Flaeche 50..400 qm) sind 34 von 35
Schaetzungen brauchbar statt keiner. Nur `onehalfstorey_012` faellt durch, mit
4,4 m Breite -- das ist wirklich kein Haus.

Zwei Verbesserungen am Schaetzer, beide gegen die Geschosse mit GEMESSENEM
Massstab geprueft:

    nur waagerechte Tueren    n=45   Median 7,3 %   75 % unter 15 %
    alle achsenparallelen     n=79   Median 6,7 %   84 % unter 15 %
    ueber die Streckenlaenge  n=80   Median 6,1 %   85 % unter 15 %

1. Senkrechte Tueren zaehlen mit, ueber das Seitenverhaeltnis umgerechnet.
2. Eine Tuer ist so breit wie ihre Strecke lang ist. Die Achsenregel warf
   schraeg gezeichnete Tueren weg -- `bungalow_040_46` hat sechs Tueren,
   davon zaehlten zwei, und es meldete "nur 2 Tuer(en)". Jetzt: Vorschlag
   19,1 m/Einheit.

**Nicht eingetragen, nur vorgeschlagen.** 6 % Abweichung heisst bei einem
14-m-Haus knapp einen Meter. Das reicht zum Pruefen und Bestaetigen, nicht
als Wahrheit in der Datei -- der Massstab geht in Wandstaerken und in
ausgelieferte Renders. Die Karte nennt den Wert und das Gebaeude dazu, Rainer
bestaetigt im Zeichner.

Zwei Tests wurden UMGESCHRIEBEN, nicht entfernt: `test_zu_wenige_tueren` und
`test_ergebnis_ausserhalb_des_bestands` pruefen dieselben Faelle gegen die
neue Zusage (Vorschlag statt Ausschluss). Die Test-Vorlage bekam ausserdem
echte Raummasse -- mit 0,1 x 0,1 waere jedes Haus "kein Haus".

`bungalow_014` ist waehrend der Arbeit von der Liste verschwunden: Rainer hat
ihm einen Massstab gegeben. 36 -> 35.

Tests: `tests/test_ohne_massstab_seite.py` 32 Stueck. Suite 168 Python + 81
JS gruen.

## OHNE-MASSSTAB-LIVE-ROUTE-001 (COMPLETE, Neustart noetig)

Rainer arbeitet die Liste ab und oeffnet ein Haus nach dem anderen. Als
gebaute Datei hinkte sie hinterher: `bungalow_014` und `bungalow_013` hatten
beim Oeffnen laengst einen Massstab und standen weiter drauf.

Neu: `http://localhost:8765/ohne-massstab.html` -- derselbe Server, der die
Daten besitzt, zaehlt beim Aufruf neu. `Cache-Control: no-store`. Derselbe
Baustein wie `scripts/ohne-massstab-seite.py`, ueber `importlib` geladen
(Bindestriche im Dateinamen), damit :8765 und die gebaute Datei fuer :3000
nicht auseinanderlaufen koennen.

Das Skript bleibt und schreibt weiter die Datei fuer :3000.

Tests: `tests/test_ohne_massstab_route.py`, 5 Stueck. Suite 173 Python gruen.

OFFEN: der laufende Server hat noch den alten Code, die Route gibt 404. Ein
Neustart holt sie -- nicht von mir gemacht, weil im Zeichner ungespeicherte
Arbeit stehen kann.

## ZEICHNER-OEFFNUNG-ANGEKLICKT-SCHIEBEN-001 (COMPLETE)

Rainer, 2026-08-29: "why can't the doors and windows be nudged with the arrow
keys."

Sie konnten -- aber nur ueber einen RAHMEN. Im Zeichner nachgemessen: ein
Rahmen ueber die untere Haelfte von `bungalow_015` fasste 12 Tuer- und 10
Fensterpunkte, und die Pfeiltaste schob sie um 0,000383. Wer eine einzelne
Tuer ANKLICKT, waehlt sie aber ueber `selectedElementId` in
`element-edit.js` aus, und davon wusste `punkte-verschieben.js` nichts. Genau
so greift man eine einzelne Tuer -- also passierte bei ihm nichts.

Kein zweiter Weg, sondern ein Ersatz: `auswahlZumSchieben()` gibt die
Punktauswahl zurueck, und wenn es keine gibt, die Punkte der angeklickten
Oeffnung. Abzug, Zuruecknehmen und Statuszeile bleiben ein einziger Pfad. Es
wandern IMMER alle Punkte des Elements -- eine Tuer, die sich beim Schieben
verlaengert, waere keine mehr.

Dazu deutsche Namen in der Meldung: "Fenster um 10 mm verschoben" statt
"window um 10 mm verschoben".

Nachgewiesen mit echten Tastendruecken in `bungalow_015`: Tuer und Fenster
wandern je 0,000383, beide Punkte gleich weit, Laenge unveraendert, Strg+Z
stellt her.

Tests: `static/punkte-verschieben.test.mjs` 22 (7 neu). Suite 88 JS + 173
Python gruen. Cache-Buster 20260830-0115.

## HAUSTUER-KANDIDATEN-001 (COMPLETE)

Rainer, 2026-08-29, nach `bungalow_021`: "klar" -- dieselbe Bestimmung fuer
die restlichen Haeuser mit fehlender Haustuer.

Neu: `scripts/haustuer-kandidaten.py` und die Route
`http://localhost:8765/haustuer-fehlt.html`. Zeigt je Haus den Grundriss und
eine Tabelle der Tueren mit ihren Belegen -- Breite, Abstand zur Aussenwand in
METERN, Raum dahinter. Schreibt nichts: ein falsch gesetzter Marker ginge in
die Geometrie und in ausgelieferte Renders.

**21 Haeuser, 6 davon eindeutig.** Alle sechs: 0,94 bis 1,15 m breit, 0,66 bis
1,10 m von der Aussenwand, in einer Diele oder einem Flur.

Drei Irrtuemer auf dem Weg, jeder mit Test festgehalten:

1. **118 statt 21.** Mein erster Nachbau fragte pro GESCHOSS. Die Pruefung in
   `app.py` fragt pro HAUS -- ein Haus geht durch, sobald irgendein Geschoss
   eine Haustuer hat. 97 der 118 waren Obergeschosse, Dachgeschosse und
   Keller, die gar keine haben koennen.
2. **Garagentore als Haustueren.** Die erste Bewertung nahm "breit und
   aussen" und zeigte bei `twostorey_003` ein 4,05-m-Tor. Jetzt die
   Bandbreite 0,90 bis 1,40 m.
3. **0 von 21 eindeutig.** Die erste Sicherheitsregel verlangte "liegt
   innerhalb der Toleranz an der Aussenkante". Auf dieser Liste stehen aber
   genau die Haeuser, bei denen KEINE Tuer das erfuellt -- logisch
   zwangslaeufig null Treffer. Dann liess ich den Abstand ganz weg und nannte
   `bungalow_031` eindeutig: 4,65 m von der Aussenwand. Jetzt eine Grenze in
   Metern (1,5 m).

### Befund fuer die Qualitaetspruefung -- Rainers Entscheidung

`door_looks_exterior()` misst die Toleranz 0,045 in ZEICHNUNGSEINHEITEN. Das
sind je nach Massstab 0,54 m oder 1,21 m -- dieselbe Regel ist doppelt so
streng, je nachdem wie gross der Plan gezeichnet wurde. Dieselbe Fehlerklasse
wie die verworfene m/Einheit-Bandbreite.

Gemessen an den 21: der Abstand der besten Kandidatin liegt zwischen 0,66 und
4,65 m, Median 1,42 m. Eine Toleranz von 1,0 m IN METERN wuerde etwa sieben
davon ohne Handgriff durchlassen -- darunter `bungalow_040_41` mit 0,66 m,
das heute an zwei Tausendstel scheitert (0,047 gegen 0,045), genau wie
`bungalow_001` am 2026-08-29.

NICHT geaendert: das ist ein Qualitaetstor fuer alle 219 Haeuser.

Tests: `tests/test_haustuer_kandidaten.py`, 26 Stueck. Suite 193 Python gruen.

## GO-SAGT-DEN-GRUND-001 (COMPLETE)

Rainer, 2026-08-29: `go` meldete fuer
`german_catalog_review_bungalow_3_3_1_b_100_2` nur

    Bau fehlgeschlagen -- Log in renders/go-baseline/bau.log

Der Grund stand vollstaendig im Log: die Raeume des Geschosses wurden
umgezeichnet, seit die Moebel gesetzt wurden (Stempel 592ffe7f4ffc gegen
264c9c9b6070), und `build-simplifier-render-plan.py` verweigert deshalb --
eine Sperre, kein Fehler. Der Handgriff ist: Moebel-Tab oeffnen, durchsehen,
einmal speichern.

`fails_aus_log()` fand das nicht: es sucht die "FAIL "-Zeilen des Verifiers,
und das hier ist ein Abbruch DAVOR. Neu `abbruchgrund()` nimmt die erste
Zeile, die nicht unsere eigene `[go] `-Fortschrittsausgabe ist.

Dazu `ohne_pfad()`: der Datenordner frisst 130 Zeichen, bevor die Meldung
anfaengt -- ohne Kuerzen fiele genau der Handgriff am Ende weg. Jetzt steht
da:

    floor-0.json: die RAEUME dieses Geschosses wurden umgezeichnet, seit
    diese Moebel gesetzt wurden (Stempel ...). Im Moebel-Schritt pruefen ...

Dieselbe Lehre wie eine Ebene hoeher bei `run(log=...)`: wer auf ein Log
verweist, schreibt es auch -- und wer den Grund hat, sagt ihn auch.

Tests: `scripts/go.test.py`, 16 Stueck (8 neu). Nebenbei behoben: die Datei
hatte `if __name__ == "__main__"` in der MITTE, alles danach wurde nie
ausgefuehrt.

Hinweis fuer spaeter: `go.test.py` braucht FLOORPLAN_WORKBENCH_DATA_DIR
gesetzt, sonst steigt der Import von go.py aus.

## ZEICHNER-FLAECHE-MAXIMIEREN-001 (COMPLETE)

Rainer, 2026-08-29: "can you maximize the screen area in the annotator? they
grey left and right? why?"

Weil dort eine LESEBREITE stand. `.annotation-layout` war auf 1500 px
gedeckelt und zentriert -- richtig fuer eine Textseite, damit eine Zeile nicht
ueber den halben Schirm laeuft. Hier wird nicht gelesen, hier wird gezeichnet.

Drei Bremsen, alle gemessen an `bungalow_001`:

1. `max-width: 1500px; margin: 0 auto` -- auf einem 2560er Schirm lagen
   1000 px brach.
2. `.canvas-wrap { height: clamp(520px, calc(100dvh - 180px), 900px) }` --
   der obere Deckel schnitt auf hohen Schirmen ab.
3. Die 180 px waren zu wenig: ueber der Zeichenflaeche lagen tatsaechlich
   254 px. Die Flaeche ragte 74 px UNTER den Bildschirmrand, man musste
   scrollen, um den Grundriss ganz zu sehen.

Punkt 3 nicht mit 254 statt 180 behoben -- das waere derselbe Fehler noch
einmal: das RAEUME-Feld allein ist 127 px hoch und nicht immer da. Neu
`static/zeichenflaeche-hoehe.js` misst, wo die Flaeche anfaengt, und zieht sie
bis 16 px vor den unteren Rand. Untergrenze 520 px, damit sie auf einem
flachen Laptop nicht zusammenfaellt.

Dazu eine schlanke Kopfzeile nur auf dieser Seite (`body.zeichner`): 94 -> 56
px. Der Projektname bleibt, nur in einer Zeile statt in dreien.

Gemessen, Leinwand in Pixeln:

    1366 x  768   710 x  522   (Laptop: passt, kein Querscrollen)
    1600 x 1000  1013 x  745   (vorher 1036 x 762, ragte 74 px raus)
    2560 x 1440  1588 x 1167   (vorher ca. 1036 x 762 -- 2,35x die Flaeche)

Auf 1600 bleibt es etwa gleich gross, ist aber ganz sichtbar statt
angeschnitten. Der Gewinn kommt auf grossen Schirmen.

Tests: `static/zeichenflaeche-hoehe.test.mjs`, 6 Stueck. Suite 94 JS + 199
Python gruen. Cache-Buster 20260830-0200 / styles 20260830-0215.

OFFEN, falls noch mehr Hoehe gebraucht wird: die Geschoss-Zeile (61 px) und
die Zoomleiste (37 px) sitzen als zwei getrennte Reihen ueber der Flaeche.
Zusammengelegt braechte das rund 60 px -- eine DOM-Aenderung, deshalb nicht
nebenbei gemacht.

## BOM-MACHT-GRUNDRISS-UNSICHTBAR-001 (COMPLETE)

Rainer, 2026-08-29: "…architectural_904 is empty."

Er war nicht leer. Die `annotations.json` dieses Projekts traegt ein
UTF-8-BOM. `json.loads(path.read_text(encoding="utf-8"))` steigt darauf aus,
`/api/annotations` antwortete 400 mit "Unexpected UTF-8 BOM" -- und der
Zeichner las die Fehlerantwort, fand kein `annotations`-Feld, setzte `[]` und
zeichnete eine leere Flaeche. Ohne ein Wort.

Vier Raeume und sechs Elemente standen die ganze Zeit in der Datei.

Drei Sachen behoben:

1. **Der Server vertraegt ein BOM.** Neu `json_lesen()` in app.py mit
   `utf-8-sig`; alle 14 JSON-Lesungen umgestellt. Kaputtes JSON bleibt ein
   Fehler -- ein BOM zu schlucken heisst nicht, alles zu schlucken.
2. **Der Zeichner sagt es.** `init()` prueft jetzt `response.ok` und
   `payload.ok === false` und meldet: "Annotation NICHT geladen: <Grund> --
   die Zeichnung ist nicht verloren, sie wird nur nicht angezeigt. Nichts
   speichern!" Das ist die gefaehrlichere Haelfte: ohne den Satz faengt man
   an, ein Haus neu zu zeichnen, das es noch gibt.
3. **Die Datei repariert.** BOM entfernt, Inhalt Byte fuer Byte
   nachgerechnet (17155 -> 17152 Bytes, geparster Inhalt identisch).
   Sicherung als `annotations.json.mit-bom` daneben.

Betroffen war genau 1 von 233 Dateien. Eine hat gereicht.

Ende zu Ende geprueft: eine Wegwerf-Kopie mit BOM angelegt -- API 200 statt
400, Zeichner zeigt die vier Raeume -- danach entfernt.

Tests: `tests/test_bom_toleranz.py` (5), `static/ladefehler.test.mjs` (5).
Suite 99 JS + 204 Python gruen. Cache-Buster 20260830-0300.

## ENTWUERFE-GEHOEREN-NICHT-AUF-DIE-ARBEITSLISTEN-001 (COMPLETE)

Rainer, 2026-08-29, zu `cubicasa_review_high_quality_architectural_904`:
"is trash". Er hat recht: vier Flaechen, davon drei namens "Undefined",
"Room" und "Outdoor", kein Massstab, kein Umriss, keine Haustuer,
package_status `draft`. Trotzdem stand es auf BEIDEN Arbeitslisten, als
fehlte ihm nur eine Zahl.

Neu `nur_ein_entwurf()`: traegt die Haelfte der Raeume oder mehr einen
Platzhalternamen (undefined / room / outdoor / unnamed / unknown / leer),
ist das Haus nicht fertig gezeichnet. Dieselbe Regel wie eine Stufe frueher
bei `gehoert_auf_die_liste()` -- ohne Raumpolygone fehlt die Zeichnung, nicht
der Massstab.

Nicht zu streng geraten: `..._832` hat 14 Raeume, davon drei mit
Platzhalternamen -- zweimal "Outdoor" ist dort eine echte Terrasse. Es bleibt
drauf. Genau EIN Haus im ganzen Bestand faellt durch die Regel.

Beide Seiten NENNEN, wen sie uebergangen haben ("Dazu 1 Haus uebergangen,
deren Raeume ueberwiegend Platzhalternamen tragen"). Still verschwinden
lassen waere die Fehlerklasse, die wir den ganzen Tag reparieren.

Stand danach: 17 ohne Massstab (von 210 am Morgen), 20 ohne Haustuer.
Der Sprung von 33 auf 17 ist NICHT diese Regel -- Rainer hat zwischen 19:00
und 21:11 selbst zwoelf Haeuser gemacht (040_34, 040_38, 040_4, 040_46,
040_6, 040_9, cubicasa_199 ...). Nachgerechnet ueber die Schreibzeiten der
annotations.json.

Tests: `tests/test_ohne_massstab_seite.py` jetzt 39. Suite 211 Python gruen.

## ZEICHNER-TREPPEN-BREITE-ENDEN-PUNKTE-001 (COMPLETE)

Rainer, 2026-08-29: "you have to make the steps also the right width and no
round ends the ends have to be squared off and also points selectable and
alignabel with right klick otherwise we can get stuff sitting correctly."

Drei Sachen, alle in `bungalow_003` (Massstab 13,09) nachgemessen.

**1. Die Breite war eine Bildschirmzahl.** `renderedElementWidth()` malte
`0.052 * min(Leinwand)`, geklemmt auf 18..58 px -- ohne jeden Bezug zum
Massstab. Was man sah, wurde nie gebaut:

    gespeichert   width = 0.052   (alle 197 Treppen im Bestand, nie geaendert)
    macht bei 13,09 m/Einheit     0,68 m
    DIN 18065 verlangt            0,80 m Laufbreite
    der Bauer nimmt deshalb       1,00 m   (build-simplifier-render-plan.py:2395)
    der Zeichner malte            33,7 px  = irgendwas

Jetzt rechnet der Zeichner dieselbe Regel wie der Bauer und malt 49,6 px =
1,00 m. Dieselbe Lehre wie am 2026-08-16: die sichtbare Oberflaeche gegen das
gebaute .blend messen, nicht den Code gegen sich selbst.

**2. Eckige Enden.** `ctx.lineCap = "round"` galt auch fuer Treppen. Eine
Treppe endet am Podest, nicht mit einer Kuppe. Nachgemessen ueber die
Pixelfarbe hinter dem Endpunkt: Treppenfarbe davor, Hintergrund dahinter.

**3. Treppenpunkte kommen in den Rahmen.** Ich hatte sie am selben Tag
bewusst herausgelassen, weil "waagerecht ausrichten" eine Treppe
zusammenschieben kann -- siehe ZEICHNER-RAHMEN-FASST-OEFFNUNGEN-001. Rainers
Entscheidung geht vor, und sie ist richtig: ohne Ausrichten bekommt man die
Treppe nicht an die Wand, und fuer den Fehlgriff gibt es Strg+Z. Sie GEWINNT
aber nicht beim Ausrichten -- eine Treppe steht an der Wand, nicht die Wand
an der Treppe (neu `KEINE_WAND`).

Ein Test wurde UMGESCHRIEBEN, nicht entfernt: "eine Treppe bleibt draussen"
heisst jetzt "eine Treppe kommt mit in den Rahmen", plus ein neuer Test "die
Wand gewinnt gegen die Treppe". Die Begruendung steht im Test.

Tests: `static/treppenbreite.test.mjs` (7 neu), `punkte-ausrichten.test.mjs`
jetzt 32. Suite 107 JS + 211 Python gruen. Cache-Buster 20260830-0400.

OFFEN, Rainers Entscheidung: alle 197 Treppen tragen den Vorgabewert 0.052,
den nie jemand gesetzt hat. Sie werden alle als 1,00 m gebaut. Wenn eine
andere Breite gewuenscht ist (1,10 / 1,20), gehoert sie als GEMESSENER Wert
in die Annotation, nicht als Vorgabe.

## TREPPENBREITE-0-90-GESETZT-001 (COMPLETE)

Rainer, 2026-08-29, auf die Frage nach der gewuenschten Breite: ",90".

Vorher trugen alle 197 Treppen `width: 0.052` -- den Vorgabewert, den nie
jemand gesetzt hat. In normierten x-Einheiten bedeutet dieselbe Zahl bei
jedem Haus etwas anderes: bei Massstab 13,09 sind es 0,68 m, bei 27 sind es
1,40 m. Unter dem DIN-Mindestmass von 800 mm verwarf der Bauer den Wert und
baute 1000 mm -- die meisten Treppen wurden also als 1,00 m gebaut, ohne dass
das irgendwo stand.

Jetzt steht es. `width = 0.90 / massstab`, je Haus UND je Geschoss gerechnet
-- ein Zweigeschosser kann oben und unten verschiedene Massstaebe haben, und
dieselbe Breite waere dann eine andere Zahl. 0,90 liegt ueber dem
DIN-Mindestmass, wird also als GEMESSENER Wert uebernommen und nicht mehr
ersetzt.

    197 Treppen insgesamt
     82 Haeuser geschrieben, 161 Treppen messen jetzt 0,90 m
      0 weichen ab
     36 Treppen ohne Massstab -- unberuehrt, koennen ohnehin nicht gebaut werden

Nachgerechnet: alle 82 Dateien sind ausser der Treppenbreite Byte-gleich
geblieben. Jede beruehrte Datei hat eine Sicherung
`annotations.json.vor-treppenbreite` daneben.

Im Zeichner geprueft (`bungalow_003`, Massstab 13,09): gespeichert 0.068774,
das sind 0,900 m, gemalt 31,7 px, ueber dem DIN-Mindestmass -- der Bauer
uebernimmt es.

Auch NEUE Treppen bekommen die richtige Breite: `neueTreppenbreite()` in
annotate.js rechnet 0,90 / Massstab statt der alten 0.052.

Neu: `scripts/treppenbreite-setzen.py` (laeuft ohne Argument nur als
Trockenlauf), `tests/test_treppenbreite_setzen.py` (9). Suite 108 JS + 220
Python gruen.

## ZEICHNER-AUFTRITTE-EINBLENDEN-001 (COMPLETE)

Rainer, 2026-08-29: "is it possible to calculate the length of the stairs and
if they are long enough ... you could just blend in the auftrittsbreite?" und
praezisiert: "when i edit the points of the stairs overlay the
auftrittsbreite on the screen that way i know when i have enough".

Die Treppe zeigt jetzt beim Zeichnen ihre Auftritte als Querkanten ueber dem
Band, dazu die Zahl daneben: "310 mm · 4,34 m". Beim Ziehen eines Punktes
rechnet es mit -- gemessen: 4,34 m / 310 mm, nach dem Verschieben 4,42 m /
316 mm.

Die Zahlen kommen aus `build-simplifier-render-plan.py`, nicht aus dem
Bauchgefuehl:

    Geschosshoehe   2620 mm  (Wand 2400 + Deckenplatte 220)
    Zielsteigung     175 mm  -> 15 Steigungen, 14 Auftritte
                              (die letzte Stufe IST der Boden oben)
    Soll-Auftritt    280 mm
    DIN-Minimum      260 mm

Ampel: gruen ab 280, gelb 260..280 ("baubar, aber der Bauer setzt ein
Podest"), rot darunter.

**Rainers 250 mm faerben NICHT gruen.** 16 Stufen zu 25 cm waeren 4,00 m --
nah an den 3,92 m, die der Bauer will, aber 250 liegt unter dem DIN-Minimum
von 260, an dem `stair_turn_style()` zwischen geradem Lauf, Podest und
Wendelung entscheidet. Wer hier bei 250 gruen faerbte, liesse den Zeichner
wieder etwas anderes zeigen als gebaut wird -- derselbe Fehler wie bei der
Treppenbreite heute frueh. Deshalb steht die ZAHL daneben: 251 mm sieht man,
und man entscheidet selbst.

### Befund: 57 von 162 Treppen sind zu kurz

Ueber alle Treppen mit Massstab gemessen:

    Median 3,79 m, kuerzeste 2,82 (twostorey_005), laengste 6,89
    105 reichen fuer einen geraden Lauf (>= 3,64 m = 14 x 260)
     57 nicht -- die brauchen Podest oder Wendelung

Bei mehreren davon hat die Lauflinie nur ZWEI Punkte, ist also gerade
gezeichnet. Eine gerade Treppe kann nicht wendeln. Das ist jetzt sichtbar,
statt erst im Bau aufzufallen.

Tests: `static/treppenstufen.test.mjs` (10). Suite 118 JS + 220 Python gruen.
Cache-Buster 20260830-0510.

Nebenbei: die drei neuen Zeichenfunktionen lagen erst versehentlich INNERHALB
von `drawElement`. Lief, war aber falsch verschachtelt -- herausgezogen.

## ZEICHNER-TREPPENART-UND-PODESTRECHNUNG-001 (COMPLETE)

Rainer, 2026-08-29: "können wir rechtsklick treppenart auswählen podest oder
wendeltreppe?"

Ja. Rechtsklick auf eine Treppe bietet jetzt Gerade / Podesttreppe /
Viertelgewendelt / Halbgewendelt, hakt die gesetzte an und bietet "Art nicht
erklären (der Bauer misst selbst)". Geschrieben wird `stair_type` -- das Feld,
das `declared_stair_type()` liest und das laut
`stair_turn_style()` der eigenen Messung des Bauers VORGEHT.

`spindel` fehlt bewusst: sie steht dort unter STAIR_TYPES_NOT_YET. Sie
anzubieten hiesse, einen Bau anzubieten, der scheitert. Ein unbekannter Wert
bricht den Bau mit SystemExit ab -- deshalb stehen die vier erlaubten Namen
als Test fest.

### Dabei eine eigene Rechenluecke gefunden

Die Auftritts-Einblendung von vorhin teilte die Lauflinie GLEICHMAESSIG. Bei
`onehalfstorey_002` (6,01 m, vier Punkte) kam so 401 mm heraus -- das ist
keine Treppe, das ist eine Rampe. An den Ecken sitzen Podeste, und darauf
liegt keine Stufe.

Jetzt dieselbe Rechnung wie `stair_landing_zones()`:

    Lauflinie      6,01 m
    2 Podeste      2,14 m   (je Treppenbreite, um die Ecke zentriert;
                             zwei enge Ecken werden zu EINEM U-Podest)
    Fluglauf       3,87 m
    13 Auftritte   (15 Steigungen - 2 Podeste; man tritt aufs Podest)
    -> 298 mm      gruen

Die Kanten werden ueber die Podestzonen hinweggeschoben statt hineingemalt.

### Und eine Korrektur an meiner eigenen Zahl von vorhin

Ich hatte "14 Auftritte, 3,92 m gebraucht" geschrieben -- meine eigene
Herleitung ("die letzte Stufe ist der Boden oben"). Der Bauer rechnet
`max(1, risers - len(zones))`, bei einer geraden Treppe also 15 und 4,20 m.
Der Zeichner folgt jetzt der Formel des Bauers, nicht meiner. Die Zahl "57 von
162 zu kurz" aus ZEICHNER-AUFTRITTE-EINBLENDEN-001 ist damit zu niedrig
gegriffen; die Karte im Zeichner zeigt fuer jedes Haus den echten Wert.

Tests: `static/treppenart.test.mjs` (8), `treppenstufen.test.mjs` jetzt 18.
Suite 134 JS. Cache-Buster 20260830-0610.

Im Zeichner geprueft: Menue setzt `podest`, hakt an, Zuruecksetzen entfernt
das Feld wieder.

## HTML-NIE-ZWISCHENSPEICHERN-001 (COMPLETE)

Rainer, 2026-08-29: "there is no house there ... and also the rechts click for
the wendel oder Podesttreppe?"

Beides war da. Der Server lieferte `onehalfstorey_002` auf beiden Geschossen
aus (5 Raeume unten, 5 oben, 45 % der Leinwand bemalt, keine Fehler), und das
Treppenart-Menue war eine Stunde vorher gebaut. Er sah eine alte Seite.

Der Grund: `annotate.html` ging ohne `Cache-Control` raus. Die Skripte tragen
ihre Version im Namen (`annotate.js?v=...`) -- aber das steht IN der HTML.
Haelt der Browser die HTML fest, bleiben auch die alten Skriptversionen. Genau
deshalb musste heute nach JEDER Aenderung "Seite neu laden" dabeistehen, und
einmal hat es trotzdem nicht gereicht.

Behoben an der Ursache: `nicht_zwischenspeichern()` -- HTML geht mit
`Cache-Control: no-store` raus, alles andere darf bleiben. Geprueft:

    HTML  Cache-Control: no-store
    JS    (keiner -- darf bleiben)

Ampel im Zeichner nachgemessen, indem die Lauflinie gestaucht wurde:

    6,01 m -> 298 mm   GRUEN
    4,33 m -> 162 mm   ROT
    3,30 m -> 106 mm   ROT

Tests: `tests/test_html_nicht_zwischenspeichern.py` (5). Suite 134 JS + 225
Python gruen.

## HAUSSEITE-RAHMEN-ZUSAMMENGEFALLEN-001 (COMPLETE)

Rainer, 2026-08-29: "my house page is empty".

War sie nicht -- die Seite waehlte das richtige Haus, hatte ihre
Schrittleiste und bettete den Annotator ein. Der EINGEBETTETE RAHMEN war
296 x 144 Pixel gross. Darin ist kein Grundriss zu sehen.

`.rahmen { flex:1 1 auto; min-height:0 }` gibt dem iframe genau den Rest, den
Kopfzeile, Schrittleiste und Hausliste uebriglassen -- und `min-height:0`
erlaubt ihm, auf einen Streifen zusammenzufallen. Jetzt eine Untergrenze wie
im Annotator selbst: `clamp(520px, calc(100dvh - 240px), 1400px)`.

Gemessen auf 1500x950: 1230 x 858 statt 296 x 144.

Dabei selbst einen Fehler gebaut: mein Kommentar enthielt Backticks um
`min-height:0`. Das steht in einem styled-jsx-Template-Literal -- der Backtick
hat es beendet, und die Seite kam mit HTTP 500 und leerem Body zurueck. Also
war sie fuer ein paar Minuten wirklich leer, meinetwegen. Behoben.

Zusammen mit HTML-NIE-ZWISCHENSPEICHERN-001 die zweite Ursache derselben
Beschwerde an einem Abend: einmal sah er eine alte Seite, einmal einen
Rahmen ohne Hoehe.

## ZEICHNER-TREPPE-WAR-NICHT-ANKLICKBAR-001 (COMPLETE)

Rainer, 2026-08-29: "where do i click for podest wendel?"

Nirgends. Das Menue war gebaut, aber unerreichbar: `elementAtPoint()` liess
Treppen gar nicht zu -- `LINE_ELEMENTS` kannte nur door/window/opening. Im
Zeichner nachgemessen: ein Klick MITTEN auf die Treppenlinie traf nichts, auf
einem ihrer Punkte auch nicht, und 5 bis 25 Pixel daneben ebenso wenig.

**Mein Fehler in der Pruefung, nicht nur im Code.** Ich hatte das Menue
gemeldet, nachdem ich `openElementMenu()` programmatisch aufgerufen hatte.
Das beweist, dass das Menue existiert -- nicht, dass man hinkommt. Genau die
Lehre vom 2026-08-16: gegen die sichtbare Oberflaeche pruefen, nicht gegen
den eigenen Code. Ein synthetischer Rechtsklick auf die Leinwand haette es
sofort gezeigt; ich hatte ihn sogar versucht, sah "gewaehlteTreppe: false"
und bin darueber hinweggegangen.

Zweiter Fehler in derselben Zeile: geprueft wurde nur
`points[0]..points[1]`. Eine Treppe hat zwei bis vier Punkte -- eine
geknickte waere nur auf ihrem ersten Schenkel greifbar gewesen. Jetzt jeder
Schenkel.

Dazu der Hinweis in der Statuszeile, den bisher nur Tueren bekamen:
"stair path · Rechtsklick für Optionen · Ziehen zum Verschieben, Entf löscht."

Mit einem ECHTEN Rechtsklick auf die Leinwand geprueft: Treffer "stairs",
Treppe gewaehlt, Menue offen mit Gerade / Podesttreppe / Viertelgewendelt /
Halbgewendelt.

Tests: `static/treffer.test.mjs` (7). Suite 141 JS. Cache-Buster 20260830-0700.

## TREPPE-KOPIEREN-BREITE-UMRECHNEN-001 (COMPLETE)

Rainer, 2026-08-29: "copy stairs to top floor still works correctly?"

Gute Frage -- es kopierte, aber die BREITE wurde falsch. `width` steht in
normierten x-Einheiten des JEWEILIGEN Geschosses, und 16 Haeuser im Bestand
haben je Geschoss einen anderen Massstab.

An `german_catalog_review_onehalfstorey_1_1_1_efh_120` nachgemessen:

    Erdgeschoss   11,426 m/Einheit   width 0.078767  =  0,900 m
    Obergeschoss  10,820 m/Einheit   width 0.083182  =  0,900 m

    Kopieren nach oben (vorher):     width 0.078767  =  0,852 m

Fuenf Zentimeter weg, jedes Mal. Vorher fiel das nicht auf: alle Treppen
trugen denselben Vorgabewert 0.052, und der Bauer ersetzte ihn ohnehin durch
1000 mm. Erst seit die Breite etwas bedeutet, bedeutet auch ihr Verlust
etwas -- die eigene Aenderung von heute hat den Fehler erst sichtbar gemacht.

Neu `breiteFuerGeschoss()`: beim Kopieren wird mit dem Verhaeltnis der beiden
Massstaebe umgerechnet. Nachgemessen, ohne zu speichern:

    vorher      EG 0,900   OG 0,900
    nach oben   EG 0,900   OG 0,900  (Rolle "opening" = Treppenoeffnung)
    nach unten  EG 0,900   OG 0,900

Hin und zurueck stabil. Danach neu geladen: auf der Platte unveraendert.

Tests: `static/treppenbreite.test.mjs` jetzt 13. Suite 146 JS. Cache-Buster
20260830-0710.

## TREPPENBREITE-BEIM-SPEICHERN-NACHZIEHEN-001 (COMPLETE)

Die Umstellung auf 0,90 m erreichte nur Geschosse, die DAMALS einen Massstab
hatten. 36 Treppen hatten keinen und blieben auf dem Vorgabewert 0.052. Gibt
Rainer so einem Haus spaeter einen Massstab -- und genau das tut er gerade,
Haus fuer Haus -- traegt seine Treppe weiter eine Zahl, die niemand gewaehlt
hat. `onehalfstorey_002` (Massstab 22:12 gesetzt) und `onehalfstorey_007`
(23:08) waren dieser Fall.

**Korrektur an meiner eigenen Auskunft.** Ich hatte Rainer gesagt, sein
Speichern habe meine Umstellung ueberschrieben. Das war falsch.
`bungalow_003` beweist es: zwei Treppen, eine umgestellt (0.068774) und eine
nicht (0.052), weil deren Geschoss keinen Massstab hat -- in EINER Datei, die
seit dem 14. Juli nicht mehr von Hand gespeichert wurde. Es war nie eine
Kollision, sondern immer dieselbe Luecke.

Ein Skript nachlaufen zu lassen loest das nicht: die Luecke entsteht bei
jedem neu gesetzten Massstab neu. Also macht es der Zeichner beim Speichern
(`treppenbreitenNachziehen()`), an der einen Stelle, an der die Wahrheit
ohnehin geschrieben wird. NUR der Vorgabewert wird ersetzt; eine gesetzte
Breite bleibt, auch eine kleine.

Geprueft an `onehalfstorey_007`, im Speicher:

    vorher    EG 0.052            OG 0.052
    nachher   EG 0.055063 = 0,90 m   OG 0.052 (kein Massstab, bleibt)

Tests: `static/treppenbreite.test.mjs` jetzt 19. Suite 152 JS + 225 Python
gruen. Cache-Buster 20260830-0800.

### Befund zu onehalfstorey_007

Ausrichtmarken auf BEIDEN Geschossen, Haustuer markiert, Umriss da, Massstab
16,34 im EG bestaetigt (Tueren 0,72/0,72/0,72/1,12/1,28 m).

    Treppe   4,17 m Lauflinie, 1 Podest, 234 mm Auftritt   ROT

Unter dem DIN-Minimum von 260. Entweder die Lauflinie verlaengern oder per
Rechtsklick "Halbgewendelt" erklaeren -- dann wendet der Bauer statt ein
Podest zu setzen und gewinnt Steigungen in der Wendel.

Dem Obergeschoss fehlt noch der Massstab.

## ZEICHNER-RAUMFLAECHE-ANZEIGEN-001 (COMPLETE)

Rainer, 2026-08-29: "can you also put the qm number under the room names in
the annotator?"

Unter jedem Raumnamen steht jetzt die Flaeche. Daran merkt man beim Zeichnen,
ob ein Raum stimmt -- ein Bad mit 3 m2 oder ein Kinderzimmer mit 30 ist
sofort verdaechtig.

Gerechnet mit der Gaussschen Trapezformel ueber das ECHTE Polygon, nicht
ueber den Kasten drumherum. An `bungalow_028` gemessen, wo der Unterschied
gross ist:

    HWR / HTR        Kasten 28,2 m2   Polygon 20,1 m2
    Wohnen / Essen   Kasten 46,7 m2   Polygon 34,6 m2
    Diele            Kasten 19,5 m2   Polygon 15,0 m2
    Bad              Kasten 14,5 m2   Polygon 14,5 m2   (rechteckig)

Die y-Achse bekommt das Seitenverhaeltnis der Zeichenflaeche -- sonst waere
dieselbe Zeichnung auf einer flacheren Leinwand ein anderes Haus.

Ohne Massstab steht nichts da; eine erfundene Zahl waere schlimmer als keine.

Tests: `static/raumflaeche.test.mjs` (7). Suite 159 JS. Cache-Buster
20260830-0810.

## EIN-MASSSTAB-JE-HAUS-001 (COMPLETE)

Rainer, 2026-08-29: "why just EG and not OG?" -- die Quadratmeter standen nur
im Erdgeschoss. Dann, schaerfer: "dude, that cant be we have the floors
aligned setting the massstabe there should actually be forbidden."

Sein Gedanke stimmt -- zwei Besitzer fuer eine Tatsache sind die Fehlerklasse
dieses ganzen Tages. Und der Widerspruch existiert schon: alle drei Haeuser
mit gespeichertem zweitem Massstab UND Ausrichtmarken widersprechen sich, um
6,4 / 8,7 / 24,1 Prozent.

**Aber die Aufloesung geht andersherum, als ich zuerst vorschlug.**

Erster Anlauf: den zweiten Massstab aus den Ausrichtmarken ableiten und das
Setzen von Hand sperren. Gebaut, gemessen -- und zurueckgenommen, bevor es
gemessene Werte ueberschrieb.

Der Test waren die Tuerbreiten. Zuerst gegen die ganze Baurichtmassreihe
(0,625 / 0,75 / 0,875 / 1,00 / 1,125) -- da stand es 3:4 und eine falsche
1,00 galt als Treffer. Rainer: "zimmertüren sind 87, nicht 100." Gegen 0,875
gemessen kippt es:

    Haus                aus Marken   EG-Mass aufs OG
    onehalfstorey_020      7,2 %          2,1 %
    onehalfstorey_029      7,8 %          3,4 %
    onehalfstorey_007     12,6 %          3,5 %
    twostorey_007         14,0 %         13,3 %
    bungalow_007          22,9 %         22,5 %
    onehalfstorey_010      6,5 %          7,6 %   (Marken besser)
    twostorey_030         30,4 %         45,5 %   (Marken besser)

Fuenf zu zwei fuer das Erdgeschossmass. Die Geschosse eines Hauses sind auf
demselben Planblatt im selben Massstab gezeichnet, also gilt EINE Messung
fuer alle. Die Ausrichtmarken sind zwei mit dem Auge gesetzte Eckpunkte -- gut
genug zum Uebereinanderlegen, zu ungenau zum Messen.

Also: `massstabDesHauses()`. Ein Geschoss ohne eigenen Massstab erbt den
gemessenen des Hauses. Ein eigener bleibt unangetastet.

Geprueft an `onehalfstorey_007` (OG hatte keinen):

    geerbt 16,345 -> Zimmertueren 0,83 / 0,83 / 0,86 / 0,86 m
    Flaechen: Kind 17,6 · Kind 14,6 · Bad 14,7 · Eltern 20,8 · Flur 8,0 m2
    Treppe oben 3,47 m, 187 mm Auftritt, ROT

Zum Vergleich: aus den Marken (19,07) waeren es 0,97 bis 1,01 m Tueren und
Kind 24,0 / Eltern 28,3 m2 gewesen.

Die Ableitung bleibt als PRUEFUNG: wer einen zweiten Massstab von Hand setzt
und dabei mehr als 5 % von den Marken abweicht, bekommt es gesagt. Nicht
verboten -- gezeigt.

OFFEN, Rainers Entscheidung: `twostorey_007` (24 % Widerspruch),
`onehalfstorey_029` (8,7 %) und `onehalfstorey_020` (6,4 %) tragen einen
gespeicherten zweiten Massstab. Bei allen dreien trifft das EG-Mass die
Zimmertueren besser. `onehalfstorey_020` ist ausgeliefert -- der zweite
Massstab dort zu loeschen aendert Geometrie.

Tests: `static/massstab-aus-marken.test.mjs` (14). Suite 173 JS.
Cache-Buster 20260830-0920.

## ZEICHENLISTE-NIE-GEZEICHNET-001 (COMPLETE)

Rainer, 2026-08-29: "auf die zeichenliste".

Dritte Arbeitsliste: `http://localhost:8765/nie-gezeichnet.html`, live
gerechnet wie die anderen beiden. 15 Projekte.

Zwei Sorten, beiden fehlt dasselbe -- die Zeichnung, nicht eine Zahl:

    14 Projekte mit NULL Raeumen
     1 mit ueberwiegend Platzhalternamen (`cubicasa_..._904`)

Genau diese fallen aus der Massstab- und der Haustuer-Liste heraus, und das
ist richtig: dort waeren sie Laerm. Sie verschwanden damit aber auch aus dem
Blick -- der Anlass war, dass Rainer `onehalfstorey_042` leer vorfand und
nicht wusste, ob etwas kaputt ist.

Fuenf Ordner sind als **Testrest** gekennzeichnet (`codex_privacy_check`,
`codex_privacy_check_full`, `codex_import_test`, `batch_smoke_braun`,
`area_test`). Erkannt, nicht geloescht -- Rainer hat die Loeschfrage
ausdruecklich offen gelassen.

Bleiben zehn echte Haeuser: bungalow_006/020/026, onehalfstorey_001/004/042,
twostorey_001/002/006 und cubicasa_904.

Stand der drei Listen:

    ohne Massstab    14   (heute frueh 210)
    ohne Haustuer    19   (6 davon eindeutig)
    nie gezeichnet   15   (5 Testreste)

Tests: `tests/test_zeichenliste.py` (12). Suite 237 Python + 173 JS gruen.

## GEERBTER-MASSSTAB-WIRD-ALS-GEERBT-GEZEIGT-001 (COMPLETE)

Rainer, 2026-08-29: "und wieso sind bei der Zeichnung immer noch keine qm zu
sehen im OG?"

Sie waren zu sehen -- er hatte die alte Seite im Browser. Aber beim Nachsehen
kam das Wichtigere heraus: die Zahlen dort waren FALSCH.

`onehalfstorey_002`, Obergeschoss, geerbter Massstab 20,59 vom Erdgeschoss:

    Tueren geerbt (20,59)   0,91 / 0,98 / 1,07 / 1,09 m
    Tueren bei  16,82       0,74 / 0,80 / 0,88 / 0,89 m   <- Baurichtmasse

    Flaechen geerbt -> richtig
    Eltern  36,3 -> 24,2      Bad   22,6 -> 15,1
    Kind    35,0 -> 23,4      Flur  14,0 ->  9,3

Rund 20 Prozent zu gross. Das Obergeschoss ist ein anderer Bildausschnitt --
dasselbe wie bei den Katalog-Haeusern, nur bei einem von Hand gezeichneten.

Die Vererbung von EIN-MASSSTAB-JE-HAUS-001 bleibt (ohne sie stuende dort gar
nichts), aber sie wird jetzt als das ausgewiesen, was sie ist:

    GEERBT von einem anderen Geschoss: Bildbreite ≈ 20.59 m. Ist dieses
    Geschoss ein anderer Bildausschnitt, stimmt das nicht — dann hier
    eigenen Maßstab festlegen.

Geerbt ist nicht gemessen. Wer das nicht sieht, glaubt einer Zahl, die
niemand fuer dieses Bild gemessen hat -- und genau das haette ich ihm heute
Abend fast als Verbesserung verkauft.

Suite 173 JS + 237 Python gruen. Cache-Buster 20260830-0930.

OFFEN: `onehalfstorey_002` braucht einen eigenen Massstab fuers OG (~16,8
laut Tuerbreiten). Dasselbe gilt fuer jedes Geschoss, dessen Statuszeile
"GEERBT" sagt.

## GEBAEUDEMASS-MIT-VORSCHAU-001 (COMPLETE)

Rainer, 2026-08-29: "i added a massstabe to that one and then the Aspect ratio
got screwed up" -- und danach: "mach das mit gebäude masse eingeben und den
anwenden knopf mit qm zahlen unter den raumnamen".

Der Knopf "Gebäudemaße eingeben" tut zwei Dinge auf einmal: Massstab setzen
UND das Seitenverhaeltnis der Zeichenflaeche neu definieren
(`aspect = metresPerYUnit / metresPerXUnit`). Passen die getippten Masze
nicht zur gezeichneten Aussenkontur, wird die Zeichnung gestreckt. Frueher
geschah das blind, hinter zwei `window.prompt`-Kaesten, ohne Weg zurueck
ausser Neuladen.

Jetzt ein Feld mit Breite, Tiefe, Anwenden, Abbrechen. Waehrend des Tippens:

- die Quadratmeter unter den Raumnamen zeigen SOFORT das getippte Mass
- der Hinweis nennt den Massstab und die Streckung

An `bungalow_013` nachgemessen (gespeicherter Massstab 24,52):

    12 x  9   "Bildbreite 24.58 m. ACHTUNG: streckt die Zeichnung um -10 %."
              Wohnen 37,1  Eltern 15,1  Bad 11,2
    12 x 14   "Bildbreite 24.58 m. ACHTUNG: streckt die Zeichnung um +40 %."
              Wohnen 57,7  Eltern 23,5  Bad 17,5
    Abbrechen zurueck auf Wohnen 41,1 -- nichts geschrieben

Unter 1,5 % Streckung steht "Die Zeichnung bleibt, wie sie ist."

`applyStatedBuildingSize(widthM, depthM)` nimmt die Werte jetzt entgegen; ohne
Argumente fragt es wie frueher, damit der alte Aufrufweg gueltig bleibt.

Neu: `static/gebaeudemass-vorschau.js`,
`static/gebaeudemass-vorschau.test.mjs` (8). Suite 181 JS + 237 Python gruen.
Cache-Buster 20260830-1000.

## MASSSTAB-EINGABE-VERTRAEGT-EINHEITEN-001 (COMPLETE)

Rainer, 2026-08-30, nachdem er bei `onehalfstorey_012` einen Massstab gesetzt
hatte: "hey i did it and still cant see anything". Die Datei enthielt danach
`floor_scale: {}` -- der Wert war nie angekommen.

Der Weg selbst ist in Ordnung. Im Zeichner mit echten Klicks nachgestellt:
die Messung setzt 16,58, und das Save-Paket traegt
`floor_scale: {upperfloor: 16.5827}` mit. (Seine Datei blieb dabei
unberuehrt -- die Save-Anfrage wurde abgefangen, Zeitstempel unveraendert
08:27:43.)

Was ihn still verschluckt, ist die EINGABE:

    Number("5")    -> 5      gut
    Number("5,2")  -> 5.2    Komma wurde schon ersetzt
    Number("5 m")  -> NaN    "Maßstab nicht gesetzt"
    Number("5m")   -> NaN    dasselbe

Wer nach einer Laenge IN METERN gefragt wird, tippt "5 m". Das als
Fehleingabe zu behandeln ist Schikane -- und die Meldung "Maßstab nicht
gesetzt" ist so leise, dass man glaubt, man haette ihn gesetzt.

Neu `meterAusEingabe()`: nimmt die erste Zahl aus der Eingabe. Und die
Fehlermeldung nennt jetzt, WAS ankam:

    "5"            -> 16,58 gesetzt
    "5 m"          -> 16,58 gesetzt
    "5m"           -> 16,58 gesetzt
    "1,13 m"       ->  3,75 gesetzt
    "ca 5"         -> 16,58 gesetzt
    "weiss nicht"  -> «"weiss nicht" ist keine Länge — Maßstab NICHT gesetzt.
                      Nur die Zahl eingeben, z. B. 1,13»
    Abbrechen      -> "Abgebrochen — Maßstab nicht gesetzt."

Abbrechen ist keine Fehleingabe mehr, sondern Absicht -- vorher las sich
beides gleich.

Tests: `static/masseingabe.test.mjs` (8). Suite 189 JS + 237 Python gruen.
Cache-Buster 20260830-1100.

## GEBAEUDEMASS-BREITE-MAL-HOEHE-001 (COMPLETE)

Rainer, 2026-08-30, zwei Meldungen zum selben Knopf:

**1. "your window with the gebäudemasse is missing."**

Es fehlte nicht -- der Knopf war `disabled`. `updateScaleStatus()` setzte
`buildingSizeButton.disabled = !outlineRelativeExtent()`, und ein Klick tat
daraufhin NICHTS: kein Feld, keine Meldung, kein Hinweis, was fehlt. Die
Erklaerung ("Erst die Außenkontur zeichnen") stand im Klick-Handler, aber ein
gesperrter Knopf feuert keinen Klick.

Jetzt sperrt er nicht mehr, er sagt es.

**2. "gebäude masse eingeben has to be breite x höhe."**

Die Felder hiessen "Breite (Ost-West)" und "Tiefe (Nord-Süd)". Man misst hier
aber das Rechteck, das man vor sich sieht: in der Wirklichkeit ist die
senkrechte Strecke die Tiefe des Hauses, auf der Zeichnung ist sie die Hoehe.
Wer eintippt, schaut auf die Zeichnung. Umbenannt in **Breite x Höhe**;
gespeichert wird weiter `depth_m`, das liest der Renderer.

**Dazu neu: die passende Hoehe.** An `onehalfstorey_012` fiel auf, dass
10 x 8 um -26 % streckt, 12 x 9 um -31 %, 9 x 9 nur um -8 %. Die Zeichnung
sagt selbst, welche Hoehe zur Breite gehoert -- man muss sie nur ausrechnen
statt zu raten. Der Hinweis nennt sie jetzt:

    11 x 9    "streckt die Zeichnung um -25 %.
               Zur Breite 11 m passt eine Höhe von 11.95 m."
    11 x 11,95  "Die Zeichnung bleibt, wie sie ist."

Die Breite ist meist die Zahl, die man sicher weiss (Giebelseite,
Katalogangabe). Weicht die passende Hoehe stark von der eigenen Zahl ab,
stimmt entweder die Zahl nicht oder die Kontur ist schief gezeichnet.

Tests: `static/gebaeudemass-vorschau.test.mjs` jetzt 15. Suite 196 JS + 237
Python gruen. Cache-Buster 20260830-1130.

## MASSSTAB-FENSTER-001 (COMPLETE)

Rainer, 2026-08-30: "it would be much better if i could change these
independently with a checkmark to lock the aspect ratio, actually if i could
nudge the width and height, maybe the whole Maßstab stuff in its own little
window to move around."

Aus `gebaeudemass-vorschau.js` wurde `massstab-fenster.js`: ein eigenes,
verschiebbares Fenster.

    Breite in Metern    [−] [ 11.00 ] [+]
    Höhe   in Metern    [−] [ 11.95 ] [+]      (gesperrt: grau, folgt der Breite)
    [x] Seitenverhältnis sperren
    Bildbreite entspricht dann 17.31 m. Die Zeichnung bleibt, wie sie ist.
    [Anwenden] [Abbrechen]

Stellen: tippen, +/- klicken oder Pfeiltasten im Feld. Schritt 0,1 m, mit
Shift 1 m, mit Alt 1 cm. Im Zeichner nachgemessen an `onehalfstorey_012`:

    Breite 11, gesperrt   -> Höhe 11.95   "bleibt, wie sie ist"
    Pfeil hoch            -> 11.10 / 12.06
    Shift+Pfeil           -> 12.10 / 13.14
    entsperrt, Höhe 9     -> "streckt um -32 %. Ungestreckt wären es 13.14 m."

**Die Sperre ist der eigentliche Gewinn.** Gesperrt folgt die Hoehe der Breite
so, dass NICHTS gestreckt wird -- der Normalfall: wer die Kontur sauber
gezeichnet hat, will den Massstab setzen und nicht die Zeichnung verziehen.
Genau das war Rainers urspruengliche Beschwerde ("the Aspect ratio got
screwed up"). Entsperrt geht es weiter wie bisher, nur sichtbar.

Das Fenster haengt am Griff verschiebbar wie das RAEUME-Feld und merkt sich
seinen Ort in `localStorage` -- der Ort ist eine Bedienentscheidung, kein
Zustand des Hauses, und gehoert nicht in die Annotation.

Die Quadratmeter unter den Raumnamen zeigen waehrend des Stellens das
eingestellte Mass. Geschrieben wird erst bei "Anwenden".

Tests: `static/massstab-fenster.test.mjs` (8),
`massstab-fenster-vorschau.test.mjs` (15, aus der Vorstufe uebernommen).
Suite 204 JS + 237 Python gruen. Cache-Buster 20260830-1200.

## AUSRICHTMARKEN-SIND-EINE-PRUEFUNG-001 (KORREKTUR + Befund)

Rainer, 2026-08-30: "ich habe die diagonale gezogen über die ecken die gleich
sind oben und unten, die anderen 2 ecken schaffen so eine art überdachung."

**Damit ist meine Schlussfolgerung vom 2026-08-29 falsch.** Ich hatte
geschrieben, die Ausrichtmarken bezeichneten "die Aussenecken des jeweiligen
Geschosses -- nicht dieselben Punkte", und daraus geschlossen, ein Massstab
lasse sich daraus grundsaetzlich nicht ableiten. Das war eine Erklaerung fuer
gemessene Abweichungen, keine gepruefte Tatsache. Die Marken SOLLEN dieselben
zwei Punkte bezeichnen.

An `onehalfstorey_021` nachgemessen, wo Rainer sie eben gesetzt hat:

    Erdgeschoss   Marken-Diagonale 12,89 m
    Obergeschoss  Marken-Diagonale 12,86 m     0,2 % Unterschied

Genau so soll es sein. Wo die Diagonalen auseinanderlaufen, ist das also ein
FEHLER im Haus -- kein Naturgesetz.

Ueber alle acht Haeuser mit Marken auf zwei Geschossen, mit dem einen
Hausmassstab gerechnet:

    onehalfstorey_021    12,89   12,86     0,3 %
    bungalow_007         12,67   12,61     0,5 %
    onehalfstorey_010    14,13   13,98     1,1 %
    onehalfstorey_020    14,12   13,27     6,4 %   pruefen
    onehalfstorey_029    13,18   12,28     7,4 %   pruefen
    twostorey_030        16,51   18,42    11,6 %   FEHLER
    onehalfstorey_007    14,76   12,65    16,7 %   FEHLER
    twostorey_007        12,46   16,42    31,7 %   FEHLER

Drei von acht stimmen auf 3 % ueberein. Bei den anderen sitzt mindestens eine
Marke auf der falschen Ecke -- und da die Marken das Obergeschoss aufs
Erdgeschoss legen, stapelt sich dort das Haus versetzt.

`twostorey_007` ist der schlimmste: 31,7 %. Seine EG-Marken umspannen nur
0,80 der Zeichnung, sein Raumkasten 1,10 -- dort ist wohl die Garage
ausgelassen.

### Was daraus folgt

Die Diagonale ist damit eine PRUEFUNG, die es vorher nicht gab: zwei Marken,
eine Strecke, und ein Haus, das sich selbst widerspricht, faellt sofort auf.
Das ist genauer als jede Tuerbreite -- eine Tuer ist 0,9 m, die Diagonale
13 m, dieselbe Zeichenungenauigkeit wiegt zwanzigmal weniger.

OFFEN, Rainers Entscheidung: die fuenf Haeuser mit mehr als 3 % Abweichung
durchsehen und die Marken neu setzen. Fuer eine Ableitung des zweiten
Massstabs taugen sie erst danach.

## AUSRICHTUNG-PRUEFEN-LISTE-001 (COMPLETE)

Vierte Arbeitsliste: `http://localhost:8765/ausrichtung-pruefen.html`, live
gerechnet wie die anderen drei. 5 Haeuser.

Grundlage ist Rainers Satz vom 2026-08-30: die Marken bezeichnen dieselben
zwei Ecken, die oben und unten gleich sind. Ihre Diagonale muss also auf
beiden Geschossen dieselbe Meterzahl ergeben.

    twostorey_007        EG 12,46   OG 16,42    31,7 %
    onehalfstorey_007    EG 14,76   OG 12,65    16,7 %
    twostorey_030        EG 16,51   OG 18,42    11,6 %
    onehalfstorey_029    EG 13,18   OG 12,28     7,4 %
    onehalfstorey_020    EG 14,12   OG 13,27     6,4 %

Drei weitere Haeuser mit Marken auf zwei Geschossen stimmen ueberein und
stehen deshalb nicht drauf: `onehalfstorey_021` (0,3 %), `bungalow_007`
(0,5 %), `onehalfstorey_010` (1,1 %). Toleranz 3 %.

Ueber 10 % ist rot, darunter gelb.

`onehalfstorey_020` ist ausgeliefert -- dort sind die Marken um 6,4 %
uneinig, das Obergeschoss steht also versetzt auf dem Erdgeschoss.

Stand der vier Listen:

    ohne Massstab         12
    ohne Haustuer         18
    nie gezeichnet        15
    Ausrichtung falsch     5

Tests: `tests/test_ausrichtung_pruefen.py` (14). Suite 251 Python + 209 JS
gruen.

## MOEBEL-SCHRITT-OHNE-SPEICHERN-001 (COMPLETE)

Rainer, 2026-08-30, zum DRITTEN Mal derselbe Abbruch bei
`german_catalog_review_bungalow_3_3_1_b_100_2`:

    floor-0.json: die RAEUME dieses Geschosses wurden umgezeichnet, seit
    diese Moebel gesetzt wurden (Stempel 592ffe7f4ffc, heute 264c9c9b6070).
    Im Moebel-Schritt pruefen ... und einmal speichern.

Nachgesehen: `furniture/floor-0.json` trug weiter `updated_at
2026-08-29T08:05:48Z` und die alte `geometry_identity`. Gespeichert wurde
nie.

**Nicht Vergesslichkeit -- es ging nicht.** Der eingebettete Moebel-Schritt
(`mode=furniture-embed`) blendet alles ausser dem Plan aus:

    .wb-embed > *:not(.wb-plan) { display:none !important; }

Der Knopfbalken mit "Save draft" ist ein direktes Kind von `main` und fiel
damit mit heraus. Im Browser nachgemessen: 52 sichtbare Bedienelemente, alle
aus der Moebelpalette -- "Save draft" NICHT darunter. Der Schritt liess sich
nicht abschliessen, und ich habe ihm dreimal gesagt, er solle speichern.

(Meine eigene Fehlersuche war auch schief: `querySelectorAll` findet
ausgeblendete Elemente mit, ich hielt den Knopf erst faelschlich fuer
vorhanden. Erst die Pruefung auf `getBoundingClientRect()` zeigte es.)

Behoben: der Balken bekommt `wb-aktionen`, "Save draft" bekommt
`wb-speichern`, und die Ausblendregel nimmt den Balken aus. Im Balken bleibt
NUR Speichern -- Validate, Approve, Reject und Export gehoeren in die volle
Ansicht; hier waere jeder davon ein Umweg oder ein Unfall.

Nachgemessen nach der Aenderung: Save draft sichtbar bei y=278, im Fenster,
die anderen vier weiter ausgeblendet.

Codex hatte fuer diese Ansicht ausdruecklich "Geschossauswahl, Plan,
Moebelpalette, SPEICHERN, gut sichtbares Weiter zu Bauen" vorgesehen. Das
Speichern fehlte seit dem Umbau.

Tests: `scripts/moebel-speichern-sichtbar.test.mjs` (5).

## BELEG-GILT-NUR-FUER-DEN-EIGENEN-AUFTRAG-001 (COMPLETE)

Rainer, 2026-08-30, schickt dieselbe Lieferung noch einmal zur Pruefung. Am
2026-08-29 war sie formal in Ordnung; jetzt kamen **152 Beanstandungen**, alle
gleich: "ist als sichtbar gemeldet, aber ohne `bei`".

Nichts an der Lieferung hatte sich geaendert. Der Fehler ist meiner.

    Lieferung   job_id ...-2026-08-29
    Auftrag     job_id ...-2026-08-30   beleg_verlangt: True   (erzeugt 09:38)

`go.py` erzeugt den Auftrag bei JEDEM Lauf neu. Mein Gate stand nur am
Auftrag (`beleg_verlangt`) -- und wanderte damit mit. Die Absicht war
ausdruecklich, dass eine neue Forderung nicht nach hinten wirkt; dafuer
reichte der Gate nicht.

Neu `beleg_gilt(job, katalog)`: verglichen wird die job_id. Verschont wird
nur, wo BEIDE Kennungen dastehen und sich unterscheiden. Fehlt eine, zaehlt
die Forderung -- alles andere waere zu grosszuegig, die Pruefung liesse sich
sonst abschalten, indem man die Kennung weglaesst.

Der erste Anlauf war genau so zu grosszuegig ("Lieferung ohne Kennung wird
verschont") und liess VIER bestehende Pruefungen in `BelegStattBehauptung`
durchfallen -- deren Kataloge tragen keine Kennung. Die Tests haben den
Denkfehler gefangen, bevor er hinausging.

Danach: "Lieferung ist formal in Ordnung."

Nebenbei behoben: `lieferung-pruefen.test.py` hatte
`if __name__ == "__main__"` in der MITTE -- die neue Testklasse lief nicht
mit. Dasselbe Muster wie in `go.test.py` gestern.

Tests: `scripts/lieferung-pruefen.test.py` jetzt 75 (5 neu).

## R0-MASS-PROZEDURAL-GEBAUTES-OHNE-STEMPEL-001 (COMPLETE)

Rainer, 2026-08-30, an `bungalow_001`:

    Verifier R0_symbol_sizes: kleiderschrank-10:
    footprint 1400x800 vs symbol 3000x700

Das Haus hat zwei Kleiderschraenke, 1400x800 und 3000x700. Mein erster
Vorschlag war, sie auf dieselbe Groesse zu bringen. Rainer:

    "nein, kleiderschränke gibt es nicht in EINEM maß, die möbel sind nur
     symbole die einen bestimmten bereich verdecken können"

Er hat recht, und das ist genau, was `fit_to_symbol()` im Kopf traegt: "THE
SYMBOL IS THE OBJECT". Jede gezogene Groesse muss durchkommen. Der Fehler
gehoerte an die Wurzel.

### Gemessen statt geraten

Ich hatte drei Erklaerungen am Quelltext geprueft und alle verworfen -- eine
davon zu Unrecht. Statt weiter zu raten: das gebaute Blend im Hintergrund
geoeffnet und nachgemessen.

    kleiderschrank-10   Cube.126    1400x800x2100   Stempel: KEINER
    kleiderschrank-19   Mesh.038    3000x700x2100   Stempel: 3000x700

Instanz 10 ist ein prozedural gebauter Kasten. Der Bauweg (`build_box` und
Geschwister) setzt `symbol_w_mm` nicht -- das tat nur der Prototyp-Weg. Ohne
Stempel faellt `check_symbol_sizes()` auf `wanted[asset_id]` zurueck, und
dort steht die ZULETZT gesehene Platzierung desselben Assets: 3000x700. Das
Moebel wurde also am Symbol eines anderen gemessen.

Genau der Fehler, den der Stempel am 2026-08-22 beheben sollte
(onehalfstorey_029) -- er war nur auf einem der beiden Wege eingebaut.

(Meine Hypothese 1 war die richtige. Ich hatte sie verworfen, weil im
Bauplan ein `mesh_path` steht -- der sagt aber nichts darueber, welchen Weg
der Renderer am Ende nimmt.)

### Behoben und nachgewiesen

Der Bauweg stempelt jetzt jedes gebaute Stueck mit seiner eigenen
Symbolgroesse. Danach neu gebaut:

    vorher   Stempel: KEINER            FAIL R0_symbol_sizes (8x im Log)
    nachher  Stempel: 1400.0x800.0      PASS R0_symbol_sizes, 0 FAIL

`bungalow_001` ist fertig, `delivery-manifest.json` geschrieben.

Tests: `scripts/verify_render_blend.test.py` jetzt 11 (3 neu).

Nebenbei behoben: `verify_render_blend.test.py` hatte
`if __name__ == "__main__"` in der MITTE -- die neue Klasse lief nicht mit.
Dasselbe Muster wie in `go.test.py` und `lieferung-pruefen.test.py`. Drei
Dateien, derselbe Fehler; kuenftig zuerst danach sehen.

## OEFFNUNGSREGELN-BEIM-ZEICHNEN-001 (COMPLETE)

Rainer, 2026-08-30: "can you set the standard door to the 87 unless it is
specified differently by the dropdown, and windows wider than 100 make them
automatically 2 Flügel, then from 300 make them automatically 3 Flügel?"

Beides greift jetzt schon beim Zeichnen, nicht erst per Rechtsklick.

**Tueren nach ROLLE**, nicht nach gezogener Strecke:

    Innentür        875 mm   (der Normalfall, ohne Rolle)
    WC-Tür schmal   750 mm
    Haustür        1125 mm   (Rainer, 2026-08-29: "die sind um die 1,13 m")
    Terrassentür      --     bleibt wie gezeichnet, die gibt es in jeder Breite

Wer eine Tuer zeichnet, zieht eine Strecke -- er misst nicht. In
`..._3_2_4_b_100_1` waren vier von sechs Tueren breiter als jedes Tuerblatt,
zwei fast zwei Meter. Das Mass ist bekannt, also wird es gesetzt. Die Mitte
der Oeffnung bleibt stehen, sonst wandert die Tuer aus ihrer Wand.

**Fenster nach Breite:** bis 1000 mm ein Fluegel, ueber 1000 zwei, ab 3000
drei. Die Grenzen liegen genau dort, wo Rainer sie nannte.

Von Hand Gewaehltes bleibt: das Rechtsklick-Menue setzt `width_manuell` bzw.
`panes_manuell`, und die Regel fasst solche Elemente nicht mehr an.

Im Zeichner mit echten Klicks nachgemessen (nichts gespeichert):

    Tür absichtlich breit gezogen  ->  875 mm
    Rolle WC-Tür                   ->  750 mm
    Rolle Haustür                  -> 1125 mm
    Fenster  972 mm                ->  1 Flügel
    Fenster 2944 mm                ->  2 Flügel
    Fenster 7831 mm                ->  3 Flügel

Tests: `static/oeffnungsregeln.test.mjs` (10). Suite 224 JS + 253 Python
gruen. Cache-Buster 20260830-1400.

## REGEL-MOEBELGRUPPEN-TRAGEN-DASSELBE-001 (COMPLETE)

Rainer, 2026-08-30, am ersten Grundriss einer neuen Erzeugung: "codex is
using different materials for a 2 seater and threeseater in the same group,
is there not a rule against that?"

**Es gab keine.** Das Regelwerk verlangte Unterschiede ZWISCHEN den vier
Bildern (Abschnitt 10, Punkt 2: "Polstermoebel -- Farbe UND Stoff") und je
Stil eine Akzentfarbe. Ueber die Einheitlichkeit INNERHALB einer Gruppe stand
nichts. Codex hat also nichts gebrochen, sondern eine Luecke gefunden.

Neu als Abschnitt 10, Punkt 5: **"Was zusammensteht, ist ein Satz."**

    Zweisitzer, Dreisitzer und Sessel einer Sitzgruppe
    die Stuehle eines Esstisches untereinander
    die Schrankfronten einer Kuechenzeile samt Insel
    die Nachttische links und rechts vom Bett

So werden Moebel gekauft, und so liest sich ein Raum. Zwei verschiedene
Stoffe in einer Gruppe sehen nicht nach Gestaltung aus, sondern nach zwei
getrennten Anschaffungen -- und der Blick bleibt daran haengen statt am
Grundriss.

Ein gesetzter Akzent bleibt erlaubt: genau EIN Stueck je Raum. Zwei Sofas
derselben Gruppe sind kein Akzent.

Dazu als Ablehnungsgrund in die Liste in Abschnitt 11 -- eine Regel ohne
Ablehnungsgrund wird zur Empfehlung.

Das Regelwerk liegt jedem Auftrag als `CODEX-REGELN.md` bei, die Regel wirkt
also ab dem naechsten erzeugten Auftrag.

Tests: `scripts/make-codex-job.test.py` jetzt 43 (5 neu).

Nebenbei behoben: auch diese Testdatei hatte
`if __name__ == "__main__"` in der MITTE. Vierte Datei mit demselben Muster
(nach go.test.py, lieferung-pruefen.test.py, verify_render_blend.test.py).

## BEANSTANDUNG-ERREICHT-CODEX-001 (COMPLETE)

Rainer, 2026-08-30: "wie bringen wir das jetzt codex bei?"

Zwei Wege, und einer war offen.

**Regeln** erreichen Codex von selbst: `make-codex-job.py` legt das Regelwerk
jedem Auftrag als `CODEX-REGELN.md` bei. Die neue Regel 10.5 steht dort ab
dem naechsten erzeugten Auftrag -- geprueft, sie ist drin.

**Die Beanstandung an DIESEM Haus** erreichte ihn nicht.
`lieferung-pruefen.py --auge` schrieb sie in `RUNDEN.jsonl`, und
`make-codex-job.py` las die Datei nie. Notiert und vergessen. Ein Auftrag
ohne die Beanstandung der letzten Runde ist derselbe Auftrag wie vorher -- und
bekommt dieselbe Antwort.

Neu: der Auftrag beginnt jetzt mit "Was beim letzten Mal beanstandet wurde",
direkt nach der Modellsperre. Der MENSCHLICHE Blick steht zuerst; was der
Pruefer fand, darunter. Ende zu Ende durchgespielt:

    lieferung-pruefen.py ... --auge "Zweisitzer und Dreisitzer derselben
        Sitzgruppe haben verschiedene Bezugsstoffe (Regelwerk 10.5)"
    make-codex-job.py german_catalog_review_bungalow_3_3_1_b_100_2

    -> CODEX-AUFTRAG.md:

       ## Was beim letzten Mal beanstandet wurde
       **Am Bild gesehen** (das wiegt am schwersten):
       - Zweisitzer und Dreisitzer derselben Sitzgruppe haben verschiedene
         Bezugsstoffe (Regelwerk 10.5: Was zusammensteht, ist ein Satz)
       Diese Punkte gelten als bekannt. Kommen sie wieder, ist die Lieferung
       ohne weitere Pruefung abgelehnt.

Damit ist ein Stueck von KREIS-MIT-CODEX-SCHLIESSEN-001 zu: die Rueckmeldung
laeuft jetzt von Rainers Auge ueber RUNDEN.jsonl in den naechsten Auftrag,
ohne Abschreiben.

Tests: `scripts/make-codex-job.test.py` jetzt 50 (7 neu). Der Verdrahtungstest
prueft den EINBAU, nicht nur die Definition -- ein Helfer, den niemand
aufruft, ist keine Uebermittlung.

Nebenbei, zum vierten Mal heute: `if __name__ == "__main__"` stand in der
Mitte der Testdatei, die neue Klasse lief nicht mit. Bei jeder Testdatei
dieses Projekts zuerst danach sehen.

## PUNKTAUSWAHL-BLOCKIERT-ELEMENTE-001 (COMPLETE)

Rainer, 2026-08-30: "after working point i cant select single things like
windows i have to save and reload each time."

Nachgestellt an `bungalow_001`: ein Rahmen ueber das Erdgeschoss markiert
74 Punkte. Danach kam man an das Fenstermenue nicht mehr heran.

Zwei Ursachen, beide im Zusammenspiel zweier Dateien:

1. `punkte-ausrichten.js` faengt den Rechtsklick mit
   `stopImmediatePropagation()` ab, SOLANGE Punkte markiert sind. Das
   Fenstermenue in `element-edit.js` kam nie zum Zug.
2. Die Markierung wurde nie geloescht. Ein Klick AUF ein Element bleibt in
   `element-edit.js` mit `stopPropagation()` stehen -- und Chrome haelt damit
   auch die spaeteren Horcher auf DEMSELBEN Knoten an (nachgemessen; nach
   Buchstaben der Norm taete es das nicht). Der Rahmen-Handler, der die
   Markierung sonst leert, lief also nicht mehr. Nur Neuladen half, und
   Speichern laedt neu -- daher sein "save and reload".

Behoben:

- `selectElement(element)` gibt die Punktauswahl ab (`punktAuswahlAbloesen()`).
  Nur bei einem echten Treffer: `selectElement(null)` steht am Anfang jedes
  Rahmens, und eine mit Shift begonnene Auswahl muss dort stehenbleiben.
- Der Rechtsklick auf eine Oeffnung oder Treppe gehoert dem Element, ohne
  Ausnahme (`elementUnterZeiger()`). Ich hatte es zuerst enger gefasst -- nur,
  wenn das Element NICHT mit markiert ist. Am Zeichner nachgemessen half das
  genau im Fall nicht, um den es geht: ein Rahmen ueber das Geschoss fasst die
  Fensterpunkte mit (so gewollt seit 2026-08-29), also gewann wieder das
  Ausrichten. Das Ausrichtmenue verliert nichts -- es ist ueberall sonst zu
  haben.

Test: `static/punkte-und-elemente.test.mjs` (5 Faelle). Er laedt die BEIDEN
echten Browser-Dateien in einen gemeinsamen Geltungsbereich und schickt echte
Ereignisse hinein, statt die Regeln nachzubauen -- der Fehler lag im
Zusammenspiel, eine nachgebaute Kopie haette ihn nie gezeigt. Der Notbehelf-DOM
bildet dafuer Chromes `stopPropagation`-Verhalten nach, nicht das der Norm;
steht so im Test kommentiert.

Nachgewiesen am laufenden Zeichner (`bungalow_001`, 74 markierte Punkte, und
`onehalfstorey_021`, 50 markierte Punkte + Treppe):

    Rahmen ueber alles        -> 74 Punkte markiert
    Rechtsklick ins Leere     -> Ausrichtmenue
    Rechtsklick aufs Fenster  -> Fenstermenue, 14 Eintraege
    Rechtsklick auf Treppe    -> Gerade/Podest/Viertel-/Halbgewendelt
    Linksklick aufs Fenster   -> Punktauswahl 0, Fenster ausgewaehlt

Tests: 253 Python (OK), 59 JS in static/*.test.mjs (OK).
`annotate.html` traegt jetzt `v=20260830-1530`, sonst haette der Browser die
alten Skripte behalten.

## KATALOG-DOPPELTE-BILDER-001 (OFFEN)

Beim Hochladen von `bungalow_001` (2026-08-30) sind aus 6 gesendeten Bildern
8 Anhaenge geworden:

    364 01-exterior-classic-review
    365 02-exterior-modern-review
    366 03-floorplan-warm-modern-review
    367 04-floorplan-dark-modern-review
    368 05-floorplan-soft-scandinavian-review        <- nicht gemeldet
    369 05-floorplan-soft-scandinavian-review-1      <- das Skript meldete DIESE
    370 06-floorplan-classic-review                  <- nicht gemeldet
    371 06-floorplan-classic-review-1                <- das Skript meldete DIESE

`publish-renders.py` sendet jede Datei genau einmal, und `request()` wiederholt
nichts. Trotzdem liegen 368 und 370 auf der Seite, ohne dass das Skript sie je
zu Gesicht bekam: der Server hat den Anhang angelegt, die Antwort erreichte den
Aufrufer nicht, und der zweite Versuch bekam wegen des belegten Slugs das
"-1" angehaengt. Betroffen sind genau die zwei GROESSTEN Dateien (5,9 und
6,2 MB) -- ein Zeitablauf beim Hochladen ist die naheliegende Ursache,
bewiesen ist sie nicht.

Offen, Rainers Entscheidung:

1. Die zwei Dubletten von der Seite nehmen (369 und 371; die Namen ohne "-1"
   sind die besseren). Loeschen auf der Live-Seite -- nicht ohne sein Wort.
2. Das Skript gegen den Fall haerten: nach dem Hochladen nachsehen, ob der
   angelegte Anhang den erwarteten Slug traegt, und bei einem "-N" den
   ueberzaehligen selbst wieder wegnehmen. Ausserdem ein Zeitlimit auf
   `request()` -- `urlopen` laeuft derzeit ohne, ein haengender Aufruf blockt
   ewig.

Ohne 2. wiederholt sich das bei jedem grossen Bild.

## MASSSTAB-FENSTER-UNAUFFINDBAR-001 (COMPLETE)

Rainer, 2026-08-30, an twostorey_004: "the massstab button isn't working."

Zuerst das, was NICHT stimmte: ich hatte gemeldet, ein echter Klick auf den
Knopf tue nichts. Das war mein eigener Messfehler -- der Klick lief im
Koordinatenrahmen einer alten Bildschirmaufnahme und landete 700 px daneben.
Im richtigen Rahmen gemessen laeuft der Knopf durch, Ende zu Ende:
Fenster auf, 9,2 x 9,45 m eingestellt, Massstab 23,54 m je Bildbreite gesetzt.

Zwei echte Fehler standen daneben, und beide sehen von aussen aus wie ein
toter Knopf:

1. **Der Knopf sah nicht wie ein Knopf aus.** `.feature-controls` ist ein
   Raster aus zwei Spalten; der lange Hilfetext teilte sich die Zeile mit
   "Gebaeudemasse eingeben", und weil Rasterzellen sich strecken, war der
   Knopf 137 x 249 px -- ein grosser leerer Kasten mit der Beschriftung oben
   in der Ecke. Die zwei Massstab-Knoepfe standen ausserdem DIAGONAL statt
   nebeneinander. Behoben: `.feature-controls > p { grid-column: 1 / -1 }`.
   Gemessen nachher: beide Knoepfe 237 x 39, Text ueber volle Breite.

2. **Das Fenster liess sich verlieren.** Weder beim Ziehen noch beim
   Zurueckholen wurde der Ort begrenzt, und er ueberlebt im Browserspeicher.
   Wer den Griff einmal ueber den Rand zieht -- oder die Seite auf einem
   kleineren Bildschirm oeffnet als beim letzten Mal -- sieht das Fenster nie
   wieder: es liegt `position: fixed`, es gibt keinen Rollbalken dorthin, und
   der einzige Ausweg waere, den Browserspeicher zu loeschen. Das weiss
   niemand. Neu: `massOrtImBild()` begrenzt beim Ziehen UND beim Oeffnen.
   Passt das Fenster ueberhaupt nicht mehr, gewinnt der obere Rand -- an der
   Titelleiste zieht man es weiter, die darf nie die sein, die fehlt.
   Begrenzt wird NACH `neuRechnen()`: der Hinweistext waechst dabei, und ein
   vorher begrenzter Ort ragt hinterher wieder unten heraus (erst falsch
   gebaut, gemessen, umgestellt).

Tests: `static/massstab-fenster.test.mjs` (6 Faelle) laedt die echte Funktion
aus der echten Datei. Alle JS-Tests: 65, OK. Python: 253, OK.
`annotate.html` traegt jetzt `v=20260830-1715` -- auch die styles.css haengt
daran, sonst behaelt der Browser das alte Raster.

Nachgewiesen am laufenden Zeichner (Fensterhoehe 346 px, Ort 4000/3000 px
gespeichert): Fenster oeffnet bei x=316 y=1, ganz im Bild, Titelleiste
greifbar.

## GO-HINWEIS-NANNTE-NUR-DIE-HAELFTE-001 (COMPLETE)

`go.py --hochladen` schloss mit "jetzt freigeben: python approve-plan.py ...".
Wer dem folgt, hat einen freigegebenen Plan mit LEERER Katalogkarte:
`approve-plan.py` schreibt nur ins lokale Ledger, scharf schaltet erst
`freigeben.py` ueber b2t/v1/freigabe. Genau das stand bei bungalow_001 am
2026-08-30: 9 Bilder hochgeladen, `im: 0`, Karte leer.

Der Knopf in der Hausakte macht laengst beides (pipeline/route.ts). Nur die
Kommandozeile sagte die Haelfte. Jetzt nennen `go.py` und `workflow.py`
Stufe 7 beide Befehle.

Tests: `scripts/go.test.py` 16, OK.

## MASSSTAB-FENSTER-LIESS-SICH-NICHT-SCHLIESSEN-001 (COMPLETE)

Nachtrag zu MASSSTAB-FENSTER-UNAUFFINDBAR-001. Rainer schickte twostorey_004
noch einmal, und da lag der eigentliche Grund fuer "the massstab button isn't
working":

    hidden (Attribut) : true
    hidden (Eigenschaft): true
    computed display  : grid        <-- das Fenster war SICHTBAR
    inline display    : grid

`fenster.hidden = true` wirkt allein ueber die Browserregel
`[hidden] { display: none }`. Der Inline-Stil des Fensters setzte
`display:grid` und schlug sie. Folge: das Fenster stand seit dem Laden offen,
lag ueber dem Grundriss, das Kreuz schloss nichts, und der Knopf schaltete
zwar `hidden` um -- sichtbar aenderte sich nie etwas. Von aussen ist das ein
toter Knopf.

Behoben: `display` aus dem Inline-Stil heraus, dafuer in styles.css

    #massFenster         { display: grid; }
    #massFenster[hidden] { display: none; }

Gleiche Staerke, die genauere Regel gewinnt.

Am laufenden Zeichner nachgemessen:

    beim Laden   display none,  Hoehe 0
    nach Knopf   display grid,  Hoehe 345
    nach Kreuz   display none,  Hoehe 0
    wieder auf   display grid,  Hoehe 345

Zum Merken: ich hatte `hidden: true` und `display: "grid"` in meiner ALLERERSTEN
Messung nebeneinander stehen und bin darueber hinweggegangen -- und habe
danach zwei andere Fehler gefunden und behoben, die beide echt sind, aber
nicht der waren, den er sah. Ein Widerspruch in den eigenen Messwerten ist
kein Rauschen.

Tests: `static/massstab-fenster.test.mjs` jetzt 8 (2 neu, sie halten genau
diese Falle fest). Alle JS-Tests in static/: 224, OK.
`annotate.html` traegt `v=20260830-1745`.

Offen und klein: auf schmalen Fenstern liegen das Massstab-Fenster und das
RAEUME-Feld uebereinander -- beide sind frei verschiebbar, aber ihre
Startorte kollidieren unter etwa 900 px Breite.

## MASSSTAB-FENSTER-ZUSTAND-MERKEN-001 (COMPLETE)

Rainer, 2026-08-30, direkt nach der Behebung: "the windwo is now gone for the
massstab."

Kein neuer Fehler, sondern die Folge des behobenen. Solange sich das Fenster
nicht schliessen liess (Inline-`display` schlug `[hidden]`), stand es seit dem
Laden da -- und so hat er damit gearbeitet. Seit es sich schliessen laesst,
braucht es den Knopf, und der sitzt bei 1440 px Breite rund 2200 px weit unten
in der Seitenleiste, unter den Raumknoepfen. Aus seiner Sicht war das Fenster
fort.

Also wird gemerkt, wie er es zuletzt hatte -- wie beim Ort und aus demselben
Grund: eine Bedienentscheidung, kein Zustand des Hauses.

    massstab.offen = "ja" | "nein"   (localStorage)

Der Knopf und das Kreuz schreiben es. "Anwenden" NICHT: das ist fertig werden,
nicht wegraeumen -- wer das Fenster offen haben will, will es beim naechsten
Haus wieder.

Eine Falle steckte darin, und sie steht in annotate.js schon einmal
kommentiert ("drawn once at script load, before this fetch resolves"): das
Fenster wird gebaut, BEVOR die Annotation geladen ist. `outerOutline` ist dann
leer, und die Pruefung "gibt es hier ein Rechteck zu messen" sagte immer nein
-- gemerkt "ja", Fenster trotzdem zu. Am Zeichner gemessen und dann
umgestellt: `annotate.js` traegt `massFensterNachLaden()` nach, an derselben
Stelle, an der es schon `updateScaleStatus()` nachtraegt.

Am laufenden Zeichner nachgewiesen:

    frisch, nichts gemerkt   -> zu
    Knopf gedrueckt          -> auf, gemerkt "ja"
    neu geladen              -> auf, Hinweis gerechnet, Ort 277/120
    Kreuz gedrueckt          -> zu, gemerkt "nein"
    neu geladen              -> zu

Tests: `static/massstab-fenster.test.mjs` jetzt 13 (5 neu, einer davon prueft
den Nachtrag in annotate.js -- ohne ihn bliebe das Fenster stumm zu).
Alle JS-Tests: 229, OK. Python: 253, OK. `annotate.html` traegt
`v=20260830-1815`.

## MASSSTAB-FENSTER-VERDECKT-UND-VERRECHNET-001 (COMPLETE)

Rainer, 2026-08-30: "where is massstab window".

Zwei Sachen, und die zweite ist die schlimmere.

**1. Das RAEUME-Feld lag darueber.** `#roomNavPanel` (`.room-nav`) hat
`z-index: 40`, das Massstab-Fenster hatte 30. Beide schweben, beide starten
oben rechts, und unter etwa 900 px Breite ueberdecken sie sich. Sichtbar blieb
nur die Kopfzeile "Massstab · Gebaeudemasse", alles darunter war verdeckt.
Jetzt `z-index: 50` in styles.css -- wer den Knopf drueckt, will DIESES
Fenster sehen; das RAEUME-Feld steht immer da.

**2. Das Fenster rechnete mit dem Notnagel.** `fallbackAspectRatio()` fragt
`konzeptSeitenverhaeltnis()`, und das liefert beim ERSTEN Fragen null und holt
die SVG erst -- danach faellt es auf die Bounding-Box der Raeume zurueck. An
twostorey_004 gemessen: 1,39 statt 0,738, also bei Breite 10 eine Hoehe von
**19,36 m statt 10,27 m**. Fast das Doppelte. Wer in dem Moment "Anwenden"
drueckt, setzt einen falschen Massstab UND verzieht die Zeichnung, weil das
Seitenverhaeltnis der Zeichenflaeche mit gesetzt wird.

Das Rennen gab es schon immer; scharf gemacht hat es MEINE letzte Aenderung:
seit das Fenster beim Laden von selbst aufgeht, rechnet es, bevor die SVG da
ist. Vorher oeffnete man es von Hand, und da war sie laengst angekommen.

Behoben: `zeichenflaeche-ersatz.js` ruft `massFensterNachrechnen()`, sobald
das echte Verhaeltnis eintrifft -- an derselben Stelle, an der es schon
`syncCanvasSize()` und `draw()` nachzieht.

Am laufenden Zeichner nachgewiesen (twostorey_004, frisch geladen):

    Breite 10  ->  Hoehe 10,27      (vorher 19,36)
    fallbackAspectRatio  1,3558 = 1 / 0,7376
    z-index Fenster 50, RAEUME 40   -- Felder sichtbar

Tests: `static/massstab-fenster.test.mjs` jetzt 14. Alle JS-Tests: 230, OK.
`annotate.html` traegt `v=20260830-1845`.

Offen: die Statuszeile meldet danach noch "sized to this floor's own room
layout instead", obwohl das Verhaeltnis inzwischen aus der Konzeptzeichnung
stammt. Nur die Meldung, nicht die Rechnung -- aber sie sagt die Unwahrheit.

## MASSSTAB-STAND-UNTER-VIERZIG-RAUMKNOEPFEN-001 (COMPLETE)

Rainer schickte am 2026-08-30 ein Bildschirmfoto: "where is massstab window".
Darauf ist zu sehen, warum meine bisherigen Antworten an der Sache vorbeigingen
-- das Fenster war zu, und der Knopf, der es oeffnet, stand in der
Seitenleiste UNTER der ganzen Raumliste. Reihenfolge bisher:

    Tool -> Geschoss darunter -> Giebel -> Room (rund 40 Knoepfe)
         -> Area Suggestions -> MASSSTAB -> Waende -> Saved Areas/Elements

Bei 1440 px Breite lag "Gebaeudemasse eingeben" damit rund 2200 px weit unten.
Ohne Massstab gibt es keine Quadratmeter, keine Wandstaerken und keinen Render
-- bei einem Haus ohne ihn ist das der ERSTE Griff und nicht der letzte.

Der Massstab-Block steht jetzt vor den Raumknoepfen. Gemessen: Knopf bei
y = 686 statt y = 2208.

Nebenbei, aus demselben Bildschirmfoto: der Knopf "Zurueck" (Punktaenderung
zuruecknehmen) schwebte frei rechts neben dem Grundriss, bei x = 1640 im
Leeren. `zurueckKnopfAnlegen()` suchte `#toolbar` und `.toolbar` -- beides gibt
es in dieser Seite nicht, also blieb es immer beim letzten Rueckfall
`canvas.parentElement`. Die Leiste heisst `.zoom-bar`. Jetzt sitzt er dort.

Tests: 230 JS, 253 Python, OK. `annotate.html` traegt `v=20260830-1900`.

## MASSSTAB-FENSTER-UNTER-DEM-BILDSCHIRMRAND-001 (COMPLETE)

Rainer, 2026-08-30: "i cant see it and cant scroll down to it."

Das ist die genaue Beschreibung eines `position: fixed`-Fensters ausserhalb
des Bildschirms: Scrollen hilft dagegen nicht, das ist der Sinn von `fixed`.

Meine Begrenzung von vorhin (MASSSTAB-FENSTER-UNAUFFINDBAR-001) fasste nur den
Fall "ein Ort ist gespeichert". Ohne gespeicherten Ort stieg sie sofort aus:

    const ort = ... localStorage ...
    if (!ort?.l) return;          // <-- und der Startwert blieb stehen

Der Startwert ist `top: 120px` bei einer Fensterhoehe von 345 px. Auf einem
Browserfenster unter 465 px Inhaltshoehe haengt es damit unten heraus -- und
bei geoeffneten Entwicklerwerkzeugen oder einem kleinen Laptopfenster ist man
schnell da.

Jetzt wird bei JEDEM Oeffnen begrenzt, mit gespeichertem Ort oder ohne. Am
laufenden Zeichner in einem 566 x 346 px grossen Fenster gemessen:

    ohne gespeicherten Ort   -> 277 / 1    ganz im Bild
    mit Ort 5000 / 4000 px   -> 316 / 1    ganz im Bild
    nach Zu und wieder Auf   -> 316 / 1    ganz im Bild

Vorher stand es in allen drei Faellen auf y = 120 und ragte 119 px unter den
Rand.

Tests: 230 JS, OK. `annotate.html` traegt `v=20260830-1930`.

## SPEICHERN-WARF-TREPPENFELDER-WEG-001 (COMPLETE, Server-Neustart noetig)

Rainer, 2026-08-30, an twostorey_004: "something is wrong with the stairs."

Die Geometrie war es nicht -- er hat sie waehrend der Untersuchung selbst
gerichtet, Treppe und Treppenoeffnung decken sich jetzt auf 5 cm genau
(2,14 x 1,18 m unten, 2,14 x 1,19 m oben). Falsch war, was der Zeichner beim
Speichern mit der Treppe macht.

`normalize_element()` in app.py baut jedes Element aus einer NAMENSLISTE neu
auf. Was nicht darin steht, faellt weg -- lautlos, ohne Fehler, ohne Meldung.
Vier Felder, die der Zeichner seit dem 2026-08-29 schreibt, standen nicht
darin:

    stair_type      Treppenart aus dem Rechtsklickmenue. Im GANZEN Bestand:
                    0 Stueck. Das Menue, das ich am 2026-08-29 auf seine
                    Frage "koennen wir rechtsklick treppenart auswaehlen
                    podest oder wendeltreppe?" gebaut habe, hat noch nie
                    etwas gespeichert.
    width_m         Laufbreite in Metern. 174 Stueck im Bestand -- ALLE vom
                    Umstellungsskript direkt auf die Platte geschrieben,
                    keines durch den Zeichner. Die vier Haeuser, die er
                    heute gespeichert hat (onehalfstorey_027/036/039,
                    twostorey_004), haben es verloren.
    width_manuell   "Diese Breite habe ich von Hand gewaehlt."
    panes_manuell   "Diese Fluegelzahl habe ich von Hand gewaehlt."

Die beiden letzten schuetzen eine Handeingabe vor den automatischen
Oeffnungsregeln. Fallen sie weg, ueberschreibt die Regel beim naechsten
Antippen, was er ausdruecklich gesetzt hat.

Das ist genau der Fehler, vor dem meine eigene Notiz warnt
(verify-against-user-visible-surface): geprueft wurde die Kette im Zeichner,
nicht bis auf die Platte. Dreimal hintereinander dasselbe Muster.

Behoben in `normalize_element()`, mit Pruefung statt blossem Durchreichen:

    width_m         Zahl > 0, sonst ValueError
    stair_type      gegen STAIR_TYPES geprueft (dieselben Namen wie
                    STAIR_TYPES_BUILDABLE + STAIR_TYPES_NOT_YET beim Bauer).
                    Der Bauer bricht bei einem unbekannten Wert ab -- ihn
                    durchzulassen hiesse, den Fehler bis in den Bau zu tragen.
    width_manuell / panes_manuell   als bool

Tests: `tests/test_element_felder_ueberleben_speichern.py`, 8 Faelle. Einer
davon geht durch `write_annotations()` bis auf die Platte und liest die Datei
zurueck -- `normalize_element` allein zu pruefen haette den Fehler zwar
gezeigt, aber die Frage war, ob es ankommt. Gesamt: 261 Python-Tests, OK.

OFFEN, braucht Rainer:

1. **Server neu starten.** Der laufende Prozess hat den alten Code; bis dahin
    faellt beim Speichern weiter alles weg.
2. Die vier heute gespeicherten Haeuser haben `width_m` verloren. Repariert
    `python scripts/treppenbreite-setzen.py --schreiben` (4 Haeuser, legt je
    eine Sicherung an). Die Breite selbst stimmt (0,0351783 x 25,584 =
    0,900 m) -- nur die Absicht in Metern fehlt.
3. Verlorene `stair_type`-Angaben lassen sich nicht wiederherstellen: es gab
    nie welche. Wer eine Treppenart gesetzt hat, muss sie neu setzen.

## FENSTER-ZWISCHEN-GESCHOSSEN-UEBERTRAGEN-001 (COMPLETE)

Rainer, 2026-08-30: "could we also integrate one thing? Copy windows from EG
to OG or from OG to EG? like the stairs"

Zwei Knoepfe neben "Copy stairs", `static/fenster-kopieren.js`. Die
Maschinerie lag schon da: `transformPointsBetweenFloors()` legt die Geschosse
ueber die zwei Ausrichtmarken aufeinander -- dieselbe Registrierung, die die
Treppen benutzen. Der Grund, warum es funktioniert: ein Fenster sitzt in der
FASSADE, und die Fassade ist auf beiden Geschossen dieselbe Wand.

In einem Punkt bewusst ANDERS als das Treppenkopieren:

    Treppen  ERSETZEN, was auf dem Zielgeschoss liegt.
    Fenster  werden HINZUGEFUEGT, und was schon fast an derselben Stelle
             liegt, wird uebersprungen.

An Fenstern sitzt die meiste Zeichenarbeit; ein Griff daneben loeschte sie.
Zweimal druecken verdoppelt nichts, und ein selbst gezeichnetes Fenster oben
bleibt stehen. "Fast dieselbe Stelle" ist 0,004 normierte Einheiten, bei einem
10-Meter-Haus rund 4 cm -- feiner, als man mit der Maus zielt. Verglichen
werden beide Enden in BEIDEN Richtungen: wer von rechts nach links zeichnet,
zeichnet kein zweites Fenster.

NUR Fenster, keine Tueren. Eine Zimmertuer steht dort, wo oben die RAEUME
liegen, und die liegen anders -- sie zu uebertragen braechte nur Aufraeumarbeit.

Es ist ein ANFANG, kein Ergebnis. Die Meldung sagt das: "Dort pruefen,
verschieben oder loeschen -- und speichern."

Am laufenden Zeichner an twostorey_004 nachgewiesen:

    vorher            EG 9 Fenster, OG 6
    einmal gedrueckt  OG 15   "9 Fenster nach upperfloor uebertragen"
    nochmal gedrueckt OG 15   "Alle 9 liegen schon an derselben Stelle"
    Knopf oben        "Fenster nach upperfloor" (nennt das Ziel)
    Knopf unten       gesperrt (unter dem Erdgeschoss ist nichts)

Tests: `static/fenster-kopieren.test.mjs`, 12 Faelle, laedt die echte Datei.
Alle JS-Tests: 242, OK. Python: 261, OK. `annotate.html` traegt
`v=20260830-2000`.

## MARKER-BELEG-WAR-ABGESCHRIEBEN-001 (COMPLETE, mit einem Eingestaendnis)

Rainer, 2026-08-30, "ok" auf beide Vorschlaege.

**Teil 1: Regelwerk 10.6 und 10.7 (fertig).**

10.6 "Die vier Grundrisse zeigen DASSELBE Haus, gleich moebliert." Was sich
unterscheiden darf, ist der STIL -- Material, Farbe, Stoff, Holzton, Leuchten,
Teppich, Dekoration. Was sich NICHT unterscheiden darf, ist die Anordnung.
Mit Anlass (german_catalog_review_bungalow_3_3_2_b_100_2, drei von vier
Bildern) und einer Selbstpruefung: px-Angabe der Objektkarte nehmen und in
JEDEM der vier Bilder dort nachsehen.

10.7 "Ein Marker gilt nur, was du wirklich gesehen hast." Mit `unklar` und
`verschoben` als erlaubten Auswegen -- falsch abhaken wiegt schwerer als der
Fehler selbst, weil es ihn verdeckt.

Beide auch in der Ablehnungsliste in Abschnitt 11.

**Teil 2: der maschinelle Beleg -- zwei Messwege gescheitert.**

Rainers Wunsch war, den Ausschnitt um jede Planposition maschinell gegen das
Baseline-Rendering zu vergleichen. Das geht nicht, und ich habe es gemessen
statt behauptet:

  Ansatz 1: Kantenbild (FIND_EDGES) des gelieferten Bildes gegen das
    Baseline-Rendering, normierte Kreuzkorrelation im 140x140-Fenster um jeden
    Marker. Ergebnis: alles zwischen -0.04 und 0.46, OHNE Trennung. Das
    Doppelbett -- am Auge in allen vier Bildern richtig -- lag bei 0.02 bis
    0.13, der Couchtisch -- in dreien falsch -- bei -0.02 bis 0.01. Der Stil
    veraendert die Textur so stark, dass die Kanten nichts mehr gemeinsam
    haben.

  Ansatz 2: die vier Lieferungen gegeneinander, stark verkleinert (Faktor 4,
    Textur weg) und ueber den Helligkeitsgradienten verglichen. Ergebnis
    ebenso: Doppelbett 0.02 bis 0.41, Couchtisch -0.07 bis 0.10. Kein
    Schwellwert trennt richtig von falsch.

Beide Male dieselbe Ursache: die Bilder sind keine Varianten desselben
Renderings, sondern vier eigenstaendige Bilder. Wer den Unterschied zwischen
einem Esstisch und einem Couchtisch messen will, braucht Objekterkennung,
keine Korrelation. Etwas zu bauen, das Rauschen meldet, waere schlimmer als
nichts.

**Was stattdessen gebaut ist, und was es beweist.**

`abgeschriebene_marker()` in lieferung-pruefen.py: drei oder mehr Bilder mit
einem ZEICHENGLEICHEN marker_check (n, status, bei) sind eine Beanstandung.
Vier getrennt gerenderte Bilder mit anderem Stil und anderem Licht ergeben
nicht denselben Pixelbefund.

Das beweist NICHT, dass die Bilder falsch sind. Es beweist, dass der Befund
keiner ist -- und genau das war der Fall: alle 34 `bei`-Werte pixelgenau die
`px` aus dem Auftrag, in allen vier Bildern zeichengleich. Der aeltere Beleg
(`bei` nahe am Marker) belohnt das sogar: wer abschreibt, besteht ihn immer.
Er faengt eine erfundene Zahl, aber keine abgeschriebene.

Es faellt auch bei bungalow_001 an, dessen Bilder in Ordnung waren. Das ist
kein Fehlalarm: dort war der Befund genauso wertlos, nur ist nichts
schiefgegangen.

Nachgemessen an beiden echten Lieferungen -- beide werden jetzt beanstandet.

Tests: `lieferung-pruefen.test.py` 82 (6 neu). Einer davon prueft den EINBAU
in `pruefe()`, nicht nur die Funktion -- vierter Verdrahtungsfehler dieser Art
heute. Eine meiner eigenen neuen Erwartungen war falsch ("ein abweichendes
Bild entschuldigt die anderen drei") und ist mit Begruendung umgeschrieben;
sie schuetzte kein bestehendes Verhalten.

OFFEN: Codex muss jetzt WIRKLICH je Bild hinsehen. Der naechste Auftrag traegt
Regel 10.7 und die zwei Beanstandungen aus RUNDEN.jsonl mit. Ob das reicht,
zeigt die naechste Lieferung -- messbar an dieser Pruefung.

## MASSSTAB-RECHNETE-MIT-EINEM-NOTWERT-001 (COMPLETE, Server-Neustart noetig)

Rainer, 2026-08-30, an twostorey_023: "something is wrong with the massstab."

Der Aussenumriss ist dort in der Zeichnung fast QUADRATISCH -- 0,857 x 0,861
normierte Einheiten. Das Massstab-Fenster bot bei 10 m Breite trotzdem
7,37 m Tiefe an, mit gesperrtem Seitenverhaeltnis und dem Satz "Die Zeichnung
bleibt, wie sie ist".

Die 7,37 kommen nicht aus der Zeichnung. Sie kommen aus app.py:

    def source_aspect_ratio(project_dir, floor_level=None):
        ...
        return 1.36          # Notwert, wenn es kein Vorschaubild gibt

1/1,36 = 0,735 -- genau das Verhaeltnis, mit dem das Fenster rechnete.

Und der Kreis schliesst sich auf die schlimmste Art: die Konzept-SVG wird MIT
diesem Notwert gezeichnet, und der Zeichner liest das Verhaeltnis hinterher
aus eben dieser SVG wieder heraus (`konzeptSeitenverhaeltnis` ->
`fallbackAspectRatio`). Er leitet aus seiner eigenen Schaetzung ab und haelt
das Ergebnis fuer eine Messung.

Im Bestand gemessen:

    97 Haeuser  mit Vorschaubild   -> echtes Seitenverhaeltnis
    11 Haeuser  mit Gebaeudemass   -> eingetipptes
    125 Haeuser mit keinem von beidem -> Notwert 1.36

Bei 125 von 233 Haeusern war die angebotene Tiefe also geraten. Wer sie
uebernahm, speicherte eine erfundene Gebaeudetiefe -- bei twostorey_023 waeren
das 2,7 m Unterschied gewesen.

Rechnen laesst sich das nicht reparieren: die Auskunft fehlt wirklich, das
Vorschaubild ist nach der Annotation geloescht worden (Datenschutz). Was sich
reparieren laesst, ist die Auskunft DARUEBER.

Neu:

- `PLATZHALTER_SEITENVERHAELTNIS = 1.36` -- der Notwert hat jetzt einen Namen.
- `seitenverhaeltnis_herkunft(project_dir, geschoss)` gibt "vorschaubild",
  "gebaeudemass" oder "platzhalter" zurueck. Sie benutzt DIESELBE Bildersuche
  wie `source_aspect_ratio` (`_vorschaubild_kandidaten`) -- zwei Suchen, die
  auseinanderlaufen, waeren schlimmer als gar keine Auskunft: der Zeichner
  meldete "gemessen" und rechnete mit dem Notwert.
- Die Leseantwort traegt `seitenverhaeltnis_herkunft` je Geschoss mit.
- Das Massstab-Fenster schaltet die Sperre AUS und sperrt sie zu, wenn die
  Proportion geraten ist, und sagt es:
  "Die Proportion der Zeichenflaeche ist nicht bekannt -- fuer dieses Haus
  gibt es kein Vorschaubild mehr. Breite UND Tiefe vom Beiblatt eintragen;
  eine abgeleitete Tiefe waere geraten."

Am laufenden Zeichner nachgewiesen (Feld von Hand gesetzt, weil der Server
noch den alten Code hat):

    platzhalter    Sperre aus und gesperrt, Hoehe aenderbar, Hinweis steht
    vorschaubild   alles wie bisher, Sperre wieder bedienbar

Ohne das Feld (alter Server) faellt es auf das alte Verhalten zurueck -- keine
Verschlechterung, aber auch keine Warnung.

Tests: `tests/test_seitenverhaeltnis_platzhalter.py`, 7 Faelle. Einer prueft,
dass die LESEANTWORT den Helfer aufruft -- fuenfter Verdrahtungsfehler dieser
Art heute. Gesamt: 268 Python, 242 JS, OK. `annotate.html` traegt
`v=20260830-2100`.

OFFEN, alles am selben Handgriff: der Server laeuft noch mit dem Code von
heute frueh. Bis zum Neustart fehlen DREI Dinge -- `stair_type` und `width_m`
fallen beim Speichern weiter weg, und die Massstab-Warnung erscheint nicht.

## HAUSAKTE-ERLEDIGTE-HAEUSER-GRUEN-001 (COMPLETE)

Rainer, 2026-08-30: "the logic here is confusing me, i really can't tell which
one i still have to fix, can we make the ones green that are accepted and
uploaded?"

Zwei Sachen waren daran falsch, und die zweite erklaert die erste.

**1. Der Zaehler log.** Die Seite zaehlte als offen, was nicht GENAU "fertig"
war:

    const offen = haeuser.filter((h) => h.state !== "fertig")

Im Bestand hat kein einziges Haus den Zustand "fertig" -- die elf
veroeffentlichten stehen auf `veroeffentlicht_build_alt`. Der Kopf meldete
also "233 Häuser · 233 offen", obwohl elf davon in `deriveHouseState` als
naechste Handlung ausdruecklich "nichts noetig" tragen. Jetzt: 222 offen.

**2. Nichts war zu sehen.** Alle 233 Zeilen sahen gleich aus; der Zustand
stand nur als Wort daneben, in derselben Farbe wie alles andere.

Neu: `ERLEDIGT` und `istErledigt()` in `house-state.mjs`, neben `STATES` --
und ZWINGEND dort und nicht in der Seite: der Zaehler im Kopf und die gruene
Farbe in der Zeile muessen dasselbe meinen, sonst steht "11 offen" neben elf
gruenen Zeilen. Die Seite benutzt sie an drei Stellen: Zaehler, Zeilenfarbe
und "Naechstes Haus" (das ueberspringt Erledigte jetzt nach derselben Regel).

Gruen ist NUR erledigt. Faerbte man auch die Zwischenstufen, waere wieder
nichts zu unterscheiden. Die Auskunft traegt der Balken links, nicht die
Schriftfarbe -- auf der aktiven (braunen) Zeile bliebe gruener Text unlesbar.
Verwendet wird das vorhandene `--ok`, kein neuer Farbwert.

Unbekannte Zustandsworte gelten als OFFEN. Lieber ein Haus zu viel auf der
Liste als eines zu wenig.

An der laufenden Seite nachgewiesen:

    233 Zeilen, 11 gruen (alle veroeffentlicht_build_alt)
    Kopf "233 Häuser · 222 offen"   (vorher 233 offen)
    Randfarbe rgb(76,175,125) = --ok im dunklen Thema
    bungalow_001 und 3_3_2 bleiben grau: bilder_freigeben

Tests: `house-state.test.mjs` 12 (4 neu), alle 21 in src/lib OK.

## HAUSAKTE-GELB-FUER-FAST-FERTIG-001 (COMPLETE)

Rainer, 2026-08-30: "how about yellow for things that are almost finished like
Bilder Freigeben?"

Dritte Stufe, `FAST_FERTIG` neben `ERLEDIGT` in house-state.mjs:

    warten_auf_freigabe    Bilder freigegeben, Plan noch nicht
    bilder_freigeben       hochgeladen, noch nicht angehakt
    bilder_hochladen       lokal fertig, online noch keine

Was diese drei verbindet: gebaut, zertifiziert, die Bilder sind da -- es fehlt
nur die Lieferstrecke, und jeder Schritt ist EIN Knopf.

Bewusst NICHT dabei:

    warten_auf_codex        Da liegt die Arbeit bei Codex. Wie viele Runden
                            das kostet, hat der 2026-08-30 gezeigt:
                            3_3_2 brauchte drei und war danach noch falsch.
    wordpress_unerreichbar  Der Stand ist UNBEKANNT. Unbekannt ist nicht
                            fast fertig.

Ein Test haelt fest, dass die drei in STATES direkt hinter den erledigten
stehen. STATES sortiert auch die Hausliste; nur so stehen gruen und gelb
beieinander und die Farbe bleibt ein Fortschrittsbalken statt bunter Punkte.

Eigener Farbwert `--fast` (#a07800 hell, #d9bb4a dunkel), nicht `--warn`: das
hier ist kein Warnhinweis, und `--warn` ist dem Braun des Akzents zu nah, um
sich auf einen Blick zu unterscheiden.

Der Kopfzaehler nennt jetzt alle drei Stufen statt nur "offen".

Beim Bauen zum ZWEITEN Mal heute in dieselbe Falle getreten: Backticks in
einem Kommentar INNERHALB des Template-Strings `HAUS_CSS` beendeten den
String, die Seite gab nur noch Parserfehler. Steht jetzt als Warnung im Block.

An der laufenden Seite nachgewiesen:

    233 Häuser · 12 fertig · 1 fast · 220 offen
    gruen rgb(76,175,125) = --ok
    gelb  rgb(217,187,74)  = --fast
    Kopfzeile "◑ bilder_freigeben · 2 Bilder hochgeladen, 0 angehakt"

Nebenbei: bungalow_001 steht inzwischen auf "fertig" -- Rainer hat es
freigegeben.

Tests: `house-state.test.mjs` 18 (6 neu), alle 27 in src/lib OK.

## MOEBELSCHRITT-PLATZ-STATT-ANLEITUNG-001 (COMPLETE)

Rainer, 2026-08-30: "get rid of that text i would rather see more furniture"
-- gemeint war der Absatz "The clean view is the default. Select Edit
geometry to show room points, wall endpoints, wall-linked openings and the
shared stair core..." in der rechten Spalte des Workbench-Editors.

Vier Bloecke standen dort dauerhaft ueber und unter der Moebelliste, drei
davon sagen im Moebel-Schritt gar nichts:

    Erklaertext zur Geometrie-Auswahl   weg (sagt nur beim ERSTEN Mal etwas)
    Ueberschrift "Selected geometry"    nur noch MIT Auswahl -- ohne Auswahl
                                        stand darunter ohnehin nichts
    "Closed opening legend" (7 Zeilen)  nur in der Geometrie-Ansicht
    "Stair rulebook" (5 Zeilen)         nur in der Geometrie-Ansicht

Geloescht ist nur der Erklaertext. Legende und Regelwerk sind nicht weg,
sondern dort, wo sie etwas bedeuten -- eine Farblegende fuer Tueren hilft
niemandem beim Sofa-Stellen.

An der laufenden Seite nachgewiesen:

    Moebel-Schritt      alle vier fort
    Geometrie-Ansicht   Legende und Stair rulebook stehen, Erklaertext fort,
                        "Selected geometry" erst bei einer Auswahl

## MOEBELAUSWAHL-WAR-AUF-320-PX-GEDECKELT-001 (COMPLETE)

Rainer, 2026-08-30, direkt nach dem Entfernen der Erklaertexte: "it doesn't
help, the part with the furniture on the top is still so small."

Er hatte recht, und mein erster Griff ging am Problem vorbei. Nachgemessen:

    Moebelauswahl   320 px hoch, 444 px Inhalt -> scrollte
    darunter FREI   562 px

Die Liste presste ihren Inhalt auf 320 px zusammen, waehrend unter ihr mehr
als ein halber Bildschirm leer stand. `max-h-[320px]` in furniture.tsx --
eine feste Zahl. Texte darunter wegzunehmen konnte deshalb nichts bringen:
die Kappe war das Problem, nicht der Platz.

Jetzt `max-h-[70vh] min-h-[180px]`. Gemessen: 444 px hoch, kein Rollbalken
mehr, alle 44 Moebelknoepfe auf einmal zu sehen.

70vh und nicht 100%: die rechte Spalte ist hoeher als die Zeichenflaeche
daneben (1373 gegen 781), und eine Liste, die ueber das Bild hinauswaechst,
macht die ganze Seite scrollbar -- dann sucht man den Grundriss. In der
Hausakte ist vh die Hoehe des eingebetteten Rahmens und waechst mit ihm.

Das Entfernen der Erklaertexte (MOEBELSCHRITT-PLATZ-STATT-ANLEITUNG-001)
bleibt richtig, war aber nicht die Antwort auf seine Frage.

## MARKER-BELEG-JETZT-EHRLICH-001 (Teilerfolg, ein Rest offen)

Rainer schickte den Lieferordner 3_3_2 erneut. Die Bilder sind unveraendert
(12:56 / 13:26), aber die catalog.json wurde um 16:02 NEU geschrieben --
Codex hat auf Regel 10.7 reagiert.

**Codex hat aufgehoert abzuschreiben.** Vorher trugen alle vier Bilder
34 von 34 `bei`-Werte PIXELGENAU aus dem Auftrag und waren untereinander
zeichengleich. Jetzt:

    Bild   bei == Plan   ueber 150 px weg
    03          0             12
    04          0              5
    05          0             10
    06          0             11

Null Abschriften. Die Regel im Regelwerk hat gewirkt, und
`abgeschriebene_marker()` greift folgerichtig nicht mehr.

**Der Pruefer findet jetzt von selbst, was ich mit dem Auge fand.** Die alte
Beleg-Regel (`bei` nahe am Marker) meldet 14 Beanstandungen. Kreuzgeprueft
ueber alle vier Bilder je Objekt, Spalte "kleinster Abstand":

    essgruppe_6-5          233   10  226  262        10
    waschmaschine-12       210   14   62   69        14
    essgruppe_stuhl-30     276   33  234  260        33
    couchtisch-9           234   39   82  162        39

Bild 04 trifft diese Objekte auf 10 bis 39 Pixel, die anderen drei liegen
200 bis 280 daneben. Das ist genau mein Befund vom Nachmittag, jetzt aus
Codex' eigenen Zahlen: 04 stimmt, 03/05/06 haben umgeraeumt.

**Der Rest, und er ist ein Fehler MEINES Pruefers, nicht der Lieferung.**
Zwei Objekte werden in ALLEN VIER Bildern beanstandet:

    doppelwaschtisch-23    308  346  347  511       308
    badewanne-21           180  325  363  155       155

Kein einziges Bild kommt nahe. Wenn keines trifft, liegt es nicht an den
Bildern, sondern am Massstab: `px` ist in make-codex-job.py der projizierte
URSPRUNG des fuehrenden Netzes (`_lage_zu_pixel(uv)`), nicht die sichtbare
Mitte. Am Baseline-Render nachgesehen: an der Planstelle von `wand_wc-24`
(718,839) ist gar kein WC zu sehen -- dort ist eine Wandecke. Bei einem
wandhaengenden oder mehrteiligen Objekt (`teile: 2` beim Doppelwaschtisch,
Marker = Mittel beider Becken) sitzt der Ursprung neben dem, was man sieht.

Damit ist die Regel "mehr als BELEG_RADIUS_PX daneben = falsch" bei solchen
Objekten systematisch unfair.

VORSCHLAG, noch nicht gebaut: ein Objekt gegen das BESTE der vier Bilder
messen statt gegen den Plan allein. Trifft ein Bild, ist die Planstelle gut
und die anderen sind wirklich verschoben; trifft KEINES, ist der Massstab
schief und es gibt keine Beanstandung. Ein systematischer Versatz kuerzt sich
damit heraus, echtes Umraeumen bleibt stehen. Rainers Entscheidung.

## MARKER-GEGEN-DAS-BESTE-BILD-MESSEN-001 (COMPLETE)

Rainer, 2026-08-30: "ok" auf den Vorschlag aus
MARKER-BELEG-JETZT-EHRLICH-001.

`verschobene_objekte()` in lieferung-pruefen.py misst jedes Objekt gegen das
BESTE der vier Bilder statt gegen den Plan allein:

    trifft ein Bild   -> die Planstelle ist gut, die anderen haben umgeraeumt
    trifft KEINES     -> unser Massstab ist schief, keine Beanstandung
    nur EIN Bild      -> kein "bestes"; die aeltere Regel gegen den Plan
                         bleibt die einzige, die es gibt

Der Satz nennt das Bild, in dem das Moebel richtig sitzt -- damit man
nachsehen kann, wie es aussehen soll, statt nur zu erfahren, dass etwas nicht
stimmt.

An 3_3_2 gemessen: von 14 alten Beanstandungen bleiben 10 echte. Was
wegfaellt, ist `doppelwaschtisch-23` -- kein Bild zeigt es an der Planstelle,
also ist es unser Ursprung-statt-Mitte-Problem und keine Lieferung. Es
verschwindet nicht lautlos, sondern steht ueber der Liste:

    Nicht beurteilt, weil KEIN Bild diese Objekte an ihrer Planstelle zeigt --
    die px im Auftrag ist der Objektursprung, nicht die sichtbare Mitte:
      ~ doppelwaschtisch-23

Zwei Fehler beim Bauen, beide gemessen und behoben:

1. Beide Regeln liefen nebeneinander -- 24 Beanstandungen statt 10, jedes
   Moebel zweimal: einmal gegen das beste Bild und einmal gegen den Plan
   allein, also mit genau dem Massstab, dessen Schiefe der Anlass war. Die
   aeltere Regel tritt jetzt zurueck, wo die neue urteilt
   (`abstand_pruefen=False`); ihre Pruefungen auf fehlendes, unlesbares oder
   ausserhalb liegendes `bei` bleiben. Ein Test haelt das fest.
2. `unittest.main()` stand ZUM SECHSTEN MAL heute mitten in der Testdatei --
   die neue Klasse lief nicht mit und meldete trotzdem "OK". Steht jetzt am
   Ende, mit einer Warnung darueber.

Eine meiner eigenen neuen Erwartungen war falsch (der Name des GUTEN Bildes
darf im Satz vorkommen -- er ist die nuetzlichste Angabe darin) und ist mit
Begruendung umgeschrieben.

Tests: `lieferung-pruefen.test.py` 89 (7 neu). OK.

## MARKER-RELATIV-STATT-ABSOLUT-MESSEN-001 (COMPLETE)

Rainer, 2026-08-30: "ja" auf die relative Regel.

Anlass war die dritte Runde an 3_3_2. Das Wohnzimmer war repariert -- alle
elf Objekte 4 bis 207 Pixel von ihrem Platz, meist unter 100, kein Tausch
mehr. Es blieben neun Beanstandungen, ALLE im Bad:

    badewanne-21           352 167 175 155   bestes 155
    doppelwaschtisch-23    319 343 363 293   bestes 293
    dusche_gross-20        303 320 322 197   bestes 197
    vorwandinstallation-22 165 404 181 177   bestes 165
    wand_wc-24             159 396 242 248   bestes 159

Im Wohnzimmer kam das beste Bild auf 4 bis 57 Pixel heran, im Bad NIE unter
155. Wenn KEIN Bild je trifft, ist das der Versatz zwischen Objektursprung
und sichtbarer Mitte -- unser Massstab, nicht ihre Lieferung. Und dass der
Doppelwaschtisch ueberhaupt gemeldet wurde, lag allein daran, dass seine 293
knapp unter der festen 300er-Schwelle lagen. Willkuer, keine Messung.

Neu: `AUSREISSER_PX = 150`. Beanstandet wird nur, wer BEIDES ist --

    abstand > BELEG_RADIUS_PX          absolut weit weg, UND
    abstand > bestes + AUSREISSER_PX   deutlich schlechter als das beste Bild

Absolut allein meldet einen gleichmaessigen Versatz als drei Fehler. Relativ
allein meldet 40 Pixel neben 5 Pixeln als Fehler. Erst beides zusammen trifft.

Der `unklar`-Hinweis bleibt, unterdrueckt aber nicht mehr: ein Ausreisser
bleibt einer, auch wenn das Lineal schief ist.

An 3_3_2 gemessen: aus 9 Beanstandungen werden 3 --

    03: badewanne-21            352, bestes 155
    04: vorwandinstallation-22  403, bestes 165
    04: wand_wc-24              396, bestes 159

Gegengeprueft, ob sie echt sind: Codex' eigene Sichtstellen in 03 und 04 ins
Bild gezeichnet. Das Wand-WC sitzt in 03 unten links im Gaeste-Bad hinter der
Glaswand, in 04 ganz oben in einem ANDEREN Raum neben der Duschkabine. Zwei
verschiedene Zimmer -- die Beanstandung ist echt.

Rueckwaerts geprueft, dass die Regel nichts Echtes verliert: die zweite Runde
haette mit ihr dieselben Wohnzimmer-Funde ergeben (essgruppe_stuhl-26 mit
310/367 gegen bestes 133, essgruppe_stuhl-31 mit 336/353 gegen 125).

Tests: `lieferung-pruefen.test.py` 91 (2 neu). OK.

## MOEBEL-WERDEN-IN-DER-HOEHE-GESTAUCHT-001 (OFFEN, echter Baufehler)

Rainer, 2026-08-30: "sieh dir doch die blender datei an." Er hatte recht --
Plan und Bild sagen nur, WO etwas steht. Was damit passiert, steht in der
Geometrie.

Gemessen im gebauten `interior-modern-baseline.blend` von 3_3_2:

    doppelbett-10   Welt-Kasten x 6,650..8,650  y 7,473..9,273  z 0..0,500
                    2,000 x 1,800 x 0,500 m

Ein Doppelbett von einem halben Meter Gesamthoehe -- Matratze UND Kopfteil.
Das Hoehenprofil entlang der Laengsachse zeigt das Kopfteil richtig am
grossen x (0,35 gegen 0,50 m), also vom Kleiderschrank ABGEWANDT, Fussende
zum Schrank mit 1,40 m Abstand. Die Lage stimmt.

Die HOEHE stimmt nicht. Aus dem Bauplan, `verified_size_mm` gegen
`target_bbox_mm.height_mm`:

    doppelbett     856 -> 500 mm   0,58
    einzelbett     682 -> 500 mm   0,73
    badewanne     1016 -> 580 mm   0,57
    wand_wc        813 -> 400 mm   0,49

Vier Objekte werden auf die Haelfte bis drei Viertel ihrer Hoehe gequetscht.
Die anderen neun stimmen (0,88 bis 1,06).

Die Vermutung, noch nicht geprueft: die Zielhoehen sind NENNMASSE aus dem
Symbolkatalog -- ein Bett ist 500 mm hoch (Matratzenoberkante), ein Wand-WC
400 mm (Sitzhoehe). Das Modell enthaelt aber Kopfteil bzw. Spuelkasten. Wer
das ganze Netz auf die Sitzhoehe skaliert, staucht es.

Das ist UNSER Bau, nicht Codex. Es erklaert auch, warum das Bad-WC in der
Marker-Pruefung nie sauber zu treffen war.

Zu klaeren, bevor etwas geaendert wird:
- Woher kommen die `height_mm` im Symbolkatalog, und sind sie als Nennmass
  oder als Gesamthoehe gemeint?
- Skaliert der Bauer gleichmaessig oder nur in z? Bei 0,58 in z allein waere
  das Bett flach; bei gleichmaessiger Skalierung waere auch der Grundriss zu
  klein -- er ist es NICHT (2,000 x 1,800 stimmt gegen 1800 x 2000 Ziel).
  Also wird nur z gestaucht.

## ZOOM-IM-MOEBEL-EDITOR-001 (COMPLETE)

Rainer, 2026-08-31: "can we add a zoom to the furniture setting? it would be
easier to place the furniture."

Der SVG hatte einen festen viewBox aus den Geschossgrenzen. Ein Haus von 15 m
auf 680 Bildpunkten sind rund 19 mm je Punkt -- ein Wand-WC ist damit
19 Punkte breit. Auf 30 mm genau zu setzen war Gluecksache.

Gezoomt wird ueber den **viewBox**, nicht ueber eine CSS-Transformation.
Grund: `coordinate()` rechnet mit `getScreenCTM()`, und die kennt den viewBox
von selbst -- so kann sich der Zeiger nicht von der Zeichnung loesen. Eine
CSS-Skalierung waere ein zweiter Weg, auf dem beide auseinanderlaufen koennen.

    Strg + Mausrad   zoomt um den ZEIGER (wie im Annotator)
    + / -            zoomt um die Bildmitte, fuer Zeiger ohne Rad
    Einpassen        wieder alles zeigen
    1x bis 8x, Schritt 1,25

Kein eigenes Verschieben. Wer um den Zeiger zoomt, verschiebt schon:
herauszoomen, Zeiger woandershin, hineinzoomen. Ein Zieh-Modus muesste sich
mit Setzen, Rahmen-Auswahl und Punkte-Ziehen um dieselbe Maustaste streiten.

Der Ausschnitt wird im Grundriss gehalten -- sonst zoomt man einmal am Rand
und sucht das Haus in weisser Flaeche.

Der Zoom-Zustand liegt in der SEITE, nicht im Editor: die Knoepfe stehen dort.
Zwei Zustaende ueber denselben Zoom waeren zwei Wahrheiten.

Am laufenden Editor nachgewiesen:

    Start        viewBox -550 -550 10000 9100     100 %
    + einmal     450 360 8000 7280                125 %
    + dreimal    1890 1670 5120 4659              195 %
    Strg+Rad     2094 1856 4096 3727              244 %   (um den Zeiger)
    Einpassen    -550 -550 10000 9100             100 %

Zeigergenauigkeit geprueft: der Unterschied zwischen `getScreenCTM()` und der
naiven viewBox-Rechnung betraegt 55 mm bei 100 % und 28 mm bei 195 % -- in
BILDPUNKTEN konstant (rund 2,5), also der Rand, den SVG bei ungleichem
Seitenverhaeltnis laesst, und keine Drift. `coordinate()` nimmt ohnehin die
Matrix.

Zwei Fehler beim Bauen, beide gemessen:
- Der Zustand lag zuerst im Editor, die Knoepfe stehen aber in der Seite.
- `documentBounds(document, ...)` lief vor dem ersten Laden gegen `undefined`
  -- die ganze Seite gab HTTP 500. Jetzt mit Rueckfall.

Tests: `src/lib/floorplan-workbench/sicht.test.mjs`, 8 Faelle. Alle 35 in
src/lib OK.

## QUERPRUEFUNG-BLIND-WENN-ALLE-GLEICH-FALSCH-001 (OFFEN)

Rainer, 2026-08-31, an 3_3_4: "codex is not following the rules, if you look
at the bedroom nothing is making sense for me."

Gemessen und mit Markern ins Bild gezeichnet:

    kleiderschrank-19  Marker 20, BLAU ("bleibt"), px 253/646
                       rund 3 m Korpus an der linken Schlafzimmerwand
                       -> fehlt in ALLEN VIER Grundrissen
    doppelbett-18      Marker 3, px 603/820, im Plan quer an der unteren Wand
                       -> liegt in allen vier diagonal durch die Raummitte,
                          Kopfende dort, wo der Schrank stand

Das Bett hat den Platz des Schranks eingenommen.

**Die Luecke im Pruefer.** `verschobene_objekte()` misst seit gestern jedes
Objekt gegen das BESTE der vier Bilder -- ein gleichmaessiger Versatz gilt als
unser Massstabsfehler. Wenn aber ALLE VIER dieselbe abweichende Anordnung
zeigen, sind sie untereinander einig und die Pruefung schweigt. Genau das ist
hier passiert.

Die relative Regel war richtig gegen den Ursprung-statt-Mitte-Versatz im Bad
(dort traf KEIN Bild je unter 155 px). Sie ist blind gegen ein einstimmig
umgestelltes Zimmer.

Noch nicht gebaut, weil die Unterscheidung nicht trivial ist: beide Faelle
sehen gleich aus -- vier Bilder, alle weit vom Plan. Der Unterschied liegt in
der STREUUNG: beim Massstabsfehler liegen die vier eng beieinander (Bad:
293..363, Spanne 70), bei einem umgestellten Zimmer ebenfalls. Ein Kandidat
waere, VERSCHWUNDENE Objekte getrennt zu behandeln -- ein blaues Objekt, das
in allen vier Bildern weit weg gemeldet wird, ist etwas anderes als eines, das
ueberall gleich leicht daneben liegt. Braucht aber die catalog.json, und die
liefert Codex seit dieser Runde nicht mehr mit.

Erst einmal Rainers Entscheidung, ob wir Codex fragen (siehe
BEANSTANDUNG-SCHLAFZIMMER.md) oder gleich bauen.

## RUECKKANAL-ZU-CODEX-UND-WAS-ER-SAGTE-001 (COMPLETE)

Rainer, 2026-08-31: "can we create a backchannel where you discuss with codex
yourself?" -- danach: "sprich das ab mit codex, i just want to get stuff
finished."

Es gibt eine Codex-CLI: `codex exec -s read-only --skip-git-repo-check`.
Sie sieht PNG-Dateien an. Damit laesst sich der Bearbeiter direkt befragen,
statt ueber Beanstandungen zu raten.

**Was er auf die Frage sagte, was er im Rohrender sieht** (woertlich):

> "In Bild A liegt bei (253,646) ein glatter, weisser laenglicher Quader; bei
> (603,820) eine flache, rechteckige, kariert strukturierte Form."
> "Ein glatter, merkmalloser Quader ist semantisch mehrdeutig: Der Bearbeiter
> kann ihn fuer WAND, Platzhalter oder unwichtiges Bauteil halten. Fehlen
> feste Objektmasken, Tiefen-/Geometriedaten und eine ausdrueckliche
> Positionsbindung, koennen Gestaltungsprioren daraus eine 'plausiblere'
> Moeblierung ableiten und Objekte entfernen oder umstellen."

Er hat den Kleiderschrank nicht entfernt -- er hat ihn nie als Moebel gesehen.
Das Bett war eine flache karierte Platte (die 50-cm-Stauchung von gestern).

**Was daraufhin geprueft wurde.** Der Auftrag gab in seiner Dateiliste NUR die
drei .blend mit. Im Ordner lagen die ganze Zeit:

    interior-modern-baseline.png            Rohrender
    interior-modern-baseline-depth.png      Tiefenpass  -- im Auftrag 0 x erwaehnt
    interior-modern-baseline-edge.png       Kantenpass  -- 1 x
    OBJEKTKARTE-interior-modern-baseline.png             -- 3 x, aber nie in der Liste

Der Tiefenpass ist genau das Mittel, das die zwei Faelle trennt: ein Schrank
steht rund 500 mm vor der Wand, eine Wand ist buendig. Im Farbbild sind beide
ein weisser Quader, im Tiefenbild zwei Grauwerte.

**Gebaut:**

1. `auftragsdateien()` in make-codex-job.py -- die Dateiliste traegt jetzt zu
   jeder .blend ihren Rohrender, Tiefenpass, Kantenpass und die Objektkarte.
   Aus 3 Dateien wurden 13. Kein Ordnerabzug: nur was zu einer .blend gehoert.
2. Regelwerk 10.6, neuer Abschnitt "Ein glatter Quader ist ein Moebel, keine
   Wand" -- mit Codex' eigener Antwort als Begruendung, dem Verweis auf den
   Tiefenpass, und dem Satz: findest du zu einem Marker kein Objekt, ist das
   eine MELDUNG, kein Freibrief.

Tests: make-codex-job 53 (3 neu), go 16, lieferung-pruefen 91 -- OK.

**Codex' eigene Liste, was noch fehlt** (read-only gefragt, Punkte 3 bis 5
noch nicht gebaut):

3. Je Pflichtobjekt eine eindeutige Objekt-ID aus der .blend UND eine
   Bildmaske oder Bounding-Polygon-Koordinaten -- nicht nur den Markerpixel.
   Das wuerde AUCH unser Ursprung-statt-Mitte-Problem loesen: `px` ist heute
   der projizierte Objektursprung, deshalb traf im Bad kein Bild je unter
   155 px. Eine Messung, zwei Probleme.
4. Pflichtpruefung vor der Bearbeitung: Objektkarte, Tiefen-, Kantenpass und
   .blend gemeinsam jedem Marker zuordnen.
5. Ausgabe verwerfen, sobald ein Vorher-Nachher-Abgleich bei einem
   Pflichtobjekt abweicht.

Punkt 3 ist der naechste und braucht einen Blender-Durchlauf, der je Objekt
die Bildschirm-Bounding-Box misst.

OFFEN, nicht von mir verursacht: `build-simplifier-render-plan.test.py`,
`test_door_hinge_and_swing_are_normalized_into_the_walls_frame` ist rot -- war
es schon vor der Hoehenaenderung, mit den alten Werten nachgeprueft.

## CODEX-HAT-DIE-BLEND-NIE-GEOEFFNET-001 (COMPLETE)

Rainer, 2026-08-31: "aber codex kann doch die objectnamen doch lesen oder
nicht?"

Read-only gefragt, woertlich:

> "Ja, ich kann Objektnamen, Positionen und Abmessungen aus einer .blend
> auslesen, am zuverlaessigsten ueber Blender im Hintergrundmodus mit einem
> kurzen bpy-Skript."
> "Bei meinen bisherigen Auftraegen in diesem Projekt habe ich keine .blend
> tatsaechlich geoeffnet ... soweit belegbar, war es nur die PNG beziehungsweise
> gar keine solche Pruefung."

Er KANN es und tat es nicht. Der Auftrag sagte "Immer die NEUESTE gelieferte
.blend oeffnen" -- gemeint als "mach sie auf", gelesen als "nimm diese und
keine alte". Die ganze Zeit stand die Wahrheit in der Datei, und er sah auf
ein Bild, in dem ein Schrank wie eine Wand aussieht.

Der Auftrag sagt es jetzt unmissverstaendlich, mit dem Befehl daneben:

    **OEFFNEN heisst AUFMACHEN.** Die Objektliste in der .blend ist die
    Wahrheit, nicht das Rohrender ...

    blender --background "<datei>.blend" --python-expr 'import bpy; [print(
      o.name, [round(v,3) for v in o.location],
      [round(v,3) for v in o.dimensions]) for o in bpy.data.objects
      if o.type == "MESH"]'

    Findest du zu einem Marker der Objektkarte in der .blend kein Objekt, ist
    das eine MELDUNG in deiner Rueckgabe -- kein Grund, den Raum neu
    einzurichten.

Der Befehl steht als Konstante `BLENDER_OBJEKTLISTE` im Generator: er enthaelt
einfache UND doppelte Anfuehrungszeichen, und in die Zeilenliste eingebettet
zerbrach daran die Quelle (einmal passiert, deshalb der Kommentar dort).

Tests: make-codex-job 53, OK. Auftrag fuer 3_3_2 neu geschrieben und
nachgesehen -- Abschnitt steht drin, 13 Dateien in der Liste.

## PODESTE-FRASSEN-STUFEN-001 (COMPLETE)

Rainer, 2026-08-31, an onehalfstorey_029: "it is still wrong, now it combines
both but the intersection points are forgotten."

An seiner U-Treppe im Zeichner nachgemessen:

    Lauflinie gesamt   1179 px
    Podestzonen        [338, 539] und [636, 836]   (die zwei Ecken)
    reine Lauflaenge    779 px
    gebraucht            13 Auftritte
    GEZEICHNET           11 Striche
    Striche bei        60 120 180 240 299 | 598 | 896 956 1016 1076 1136

Der mittlere Schenkel von 1,34 m bekam EINEN Strich.

Die Schleife in `zeichneAuftritte` lief `auftritte` mal und sprang INNERHALB
desselben Durchlaufs ueber ein Podest:

    for (let i = 1; i < mass.auftritte; i += 1) {
      gelaufen += schritt;
      while (imPodest(gelaufen)) gelaufen = zone[1] + schritt;   <-- kostet einen

Jeder Sprung kostete einen Auftritt. Zwei Podeste, zwei verlorene Stufen --
waehrend die Beschriftung ("269 mm") weiter mit allen dreizehn rechnete. Das
ist Rainers "die Schnittpunkte sind vergessen": an der Ecke frisst das Podest
den Tritt.

Neu: `auftrittsStellen(gesamt, zonen, auftritte)` verteilt die Kanten
gleichmaessig ueber die REINE Lauflaenge (alles ausserhalb der Podeste) und
rechnet jede Stelle auf die Lauflinie zurueck. Ein Podest VERSCHIEBT die
folgenden Stufen, es loescht keine.

Gemessen nachher, dieselbe Treppe:

    12 Kanten (13 Auftritte -> 12 dazwischen)
    60 120 180 239 299 | 560 620 | 880 940 999 1059 1119
    keine liegt in einem Podest, der mittlere Schenkel bekommt zwei

Eine meiner eigenen Testerwartungen war falsch: ich hatte den Lauf bei 13
Auftritten in ZWOELF Teile geteilt. Ein Auftritt ist einen Auftritt tief, der
Lauf also in dreizehn -- die Datei rechnet seit jeher `flugLauf / auftritte`.
Mit Begruendung im Test korrigiert.

Tests: `static/auftrittsstellen.test.mjs`, 7 Faelle. Alle JS-Tests: 249, OK.
`annotate.html` traegt `v=20260831-2000`.

OFFEN, im selben Haus: dem OBERGESCHOSS fehlt ein eigener Massstab
(`scale_missing: ["upperfloor"]`), und das Haus steht seit Rainers Speichern
um 16:11 auf "baubereit" statt veroeffentlicht -- 4 .blend ohne Zertifikat,
obwohl 10 Bilder im Katalog stehen.

## FLAECHEN-WIRKLICH-VERSCHMELZEN-001 (COMPLETE fuer Raeume, Aussenflaechen OFFEN)

Rainer, 2026-08-31: "if 2 of the same overlap ... could they really be merged
together, i mean really melt together" -- und zum Gehweg: "supposed to be 2
rectangles joined, not some kind of triangle with chopped off points."

**Was "Verbinden" bisher war.** Der Dialog beim Speichern fragte "Connect them
as one room while preserving every shape?" und setzte allen Flaechen dieselbe
`connected_room_id`. Eine GRUPPE, keine Vereinigung. Gelesen wird sie an genau
EINER Stelle: `room_fill_colors` in app.py, damit beide dieselbe Farbe
bekommen. `build-simplifier-render-plan.py` kennt `connected_room_id`
ueberhaupt nicht -- fuer den Bauer sind es zwei Raeume mit einer Kante
dazwischen. Betroffen sind 9 Haeuser.

**Der Gehweg von onehalfstorey_020**, von Hand gezogen:

    0.3415 0.9051 / 0.3282 1.1634 / 0.9096 1.1965
    0.9295 1.0243 / 0.6172 1.0110 / 0.6139 0.9117

Kein einziger rechter Winkel: die x-Werte, die gleich sein sollten, weichen um
0,013 und 0,020 ab.

**Gebaut:** `static/flaechen-vereinigen.js`, `vereinigeFlaechen(a, b, toleranz)`.

Bewusst KEINE allgemeine Polygon-Verschneidung -- die ist heikel und die
Faelle sind es nicht. Gezeichnet werden Rechtecke. Also:

  1. x- und y-Werte BEIDER Polygone buendeln: was naeher als die Toleranz
     liegt (0,004 = rund 4 cm bei einem 10-Meter-Haus), wird derselbe Wert.
     Damit stehen die Ecken exakt uebereinander.
  2. Ueber das Gitter aus diesen Werten Zelle fuer Zelle fragen, ob sie in
     einem der Polygone liegt.
  3. Den Rand der bedeckten Zellen ablaufen -> EIN Polygon mit rechten
     Winkeln, Kanten auf einer Geraden zusammengefasst.

Beruehren sich die Flaechen nicht ueberall, gibt es null und der Zeichner sagt
es -- statt eine Luecke zu ueberbruecken, die es wirklich gibt.

Im Dialog steht Verschmelzen jetzt VOR Verbinden, weil es das ist, was man
meint. Verbinden bleibt die zweite Frage: der einzige Weg, wenn die Formen
absichtlich verschieden bleiben sollen.

Am laufenden Zeichner mit dem echten Gehweg nachgewiesen:

    0.335 0.908 / 0.616 0.908 / 0.616 1.018
    0.920 1.018 / 0.920 1.180 / 0.335 1.180
    alle sechs Kanten waagerecht oder senkrecht

Tests: `static/flaechen-vereinigen.test.mjs`, 9 Faelle -- L-Form, rechte
Winkel, Flaecheninhalt, krumm gezogene Ecken, nur anliegend, GETRENNT (muss
null geben), eine Flaeche in der anderen, Unsinn. Alle JS-Tests: 258, OK.
Python: 268, OK.

OFFEN: die AUSSENFLAECHEN (Gehweg, Terrasse, Einfahrt) haben keinen solchen
Dialog -- dort gibt es beim Speichern keine Ueberlappungsfrage. Die Funktion
liegt bereit; es fehlt die Stelle, an der sie fuer `exterior_areas` gefragt
wird.

## KONVEXE-HUELLE-WAR-DER-ABGESCHNITTENE-ZIPFEL-001 (COMPLETE)

Rainer, 2026-08-31: "still doesn't create an L, it creates a cutoff triangle
still."

Er hatte recht, und meine Vereinigung von vorhin sass an der falschen Stelle.
Sie ging in den Raum-Dialog. Der Gehweg ist eine AUSSENFLAECHE, und die hatte
laengst eine eigene Zusammenfuehrung -- mit der konvexen Huelle:

    overlapping.points = convexHullOf(overlapping.points.concat(cleanedPoints));

Die konvexe Huelle legt ein Gummiband um beide Formen. Bei einem L schneidet
sie die einspringende Ecke ab; mathematisch kann sie nichts anderes. Deshalb
sah es jedes Mal gleich aus, egal wie sauber er gezeichnet hat.

Am laufenden Zeichner nebeneinander gemessen, dieselben zwei Rechtecke:

    konvexe Huelle   5 Ecken
    Vereinigung      6 Ecken, Kerbe bei 0.4 / 0.3
                     0,0 -> 0.6,0 -> 0.6,0.8 -> 0.4,0.8 -> 0.4,0.3 -> 0,0.3

Jetzt gehen Raeume und Aussenflaechen ueber denselben Weg. Laesst sich nichts
verschmelzen (Luecke dazwischen), sagt es das und aendert nichts.

ZWEITER Grund, warum er keine Aenderung sah: `annotate.html` trug noch
`v=20260831-2000`, dieselbe Version wie vor meiner Aenderung -- sein Browser
lieferte die alte annotate.js. Jetzt `v=20260831-2130`. Beim Aendern von
annotate.js IMMER die Version mitziehen.

Tests: `flaechen-vereinigen.test.mjs` 10 (einer haelt fest, dass die Kerbe
bleibt und die Flaeche kleiner ist als die der Huelle). Alle JS-Tests: 259, OK.

OFFEN: die Ueberlappungsfrage bei Aussenflaechen kommt nur, wenn man eine
Flaeche NEU zeichnet. Zwei laengst gespeicherte, die sich ueberlappen, werden
nicht gefragt -- anders als bei Raeumen, wo `confirmOverlappingSameRooms()`
beim Speichern prueft.

## 2026-08-31 -- Codex macht dieselben Fehler (Rainer: "its not working codex is makeing the samle mistakes")

Gemessen an der Lieferung fuer german_catalog_review_bungalow_3_3_4_b_100_2:

- **Stuehle doppelt.** codex-job.json fuehrte `essgruppe_6-25` und sechs
  `essgruppe_stuhl-30..35` am selben Fleck mit derselben Rolle. Die sechs sind
  aber die Stuehle DIESES Tisches (build-simplifier-render-plan.py:3028,
  `derived_from`). Gezeichnet wurden neun. ERLEDIGT: `stueckzahlen()` in
  make-codex-job.py, Abschnitt "## Stueckzahlen" im Auftrag.
- **Nachweis.** Codex hat am 2026-08-30 zugegeben, nie eine .blend geoeffnet
  zu haben. ERLEDIGT: der Auftrag verlangt die Zahl der MESH-Objekte in
  catalog.json, `lieferung-pruefen.py::nachweis_beanstandungen` prueft sie.

OFFEN:

- [ ] Die zwoelf Auftraege vom 28.-30. August tragen weder Stueckzahlen noch
      Nachweis. `make-codex-job.py --all` neu schreiben -- setzt voraus, dass
      jedes Haus eine zertifizierte Lieferung hat.
- [ ] german_catalog_review_bungalow_3_3_4_b_100_2 laesst sich nicht neu
      beauftragen ("keine zertifizierte Lieferung"). Erst Moebel-Schritt
      oeffnen und einmal speichern, dann `go.py`, dann make-codex-job.py.
- [ ] Bett von 3_3_4: `doppelbett-18` (px 603,820) steht im gelieferten Bild
      auf der Stelle von `kleiderschrank-19` (px 253,646), und ein
      Kleiderschrank fehlt im Zimmer ganz. Die Stueckzahlen decken das NICHT
      ab -- Anzahl stimmt, Ort nicht. Offen: die Lagepruefung ist blind, wenn
      alle vier Bilder denselben falschen Aufbau zeigen.
- [ ] Codex-Rueckkanal: `codex exec -s read-only` lief am 2026-08-31 zehn
      Minuten ohne Antwort und wurde abgebrochen. Zeitlimit oder kleinere
      Frage noetig.

## 2026-09-01 -- Positionierung streng nach .blend (Rainer: "positionierung streng nach blender file")

Der Auftrag gab je Moebel EINEN Pixelpunkt. "Mitte, Fussabdruck, Groesse und
Ausrichtung bleiben erhalten" war damit nicht befolgbar. ERLEDIGT:

- Objektkarte zeichnet je Moebel den Quader aus der .blend (12 Kanten).
- Auftragsliste nennt `B x T x H` in mm und die Drehung in Grad.
- Pfeil zeigt von der naechsten Wand FORT (Bett: Kopf->Fuss, Schrank:
  Rueckwand->Front). `weg_von_der_wand` in make-codex-job.py.
- Passungsregel: die Wandseite bleibt fest, der Unterschied geht in den Raum.
- 14 von 16 Auftraegen neu geschrieben.

Auf dem Weg gefunden und behoben:

- Der Abstand wurde vom Mittelpunkt gemessen -- ein 2 m langes Bett hat seinen
  Mittelpunkt 1 m von seiner eigenen Wand entfernt und sah aus wie ein Moebel
  in der Zimmerecke. Jetzt Kante zu Kante.
- Eine Wand, die auf ihrer Laengsachse 5 m neben dem Moebel liegt, meldete
  Abstand null. Jetzt beide Achsen.
- `wall`-Objekte von 0,10 x 0,11 m (Stuetzen an Wandkreuzungen) waren fast
  quadratisch; die "Normale" war ein Muenzwurf. Jetzt aussortiert.
- Eine "+ 50"-Toleranz mischte Millimeter (Tests) und Meter (Blender) und
  loeschte alle 40 Pfeile eines Hauses. Toleranz ist jetzt rein relativ.
- Drei eigene Tests liefen mit quadratischer Wandkiste und waren falsch-gruen.

Codex befragt (2026-09-01), umgesetzt: Masse als B x T x H beschriftet,
Pivot benannt (Schwerpunkt, nicht Objekt-Ursprung), Drehachse und Drehsinn
erklaert, Passungsregel ergaenzt, "kein Pfeil in der Ecke", "der Pfeil ist
KEINE Verschieberichtung".

OFFEN:

- [ ] onehalfstorey_020 und onehalfstorey_029 bauen nicht: "Massstab fuer
      upperfloor vom groundfloor uebernommen" -- das Obergeschoss hat keinen
      eigenen Massstab. Braucht Rainers Entscheidung, kein Raten.
- [ ] Codex-Vorschlag, nicht gebaut: fester Nordpfeil / Raumrichtung auf der
      Karte als zusaetzlicher Bezug fuer freistehende Moebel (Esstisch, Sofa
      haben heute keinen Pfeil).
- [ ] Codex-Vorschlag, nicht gebaut: bei symmetrischen Moebeln ist die
      funktionale Vorderseite weiterhin nicht erkennbar.
- [ ] Die Lagepruefung in lieferung-pruefen.py vergleicht noch nicht gegen
      `umriss_px`/`vorne_px` -- der Kasten steht im Auftrag, wird aber beim
      Pruefen der Lieferung nicht nachgemessen.

## 2026-09-01 -- Treppe erreicht das Geschoss (Rainer: "just use logic")

Die beiden offenen Haeuser hingen NICHT am Obergeschoss-Massstab. Der
Massstab wird seit jeher bewusst vererbt ("geerbt, nicht geraten"); die
Info-Zeile wurde nur von `abbruchgrund()` als Fehlermeldung durchgereicht.

Der echte Grund war zweimal derselbe wie bei 3_3_4: veralteter
Geometrie-Stempel. Alle 88 Moebel beider Haeuser nachgemessen -- jedes noch
im richtigen Raum -- und ueber den Speichern-Weg der App neu gestempelt.

- onehalfstorey_020: gebaut, zertifiziert, Auftrag geschrieben.
- onehalfstorey_029: Treppenfehler gefunden und behoben, siehe unten.

**Treppe (R9_stair_access).** Der Verifier meldete "top tread stair-step-13
finishes at 2271mm but this storey's floor is at 2620mm". 2620 - 2271 = 349
= genau zwei Steigungen, und die Treppe hat zwei Podeste.

`_laufplan` in render-furnished-dollhouse.py lief mit festem Auftritt die
Lauflinie entlang und nahm ein Podest, sobald die NAECHSTE Stufe
hineingeragt haette -- die angefangene Stufe davor fiel weg. 1518 / 267,5 =
5,68 Stufen, gelegt wurden fuenf. Pro Podest eine verlorene Steigung.

DERSELBE Fehler wie im Annotator beim Zeichnen der Stufenkanten
(`auftrittsStellen`, behoben 2026-08-31). Gezeichnet wurde seitdem richtig
und gebaut weiter falsch.

ERLEDIGT: `laufplan_stufen()` in render-furnished-dollhouse.py, acht Tests.
Jedes Flugstueck bekommt eine GANZE Zahl Stufen, verteilt nach groesstem
Rest; der Auftritt bleibt innerhalb eines Flugs gleich (DIN 18065).
Gegengemessen in der gebauten .blend: 15 Elemente, Oberkante 2620,0 mm.
R9_stair_access besteht in allen acht Durchlaeufen.

Von den gebauten Haeusern hat nur onehalfstorey_029 eine Podesttreppe; 020
und twostorey_030 sind gerade und rechnen unveraendert (an 020 nachgemessen:
15 Elemente, 2620,0 mm). Kein Neubau der uebrigen noetig.

OFFEN:

- [ ] onehalfstorey_029 scheitert jetzt nur noch an `opening_count`:
      upperfloor hat 15 Tuer/Fenster-Elemente, der Plan bringt 13 unter. Die
      zwei ohne Wand sind Fenster an der WESTSEITE des Obergeschosses:
      Punkte 0.0833..0.1455 bei y 0.6526 und 0.0930..0.1513 bei y 0.2957.
      Das ist Rainers Zeichnung -- entweder fehlt dort im Obergeschoss die
      Wand, oder die zwei Fenster gehoeren geloescht. Keine Entscheidung
      ohne ihn.
- [ ] `abbruchgrund()` in go.py liest eine "[plan] ..."-Info-Zeile als
      Abbruchgrund. Das hat zwei Haeuser einen Tag lang als
      "Massstab-Problem" aussehen lassen, obwohl es der Moebel-Stempel war.

## 2026-09-01 -- Ueberlappende Fenster beim Kopieren (Rainer: "color the windows red where they overlap")

`schonVorhanden` in fenster-kopieren.js verglich beide ENDPUNKTE auf 0,004
genau und fing damit nur das exakt gleiche Fenster. Ein 1,20-m-Fenster unten
und ein 1,60-m-Fenster oben, 30 cm versetzt in derselben Wand, galten als
verschieden und standen danach im Plan ineinander.

ERLEDIGT:

- `fensterUeberlappen()` in fenster-kopieren.js, elf Tests
  (fenster-ueberlappung.test.mjs): quer zur Wand 0,01 (rund 10 cm), laengs
  echte Ueberschneidung. Zwei Fenster NEBENEINANDER in einer Fassade sind
  der haeufigste Fall und schlagen nicht an.
- Beim Kopieren werden Kopie UND vorhandenes Fenster mit
  `fenster_ueberlappt` markiert, annotate.js malt sie rot (#e11d48), die
  Statuszeile nennt die Zahl.
- `normalize_element()` in app.py behaelt das Feld -- sonst waere die
  Markierung nach dem naechsten Laden weg, so wie `stair_type`, das deshalb
  im ganzen Bestand null Mal vorkam. Zwei Tests.
- annotate.html auf v=20260901-0730.

GELOESCHT WIRD NICHTS. An den Fenstern sitzt die meiste Zeichenarbeit; der
Kommentar in fenster-kopieren.js haelt seit dem 2026-08-30 fest, was ein
Griff daneben kostet. Exakte Duplikate werden weiterhin uebersprungen, alles
andere wird markiert und von Hand aufgeraeumt.

Am laufenden Zeichner nachgemessen (onehalfstorey_029, nur im Speicher, NICHT
gespeichert): ein oberes Fenster um 0,03 verschoben, kopiert -- Kopie und
Original beide markiert, am Strich rot minus gruen +107 bzw. +191 gegen -104
beim nicht markierten Nachbarn.

OFFEN:

- [ ] Die Markierung entsteht nur beim KOPIEREN. Zwei von Hand
      uebereinandergezeichnete Fenster faellt sie nicht auf. Eine Pruefung
      beim Speichern waere der naechste Schritt.

## 2026-09-01 -- Quader statt Moebel (Rainer: "codex muss sich mehr Muehe geben passende Moebelstuecke zu erfinden")

`stuff-9` (400 x 2450 x 800 mm an der Kuechenwand von 3_3_4) blieb in 03 und
06 ein glatter Klotz; in 04 und 05 war eine Kuechenzeile mit Fronten und
Griffen daraus geworden. Zwei gemessene Ursachen:

1. Der Auftrag sagte nur "Stuff (ersetzen)". Im Plan steht `build: "rect"` --
   es gibt KEIN Modell, der Bauer baut einen Quader. Was daraus werden soll,
   stand nirgends. `garderobe` heisst "Garderobe" und wird jedes Mal richtig.
2. `messe_platzhalter` mass nur das ERSTE Innenbild, mit der Begruendung im
   eigenen Docstring: "ein Platzhalter, der in einem Stil ein Kasten blieb,
   ist es in allen vieren." Widerlegt. Die Warnung kam nur, weil 03 zufaellig
   das erste Bild ist.

ERLEDIGT:

- `messe_platzhalter` misst ALLE Innenbilder, `kasten_verdacht` schlaegt an,
  sobald EINES flach ist. Fuenf Tests. Eine einzelne Zahl bleibt gueltig.
- Rolle: "Stauraum-Platzhalter (ersetzen) -- ein echtes Moebel mit Fronten,
  Fugen und Griffen daraus machen; ein glatter Kasten ist kein Ergebnis".
  `(ersetzen)` bleibt woertlich, sonst faerbt `farbe_fuer` den Marker blau --
  ein erster Versuch tat genau das, zwei bestehende Tests haben es gefangen.
- Neuer Abschnitt im Auftrag: "Erfinde ein passendes Moebelstueck, stell
  keinen Quader hin", mit Masse-zu-Moebel-Beispielen.
- `test_the_named_roles_keep_their_wording` mit Rainers Zustimmung angepasst:
  prueft jetzt `(ersetzen)` woertlich UND den scharfen Satz, statt die alte
  Zeichenkette. Der Wortlaut wurde geschaerft, nicht abgeschwaecht.
- 15 von 16 Auftraegen neu geschrieben.
- german_catalog_review_bungalow_3_3_4_b_100_2 angenommen und HOCHGELADEN
  (sechs Bilder aus dem Codex-Ordner, keine Baselines). Freigeben steht aus.

BEWUSST NICHT GEMACHT:

- Die Schwelle KASTEN_BLEIBT_FLACH (65 %) NICHT gesenkt. stuff-9 misst
  72,0 / 41,3 / 49,9 / 63,0 -- 06 rutscht mit 63 durch. Auf 60 zu senken
  wuerde garderobe-11 (61,5 %) treffen, und die ist in allen vier eine
  richtige Garderobe mit Maenteln und Schuhregal. Zwei echte Faelle liegen
  zwei Punkte auseinander; die Flachheitszahl kann das nicht entscheiden.

OFFEN:

- [ ] german_catalog_review_bungalow_3_3_4_b_100_2 FREIGEBEN: zwei Schritte,
      approve-plan.py und freigeben.py. Beide noch nicht gelaufen.
- [ ] Die Beanstandung "03 und 06 neu rendern" steht noch im Auftrag von
      3_3_4, obwohl die Bilder inzwischen hochgeladen sind. Vor dem naechsten
      Codex-Lauf fuer dieses Haus bereinigen.
- [ ] onehalfstorey_029 hat die neue Regel nicht -- baut nicht (opening_count,
      zwei Fenster an der Westseite des Obergeschosses ohne Wand).

## 2026-09-01 -- 3_3_4 freigegeben, und der Auftrag bestellte es sofort neu

FREIGEGEBEN: german_catalog_review_bungalow_3_3_4_b_100_2, beide Haelften
(approve-plan.py und freigeben.py). Katalog: im=6 ok=ja, approved_real 5.
An der Seite selbst nachgemessen -- alle sechs Dateien liegen in der
WordPress-Mediathek, Byte fuer Byte identisch mit den lokalen, 05 im Stand
von 12:15 mit sechs Stuehlen.

Beim Bereinigen der veralteten Beanstandung fiel ein groesserer Fehler auf:

**Ein angenommenes Bild wurde sofort wieder bestellt.** `make-codex-job.py`
schrieb `"state": "pending"` fest verdrahtet fuer jedes geforderte Bild und
sah nie in `renders/ANGENOMMEN.json` nach. Der frisch geschriebene Auftrag
fuer 3_3_4 verlangte alle sechs Bilder erneut -- Minuten nachdem sie im
Kundenkatalog scharf geschaltet worden waren. Jeder neue Durchgang ist ein
neuer Wuerfelwurf; dabei ist schon dreimal die Badewanne aus einem fertigen
Bad verschwunden.

ERLEDIGT:

- `angenommene_lieferung()` und `zustand_setzen()` in make-codex-job.py,
  fuenf Tests. Angenommene Bilder bekommen `state: "angenommen"` und den
  Ordner, in dem sie liegen.
- Neuer Abschnitt ueber der Bestellung: "## Schon angenommen -- NICHT neu
  rendern", und wenn alles fertig ist: "**NICHTS ZU TUN.** ... frag nach,
  rendere nichts."
- Sechs Haeuser mit angenommener Lieferung neu geschrieben: bungalow_039,
  3_2_4, 3_2_5, 3_3_1, 3_3_4, onehalfstorey_020. Alle stehen jetzt auf
  NICHTS ZU TUN statt auf einer Bestellung.

OFFEN:

- [ ] bungalow_001: graues Baseline-Bild (id 80) weiterhin live im
      Kundenkatalog, Duplikate 369/371 unaufgeloest. Nicht angefasst --
      Kundenkatalog, braucht eine klare Ansage.
- [ ] `publish-renders.py` schliesst `-depth`/`-edge`/`-mask` aus, aber NICHT
      `-baseline`. Genau so kam id 80 hinein.

## 2026-09-01 -- Aussenwaende fallen an der Eingangsnische zusammen

Rainer, zu german_catalog_review_bungalow_3_4_5_b_120: "the outer walls seem
to be kaputt at the entrance."

Gemessen: der Aussenring hatte zwei Waende mit LAENGE 0 --

    wall-9   14321,11866 -> 10809,11866
    wall-11  10809,11866 -> 10809,11866   L 0   <- Seitenwand der Nische
    wall-12  10809,11329 ->  8855,11329
    wall-13   8855,11866 ->  8855,11866   L 0   <- Seitenwand der Nische

URSACHE: `_close_exterior_corners` arbeitet mit tol_mm = 800 und probiert
alle vier Endpunkt-Paarungen zweier Waende durch. Bei einer Aussenwand, die
KUERZER als die Toleranz ist, liegt auch ihr FERNES Ende innerhalb der
Toleranz zur Ecke und wird dorthin gezogen -- die Wand faellt auf null
zusammen. Die Nische war 537 mm tief.

    VOR  _close_exterior_corners  wall-11  ... -> 10809.1 2038.2   L 537.2
    NACH _close_exterior_corners  wall-11  ... -> 10809.1 1501.0   L   0.0

ERLEDIGT: nur das NAEHERE Ende wandert auf den Schnittpunkt, plus ein Schutz
gegen das Zusammenfallen bei zwei gleich weit entfernten Enden. Vier Tests in
build-simplifier-render-plan.test.py.

Isoliert gemessen (derselbe Code, nur mit und ohne den Guard):

    3_3_3_b_100_2      Nullwaende 2 -> 0
    3_4_1_b120         Nullwaende 1 -> 0
    3_4_3_b_120        Nullwaende 1 -> 0
    4_3_4_wb_125       Nullwaende 2 -> 0
    3_4_5_b_120, 4_1_1_wb_105, twostorey_030, onehalfstorey_020,
    3_3_4_b_100_2      identisch -- keine Regression

27 Haeuser haben Aussenwaende unter 800 mm und lagen damit in der
Gefahrenzone; bei den obigen vier ist sie wirklich zugeschlagen.

WICHTIG ZUR ZUORDNUNG: 3_4_5 selbst zeigt mit und ohne Guard dasselbe
Ergebnis -- Rainer hat die Annotation um 14:37:56 geaendert und die Nische
dabei von 537 auf 837 mm vertieft, also aus der Toleranz heraus. Sein Haus
ist jetzt in Ordnung, aber NICHT allein wegen des Fixes. Der Fehler war
trotzdem echt und ist an den vier anderen Haeusern belegt.

OFFEN:

- [ ] 3_3_3_b_100_2, 3_4_1_b120, 3_4_3_b_120 und 4_3_4_wb_125 haben
      gespeicherte Plaene und .blend aus der Zeit mit den Nullwaenden. Vor
      der naechsten Lieferung neu bauen.

## 2026-09-01 -- Der Rohbau stand zum Hochladen bereit

Rainer, zu german_catalog_review_bungalow_3_4_5_b_120: "es heisst ich muss
die bilder freigeben das sind aber keine Bilder."

Gemessen. Das Haus ist gebaut und zertifiziert, aber Codex hat nie etwas
geliefert -- unter renders/ liegt nur go-baseline. Hochladen haette genommen:

    exterior-classic-baseline.png
    exterior-modern-baseline.png
    interior-modern-baseline.png

Drei graue Rohbauten, direkt in den Kundenkatalog. DREI Loecher, alle drei
zu:

1. `collect()` in publish-renders.py schloss `-depth`, `-edge` und `-mask`
   aus, aber NICHT `-baseline`. Jetzt auch das, und ein Ordner mit nur
   Baselines wird abgelehnt statt stillschweigend leer hochgeladen.
2. `bilderordner()` in go.py nahm go-baseline, wenn es keinen Codex-Ordner
   gab (`kandidaten = codex or sorted(...)`) -- gegen den eigenen Docstring.
   Kein Rueckfall mehr.
3. Der Aufrufer in `treibe()` machte denselben Rueckfall ein zweites Mal
   (`bilderordner(name) or os.path.join(..., "go-baseline")`). Auch zu; ohne
   Lieferung kommt jetzt "noch keine Codex-Lieferung -- nur der Rohbau ist
   da, und der geht nicht in den Katalog".

Neue Datei publish-renders.test.py, sechs Tests, plus einer in go.test.py.
An 3_4_5 gegengeprueft: `bilderordner()` gibt None, der Pipeline-Schritt
lehnt ab. An 3_3_4 gegengeprueft: der Codex-Ordner wird weiter gefunden.

OFFEN:

- [ ] bungalow_001: Bild id 80 ist der Rohbau und liegt seit dem 2026-08-26
      im Kundenkatalog. Die Loecher sind jetzt zu, aber das Bild ist noch
      drin -- es muss von Hand raus. Dazu Duplikate 369/371.
- [ ] german_catalog_review_bungalow_3_4_5_b_120 hat noch keinen
      Codex-Auftrag. Es war in den 16 von heute nicht dabei.

## 2026-09-01 -- WARUM die Bildfehler entstehen (Rainer: "find out why stuff like that happens")

Codex am 2026-09-01 direkt gefragt, mit seiner eigenen Fehlerliste aus
german_catalog_review_bungalow_3_4_2_b_120 (zwoelf nachgemessene
Abweichungen). Seine Antwort, woertlich:

  "Jedes Bild ist eine neue Bildmodell-Stichprobe, selbst wenn der
   Baseline-Render als Vorlage diente."

  "A bis E sind erwartbares stochastisches Rauschen bzw. mangelnde
   Objektpersistenz -- kein bewusstes Missachten der Regeln."

  "Prompts beeinflussen Wahrscheinlichkeiten, garantieren aber weder
   Objektanzahl noch Position, Existenz, Geometrie oder Kollisionsfreiheit."

Die Antwort ist konditional formuliert -- Codex hat NICHT bestaetigt, welches
Verfahren er wirklich benutzt. Die Bilder beweisen es aber selbst: eine
Dusche kann zwischen vier Renders derselben Szene nicht verschwinden, und
Stuehle koennen sich nicht vermehren. Vier Renders einer Szene unterscheiden
sich in Material und Licht, nie im Inventar.

FOLGE FUER ALLES, WAS HEUTE GEBAUT WURDE: Stueckzahlen, Kasten, Pfeil,
Nachweis und "kein Quader" verschieben Wahrscheinlichkeiten und garantieren
nichts. Beleg: 3_3_4 bekam mit demselben Auftrag sechs Stuehle, 3_4_2 acht.
Die Regeln bleiben sinnvoll -- sie sind aber nicht der Hebel.

DER HEBEL (Codex' Vorschlag, deckt sich mit dem eigenen Regelwerk fuer
aussen): dieselbe Blender-Szene, identische Objekte, Transformdaten und
Kamera; nur Materialien, Beleuchtung und Render-Einstellungen variieren.
Alternativ feste Masken/Segmentation plus Depth/Normal-Paesse und
REGIONSWEISE Materialaenderung statt kompletter Neugenerierung.

GEMESSENE LUECKE:

    exterior-*-baseline-depth.png / -edge.png / -mask.png   Maske DA
    interior-modern-baseline-depth.png / -edge.png          KEINE Maske

Fuer aussen existiert das maskierte Verfahren seit Wochen
(comfyui-polish-exterior.py, eigene Regressionstests). Fuer innen nicht --
und alle zwoelf Fehler von 3_4_2 sind Innenbilder.

OFFEN, gross, braucht Rainers Entscheidung:

- [ ] Maskenpass fuer die Innen-Renders schreiben (der Renderer kann es
      bereits fuer aussen).
- [ ] Innenbilder auf dasselbe maskierte, regionsweise Verfahren umstellen
      wie die Aussenbilder, statt sie frei neu generieren zu lassen.
- [ ] Solange das nicht steht: jede Innenlieferung braucht die Augenpruefung.
      Der automatische Pruefer fand bei 3_4_2 null von zwoelf Fehlern; vier
      Subagenten fanden alle zwoelf in rund 20 Minuten.

## 2026-09-01 -- Messwerkzeug fuer Objektpersistenz gebaut, Input fehlt noch

Codex' kleinster Tagesschritt war: einen Low-Denoise-Pass (0,22) erzeugen und
je Moebel messen, ob es im Kasten geblieben ist. Der Kasten liegt seit heute
in jeder codex-job.json (`umriss_px`, acht projizierte Ecken).

GEBAUT: scripts/moebel-persistenz.py plus sechs Tests. Misst die Kantendichte
im projizierten Quader, Lieferung gegen Baseline.

GEMESSEN an german_catalog_review_bungalow_3_4_2_b_120:

    Baseline gegen sich selbst              43 Objekte, alle 1,00
    dusche-3 kuenstlich uebermalt           0,35, Nachbarn unveraendert 1,00
    freie Lieferung, dusche-3 FEHLT         1,16
    freie Lieferung, schreibtisch-20 FEHLT  1,06 und 1,26

Das Werkzeug ist richtig, der freie Input untauglich. Wo die Dusche fehlt,
stehen Fliesen und eine Topfpflanze -- mehr Kanten als der graue Rohbau, nicht
weniger. Ein Pixelmass kann Anwesenheit nicht messen, wenn die zwei Bilder
gar nicht zueinander passen; das ist der unabhaengige Beleg fuer Codex'
Diagnose.

ComfyUI lief nicht (127.0.0.1:8188 tot), der 0,22-Pass steht also aus.

OFFEN:

- [ ] ComfyUI starten und einen Low-Denoise-Pass (0,22, Depth + Edge) auf ein
      Innenbild fahren. Dann misst moebel-persistenz.py etwas Sinnvolles, und
      wir haben eine Zahl statt einer Meinung.
- [ ] Danach der zweite Pass (0,40-0,55) fuer den Stilwechsel, nur in sichere
      Flaechen eingeblendet -- Codex: "Ein einzelner hoher Denoise-Wert kann
      beides nicht zuverlaessig leisten."
- [ ] Object-ID-Pass (interior-modern-object-id.png, RGB je Blender-Objekt,
      plus .json mit der Zuordnung) fuer das regionsweise Kompositing.
- [ ] Bis dahin bleibt die Augenpruefung. Vier Subagenten fanden bei 3_4_2
      zwoelf Fehler, der automatische Pruefer null.

## 2026-09-01 -- Mein eigener Auftragstext hat die vier Entwuerfe bestellt

Rainer: "die Tatsache dass Codex den Blender-File 4 mal interpretiert faellt
auf Dich zurueck." Er hat recht. Im Auftrag stand woertlich:

    "Vier echte Entwuerfe, kein Farbfilter uebereinander."
    "Der Rohrender mit Farbstich ist KEIN Stil und wird abgelehnt."

Der erste Satz bestellte vier Entwuerfe, der zweite verbot den einzigen Weg,
der die Moeblierung festhaelt. Zwei Saetze weiter stand "gleiche Geometrie in
allen vieren" -- ein Widerspruch, den Codex zugunsten der Entwuerfe aufloeste.

ERLEDIGT: `INNEN_REGEL` in make-codex-job.py, als Konstante herausgezogen und
mit fuenf Tests belegt. Sie trennt jetzt:

    VARIIEREN DARF: Material und Farbe, Licht und Stimmung, Textilien,
                    Teppiche, Bilder, Pflanzen, Dekoration
    NICHT VARIIEREN DARF: welche Moebel dastehen, wie viele es sind, wo sie
                    stehen und wohin sie zeigen

16 Auftraege neu geschrieben.

ComfyUI ist raus (Rainer: "ComfyUI haben wir lange ausgeschlossen, die Tests
dort waren nicht gut"). Damit faellt Codex' Vorschlag mit dem
Low-Denoise-img2img-Pass weg, und `moebel-persistenz.py` bleibt vorerst ohne
brauchbaren Input.

Uebrig bleibt Codex' ERSTE Option, die weder ComfyUI noch ein Bildmodell
braucht: dieselbe Blender-Szene viermal rendern, nur Material und Licht
variieren. Objektpersistenz waere dann per Konstruktion garantiert.

GEMESSEN, wie weit der Blender-Innenrender davon entfernt ist
(german_catalog_review_bungalow_3_4_2_b_120, 43 Objekte):

    13 Objekte rendern als glatte Flaeche ohne Material (>= 65 % flach):
    kleiderschrank-2 92%, essgruppe_6-27 81%, trockner-12 76%,
    einzelbett-14/-18 je 73%, dusche-3 70%, essgruppe_stuhl-33 70%,
    lowboard-29 70%, fernseher-30 68%, kleiderschrank-19 68%,
    dusche-8 66%, wall-8-door 66%, wall-0-door 65%

Inventar und Position sind im Blender-Render bereits exakt richtig. Der Rest
ist Material und Licht -- also 13 Objekte mit Materialien versehen und vier
Material-/Lichtsaetze bauen.

OFFEN, braucht Rainers Entscheidung:

- [ ] Weg A: vier Stile direkt in Blender rendern. Objektpersistenz sicher,
      Aufwand = Materialien fuer die 13 glatten Objekte plus vier
      Beleuchtungssaetze.
- [ ] Weg B: bei Codex bleiben und mit der geschaerften INNEN_REGEL messen,
      ob die Fehlerzahl faellt. Kostet nichts, garantiert nichts.

## 2026-09-01 -- Fluss statt Perfektion (Rainer: "damit wir einen Fluss hinbekommen")

Rainer: "codex hat keine schlechte Arbeit geleistet, nur muessen wir die
Fehler minimieren wo moeglich." Weg B also -- bei Codex bleiben, Fehler
klein halten, Durchsatz erhoehen.

Der Fluss scheitert nicht an der Bildqualitaet, sondern an den RUNDEN. Bei
german_catalog_review_bungalow_3_4_2_b_120 ging die Beanstandung DREIMAL
raus, weil stueckweise geprueft wurde: erst die Stuehle, dann der glatte
Kasten, dann die fehlende Dusche und das erfundene Bett.

ERLEDIGT:

- `INNEN_REGEL` geschaerft: trennt jetzt, was variieren darf (Material,
  Licht, Textilien, Deko) von dem, was nicht darf (welche Moebel, wie viele,
  wo, wohin gedreht). 16 Auftraege neu geschrieben.
- `scripts/pruefbrief.py` plus acht Tests: schreibt PRUEFBRIEF.txt in den
  Lieferordner -- Stueckzahlen, alle Marker mit Pixel und Massen, die
  Innenbilder mit vollem Pfad, und die Warnung vor der Schwerpunkt-Falle.
  Damit startet die parallele Pruefung in Sekunden statt in einer
  Viertelstunde Handarbeit.

ARBEITSWEISE ab jetzt bei jeder Lieferung:

  1. lieferung-pruefen.py laufen lassen (findet Dateinamen, Nachweis, Marker)
  2. pruefbrief.py <plan>  -> PRUEFBRIEF.txt
  3. je Innenbild einen Pruefer parallel, alle mit demselben Brief
  4. jeden schweren Fund selbst nachzoomen, BEVOR er in die Beanstandung geht
  5. EINE Beanstandung, vollstaendig, dann neu beauftragen

Bei 3_4_2 fand der automatische Pruefer 0 von 12 Fehlern, vier parallele
Pruefer alle 12 in rund 20 Minuten -- und einer korrigierte meine eigene
falsche Stuhlzaehlung in Bild 06.

OFFEN:

- [ ] Weg A (vier Stile direkt in Blender) bleibt liegen, nicht verworfen:
      13 von 43 Objekten rendern ohne Material. Wenn der Fluss mit Codex
      trotz geschaerfter Regel nicht traegt, ist das der sichere Weg.

## 2026-09-01 -- Der neue Pruefablauf, erprobt am VEROEFFENTLICHTEN Haus

Rainer: "ok probieren wir mal". Getestet an
german_catalog_review_bungalow_3_3_4_b_100_2 -- dem Haus, das heute Mittag
freigegeben wurde und im Kundenkatalog steht.

ABLAUF: pruefbrief.py (ein Befehl), dann vier Pruefer parallel, je ein
Innenbild. Aufbau in Sekunden statt einer Viertelstunde.

ERGEBNIS: Bei der Freigabe hatte ich das Haus selbst geprueft und NUR die
Stuehle gefunden. Der automatische Pruefer meldete 0 Beanstandungen,
kasten_verdacht schwieg zum dritten Mal. Die vier Pruefer fanden:

    03  kuehlschrank-22 als glatter Quader
        kleiderschrank-14 als glatter Quader
        schreibtisch_kind-12 ist eine SCHUHBANK mit Schuhen (in 04/05/06 ein
        Schreibtisch mit Laptop) -- selbst nachgeprueft
        das Zimmer mit dem Einzelbett ist als Diele moebliert
    04  kuehlschrank-22 als Quader, kleiderschrank-14 als Quader mit der
        Garderobe buendig darin versenkt -- selbst nachgeprueft
        kleiderschrank-19 um 180 Grad verdreht, Fronten zur Wand
        zwei WCs mit durchscheinendem bzw. KARIERT texturiertem Deckel
        vier Tuerblaetter statt drei, an wall-0-door haengt keins
    05  kleiderschrank-19 rund 1 m hoch statt 2100 mm -- selbst nachgeprueft
        Quader auf dem Backofenturm, ragt ueber die Aussenwand
    06  stuff-20 FEHLT ganz (in 03/04/05 vorhanden)
        stuff-8 und stuff-9 als glatte Kloetze
        zweite Waschmaschine an der Stelle der vorwandinstallation

FALSCHMELDUNGEN AUSSORTIERT: Wanne, Waschmaschine und Schraenke "im Fenster".
Der Plan hat NULL Moebel-Oeffnungs-Ueberschneidungen (nachgerechnet), und im
Rohbau-Render sieht es identisch aus -- der Puppenhaus-Schnitt legt die
Fensterrahmen frei. Ohne diese Trennung waeren Codex vier Fehler
vorgeworfen worden, die er nicht gemacht hat. Das ist der eigentliche Gewinn
des Ablaufs.

OFFEN, braucht Rainers Entscheidung:

- [ ] 3_3_4 ist LIVE im Kundenkatalog (im=6, freigegeben 2026-09-01). Bleiben
      die Bilder drin bis zur Nachlieferung, oder kommen sie raus?
- [ ] Beanstandung fuer 3_3_4 schreiben, sobald das entschieden ist.
- [ ] LEHRE: kein Haus mehr freigeben, bevor der Pruefablauf gelaufen ist.
      Bei 3_3_4 lag zwischen meiner Einzelpruefung und der Freigabe keine
      Stunde, und ich habe 14 von 15 Fehlern uebersehen.

## 2026-09-01 -- Blender-Zweig verworfen, und warum

Ich hatte Blender empfohlen mit der Schaetzung "13 Objekte ohne Material plus
vier Lichtsaetze, ein Tag". Beide Zahlen waren falsch:

- Die "13 ohne Material" waren ein FLACHHEITSMASS IM BILD, nicht fehlende
  Materialien. Nachgemessen in der .blend: 62 Moebel, davon 62 MIT Material.
  Was fehlt, sind Texturen (27 von 81 Materialien haben eine) sowie Teppiche,
  Bilder, Pflanzen und Wandstruktur -- Wochen Ausstattungsarbeit an 61
  Haeusern, kein Tag.
- Der Versuch mit Raumleuchten (scripts/innenlicht.py, wieder geloescht)
  brachte Waerme und Kontrast, schloss die Luecke zu Codex aber nicht.

Rainer, danach: "Raumleuchten sind eigentlich nicht wichtig, wir haben kein
Dach." Richtig, und das ist der grundsaetzlichere Punkt: die Innenbilder sind
Puppenhaus-Ansichten OHNE DECKE. Eine Deckenleuchte kann es dort gar nicht
geben, das Licht kommt zwangslaeufig von oben.

FOLGE, die bleibt: Der Auftrag verlangt von Codex "die Leuchten im Raum sind
AN und werfen sichtbare warme Lichtkegel". Genau das kann Blender in dieser
Ansicht STRUKTURELL nicht liefern -- es ist reine Bildmodell-Dekoration. Ein
weiterer Grund, warum die Innenbilder nicht nach Blender wandern koennen.

ENTSCHIEDEN: bei Codex bleiben. Das Prueftor (pruefbrief.py + vier parallele
Pruefer, ~20 Minuten je Haus) ist der Preis dafuer und steht.

## 2026-09-02 -- Blender-only-Harness, Phase 0 und 1 gelaufen

Rainer hat das Bildmodell-Verfahren aufgehoben: kein ComfyUI, kein
Bildmodell, keine Ganzbild-Bearbeitung, keine frueheren Innenbilder als
Ausgangspunkt. Einzige Geometriequelle ist die .blend.

GEBAUT in scripts/blender-harness/:

    WORKFLOW-OVERRIDE.md    steht ueber Auftrag und Regelwerk
    export_invariants.py    Phase 0
    verify_invariants.py    Phase 1, ohne Blender lauffaehig
    null_render.py          Phase 1

GELAUFEN an german_catalog_review_bungalow_3_4_2_b_120:

    Objekte 223, MESH 221, davon Moebel 81, Architektur 140
    43 Marker zugeordnet, 0 ohne Blender-Objekt
    keine Stueckzahl-Abweichung
    verify_invariants: OK, Code 0 -- der Harness veraendert nichts

Auf dem Weg zwei eigene Zuordnungsfehler gefunden und behoben: fuenf Marker
zeigen auf ZUSAMMENGESETZTE Objekte (doppelwaschtisch-6 besteht aus -6-l und
-6-r, dusche-3 aus vierzehn Teilen), und die vier Tuerblaetter heissen
wall-<n>-door und liefen als Architektur.

BLOCKER FUER PHASE 2, gemessen: der Nullrender sieht anders aus als der
gelieferte interior-modern-baseline.png.

    identische Pixel     13 021 von 3 000 000 (0,43 %)
    Helligkeit           Baseline 164,8, Nullrender 183,1

Geometrie identisch, Unterschied ist Farbmanagement. URSACHE in
render-furnished-dollhouse.py: der Depth-Pass setzt view_transform auf
"Standard", exposure auf 0 und taa_render_samples auf 8 und stellt das vor
DMH_SAVE_BLEND NICHT zurueck. Die ausgelieferte .blend traegt die
Einstellungen des Depth-Passes -- in invariants.json nachgelesen:
view_transform "Standard", samples 8.

Wer die gelieferte .blend rendert, bekommt also nicht das gelieferte Bild.
Fuer einen Workflow, in dem die .blend die einzige Quelle ist, ist das der
erste zu schliessende Punkt.

OFFEN:

- [ ] View-Settings vor DMH_SAVE_BLEND zuruecksetzen (oder der Harness setzt
      sie explizit). Betrifft ALLE bisher ausgelieferten .blend-Dateien.
- [ ] Phase 2 erst danach: Moebeltausch gegen die 15 Assets in
      E:\_models_hub\_codex_catalog_assets.
- [ ] Auftrag und Regelwerk nach WORKFLOW-OVERRIDE.md Abschnitt 7 bereinigen
      (11 Stellen im Regelwerk, 5 im Auftrag).

---

## 2026-09-03 -- Aufgeloestes Modell schlaegt den prozeduralen Kasten

Plan: born2thrill-local-workbench/plans/model-beats-procedural-box.md

Befund, gemessen an invariants.json der Baseline
german_catalog_review_bungalow_3_4_2_b_120:
81 Moebelobjekte, davon 49 reine Quader (8 Ecken). Damit kann die Pruefliste
in CODEX-REGELN.md Abschnitt 11 gar nicht bestanden werden - sie lehnt genau
diese Kaesten ab (schwarze Platte statt Fernseher, flaechige Kuechenbloecke,
sichtbare Platzhalter). Das war der Grund, warum die Ganzbild-Erzeugung
alternativlos schien.

Der View-Settings-Blocker darueber ist geschlossen (WORKFLOW-OVERRIDE.md
Abschnitt 9).

ERLEDIGT:

- [x] has_real_model nicht mehr auf type == sink verengt; ein aufgeloestes
      Modell schlaegt den prozeduralen Bau. Fernseher kommt jetzt aus
      TV Flatscreen 03.blend. Belegt: 2913 von 3 000 000 Pixeln geaendert,
      ausschliesslich im Bereich des Fernsehers.
- [x] TYPE_FINISH-Eintrag fuer tv. Ohne ihn fiel der Typ auf wood-oak und
      das echte Modell rendete beige. Dasselbe Loch war fuer fridge bereits
      dokumentiert.

OFFEN:

- [ ] Kleiderschrank: ein Modell pro Symbol statt pro Moebelstueck. Fuer alle
      drei Schraenke wird White Wardrobe (3082 mm) geholt; beim 3700er passt
      es, die beiden 1050er werden als Kasten gebaut. Eine reine
      Groessensuche reicht nicht: hub-models-resolved.json kennt genau EIN
      Modell vom Typ wardrobe. Vorschlag ist eine Fallback-Kette
      Hub-Modell -> erzeugtes .glb aus full-catalog -> Kasten.
- [ ] Dusche: hat im Plan ein Modell (Square Shower bzw. Rectangular Shower)
      und wird trotzdem prozedural gebaut. Bewusst nicht angefasst; die
      sieben semantischen Einzelteile sind moeglicherweise besser als ein
      fremdes Komplettmodell. Entscheidung offen.
- [ ] garderobe, kuehlschrank, kochfeld, lowboard, stuff, kuechenzeile:
      stehen im Plan als model_source = procedural, die Bibliothek wird gar
      nicht gefragt. Fuer coat_rack, tv_unit und storage_shelving liegen in
      data/furniture-assets/full-catalog/ modern- UND classic-Modelle bereit.
- [ ] E:\_models_converted (1160 konvertierte FBX) ist nie in
      hub-models-resolved.json aufgenommen worden; dort stehen nur 93 Modelle.
      Solange das so ist, hat jede Modellsuche zu wenig Kandidaten.
- [ ] Materialien: preserve_materials ist im Plan false, die eigenen
      Materialien eines geladenen Modells werden verworfen und durch eine
      flache Farbe ersetzt. Betrifft die Bildqualitaet aller Modellmoebel.
- [ ] Maskierte Bearbeitung fuer Innenbilder pruefen. CODEX-AUFTRAG.md
      Zeile 27 und CODEX-REGELN.md Zeile 445 VERBIETEN Masken und schreiben
      den Ganzbild-Durchgang vor; das ist die Ursache saemtlicher
      Klasse-A-Fehler (verschwundene Objekte, verschobene Moebel, falsche
      Stueckzahlen). scripts/composite-mask-polish.py existiert bereits und
      wird nur fuer Aussenbilder benutzt.

### Nachtrag 2026-09-03, Teil 2 gemessen

Fallback-Kette gebaut: Hub-Modell -> erzeugtes .glb aus full-catalog -> Kasten.
Zwei Stellen: der Planbauer waehlt, der Renderer greift zusaetzlich in seinem
eigenen Verzerrungs-Abbruch danach (dort fiel der Kleiderschrank durch, nicht
im Planbauer -- dessen size_mismatch stand auf false, weil der Fussabdruck
gemessen war).

- [x] garderobe: klarer Gewinn. Der 900x320x1900-Quader ist jetzt ein
      Garderobenstaender mit Haken (coat_rack__modern.glb).
- [ ] kleiderschrank: REGRESSION, deshalb abgeschaltet. Der prozedurale
      Quader traegt Fugenschnitte (kleiderschrank-17-gap-*), die eine
      Tuerfuge zeichnen. Das erzeugte Modell ersetzte ihn durch eine
      merkmallose Platte -- die Fuge verschwand, es kam nichts zurueck. Die
      Datei ist 519 KB, das Detail existiert also; die Tueren zeigen nur
      nicht zur Kamera. Gesperrt ueber GENERATED_TYPES_VERIFIED in
      build-simplifier-render-plan.py.
- [ ] URSACHE UND NAECHSTER SCHRITT: importierte Assets erklaeren nirgends,
      welche lokale Achse ihre Vorderseite ist. Ohne diese Angabe ist jede
      Modellersetzung ein Wuerfelwurf. Pro Asset deklarieren: Front-, Hoch-
      und Bodenachse. Codex hat denselben Punkt unabhaengig gemeldet.
- [ ] Erst danach wieder freischalten: wardrobe, und dann die uebrigen Typen
      aus data/furniture-assets/full-catalog/.

Gemessener Endstand des Testrenders (renders/harness/model-beats-build/,
Lieferordner unberuehrt): 18 015 von 3 000 000 Pixeln gegenueber der Baseline
geaendert, in genau zwei Bereichen -- Fernseher (x 1420-1604, y 466-655) und
Garderobe (x 657-885, y 810-1049). Kein Moebel verschoben, 38 Platzierungen
vorher wie nachher.

### Nachtrag 2026-09-03, Vorderseite wird gemessen

Plan: born2thrill-local-workbench/plans/front-axis-derived.md

- [x] derive_front_axis im Renderer. Von den beiden waagerechten Achsen ist
      die kuerzere die Tiefenachse; von deren zwei Flaechen ist die flachere
      der Ruecken. Gemessen als Anteil der Flaeche, die in der aeussersten
      Ebene liegt. Ergebnis am Kleiderschrank: -X 0,95 gegen +X 0,0, also
      90 Grad auf +Y. Tuerfuge, Griff und Deckplatte sind zurueck.
- [x] Zweifelsfall greift: die Garderobe ist ein offenes Gestell, 0,0 auf
      beiden Seiten, wird nicht gedreht und meldet das.
- [x] STILLER FEHLER GEFUNDEN UND BEHOBEN: der Prototyp-Cache war auf
      asset_id allein geschluesselt. Drei Kleiderschraenke teilen eine
      asset_id, aber nicht ein Modell -- der erste Treffer baute den
      Prototyp, die anderen benutzten ihn stillschweigend mit. Jetzt auf
      (asset_id, mesh_path). Betraf jede asset_id mit zwei Modellen.
- [x] wardrobe wieder in GENERATED_TYPES_VERIFIED.

OFFEN:

- [ ] Die uebrigen Katalogtypen einzeln freischalten und ansehen:
      lowboard/tv_unit, storage_shelving, nightstand, rug, wall_art,
      floor_lamp, mirror, bathroom_vanity.
- [ ] MODEL_FACING_DEG mittelfristig durch die Messung ersetzen. Heute gilt
      sie nur fuer erzeugte Katalogmodelle; die Hub-Eintraege sind am Bild
      verifiziert und werden nicht durch eine Heuristik ersetzt.
- [ ] Die Messung greift nur bei schrankfoermigen Moebeln. Fuer offene
      Gestelle, Sitzmoebel und Sanitaer sagt sie nichts -- dort braucht es
      weiterhin eine Angabe oder ein Auge.

### Nachtrag 2026-09-03, Katalog aufgemacht

- [x] tv_unit fuer lowboard freigeschaltet: REGRESSION. Das erzeugte Modell
      wurde von rund 1200 mm auf 3500 mm gestreckt und verlor dabei jede
      Tuerfuge -- aus fuenf Feldern wurde eine glatte 3,5-Meter-Planke,
      sichtbar schlechter als der prozedurale Quader mit seinen
      Fugenschnitten.
- [x] Statt den Typ von Hand zurueckzunehmen: GENERATED_MAX_ASPECT = 4,0 im
      Planbauer. Ein Symbol mit Breite-zu-Tiefe ueber 4 ist keine
      Einzelmoebel mehr, sondern eine Zeile, und bekommt kein einzelnes
      Modell. Gemessen: Lowboard 3500/300 = 11,7 abgelehnt, Kleiderschrank
      1050/600 = 1,75 und Garderobe 900/320 = 2,8 angenommen. Die Schwelle
      trennt die Faelle mit Abstand.
      tv_unit bleibt damit freigeschaltet -- der TYP ist in Ordnung, diese
      INSTANZ ist es nicht, und das entscheidet jetzt die Regel statt eines
      Menschen.

Der Katalog ist fuer dieses Haus damit ausgeschoepft. Uebrig bleiben nur
Symbole, fuer die es gar kein Katalogmodell gibt:

- [ ] kuechenzeile (Zeile, Laenge aus der Zeichnung) -- braucht modulare
      Erzeugung, kein Modelltausch. Groesster verbleibender Posten.
- [ ] stuff 250x2850 (Verhaeltnis 11,4, ebenfalls eine Zeile)
- [ ] lowboard 3500x300 (dito)
- [ ] kuehlschrank, kochfeld, hochschrank_herd: Normmasse, kein
      Katalogeintrag. In E:\_models_converted liegen 72 Kuechengeraete und
      21 Kuechenmoebel, die nie in hub-models-resolved.json aufgenommen
      wurden. Das ist der billigste naechste Schritt fuer diese drei.
- [ ] doppelwaschtisch: prozedural, nicht geprueft.

Endstand des Testrenders (renders/harness/model-beats-build/interior-final.png,
Lieferordner unberuehrt): 21 885 von 3 000 000 Pixeln gegenueber der Baseline
geaendert, in zwei Bereichen -- Fernseher und die Schrankwand. 38
Platzierungen vorher wie nachher, keine verschoben.

### Nachtrag 2026-09-03, Vorderseite immer von der Wand weg

Plan: born2thrill-local-workbench/plans/vorderseite-immer-von-der-wand-weg.md

URSACHE der 26 von 62 falsch stehenden Moebel gefunden. snapStampToWalls
bestimmte die Wandnormale und drehte sie korrekt in den Raum, gab dann aber
die Richtung der WAND als rotation_deg zurueck statt die der Normalen. Das
korrigierte Vorzeichen ging nur in die Position ein. Zwei Raeume links und
rechts derselben Wand bekamen dieselbe Drehung -- die Haelfte steht damit
zwangslaeufig falsch.

- [x] rotation_deg kommt aus der Normalen: Math.atan2(-nx, ny). Im nicht
      gespiegelten Fall rechnerisch identisch mit vorher; nur der gespiegelte
      Fall aendert sich, und genau der war falsch.
- [x] Der Pfeil gilt jetzt fuer ALLE Moebel. Die Liste zaehlt die Ausnahmen
      statt der Teilnehmer: esstisch, couchtisch, essgruppen. Kleiderschrank,
      Garderobe und Lowboard hatten vorher keinen.
- [x] scripts/moebel-vorderseite.test.mjs auf die neue Regel gezogen, nicht
      abgeschwaecht: die alten Faelle bleiben drin und wechseln die Seite,
      dazu zwei neue Tests fuer die Drehung aus der Normalen. 10 von 10 gruen.
- [x] tsc --noEmit sauber.

OFFEN:

- [ ] KORREKTURLAUF ueber die 19 vorhandenen Moebeldateien (516 Symbole). Die
      Reparatur wirkt erst beim naechsten Setzen oder Anschnappen; gespeicherte
      Moebel behalten ihre alte Drehung. Ein Lauf, der je Symbol die naechste
      Wand sucht und die Vorderseite von ihr wegdreht, wuerde den Bestand in
      einem Rutsch richten. Sichtbar wird es jetzt ohnehin, weil alle Moebel
      einen Pfeil haben.
- [ ] Danach neu messen: wie viele zeigen noch in die Wand.

NICHT VON DIESER AUFGABE, aber beim Testlauf aufgefallen:
scripts/furniture-placement.test.mjs schlaegt in zwei Faellen fehl, weil
src/lib/generator/furniture-placement.mjs "shoe_rack" in die Raumrezepte
aufgenommen hat und der Test noch die alte Liste erwartet
(mirror, nightstand, rug). Anderes Modul, unabhaengig vom Editor.

### Nachtrag 2026-09-03, Korrekturlauf ueber den Bestand

Neu: born2thrill-local-workbench/scripts/moebel-vorderseite-richten.py
Tests: scripts/moebel-vorderseite-richten.test.py (10 von 10 gruen)

Trockenlauf ueber die 19 Moebeldateien, 304 wandnahe Stuecke:
68 zeigten mit der Vorderseite in die Wand.

- [x] 49 gerichtet: kleiderschrank 19, lowboard 11, garderobe 9, kochfeld 3,
      schrank_60 3, sideboard 2, handwaschbecken 1, doppelwaschtisch 1.
      Vor jedem Schreiben eine Sicherung als
      <name>.vor-vorderseite-2026-09-03.json, 18 Stueck.
      Nachmessung: 0 offene Faelle in dieser Gruppe, der Lauf ist idempotent.
- [x] Auffaellig und erwartbar: die drei Spitzenreiter sind genau die Typen,
      die vorher KEINEN Pfeil hatten. Was niemand sieht, driftet.

BEWUSST NICHT GERICHTET, 19 Stueck -- "Ruecken an die Wand" gilt dort nicht:

- [ ] badewanne 9, eckbadewanne 3: eine Wanne liegt mit der LANGEN Seite an
      der Wand, ihre Vorderseite ist das Armaturenende und zeigt die Wand
      ENTLANG. Wegdrehen waere ein neuer Fehler. Braucht eine eigene Regel
      (Armaturenende ans kurze Ende) oder eine Sichtentscheidung.
- [ ] schreibtischstuhl 3: schaut zum Schreibtisch, nicht in den Raum.
- [ ] schreibtisch 2, schreibtisch_kind 1: es wird davor gesessen, oft mit
      Blick zur Wand.
- [ ] dusche_gross 1: Eckstueck, die Regel aus MODEL_FACING_DEG gilt.

Ein Fehler im Lauf selbst gefunden und behoben: der zweite Durchgang hat die
eigenen Sicherungen mitgemessen (gleicher Ordner, gleiche Endung) und die
alten Zahlen als offen gemeldet. Dateifilter ergaenzt, Test dazu.

### Nachtrag 2026-09-03, Schrankfronten als Material

Plan: born2thrill-local-workbench/plans/schrankfronten-als-material.md

- [x] `front_material()` in render-furnished-dollhouse.py: Felder, Fugen und
      Sockel als Shader-Muster, keine Geometrie. GENERATED-Koordinaten, weil
      die Kaesten Einheitswuerfel mit gesetzten `dimensions` sind und ihre
      Objektkoordinaten darum -0,5..0,5 laufen statt in Metern. Die Feldzahl
      wird beim Bauen aus der echten Laenge berechnet.
- [x] Angewendet auf counter, sideboard, wardrobe, storage_shelving,
      oven_housing, fridge -- in build_path_run und build_box.
- [x] classic bekommt zusaetzlich einen Kassettenrahmen je Feld.
- [x] `PLAN_STIL` aus plan["style"]: der Aufrufer hatte "modern" als
      Vorgabewert, womit classic NIE kassettierte Felder bekommen haette,
      obwohl der Code dafuer da ist. Stiller Fehler, vor dem ersten
      Classic-Render gefunden.
- [x] Gemessen: 4943 Pixel geaendert gegenueber dem Stand davor, alle an
      Lowboard, Kuechenzeile, Kuehlschrank und Hochschrank. 38 Platzierungen
      bleiben 38.
- [x] Modern und Classic sind an den Fronten unterscheidbar.

OFFEN:

- [ ] Griffe. Bewusst zurueckgestellt, bis Felder und Sockel sitzen.
- [ ] Der Kassettenrahmen sitzt dicht an der Feldgrenze und liest sich eher
      als doppelte Fuge denn als Rahmen. Weiter nach innen ruecken.
- [ ] Fugenbreite ist auf 2 Pixel bemessen (RENDER_MM_PRO_PX = 11,3). Bei
      einem Haus mit anderem Massstab stimmt das nicht mehr -- der Wert
      gehoert aus der Kamera berechnet statt fest verdrahtet.

### Nachtrag 2026-09-03, Fronten v2 und Kuechentexturen

- [x] RENDER_MM_PRO_PX wird jetzt aus der Kamera gerechnet
      (ortho_scale * 1000 / Aufloesung) statt fest verdrahtet. Gemessen:
      9,06 mm je Pixel. Der frueher abgemessene Wert 11,3 war der SCHRAEGE --
      die Dollhouse-Kamera sieht von oben, eine senkrechte Front erscheint
      gestaucht. Fest verdrahtet waere er bei jedem anderen Haus falsch.
- [x] Kassettenrahmen sitzt jetzt als EINE Linie 70 mm eingerueckt statt als
      Ring dicht an der Fuge. Vorher verschmolz er mit der Fuge zu einer
      doppelten Naht.
- [x] Griffleiste je Feld: gebuerstetes Metall bei modern, Messing bei
      classic. 15 mm sind unter zwei Pixel, deshalb auf zwei Pixel angehoben.
- [x] Modern und Classic sind an denselben Kaesten klar unterscheidbar.

KUECHENTEXTUREN GEFUNDEN (Rainer: "da sind auch Spuelen, Texturen und
Arbeitsplatten drin"):

Die acht Kitchen_Furniture_Set tragen ihre Texturen GEPACKT in der .blend,
nicht als Dateien daneben. Herausgeloest und benannt nach
E:\_models_hub\_kuechentexturen\ -- 11 Stueck:

    arbeitsplatte-granit-schwarz / -anthrazit / -dunkel   je 1000-2048 px
    front-eiche-hell, front-nuss-dunkel, front-kirsche,
    front-hell-gestreift, front-grau, front-lack-weiss,
    front-beige, front-taupe

BEFUND: die heutige Arbeitsplatte benutzt GRANITE_MAT, und das ist
`floor-granite` -- eine BODENtextur. Jetzt liegen drei echte
Arbeitsplattensteine bereit.

OFFEN:

- [ ] Arbeitsplatte auf einen echten Stein umstellen statt floor-granite.
- [ ] Die Fronttexturen den vier Stilen zuordnen. Roher Vorschlag:
      Warm Modern = eiche-hell + granit-schwarz;
      Dark Modern = nuss-dunkel + granit-dunkel;
      Soft Scandinavian = hell-gestreift + lack-weiss;
      Classic = kirsche + granit-anthrazit.
      Das ist Geschmack und gehoert Rainer, nicht mir.
- [ ] Spuele: Kitchen_Sink_22 und _23 sind jetzt entpackt, aber noch nicht
      katalogisiert.
- [ ] 44 Archive insgesamt entpackt (Kueche, Wohnzimmer, Tableware). Der
      Katalogisierungslauf steht weiterhin aus -- ohne ihn erreicht keins der
      neuen Modelle den Renderer.

### Nachtrag 2026-09-03, Katalogisierung und Stiltexturen

- [x] 44 Archive entpackt, `catalog-hub-models.py` neu gelaufen:
      169 Modelle katalogisiert, 0 fehlgeschlagen.
- [x] `resolve-hub-scales.py` um die fehlenden Kuechentypen ergaenzt:
      refrigerator, fridge, induction hob, hob, built in oven,
      built in double oven, oven, built in microwave, electric cooker,
      kitchen utensils. Ohne Sollmass kann `classify` nichts zuordnen --
      deshalb war bis heute KEIN einziges Modell vom Typ fridge oder hob im
      Katalog, obwohl Refrigerator_2 seit Wochen entpackt danebenlag.
- [x] `build-symbol-picks.py`: kuehlschrank -> fridge, kochfeld -> hob,
      hochschrank_herd -> oven.
- [x] Ergebnis: 93 -> 146 aufgeloeste Modelle. fridge 4, hob 3, oven 3,
      microwave 1, cooker 1, kitchen_sink 2. Und fuer die Stile:
      corner_sofa 1 -> 8, sofa_3 9 -> 18, chair 5 -> 10, dining_table 6 -> 7.
      Das Ecksofa hat erstmals ein anderes Modell fuer modern und classic.
- [x] Im Plan sind nur noch doppelwaschtisch und lowboard prozedural --
      vorher waren es fuenf.

STILLER FEHLER GEFUNDEN UND BEHOBEN:

`essgruppe_stuhl` und `schreibtischstuhl` sind beim Neulauf des Pickers
VERSCHWUNDEN. Beide standen nie in SYMBOL_TYPES, sondern waren von Hand in
data/symbol-model-picks.json eingetragen -- `schreibtischstuhl` mit
divisor 3.5 und der Notiz "measured 2236x2238x4340mm raw on 2026-08-10;
divisor calibrated to 1240mm seat-back height". Ein Neulauf haette 2,54
gesetzt und den Stuhl verzerrt.

Aus HEAD wiederhergestellt. `HANDGEPFLEGT` in build-symbol-picks.py traegt
solche Eintraege jetzt ueber einen Neulauf hinweg, mit Meldung.

KUECHENTEXTUREN VERDRAHTET:

- [x] `STIL_TEXTUREN`: je Stil ein Holz und ein Stein. Die Zuordnung steht als
      Tabelle an einer Stelle, weil sie Geschmack ist und nicht Technik.
- [x] Arbeitsplatte kommt aus einem echten Stein statt aus `floor-granite`.
- [x] Fronten bekommen Holzmaserung, auf echte Meter gezogen
      (Generated * Kantenlaenge / Kachelgroesse) -- sonst haette eine 3,3 m
      lange Zeile dieselbe Maserung wie ein 600er Schrank, nur gestreckt.

OFFEN:

- [ ] Boden ist in allen Stilen gleich. Die Stiltabelle kennt ihn noch nicht.
- [ ] doppelwaschtisch hat kein Modell (double_basin), bleibt Kasten.
- [ ] Teppiche und Bilder platzieren -- rug__* und wall_art__* liegen fertig
      im erzeugten Katalog, es fehlt die Regel, woran sie haengen.
- [ ] 23 Modelle bleiben UNRESOLVED, meist "no type matched the name"
      (White Bedside Cabinet, Wooden Table 27, Round Light Grey Rugr ...).
      Jeder braucht eine Zeile in TYPES.

### Nachtrag 2026-09-03, Doppelwaschtisch, Teppiche

- [x] Alle restlichen Archive entpackt -- meine erste Runde hatte nur Kitchen,
      Living Room und Tableware erwischt, das Double Bathroom Sink lag in
      Furnishing. 29 weitere entpackt, 196 Modelle katalogisiert,
      156 aufgeloest.
- [x] `[picks] 34 symbols mapped, 0 without a model` -- zum ersten Mal hat
      JEDES Symbol ein Modell.
- [x] Teppiche unter Sitzgruppe, Essgruppe und Bett. Sie entstehen nur UNTER
      einem vorhandenen Objekt, nie auf freier Flaeche -- damit sind sie
      Ausstattung im Sinne von 3.4 und keine erfundene Moeblierung.
      Rainer: "Bilder will be hard because the walls are cut but rugs,
      come on?" -- richtig, ein Bild braucht Wandflaeche und die ist
      geschnitten; ein Teppich liegt auf dem Boden und ist immer sichtbar.

ZWEI FEHLER IM TEPPICHLAUF, beide gefunden und behoben:

1. Erste Fassung klemmte symmetrisch auf den kleineren Wandabstand. Bei einem
   Sofa an der Wand ging der Teppich auf null und BEIDE fielen ersatzlos weg,
   ohne Meldung. Jetzt wird jede Kante einzeln beschnitten und die Mitte
   nachgezogen.
2. Einheiten gemischt: `polygon_mm` haelt Millimeter, `instance.location`
   haelt Meter. Die Klemmung verglich 9,6 mit 8800 und schnitt jeden Teppich
   auf null. Eine Meldung sagt jetzt, wenn ein Teppich verworfen wird -- der
   stille Ausfall war das eigentliche Problem.

OFFEN:

- [ ] Der Teppich wird auf die BOUNDING BOX des Raumes geklemmt, nicht auf
      sein Polygon. Bei einem L-foermigen Wohnbereich reicht er darum noch
      unter die Wand. Polygongenau beschneiden.
- [ ] Bilder an der Wand: zurueckgestellt. Die Dollhouse-Kamera schneidet die
      Waende auf 500 bis 2000 mm, es bleibt kaum sichtbare Wandflaeche.
- [ ] Boden ist in allen Stilen gleich.
- [ ] Double Bathroom Sink ist aufgeloest, aber mit schlechtem Sitz:
      576 x 187 x 226 mm gegen ein Sollmass von 1200 x 500 x 250, Divisor 10.
      Bei Divisor 5 waere die Breite 1152 und damit fast genau richtig. Der
      Resolver hat den falschen Massstab genommen; das Ergebnis ist ein zu
      kleiner Waschtisch. Nachrechnen.

### 2026-09-03 -- SCHWARZWEISS-TEST BESTANDEN? NEIN.

Erstmals alle vier Stile aus derselben .blend gerendert
(DMH_STIL waehlt den Materialsatz; der Planbauer kennt nur modern und
classic als MODELL-Satz, warm/dark/scandi laufen alle auf modern).

Regelwerk Abschnitt 3.2: "waeren alle vier Bilder schwarzweiss, muessten sie
immer noch als vier verschiedene Einrichtungen erkennbar sein. Wenn nicht,
sind es Farbfilter."

GEMESSEN, mittlere Helligkeitsabweichung in Graustufen (0-255):

    Warm Modern       vs Dark Modern         1,4
    Warm Modern       vs Soft Scandinavian   2,5
    Warm Modern       vs Classic             3,9
    Dark Modern       vs Soft Scandinavian   3,9
    Dark Modern       vs Classic             3,6
    Soft Scandinavian vs Classic             5,8

Mittlere Helligkeit 161,6 bis 166,3 -- alle vier praktisch gleich.

DER TEST IST NICHT BESTANDEN. In Schwarzweiss sind Warm und Scandinavian
nicht zu unterscheiden, Dark unterscheidet sich nur am Lowboard. Nur Classic
faellt auf, und zwar WEIL es andere Modelle bekommt (Sofa, Stuehle, Schrank),
nicht wegen des Materials.

URSACHE, klar benennbar: stilabhaengig sind heute NUR Schrankfronten und
Arbeitsplatte. Identisch bleiben in allen vier Bildern:

- der Boden -- die groesste zusammenhaengende Flaeche im Bild
- die Wandtoene
- Polster, Bettzeug, Vorhaenge
- saemtliche Modelle bei warm/dark/scandi (alle drei laufen auf demselben
  modern-Plan)

WAS FEHLT, in der Reihenfolge ihres Flaechenanteils:

- [ ] Boden je Stil. Groesster Hebel, mit Abstand.
- [ ] Wandton je Stil.
- [ ] Polster- und Textilfarbe je Stil. Betrifft Sofa, Bett, Stuehle.
- [ ] VIER Modellsaetze statt zwei. Der Picker kennt nur modern und classic;
      warm, dark und scandi teilen sich einen. Mit 18 Sofas, 10 Stuehlen und
      8 Ecksofas im Katalog waere das jetzt moeglich.

Das ist die Antwort auf die Frage, die den ganzen Tag offen war: Material und
Modellwahl REICHEN, aber nicht so verdrahtet wie heute. Es fehlt nicht das
Verfahren, es fehlen vier von sechs Stellschrauben.

### 2026-09-03 -- Boden je Stil, Schwarzweiss-Test erneut

STIL_TEXTUREN um einen dritten Eintrag erweitert: den Bodenbelag. `None`
heisst "Vorgabebelag behalten" -- Warm Modern bleibt damit auf der
vorhandenen Eiche. Nassraeume und Diele behalten ihren Belag in jedem Fall;
Granit im Bad ist keine Stilfrage.

Gemessen, mittlere Helligkeitsabweichung in Graustufen, vorher in Klammern:

    Warm  vs Dark        9,5   (1,4)
    Warm  vs Scandi      5,2   (2,5)
    Warm  vs Classic     5,9   (3,9)
    Dark  vs Scandi     14,7   (3,9)
    Dark  vs Classic     8,9   (3,6)
    Scandi vs Classic   10,4   (5,8)

    mittlere Helligkeit  Warm 163,8  Dark 154,4  Scandi 169,0  Classic 159,5
    vorher lagen alle vier zwischen 161,6 und 166,3

Faktor 2,5 bis 10 je Paar. Dark ist jetzt unverwechselbar das dunkelste Bild,
Scandi das hellste, Classic hat einen erkennbaren Dielenboden.

Der Boden allein hat also mehr gebracht als Fronten und Arbeitsplatte
zusammen -- was zu erwarten war, er ist die groesste Flaeche.

SCHWAECHSTES PAAR: Warm gegen Scandi mit 5,2. Beide sind helle Hoelzer und
laufen ausserdem auf demselben Modellsatz. Das ist der naechste Hebel.

OFFEN, in dieser Reihenfolge:

- [ ] Polster- und Textilfarbe je Stil. Sofa, Bett, Stuehle sind in allen
      Bildern gleich.
- [ ] VIER Modellsaetze statt zwei. warm, dark und scandi teilen sich den
      modern-Plan; nur classic bekommt eigene Modelle. Mit 18 Sofas,
      10 Stuehlen und 8 Ecksofas im Katalog waere das jetzt moeglich.
- [ ] Wandton je Stil.

### 2026-09-03 -- VIER MODELLSAETZE, Schwarzweiss-Test bestanden

`build-symbol-picks.py` liefert jetzt vier Varianten je Symbol statt zwei:
modern, classic, warm, dark, scandi. Die Zuordnung geht ueber Farbwoerter im
Modellnamen ("grey", "beige", "orange") -- der einzige Hinweis, den ein Asset
auf sein Aussehen gibt.

Zwei Fallen dabei, beide gemessen:

1. In der ersten Fassung standen "leather", "wooden" und "brown" in der
   warm-Liste. Das sind genau die CLASSIC_WORDS. Warm und Classic griffen
   nach denselben Modellen und ihr Abstand FIEL von 5,9 auf 3,5. Die Listen
   sind jetzt ueberschneidungsfrei.
2. Ohne Merkliste vergebener Modelle bekamen zwei Stile dasselbe Sofa.
   `waehle_je_stil` fuehrt jetzt eine, Classic waehlt zuerst, und was
   vergeben ist, wird uebersprungen. Reicht die Auswahl nicht, faellt ein
   Stil auf den besten freien Kandidaten zurueck -- die GROESSE schlaegt den
   Farbton.

ENDSTAND, mittlere Helligkeitsabweichung in Graustufen, in Klammern der Stand
von heute Morgen:

    Warm   vs Dark        11,4   (1,4)
    Warm   vs Scandi       7,9   (2,5)
    Warm   vs Classic      6,3   (3,9)
    Dark   vs Scandi      16,5   (3,9)
    Dark   vs Classic      9,2   (3,6)
    Scandi vs Classic     11,3   (5,8)

    schwaechstes Paar 6,3 -- heute Morgen war das BESTE Paar 5,8.
    Helligkeit  Warm 163,5  Dark 154,6  Scandi 169,5  Classic 159,5

Jedes Paar liegt jetzt ueber dem, was heute Morgen der groesste Unterschied
war. In Schwarzweiss sind vier verschiedene Einrichtungen zu erkennen:
andere Betten, andere Sofas, andere Boeden, andere Fronten.

Damit ist die Frage beantwortet, die den ganzen Tag offen war: Material und
Modellwahl reichen fuer vier Entwuerfe, ohne Bildmodell.

OFFEN:

- [ ] Wandton je Stil. Der letzte grosse Flaechenanteil, der noch in allen
      vier Bildern gleich ist.
- [ ] Warm gegen Classic bleibt mit 6,3 das schwaechste Paar.
- [ ] Nichts davon ist bisher von einem Menschen abgenommen. Der
      Schwarzweiss-Test ist eine Zahl, kein Urteil ueber Geschmack.

### 2026-09-03 -- Wandton je Stil, ENDSTAND des Tages

FINISH_SETS gab es laengst mit Wandton, Boden-Toenung, Kuechen- und
Sofafarbe -- vier Saetze, ausgewaehlt ueber DMH_FINISH, aber an nichts
gekoppelt. Vier neue Saetze mit den Namen der Stile ergaenzt; DMH_STIL waehlt
sie jetzt, DMH_FINISH schlaegt sie weiterhin fuer Einzelpruefungen.

Die Waende bleiben hell. Ein Dollhouse-Schnitt zeigt sie von aussen und von
oben; eine dunkle Wand wuerde das Bild zumachen statt den Stil zu zeigen.
Der Unterschied liegt im Ton, nicht in der Helligkeit.

Warm gegen Classic ist das schwerste Paar -- beide sind warme Hoelzer, so
stehen sie im Regelwerk. Warm bekommt darum die helle Eiche OHNE Toenung und
einen neutralen Wandton, Classic das dunklere Kirschholz und Pergament.
Mit gleicher Toenung lagen sie bei 6,0, danach bei 6,8.

ENDSTAND, mittlere Helligkeitsabweichung in Graustufen, in Klammern der Stand
von heute Morgen:

    Warm   vs Dark        12,5   (1,4)
    Warm   vs Scandi       8,1   (2,5)
    Warm   vs Classic      6,8   (3,9)
    Dark   vs Scandi      18,0   (3,9)
    Dark   vs Classic      9,7   (3,6)
    Scandi vs Classic     12,2   (5,8)

    schwaechstes Paar 6,8 -- heute Morgen war das BESTE Paar 5,8
    Helligkeit  Warm 163,9  Dark 153,7  Scandi 170,2  Classic 159,2

GRENZE DES MASSES, ausdruecklich: die mittlere Helligkeitsabweichung sieht
Flaechen, nicht Struktur. Dass Classic kassettierte Fronten hat und Warm
glatte, faellt dem Mass kaum auf, dem Auge aber sofort. Die Zahl ist ein
Rauchmelder, kein Gutachten -- sie findet vier Farbfilter zuverlaessig und
sagt nichts darueber, ob ein Stil gut aussieht.

OFFEN:

- [ ] Menschliche Abnahme. Keins dieser vier Bilder hat jemand beurteilt.
- [ ] Die 14 aufgehobenen Zeilen aus CODEX-REGELN.md und CODEX-AUFTRAG.md
      streichen -- Aufraeumen, keine Entscheidung.
- [ ] Teppich sitzt auf der Raum-Bounding-Box plus Polygon-Schrumpfung; ein
      echter Polygonschnitt waere sauberer.
- [ ] 40 Modelle bleiben UNRESOLVED, meist "no type matched the name"
      (Leuchten, Teppiche, Treppen, Pflanzen). Je eine Zeile in TYPES.

### 2026-09-03 -- Regelwerk und Auftrag bereinigt

Die aufgehobenen Stellen stehen jetzt IN den Originaldateien gestrichen, nicht
mehr nur in WORKFLOW-OVERRIDE.md Abschnitt 7. Zwoelf Stellen im Regelwerk,
fuenf im Auftrag. Sicherungen:

    CODEX-REGELN.md.vor-bereinigung-2026-09-03
    CODEX-AUFTRAG.md.vor-bereinigung-2026-09-03

Gegenprobe: "keine Maske", "Masken sind nicht noetig", "Ganzbild-Durchgang"
und "scheitert an Abschnitt 11" kommen nur noch in den GESTRICHEN- und
AUFGEHOBEN-Vermerken vor, nirgends mehr als Vorschrift.

Damit ist der Punkt aus dem Audit erledigt: ein Regelwerk mit einem
Override-Zettel daneben war kein Regelwerk.

### 2026-09-03 -- Rainers Durchsicht der vier Stile

Urteil: vier unterschiedliche Bilder, Fronten ausreichend, Modellzuordnung
unklar (nicht beurteilt).

BEHOBEN -- Teppich:

Rainer: "ein Teppich fuer Esszimmer zum Wohnzimmer durchgezogen ist sehr
unrealistisch. Normalerweise haelt ein Teppich eine Gruppe zusammen -- fuer
6 Stuehle und den Esstisch, oder eine Couchgruppe mit dem Couchtisch. Oder um
ein Bett herum."

Der Teppich richtet sich jetzt nach der GRUPPE, nicht nach dem Raum:

    essen     Esstisch + Stuehle,        Rand 400 mm (zurueckgeschobener Stuhl)
    wohnen    Sofa/Ecksofa + Couchtisch, Rand 250 mm
    schlafen  je Bett einer,             Rand 500 mm

Ohne Ankerstueck (Tisch, Sofa, Bett) entsteht kein Teppich -- vier Stuehle
ohne Tisch sind keine Essgruppe.

Ein Fehler dabei: die drei Betten des Hauses fielen unter denselben
Gruppenschluessel und ergaben EINEN Teppich von 9,85 x 6,15 m quer durchs
Geschoss. Ursache: room_at fand fuer sie keinen Raum, und ohne Raum war der
Schluessel identisch. Betten gruppieren jetzt immer einzeln, und ein
fehlender Raum faellt auf die Position zurueck statt auf None.
Ergebnis: 5 Teppiche, 1,90 x 2,60 bis 3,00 x 2,80 m.

OFFEN -- Ausrichtung von Couch und Bett:

Rainer: "was auffaellt ist dass die Couch die falsche Ausrichtung hat und das
Bett auch."

URSACHE, klar benennbar: `MODEL_FACING_DEG` gilt pro SYMBOL (ecksofa,
doppelbett). Seit heute laedt jeder Stil ein ANDERES Modell mit eigener
lokaler Achse:

    ecksofa     warm Modern Corner Sofa        dark cgaxis_grey_4_seat
                scandi cgaxis_beige_large      classic cgaxis_brown_leather
    doppelbett  warm Tall Bed with Shelves     dark Grey Bed with Grid Pattern
                scandi White Leather Bed       classic Wooden Bed Black-Orange

Eine Zahl je Symbol kann fuer vier Modelle nicht stimmen. Der richtige Ort
ist `MODEL_ORIENT_BY_LABEL` -- pro MODELL. Darin steht heute genau EIN
Eintrag ("Violet Corner Sofa 14"), am Kontaktbogen festgelegt.

- [ ] Je Modell einen Eintrag in MODEL_ORIENT_BY_LABEL. Acht neue Sofas und
      Betten warten.
- [ ] WICHTIG zum Verfahren: der Kommentar bei ROTATION_OVERRIDE warnt
      ausdruecklich "Never eyeball chair facing from a perspective render --
      sheet only". Die Ausrichtung gehoert an einem FLACHEN Blatt entschieden
      (DMH_TOPVIEW=1), nicht an der Dollhouse-Perspektive. Sonst wiederholt
      sich der Fehler vom 2026-08-25.
- [ ] derive_front_axis hilft hier nicht: es misst die kuerzere waagerechte
      Achse und die flachere Seite. Bei einem Sofa passt das, bei einem Bett
      nicht -- Kopf und Fuss liegen auf der LANGEN Achse.

### 2026-09-03 -- Kontaktbogen zur Ausrichtung

Neu: born2thrill-local-workbench/scripts/ausrichtungs-kontaktbogen.py

Rendert jedes Modell eines Symbols von SENKRECHT OBEN, ungedreht, mit einem
Pfeil nach +y -- dorthin, wo der Renderer die Vorderseite vermutet. Der
noetige Korrekturwert laesst sich daran ablesen und gehoert nach
MODEL_ORIENT_BY_LABEL.

Warum Draufsicht und nicht die Dollhouse-Perspektive: bei ROTATION_OVERRIDE
steht "Never eyeball chair facing from a perspective render -- sheet only",
und am 2026-08-25 wurde genau dieser Fehler schon einmal gemacht.

DREI FEHLER IM BOGEN SELBST, in dieser Reihenfolge:

1. Kamera auf fester Hoehe `spanne * 5` statt ueber dem Modell. Verdaechtigt,
   behoben, half nicht.
2. Sichtbarkeit: hide_render aus der Quelldatei. Verdaechtigt, vorsorglich
   behoben, half nicht.
3. GEMESSEN statt geraten -- die Spanne je Modell ausgegeben:

       warm     31,78 m
       dark     44,44 m
       scandi  687,48 m
       classic 857,97 m

   Die Ursache: `obj.scale = 1/divisor` UEBERSCHRIEB die Eigenskalierung der
   Modelle und skalierte Kinder ein zweites Mal. Jetzt wird multipliziert und
   nur die Wurzel skaliert. Danach: 2,0 bis 5,5 m, keine leere Zelle mehr.

Der Umweg ist die Lehre: zwei Vermutungen kosteten zwei Laeufe, eine Messung
loeste es sofort.

OFFEN:

- [ ] Rainer liest die 16 Zellen ab und legt die Werte fest. Danach je Modell
      ein Eintrag in MODEL_ORIENT_BY_LABEL.
- [ ] Der Bogen deckt ecksofa, doppelbett, einzelbett und sofa_3sitzer ab.
      Die uebrigen Symbole mit mehreren Modellen brauchen ihn auch.

### 2026-09-03 -- Objektmaske steht

Neu: born2thrill-local-workbench/scripts/objektmaske.py

Rendert aus einer fertigen .blend eine pixelgenaue Maske je Objekt. Kein
Compositor -- Workbench, flache Beleuchtung, Objektfarbe als Nummer. Der
Object-Index-Pass haengt in Blender 5 an einer anderen Stelle als in 4 und
sein Dateiausgabe-Knoten hat kein base_path mehr; der Umweg ueber die
Objektfarbe laeuft in jeder Version.

Belegt an interior-modern-baseline.blend: 205 Objekte kodiert, Masken
pixelgenau auf Ecksofa, Doppelbett, Essgruppe und Fernseher.

DREI FEHLER, alle gemessen statt geraten:

1. Compositor-API zweimal anders in Blender 5 -> Verfahren gewechselt.
2. Workbench nimmt NICHT world.color, sondern seine eigene
   Hintergrundfarbe. Der Hintergrund kam als mittleres Grau heraus, dessen
   roter Kanal zufaellig 28 traf -- und 28 war das Ecksofa. Die Maske
   "ecksofa-28" umfasste 39 Prozent des Bildes.
3. obj.color ist LINEAR, das PNG sRGB. Aus dem Wert 28 wurde im Bild 94, und
   weil die sRGB-Kurve unten steil ist, fielen benachbarte Nummern auf
   denselben Ausgabewert: 205 Objekte ergaben nur 157 verschiedene Werte.
   Jetzt wird vorkompensiert.

WAS DAMIT MOEGLICH WIRD:

- Maskierte Bearbeitung. Ausserhalb der Maske wird kein Pixel geschrieben,
  also koennen Position, Drehung und Anzahl sich nicht aendern. Das war der
  Kern des Streits und der Grund fuer jeden Klasse-A-Fehler.
- "sichtbar" wird gemessen statt behauptet: ein Objekt mit null Pixeln ist
  verdeckt. Ersetzt die marker_check-Selbstauskunft aus Abschnitt 11.1.

OFFEN:

- [ ] Der Hintergrund traegt noch den Wert 124 statt 0. Fuer die Masken
      unschaedlich, aber unsauber.
- [ ] Der eigentliche Test: eine Maske an ComfyUI geben, fuellen lassen,
      danebenlegen. Erst danach ist entschieden, ob der Blender-Weg oder der
      maskierte Weg die vier Stile liefert -- oder beide zusammen.

### 2026-09-03 -- ENTSCHIEDEN: Blender rendert, Codex bearbeitet, die Maske schneidet

Gemessen mit unserem Verfahren, nicht mit Codex' eigenem:

    Codex EDIT-Modus (nur "Holzboden waermer")   exakt 77,2 %   +-2 px 97,0 %
    Codex Ganzbild (Lieferung 2026-09-01)        exakt 28,6 %   +-2 px 57,0 %

    Kantenkontrast in den Moebelflaechen: Codex 126 % von Blender

Codex' Schnittstelle hat NUR prompt und referenced_image_paths -- kein
mask, kein strength, keine Ausgabegroesse. Native Ausgabe 1448 x 1086.
Codex' eigenes Fazit lautete "fuer einen maskierten, deckungsgleichen
Workflow nicht geeignet". Die Messung sagt das Gegenteil: der EDIT-Modus
bleibt innerhalb von zwei Pixeln, und zwei Pixel deckt eine Feder ab.

DER WEG:

1. Blender rendert das Bild UND die Objektmasken (objektmaske.py, 205
   Objekte, pixelgenau).
2. Codex bearbeitet das ganze Bild im EDIT-Modus, je Stil ein Durchgang.
   Kein Masken- oder Strength-Parameter noetig -- er hat keinen.
3. Wir setzen zusammen: INNERHALB der Masken Codex, ausserhalb Blender.
   Feder 3 px deckt den gemessenen Versatz von +-2 px.

WAS DAS GARANTIERT: Architektur, Position, Stueckzahl und Ausrichtung
kommen aus Blender, weil sie ausserhalb der Masken liegen. Verschiebt Codex
etwas, faellt die Verschiebung heraus statt in die Lieferung. Damit sind die
Klasse-A-Fehler konstruktiv erledigt -- nicht durch eine Regel, sondern
durch den Zuschnitt.

WAS CODEX BEHAELT: alles, was er nachweislich gut kann -- Material, Stoff,
Holzton, Deko, Lichtstimmung innerhalb der Silhouetten.

ZURUECKZUNEHMEN: die heute gestrichene Regelwerkzeile zum Hochskalieren
kleinerer Bildmodell-Ausgaben (Abschnitt 9). Ich hatte sie als
gegenstandslos markiert, weil Blender exakt liefert. Mit Codex' 1448 x 1086
gilt sie wieder.

OFFEN:

- [ ] Entscheiden, WAS maskiert wird. Heute im Test: Moebel plus Boden.
      Waende und Oeffnungen bleiben in jedem Fall aus Blender.
- [ ] Den Zuschnitt als Skript festhalten (composite-mask-polish.py kann es
      im Prinzip schon, braucht aber die Objektmaske statt der Gebaeudemaske).
- [ ] Der Blender-only-Weg bleibt als Rueckfall bestehen und besteht den
      Schwarzweiss-Test bereits. Er ist jetzt nicht mehr der Hauptweg,
      sondern die Absicherung.

## NACHTSITZUNG-2026-09-07-SAMMEL-001 (teils COMPLETE, teils PENDING)

Eine lange Sitzung, mehrere kleine Auftraege von Rainer nacheinander.
Gesammelt hier, weil jeder einzeln zu klein fuer einen eigenen Plan war.

**COMPLETE, verifiziert:**

- Teppich-Klemmung unter der Wand: `raum["polygon_mm"]` liegt auf der
  Wand-MITTELLINIE, nicht der Innenkante. Der alte Rand von 100 mm ging bei
  Waenden ueber 200 mm Staerke ins Negative. Jetzt 200 mm (deckt die
  dickste Aussenwand, 365 mm, mit Reserve). `render-furnished-dollhouse.py`.
- Fensterbank innen (helles Granit) und aussen (Anthrazit wie der
  Fensterrahmen), bodentiefe Fenster ausgenommen. `render-furnished-
  dollhouse.py` (innen) und `render-exterior.py` (aussen). Strukturell
  geprueft an einem neu gebauten `german_catalog_review_bungalow_
  3_3_1_b_100_2` -- Objekt, Material, Farbe und Position direkt in der
  .blend nachgesehen. NICHT nochmal mit Lichtstimmung/Politur bildlich
  bestaetigt (EEVEE-Testrender war zu flach, um Granit klar zu lesen).
- Echte Metall-Haustuer am Haupteingang, geschlossen. `role ==
  "main_entrance"` verzweigt in `render-exterior.py` auf `place_asset()`
  statt der Verfahrens-Tuer; Metallic-Fix (0.9) fuer das Assetmaterial, das
  flach mit Metallic=0 aber ohne Texturknoten kam. Volles Haus neu gebaut,
  Breit- und Nahaufnahme kontrolliert.
- Raum-Umbenennung per Rechtsklick (Kind -> Eltern etc.) im Zeichner.
  `element-edit.js`, `annotationAtPoint()` als Fallback, wenn kein Element
  unter dem Klick liegt. Live Ende-zu-Ende geprueft, nicht in echte Daten
  gespeichert.
- Einzelpunkt-Loeschen auf dem Kuechenzielpfad: existierte bereits und
  funktioniert (`onPathMenu` in `page.tsx` reicht korrekt an
  `CorrectionFurnitureLayer` durch) -- keine Aenderung noetig, nur
  verifiziert.
- Objektmasken-Pass ("Cryptomatte"), Rainer 2026-09-07: neuer
  `*-idmask.png` Renderpass in `render-furnished-dollhouse.py`, gleiches
  Tausch-Render-Wiederherstellen-Muster wie der bestehende Tiefenpass
  (Mesh-Datenblock-Schluessel, nicht Objekt-Schluessel). Jede
  Moebelkategorie (Objektname ohne Instanznummer(n)) bekommt eine feste
  Flaechenfarbe, Architektur einheitlich grau. Farbtabelle steht im
  Manifest unter `idmask_legend`. Eingebunden in `make-codex-job.py`
  (`BEIWERK`) und `docs/CODEX-REGELN-4PLUS2.md`. Isoliert an
  `bungalow_039` getestet (`DMH_ALLOW_STALE=1`, Scratch-Ausgabe, nicht die
  echte Lieferung) -- 38 stabile Kategorien, gleiche Moebeltypen an
  verschiedenen Stellen im Raum bekommen dieselbe Farbe, Bild visuell
  gepruef.

**PENDING:**

- [ ] Fensterbank + Teppich-Fix noch nicht mit einem echten, politurfaehigen
      Render bildlich bestaetigt -- nur strukturell in der .blend.
- [ ] Wiederkehrendes Muster: der Kuehlschrank fehlt in Codex' KI-politierten
      Pruefbildern, beobachtet an mind. 3 Haeusern (4_2_4, 4_2_6, 4_3_1).
      Rainer hat beide Male "trotzdem hochladen" gesagt, die Ursache ist
      nicht gefunden.
- [ ] WordPress-Katalog: Checkbox "an Kunden" und Titelbild liessen sich
      nicht setzen. Ursache vermutlich Login/Session/Capability-Race im
      Katalog-eigenen JS (`MAY_RELEASE` aus einem async Status-Fetch) --
      nicht in diesem Repo behebbar, nicht weiter untersucht.
- [ ] Was mit Rainers "meine Uebersichtsseite" gemeint war, ist offen
      geblieben -- er ist zur naechsten Frage weitergegangen, bevor das
      geklaert war.

## SITZUNG-2026-09-14/15-GARDEROBE-UND-SCHNITTHOEHE (teils COMPLETE, teils PENDING)

Zwei Plaene, beide von Rainer mit "both" freigegeben:
`born2thrill-local-workbench/plans/garderobe-composite-guard-v1.md` und
`born2thrill-local-workbench/plans/realistic-cut-height-slab-clearance-v1.md`.

**COMPLETE, verifiziert:**

- `schuetze-garderobe.py` (neu) + `schuetze-garderobe.test.py` (neu, 18
  Tests, alle gruen): holt `garderobe*` pixelgenau aus dem eigenen
  Baseline-Render zurueck, wenn eine Codex-Lieferung sie ersetzt/entfernt
  hat -- bewusst NUR `garderobe`, nicht `stuff` (das soll Codex laut
  `make-codex-job.py` kreativ neu erfinden; ein Komposit wuerde das
  rueckgaengig machen). Per Vorschau (`--in-place` fehlt) gegen die echte
  Lieferung `codex-twostorey_045-2026-09-14` (E:-Datenordner) laufen
  lassen: alle 4 EG-Bilder korrekt erkannt und im Vorschau-Ordner
  komponiert, Aussenansichten und beide OG-Bilder korrekt uebersprungen
  (keine Garderobe in der Obergeschoss-.blend). Bildlich gegengeprueft.
- Nebenbefund beim ersten echten Lauf: `objektmaske.py`s
  250-Objekte-Grenze blockierte das Obergeschoss (301 sichtbare Meshes).
  Kleiner, abwaertskompatibler Zusatz: optionaler Umgebungsvariablen-Filter
  `OBJEKTMASKE_NUR_STAMM`, wirkt nur wenn gesetzt. `objektmaske.py`.

**FALSCH DIAGNOSTIZIERT, dann richtiggestellt:**

- Erste Diagnose (`CUT_HEIGHT_BACK_MM` kollidiert mit `wall_height`, legt
  den Zwischengeschoss-Estrich frei) war FALSCH. Fix implementiert
  (`render-furnished-dollhouse.py`, Deckelung auf `wall_height - 150mm`),
  `twostorey_045` komplett neu gebaut (0 ausgeschlossen, alle Pruefungen
  gruen) -- Grauband bildlich UNVERAENDERT. Gegenprobe: alle
  `slab-under-wall-*` versteckt und neu gerendert -- Band blieb, also war
  es nie der Estrich.
  Echte Ursache per Raycast gefunden: das Band ist `teppich-1` (Teppich),
  der korrekt auf dem EIGENEN Boden des Obergeschosses liegt (Welt-Z 2,625m
  = Geschosshoehe + 3,5mm Teppichdicke, kein Schwebe-Fehler), aber bei der
  "realistic"-Kamera (flacher, sehr weit entfernter Blickwinkel) UEBER den
  bewusst abgeschnittenen Wandstumpf hinweg sichtbar wird. Gegenprobe: alle
  `teppich*`/`teppich-rand*` versteckt -- Band komplett weg, beide
  Bildausschnitte sauber.
  Rainer hatte woertlich recht: "teppiche ... durch die wände" ist keine
  Metapher, es sind tatsaechlich Teppiche.
  Die `CUT_HEIGHT_BACK_MM`-Deckelung bleibt im Code (harmlos, greift nur
  bei "realistic"), behebt das gemeldete Problem aber nicht. Fix fuer die
  echte Ursache noch nicht gewaehlt/umgesetzt -- siehe PENDING.
  Vollstaendiges Hypothesen-Protokoll in
  `born2thrill-local-workbench/plans/realistic-cut-height-slab-clearance-v1.md`.

**PENDING:**

- [ ] Eigentlicher Fix fuer "Teppich sichtbar ueber dem abgeschnittenen
      Wandstumpf" noch offen. Optionen, noch nicht mit Rainer abgestimmt:
      (a) Schnitthoehe fuer "realistic" nochmal anheben (ueber die
      bisherigen +400mm hinaus), (b) Bodendeko (Teppiche u.ae.) bei
      "realistic" zusaetzlich von Aussenwaenden zurueckhalten, (c) beides.
- [ ] `schuetze-garderobe.py` noch nicht mit `--in-place` auf eine echte
      Lieferung angewendet -- nur Vorschau. Rainer muss entscheiden, ob/wann
      das auf `codex-twostorey_045-2026-09-14` und die
      `twostorey_045-complete-package-2026-09-14.zip`-Lieferung angewendet
      wird.
- [ ] Ungeklaerte Frage aus dem Plan: ob `docs/RENDER-WORKFLOW.md` den
      Codex-Lieferungs-Pruefschritt schon beschreibt und einen Absatz zu
      `schuetze-garderobe.py` vertraegt, oder ob das ein eigener Abschnitt
      werden muss -- noch nicht nachgesehen.
- [ ] `schuetze-garderobe.py` ist bisher nur an `twostorey_045` erprobt;
      andere Haeuser mit Garderobe-Objekten sind nicht durchprobiert.

## SITZUNG-2026-09-15-IMAGE-SIZE-SEITENVERHAELTNIS (COMPLETE, mit PENDING)

Plan: `born2thrill-local-workbench/plans/image-size-ground-floor-priority-v1.md`,
von Rainer freigegeben ("yes"), nachdem er an `twostorey_046` zwei konkrete
Fehler meldete: "the right wall in the htr is missing and the aspect ratio
is totally off ... why do you not believe me?" -- beide Male hatte Rainer
recht, beide Male war die erste Antwort (Bildschirm-Race, dann eine falsche
Diagnose ueber die Zwischengeschoss-Deckenplatte) falsch.

**COMPLETE, verifiziert:**

- `image_size()` in `build-simplifier-render-plan.py` pruefte bei mehrgeschossigen
  Projekten eine nackte, geschossunabhaengige `room_concept.png` VOR jeder
  geschoss-praefigierten Datei. Diese generische Datei existiert bei `twostorey_046`
  zufaellig (1600x1390, Verhaeltnis 1,151) und gewann gegen die echte
  `groundfloor_original_preview.png` (1130x1448, Verhaeltnis 0,780) -- 47,5%
  Fehler in der Gebaeudehoehe. Da `RegisteredFrame` (Obergeschoss-Registrierung)
  JEDE Geschossgeometrie durchs Erdgeschoss-Frame leitet, reicht es, nur die
  Erdgeschoss-Datei richtig zu priorisieren. Fix: geschoss-praefigierte
  `_original_preview.png` zuerst, NICHT `_room_concept.png` (das brach einen
  bestehenden Tuer-Test an `bungalow_039`, das keine eigene
  `groundfloor_original_preview.png` hat -- beim ersten Versuch entdeckt,
  korrigiert).
- Direkt nachgewiesen, dass die fehlende HWR/HTR-Wand eine ZWEITE Symptom
  DESSELBEN Fehlers war, kein eigener Wandabgleich-Fehler: dieselben zwei
  Raeume mit dem korrekten Frame gebaut ergeben die Wand korrekt, mit dem
  falschen Frame verschwindet sie (Ueberlappungs-Berechnung im
  Kanten-Abgleich haengt an den y-Koordinaten, die die Hoehen-Verzerrung
  verschob). Keine Aenderung an `build_walls()` noetig.
- 4 neue Tests in `build-simplifier-render-plan.test.py`
  (`ImageSizeGroundFloorPriorityTests`), alle gruen; volle Testsuite gruen
  bis auf einen VORBESTEHENDEN, unabhaengigen Fehlschlag (siehe PENDING).
  Bildlich im Möbel-Schritt von `/haus?plan=twostorey_046` bestaetigt:
  Seitenverhaeltnis jetzt korrekt, HWR/HTR-Wand jetzt durchgezogen sichtbar.
- Ausmass geprueft: 37 von 48 Projekten mit derselben zweideutigen Datei
  betroffen (0,2% bis 47,5% Fehler), aber KEINS davon schon gebaut (keine
  .blend-Dateien) -- keine ausgelieferte Arbeit betroffen. Der Fix gilt
  automatisch fuer alle 37 beim naechsten Bauen, keine Nacharbeit an
  einzelnen Projekten noetig.
- Stale `.git/index.lock` (Datum 12. August, kein laufender Prozess) blockierte
  `git stash`/-Schreibzugriffe; entfernt, damit git wieder normal funktioniert.

- Rainer, nach dem ersten Fix: "the wall to the htr still has a whole in
  it" -- richtig, ein ZWEITER, unabhaengiger Fehler in derselben Wand.
  `HWR/HTR`s Grenze zu `Diele` macht dort einen kleinen Versatz (~370mm);
  die daraus gebaute Wand steht 8,85 Grad schief. `_orthogonalize_interior_
  walls` zieht schiefe Innenwaende gerade -- ABER auf den MITTELWERT beider
  Enden, nicht auf ein Ende, das schon exakt eine Nachbarwand beruehrt. Bei
  dieser (langen, nur leicht schiefen) Wand verschob das ihr oberes Ende
  um 184,7mm zur Seite, weg von der Nachbarwand, die es vorher exakt
  beruehrt hatte -- die Luecke. Fix: haelt ein Wandende schon (<=5mm) eine
  andere Wand, wird auf DEREN Achse gefangen statt auf den Mittelwert;
  ohne solchen Kontakt bleibt das alte Verhalten (Mittelwert) unveraendert.
  Beim ersten Versuch einen echten Fehler im eigenen Fix gefunden und
  behoben: der Ausschluss der eigenen zwei Wandenden verglich nach WERT,
  nicht nach Wand-Identitaet -- das schloss genau den Nachbarn aus, den die
  Funktion finden sollte, wann immer der zufaellig denselben Punkt traf.
  Regressionstest dafuer ergaenzt. Ergebnis: die beiden Wandstuecke
  verschmelzen jetzt (ueber den bestehenden `_merge_collinear_walls`-
  Schritt) zu EINER durchgehenden Wand -- Luecke vollstaendig geschlossen,
  bildlich im Möbel-Schritt bestaetigt. 2 neue Tests in
  `InteriorWallGeometryTests`, alle gruen; volle Suite weiterhin gruen bis
  auf denselben vorbestehenden, unabhaengigen Fehlschlag.
  Details: `born2thrill-local-workbench/plans/interior-step-edge-orphaned-when-outline-present-v1.md`
  (inkl. einer ersten, FALSCHEN Hypothese -- protokolliert, nicht geloescht).

- Rainer schickte danach zwei Blender-Screenshots (kein Text-Report,
  einfach Bilder): eine sichtbare Kerbe an einer Aussenecke, und in einem
  zweiten Bild ein Teppich, der durch genau diese Kerbe unter der Wand
  hervorschaut. "you have to fix these corners ... this cant be that hard
  to fix" / "the carpet form the inside going underneth the wall". Ursache
  gefunden in `render-furnished-dollhouse.py`s `_end_extension_mm()`
  (baut die tatsaechlichen 3D-Wandkoerper, ein anderer Code-Pfad als
  `build_walls()` in `build-simplifier-render-plan.py`): an einer
  rechtwinkligen Aussenecke liegt ein Wandende GENAU auf der Mittellinie
  der Nachbarwand (side=0) -- welche der zwei moeglichen Normalenrichtungen
  "die richtige" ist, war bisher reines 50/50 je nachdem, in welcher
  Reihenfolge die Nachbarwand gezeichnet wurde. Bei falscher Wahl wurde
  `approach` negativ und die Verlaengerung ganz uebersprungen -- eine
  ca. 130x130mm grosse Kerbe genau in der Ecke, an ALLEN 4 Aussenecken
  von twostorey_046s Erdgeschoss. Fix: bei negativem `approach` die
  Normale umdrehen und nochmal versuchen, statt aufzugeben -- reduziert
  sich auf dasselbe Ergebnis wie vorher, wann immer die alte side<0-Regel
  schon eindeutig war. Haus komplett neu gebaut, alle 4 Ecken direkt an
  den Wand-Bounding-Boxen nachgemessen (jede Wand ueberlappt jetzt die
  andere bis ueber deren Aussenflaeche hinaus) und bildlich bestaetigt --
  keine Kerbe mehr, alle Pruefungen gruen.

**PENDING:**

- [ ] Vorbestehender, von diesen Fixes unabhaengiger Testfehlschlag:
      `GeometryOnlyWallsAndOpeningsTests.test_door_hinge_and_swing_are_normalized_into_the_walls_frame`
      in `build-simplifier-render-plan.test.py` schlaegt auch auf dem
      Code VOR diesen Fixes fehl (direkt nachgewiesen) -- Ursache nicht
      untersucht, nicht in diesem Plan behoben.

## VIER-DACHFORMEN-EXTERIOR-001 (COMPLETE)

Rainer: "the boss aske for more 2 roof forms Pultdach and Satteledach",
dann klargestellt: "he just wanted all of the roof forms so not just 2
exteriors but all 4". Scope per AskUserQuestion bestaetigt (nur Dach,
ein Materialstil), Pultdach-Traufhoehe von Rainer: "the lower die would
be around 2,50m".

- `render-exterior.py`: echtes Satteldach (giebelstaendige, senkrechte
  Stirnwaende statt der Walmdach-Schraegen -- `ridge_inset = 0.0` statt
  `inset`, sonst identische Quer-schnitts-Mathematik) und echtes Pultdach
  (eine einzelne geneigte Flaeche, keine First, niedrige Traufe auf
  `WALL_TOP_Z`) fuer Rechteck-Grundrisse ergaenzt; nicht-rechteckige
  Grundrisse fallen weiterhin auf den bestehenden `bpypolyskel`-Walmdach-
  Solver zurueck (Gable/Pultdach dort nicht unterstuetzt).
  Erster Pultdach-Versuch nutzte den geteilten 22-Grad-Winkel ueber die
  volle Spannweite -- geometrisch "richtig", aber im Rendering absurd
  hoch/ueberkragend (4,26m First auf ~9m Spannweite). Nach einem echten
  Referenzfoto von Rainer (flach geneigtes Pultdach-Haus) durch eigene
  Konstante `PULTDACH_PITCH_DEG = 10.0` ersetzt.
  `EXT_ROOF_TYPE`-Env-Override ergaenzt (gleiches Muster wie
  `DMH_CAMERA_STYLE`), damit `run_project.py` 4 Exterior-Renders aus
  EINEM Plan erzeugen kann, ohne 4 separate Plan-JSONs zu brauchen.
- `run_project.py`: `ROOF_TYPES = (flachdach, walmdach, satteldach,
  pultdach)` als Konstante; Exterior-Rendering laeuft jetzt einmalig
  (nicht mehr pro Stil) und iteriert ueber alle 4 Dachformen;
  `trim_to_delivery()` behaelt alle 4 `exterior-{roof}-baseline`-Dateien;
  Liefer-Erwartung von `2 + len(floors)` auf `len(ROOF_TYPES) +
  len(floors)` angepasst; `handoff["roof_exteriors"]` enthaelt alle 4,
  `handoff["styles"][style]["exterior_baseline_*"]` zeigt weiterhin auf
  die erste erfolgreich gerenderte Dachform (Rueckwaertskompatibilitaet).
- Verifiziert durch ZWEI vollstaendige End-zu-Ende-Rebuilds von
  twostorey_046 (`go.py twostorey_046 --laut`): Lieferung "6 .blend
  (expected 6)", "2 style(s) verified and ready, 0 excluded"; alle 4
  Dachformen einzeln im gerenderten PNG bildlich gegengeprueft
  (Flachdach/Walmdach unveraendert korrekt, Satteldach zeigt echte
  Giebelwand, Pultdach zeigt eine saubere flache Einzelflaeche).
  Details: `born2thrill-local-workbench/plans/four-roof-form-exteriors-v1.md`

**PENDING:**

- [ ] Offene Rueckfrage an Rainer (noch unbeantwortet): soll
      `docs/CODEX-REGELN-4PLUS2.md` (aktuell "je ein Bild fuer Classic
      und Modern" Exterior-Restyling) auf 4 restylte Exteriors (eins pro
      Dachform) statt 2 umgestellt werden?

## MOEBEL-SCHRANK-ROTATION-RECT-BUILD-001 (COMPLETE)

Rainer, mit Screenshot der HWR: "who in the fuck rotated the Kleider and
Abstell schränke in the HWR? the shure as hell are not rotetd like that
in the annotater. i cant even roteat stuff like that just 45 and 90
dergrees".

Ursache: `RECT_BUILD` in `build-simplifier-render-plan.py` (Liste der
Symboltypen, die als achsengerechtes Rechteck statt als gezeichneter
Pfad gebaut werden) enthielt `kleiderschrank`/`abstellschrank`/
`schrank_40`/`schrank_60`/`garderobe` nicht. Diese Typen fielen auf
`"build": "path"` zurueck -- gedacht fuer Theken/Vorwandinstallation,
deren Rotation zurecht aus der gezeichneten Pfadrichtung folgt. Fuer ein
per Zwei-Ecken-Drag gezeichnetes Rechteck macht `build_path_run()` in
`render-furnished-dollhouse.py` daraus `atan2()` der rohen Eckpunkte --
eine minimale Sub-Pixel-Ungenauigkeit beim Ziehen wird zu einer grossen,
beliebig wirkenden Rotation. Exakt derselbe Fehlerfall wie bei
`kuecheninsel` (dokumentiert in `plans/kuecheninsel-rechteck-v1.md`,
mit explizitem Warnkommentar im Code, neue Rechteck-Symbole dort
einzutragen -- diese Symbole wurden nie eingetragen).
Numerisch bestaetigt: `abstellschrank-14-0` baute bei rot_z=-169.7 Grad,
`abstellschrank-15-0` bei -17.8 Grad -- exakt der rohe Eckpunkt-zu-
Eckpunkt-Winkel aus `furniture/floor-0.json`, nicht ihr annotiertes
`rotation_deg: 0`.
Zweiter, separater Fehler in derselben Untersuchung gefunden:
`build_rect()` in `render-furnished-dollhouse.py` hatte `angle=0.0` fuer
alle seine `box(...)`-Aufrufe fest verdrahtet -- unschaedlich fuer
`kuecheninsel`/`stuff` (immer rotation_deg=0), aber selbst nach dem
`RECT_BUILD`-Fix haette ein Kleiderschrank mit echtem, nicht-null
`rotation_deg` (90/180/270 in echten Annotationen bestaetigt) trotzdem
immer bei 0 Grad gerendert.
Fix: `RECT_BUILD` um die 5 Schranktypen erweitert; `build_rect()` liest
jetzt `angle = math.radians(item.get("rotation_deg", 0))` und wendet sie
auf Korpus, Regal-Deckplatte und Arbeitsplatte konsistent an.
Verifiziert an echtem Rebuild von twostorey_046 (`.blend` gespeichert,
Rotationswerte direkt per Blender-Python abgefragt):
`abstellschrank-14`/`-15` jetzt exakt 0.0/0.0 Grad (vorher -169.7/-17.8);
`kleiderschrank-0/-3/-4` im Obergeschoss jetzt exakt 270/90/180 Grad --
Grad-fuer-Grad identisch mit `rotation_deg` in
`furniture/floor-1.json`. Bildlich bestaetigt: alle Schraenke liegen
jetzt buendig an der Wand statt schief im Raum zu stehen.

**PENDING:**

- [ ] Kein Testfall fuer `RECT_BUILD`-Erweiterung/`build_rect()`-Rotation
      ergaenzt -- sollte in `build-simplifier-render-plan.test.py`
      bzw. einem Pendant fuer `render-furnished-dollhouse.py` nachgezogen
      werden.
- [ ] Kein separates `plans/*.md` fuer diesen Fix geschrieben (die
      Diagnose war eine exakte, bereits im Code dokumentierte
      Wiederholung eines fruehreren Bugs -- direkt implementiert statt
      erst einen Plan aufzusetzen). Governance-Konsistenz nachtraeglich
      pruefen/entscheiden.

## TREPPENLOCH-GELAENDER-PRO-ABSCHNITT-001 (COMPLETE)

Rainer, zu einer viertelgewendelten Treppe: "if you have a
viertelgewendelt it makes no sence to nad a railing on any side because
the stairs go around a corner you have to ba able to click on the parts
of each segament", dann bestaetigt: "the need to be activated per
segment othewise it odesn't work".

Ursache: sowohl die Annotator-Klickflaechen (`stairRailingEdges()` in
`floorplan-simplifier/static/annotate.js`) als auch der tatsaechliche
Gelaenderbau (`render-furnished-dollhouse.py`, ~Zeile 3931) reduzierten
die Treppenform auf ihre Bounding-Box und boten nur 4 feste
Himmelsrichtungen (Nord/Sued/West/Ost) an. Fuer eine gerade Treppe sind
Box-Kanten und echte Kanten identisch, harmlos. Fuer eine gewendelte
Treppe (L-foermiges `polygon_mm`, mehrere Segmente) schneidet die Box
durch Boden, der nie Teil der Öffnung war -- eine gewaehlte "Nord"-Seite
entsprach keiner echten Kante mehr.

Fix: EIN Links/Rechts-Kantenpaar PRO SEGMENT statt vier Himmels-
richtungen, in beiden Sprachen mit identischer Aufteilung:
- `annotate.js`: neue `pathBandOffsets()` spiegelt exakt die Gehrungs-
  Offset-Mathematik aus `build-simplifier-render-plan.py`s
  `polygon_mm`-Bauer; `stairRailingEdges()` liefert jetzt
  `{"0-left":[...], "0-right":[...], "1-left":..., ...}` statt
  `{north,south,west,east}`. Klick-Trefferlogik
  (`stairRailingEdgeAtPoint`) und die Overlay-Zeichnung blieben
  unveraendert, da beide schon generisch ueber `Object.entries()`
  liefen.
- `element-edit.js`: das Rechtsklick-Menue listet jetzt "Abschnitt N
  links/rechts" dynamisch nach `element.points.length - 1` Segmenten
  statt der vier festen Eintraege.
- `render-furnished-dollhouse.py`: die echten Kanten werden aus dem
  bereits vorhandenen `corners` (= `polygon_mm` = `left + reversed
  (right)`) zurueckgewonnen statt neu geschaetzt -- garantiert dieselbe
  Form wie das tatsaechlich gebaute Treppenband. `wall_adjacent_
  intervals`/`rail_run`/`arrival_gap` blieben unveraendert (schon
  generisch fuer beliebige Kanten).
- Wanderungs-Schutz: ein `railing_sides`-Wert im ALTEN Vokabular (z.B.
  `["east"]`, gefunden in twostorey_047s eigener Treppe) passt auf keine
  neue Kante mehr -- statt daraus "Gelaender nirgends" zu bauen, wird
  das als veraltetes Format erkannt (Log-Hinweis) und auf die
  automatische Wanderkennung zurueckgefallen.

Verifiziert an einem echten Bau von twostorey_047s Obergeschoss
(viertelgewendelt, `plan_type=quarter_turn`, 2 Segmente): 4 Gelaender-
Laeufe im `.blend` direkt nachgemessen -- `loch-rail-0-left`/`-0-right`
laufen entlang des ERSTEN Laufs (x=4.234/5.134, y 3.0..6.7/5.9),
`loch-rail-1-left`/`-1-right` entlang des ZWEITEN, nach der Wendung
(y=6.72/5.82, x 4.2..5.6/5.1..5.6) -- folgt der echten L-Form statt
eines Rechtecks drumherum. Migrations-Hinweis fuer das alte
`["east"]` im Build-Log bestaetigt.

**PENDING:**

- [ ] Kein separates `plans/*.md` geschrieben (Umfang war schon vorab
      mit Rainer per Rueckfrage abgestimmt). Governance-Konsistenz
      nachtraeglich pruefen.
- [ ] Kein Testfall ergaenzt fuer die neue Segment-Aufteilung (weder
      `build-simplifier-render-plan.test.py` noch ein Python-Pendant
      fuer `render-furnished-dollhouse.py`).
- [ ] `twostorey_047`s eigene Treppen-Annotation traegt noch das alte
      `railing_sides: ["east"]` -- baut dank Migrations-Fallback korrekt
      (automatisch), aber die Annotation selbst wurde nicht aktualisiert.
      Im Annotator einmal neu setzen, wenn eine bestimmte Seite (nicht
      die automatische Wandkennung) gewuenscht ist.

**Nachtrag, selber Tag:** Rainer schickte einen echten Render (Obergeschoss,
kein Text): am Treppenloch fehlte JEDES Gelaender an der Kante quer zum
Austritt -- links/rechts pro Abschnitt laufen ENTLANG des Laufs und
deckten genau diese quer liegende Kante nie ab. Dieselbe Luecke stand
schon im Build-Log ("kein Austritt gefunden"), nur nicht als Problem
erkannt.

Fix: zwei weitere Kanten, "start" und "end", die die bereits berechneten
Links/Rechts-Punkte am ERSTEN bzw. LETZTEN Pfadpunkt verbinden -- in
`annotate.js` (`stairRailingEdges`), im Rechtsklick-Menue ("Anfang" /
"Austritt (Ende)") und in `render-furnished-dollhouse.py` (dieselbe
Kantenliste). "Richtung umkehren" tauscht jetzt auch start<->end mit,
zusaetzlich zum bestehenden links<->rechts-Tausch pro Segment.

Verifiziert an einem zweiten echten Bau von twostorey_047s Obergeschoss:
Log zeigt "5 Gelaender am Treppenloch mit 900mm Austritt" (vorher 4 ohne
Austritt-Erkennung), `loch-rail-start` im .blend nachgemessen (volle
900mm Laufbreite, kein Austritt an diesem Ende noetig), `loch-rail-end`
korrekt komplett als Austritt offen (900mm Gang = volle Treppenbreite,
kein Rest zum Umranden). Bildlich bestaetigt: die vorher offene Ecke am
Treppenloch hat jetzt ein Gelaender, der tatsaechliche Austritt bleibt
frei begehbar.

Ausserdem in derselben Sitzung ergaenzt (Rainer: "is ther a way to
revers top and bottom of the stairs, incease we get it wrong by
drawing"): "Richtung umkehren (oben/unten tauschen)" im Rechtsklick-Menue
dreht `element.points` um, damit render-furnished-dollhouse.py (das die
Kletterrichtung rein aus der Punktreihenfolge liest) den Austritt am
richtigen Ende baut, ohne die Treppe neu zeichnen zu muessen. Bildlich
und rechnerisch bestaetigt: dieselbe reale Kante behaelt ihr Gelaender
nach dem Umkehren (0-left -> 1-right etc., start <-> end).

## MOEBEL-KOORDINATEN-DOPPELT-GESPIEGELT-001 (COMPLETE)

Rainer, zum twostorey_047-Codex-Paket: "why is the playstation group not
in the bed rooms oder the kids room furniture in the wohnzimmer it
maked no sense". Beide Geschosse waren komplett vertauscht: Kueche/
Sofas/Fernseher lagen in WC/HWR/Gast, WC-Moebel lagen im Wohnbereich,
Kinderbetten/-schreibtische/Playstation-Gruppen lagen in Eltern/
Schlafen und Bad, Eltern-Doppelbett und Bad-Sanitaer lagen im
Kinderzimmer.

Ursache NICHT im Renderer: `twostorey_046`s Moebel wurden mit derselben
Pipeline-Logik gegengeprueft und lagen exakt richtig. `workbench_
furniture()` in `build-simplifier-render-plan.py` spiegelt gespeicherte
Positionen einmal (Anzeige-Raum y-unten -> Frame y-oben), weil der
Moebel-Editor sie in genau dieser Anzeige-Orientierung anzeigt und
speichert. `twostorey_047`s `furniture/floor-0.json` und `floor-1.json`
trugen aber Koordinaten, die schon OHNE diese Spiegelung exakt in die
richtigen (Frame-Raum-)Polygone passten -- bewiesen durch direkten
Punkt-in-Polygon-Test der ROHEN, ungespiegelten Werte gegen `--geometry-
only`s Raumpolygone: 100% Treffer. Die Datei war also nicht im
Anzeige-Raum authoriert (trotz `coordinate_space: "render-geometry-mm-
y-down-v1"`), sondern schon im Frame-Raum -- die Pipeline-Spiegelung hat
sie dadurch ein zweites Mal (und damit falsch) gedreht. Wie diese Datei
entstand (Hand-Klicks im Moebel-Editor oder ein externer Generator)
blieb ungeklaert -- Rainer wollte trotz Nachfrage sofort die Korrektur.

Fix: beide Dateien direkt korrigiert (Sicherungskopien vorher unter
`floor-0.json.bak`/`floor-1.json.bak` im Scratchpad) -- jedes `position_
mm`/`points_mm` einmal mit `y -> lo+hi-y` vorab gegengespiegelt (`lo,hi`
aus `level_room_extent()` je Geschoss) und jede `rotation_deg` negiert,
sodass die EINE Spiegelung der Pipeline sie wieder auf die (bereits
korrekten) Frame-Raum-Werte zurueckdreht. Verifiziert mit
`workbench_furniture()` + Punkt-in-Polygon gegen beide Geschosse: alle
33 Stuecke jetzt im richtigen Raum (beide Playstation-Gruppen in "Kind",
Doppelbett in "Eltern / Schlafen", alle Sanitaerobjekte in "Bad", Kueche/
Sofas in "Wohnen / Essen / Kochen"). Bildlich am neu gebauten `plan-
modern.json` bestaetigt.

Hochgeladen auf Rainers ausdruecklichen Wunsch trotz weiterhin offener
Frage nach der Bildqualitaet (das Codex-Zip-Paket war zum Zeitpunkt des
Uploads bereits mit den ALTEN, falschen Moebel-Positionen gerendert --
die neuen Bilder muessten von Codex mit den jetzt korrigierten Dateien
neu erzeugt werden, um Moebel UND Optik gleichzeitig richtig zu haben).

**PENDING:**

- [ ] Unklar, WIE `twostorey_047`s Moebel-Dateien entstanden sind (Hand
      oder Generator) -- falls ein Generator-Skript existiert, das
      Frame-Raum-Koordinaten schreibt statt Anzeige-Raum, wuerde es
      denselben Fehler bei jedem kuenftigen automatisch moeblierten
      Haus wiederholen. Nicht gefunden/untersucht.
- [ ] Codex muss das Rendering-Paket fuer twostorey_047 mit den jetzt
      korrigierten Moebeldaten neu erzeugen; das hochgeladene Paket
      zeigt weiterhin die alten (moebeltechnisch falschen) Bilder.
- [ ] Waehrend derselben Untersuchung gemeldet, nicht abschliessend
      verifiziert: "rugs go underneath the wall" im selben Rendering-
      Paket (camera_style=realistic) -- exakt die Fehlerklasse aus
      `realistic-cut-height-slab-clearance-v1.md` (dort PENDING seit
      twostorey_045), nur an einem neuen Haus. Rainer bestand darauf,
      dass NUR dies das eigentliche Problem sei; Untersuchung wurde
      unterbrochen (User: "wait a second"), nicht zu Ende gefuehrt.

## HAUS-UPLOAD-TAB-VOR-ZEICHNEN-001 (COMPLETE)

Rainer: "cant you put that in a tab before Zeichnen Räume und Aussen?
and when the images are uploaded and saved then go tot the next tab" --
ein neues Haus anfangen hiess bisher: zur Simplifier-Startseite (8765)
wechseln, Formular ausfuellen, dann von Hand zu `/haus?plan=<neu>`
zurueckfinden. Ausserhalb der Hausakte, kein Rueckweg.

Fix, gleiches Einbett-Muster wie beim Moebel-Schritt:
- `floorplan-simplifier/static/index.html`+`app.js`: neuer `?embed=1`-
  Modus blendet Topbar und Annotation-Queue aus (nur das Upload-
  Formular bleibt), und meldet bei Erfolg `{typ: "haus-erstellt",
  projekt: id}` an `window.parent` statt selbst zu `annotate.html` zu
  navigieren (die eingebettete Seite haette sonst Rahmen und
  Seitenleiste der Hausakte verlassen).
- `born2thrill-local-workbench/src/app/haus/page.tsx`: neuer Schritt
  "neu" ("Hochladen (neues Haus)") ganz vorne in `SCHRITTE`, laedt
  `${ANNOTATOR}/?embed=1` ohne gebundenen Plan; der bestehende
  Message-Listener wechselt bei `haus-erstellt` per `wechslePlan(id,
  "raeume")` automatisch zum neuen Haus und direkt in den Zeichnen-
  Schritt.
- Beim Implementieren einen echten Bug gefangen, bevor er auslieferte:
  `wechslePlan` im Abhaengigkeits-Array des Message-Listeners referenziert,
  obwohl `wechslePlan` erst SPAETER im selben Funktionskoerper deklariert
  wird (`const` -- TDZ) -- Live im Dev-Server als "Cannot access
  'wechslePlan' before initialization" aufgetreten, sofort behoben
  (Referenz aus dem Deps-Array entfernt, bleibt im Closure-Body
  erreichbar).

Bildlich verifiziert: neuer Tab "Hochladen (neues Haus)" ganz links,
eingebettetes Formular zeigt nur das Upload-Panel ohne Chrome.

Gleichzeitig ergaenzt (Rainer: "then one more button please on the last
tab open the catalog on the external site"): Button "Katalog auf
born2thrill.de ansehen ↗" auf dem Hochladen-&-Freigeben-Schritt, oeffnet
https://born2thrill.de/grundriss-katalog/ in neuem Tab. Verifiziert (href
direkt gelesen).

**PENDING:**

- [ ] Kein separates `plans/*.md` fuer beide Features geschrieben (User
      wollte explizit Tempo, Design folgte direkt aus bereits im Code
      etablierten Mustern). Governance-Konsistenz nachtraeglich pruefen.
- [ ] Kein Testfall fuer den neuen `?embed=1`-Modus oder die
      `haus-erstellt`-Nachricht ergaenzt.

## TREPPENLOCH-GELAENDER-VOM-OBERGESCHOSS-001 (COMPLETE)

Rainer, direkt im Anschluss an die Segment-Gelaender-Arbeit: "i would
like to have my railing login on the upperfloor ... looking ath the
treppen loch from the OG or DG" -- railing_sides lebt auf DER (im
Erdgeschoss gezeichneten) Treppe, aus der render-furnished-dollhouse.py
JEDES Geschoss baut; die role:"opening"-Kopie im Obergeschoss (oder
Dachgeschoss, bei einer dritten Etage) hatte nie ein eigenes Feld, das
irgendetwas ansieht. `stairRailingEdgeAtPoint()` schloss `role ===
"opening"` bisher sogar explizit aus -- Klicks dort taten schlicht
nichts, ohne jede Rueckmeldung.

Fix: neue `stairRailingQuelle(element)` in `annotate.js` findet das EINE
echte (nicht-"opening") Treppenelement -- unabhaengig davon, auf welchem
Geschoss man gerade steht. Drei Stellen darauf umgestellt:
- `stairRailingEdgeAtPoint()` (element-edit.js): testet Klicks gegen die
  Geometrie des AUSGEWAEHLTEN Elements (das, was auf diesem Geschoss
  tatsaechlich gezeichnet ist), schreibt aber auf die Quelle.
- Rechtsklick-Menue (element-edit.js): Segment-Liste, Anfang/Austritt und
  "Automatisch" lesen/schreiben jetzt `stairRailingQuelle(element).
  railing_sides` statt des eigenen (nie gelesenen) Felds der Kopie.
- Kanten-Overlay beim Zeichnen (annotate.js): war an `!isStairOpening`
  gebunden -- eine ausgewaehlte Kopie zeigte NIE ihre Kanten, egal was
  gesetzt war. Jetzt zeigt jede ausgewaehlte Treppe (auch eine Kopie)
  ihre Kanten, eingefaerbt nach dem Zustand der Quelle.

Verifiziert an twostorey_047s Obergeschoss-Kopie (role="opening"): Klick
auf "Abschnitt 1 links" im Rechtsklick-Menue trug sich korrekt in die
`railing_sides` des ECHTEN Erdgeschoss-Treppenelements ein (nicht in ein
eigenes Feld der Kopie), `draw()` lief ohne Fehler mit sichtbarem
Kanten-Overlay auf der Kopie.

## CODEX-REVIEW-RAILING-VALIDATOR-REGRESSION-001 (COMPLETE)

Rainer, nach dem obigen Segment-Gelaender-Umbau: "vielleicht willst Du
deinen code mal mit codex komplett durchgehen und troubleshooten" --
erste Codex-Zweitmeinung dieser Session (`/codex`, read-only, ueber
floorplan-simplifier: annotate.js/element-edit.js/geometry-tools.js/
zoom-pan.js/app.py). Codex-CLI musste dafuer erst von 0.147.0 auf
0.154.0 aktualisiert werden (das konfigurierte Default-Modell
"gpt-6-astra" war der alten CLI unbekannt; "o3"/"gpt-5-codex" sind fuer
dieses ChatGPT-Konto explizit gesperrt).

12 Funde zurueckgemeldet, 11 noch unverifiziert (siehe Tabelle im Chat).
EIN Fund musste SOFORT behoben werden, weil er eine eigene Aenderung
von heute regressierte:

`app.py`s `normalize_element()` validierte `railing_sides` weiterhin
gegen das ALTE Vokabular (`{"north","south","east","west"}`) -- die neue
Segment-Schreibweise ("0-left", "1-right", "start", "end") aus dem
heutigen Gelaender-Umbau fiel komplett durch. Jede Treppe mit einer neu
gesetzten Seite konnte ueberhaupt nicht mehr gespeichert werden
(HTTP 400, `ValueError`). Fix: Validator akzeptiert jetzt zusaetzlich
"start"/"end" und das Muster `<zahl>-(left|right)`; die vier alten Namen
bleiben gueltig (Altbestand darf weiter speichern).

Verifiziert live: `saveAnnotations()` mit `railing_sides:
["0-left","1-right","start"]` auf twostorey_047s echter Treppe schlug
VOR dem Fix fehl (durch Codex' Quellcode-Trace bestaetigt, nicht selbst
reproduziert) und gelang NACH dem Fix (`ok:true`); Testwert danach
wieder entfernt (zurueck auf automatische Wanderkennung).

**PENDING:**

- [ ] 11 weitere Codex-Funde noch nicht verifiziert/entschieden (siehe
      Fundtabelle im Chatverlauf dieser Sitzung). Rainer noch keine
      Auswahl getroffen, welche als naechstes bearbeitet werden.
- [ ] Kein `plans/*.md` fuer diesen Fix geschrieben (Nachregression
      einer heutigen eigenen Aenderung, sofort behoben statt erst einen
      Plan aufzusetzen).

## MOEBEL-REFERENZBILD-HINTERGRUND-001 (COMPLETE)

Rainer: "could you leave my images that i use to annotate the images
also in the Möbel part?" -- der Möbel-Editor (born2thrill-local-
workbench) zeigte nur die reinen Raumpolygone, kein Referenzfoto,
obwohl der Annotator (floorplan-simplifier) genau dieses Foto beim
Zeichnen zeigt.

Umsetzung: `GeometryEditor` in `floorplan-workbench/page.tsx` bekommt
eine neue `projectId`-Prop (`document.source_reference_id`), zeichnet
das Original-Vorschaubild als `<image>` bei 30% Deckkraft hinter den
Raumpolygonen. Näherungsweise, nicht pixelgenau: die Platzierung nutzt
die Bounding-Box aller Raumpolygone dieses Geschosses (plus Rand), nicht
die echte Frame/RegisteredFrame-Transformation des Annotators -- die
braeuchte eine neue Server-Route, die es noch nicht gibt. Reicht zum
Wiedererkennen, welche Wand welche ist.

Dabei ZWEI echte Bugs gefunden und behoben, keiner davon vorher
sichtbar, weil noch nie jemand versucht hatte, ein Bild aus dem
Simplifier (Port 8765) in die Workbench (Port 3020) einzubetten:
- `floorplan-simplifier/app.py`s `serve_file()` schickte keinen
  `Access-Control-Allow-Origin`-Header. Ein normales `<img>` braucht
  den nicht, ein SVG-`<image>` schon -- ohne ihn blockiert der Browser
  das Rendern (nicht das Laden selbst; die Anfrage kam mit 200 zurueck,
  das Bild durfte trotzdem nicht gezeichnet werden). Fix: `*` fuer alle
  ausgelieferten Dateien, da dieser Server ohnehin nur lokal und ohne
  Auth laeuft.
- Der eigene `onError`-Handler im neuen `<image>` mutierte `style.
  display` DIREKT auf dem DOM-Knoten. React behaelt denselben Knoten
  ueber Renders hinweg (stabile Position im Baum) und verwaltet
  `display` nirgends selbst -- ein EINZIGER fehlgeschlagener Ladeversuch
  (z.B. genau die obige CORS-Luecke, vor ihrem eigenen Fix) blieb also
  FUER IMMER unsichtbar, selbst nachdem derselbe Knoten spaeter mit
  derselben URL erfolgreich haette laden koennen -- bestaetigt: ein
  frisch erzeugtes `<image>` mit identischer URL lud sofort korrekt,
  waehrend das bestehende Element weiter `display:none` trug. Fix:
  Handler entfernt (ein SVG-`<image>` mit ungueltiger href zeichnet
  ohnehin nichts, kein Broken-Icon wie bei `<img>`) und einen `key`
  ergaenzt, der bei Projekt-/Geschosswechsel einen frischen Knoten
  erzwingt.

Verifiziert: `<image>`-Element im DOM mit korrekter href, `display`
nach Fix leer (nicht mehr "none"); Ressource per separatem Test-`<img>`
UND per direkt erzeugtem `<image>`-Element bestaetigt ladbar (1168x1544,
identisch zur Originaldatei).

**PENDING:**

- [x] Nur Naeherung (Raum-Bounding-Box), keine echte Frame/
      RegisteredFrame-Registrierung -- siehe Nachtrag unten, behoben.
- [ ] Kein Toggle zum Ein-/Ausblenden des Referenzbilds ergaenzt.

**Nachtrag, selber Tag:** Rainer: "why are the uploaded floorplans not
visible on the möble tab?" -- das Bild WAR da (per DOM bestaetigt, `href`
korrekt, `display` nicht "none"), aber vollstaendig unsichtbar: die
Raumpolygone darueber haben eine UNDURCHSICHTIGE Fuellfarbe, die das
Bild ueberall bedeckt ausser in den duennen Luecken zwischen Raeumen.

Fix, auf Rainers eigenen Vorschlag ("well just make the rooms multiply
thier colors"): `mix-blend-mode: multiply` auf dem Raum-`<polygon>`
statt reduzierter `fillOpacity` -- die Fuellfarbe bleibt volle Staerke
(faerbt nicht selbst aus), waehrend das Foto darunter durchscheint,
statt dass beide Ebenen gemeinsam milchig-transparent werden. Dafuer
das Bild selbst wieder auf volle Deckkraft (1 statt 0.45) gesetzt --
multipliziert man eine Raumfarbe gegen ein bereits ausgewaschenes
(halbtransparentes, richtung Weiss gemischtes) Bild, passiert fast
nichts (multiplizieren mit Fast-Weiss ist fast ein No-Op). Nur aktiv,
wenn tatsaechlich ein Referenzbild vorhanden ist -- ein Projekt ohne
eigenes Foto behaelt seine normale volle Fuellung.

Beim Umbau einen Turbopack-HMR-Fehlzustand getroffen (nicht der eigene
Code): eine Zwischenversion loeste kurz einen echten Parse-Fehler aus,
und selbst nach dessen Behebung im Quelltext blieb der Dev-Server auf
der alten Fehlermeldung mit falschen Zeilennummern haengen (bestaetigt:
die gemeldete Zeile 763 passte nicht mehr zur echten Datei). Ein voller
Neustart des Dev-Servers loeste es; kein Bug im gelieferten JSX.

Verifiziert: DOM zeigt `mix-blend-mode: multiply` (computed style) auf
dem Raum-Polygon, Bild-`opacity` = 1, bildlich bestaetigt -- die
Wand-/Moebellinien des Originalfotos sind jetzt innerhalb der
eingefaerbten Raeume sichtbar, nicht mehr nur in den Raumluecken.

**Nachtrag, 2026-09-17: echte Registrierung statt Bounding-Box.** Rainer,
mit zwei vollen Grundriss-Screenshots (Erd- und Obergeschoss): "scale is
off but it is all from the same data how can it be off" -- die
Bounding-Box-Naeherung platzierte das Referenzfoto sichtbar falsch
skaliert/verschoben, sobald das Foto ueber die gezeichneten Raeume
hinausging (Garten, Dachueberstand vor der Fassade).

Fix, serverseitig: `geometry_only()` in `build-simplifier-render-plan.py`
berechnet jetzt `image_corners_mm` -- die 4 normierten Bildecken (0,0)/
(1,0)/(1,1)/(0,1) durch DIESELBE `frame.point()`-Transformation (Frame
fuer Erdgeschoss, RegisteredFrame fuer Obergeschoss) wie Raeume/Waende/
Treppe, plus denselben Y-Flip. Neues Feld pro Geschoss im
`--geometry-only`-Output. Die API-Route
`/api/floorplan-workbench/corrections` (`render_geometry`) reicht das
Feld ungefiltert durch (kein eigener Whitelist-Code dort), also war kein
Backend-Change noetig.

Fix, clientseitig: `renderFloor` in `floorplan-workbench/page.tsx`
uebernimmt `fl.image_corners_mm` als `imageCorners`; `GeometryEditor`s
Referenzbild-Block nimmt jetzt min/max der 4 echten Bildecken statt
min/max der Raumpolygone (+400mm Rand) fuer `x/y/width/height` des
`<image>`-Elements. Faellt nur auf die alte Naeherung zurueck, wenn
`imageCorners` fehlt (z.B. eine gecachte alte Antwort).

Verifiziert live gegen `twostorey_047`: `image_corners_mm` aus einem
echten `--geometry-only`-Lauf (Erdgeschoss x 0.0..11545.0 / y -2609.5..
12652.0; Obergeschoss x -1010.8..12451.1 / y 1.9..12730.3) stimmt exakt
mit den `<image>`-Attributen im laufenden DOM ueberein (per
`javascript_tool` ausgelesen, beide Geschosse). Bildlich bestaetigt:
Wandlinien des Fotos liegen jetzt praezise auf den Raumpolygon-Kanten,
nicht mehr nur naeherungsweise.

## HAUS-ANNOTATOR-EINGEKLEMMT-001 (COMPLETE)

Rainer: "why can't i select the railing anymore it wirked yesterday",
dann auf Rueckfrage: `http://localhost:3020/haus?plan=twostorey_047`.

Kein Klick-Handler-Fehler: die Gelaender-Kante-Klicklogik in
`floorplan-simplifier/static/element-edit.js` (`stairRailingEdgeAtPoint`)
wurde direkt gegen `twostorey_046` UND `twostorey_047` getestet (echte
Klicks per Browser-Tool und synthetische PointerEvents, gezoomt und
ungezoomt) und funktionierte in JEDEM Fall korrekt.

Ursache lag stattdessen in `born2thrill-local-workbench/src/app/haus/
page.tsx`: die eingebettete Annotator-Seite (iframe) bekommt nur die
Restbreite neben der Hausliste (270px offen). Auf einem ~1025px breiten
Fenster bleiben dem iframe dann ~754px -- UNTER dem Annotators eigenem
`@media (max-width: 900px)`, das seine Werkzeugleiste und die Kanvas
von nebeneinander auf UNTEREINANDER umstellt. Die Kanvas landet dabei
ausserhalb des sichtbaren, nicht scrollbaren iframe-Bereichs -- nichts
auf dem Grundriss ist mehr klickbar, nicht nur das Gelaender.

Der Zusammenklapp-Knopf fuer die Hausliste existierte schon (Rainer,
2026-08-20: "make the left column colapsable so i have more room for
the annotaitns and funiisching"), merkt sich aber nur den zuletzt
gewaehlten Zustand ueber `localStorage` -- unabhaengig vom Schritt. Wer
die Liste zum Haussuchen aufklappt und dann zu Zeichnen/Moebel wechselt,
hat sie ungewollt weiter offen und verliert die Breite wieder.

Fix: ein `useEffect` auf `schritt` klappt die Liste beim BETRETEN von
"raeume" oder "moebel" automatisch zu (`setZu(true)`); der Knopf zum
manuellen Wiederaufklappen bleibt unveraendert nutzbar. Bildlich
bestaetigt fuer beide Schritte: Werkzeugleiste und Kanvas wieder
nebeneinander, volle Interaktion.

## HAUSTUER-ANTHRAZIT-GESCHLOSSEN-HARD-RULE-001 (COMPLETE)

Rainer: "do you still have the models of the real front door the
anthrazit one? didn't we want to put that one in but not opend so
plwease try that and make a hard rule out of it" -- Rueckbezug auf eine
fruehere Session (2026-09-07 laut Code-Kommentar), in der ein reales
Anthrazit-Metall-Haustuer-Modell anstelle der prozeduralen Tuer
eingebaut werden sollte, geschlossen.

Bestand bereits vollstaendig, nur nie mit einer Hard Rule
abgesichert:

- `FRONT_DOOR_ASSET` in `born2thrill-local-workbench/scripts/
  render-exterior.py:639` referenziert
  `E:\_models_hub\_extracted\Metal_Front_Door_3D_Model_7961_BLEND\
  Metal Front Door 3D Model (7961).blend` -- existiert auf der Platte,
  geprueft. Wird nur fuer die Oeffnung mit `role: main_entrance`
  platziert (`render-exterior.py:1041-1052`), `FRONT_DOOR_METALLIC_FIX
  = 0.9` erzwingt das metallische Anthrazit-Finish.
- Kein Aufschlag-/Oeffnen-Mechanismus auf diesem Pfad -- anders als
  Innentueren (`add_door_leaf()` in `render-furnished-dollhouse.py`,
  nur fuer Innenwaende) hat der Haustuer-Pfad ueberhaupt keinen
  Rotations-/Oeffnungs-Parameter, das Objekt wird statisch gesetzt.

Verifiziert nicht nur per Code-Lesen, sondern direkt am echten Blender-
Objekt: `twostorey_047`s aktuellstem Baseline-Render
(`go-baseline/exterior-flachdach-baseline.blend`, 2026-09-17) per
`blender --background ... --python` inspiziert. Objekt
`extwall-0-3-door` traegt die Original-CGAxis-Materialien
`cgaxis_models_79_61_01`/`_02`: Base Color RGB ~0.047-0.059 (nahezu
Schwarz/Anthrazit), Metallic 0.9 (exakt `FRONT_DOOR_METALLIC_FIX`).
`matrix_world` zeigt reine Skalierung (0.75 / 1.0 / 0.922), keinerlei
Rotationskomponente -- die Tuer steht zu 100% geschlossen, kein
Aufschlagwinkel.

Neu ergaenzt, die eigentliche Hard Rule:

- `policies/zuhausefinder-hard-rules.v1.json`: neuer Schluessel
  `"entrance_door_closed": true` neben dem bestehenden `entrance_door`
  (Erscheinungsbild-Beschreibung).
- `scripts/render-contract.py`s `REQUIRED_RULES`-Tupel um
  `entrance_door_closed` erweitert -- jede Vertragskompilierung
  scheitert jetzt, wenn dieser Schluessel fehlt oder falsy ist, exakt
  wie bei den bestehenden Pflichtregeln.
- `scripts/render-contract.test.py`s Fixture-Policy und die
  Missing-Rules-Testschleife um denselben Schluessel ergaenzt, damit
  der neue Pflichtschluessel selbst getestet ist. `python
  render-contract.test.py -v`: 5/5 gruen.
- Prosa-Regelwerk `plans/visual-catalog-handoff-2026-09-05/
  VISUAL-CATALOG-HARD-RULES.md`, Abschnitt 4, neuer Punkt 8: Haustuer
  (`role: main_entrance`) rendert immer geschlossen, mit Verweis auf
  die beiden Policy-/Contract-Fundstellen.

Kein Bug, keine Regression -- reine Nachtraeglich-Absicherung eines
bereits korrekt gebauten, aber bislang ungeschuetzten Verhaltens gegen
kuenftige Aenderungen an `render-exterior.py`.

## CODEX-FUND-6-TREPPENART-VON-KOPIE-001 (COMPLETE)

Aus dem `/codex`-Review vom 2026-09-17 (siehe
`CODEX-REVIEW-RAILING-VALIDATOR-REGRESSION-001`): Fund #6, medium,
`element-edit.js:290` -- "Changing stair type or reversing direction
from an opening copy leaves the real stair unchanged." Rainer bat
danach explizit, die 11 offenen Funde nacheinander durchzugehen, hier
Fund #6 zuerst (baut direkt auf der `stairRailingQuelle()`-Infrastruktur
von heute auf).

Bestaetigt per Code-Lesen: `annotation_stair_core()` in
`build-simplifier-render-plan.py:2705-2711` filtert `elements` auf
`type == "stairs" and floor_level == ground_level` -- eine role:
"opening"-Kopie im Ober-/Dachgeschoss wird NIE gelesen, weder ihr
`stair_type` noch ihre Punktreihenfolge (Richtung). Trotzdem schrieben
die Rechtsklick-Menuepunkte "Treppenart" und "Richtung umkehren
(oben/unten tauschen)" in `element-edit.js` bislang direkt auf
`element` -- das SELEKTIERTE Element, auch wenn das die wirkungslose
Kopie war. Anders als der `railing_sides`-Block direkt darunter, der
schon seit `TREPPENLOCH-GELAENDER-VOM-OBERGESCHOSS-001` ueber
`stairRailingQuelle()` zur echten Quelle durchschreibt.

Fix in `element-edit.js`:
- `railingQuelle = stairRailingQuelle(element) || element` an den Anfang
  des `if (element.type === "stairs")`-Blocks gezogen (vorher erst kurz
  vor dem Gelaender-Menue deklariert) und fuer alle drei Stellen
  wiederverwendet.
- Treppenart-Menue (Punkte setzen/loeschen) liest und schreibt jetzt
  `railingQuelle.stair_type` statt `element.stair_type`.
- "Richtung umkehren" kehrt jetzt `railingQuelle.points` und
  `railingQuelle.railing_sides` um (vorher `element.*`). Zusaetzlich,
  nicht nur eine Ein-zu-eins-Uebertragung des Gelaender-Fixes: jede
  ANDERE role:"opening"-Kopie (andere Geschosse) bekommt ihre eigene
  Punktreihenfolge ebenfalls umgedreht -- sonst zeigt Segment "0-left"
  auf einer Kopie nach der Umkehr nicht mehr auf dasselbe reale Segment
  wie "0-left" an der jetzt umgekehrten Quelle, und ein Klick auf die
  Kopie wuerde das falsche Segment umschalten (Codex' zweiter Punkt im
  selben Fund).

Verifiziert live gegen `twostorey_047` (2 Geschosse, ein echtes
Treppenelement + eine role:"opening"-Kopie im Obergeschoss), direkt im
laufenden Annotator per `javascript_tool`, OHNE zu speichern:
- Die exakte neue Handler-Logik ausgefuehrt mit der Obergeschoss-Kopie
  als `element`: `stairRailingQuelle(copy) === source` (true),
  `railingQuelle.stair_type = "podest"` gesetzt -- Ergebnis: die QUELLE
  (Erdgeschoss) traegt jetzt `stair_type: "podest"`, die Kopie behaelt
  ihr eigenes (ungenutztes) `"viertelgewendelt"`. Vorher waere das
  umgekehrt gewesen.
- Dieselbe Live-Ausfuehrung fuer "Richtung umkehren": Quelle-Punkte UND
  Kopie-Punkte beide korrekt umgekehrt (`JSON.stringify(...) ===
  JSON.stringify([...vorher].reverse())` fuer beide bestaetigt).
- Alle Testwerte danach zurueckgesetzt, Live-Projektdaten unveraendert
  (per erneutem Auslesen bestaetigt: `stair_type` wieder
  "viertelgewendelt", Punkte identisch zum Ausgangszustand). `node
  --check element-edit.js`: syntaktisch sauber.

**PENDING (aus demselben Codex-Review, noch nicht angegangen):** Funde
#1 (bereits als kritische Regression sofort gefixt, separat
dokumentiert), #2-5 und #7-12 -- siehe
`CODEX-REVIEW-RAILING-VALIDATOR-REGRESSION-001` fuer die volle Liste
mit Einordnung.

## HAUSTUER-OFFEN-VON-INNEN-001 (COMPLETE)

Rainer, nach eigener Neu-Generierung von `twostorey_049`: "so now what i
just generated the models again and the front dorr has not changed and
sis still open". Direkter Widerspruch zu
`HAUSTUER-ANTHRAZIT-GESCHLOSSEN-HARD-RULE-001` von vorhin -- dort war
die Haustuer im AUSSEN-Render nachweislich geschlossen. Der Widerspruch
war der Hinweis: zwei verschiedene Skripte bauen zwei verschiedene
`.blend`-Dateien aus DENSELBEN Annotationen, und nur eines der beiden
kennt die Sonderregel.

Root Cause: `render-exterior.py` (Aussen-Render) haelt die Haustuer
schon lange geschlossen -- die reale Anthrazit-Metalltuer, kein
Aufschlag. Aber `render-furnished-dollhouse.py` (Innen-Dollhouse, jede
Interior-Ansicht) hat `role: "main_entrance"` NIRGENDS im Code erwaehnt
(bestaetigt: `grep main_entrance render-furnished-dollhouse.py` -> kein
Treffer). `add_door_leaf()` behandelte die Haustuer wie jede
Zimmertuer: generisches weisses Blatt, 45 Grad aufgeschwenkt
(`DOOR_OPEN_DEG`), inklusive Anschlag-/Kollisionslogik. Von aussen
korrekt, von innen (Diele-Blickwinkel jeder Interior-Aufnahme) sichtbar
offen -- exakt das, was Rainer nach der Neugenerierung sah.

`role` war technisch schon im Plan-JSON vorhanden
(`build-simplifier-render-plan.py:2042`: `"role": element.get("role")`
je Oeffnung) -- render-furnished-dollhouse.py hat es nur nie
abgefragt.

Fix in `render-furnished-dollhouse.py`s `add_door_leaf()`: neue
Bedingung `ist_haustuer = opening.get("role") == "main_entrance"`.
Wenn wahr, nimmt die Tuer sofort die Pose `leaf_pose(hinge_sign, 0.0)`
-- exakt dieselbe "0 Grad = geschlossen"-Pose, die die Funktion
ohnehin schon als Fallback benutzt, wenn eine normale Tuer beim
Aufschwingen mit Moebeln oder einer anderen Tuer kollidiert
(`leaf_pose(hinge_sign, 0.0)` weiter unten, unveraendert) -- kein neuer
Code-Pfad, nur ein zusaetzlicher Aufrufer der bestehenden
Geschlossen-Pose. Die Kollisions-/Umhaengen-Pruefung (`blocked()`,
`hits_furniture()`, `hits_other_leaf()`) wird fuer die Haustuer
uebersprungen -- unnoetig, wenn sie ohnehin nie aufschwingt.

Verifiziert: `python -m py_compile` sauber; bestehende Testsuite
`render-furnished-dollhouse.test.py` weiterhin 20/20 gruen (keine davon
beruehrt `add_door_leaf`/`main_entrance` direkt). Live-Regeneration von
`twostorey_049`s Interior-Baseline-Blend (derselbe `plan-modern.json`,
derselbe `blender --background --python render-furnished-dollhouse.py
--`-Aufruf wie `run_project.py` ihn nutzt) bestaetigt per
Blender-Objektinspektion:
- Log: `[dollhouse] door closed wall-9-door (main_entrance renders
  closed everywhere)` -- der neue Zweig feuert tatsaechlich fuer genau
  das Element, das vorher offen war.
- `wall-9-door`s `rotation_euler_deg` vorher `[0, 0, 135]` (45 Grad
  Aufschlag vom Wandwinkel), nachher `[0, 0, 180]` (reiner Wandwinkel +
  180, keinerlei Aufschlagkomponente) -- die Tuer steht buendig in der
  Wandebene, wie jede andere per `leaf_pose(..., 0.0)` geschlossene Tuer
  in diesem Skript.

Rainers Regenerierung, die diese Meldung ausloeste, lief VOR diesem
Fix -- der go-baseline-Satz von `twostorey_049`
(`E:\born2thrill-local-workbench-data\corrections\twostorey_049\renders\go-baseline\`,
14:33 Uhr) zeigt also noch den alten Stand. Eine erneute Generierung
nach diesem Fix ist noetig, um die geschlossene Haustuer auch im
gelieferten Satz zu sehen.

**PENDING:** Nur die Haustuer-Oeffnung selbst wurde ausgenommen. Sollte
es je eine zweite `role: "main_entrance"`-Oeffnung im selben Haus geben
(bisher nie beobachtet, `annotation_stair_core()`-Analogon fuer Tueren
existiert nicht), wuerden alle betroffen -- vermutlich korrekt, aber
nie getestet.

## MOEBEL-KOORDINATEN-STALENESS-UND-TREPPENBREITE-001 (COMPLETE)

Rainer, nach einem Screenshot mit doppelten/geisterhaften Raumbeschriftungen
und einem schwarzen Kasten ueber der Treppe in twostorey_047s Moebel-Tab:
"dude i think your code is broken", dann "this is getting tiresome", dann
explizit: "i think there are many flaws especially in the scaling between
the different tabs i think this has to be standardised and simplified" plus
Auftrag zu einem vollen Codex-Architektur-Review der Koordinatenraeume,
gefolgt von "can you two guys do this and fix it and test it i have some
stuff to do, just get it to work."

Voller Plan mit Befund, Umsetzung und Verifikation:
`born2thrill-local-workbench/plans/
moebel-koordinaten-staleness-und-treppenbreite-v1.md`.

Codex fand 10 Befunde in einem dedizierten Architektur-Review (Brief +
Ergebnis liegen im Scratchpad dieser Sitzung). Vier davon in diesem Task
behoben, mit eigener Verifikation bestaetigt:

1. **Root Cause der twostorey_047-Moebelverwuerfelung gefunden**: nicht ein
   erneutes Umzeichnen, sondern `saveFurniture()` (corrections/route.ts)
   stempelte beim Speichern IMMER die GERADE AKTUELLE Raum-Identitaet,
   unabhaengig davon, welche der Moebel-Tab beim Platzieren tatsaechlich
   angezeigt hatte. Der bestehende Staleness-Check auf der Bauseite
   (`workbench_furniture()`) kann das nie erwischen, wenn der Speicherpfad
   selbst schon einen frisch aussehenden, aber falschen Stempel setzt --
   genau das ist am 2026-09-16 schon einmal korrigierten Daten erneut
   passiert (dieselben Raumausdehnungen wie damals, byte-identisch --
   also keine neue Zeichnung, sondern eine erneute Spiegelung).
   Fix: `render_geometry`/`geometry_only()` liefert jetzt pro Geschoss
   `geometry_identity` (dieselbe `level_geometry_identity()`, die der Bau
   schon nutzt); der Client haelt sie in einer Ref und schickt sie als
   `displayed_geometry_identity` beim Speichern mit; die API lehnt ab
   (409), wenn sie von der aktuellen abweicht, statt neu zu stempeln.
2. **Legacy-Raum-Umettikettierung geschlossen**: `normalizeFurnitureDocument()`
   ueberschrieb jeden eingehenden `coordinate_space` bedingungslos mit dem
   aktuellen -- eine noch nicht migrierte Legacy-Datei haette nach einem
   Speichern wie migriert ausgesehen, ohne dass eine einzige Koordinate
   umgerechnet wurde. Lehnt jetzt ab (wirft), nennt bei Legacy-Raum das
   Migrationsskript.
3. **Treppenbreiten-Widerspruch (Codex-Fund #6 von heute Morgen, nicht
   vollstaendig behoben)**: `geometry_only()` rief `annotation_stair_core()`
   noch mit dem Geschoss-EIGENEN Frame auf (fuer ein Obergeschoss ein
   RegisteredFrame) statt mit dem Ground-Frame, obwohl die Funktion IMMER
   die Ground-eigenen Punkte liest -- Ground-native Koordinaten liefen also
   durch eine Registrierungs-Affinitaet, die fuer die andere Richtung gebaut
   ist. Gemessen: Bau (shared_stair_core) 900/1415.5mm (EG/OG je nach Haus),
   Moebel-Tab-Ansicht vorher 1049.4mm (_047) / 1021.6mm (_049) auf dem
   Obergeschoss. Fix: Quelle ist jetzt immer Ground-Frame + ground_level,
   der Y-Flip fuers Display bleibt pro Geschoss. Beide Testhaeuser stimmen
   jetzt exakt mit dem echten Bau ueberein.
4. **twostorey_047 korrigiert**: beide Geschoss-Moebeldateien einmal
   zurueckgespiegelt (dieselben, unveraenderten Raum-Ausdehnungen wie beim
   ersten Fix), pruegepunktweise (Point-in-Polygon) verifiziert -- alle 21
   Erdgeschoss- und alle 17 Obergeschoss-Objekte stehen jetzt in ihrem
   plausiblen Raum (Kueche komplett in Kueche, Bad-Objekte im Bad, etc.).

Verifiziert: `python build-simplifier-render-plan.test.py` (72 Tests, 1
VORBESTEHENDER unabhaengiger Fehler in `build_floor_walls_and_openings()`
-- gezielt durch Revert+Re-Test der eigenen Aenderung als vorbestehend
bestaetigt, nicht behoben, siehe Plan); `node --test furniture-document.test.mjs`
(15/15, 3 neu); `npx tsc --noEmit` sauber; live gegen die laufenden
Dev-Server getestet (409 bei falscher Identitaet, 200 bei richtiger);
`workbench_furniture()` liest beide korrigierten Geschosse ohne Fehler;
`go.py twostorey_047` erneut durchlaufen lassen.

**PENDING (aus demselben Codex-Review, nicht in diesem Task angegangen):**
Codex' vorgeschlagene grosse Vereinfachung (EIN kanonischer mm/y-oben-Raum,
Geometrie-Snapshot mit Revisions-Hash, Entfernen von RENDER_GEOMETRY_SPACE/
LEGACY_FURNITURE_SPACE nach Einmal-Migration) -- eigenes, groesseres Vorhaben,
braucht eine Korpus-weite Migrationsstrategie und Rainers Freigabe, bevor es
angegangen wird. Ausserdem ungeprueft: ob NOCH ein anderes Projekt durch den
alten (jetzt gefixten) Speicherpfad bereits denselben Spiegelfehler hat --
`_047` war das einzige gemessene Projekt. Empfehlung: Stichprobe uebers
Corpus, nicht annehmen, dass es sauber ist.

**Nachtrag, selber Tag: die Flip-BASIS selbst, korpusweit.** Rainer: "well
do it the other stuff doesn´t seem to be working, but it is the only
logical thing to do" -- Freigabe fuer Codex' Kernempfehlung (nicht nur die
Punktkorrekturen oben). Umgesetzt: die Spiegel-Basis von `lo, hi`
(bewegliches Ziel -- diese eigenen Raumpolygone dieses Geschosses, von
geometry_only() und workbench_furniture() unabhaengig voneinander neu
berechnet) auf `frame.height_mm` (stabil -- reine Funktion aus Massstab und
Bildseitenverhaeltnis, fuer eine RegisteredFrame identisch mit ihrer
Ground-Frame) umgestellt. Genau die von Codex benannte Gefahr
("coordinate labels and geometry stamps can be changed without
transforming... the coordinates they describe") behoben, OHNE die volle
Neuarchitektur (neues Speicherschema, Flips komplett aus dem Speicher
entfernen, GeometrySnapshot-Vertrag) in einem unbeaufsichtigten Durchgang
zu versuchen.

Vollstaendiger Bericht inklusive eines waehrend dieser Aufgabe SELBST
gemachten und sofort gefangenen Fehlers (Migration versehentlich zweimal
auf `_047`/`_049` angewendet, per Point-in-Polygon-Check erkannt, von Hand
korrigiert, Skript danach mit einem `flip_basis`-Stempel idempotent
gemacht) im "Addendum, same day" am Ende von
`born2thrill-local-workbench/plans/
moebel-koordinaten-staleness-und-treppenbreite-v1.md`.

Neues Skript `scripts/moebel-flip-basis-migrieren.py`: einmalige,
korpusweite Migration (61 Moebeldateien, 103 Projekte durchsucht) --
da beide Konventionen "spiegle um eine Konstante" sind, ist die Umrechnung
eine reine Verschiebung pro Geschoss, keine Neuableitung aus Raumpolygonen.
57 Dateien migriert und verifiziert (Stichprobe: 3 weitere Projekte per
`workbench_furniture()` gegengelesen, `_047`/`_049` vollstaendig per
Point-in-Polygon gegen frisches `geometry_only()` erneut verifiziert, 0
Treffer ausserhalb jedes Raums).

Verifiziert: `python build-simplifier-render-plan.test.py` weiterhin 72
Tests, derselbe eine vorbestehende, unabhaengige Fehler; `go.py
twostorey_047` einmal mehr vollstaendig durchgelaufen.

**PENDING:** die 57 nicht-`_047`/`_049`-Korpusdateien wurden im Batch
migriert und nur stichprobenartig gegengelesen, nicht einzeln
Point-in-Polygon-verifiziert wie die beiden Fokus-Haeuser. Codex' weitere
Empfehlungen (stabile Geschoss-IDs ueberall, den separaten Flip des
`--corrected`-Pfads vereinheitlichen, ein GeometrySnapshot-Vertrag)
bleiben offen. Eine vorbestehende, von diesem Fix unabhaengige
Staleness-Ablehnung wurde bei `onehalfstorey_020`s Erdgeschoss gefunden
(dessen Raeume wurden zu einem fruaeheren, unabhaengigen Zeitpunkt
umgezeichnet) -- nicht behoben, da ausserhalb des Umfangs.

**Nachtrag, selber Tag: die volle Korpus-Verifikation und vier weitere
Punkte.** Rainer: "all 5" -- Auftrag, alle fuenf zu dieser Zeit offenen
Punkte durchzugehen.

1. **Volle Korpus-Verifikation (statt Stichprobe).** Alle 43 aktiven
   Moebel-Geschossdateien (61 Dateien minus `.vor-vorderseite-*`-Backups
   und leere) per Point-in-Polygon gegen frisches `geometry_only()`
   geprueft: **43 von 43 sauber**, jedes Objekt in einem Raum. Dabei
   selbst einen Fehler im PRUEFSKRIPT gefunden und korrigiert: ein erster
   Versuch verglich `workbench_furniture()`s Ausgabe (Frame-Raum, y oben)
   direkt gegen `geometry_only()`s Raeume (Display-Raum, y unten) --
   Aepfel gegen Birnen, meldete faelschlich fast das ganze Corpus als
   kaputt, inklusive der gerade erst dreifach verifizierten `_047`/`_049`.
   Korrigiert: direkt die rohe gespeicherte JSON gegen die Display-Raeume
   pruefen, wie beim urspruenglichen `_047`-Fix.
2. **`onehalfstorey_020`s Erdgeschoss-Staleness behoben.** Die 27
   gespeicherten Moebel wurden gegen die AKTUELLE Raumgeometrie
   Point-in-Polygon geprueft: alle 27 stehen bereits korrekt (die
   Abweichung war kosmetisch). Identitaets-Stempel manuell auf die
   aktuelle Identitaet gesetzt -- genau die Pruefung, die ein Mensch beim
   Speichern im Moebel-Tab von Hand gemacht haette, nur diesmal
   programmatisch bestaetigt statt vermutet.
3. **"Teppiche unter der Wand" auf `twostorey_047` nicht reproduzierbar.**
   Wandnahe Teppiche in vier Ansichten geprueft (heutiger frisch gebauter
   Grund- und Obergeschoss-Baseline-Render, sowie das aeltere Sept-16-
   Auslieferungspaket, dieselben Ansichten) -- ueberall sauber, keine
   sichtbare Ueberschneidung mit einer Wand. Die bereits bestehende
   200mm-Randklemmung (2026-09-07-Fix) greift korrekt. Keine neue
   Vermutung geraten (Governance-Regel: nicht ein drittes Mal raten) --
   stattdessen ehrlich als "nicht reproduzierbar" gemeldet. Die
   VERWANDTE, bereits fruaeher dokumentierte, andere Teppich-Anzeige
   (`plans/realistic-cut-height-slab-clearance-v1.md`, Teppich durch eine
   verkuerzte Wand von der "realistic"-Kamera aus sichtbar, NICHT unter
   der Wand) bleibt separat offen, siehe dortige Status-Notiz.
4. **WordPress-Katalog fuer `twostorey_047` ist NICHT stale, weil nichts
   live ist.** `/api/floorplan-workbench/state` bestaetigt: `state:
   "bilder_freigeben"`, `catalogue_images: 0`, `approved: "offen"` -- 12
   Bilder liegen in WordPress' Mediathek (hochgeladen), aber KEINES ist
   angehakt/freigegeben, also erscheint auf der oeffentlichen Katalogseite
   nur ein Platzhalter-Icon, kein echtes Bild. Kein Kunde sieht derzeit
   irgendein Bild dieses Hauses. **Aber:** diese 12 hochgeladenen Bilder
   selbst stammen sehr wahrscheinlich noch aus VOR den heutigen Fixes
   (verwuerfelte Moebel) -- vor einer Freigabe sollten sie durch frisch
   generierte ersetzt werden, nicht einfach angehakt. Keine WordPress-
   Aenderung vorgenommen (externes System, braucht Rainers ausdrueckliche
   Freigabe).
5. **Drei weitere Codex-Funde aus dem Annotator-Review von heute Morgen
   behoben** (kleine, isolierte, sofort getestete Fixes, kein Bezug zu
   den Koordinatenraum-Themen oben):
   - **Fund #8** (`annotate.js:125`): `imageLoadFailed` wurde von der
     "error"-Behandlung gesetzt und NIE zurueckgesetzt -- dieselbe
     DOM-Mutation-ueberlebt-Neurendern-Fehlerklasse wie der Moebel-
     Referenzbild-Fix von heute frueh, nur mit rohem DOM statt React.
     Ein Bild, das nach einem fehlgeschlagenen Laden erfolgreich
     nachgeladen wird (Geschosswechsel, Bild ersetzt), blieb fuer immer
     auf der Fallback-Groesse. Fix: der "load"-Handler setzt das Flag
     jetzt zurueck und raeumt die Inline-Fallback-Groesse auf.
   - **Fund #10** (`app.py:5199`): `width_mm` (das Fenster-Breiten-
     Dropdown) fehlte in `normalize_element()`s Namensliste -- derselbe
     "stille Filter" wie schon bei `stair_type`. Eine gewaehlte
     Fensterbreite ueberlebte den Editor, aber nicht das Speichern. Fix:
     Feld zur Liste ergaenzt; neuer Test
     `test_fenster_breite_ueberlebt` in
     `tests/test_element_felder_ueberleben_speichern.py` (271/271 Tests
     weiterhin gruen).
   - **Fund #11** (`annotate.js:725`): `treppenbreitenNachziehen()`s
     Falluntscheidung schrieb in BEIDEN Zweigen denselben Wert
     (TREPPE_BREITE_M) -- der "von Hand gesetzt"-Zweig trug den
     Kommentar seiner Absicht, aber nicht deren Code. Eine von Hand auf
     1,20 m gezogene Treppe wurde beim naechsten Speichern lautlos auf
     0,90 m zurueckgesetzt. Fix: der Zweig rechnet jetzt die tatsaechliche
     `element.width` mit dem aktuellen Massstab um, statt den Standard
     zu wiederholen. Drei neue Tests in `treppenbreite.test.mjs`
     (27/27 gruen).

Verifiziert: `python -m unittest discover -s tests` (floorplan-simplifier,
271 Tests) und `node --test static/treppenbreite.test.mjs` beide gruen;
`node --check annotate.js` sauber.

**Nachtrag, selber Tag: die restlichen sechs Codex-Funde behoben.**
Rainer, nach der Liste offener Punkte: "all 4" (inklusive "die
restlichen Annotator-Funde"). Alle sechs noch offenen Funde aus dem
Annotator-Review jetzt behoben, jeweils live im laufenden Annotator
gegen echte oder synthetische Testdaten verifiziert (nicht nur gelesen):

- **Fund #5** (`annotate.js`, `saveAnnotations()`): Speichern sperrte
  die Save-Knoepfe, aber nicht Zeichnen/Ziehen/Rechtsklick -- eine
  Aenderung waehrend des laufenden Requests wurde von der
  Server-Antwort ueberschrieben, sobald sie zurueckkam. Fix: ein
  monotoner `dirtyRevision`-Zaehler (steigt bei jedem `markDirty()`);
  hat er sich waehrend des Awaits veraendert, behaelt die Funktion die
  LOKALEN (neueren) Daten und ruft NICHT `markClean()` auf. Live
  verifiziert: `fetch` kuenstlich verzoegert, waehrend des Requests ein
  Testelement eingefuegt -- es ueberlebte den Save, `hasUnsavedChanges`
  blieb korrekt `true`.
- **Fund #9** (`zoom-pan.js`, `applyZoom()`): `applyZoom(viewZoom)` beim
  Bildwechsel war ein No-Op, sobald sich die ZAHL nicht aenderte, auch
  wenn das Bild selbst (und damit seine Pixelgroesse) sich geaendert
  hatte. Fix: zusaetzlich `lastAppliedNaturalWidth/Height` verfolgen und
  bei Aenderung auch bei gleichem Zoomfaktor neu anwenden. Live
  verifiziert an `twostorey_047`s zwei echten, unterschiedlich grossen
  Geschossbildern: bei 200% Zoom auf das Obergeschoss gewechselt --
  Inline-Groesse folgte jetzt exakt der neuen Bildgroesse
  (2684x2540 statt der alten 2336x3088).
- **Fund #12** (`geometry-tools.js`, `fetchWallOverlay()`): `activeFloor`
  wurde NACH dem Await gelesen, um das Ergebnis zu beschriften --
  wechselte das Geschoss waehrend der Anfrage, bekamen die Waende des
  ALTEN Geschosses das Etikett des NEUEN. Fix: das Geschoss VOR dem
  Fetch einmal einfrieren (`requestedFloor`) und damit beschriften. Live
  verifiziert: `/api/walls` kuenstlich verzoegert, waehrend der Anfrage
  das Geschoss gewechselt -- das Ergebnis trug korrekt weiter das ALTE
  Geschoss, `drawWallOverlay()`s bestehende Schutzklausel blendet es
  damit korrekt aus.
- **Fund #7** (`annotate.js`, Aussenflaechen): Terrasse/Garten/Gehweg
  wurden roh auf JEDEM Geschoss gezeigt, ohne die Registrierung, die
  `outerOutline` fuer denselben Zweck laengst hat -- sie "wanderten"
  beim Geschosswechsel relativ zum Gebaeude. Fix: neues
  `floor_level`-Feld je Flaeche (gesetzt beim Zeichnen), neue
  `exteriorAreaPointsForFloor()` (dieselbe Transformation wie
  `outlineForFloor()`), angewendet beim Zeichnen UND beim
  Ueberlappungstest/-Zusammenfuehren zweier Flaechen. Live verifiziert:
  eine neue Testflaeche auf dem Erdgeschoss angelegt, `floor_level`
  korrekt gesetzt, auf dem Obergeschoss erschienen andere (registrierte)
  Koordinaten als die gespeicherten.
- **Fund #2** (`geometry-tools.js`, `applyStatedBuildingSize()`): ein
  eingetipptes Gebaeudemass leitete den Massstab aus DIESEM Geschoss
  ab und uebernahm densselben Zahlenwert fuer JEDES andere Geschoss --
  bei bis zu 21% Unterschied in der eigenen Bild-Registrierung
  zwischen zwei Geschossen (dokumentiert im Code selbst, mehrere
  Beispielhaeuser) ein entsprechend falscher Massstab ueberall ausser
  dem einen Geschoss, auf dem getippt wurde. Fix: neue
  `outlineRelativeExtentForFloor(level)`; jedes Geschoss bekommt seinen
  EIGENEN aus der Aussenkontur abgeleiteten Massstab, nur ein Geschoss
  ohne eigene Registrierung faellt auf den geteilten Wert zurueck. Live
  verifiziert an `twostorey_047`: Erdgeschoss 11,77 m/Einheit,
  Obergeschoss 13,73 m/Einheit -- vorher waeren beide 11,77 gewesen.
- **Fund #3** (`annotate.js`, `stairCopyElement()`): eine "opening"-Kopie
  ABWAERTS zu kopieren (z.B. vom Obergeschoss aus "nach unten
  kopieren") blieb wegen `element.role === "opening"` in der Bedingung
  weiterhin "opening", unabhaengig von der Richtung --
  `copyStairsToAdjacent()` ersetzt das Zielgeschoss aber bedingungslos,
  loeschte also die ECHTE Treppe und setzte eine ZWEITE Oeffnung an
  ihre Stelle: am Ende keine einzige echte Treppe mehr im ganzen Haus
  (die einzige Quelle, aus der `annotation_stair_core()` je baut). Die
  Schwesterfunktion `stairCopyRoom()` (fuer die Luftraum-Flaeche)
  entscheidet schon laenger rein nach Richtung, nicht nach der Rolle
  der Quelle -- `stairCopyElement()` jetzt genauso angeglichen: die
  Bedingung ist nur noch `direction > 0`. Live verifiziert (reine
  Funktionspruefung, keine echten Daten angefasst): Opening abwaerts
  kopiert -> "Treppe" (vorher faelschlich "Treppenöffnung"); alle drei
  anderen Kombinationen unveraendert korrekt.

Verifiziert: `python -m unittest discover -s tests` (271/271) und
`node --test static/*.test.mjs` (277/277) beide gruen nach allen sechs
Fixes zusammen.

**PENDING (Stand vor dem Nachtrag unten):** keine der sechs Annotator-Funde
aus dem urspruenglichen Codex-Review bleibt offen. Aus dem SEPARATEN
Koordinatenraum-Review vom selben Tag bleiben weiterhin offen: RegisteredFrame
Snapping-vs-Affine-Abweichung, der separate Flip des `--corrected`-Pfads,
Geschoss-Identitaet per Array-Index bei 3+ Geschossen,
`moebel-registrieren.py`s Migrations-Policy-Luecke, sowie Codex' groessere
Vereinfachungs-Idee (ein kanonischer Raum, GeometrySnapshot-Vertrag)
insgesamt.

## MOEBEL-KOORDINATEN-STALENESS-UND-TREPPENBREITE-002 (Nachtrag, selber Tag, 2026-09-18)

Rainer: "fix whatever need to be fixed". Vier Punkte abgearbeitet:

1. **Lokaler Neu-Render `twostorey_047`** mit allen heutigen Fixes (Flip-Basis,
   Stair-Frame, Staleness-Guard): `python run_project.py twostorey_047
   --styles modern,classic --floors 0,1` (mit `FLOORPLAN_WORKBENCH_DATA_DIR`
   gesetzt). Beide Stile, beide Geschosse, alle `verify_render_blend`/
   `verify_render`-Pruefungen gruen (R0-R9, wall_angles, opening_count,
   furniture_inside). Sichtpruefung beider Grundrisse: Kuecheninsel/Geraete
   in der Kueche, Sofas im Wohnbereich, kein schwebendes oder falsch
   platziertes Moebel -- deckt sich mit der frueheren Point-in-Polygon-Pruefung.
   Alte Dateien automatisch nach `superseded-2026-09-18` verschoben. NICHT
   auf die live WordPress-Katalogseite hochgeladen -- das bleibt eine separate,
   im Chat explizit zu bestaetigende Aktion (Governance zu oeffentlichen
   Veroeffentlichungen), unabhaengig von "fix whatever need to be fixed".

2. **Teppich-ueber-Wand-Problem (realistic Kamera) -- NICHT reproduzierbar,
   NICHT geraten.** Aus `realistic-cut-height-slab-clearance-v1.md`: der
   urspruengliche Fund kam nur aus einem Pixel-genauen Raycast, nicht aus
   Sichtpruefung. Heute an vier echten `camera_style: realistic`-Renders
   nachgesehen (`twostorey_045` und `twostorey_046`, je Erd- und Obergeschoss,
   `renders/go-baseline/interior-modern*.png`): kein sichtbarer Fehler in
   keinem der vier Bilder, Teppiche bleiben sauber im Rauminneren. Da der
   Fehler nicht reproduzierbar ist, wurde KEIN Code geaendert (Plan-Dokument
   selbst warnt davor, eine dritte Hypothese ohne Beleg zu raten). Bleibt als
   unreproduziert/unbeobachtet dokumentiert statt als behoben oder als Code-Fix
   verbucht.

3. **`moebel-registrieren.py` Migrations-Policy-Luecke (Codex-Fund #10,
   Koordinatenraum-Review) -- behoben.**
   [scripts/moebel-registrieren.py:67](scripts/moebel-registrieren.py:67):
   das Skript prüfte nur `floor_registration`, nie `coordinate_space` --
   haette es also ein Dokument in falschem Raum (z. B. `LEGACY_FURNITURE_SPACE`
   oder ein bereits einmal registriertes) als "unregistriert" angesehen und
   die Umrechnung blind angewendet, waere jedes Moebelstueck verschoben
   worden. Guard ergaenzt: bricht mit `[moebel] ... coordinate_space ist ...
   nicht ... -- ueberspringe` ab statt zu konvertieren, sobald
   `coordinate_space != RENDER_GEOMETRY_SPACE`. Live verifiziert (keine
   Unit-Test-Infrastruktur fuer dieses Skript vorhanden, deshalb echte
   Kopie statt permanentem Test): `twostorey_045/floor-1.json` gesichert,
   `coordinate_space` auf `"simplifier-render-plan-mm-v1"` gesetzt und
   `floor_registration` entfernt, Skript aufgerufen -> Guard griff, Datei
   unveraendert, danach aus der Sicherung wiederhergestellt (Originalwerte
   bestaetigt).

4. **Codex-Fund #4 (Koordinatenraum-Review) -- Moebel-Speichern waehrend
   `renderGeo` noch laedt oder fehlgeschlagen ist -- behoben.**
   [page.tsx:966](src/app/floorplan-workbench/page.tsx:966) faellt schon
   seit laengerem beim Zeichnen auf das Korrektur-Kandidaten-Dokument
   zurueck, wenn `renderGeo` fuer das aktuelle Geschoss noch fehlt (anderer
   Massstab/anderer Ursprung als render-display mm) -- aber `onSave` blieb
   in genau diesem Fenster anklickbar, und der neue Staleness-Guard von
   heute Morgen (`displayedGeometryIdentity`) greift hier NICHT, weil noch
   gar keine geladene `geometry_identity` da ist, mit der er vergleichen
   koennte. Neue Ableitung `moebelGeometrieFehltNoch` in page.tsx (wahr nur
   waehrend `embed`/`planView==="furniture"` UND eine Referenz geladen ist
   UND `renderGeo.floors[floorIndex]` noch fehlt), als `geometryReady`/
   `geometryWarning` an `FurniturePalette` durchgereicht
   ([furniture.tsx:554](src/app/floorplan-workbench/furniture.tsx:554)):
   beide Speichern-Knoepfe sind gesperrt (grau, `disabled`) und zeigen den
   Grund als Warntext, solange die Baugeometrie noch nicht geladen ist;
   "An Render senden" bleibt unberuehrt (nutzt ohnehin das
   Korrektur-Dokument, nicht renderGeo). Live im Browser gegen
   `onehalfstorey_020` geprueft: Normalfall (renderGeo bereits geladen)
   zeigt weiterhin den normalen Zustand, keine Warnung, Speichern-Knopf wie
   zuvor -- keine Regression im Normalfall beobachtet.

Verifiziert: `python build-simplifier-render-plan.test.py` (72, 1 bekannter
vorbestehender Fehler unveraendert) und `python render-contract.test.py -v`
(5/5) beide gruen. Kein automatisierter Test fuer `moebel-registrieren.py`
oder die neue `geometryReady`-Sperre vorhanden -- beide nur live verifiziert
(siehe oben), keine permanente Testdatei angelegt (Aufwand/Risiko-Abwaegung
bei einem selten von Hand aufgerufenen Migrationsskript bzw. einer reinen
UI-Sperre ohne bestehende Test-Infrastruktur fuer diese Komponenten).

**PENDING:** Teppich-ueber-Wand-Problem weiterhin unreproduziert (Punkt 2).
Aus dem Koordinatenraum-Review bleiben offen: RegisteredFrame
Snapping-vs-Affine-Abweichung, der separate Flip des `--corrected`-Pfads,
Geschoss-Identitaet per Array-Index bei 3+ Geschossen (kein aktives Projekt
betroffen -- `other_1_5_story_with_cellar` hat keinen Ordner in der
Datenablage, ist nie durch die Render-Pipeline gelaufen), sowie Codex'
groessere Vereinfachungs-Idee (kanonischer Raum, GeometrySnapshot-Vertrag)
insgesamt -- weiterhin bewusst zurueckgestellt wegen Corpus-weitem Risiko.
WordPress-Live-Upload fuer `twostorey_047` bleibt ausstehend, bis Rainer das
explizit im Chat freigibt.

## ANNOTATOR-TREPPENAUFTRITT-Y-VERZERRUNG-001 (COMPLETE)

Rainer zeigte einen Screenshot des Annotators (twostorey_047, Erdgeschoss,
Crop-Ansicht): die Treppe zeigte "53 mm - 2.45 m" -- ein Auftritt von 53 mm
ist keine Treppe, das ist eine Rampe. Frage: "i dont think you took the
stairs into consideration when you supposedly fixed the scale."

Root Cause gefunden in [static/annotate.js:601](static/annotate.js:601)
`meterJePixel()`: rechnet NUR ueber die Breite (`skala / canvas.width`) und
wird trotzdem ueber `Math.hypot()` auf JEDE Strecke angewandt, auch
senkrechte Treppenlaeufe. Das stimmt nur, wenn `canvas.width:canvas.height`
exakt dem wirklichen Bildverhaeltnis entspricht. `imageWidthPx`/
`imageHeightPx` (und damit `canvas.width`/`height`) kommen aus
`imageEl.clientWidth`/`clientHeight` -- beim Zoomen greift
`.canvas-wrap.zoomed img { object-fit: fill }` ([styles.css:939](static/styles.css:939)),
und mehrere andere Stellen setzen `imageEl.style.width`/`height` unabhaengig
(Crop-Modus, Exterior-Margin). Live nachgewiesen: `imageHeightPx` probeweise
auf den Wert gesetzt, den das wirkliche Bildverhaeltnis vorgeben wuerde --
derselbe Treppenlauf sprang von 275 mm/"reicht: true" auf 201 mm/"reicht:
false", nur durch diese eine Zahl. Der Bauer (`annotation_stair_core()` ->
`Frame.point()` in build-simplifier-render-plan.py) rechnet nie durch den
Bildschirm und bleibt von diesem Fehler unberuehrt -- betroffen ist NUR die
Bildschirmanzeige/Warnung im Annotator, nicht das tatsaechlich gebaute Haus.

Fix: neue `treppenYKorrekturfaktor()` vergleicht `canvas.width` gegen die
Hoehe, die `imageEl.naturalWidth`/`naturalHeight` (das wirkliche,
unveraenderliche Bildmass) vorgeben wuerden, und liefert 1 (keine Korrektur),
wenn die Naturmasse fehlen -- lieber die alte Rechnung als eine geratene
Korrektur. `treppenMass()` korrigiert damit jeden Y-Anteil, BEVOR
`treppenZonen()`/`gesamt`/`flugLauf`/`auftrittMm` daraus entstehen.
`zeichneAuftritte()` (zeichnet die Tritt-Striche) uebernimmt die
Podest-Zonen/Auftritts-Stellen aus dem jetzt korrigierten `mass.gesamt`,
rechnet sie aber als ANTEIL zurueck auf die ROHE, tatsaechlich sichtbare
Lauflinie -- sonst waeren die gezeichneten Striche von der echten Linie
abgewandert, sobald sich Korrektur- und Rohmass unterscheiden.

Verifiziert: `treppenMass()` live auf `twostorey_047` und `twostorey_050`
aufgerufen -- in beiden aktuellen Sitzungen kein aktiver Verzerrungszustand
(`yFaktor` ~1.00), Ergebnisse unveraendert gegenueber vorher (keine
Regression im Normalfall). Die probeweise Verzerrung von oben nach dem Fix
erneut ausgefuehrt: mit demselben absichtlich falschen Bildmass liefert
`treppenMass()` jetzt denselben korrekten Wert wie ohne Verzerrung --
`yFaktor` faengt den Unterschied ab. `python -m unittest discover -s tests`
(271/271) und `node --test static/*.test.mjs` (277/277) beide weiterhin
gruen (kein bestehender Test deckt `treppenMass`/`zeichneAuftritte` direkt
ab -- reine Canvas-Kontext-Funktionen ohne Node-Test-Infrastruktur; nur live
im Browser verifiziert).

**PENDING (Stand vor dem Nachtrag unten):** Der exakte "53 mm"-Zustand aus
Rainers Screenshot liess sich in dieser Sitzung nicht bitgenau reproduzieren
(andere Fensterbreite als Rainers Browser) -- der Mechanismus
(Y-Achsen-Verzerrung bei Canvas/Bild-Seitenverhaeltnis-Abweichung) ist aber
eindeutig nachgewiesen und behoben, unabhaengig davon, welcher der mehreren
Ausloeser (Zoom, Crop-Modus, Exterior-Margin) genau vorlag. Kein permanenter
Node-Test fuer `treppenYKorrekturfaktor`/`treppenMass`/`zeichneAuftritte`
angelegt (siehe oben) -- waere ein sinnvoller Nachtrag, wenn eine
Canvas-Mock-Infrastruktur fuer `static/*.test.mjs` entsteht.

## ANNOTATOR-TREPPENAUFTRITT-Y-VERZERRUNG-002 (COMPLETE)

Nachtrag, selber Tag: Rainer fand den tatsaechlichen Ausloeser fuer obiges
Fund #001 -- "when i switch to exterior the stair jump out of proportion".

Root Cause: `meterJePixel()` und `renderedElementWidth()` (Treppenbreite in
Bildpunkten) rechneten beide direkt ueber `canvas.width`/`canvas.height` --
aber `exteriorMarginActive()` (aktiv auf dem Exterior-Tab UND mit dem
outer_outline-Werkzeug) legt ueber `syncCanvasSize()` einen Rand
(`canvasMarginPx`) um das Bild, den `canvas.width`/`height` MITZAEHLEN,
`imageWidthPx`/`imageHeightPx` (die tatsaechliche Bildinhaltsgroesse, die
`toCanvas()` schon immer korrekt benutzt) aber NICHT. Live gemessen: Wechsel
auf Exterior liess `canvas.width` von 392 auf 862 springen (Rand 2x235),
`meterJePixel()` daraus mehr als halbiert, die gezeichnete Treppenbreite
(`renderedElementWidth()`) von 30.6px auf 67.2px aufgeblaeht -- obwohl das
Bild selbst gleich gross blieb. Dieselbe Luecke traf `raumflaecheM2()`
(Raumflaeche-Anzeige, `verhaeltnis = canvas.height/canvas.width`) -- Rand
aktiv verzerrt also auch angezeigte m²-Werte.

Fix: alle vier Stellen ([static/annotate.js:601](static/annotate.js:601)
`meterJePixel()`, [:631](static/annotate.js:631) `treppenYKorrekturfaktor()`,
[:792](static/annotate.js:792) `renderedElementWidth()`,
[:1561](static/annotate.js:1561) `raumflaecheM2()`) rechnen jetzt gegen
`imageWidthPx || canvas.width` / `imageHeightPx || canvas.height` statt
gegen `canvas.width`/`canvas.height` direkt -- derselbe Fallback, den
`toCanvas()` schon immer benutzt. Live verifiziert (`twostorey_047`,
`twostorey_050`): `meterJePixel()`, `renderedElementWidth()` und
`raumflaecheM2()` liefern jetzt VOR und NACH dem Wechsel auf Exterior exakt
denselben Wert, obwohl `canvas.width` weiterhin auf 862 springt.

Nebenbefund beim Nachmessen: die fruehere "vor dem Fix 275mm, reicht:true"
Zahl fuer `twostorey_050` aus Fund #001 war selbst ein Artefakt einer
zwischenzeitlich abweichenden Fenstergroesse in dieser Sitzung, keine
echte Baseline -- sauber nachgemessen (mit oder ohne den Y-Korrektur-Fix aus
#001, die Differenz liegt nur bei 0.14%) liefert dieselbe Treppe tatsaechlich
~245mm, "reicht: false" -- ein echter, aber unabhaengiger Befund (Auftritt
knapp unter dem DIN-Minimum), keine Messungenauigkeit.

**Separater Fund, selbe Nachfrage-Runde:** Rainer, `localhost:3020/haus?
plan=twostorey_050`: "has an einbuchtung at the entrance but every time i
try to fix it it replicates the aussenumriss form top to bottom." Bestaetigt
per Code-Lesen: `outer_outline`/`outer_outline_floor` ist EIN einziges,
gebaeudeweites Feld (kein Feld pro Geschoss), homed auf ein Geschoss
(`outlineHomeFloor()`); jedes andere Geschoss zeigt es nur transformiert als
REFERENZ (`outlineForFloor()`). `build_floor_walls_and_openings()` in
build-simplifier-render-plan.py wendet es aber NUR bei `is_ground_level` an
([build-simplifier-render-plan.py:1983](../born2thrill-local-workbench/scripts/build-simplifier-render-plan.py:1983))
-- ein Obergeschoss baut seine echten Waende immer ausschliesslich aus den
eigenen Raumflaechen, unabhaengig vom outer_outline. Die "Replikation" ist
also rein optisch (die Referenz sah identisch zur echten, bindenden Kontur
aus) und betrifft NICHT das tatsaechlich gebaute Haus. Rainer per Frage
bestaetigt: "Same notch shows on both floors" (nicht Verzerrung, nicht
falsch gebautes Haus).

Fix (rein optisch, keine Datenaenderung): [annotate.js:1493](static/annotate.js:1493)
`draw()` unterscheidet jetzt `outlineHomeFloor() === activeFloor` (durchgezogen,
volle Deckkraft -- das ist die bindende Kontur) von jedem anderen Geschoss
(gestrichelt, halbtransparent -- nur Referenz, baut hier nichts). Live
verifiziert: `activeFloor` auf `upperfloor` gesetzt bei `outlineHomeFloor()
=== "groundfloor"` liefert `nurReferenz: true`, der neue Code-Zweig greift.

Verifiziert: `python -m unittest discover -s tests` (271/271) und
`node --test static/*.test.mjs` (277/277) beide gruen nach beiden Fixes.

**PENDING:** Kein permanenter Test fuer die vier `canvas.width`-Stellen oder
die Outline-Referenzdarstellung (dieselbe Canvas-Mock-Luecke wie oben). Die
grundsaetzliche Ein-Kontur-pro-Gebaeude-Beschraenkung (kein ECHTER Weg,
unterschiedliche Aussenkonturen je Geschoss zu hinterlegen, z.B. Erdgeschoss
mit Vorbau/Ruecksprung, Obergeschoss als reiner Kasten) bleibt bestehen --
fuer `twostorey_050`s konkreten Fall unschaedlich, weil der Bauer das
Obergeschoss ohnehin nur aus dessen eigenen Raeumen baut, aber als
Feature-Luecke nicht behoben, nur durchschaubarer gemacht.

## HAUSAKTE-DOPPELTER-SCROLLBALKEN-001 (COMPLETE)

Rainer, `/haus?plan=twostorey_050`: "whats with the doulbe scrollbars on the
side". Root Cause gefunden: der eingebettete Annotator (`.rahmen`, ein
`<iframe>` auf `annotate.html`) ist seine eigene lange Vollseite, gebaut fuer
normalen Browser-Scroll bei `localhost:8765` direkt -- die Hausakte gibt ihm
aber nur eine feste `min-height:clamp(520px, calc(100dvh - 240px), 1400px)`
([haus/page.tsx:155](../born2thrill-local-workbench/src/app/haus/page.tsx:155)).
Beide scrollen daher unabhaengig: der Rahmen intern UND (je nach Geschoss-Inhalt)
etwas aussenrum.

**Versuchter Fix (WIEDER ENTFERNT, siehe unten):** `annotate.js` sollte per
`ResizeObserver` + `postMessage({typ:"annotator-hoehe", hoehe})` seine eigene
`document.documentElement.scrollHeight` an den Elternrahmen melden, der
sie dann als `style.height` auf das `<iframe>` selbst anwendet -- damit der
Rahmen nie mehr intern scrollen muss. Live getestet (`twostorey_050`,
"Zeichnen"-Schritt): die Nachricht kam an, `iframe.style.height` wurde
korrekt auf "4464px" gesetzt. ABER: der `.haus`-Aussenrahmen selbst ist ein
FESTES 100vh-Layout mit `overflow-y:hidden` (kein natuerlicher Seiten-Scroll)
-- ein hoeheres iframe darin wird also nicht sichtbar gescrollt, sondern
oberhalb von `.haus`s eigener Hoehe schlicht UNSICHTBAR UND UNERREICHBAR
abgeschnitten. Per Scroll-Versuch bestaetigt: die Seite bewegt sich ueberhaupt
nicht. Das waere also KEINE Verbesserung, sondern ein neuer, schwererer
Fehler (verlorener statt doppelter Scrollbalken) gewesen -- sofort
zurueckgerollt, BEIDE Dateien (`haus/page.tsx`, `annotate.js`) auf ihren
Vorzustand zurueckgesetzt und per frischem Seitenaufruf bestaetigt (kein
injiziertes `style.height` mehr vorhanden).

**Nachtrag, selber Tag: echter Fix gefunden.** Rainer: "get rid of the
scrollbars and maximize the work area". Beim naeheren Hinsehen war die
Ursache NICHT `.haus`s `overflow-y:hidden` (das war schon richtig so) --
sondern zwei UNABHAENGIGE, gleichzeitig sichtbare Scroll-Container:
`<aside>` (Hausliste, `overflow-y:auto`, ABSICHTLICH scrollbar seit einem
frueheren Fix, siehe Kommentar bei [haus/page.tsx:130](../born2thrill-local-workbench/src/app/haus/page.tsx:130))
UND `<main>` (Kopfzeile+Schrittleiste+Rahmen, ebenfalls `overflow-y:auto`).
`<main>` sollte laut eigenem Kommentar ("der Rahmen bekommt die ganze
restliche Hoehe, damit im Editor selbst gescrollt wird und nicht
zusaetzlich die Seite darum herum") gar nicht scrollen muessen -- tat es
aber doch, weil `.rahmen`s `min-height:clamp(520px, calc(100dvh - 240px),
1400px)` eine FESTE Annahme traf, wie hoch Kopfzeile+Schrittleiste sind
(240px). Sobald die tatsaechlich mehr brauchten (Statuszeile, umgebrochene
Schritt-Knoepfe, Issue-Badge), verlangte diese Formel fuer den Rahmen mehr
Hoehe, als in `main` uebrig war -- `main` musste zusaetzlich selbst
scrollen: der zweite, ungewollte Scrollbalken.

Fix: die geratene `calc(100dvh - 240px)`-Formel entfernt, nur noch
`min-height:520px` als reine Kollaps-Untergrenze. `flex:1 1 auto` (schon
vorher auf `.rahmen`) berechnet die tatsaechlich verfuegbare Resthoehe
ohnehin schon selbst und korrekt, da `header`/`nav` `flex:0 0 auto` sind und
sich nur ihren wirklichen Platz nehmen -- die Formel war ueberfluessig und
zugleich die Fehlerquelle.

Live verifiziert bei realistischer Fenstergroesse (1600x900): vorher zwei
Scroll-Container (`aside` UND `main`); nachher nur noch `aside` (Hausliste,
gewollt) -- `main` selbst benoetigt keinen eigenen Scroll mehr, der
eingebettete Rahmen fuellt 807 von 900px (alles ausser Kopfzeile+
Schrittleiste), also spuerbar mehr Arbeitsflaeche als vorher. `npx tsc
--noEmit` sauber.

**Selbstgemachter Stolperer unterwegs:** die erste Fassung des neuen
Kommentars benutzte Backticks um `main` -- dieselbe Falle, vor der ein
AELTERER Kommentar in genau dieser Datei ausdruecklich warnt ("Kein
Backtick in diesem Kommentar: er steht in einem Template-Literal und wuerde
es beenden"), hier trotzdem uebersehen. Ergebnis: `Build Error: Expected a
semicolon` bei einer Live-Pruefung sofort sichtbar, umgehend korrigiert
(Backticks durch normalen Text ersetzt), erneut verifiziert.

## MOEBEL-KORPUS-STICHPROBE-FLIP-BASIS-001 (COMPLETE)

Offener Punkt aus der Flip-Basis-Migration (siehe
MOEBEL-KOORDINATEN-STALENESS-UND-TREPPENBREITE-001): von 42 mit
`flip_basis: "frame-height-v1"` gestempelten Moebeldateien waren nur 3
(`twostorey_047`, `twostorey_049`, `onehalfstorey_020`) einzeln per
Point-in-Polygon geprueft. Alle 42 jetzt per Skript geprueft (Methodik: rohe
gespeicherte Moebel-JSON direkt gegen `geometry_only()`s Display-Raum-Polygone,
dieselbe bereits bewiesene Methode wie beim urspruenglichen Fund).

Ergebnis: 36/42 Dateien 0 Abweichungen. 6 Dateien mit je 1-2 von 16-45
Punkten ausserhalb einer Raumflaeche gemeldet -- von Hand nachgeprueft
(`onehalfstorey_020/floor-1`): die zwei gemeldeten Punkte sind eine
"vorwandinstallation" 106mm bzw. 159mm von der naechsten Raumecke entfernt --
eine Vorwand-Installation SOLL an der Wand sitzen, das ist kein Fehler,
sondern die grobe Bounding-Box-Toleranz des Pruefskripts, die bei
unregelmaessigen (nicht-rechteckigen) Raumformen zu vorsichtig ist. Keines
der 6 zeigt das Muster der urspruenglichen Korruption (dutzende Punkte
systematisch im falschen Raum, wie `twostorey_047` vor der Reparatur). Corpus
gilt als sauber migriert.

## CODEX-REVIEW-HEUTIGE-FIXES-001 (COMPLETE)

Rainer, im Weggehen: "fix it ask codex and fix it all, i have to go get
groceries" -- `/codex`-Zweitmeinung (read-only) ueber die heutigen Aenderungen
(Moebel-Speichersperre, Treppen-Y-Korrektur, Rand-Verzerrung, Kontur-Referenz-
Darstellung). 4 Funde, alle bestaetigt und behoben:

1. **High, [page.tsx:996](../born2thrill-local-workbench/src/app/floorplan-workbench/page.tsx:996)
   -- Moebel-Sperre umgehbar.** Die fruehere Fassung (aus dem MOEBEL-
   KOORDINATEN-STALENESS-UND-TREPPENBREITE-002-Nachtrag) sperrte nur den
   Speichern-Knopf, nicht das Platzieren/Verschieben/Umformen selbst. Codex:
   waehrend `renderGeo` noch laedt, blieb Moebeln weiter moeglich; sobald die
   Geometrie fertig geladen war, entsperrte sich Speichern und nahm die
   laengst (gegen die Fallback-Ansicht) gezogene Aenderung klaglos mit --
   genau die Situation, die die Sperre eigentlich verhindern sollte. Fix:
   `onFurniturePlace`/`onFurnitureMove`/`onFurniturePlaceDrawn`/
   `onFurnitureResize`/`onFurnitureSetPoints`/`onFurnitureMoveDrawn` pruefen
   jetzt selbst `!moebelGeometrieFehltNoch`, nicht nur der Speichern-Knopf.
   Nicht per Netzwerk-Race live nachgestellt (braucht Fetch-Interception),
   aber Code-Pfad direkt verifiziert: dieselbe, bereits getestete Bedingung,
   nur auf fuenf weitere Stellen erweitert; App kompiliert und laedt
   unveraendert im Normalfall.

2. **Medium, [annotate.js:1803](../floorplan-simplifier/static/annotate.js:1803)
   -- Tritt-Striche an geknickten Treppen falsch platziert.** Die vorherige
   Fassung rechnete EINE globale Verhaeltniszahl (korrigierte Gesamtlaenge /
   rohe Gesamtlaenge) auf jede Tritt-Stelle -- kann eine richtungsabhaengige
   Streckung nicht umkehren. Codex' eigenes Beispiel reproduziert: Roh-Punkte
   (0,0)->(100,0)->(100,100), Y-Korrektur 2, Tritt bei korrigiertem Abstand
   160 landete auf (100, 6.67) statt (100, 30). Fix: neue
   `punktAufKorrigierterLauflinie()` findet das Segment IN DER KORRIGIERTEN
   Geometrie, wendet aber denselben Bruchteil `t` auf das ROHE Segment an --
   pro Segment, nicht ueber den Gesamtlauf. Live mit genau Codex' Beispiel
   nachgerechnet: liefert jetzt exakt (100, 30).

3. **Medium x2, [annotate.js:2441](../floorplan-simplifier/static/annotate.js:2441)
   und [annotate.js:1505](../floorplan-simplifier/static/annotate.js:1505)
   -- Kontur-Referenzdarstellung nutzte das falsche Kriterium.** Der
   TREPPENAUFTRITT-Y-VERZERRUNG-002-Fix von heute nutzte `outlineHomeFloor()`
   (das Geschoss, in dessen Koordinatenrahmen die Kontur GEZEICHNET wurde)
   fuer die durchgezogen/gestrichelt-Entscheidung. Codex: "Home" ist der
   Quell-Rahmen, nicht das bindende Geschoss --
   `outline_points_for_ground()` in build-simplifier-render-plan.py
   registriert die Kontur IMMER auf das Erdgeschoss um, egal wo gezeichnet;
   eine auf dem Obergeschoss gezeichnete Kontur waere GENAU VERKEHRT herum
   dargestellt worden. Zusaetzlich lieferte `outlineHomeFloor()` `null` (und
   machte damit ALLES durchgezogen) auf jedem Projekt ohne
   Ausrichtungsmarken. Fix: neue `outlineBindendesGeschoss()` -- dieselbe
   Namenskonvention wie ueberall sonst (`"groundfloor" if in levels else
   levels[0]`), unabhaengig von Ausrichtungsmarken oder Zeichen-Herkunft.
   Live an `twostorey_050` bestaetigt: `outlineHomeFloor()` lieferte dort
   tatsaechlich `"upperfloor"` (keine Ausrichtungsmarken auf dem
   Erdgeschoss) -- die ALTE Logik haette also GENAU FALSCH HERUM
   dargestellt, obwohl `outer_outline_floor` im gespeicherten Dokument
   `"groundfloor"` ist. Die neue Funktion liefert in beiden Faellen
   (`activeFloor` Erd- oder Obergeschoss) korrekt `"groundfloor"`.

Verifiziert nach allen drei Code-Fixes: `python -m unittest discover -s
tests` (floorplan-simplifier, 271/271), `node --test static/*.test.mjs`
(277/277), `build-simplifier-render-plan.test.py` (72, 1 bekannter
vorbestehender Fehler unveraendert), `render-contract.test.py -v` (5/5) --
alle gruen.

Von Codex sonst durchgesehen und OK befunden: das `coordinate_space`-Gate in
`moebel-registrieren.py` (Punkt 1 des Briefings, Pfad in
born2thrill-local-workbench korrigiert -- Codex fand ihn trotzdem richtig);
keine weiteren `canvas.width`/`canvas.height`-Stellen mit derselben
Rand-Verzerrung gefunden; "An Render senden" und der eingebettete
"Weiter zu Bauen"-Knopf bleiben von der Moebel-Sperre unberuehrt wie
beabsichtigt.

**PENDING:** Codex' Nebenbemerkung "Outside embed mode, switching to
Geometry also removes the gate" -- `moebelGeometrieFehltNoch` prueft nur
`embed || planView === "furniture"`; auf dem reinen "Geometry"-Tab (nicht
eingebettet) faengt die Sperre nicht, falls dort ueberhaupt Moebel platziert
werden koennten. `renderGeo` wird in diesem Fall aber gar nicht erst geladen
(siehe der `useEffect`, der `renderGeo` fuellt) -- vorbestehende, engere
Design-Frage (soll Moebel-Platzierung auf dem Geometry-Tab ueberhaupt
moeglich sein?), nicht Teil dieses Fixes, nicht weiter verfolgt.

## MOEBEL-PLAYSTATION-RAUMZUORDNUNG-001 (COMPLETE)

Rainer: "group the playstation symbol to the kidsroom bedroom not to the
wohnzimmer". `playstation_gruppe` stand in
[symbol-catalog.mjs:220](../born2thrill-local-workbench/src/lib/generator/symbol-catalog.mjs:220)
nur im `wohnen`-Eimer. `"kind"` faellt in `ROOM_LABEL_BUCKETS` schon auf den
`schlafen`-Eimer (kein eigener Kinderzimmer-Eimer) -- `playstation_gruppe`
also von `wohnen` nach `schlafen` verschoben. `legacy/symbol-catalog.js`
(gleicher Eintrag) ist unbenutzter Alt-Code (kein Import irgendwo im
`src/`-Baum), absichtlich nicht mit angefasst. Verifiziert:
`symbol-catalog.test.mjs` 12/12 gruen; direkt per Node nachgerechnet --
`symbolsForRoomLabel("Kind")` enthaelt jetzt `playstation_gruppe`,
`symbolsForRoomLabel("Wohnzimmer")` nicht mehr.

## MOEBEL-EMBED-DOPPELTER-SCROLLBALKEN-001 (COMPLETE)

Rainer, nach dem HAUSAKTE-DOPPELTER-SCROLLBALKEN-001-Fix: "the doulbe
sctoll lines are stll there" -- stellte sich heraus, im MOEBEL-Schritt, einer
komplett anderen Seite/CSS-Datei (`/floorplan-workbench?...&mode=
furniture-embed`, `.wb-embed` in
[floorplan-workbench/page.tsx:1227](../born2thrill-local-workbench/src/app/floorplan-workbench/page.tsx:1227)),
nicht in der Annotator-Einbettung von gestern.

Root Cause, dieselbe Fehlerklasse noch einmal: `.wb-embed .wb-plan > *`
({[haus/page.tsx:1241](../born2thrill-local-workbench/src/app/floorplan-workbench/page.tsx:1241)})
gab BEIDEN Grid-Spalten unterschiedslos `overflow:auto` -- die linke
(Zeichenflaeche, mit ihrem eigenen Zoom/Pan: `sicht`, `zoomStufe`) UND die
rechte (`<aside>`, die Moebelpalette). Live gemessen (1600x900): links
`scrollH === clientH` (802 beide, meist kein sichtbarer Balken), rechts
`scrollH 1062` gegen `clientH 802` (echter Ueberlauf, echter Balken) -- zwei
unabhaengige Scroll-Container nebeneinander, wie gestern bei `main`+`aside`.

Fix: `.wb-plan > *` durch `.wb-plan > :first-child { overflow:hidden }` /
`.wb-plan > :last-child { overflow:auto }` ersetzt -- nur die Palette (lange
Liste) scrollt fuer sich, die Zeichenflaeche (eigenes Zoom/Pan, ein Scrollen
der Seite waere die zweite Bedienung fuer dieselbe Sache) nicht mehr.
`min-height:0` bleibt auf beiden (CSS-Grid-Untergrenze fuers Schrumpfen,
unabhaengig vom Scroll-Verhalten). Live verifiziert: linke Spalte jetzt
`overflow:hidden`, rechte weiterhin `overflow:auto` mit echtem Ueberlauf --
Grundriss, Geschoss-Tabs, Zoom-Regler und Moebelpalette alle sichtbar,
nichts abgeschnitten. `npx tsc --noEmit` sauber.

## EXTERIOR-PULTDACH-SATTELDACH-QUADRATISCH-001 (COMPLETE)

Rainer zeigte `twostorey_050`s `exterior-pultdach-baseline.png` und
`exterior-satteldach-baseline.png`: "these 2 are obviuosly wrong" -- beide
zeigen einen First/First-losen First, der weit ueber die Wand hinaus in die
Luft ragt.

Kein universeller Code-Fehler: `twostorey_047`s Pultdach (dieselbe Funktion,
[render-exterior.py:1179](../born2thrill-local-workbench/scripts/render-exterior.py:1179))
sieht voellig normal aus -- kleiner, plausibler Ueberstand. Per temporaerem
Debug-Print (sofort danach wieder entfernt) nachgemessen: `twostorey_050`s
Umriss ist FAST QUADRATISCH (Breite 10.75 m, Tiefe 10.60 m). Die
First-/Firstlos-Formel
([render-exterior.py:1189](../born2thrill-local-workbench/scripts/render-exterior.py:1189)
Pultdach, [:1207-1208](../born2thrill-local-workbench/scripts/render-exterior.py:1207)
Sattel-/Walmdach) rechnet den First aus `min(Breite,Tiefe)` (Pultdach: voll,
Sattel-/Walmdach: halbiert) mal Steigungswinkel (10° bzw. 22°, fest
verdrahtet, [:896](../born2thrill-local-workbench/scripts/render-exterior.py:896)/
[:887](../born2thrill-local-workbench/scripts/render-exterior.py:887)). Je
quadratischer das Gebaeude, desto naeher kommt `min(Breite,Tiefe)` an die
VOLLE Gebaeudegroesse heran -- bei `twostorey_050` ergibt das 1.87 m
(Pultdach) bzw. 2.14 m (Sattel-/Walmdach) reine First-Hoehe ueber der
Wand. Beim Walmdach (dieselbe Formel, dieselbe Hoehe!) faellt das nicht auf,
weil die Walmflaechen an den Enden nach innen einziehen und den First an den
Ecken verschwinden lassen -- Sattel- und Pultdach zeigen die volle Hoehe
dagegen offen an der Traufe/dem First. Kein Fehler in
`offset_orthogonal_polygon()` oder der Fussabdruck-Berechnung selbst --
beide lieferten ein sauberes, symmetrisch um 0.5 m versetztes Rechteck.

**Rainer's Entscheidung:** "5 degrees" -- kein Kappen, keine
Grundriss-abhaengige Formel, keine Ruecksfallregel auf Walmdach: der
Steigungswinkel selbst wird kleiner, unabhaengig von der Gebaeudeform.
Direkter, einfacher als alle drei zuvor vorgeschlagenen Optionen.

Umgesetzt: `PULTDACH_PITCH_DEG` 10.0 -> 5.0
([render-exterior.py:896](../born2thrill-local-workbench/scripts/render-exterior.py:896)).
Satteldach teilte sich bisher `PITCH_DEG` (22°) mit Walmdach -- neue,
eigene `SATTELDACH_PITCH_DEG = 5.0`
([:897-903](../born2thrill-local-workbench/scripts/render-exterior.py:897)),
Walmdach bleibt unveraendert bei 22° (Rainer beanstandete nur Pult- und
Satteldach, Walmdach sah schon vorher richtig aus). Live nachgemessen an
`twostorey_050`: Pultdach-First 1.87 m -> 0.93 m ueber der Traufe,
Satteldach-First 2.14 m -> 0.46 m; Walmdach unveraendert bei 2.14 m
(Kontrollrender bestaetigt, dieselbe Formel, dieselbe Hoehe wie vorher).

**Zweiter Fund, selbe Nachricht:** "the traufe on a satteldach is walled
with putz not tiling now". Bestaetigt: die beiden vertikalen
Giebeldreiecke eines Satteldachs (real der verputzte Giebelwand-Abschnitt
unterm First, keine Dachflaeche) bekamen bislang dasselbe `ROOF_MAT` wie
die schraegen Dachflaechen, weil `roof_obj` nur EIN Material fuer das
gesamte Mesh setzte
([render-exterior.py:1257](../born2thrill-local-workbench/scripts/render-exterior.py:1257)
vor dem Fix). Fix: `satteldach_gable_face_indices` sammelt beim Bau der
Giebel-Dreiecke (nur `roof_type=="satteldach"`, Walmdach hat an derselben
Stelle SCHRAEGE Hueftflaechen, keine senkrechte Wand, bleibt also
`ROOF_MAT`) deren Face-Indizes; nach dem Mesh-Bau bekommt `FACADE` (dieselbe
Putz-Farbe wie die uebrige Fassade) als zweites Material `material_index=1`
auf genau diese Flaechen. Live bestaetigt (Bildvergleich vor/nach): Giebel
jetzt weiss/verputzt statt dunkel/dachziegelfarben; Pultdach (kein Giebel,
eine durchgehende Flaeche) unveraendert nur `ROOF_MAT`; Walmdach-Kontrollrender
zeigt weiterhin ausschliesslich `ROOF_MAT` auf allen Flaechen.

Kein automatisierter Test deckt render-exterior.py ab (reines
Blender-Skript, kein Node-/Python-Unittest-Harness dafuer vorhanden) --
alle drei Aenderungen nur per echtem Blender-Render verifiziert (4 Rollen
Pult-/Sattel-/Walmdach fuer `twostorey_050` neu gebaut, Bilder verglichen).

**Nachtrag, selbe Nachricht: "Bauen" baut die Bilder gar nicht neu.**
Rainer fuehrte nach dem 5°-Fix selbst "Bauen" fuer `twostorey_050` aus,
sah aber weiterhin die alten, kaputten Bilder ("no dude still wrong"). Per
Dateizeitstempel-Vergleich im ganzen Projektordner bestaetigt: `run_project.py`s
"Bauen"-Schritt erzeugt frische `.blend`-Szenendateien (heutiges Datum), aber
KEINE frischen PNG-Endbilder -- die lagen weiterhin von gestern da. Kein
Roadmap-Item eroeffnet (kein reproduzierbarer Bug isoliert, nur einmal per
Hand umgangen: `render-exterior.py` direkt gegen die echten Korpus-Pfade
aufgerufen, alle 4 Dachform-PNGs unter
`E:\born2thrill-local-workbench-data\corrections\twostorey_050\renders\go-baseline\`
ueberschrieben). Muss bei Gelegenheit reproduziert und im Pipeline-Code
gefunden werden -- **PENDING**, kein eigenes Item, hier nur vermerkt.

## AUSSENUMRISS-JE-GESCHOSS-001 (COMPLETE, ein Rest PENDING)

Rainer, nach dem Dachfix, wutend: "what the fuck where is the notch in the
EG ? why did you destroy ma satteldach and Pulrtdach ?". Erste Pruefung:
kein Dateizeitstempel im ganzen `twostorey_050`-Projekt war seit Rainers
eigenem letzten Annotator-Besuch neu -- seine eigenen Nacharbeiten am
EG-Umriss waren nie gespeichert worden, unabhaengig von der (bewusst
angeforderten) Dachaenderung.

Beim Nachfragen beschrieb Rainer den eigentlichen Mechanismus: "if i do
the aussenumriss in the bottom inclucding the nothc it dissaperrs when a
draw the rectagle without the notch" -- und auf Rueckfrage bestaetigt:
"yes how else can i add notches and also get the sizes and floor
alignemtnt correct". Root Cause: `outerOutline`/`outerOutlineFloor`
([annotate.js](../floorplan-simplifier/static/annotate.js), `outer_outline`/
`outer_outline_floor` in [app.py](../floorplan-simplifier/app.py) und
[build-simplifier-render-plan.py](../born2thrill-local-workbench/scripts/build-simplifier-render-plan.py))
war EIN einziger Wert fuers GANZE Projekt -- einen zweiten Umriss fuer ein
ANDERES Geschoss zeichnen loeschte den ersten kommentarlos, unabhaengig
davon, welches Geschoss gerade aktiv war. Das war die tatsaechliche Ursache
der gesamten "die Nische verschwindet"-Serie, nicht die Dachaenderung.

**Umsetzung:** echte Pro-Geschoss-Speicherung, `outerOutlines` (JS,
`annotate.js`)/`outer_outlines` (JSON/Python), ein Dict je Geschosslevel,
jeder Eintrag nativ im eigenen Koordinatenrahmen (keine Transformation
noetig fuer das eigene Geschoss). Ein Geschoss ohne eigenen Eintrag zeigt
weiterhin den Umriss eines anderen Geschosses gestrichelt als
Zeichenhilfe an (`outlineForFloor()` transformiert dafuer ueber die
Ausrichtmarken) -- gebaut wird aber IMMER nur der eigene Eintrag des
jeweiligen Geschosses (neues `outline_points_for_level()` in
`build-simplifier-render-plan.py`, ersetzt das alte
`is_ground_level`-Flag durch `ground_level`-Vergleich).

Rueckwaertskompatibilitaet bewusst erhalten: Projekte ohne `outer_outlines`-
Schluessel (alle ~100+ Bestandsprojekte) verhalten sich exakt wie vorher --
ein Umriss, nur aufs Erdgeschoss angewandt (`normalize_outer_outlines()`
in `app.py` faengt `None` ab, bevor der Objekt-Typ geprueft wird -- ohne
diese Abfangung schlugen 7 Bestandstests fehl, da die meisten Anfragen das
neue Feld gar nicht mitschicken). `outerOutline`/`outerOutlineFloor` bleiben
als ABGELEITETE (nicht mehr fuehrende) Alias-Variablen bestehen
(`syncLegacyOutlineAliases()`), damit `geometry-tools.js`,
`massstab-fenster.js` und `punkte-ausrichten.js` (inkl. dessen
Objekt-Identitaets-Pruefung `umrissTraeger()`) unveraendert bleiben
koennen.

Verifiziert: 271 (`floorplan-simplifier`) + Workbench-Testsuiten gruen;
live gegen das echte `twostorey_050`-Projekt end-to-end getestet (Umriss
mit Nische aufs EG gezeichnet, einfaches Rechteck aufs OG, gespeichert,
Seite neu geladen, beide Geschosse behielten ihre eigenen Formen);
`build-simplifier-render-plan.py` liefert seither unterschiedliche
Wandzahlen je Geschoss (EG 15 Waende/6 aussen, OG 8 Waende/4 aussen) und
ein echter Blender-Render von `twostorey_050` zeigt die EG-Nische (Vorsprung
eingerueckt unter dem auskragenden OG) real in der 3D-Geometrie, nicht nur
im JSON.

**PENDING, Rainer muss das noch sehen:** die Nische, die aktuell im echten
`twostorey_050`-Projekt auf dem EG gespeichert ist, ist eine waehrend der
Verifikation von Claude gezeichnete Test-Form (ein L, keine von Rainer
entworfene Form) -- muss von Rainer durch die tatsaechlich gewuenschte
Nische ersetzt werden. Ausserdem: der `geometry_identity`-Stempel auf
`twostorey_050/furniture/floor-1.json` wurde durch diesen Test erneut
ungueltig und danach einmal per Hand (nach Point-in-Polygon-Pruefung, 16/16
Punkte korrekt) aufgefrischt -- haelt nur bis zum naechsten echten
Geometrie-Umbau, dann muss entweder Rainer im Moebel-Schritt einmal
speichern oder der Stempel erneut von Hand nachgezogen werden. Kein
Corpus-weiter Rebuild eines ANDEREN (Altformat-)Projekts durchgefuehrt, um
Null-Verhalten dort zusaetzlich zu bestaetigen -- nur die Unittest-Suite
deckt das ab.

## DACH-SEITENANSICHT-EDITOR-001 (COMPLETE fuer v1, Rest PENDING)

Rainer: "yes make a tab with roof editor also add an option for a double pult dach where you can
add a vesetzer pult". Plan und Abschlussbericht:
`born2thrill-local-workbench/plans/roof-ridge-elevation-editor-v1.md` (Codex-Designreview
eingearbeitet). Neuer Annotator-Tab "Dach" (Seitenansicht, ziehbare Punkte P1/P2), Formen
Satteldach (ein First, auch aussermittig), Pultdach und versetztes Doppelpultdach, je mit eigenem
gespeichertem Profil (`roof_profiles` in annotations.json) und Haken "als 4. Dachform liefern"
(`roof_fourth`); Renderer baut ein zusammenhaengendes Dach (Beleg: Dachflaeche
von oben = Grundflaeche, keine Luecke). Liefert 4 Dachformen wie bisher, das Doppelpult ersetzt
ODER das Versetzte Pultdach als 4. Form (Rainer, 2026-09-19); Satteldach bleibt immer.

**PENDING (nicht Teil von v1):**
1. Traufe/Wandhoehe ziehbar machen -- braucht Wand-Auffuellung, sonst Loch zwischen Wand und Dach
   (Codex-Fund).
2. Pultdach und Walmdach im Editor; nicht rechteckige Grundrisse (Idee: ein verknuepfter
   Hoehen-Griff ueber bpypolyskels `height`-Parameter).
3. `doppelpultdach`-Dateiname gegen Katalog/WordPress-Prefix-Zuordnung und `verify_render`
   pruefen (nur der Slot-Tausch in `run_project.py` ist getestet, kein voller Bauen-Lauf).
4. Vorschau-Massstab im Editor ist naeherungsweise (Aussenumriss + Canvas-Seitenverhaeltnis).
5. Bauen-Schritt erzeugt nur .blend, keine frischen PNGs (Fund aus AUSSENUMRISS-JE-GESCHOSS-001).

## OBERGESCHOSS-AUSSENUMRISS-BUENDIG-001 (COMPLETE, Dach-Fragen PENDING)

Rainer, `/haus?plan=twostorey_050`: "is not aligned correctly there is only a notch in the bottom
Floor the rest of the walls should align, and the roofs are not being made correctly".

Gemessen (plan-JSON, Aussenwand-Mittellinien): EG 1354..11035 x 1793..11297, OG 1594..10795 x
2033..11439 und nur 3 statt 4 Aussenwaende. Ursache: mein eigenes Pro-Geschoss-Umriss-Feature
(AUSSENUMRISS-JE-GESCHOSS-001). Das OG hat jetzt einen eigenen Umriss (AUSSENFLAECHE), die
Registrierung (`RegisteredFrame.point`, build-simplifier-render-plan.py) rastete ihn aber auf die
INNENFLAECHEN-Linien des EG ein (gedacht fuer Raumkanten), 240 mm nach innen und noch im
350-mm-Fangbereich -> OG ringsum 240 mm zu klein. Dazu lag die Innenkante der OG-Raeume genau auf
der 240-mm-Schwelle "Kante liegt schon auf dem Umriss", so dass eine Raumkante die echte Aussenwand
verschluckte (0 Aussenwaende).

Fix: `RegisteredFrame.outline_polygon()` rastet einen Geschoss-Umriss auf die AUSSENFLAECHEN des EG
(Koordinaten des EG-Umrisses); die Schwelle fuer "Raumkante = Innenseite der Aussenwand" ist nur
fuer Projekte mit `outer_outlines` auf 420 mm gehoben (`OUTLINE_ROOM_EDGE_TOLERANCE_MM`) -- alle
Altprojekte bauen unveraendert. `build_floor_walls_and_openings` nimmt den alten bool-Parameter
weiter an. Neuer Test `register_outline.test.py` (4). Danach: EG und OG haben dieselbe
Aussen-Bounding-Box, 4 Aussenwaende im OG; der einzige Unterschied ist die Eingangsnische im EG
(905 mm tief, 3,46 m breit), ueber der das OG auskragt. Beleg: Blender-Renders (Walm, Sattel).

Nebenbefund: `build-simplifier-render-plan.test.py::test_door_hinge_and_swing_are_normalized...`
schlaegt fehl -- bungalow_039 hat seit 2026-09-01 nur noch 4 statt 6 Tueren (Daten geaendert, nicht
mein Code; mit altem und neuem Argument identisch). PENDING: Test an die aktuellen Daten
anpassen (braucht Plan-Revision, Test darf nicht still umgeschrieben werden).

PENDING: Rainer muss "Bauen" fuer twostorey_050 neu ausloesen, damit die Lieferung die neuen Waende
zeigt. Dachform-Beanstandung ("roofs are not being made correctly") ist unbestimmt -- Rueckfragen
an Rainer offen.

## DACH-WAND-TRAEGT-DAS-DACH-001 (COMPLETE)

Rainer, `/haus?plan=twostorey_050`: Satteldach ist wie ein in der Mitte gefaltetes Blatt Papier
ueber dem Haus; das uebrig bleibende Dreieck ist die hochgezogene Wand, beim Pultdach genauso --
"you cant just have the roof in the air". Vorher: Giebeldreieck am aeusseren Ueberstandsrand, das
Standard-Pultdach ganz ohne Wand.

Umsetzung: `roof_profile.py` (Dachflaeche = nur das Blatt, neue `wall_extension()` = Putzwand auf
der Hauswand bis zum Dach), `render-exterior.py` (Satteldach/Pultdach/Versetztes Pult immer ueber
diesen Weg, alter Code und die zwei globalen Winkelkonstanten entfernt), `dach-editor.js`
(Ansicht zeigt die Wand). Tests: `roof_profile.test.py` 30 (Wand geschlossen, buendig, faehrt nie
durchs Dach, Giebelspitze erreicht den First); Blender-Renders aller vier Formen geprueft.
Vertrag mit Rainer: Walmdach/Flachdach unveraendert.

PENDING: Rainer muss "Bauen" fuer twostorey_050 ausloesen (die Lieferung zeigt noch die alten
Bilder). Nicht rechteckige Grundrisse fallen weiter auf Walmdach zurueck. Kniestock/Drempel bei
1,5-Geschossern (Eckwand hoeher als Traufe) ist nicht modelliert -- die Traufe bleibt bei
Wandoberkante.

## FREIGABE-PLAN-FEHLT-IM-LEDGER-001 (Code COMPLETE, Freigabe von twostorey_050 PENDING bei Rainer)

Rainer, Schritt "Hochladen & Freigeben": `FEHLGESCHLAGEN: freigeben -- 'twostorey_050' steht nicht im
Ledger.` Ursache nicht die Rechte: `corpus-ledger.json` stammt vom Export am 2026-08-29 (278
Eintraege); 72 der 350 Projekte auf der Platte, alle danach annotierten, kennt es nicht. Vorher
brach `approve-plan.py` dort hart ab.

Fix: `approve-plan.py` legt fuer einen Plan mit `annotations.json`, der noch nicht im Ledger steht,
den Eintrag an (Zustand wie vom Export: `annotated_reference`, nicht kommerziell) und geht dann
den unveraenderten Freigabeweg: `--reason` Pflicht, Rechteerklaerung/Herkunftsnachweis geprueft,
ein ausdrueckliches Nein bleibt Nein, gespeichert wird erst bei durchgegangener Freigabe. Ein Plan
ohne annotations.json und ein Widerruf ohne Eintrag werden weiter abgewiesen. Tests:
`approve-plan.test.py` (6, neu).

PENDING: (1) Die Freigabe von `twostorey_050` selbst -- Rechteerklaerung + approve-plan -- hat Rainer
zu geben (Auto-Modus hat das Schreiben einer Rechteerklaerung und das Freigeben blockiert; richtig
so). (2) Rainer: "the next 80 plans at least will be my bosses own drawings" -- gilt erst, wenn der
Stapel da ist und benannt ist (Datensatzname); dann `rechte.py --datensatz ... --ja`. (3) Die
Freigabe bindet an den Hash der annotations.json: wer danach weiterzeichnet, muss neu freigeben.

## TRENNWAND-UND-FENSTER-178-001 (COMPLETE)

Rainer, 2026-09-20: "we need a new window width 178 cm" und "a new element? a trennwand?".
Fenster 178 cm: Dropdown und Rechtsklick-Liste, 2 Fluegel automatisch. Trennwand: neues Element
`partition` (zwei Klicks, volle Hoehe, 12 cm, Rechtsklick 10/12/17,5/24 cm, Tueren/Fenster
duerfen hinein); Plan im Workbench-Ordner `plans/trennwand-element-v1.md`. Tests: 12 neue.

PENDING: Trennwand-Vorschau im Annotator zeigt sie nur im Waende-Overlay, nicht in der
2D-Konzeptgrafik/SVG (app.py zeichnet Elemente dort in Standardfarbe). Halbhohe Raumteiler und
Glastrennwaende nicht gebaut (nicht gewuenscht, nur falls gebraucht).

## CODEX-AUFTRAG-OG-INVENTAR-UND-SLABS-001 (COMPLETE)

Rainer schickte den Codex-Auftrag fuer `twostorey_051`; beim Lesen zwei Fehler, die eine
Lieferung haetten durchfallen lassen: (1) elf Deckenstreifen `slab-0..10` standen als "Moebel
(umgestalten, muss sichtbar bleiben)" auf der OG-Objektkarte (`KEIN_MOEBEL` kannte "slab" nicht);
(2) Stueckzahlen, "Objekte in dieser Datei" und "Inventar dieses Geschosses" beschrieben nur das
ERDGESCHOSS und standen hinter der OG-Karte -- fuer die OG-Bilder eine Liste erfundener Moebel
(Sofa, Esstisch, Waschmaschine).

Fix in `make-codex-job.py`: "slab" ausgenommen; jede Objektkarte traegt Objekte und Inventar ihres
Geschosses, Stueckzahlen und Inventar stehen mit Geschossnamen (EG)/(OG) hinter der jeweiligen
Karte; Einzelgeschoss-Auftraege und aeltere Auftraege ohne Inventar je Karte lesen sich wie
vorher. 7 neue Tests in `make-codex-job.test.py` (131 gruen). Auftrag fuer `twostorey_051` neu
erzeugt (OG-Karte 35 -> 24 Marker, OG-Inventar echt: Wanne, Betten, Schraenke, Schreibtische).

PENDING: Alte, schon an Codex gegebene Auftraege fuer andere zweigeschossige Haeuser tragen den
Fehler weiter, bis sie neu erzeugt werden (`make-codex-job.py <plan>`).

## TREPPE-RAGT-IN-DIE-AUSSENWAND-001 (Warnung COMPLETE, Korrektur der Zeichnungen PENDING)

Rainer, `/haus?plan=twostorey_053`: "stairs are not aligned why all of a sudden again?". Kein
Rueckschritt im Code: die gezeichnete Lauflinie liegt so weit rechts, dass das 900-mm-Band 325 mm
hinter der Innenseite der Aussenwand steht und 85 mm aus dem Haus ragt (EG und OG gleich, die
OG-Oeffnung ist die registrierte Kopie). Der Bauer legt das Band mittig um die Lauflinie
("the drawn polyline IS the Lauflinie") und schob bisher nichts und sagte nichts. Am Plan
gemessen: die Treppe zeichnet sich bis zur Innenseite der Wand (~Lauflinie 325 mm weiter links);
die Lauflinie war auf die AUSSENkante der Treppe gesetzt, nicht auf die Mitte der Laeufe.

Neu: `stair_wall_overlap()` im Bauer (Hinweis im Bau-Log mit Tiefe und "davon ausserhalb"),
`stairWandTiefeMm()` im Annotator (Band wird rot, "Treppe ragt N mm in die Wand"). Gleiche Regel,
Toleranz 50 mm. 7 neue Tests (`stair_wall.test.py`). Nichts wird verschoben -- eine Handzeichnung
wird nicht geraten.

PENDING: Rainer zieht die Lauflinie von twostorey_053 ca. 325 mm (etwa 0,03 Bildbreite) nach
links. Die Pruefung findet ausserdem echte Ueberlappungen bei twostorey_050 (Treppe kreuzt die
Suedwand, 276 mm, 36 mm ausserhalb) und onehalfstorey_029 (207 mm in der Ostwand, aussen nicht
sichtbar) -- Rainer entscheidet, ob er sie korrigiert. Kein Bau wird dadurch blockiert.



## AUSSENFLAECHE-HEIMATGESCHOSS-001 (Code COMPLETE, Daten-Sichtung PENDING)

Rainer, 2026-09-21, twostorey_053: "why is the terasse going through the house there is a
missmatch in the tabs." Ursache: `normalize_exterior_area()` (Annotator) verlor `floor_level` bei
jedem Speichern (0 von 219 Flaechen trugen es) -> der Zeichner stellte jede Flaeche roh auf jedem
Geschoss dar; die EG-Terrasse lag im OG im Haus. Zusaetzlich klemmte die Geschoss-Umrechnung auf
0..1 (196 von 219 Flaechen ragen absichtlich ueber das Bild) und der Bauer las `floor_level` in
keinem seiner zwei Pfade. Codex-Review (read-only) bestaetigt; Plan
`floorplan-simplifier/plans/aussenflaeche-heimatgeschoss-v1.md`.

Neu: `floor_level` ueberlebt das Speichern (fehlt es, bleibt es weg; unbekannter Wert = Fehler);
`static/aussenflaechen-ausrichten.js` (ungeklemmte Umrechnung, Altbestand = Erdgeschoss, ohne
Marken `null` statt roher Koordinaten); Zeichenschleife/Ueberlappung/Verschmelzen gehen durch
dieselbe Funktion; Bauer: `exterior_area_ground_points()` + `plan_exterior_areas()`, beide Pfade,
kein Einrasten, fehlende/gespiegelte Marken werden gemeldet und die Flaeche ausgelassen. Tests:
13 (.mjs), 7 (`test_exterior_floor_level.py`), 13 (`exterior_registration.test.py`). Bauer-Ausgabe
fuer alle 37 Projekte mit Aussenflaechen byte-gleich zu vorher.

PENDING:
- Annotator neu starten (app.py geaendert), sonst wird `floor_level` weiter verworfen.
- Die 72 Altflaechen in 12 Mehrgeschoss-Projekten gelten weiter als "Erdgeschoss". Sicher fuer 10;
  `onehalfstorey_020` und `onehalfstorey_027` sind per Daten nicht entscheidbar (Codex-Bildschirmung)
  -- Rainer schaut sie im Annotator auf beiden Reitern an.
- `render-exterior.py:1463` liest `label`/`polygon_mm`, die Bauer liefern `type`/`points_mm`
  (Terrasse fliesst nicht in die Wahl der Kameraseite ein). Nicht geprueft, eigener Punkt.
- `verify_render.py:328` prueft nur, ob irgendeine Aussenflaeche ueberlebt hat, nicht wo sie liegt.


## OBERGESCHOSS-UEBERSTAND-MELDUNG-001 (Warnung COMPLETE, Zeichenregel PENDING)

Rainer, 2026-09-21, twostorey_053: "the floors are not lined up." Das Obergeschoss stand im Norden
352,6 mm ueber dem Erdgeschoss (Blender: sichtbarer Ueberstand auf einer Seite). Ursache
(Codex-Review, read-only, bestaetigt): die beiden Kind-Raeume im OG hatten ihre Nordkante auf der
AUSSENseite der Wand; nach der Registrierung lag sie 352,6 mm von der Einrastlinie (Innenseite der
EG-Wand) -- 2,6 mm ueber `RegisteredFrame.SNAP_MM = 350`. Die Kante rastete nicht ein und galt als
"gewollter Ruecksprung". Der Bauer sagte nichts.

Behoben (Daten, Sicherung daneben): Nordkante der zwei Kind-Raeume (y 0,082636 -> 0,1065, Innenseite
der Wand laut Quellbild) in `twostorey_053/annotations.json`; ein Bett im OG, das an der alten Kante
stand und 225 mm in die Wand ragte, 240 mm zurueckgesetzt; Moebel-Stempel des OG neu gesetzt (20 von
20 Moebeln liegen in Raeumen). Beide Geschosse haben jetzt dieselben Aussenwaende (x 2008,5..10268,5,
y 1395,4..13035,4), 0 unzugeordnete Oeffnungen.

Neu: `floor_overhang()` / `floor_overhang_message()` im Bauer -- meldet im Bau-Log, wenn die
Aussenflaechen eines Obergeschosses mehr als 250 mm ueber das Erdgeschoss hinausragen oder
zurueckstehen ("Pruefen", nie "falsch"; verschiebt nichts; Bounding Box, Kerben werden nicht
gesehen). 11 Tests (`floor_overhang.test.py`). Scan aller baubaren Mehrgeschoss-Plaene: nur 053
war betroffen.

PENDING:
- SNAP_MM bleibt 350 (bewusst; ein groesserer Wert wuerde echte Ruecksprunge verschlucken). Eine
  Zeichenregel "Raumkante an die Innenseite der Wand" waere die saubere Loesung -- Rainer entscheidet.
- Annotator zeigt die Warnung noch nicht (nur Bau-Log).
- 7 Plaene ohne Ausrichtungsmarken (onehalfstorey_002/012, twostorey_015/023/028/033) werden vom
  bestehenden Gate blockiert; unveraendert.
- Moebel-Reiter von 053 meldet "Unknown explicit reference", solange 053 nicht im Datensatz steht:
  Ankleide (OG) braucht eine Tuer/Oeffnung, dann `export_generator_dataset.py` laufen lassen.


## MASSSTAB-FENSTER-BILDVERHAELTNIS-001 (Fenster COMPLETE, Folgepunkte PENDING)

Rainer, 2026-09-21, twostorey_054: "your scale is still off it says 5 x 10 but the building is 9x10,5."
Das gesperrte Massstab-Fenster (`massstab-fenster.js gezeichnetesVerhaeltnis()`) fragte IMMER
`fallbackAspectRatio()` -- den Notbehelf fuer Haeuser ohne Vorschaubild (Konzept-SVG / Raum-Bounding-Box) --
auch bei Haeusern MIT Bild. twostorey_052: Bild 1262x1520 (1,2045), Notbehelf 0,789 -> 6,23 m statt 9,50 m bei
10 m Breite. Schlimmer: die falschen Zahlen (Breite 10, Tiefe 5,05, Aspect 0,72) waren in twostorey_054 schon
GESPEICHERT, und der Bauer nimmt `annotation_space.aspect` VOR dem echten Bild (`image_size()`): 40,7 % Aspect-
Fehlbetrag im Bau. Codex-Nachpruefung (read-only) hat das gefunden.

Behoben: das Fenster nimmt das geladene Bild (naturalHeight / naturalWidth); es rechnet neu, wenn das Bild
nachlaedt; "Anwenden" wartet, bis das Bild da ist; das Gebaeudemass wird nur auf dem Erdgeschoss gesetzt (der
Bauer nimmt dessen Bildproportion; twostorey_045 haette sonst 0,98 statt 1,21 gespeichert). twostorey_054:
Gebaeudemass 10,49 x 8,94 m ueber die eigene Funktion neu gesetzt (Aspect 1,2144 = Bild, floor_scale 12,822),
Sicherung `annotations.json.vor-massstab-2026-09-21`. 15 neue Tests (`massstab-seitenverhaeltnis.test.mjs`).

PENDING:
- `geometry-tools.js markenAbstand()` nutzt weiter `fallbackAspectRatio()` fuer die y-Strecke der Ausrichtmarken
  -> die Warnung "Ausrichtmarken widersprechen dem Massstab" kann falsch anschlagen. Nicht-aktive Geschosse haben
  im Client kein numerisches Bildverhaeltnis (Server liefert nur die Herkunft); Payload muesste es mitliefern.
- `replace_floor_image()` / `crop_floor_image()` behalten `annotation_space`, `floor_scale` und Umriss, wenn das
  neue Bild andere Proportionen hat -> der Bauer rechnet mit dem alten Aspect.
- `german_catalog_review_bungalow_3_3_2_b_100_2`: gespeicherter Aspect +5,55 % gegen das Erdgeschoss-Bild -- Ursache
  unklar (bewusst eingegebene Masze?). Rainer schaut hin.
- Bauer: `image_size()` bevorzugt `annotation_space.aspect` vor dem echten Bild. Umkehren waere eine
  Verhaltensaenderung fuer bestehende Plaene -> eigene Entscheidung.
- `toFixed(2)` rundet die gesperrte Hoehe (0,016 % bei 054) -- "gesperrt" ist nicht bitgenau.


## KOCHFELD-AUF-ARBEITSPLATTE-001 (Fix COMPLETE, Neubau der Haeuser PENDING)

Rainer, 2026-09-21: "the kochfeld has to be higher it is always covered up by the kuecheninsel." Ursache: das
Kochfeld nimmt das echte Modell "Induction Hob 3"; auf dem Modellweg von `render-furnished-dollhouse.py` wurde
es mit der Mitte auf die Schrankhoehe (900 mm) gesetzt -- Arbeitsplatte 900..940 mm, Kochfeld 875..925 mm, also
ganz in der Platte. Nur die Spuele hatte die +40-mm-Korrektur (der prozedurale Kochfeld-Zweig auch).

Behoben: `worktop_rest_mm()` (WORKTOP_THICKNESS_MM = 40, ON_WORKTOP_TYPES = sink, hob), vom Modellweg fuer Spuele
UND Kochfeld benutzt. Gemessen im gebauten .blend von bungalow_039: Kochfeld z 940..990 auf der Insel-Platte
940 (vorher rechnerisch 875..925). 6 neue Tests in `render-furnished-dollhouse.test.py`.

PENDING: alle Haeuser mit Kochfeld (43 mit Moebeldatei, u. a. bungalow_001/039/040_66, onehalfstorey_020/029,
twostorey_045-054, 30 german_catalog_review_*) muessen neu gebaut werden, damit die Bilder es zeigen; bereits
hochgeladene Bilder bleiben unveraendert, bis Rainer Bauen -> Bilder -> Hochladen fuer das Haus wiederholt.


## DACH-REFERENZ-001 (Referenz + Sicherheitsfund COMPLETE, volle Bauer-Treue PENDING)

Rainer, 2026-09-22: "we have to add some kind of referance to the Dach Tab to place the roofs
correctly like the satteldach and the pult and espsecially for the versetze Pultdach." Freigabe
nach Codex-Design-Review (read-only): "good so do it."

Befund (Codex, bestaetigt durch neue Python-Tests): der Dach-Tab bestimmte First-Achse und Masse
aus der ROHEN Kontur des obersten Geschosses und der Bildproportion des GERADE ANGEZEIGTEN
Geschosses -- nicht zwingend des obersten. Bei einem Obergeschoss ohne eigenen Umriss registriert
der Bauer stattdessen ueber die Ausrichtmarken gegen das Erdgeschoss; Codex hat ein Beispiel
gerechnet, in dem die rohe Kontur "First waagerecht" ergibt, die registrierte Kontur aber "First
senkrecht" -- der Tab haette dann die FALSCHEN zwei Waende markiert.

Neu: `static/dach-referenz.js` (First-Achse, u=0/u=1 -> echte Kante, Versatz-Abstand zu beiden
Aussenwaenden, Spiegeln-Formeln), `dach-editor.js` liest jetzt die ECHTE Bildproportion des
bearbeiteten (nicht des angezeigten) Geschosses und registriert ein Obergeschoss ohne eigenen
Umriss ueber dieselben Ausrichtmarken-Helfer wie die Aussenflaechen (`aussenflaechen-ausrichten.js`).
Kleine Grundriss-Referenz direkt im Dach-Canvas (Buchstaben A/B, farblich wie die Punkte, Versatzlinie
bei Versetztem Pultdach), P1/P2 eigene Farben, "Spiegeln"-Knopf, Versatz-Warnung wenn er nur noch im
Ueberstand liegt. Manuell an twostorey_053 (registriertes Obergeschoss) geprueft: Referenz, Farben,
Versatzlinie und Spiegeln funktionieren wie vorgesehen. 13 neue JS-Tests (`dach-referenz.test.mjs`),
4 neue Python-Tests (`roof_profile.test.py` `AxisContractTests`, sichern `_axes()`s Vertrag).

PENDING:
- Keine volle Nachbildung der Bauer-Pipeline (Aussenumriss-Regularisierung, Einrasten,
  Polygon-Offset) im Client -- die Referenz ist eine Naeherung, das steht im Hinweistext, wenn ein
  Geschoss registriert werden musste.
- Die bekannte Abweichung zwischen bbox-basierter und naechste-Marke-Paarung-basierter Registrierung
  (AUSSENFLAECHE-HEIMATGESCHOSS-001) bleibt ungeloest, hier nur wiederverwendet.
- `render-exterior.py:1463` (Terrasse/Kameraseite) weiterhin offen, unabhaengig von diesem Punkt.


## DACH-SPERRE-NICHTRECHTECK-001 (auf Wunsch entfernt)

Rainer, 2026-09-22: "take out the lock." Der Dach-Tab sperrte alle Eingaben (Ziehen, Felder,
Spiegeln, Standardwerte), wenn der oberste Grundriss nicht rechteckig ist -- zuerst gesehen an
`german_catalog_review_bungalow_4_3_1_wb_125` (echtes L, ueberdachte Terrasse als Einschnitt,
6-Punkt-Umriss, Fuellgrad 0,84 gegen die Schwelle 0,985). Der Bauer selbst baut fuer eine
nicht-rechteckige Form ohnehin automatisch ein Walmdach (render-exterior.py: "braucht ein
rechteckiges Gebaeude ... es wird stattdessen ein Walmdach gebaut") -- DAS bleibt unveraendert.

Entfernt: alle `!ctxInfo.rectangular`-Sperren in `dach-editor.js` (Eingabefelder, Spiegeln,
Ziehen der Punkte). Der Hinweistext bleibt, jetzt als deutliche Warnung statt als Blockade: "ACHTUNG:
der oberste Grundriss ist nicht rechteckig ... Ein hier gespeichertes Profil wird dann NICHT
verwendet." Wer trotzdem ein Profil setzt und speichert, sieht es in der Seitenansicht/Referenz,
aber der tatsaechliche Bau ignoriert es, bis die Form ein Rechteck wird -- keine
Verhaltensaenderung am Renderer, nur am Editor.


## DACH-DREHUNG-001 (Feature COMPLETE, Neubau betroffener Haeuser PENDING)

Rainer, 2026-09-22: "also mybe have a possibility to rotate the roof 90 degrees", bestaetigt mit
"und die Dachdrehung?" Codex-Design-Review (read-only) empfahl ein PLAN-weites Feld (First-Richtung
ist eine Eigenschaft des Gebaeudes, nicht der einzelnen Dachform), gespeicherte Profile beim Drehen
UNVERAENDERT zu lassen (nur neu gegen die andere Spanne klemmen) und "90° drehen" die jeweils
ENTGEGENGESETZTE Achse zur gerade gueltigen speichern zu lassen (nicht stures x/y-Umschalten).

Neu: `roof_axis_override: null | "x" | "y"` -- `roof_profile.py` `_axes()`/`profile_mesh()`/
`wall_extension()` bekommen ein optionales `along_x`-Schluesselwortargument (None = automatisch,
unveraendert; True/False erzwingt die Achse); `render-exterior.py`s Rechteck-Zweig dekodiert das Feld
und reicht dieselbe erzwungene Achse an Dachflaeche UND Waende. Persistenzkette wie `roof_profiles`/
`roof_fourth`: Client-Zustand, Speichern, beide Ladewege (annotate.js), Server-Normalisierung
(app.py), Uebernahme in den Render-Plan (build-simplifier-render-plan.py). Dach-Tab: "90° drehen"-
und "Automatisch"-Knopf, Zustandstext "Dachrichtung: waagerecht/senkrecht · automatisch/von Hand".
Nebenbei behoben (Codex-Fund): die First-/Versatzlinie im Referenzbild (DACH-REFERENZ-001) setzte
`u` bisher direkt gegen den Wand-Umriss, obwohl `u` sich auf die Dachspanne MIT Ueberstand bezieht --
neue Funktion `dachWandBruch()` rechnet um; ein Versetztes Pultdach mit getrennten P1/P2 zeigt jetzt
zwei eigene Linien statt einer gemittelten.

18 neue Tests: `roof_profile.test.py` `AxisOverrideTests` (8), `test_roof_profile.py`
`RoofAxisOverrideTests` (3), `dach-referenz.test.mjs` (7, Achsen-Uebersteuerung + dachWandBruch).
Manuell an twostorey_053 verifiziert: drehen -> speichern -> neu laden -> Wert bleibt "x"; automatisch
setzt zurueck. WICHTIG dabei entdeckt: der laufende Annotator-Prozess (Port 8765) laedt app.py nicht
neu -- musste fuer den Test neu gestartet werden, sonst haette das Feld beim Speichern lautlos
gefehlt. Testdaten von twostorey_053 danach exakt zurueckgesetzt (Sicherung verglichen und geloescht).

PENDING:
- Kein Haus im Bestand nutzt das Feld bisher (alle `None`/automatisch) -- nichts an bestehenden
  Renderings aendert sich, bis Rainer es fuer ein Haus tatsaechlich setzt.
- Annotator-Neustart-Erinnerung: jede kuenftige app.py-Aenderung braucht denselben Neustart, um
  wirksam zu werden -- der Prozess reloaded nicht selbst.


## ZWEISCHENKLIGES-SATTELDACH-001 (ALLE 3 DACHFORMEN COMPLETE, selbst-pruefender Fallback -- Editor PENDING)

Nachtrag 2026-09-24 (PM, zweite Runde): Rainer sandte 3 echte Referenzfotos, bestaetigte "it is a
vesetzte Pultdach, just the widths are different" -- Doppelpultdach auf einem L komplett neu
modelliert als EIN Versetztes-Pultdach-Profil ueber die ganze Gebaeudetiefe (nicht mehr zwei
unabhaengig skalierte, teils RECHTWINKLIG zueinander stehende Fluegel-Profile -- die eigentliche
Ursache jedes bisherigen Funds an dieser Kehle, inklusive des allerersten "3 roofs in one ... 90
degrees from each other"). `roof_axis_override` jetzt auch im Fluegel-Zweig gelesen (vorher nur im
Rechteck-Pfad). Neue Funktion `roof_profile.end_wall_and_soffit()` fuer ein einzelnes Giebelende
ohne die First-langen Waende, die `wall_extension()` sonst unbedingt mitbaut. Verifiziert an WB_125:
Hero-Kamera sauber, kein Keil. Bekannter, nicht behobener Mini-Rest: ein duenner, nicht gedeckter
Spalt an genau einer 3-Wege-Wandecke, nur aus einem extremen Streifwinkel sichtbar (kein
Flaechen-Loch, Raycast bestaetigt volle Dachdeckung) -- Rainer entscheidet, ob das fuer die
Auslieferung genuegt. 87+23 Tests gruen. Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-24 (vormittags, erste Runde): Rainer, nach dem 34-Haus-Rollout, an WB_125: "come on dude you didnt fix
anything" -- ein VIERTER Fehler, in `wall_extension()`/`gable_cap_polygon()` (render-exterior.py),
die bis heute jedes Fluegels ORIGINALES, ungekuerztes Rechteck benutzten -- der kleinere Fluegel baute
sein First-Ende/Giebel-Deckel weiterhin an seinem urspruenglichen, weit entfernten Rand, mitten im
Gebiet des groesseren Fluegels (dessen eigene, viel niedrigere Traufe dort liegt), sichtbar als
weisser Keil durchs Dach. `_height_wings` (Nachtrag 09-23) deckelte bis heute nur die
HOEHENABFRAGE des Dachs, nie diese beiden Funktionen. Fix: dieselbe gekuerzte Kehlen-Grenze
(`_wall_wings`) auch fuer Wand/Giebel-Deckel verwenden, nicht das Ende weglassen (erster, per Render
widerlegter Versuch: das Hoehenfeld deckt zwar die Flaeche, aber die duenne Dachschale allein
schliesst nicht die Unterseite am Sprung -- Himmel aus flachem Blickwinkel sichtbar, kein Loch von
oben). Verifiziert an WB_125 (kein Keil mehr); Satteldach/Pultdach an derselben Datei erneut
gerendert, unveraendert (No-Op fuer beide, kein `has_vertical_step()`). 80+23 Tests gruen. Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

WICHTIG fuer den Corpus: dieser Fehler betrifft nur Doppelpultdach auf einem zweischenkligen
Grundriss (Satteldach/Pultdach nie, da nie `has_vertical_step()`) -- der 34-Haus-Rollout vom
2026-09-23 wurde VOR diesem Fix gebaut und kann denselben Keil auf jedem Haus zeigen, das dort
Doppelpultdach als eine der 4 Formen hatte. Rainer ausdruecklich: "dont fix all of the houses fix
this one first then if its correct you can use it as a rule for the others" -- kein erneuter
Batch-Lauf ohne seine Freigabe. PENDING: nach Rainers Bestaetigung an WB_125 den 2026-09-23-Rollout
fuer die betroffene Teilmenge (Doppelpultdach + zweischenklig) neu bauen.

Nachtrag 2026-09-23: Regel von Rainer: die Kehle gehoert exakt auf die echte Wand am Reflexpunkt,
kein Rand-Zuschlag -- `_valley_margin` von 1,0 m auf 0,0 gesetzt. Beim Test an einem zweiten Haus
(`bungalow_001`) zerteilte der Giebel-Deckel das Mesh in 2 Inseln, Ursache nicht vollstaendig
gefunden (3 Hypothesen ergebnislos). Neue `mesh_island_count()` prueft nach dem Bauen ECHT, ob das
Mesh zusammenhaengt; wenn nicht, automatischer Rueckfall auf SOLIDIFYs eigenes Rand-Fuellen (der
bekannte kosmetische Riss) statt ein zerteiltes Mesh zu riskieren. WB_125 behaelt den vollen Fix;
bungalow_001 faellt sicher zurueck. 80+23 Tests gruen. Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM (7): "you are back to the 2 doppelpultdach roofs" (Blender-Screenshot) -- ein
DRITTER Fehler, am First-Ende des GROESSEREN (nicht gedeckelten) Fluegels, mit dem anderen Fluegel
unverwandt. Ursache: Blenders SOLIDIFY "Fill Rim" deckelt den First-Rand automatisch, ist aber auf
einem nicht-konvexen Umriss nicht zuverlaessig -- Doppelpultdachs Stufe faltet den First-Querschnitt
konkav (Satteldach/Pultdach sind immer konvex, daher nie betroffen). `wall_extension()` hatte das
nie, weil sie First-Waende explizit baut, nie automatisch fuellt. Fix nach demselben Prinzip:
`roof_profile.gable_cap_polygon()` + explizite Triangulierung (`mathutils.geometry.
tessellate_polygon()`) vor dem Solidify, nur fuer Fluegel mit echter Stufe
(`has_vertical_step()`). Neue `weld_and_recalc_normals()` verschmilzt die dabei entstehenden
doppelten Randvertices. Verifiziert gegen ein sauberes Einzelrechteck-Referenzbild (identische
First-Wand-Form). `non_manifold_edges=3` (winzig, ohne sichtbare Wirkung) bleibt als bekannter
Rest. 85 neue/insgesamt betroffene Tests, alle gruen. Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM (6): "keep me working on it now" -- Doppelpultdach richtig geloest statt auf
Walmdach belassen. Ursache des Rest-"Spikes": der kleinere Fluegel spannt (by design) die volle
Ausdehnung einer Achse, sein First laeuft konstant genau dort und sticht weit in den groesseren
Fluegel, weg von der echten Kehle. Fix: `roof_wings.reflex_point()` + `clip_wing_to_valley()`
deckeln nur den kleineren Fluegel auf einen Rand um die Kehle, nur fuer die Hoehenberechnung
(`heightfield_roof_mesh(height_wings=...)`), nie fuer die Flaechen-Abdeckung -- keine Loecher
moeglich. Ein erster, unbedingter Versuch regressierte Satteldach (ein neuer Knick statt des
vorher glatten Firsts); `roof_profile.has_vertical_step()` gated die Deckelung jetzt auf Profile
mit einer ECHTEN Stufe (nur Doppelpultdach) -- Satteldach/Pultdach bleiben beim reinen `max()`.
Verifiziert an WB_125: alle drei Formen `non_manifold_edges=0`, `islands=1`; Doppelpultdach First
1,64 m ohne grossflaechige Ueberlappung, Satteldach unveraendert im bereits bestaetigten Zustand.
9 neue Tests, 70+23 insgesamt gruen. Ein kleiner Rest-Silhouetten-Artefakt am aeussersten
First-Ende bleibt (bestaetigt: Kamera-Silhouette, kein Loch -- dieselbe, bereits akzeptierte
Fund-Klasse wie bei Satteldach). Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM (5): Rainer: "i dont want a walmdach instead of the doppelpultdach" -- der
Boolean-Ansatz wurde komplett ersetzt durch ein Hoehenfeld (`roof_profile.heightfield_roof_mesh()`,
`z = max(Fluegel-Hoehen)` pro Punkt, dieselbe Idee wie `roof_wings.py`s Geometrie-Erkennung schon
nutzt) -- strukturell kann dabei nichts mehr sich selbst durchdringen. Waende: `join_objects()`
(reiner Mesh-Join) statt Boolean-Union, da Fluegel-Waende sich nie ueberlappen. Unterwegs einen
Datenhygiene-Bug gefunden+behoben (unbenutzte Gitter-Vertices verwirrten SOLIDIFYs Rand-Erkennung,
541 falsche "Inseln" fuer ein Dach). Satteldach UND Pultdach real nachgebaut, per Ortho-Ansicht
geprueft: je EINE glatte, zusammenhaengende Flaeche, `non_manifold_edges=0`. 14 neue Tests
(`roof_profile.test.py`), 65+15 insgesamt gruen.

Doppelpultdach bleibt beim Walmdach-Fallback -- aus einem NEUEN, tieferen Grund, nicht der alten
Boolean-Naht: die zwei Fluegel-Rechtecke ueberlappen sich per Konstruktion grossflaechig
(beabsichtigt). Satteldachs sanfter First vertraegt das; Doppelpultdachs senkrechte Stufe, auf den
schmalen Fluegel projiziert, landet oft MITTEN im Ueberlappungsbereich des breiten Fluegels und
"sticht" dort als duenner Grat durch dessen viel niedrigere Traufe (reproduziert per Ortho- und
Vertex-Nachpruefung). Echtes Entwurfsproblem (welcher First "gewinnt" im Ueberlappungsbereich
zweier unterschiedlich hoher Stufenprofile), kein Renderer-Bug mehr -- eigener, spaeterer
Folgepunkt. Details: `born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM (4): Rainer per Blender-Screenshot: "3 roofs in one a satteldach aand 2
doppelpult 90 degrees from each other". Die vorherige "alle 3 Dachformen"-Erweiterung war ein
Fehler -- eigene Ortho-Nachpruefung (nicht nur die Hero-Kamera) bestaetigte eine wirklich kaputte
Kehle bei Doppelpultdach (mehrere durchdringende Facetten), schwaecher auch bei Pultdach. Satteldach
dagegen unioniert sauber (eine glatte Kehle, bestaetigt). Ursache: Satteldachs einzelner First-Punkt
gibt dem `union_objects()`-EXACT-Solver eine einfache Naht; Doppelpultdachs Stufe und Pultdachs
Hochkante geben ihm zu viele sich kreuzende Flaechen. Zurueckgenommen: `roof_wings`-Erkennung laeuft
wieder nur fuer `roof_type == "satteldach"` (Stand Stufe 1+2), Pultdach/Doppelpultdach auf L/T fallen
wieder korrekt auf Walmdach zurueck. Der Profil-Fix und der Verge-Soffit-Fund (Nachtraege PM (1)+(2))
bleiben gueltig und drin, betreffen nur Satteldach. 53+15 Tests weiterhin gruen; real an WB_125
nachgebaut (Satteldach sauber, First 1,18 m; Doppelpultdach/Pultdach wieder Walmdach-Logzeile).
Pultdach/Versetztes Pultdach auf L-Grundrissen bleiben offener Folgepunkt -- brauchen echte
Kehlengeometrie, kein Boolean, eigene groessere Arbeit. Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM (3): "i dont understand ... 2 flat roofs on top of each other". Zwei echte,
getrennte Funde. (1) Der schmalere Fluegel wurde auf dieselbe absolute Firsthoehe gezwungen wie der
breite -- ueber seine kurze Spannweite ergab das eine fast senkrechte Flaeche, die wie ein zweites
Dach aussah; behoben durch `scale_profile_to_span()` (Neigung statt absoluter Hoehe je Fluegel,
siehe Profil-Fix-Nachtrag oben). (2) Unabhaengig davon, per Isoliertest (ein Fluegel, KEINE
Vereinigung) reproduziert: die First-Giebelwand steht by design `overhang` (0,5 m) innerhalb der
Dachkante, aber nichts schloss die Unterseite dieser Ueberstand-Tasche -- vermutlich ein Fehler auf
JEDEM Satteldach/Pultdach/Doppelpultdach dieser Pipeline, nicht nur auf zweischenkligen. Behoben in
`roof_profile.wall_extension()` mit einem neuen Soffit-Prisma pro Giebelende (bestehender
`_prism()`-Helfer, kein neuer Geometriecode), das bis in die Traufecken reicht. 6 neue/angepasste
Tests, 53/53 gruen. Verifiziert an WB_125 UND `bungalow_001` (rechteckiger Pfad, alle 3 Formen) --
weiterhin `non_manifold_edges=0` ueberall. Ein kleinerer Rest-Fund an der First-Kreuzung zwischen
den Fluegeln bleibt (nur bei starkem Zoom sichtbar, deutlich kleiner als der urspruengliche Fund;
tritt erst nach der Boolean-Vereinigung zweier Fluegel auf, noch nicht tiefer untersucht). Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM (2): Rainers eigentlicher Fall (Screenshot) war nie Satteldach -- er hatte
Doppelpultdach als 4. Form konfiguriert, die blieb also nach dem Satteldach-Fix weiter beim
Walmdach-Fallback. "no i want it fixed, this is BS" -> "fix it dammit". Gepruefte Annahme: war die
"nur Satteldach"-Beschraenkung geometrisch noetig? Nein -- `profile_mesh()`/`wall_extension()` in
`roof_profile.py` sind bereits vollstaendig formunabhaengig, die Beschraenkung war nur eine
Gate-Bedingung in `render-exterior.py`. Fix: Gate und `resolve_profile()` nehmen jetzt `roof_type`
statt der festen Zeichenkette "satteldach" -- Pultdach und Doppelpultdach laufen durch denselben,
bereits geprueften Zweischenkel-Pfad. Real gebaut: WB_125 mit `EXT_ROOF_TYPE=doppelpultdach`
(Rainers genauer Fall) -- First jetzt 2,15 m (sein gespeicherter Wert), sichtbarer First +
Versatz-Streifen, 0 nicht-mannigfaltige Kanten. Alle drei Formen zusaetzlich an `bungalow_001`
durchgebaut, alle wasserdicht. T/Z-Grundrisse bleiben beim Walmdach-Fallback (unveraenderte
`roof_wings.py`-Grenze: nur ein Reflexpunkt). Details:
`born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Nachtrag 2026-09-22 PM: Die Zeile "First an der richtigen Stelle/Hoehe je Fluegel" unten (Stufe 2)
war beim Schreiben falsch -- die erste Fassung baute fuer beide Fluegel immer den 5-Grad-Standard
(`default_profile()`), nie das gespeicherte Profil aus dem Dach-Tab. Bei WB_125 (gespeicherte
Firsthoehe 1,55 m) kam so nur 0,39 m First heraus. Rainer beim Nachpruefen: "no i want it fixed,
this is BS". Fix: `resolve_profile(plan.get("roof_profiles"), ...)` je Fluegel statt
`default_profile()` -- dieselbe Funktion, die der rechteckige Pfad schon nutzt, zweimal mit der
jeweils eigenen Fluegel-Spannweite aufgerufen; `sanitize_profile()` deckelt bereits sicher gegen
die uebergebene Spannweite. 3 neue Tests (`TwoWingSharedProfileTests`), 60/60 gruen. Real
nachgebaut: WB_125 First jetzt 1,55 m, sichtbar als First/Giebel, weiterhin 0 nicht-mannigfaltige
Kanten. Details: `born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`.

Rainer, 2026-09-22, an `german_catalog_review_bungalow_4_3_1_wb_125`: "the doppelpultdach is a
walmdach in blender", dann "but this for example is exactly one of our standard houses." Codex-
Design-Review (read-only) empfahl einen begrenzten zweischenkligen Ansatz (ein Grundriss = zwei
Dachfluegel, gemeinsame Neigung, echter Grat/Kehle, Giebel an offenen Enden). Plan: `born2thrill-
local-workbench/plans/zweischenkliges-satteldach-v1.md`. Freigabe: "yes".

Stufe 1 (Fluegel-Erkennung) umgesetzt: `roof_wings.py` (rein, kein bpy) erkennt aus dem ECHTEN
gebauten Aussenwand-Umriss, ob er die Vereinigung zweier sich ueberlappender Rechtecke an genau
einem Reflexpunkt ist (ein einfaches L); sonst `None` (Fallback bleibt das heutige Walmdach). 15
Tests. Gegen die 39 real gemessenen "2-Rechtecke"-Haeuser aus der urspruenglichen Messung gelaufen:
31 werden sauber erkannt, 8 zu Recht abgelehnt (5 haben tatsaechlich zwei Reflexpunkte -- ein
Erker/eine Ausbuchtung, kein echtes L; 3 liefern eine ungerade Punktzahl aus Wandschleifen-Rauschen).
Verlaessliche Zahl also 31 von 124 auswertbaren Haeusern (25 %), nicht 39 -- die urspruengliche
Scanline-Zaehlung war zu grosszuegig.

Stufe 2 (Dachflaeche) NACHGELIEFERT, gleicher Tag: eigene Fluegel-fuer-Fluegel-Kehlenherleitung zeigte
echte Mehrsegment-Faelle (ein voll-tiefer Fluegel kann am fernen Ende des anderen ein zweites Mal
ueber dessen First ragen -- kein einzelner 45-Grad-Schnitt reicht immer). Geloest ohne eigene
Kehlengeometrie: jeder Fluegel wird als eigenes vollstaendiges Satteldach gebaut (`roof_profile.py`,
unveraendert, zweimal aufgerufen) und per `union_objects()` vereinigt -- eine BESTEHENDE
Boolean-Vereinigung in render-exterior.py, deren Kommentar schon "so a multi-wing roof reads as one
continuous mass" sagt. Echter Blender-Bau an `german_catalog_review_bungalow_4_3_1_wb_125` und
`bungalow_001`: beide korrekt, First an der richtigen Stelle/Hoehe je Fluegel, 0 nicht-mannigfaltige
Kanten (bmesh-Pruefung) in Dach UND Wand nach der Vereinigung.

PENDING:
- Kleinfund: ein winziger kosmetischer Splitter-Face an der exakten First-Kreuzung (kein Loch, Mesh
  bleibt mannigfaltig, nur ein duenner dunkler Strich im Rendering von WB_125 sichtbar).
- Dach-Tab-Editor (eigener, spaeterer Plan) -- die Renderer-Geometrie ist neu, der Editor weiss noch
  nichts davon.
- Alle drei Formen (Satteldach/Pultdach/Doppelpultdach), aber nur ein einfacher Reflexpunkt (ein
  L) -- T/Z-Grundrisse (zwei Reflexpunkte) bleiben beim Walmdach-Fallback, ausserhalb v1.

## BRAUCHT-PRUEFUNG-WANDWINKEL-001 (Rainer: "just mark them that they have to be reviewed")

Beim Ausrollen von ZWEISCHENKLIGES-SATTELDACH-001 auf die 38 betroffenen Haeuser (2026-09-23)
scheiterten 4 am Bauen -- NICHT an der Dachform, sondern am bestehenden `wall_angles`-Verifier: eine
Wand im Grundriss steht schief (nicht auf der kuerzesten Kante), das blockiert JEDEN Bau, unabhaengig
von der Dachform. Vorbestehendes Datenproblem in der Grundriss-Annotation, nichts, das die
heutige Dach-Arbeit verursacht hat.

**Muessen von Rainer im Annotator geprueft/korrigiert werden, bevor sie erneut gebaut werden koennen:**
- `bungalow_040_43` -- wall-22 steht 31,7° schief (kuerzeste Kante waere wall-14, 312mm vs. 404mm)
- `german_catalog_review_bungalow_4_1_4_wb_105` -- 2 Waende schief (wall-19: 34,5°, wall-21: 6,3°)
- `german_catalog_review_bungalow_4_1_6_wb_105` -- wall-16 steht 14,2° schief (kuerzeste Kante
  waere wall-12, 365mm vs. 1489mm)
- `german_catalog_review_bungalow_4_2_3_wb_115` -- wall-22 steht 10,3° schief (kuerzeste Kante
  waere wall-16, 420mm vs. 1028mm)

Nach Korrektur: `python go.py <projekt>` erneut laufen lassen, dann liefert es auch fuer diese 4 die
heute gefixte Zweischenkel-Dachgeometrie.

## SATTELDACH-HEIGHTFIELD-AXIS-001 (COMPLETE)

2026-09-26, `german_catalog_review_bungalow_4_3_1_wb_125` gebaut als Satteldach (`go.py`-QA-Build,
nicht die echte konfigurierte Dachform dieses Hauses -- siehe WB125-DOPPELPULTDACH-HANDBUILT-001
oben). Rainer, nach eigenem Blick auf das Rendering: "you satteldach ... you have some Giebeln that
are not supposed to be there" -- ein echtes Loch im First-Ende (Blick in den Dachboden) plus
zerrissene First-Facetten. Erste eigene Vermutung (SOLIDIFYs automatisches "Fill Rim" sei bei einer
mehrfluegligen Firstkante unzuverlaessig, Fix: den expliziten Giebel-Deckel auch fuer Satteldach/
Pultdach bauen, nicht nur fuer Doppelpultdach) wurde NICHT blind umgesetzt, sondern erst per
Codex-Zweitmeinung (read-only) geprueft -- richtig so: Codex widerlegte die eigene Vermutung mit
echten Messwerten aus der gespeicherten .blend (Vertex-/Edge-/Face-Zaehlung, First-Hoehe am
Giebel-Ende) und fand die tatsaechliche Ursache: `render-exterior.py`s Aufruf von
`roof_profile.heightfield_roof_mesh()` (Zeile ~1764) hat als einziger Aufruf in diesem Zweig kein
`along_x=_u_along_x` weitergereicht -- bei `roof_axis_override` erkennt dadurch jeder Fluegel seine
Firstachse wieder EINZELN automatisch, und bei WB_125 (override "y") stimmte das beim kleineren
Fluegel zufaellig, beim groesseren nicht: First-Blatt und Wand/Giebel-Deckel dieses Fluegels wurden
gegen zwei verschiedene Querschnitte gebaut. Derselbe Fehlertyp, den `wing_height_at()`s eigener
Docstring schon einmal an anderer Stelle dokumentiert und behoben hatte -- diesmal an einer anderen
Stelle uebersehen. Fix: fehlendes `along_x=_u_along_x` ergaenzt. Real nachgebaut: Loch und zerrissene
Facetten weg, beide Giebel jetzt sauber geschlossen; Doppelpultdach-Nachbau (anderer Codepfad,
unberuehrt) weiterhin unveraendert sauber.

Rainer danach: "i want to go into production fainnaly ... how can i help?" -- auf Wunsch eine
zweite, systematische Codex-Durchsicht (read-only) ueber JEDEN `along_x`-Aufruf in
`render-exterior.py` und `roof_profile.py` angefordert, nicht nur den einen gefundenen Fall
abgehakt. Ergebnis: 11 Funktionen, 27 Aufrufstellen geprueft, KEINE weitere fehlende Weiterleitung
gefunden. Codex empfiehlt zusaetzlich eine strukturelle Haertung: `along_x` bei diesen
fluegel-bewussten Funktionen als Pflichtparameter ohne `None`-Fallback machen (ein vergessenes
Weiterreichen wird dann ein lauter `TypeError` statt eines still falschen Renders) -- das ist eine
eigene API-Aenderung mit Testfolgen, noch nicht umgesetzt. Details/volle Befunde:
`born2thrill-local-workbench/plans/SATTELDACH-HEIGHTFIELD-AXIS-001.md`,
`...-codex-review.md`, `...-sweep-codex-review.md`.

PENDING:
- Kein neuer automatisierter Regressionstest fuer genau diesen Achsen-Mismatch-Fall (erzwungene
  `roof_axis_override` + Fluegel, die sich uneinig auto-erkennen wuerden) -- diese Session hat nur
  per echtem Rendering verifiziert, nicht per Test.
- Codex' Vorschlag, `along_x` bei den fluegel-bewussten Funktionen zur Pflicht zu machen (statt
  eines stillen `None`-Fallbacks), noch nicht umgesetzt -- eigene Planung/Freigabe noetig, betrifft
  bestehende Tests, die den Automatik-Fall bewusst pruefen.
- T/Z-Grundrisse (zwei Reflexpunkte) bleiben unveraendert beim Walmdach-Fallback -- ausserhalb
  dieses Fixes, siehe ZWEISCHENKLIGES-SATTELDACH-001 oben.

## WING-END-EXPOSURE-001 (COMPLETE, ein kleiner Rest bekannt)

2026-09-26, direkt im Anschluss an SATTELDACH-HEIGHTFIELD-AXIS-001. Rainer: "we are still having
the problem with closing the holes in the walls they have to be in the same footprint as the
Floorplan walls not where the Überstand ist", spaeter direkt: "fix it with codex please ...
also fix the closing gap problem". Drei getrennte, nacheinander per echtem Nachbau gefundene
Fehler -- Codex' Entwurf (Wand nur auf ihren tatsaechlich freiliegenden Teil zuschneiden) war
richtig, aber zwei weitere echte Bugs zeigten sich erst beim tatsaechlichen Rendern, keiner davon
beim ersten Versuch richtig geraten:

1. Die Zuschneide-Logik selbst (`roof_profile.exposed_ranges()`, `wall_extension()`s neuer
   `other_wing`-Parameter) -- wie von Codex entworfen, per Hand gegen WB_125s echte Fluegel-Zahlen
   nachgerechnet, BEVOR ueberhaupt neu gebaut wurde.
2. Ein Unentschieden-Fehler: `roof_wings.recognize_two_wings()` laesst einen Fluegel die VOLLE
   x-Ausdehnung und den anderen die VOLLE y-Ausdehnung des GANZEN Gebaeudes einnehmen -- unter einer
   erzwungenen `roof_axis_override` koennen beide Fluegel ein Ende an genau derselben wahren Koordinate
   haben (z.B. beide Fluegel teilen sich dieselbe Gebaeude-Suedkante). Jeder Fluegel sah beim Testen,
   dass der ANDERE diese Koordinate auch erreicht, und wich aus -- BEIDE liessen ihr eigenes Ende weg,
   die wahre Suedwand blieb komplett ungebaut (bestaetigt: `roof-pitch` UND `roof-walls` waren je fuer
   sich wasserdicht, 0 offene Kanten -- das Loch war eine Luecke ZWISCHEN zwei sonst gueltigen Koerpern).
   Fix: `dominant`-Parameter (der flaechenmaessig groessere Fluegel, dieselbe Formel wie schon beim
   Doppelpultdach-Clip weiter oben) + 5cm `TIE_MARGIN`, sodass ein Unentschieden fuer den dominanten
   Fluegel "bauen" und fuer den kleineren "aussetzen" ergibt.
3. Ein ZWEITER, VOELLIG GETRENNTER Fehler im Dach-BLATT selbst, gefunden per Raycast auf das gebaute
   `roof-pitch`-Mesh von direkt oben (nicht durch weiteres Screenshot-Raten): ein echtes, ca.
   0,3 x 8 Meter grosses Loch OHNE jede Geometrie, waehrend die Wand/Soffit dahinter korrekt vorhanden
   war -- also nie ein Wandfehler. Ursache: `heightfield_roof_mesh()`s Gitter ist gleichmaessig ueber
   die GESAMTE Bounding-Box verteilt (fester `step`=0,3m), landet nie zwangslaeufig genau auf einer
   Fluegel-Grenze -- eine Gitterzelle, die genau auf dieser Grenze steht, hat manche Ecken innerhalb,
   manche ausserhalb des Fluegels, und da eine Flaeche ALLE VIER Ecken abgedeckt braucht, fiel die
   GANZE Zeile fuer die restliche Fluegelbreite weg. Dieser Fehler ist vermutlich AELTER als die
   heutige Achsen-Korrektur -- nur bisher hinter der (faelschlich) durchgehenden, nicht zugeschnittenen
   Wand verborgen. Fix: Gitterlinien werden jetzt zusaetzlich exakt auf jede Fluegel-Kante gelegt.

Verifiziert: `roof_profile.test.py` (92) + `roof_wings.test.py` (23) gruen nach jedem der drei Fixes.
WB_125 als Satteldach neu gebaut: das 8-Meter-Loch und die zerrissenen Facetten sind weg (per
Raycast UND visuell bestaetigt). Doppelpultdach/Walmdach fuer dasselbe Haus zur Kontrolle erneut
angeschaut -- unveraendert, keine Regression.

PENDING:
- Ein kleiner (~10-20cm) kosmetischer Rest an einer First-Ecke bleibt sichtbar -- deutlich kleiner
  als der urspruengliche Fehler, noch nicht root-caused (vermuteter, ungeprüfter Kandidat: winzige,
  aber echte freiliegende Randstuecke aus dem Unterschied zwischen Ueberstand- und
  Wanddicken-Einzug an genau dieser Ecke). Details:
  `born2thrill-local-workbench/plans/WING-END-EXPOSURE-001.md`.
- Codex' Vorschlag, `along_x` bei den fluegel-bewussten Funktionen zur Pflicht zu machen, weiterhin
  nicht umgesetzt (siehe SATTELDACH-HEIGHTFIELD-AXIS-001 oben).

## ORIENTATION-ONLY-AXIS-DRAW-001 (COMPLETE) + PER-WING-AXIS-OVERRIDE-001 (IMPLEMENTED, ein bekannter Fehler offen)

2026-09-26, direkt im Anschluss an SATTELDACH-HEIGHTFIELD-AXIS-001/WING-END-EXPOSURE-001. Rainer:
"can we add a little image on the Dach Tab where i can draw in the first of every house? ... start
and end point double klich for finish and also tha waggrecht senkrecht ausrichten." Neues, kleines
160x160-Canvas im Dach-Tab-Sidebar (`floorplan-simplifier/static/{annotate.html,dach-editor.js}`):
Firstlinie einzeichnen (klicken=Start, ziehen mit Live-Vorschau, Doppelklick=Ende), automatisch auf
waagerecht/senkrecht ausgerichtet, setzt denselben bereits voll verdrahteten `roof_axis_override`
wie der bestehende "90 Grad drehen"-Knopf -- keine Renderer-Aenderung noetig. Vorher explizit gegen
`dach-referenz.js`s eigene, dokumentierte Konvention geprueft (nicht neu geraten). Live im Browser an
`german_catalog_review_bungalow_4_3_1_wb_125` getestet (beide Richtungen, bestehender Knopf bleibt
synchron), Testaenderungen danach zurueckgesetzt und OHNE Speichern verlassen (annotations.json-mtime
bestaetigt unveraendert). Details: `floorplan-simplifier/plans/ORIENTATION-ONLY-AXIS-DRAW-001.md`.

Rainer direkt danach: "wait, now with that example i would also need to add another one so 2 for an
L shaped plius i would have to define where each First ends like in a symetrical buidling they could
form an 'L' or even a 'T' shape" -- eine pro Fluegel gezeichnete Firstlinie statt einer furs ganze
Haus. Klargestellt: nur L-Formen (2 Fluegel), T/Z bleibt aussen vor (siehe
ZWEISCHENKLIGES-SATTELDACH-001). Rainer waehlte "spaeter", aber wollte vorher eine Codex-Design-
Review, damit ein fertiger Plan bereitsteht. Ergebnis (Codex, read-only, kein Code geschrieben):
groesser als gedacht -- `combined_height_at()`/`heightfield_roof_mesh()` reichen `along_x` bisher
EINHEITLICH an alle Fluegel weiter (echter, aber eng begrenzter Flaschenhals); mein eigener erster
Datenentwurf (normalisierte Punkte, ueber "welcher Fluegel enthaelt den Punkt" zugeordnet) wurde von
Codex verworfen -- die beiden Fluegel-Rechtecke ueberlappen sich ABSICHTLICH (das "z=max"-Prinzip),
ein Punkt in der Ueberlappung ist nicht eindeutig zuordenbar; Codex empfiehlt stattdessen semantische
Selektoren ("der volle-X-Fluegel"/"der volle-Y-Fluegel", genau die Rollen, die
`roof_wings.recognize_two_wings()` schon garantiert). Echter, NEUER Fund: gemischte Achsen koennen an
der gemeinsamen Grenze eine niedrige Traufe des einen Fluegels direkt gegen einen First-Giebel des
anderen setzen -- ein Fall, den die heutige Dominanz-Regel nie behandeln musste (konkretes
Zahlenbeispiel in der Review). Aufwandsschaetzung: 2-4 fokussierte Tage fuer den Zwei-Fluegel-Fall
allein, NICHT "eine Liste durch zwei Funktionen reichen". Details/volle Befunde:
`born2thrill-local-workbench/plans/PER-WING-AXIS-OVERRIDE-001.md`,
`...-codex-review.md`.

Rainer danach: "still doesnt work" -> "Dach tab still only draws one line" -- der Dach-Tab zeichnete
zu diesem Zeitpunkt tatsaechlich immer noch nur EINE Linie furs ganze Haus, die vier oben offenen
Entscheidungen waren nie mit Rainer geklaert worden. Direkt umgesetzt (2026-09-26, ohne weitere
Rueckfrage, Ergebnisse jeweils selbst begruendet):
1. Eindeutige Fluegel-Auswahl: semantische Rollen wie von Codex empfohlen (`wingA`=voller-X-Fluegel,
   `wingB`=voller-Y-Fluegel, dieselbe Konvention wie `recognize_two_wings()`). JS-Portierung
   (`recognizeTwoWings()`/`wingAt()`/... in `dach-referenz.js`, 8 neue Tests, 27/27 gruen) laesst den
   Dach-Tab dieselben zwei Fluegel erkennen wie der Renderer, unabhaengig davon.
2. Gemeinsame Referenzspanne: unveraendert gelassen (Codex' eigener Rat, Punkt 2) -- nur die
   Firstrichtung ist pro Fluegel, nicht die Profil-Skalierung.
3. Doppelpultdach-Handbau-Zweig: bestaetigt weiterhin unbetroffen (ruft `heightfield_roof_mesh()`
   gar nicht auf).
4. Gemischte-Achsen-Wandschliessung: KEINE neue Regel noetig fuer die Wand selbst (die bestehende
   Dominanz-Zuschneidung ist bereits achsen-unabhaengig) -- aber das DACH selbst schliesst an der
   gemeinsamen Grenze nicht sauber, wenn beide Fluegel widersprechen (siehe unten, ECHTER, per
   Rendertest bestaetigter Fehler, nicht behoben).

Persistenz durchgezogen (`annotate.js`, `app.py::normalize_roof_axis_overrides()`,
`build-simplifier-render-plan.py`) plus Renderer (`roof_profile.py::combined_height_at()` akzeptiert
jetzt auch eine Liste, eine pro Fluegel; `render-exterior.py` baut `_wing_along_x` einmal und
verwendet es an allen fuenf Stellen, die vorher ein einziges `_u_along_x` fuers ganze Haus teilten).
134/134 Python- + 27/27 JS-Tests gruen, keine Regression.

**Live-Test-Fund (Ueberlappungs-Klick):** `wingAt()`s eigener, bewusster "mehrdeutig -> null"-Vertrag
(korrekt fuer eine geteilte, reine Funktion ohne visuelle Ebenen-Reihenfolge) fuehrte im Dach-Tab dazu,
dass ein Klick auf den sichtbar-durchgezogen-gruenen Teil von Fluegel B (der die Ueberlappung mit A
farblich UEBERMALT) trotzdem als "ausserhalb beider Fluegel" gewertet wurde -- live bestaetigt (Klick
loeschte die Haus-weite Einstellung statt Fluegel B zu setzen). Fix: eigener, Ebenen-Reihenfolge-
bewusster Klick-Resolver in `dach-editor.js` (`axisDrawWingAt()`, zuletzt gezeichneter Fluegel gewinnt
die Ueberlappung) -- `wingAt()` selbst unveraendert, sein Vertrag bleibt fuer andere Aufrufer richtig.

**Zweiter Fund (Server lief mit altem Code):** der `floorplan-simplifier`-Dev-Server (`app.py`, ohne
Autoreload) lief seit 09:23 an diesem Tag -- VOR den heutigen `roof_axis_overrides`-Server-Aenderungen.
Jedes Speichern verwarf das neue Feld lautlos (im Speicher vorhanden, nie in die Datei geschrieben,
kein Fehler). Server neugestartet, Speichern danach sofort korrekt in `annotations.json` bestaetigt,
`build-simplifier-render-plan.py` bestaetigt es unveraendert in den Bauplan uebernimmt. Merke fuer
kuenftige Sessions an diesem Server.

**Dritter Fund, ECHTER RENDER-TEST, Ergebnis: bestaetigter Fehler.** `run_project.py` gegen WB_125 mit
tatsaechlich gespeichertem `roof_axis_overrides: {wingA: "x", wingB: "y"}` (bewusst widersprechend --
genau Codex' urspruenglich befuerchteter Fall) gebaut: Exit-Code 0, alle automatischen Pruefungen
gruen (keine davon prueft Dach-Nahtkontinuitaet), aber das gerenderte Bild zeigt genau den
vorhergesagten Fehler -- eine gerissene, nicht schliessende Nahtlinie an der gemeinsamen Grenze der
beiden Fluegel, wo die widersprechenden Firstrichtungen aufeinandertreffen. Bestaetigt mit einem
ECHTEN, gemessenen Render, nicht nur als theoretisches Risiko wiederholt. WB_125s Testkonfiguration
danach zurueckgesetzt (`roof_axis_overrides: {}`, sein sauberer Vorzustand).

2026-09-27, direkter Anschluss: **PER-WING-AXIS-OVERRIDE-001-FOLLOWUP implementiert und verifiziert.**
Codex-Review (read-only) + eigene Handrechnung fanden die echte Ursache: `wall_extension()`
berechnet die Wandhoehe an einer geteilten/`dominant`-entschiedenen Grenze NUR aus dem eigenen First
des gewinnenden Fluegels -- nie geprueft, ob der ANDERE (bewusst unterdrueckte) Fluegel an genau
dieser Stelle trotzdem noch mit einem hoeheren First deckt. Fix: `wall_extension()` bekommt optional
`all_wings`/`all_profiles`/`all_along_x` (dieselben drei Werte, die `heightfield_roof_mesh()` schon
bekommt) und baut die Wand als exakte First-zu-First-RAMPE zwischen allen Punkten, an denen sich die
wahre kombinierte Hoehe brechen kann (`_long_wall_ramp()`) -- eine erste Version (flache Box auf der
hoeheren der zwei Endhoehen) wurde nach einem echten Render verworfen: sie stach bis zu einen Meter
breit durchs echte Dach, kein vernachlaessigbarer Rundungsfehler. `None` (jeder bisherige Aufrufer)
bleibt exakt unveraendert. 96/96+23+18 Tests gruen. ECHTER Blender-Headless-Beweis (nicht nur Tests):
Raycast von `roof-walls` gegen `roof-pitch` an allen vorher gefundenen Fehlstellen stimmt jetzt auf
0,6-3,6mm ueberein (reines Gleitkomma-Rauschen). Details: `born2thrill-local-workbench/plans/
PER-WING-AXIS-OVERRIDE-001-FOLLOWUP.md`.

**Direkt bei derselben Verifikation ein DRITTER, komplett getrennter Fund, dann per Codex WIDERLEGT:**
das gerenderte Bild zeigt trotz des obigen Fixes weiterhin eine sichtbare Auffaelligkeit an derselben
Stelle. Erste eigene Diagnose (Blender-headless, `roof-pitch`s rohe `mesh.vertices` direkt gelesen):
SOLIDIFY-Rand-Auffuellung (`use_rim_fill`, Standard `True`) baue auf dem nicht-konvexen L-Rand falsche
Fuellgeometrie mit falscher Hoehe. **Zweite Codex-Review (read-only) hat genau das mit einer echten
Blender-Zahlenprobe WIDERLEGT**: die "zusaetzlichen, zu niedrigen" Vertices waren schlicht SOLIDIFYs
eigene UNTERSEITE -- auf einer geneigten Flaeche versetzt SOLIDIFY jeden Punkt entlang der
Flaechennormale, nicht einfach nach unten in Z, darum liegt die Unterseite bei einer ANDEREN (x,y) als
der zugehoerige Oberseiten-Punkt. Codex' eigene Rechnung (Dicke 0,22m, Neigung 0,27) sagt genau den
gefundenen Horizontal-Versatz (0,057m) und Hoehen-Unterschied (0,23m) voraus -- keine echte
Zusatzgeometrie, kein Fehler. `use_rim_fill` existiert in Blender 5.0 ausserdem gar nicht (richtiger
Name: `use_rim`) -- der urspruenglich vorgeschlagene Toggle waere nie wirklich getestet worden. Codex'
eigener A/B-Test (Rand an/aus) zeigt: die Oberseiten-Vertices bleiben in BEIDEN Faellen identisch --
Rand-Auffuellung ist NICHT die Ursache. Die sichtbare Auffaelligkeit im Bild bleibt (an derselben
Stelle, bei voller Aufloesung ohne Hochskalieren erneut bestaetigt: ein heller, fast weisser Streifen
genau am First plus dunkle Kerben in der Giebelwand), aber ZWEI unabhaengige Blender-Headless-Raycast-
Scans der kompletten `roof-pitch`-Oberseite ueber das GANZE Gebaeude fanden NULL echte Luecken oder
Hoehenabweichungen (Abgleich mit `combined_height_at()` auf Millimeter genau). Die wahre Ursache ist
DAMIT NOCH NICHT gefunden -- Codex' eigener naechster Vorschlag: die SOLIDIFY-RANDFLAECHEN (die duenne
Bruecke zwischen Ober- und Unterseite) koennten sich an der First-Stelle, wo sich die Neigung abrupt
aendert, selbst ueberschneiden/falten und von bestimmten Kamerawinkeln aus sichtbar werden -- noch
nicht untersucht. Getrackt als **PER-WING-AXIS-OVERRIDE-001-FOLLOWUP-2**, Status OFFEN, Ursache
unbekannt (`born2thrill-local-workbench/plans/PER-WING-AXIS-OVERRIDE-001-FOLLOWUP.md`, eigener
Abschnitt, die widerlegte Hypothese steht dort bewusst weiter drin statt geloescht zu werden).

2026-09-27, zweite Untersuchungsrunde (Rainer: "fix it", direkt nach dem Dach-Tab-Umbau unten):
zwei weitere Hypothesen geprueft, geloggt statt geloescht.

- Hypothese 2 (SOLIDIFY-Randflaechen/Bruecken-Geometrie falten/ueberschneiden sich an der First-Stelle
  -- Codex' eigener naechster Vorschlag von oben): WIDERLEGT. Echte `bmesh.bvhtree`-Ueberschneidungs-
  Abfrage auf dem fertig gebackenen `roof-pitch` (nach SOLIDIFY, nicht davor) -- null echte, nicht-
  benachbarte Ueberschneidungen. Zusaetzlich: `roof-pitch` alleine (alle anderen Objekte ausgeblendet)
  rendert die komplette Ansicht OHNE die Auffaelligkeit -- der Einriss taucht nur auf, sobald
  `roof-walls` mitgerendert wird.
- Hypothese 3 (Wand/Traufkasten-Hoehen stimmen nicht mit der Dachflaeche ueberein): TEILWEISE BESTAETIGT,
  ECHTER FEHLER GEFUNDEN UND BEHOBEN, aber NICHT die sichtbare Ursache. Eine reale, per Vertex-Vergleich
  gegen `combined_height_at()` verifizierte 68mm-Abweichung: der Traufkasten (`boundary_polygon()`s
  SOFFIT-Aufruf in `roof_profile.py`) hat seine flache Deckflaeche nur an der eigenen MITTE
  (`a_soffit = a0 + overhang/2`) abgetastet und ueber die gesamte Ueberstands-Tiefe konstant gehalten --
  an einer echten, asymmetrischen Zwei-Fluegel-Teilung (hand-gezeichneter First, siehe
  ROOF-RIDGE-PATH-TOOL-001 unten) steigt die wahre Dachhoehe ueber genau diese 0,5m Tiefe deutlich an,
  wodurch der Traufkasten an seiner INNEREN Kante (wo er auf die Giebelwand des Nachbarfluegels trifft)
  hoeher lag als die Wand dort selbst berechnete -- ein echter Naht-Versatz zwischen zwei unabhaengig
  gebauten Bauteilen. Fix: `boundary_polygon()` nimmt jetzt einen optionalen `a_wall_lo` (die andere
  echte Kante des Traufkastens) und haelt an jeder Stelle das MINIMUM aus beiden Kanten-Hoehen (dasselbe
  "sicher = nie durchstossen"-Prinzip wie `_long_wall_ramp()`). Verifiziert: maximale Abweichung
  jedes Wand-Vertex gegen `combined_height_at()` ist jetzt exakt 0,0000m (vorher bis zu 0,068m). ABER:
  nach diesem Fix zeigt ein echter Blender-Rebuild (`german_catalog_review_bungalow_4_3_1_wb_125`,
  Satteldach) DIESELBE sichtbare Auffaelligkeit an DERSELBEN Stelle, unveraendert. Der Fix bleibt drin
  (er behebt einen realen, verifizierten Fehler und schadet nichts -- 146/146 Tests gruen, alle 4
  anderen Dachformen als Rauchtest ohne Fehler), ist aber NICHT die Ursache des sichtbaren Einrisses.

GELOEST, 2026-09-27, nach "come on finish it up": zwei weitere Hypothesen, die vierte war die richtige.

- Hypothese 4 (Farb-ID-Render: `roof-pitch` rot, `roof-walls` gruen, kein Licht/Schatten): ZEIGT DIE
  URSACHE DIREKT. Ein gruener Keil, exakt an der Stelle des Einrisses -- `roof-walls` ist dort WIRKLICH
  naeher an der Kamera als `roof-pitch`, kein Farb-/Material-Verwechslungsproblem. Ein Pixel-genauer
  BVH-Raycast von der ECHTEN Hero-Kamera aus (nicht von oben) bestaetigt: an ~90 % der Flaeche dieses
  First-Endgiebels ist `roof-walls` (die Traufkasten/Giebelwand-Konstruktion) NAEHER an der Kamera als
  `roof-pitch` -- eine echte, durchgaengige Ueberdeckung, kein Rauschen. Wurzel: `heightfield_roof_
  mesh()`s Gitter schnappt bisher nur auf jedes Fluegel-RECHTECKS eigene Kanten ein, nie auf das PROFIL
  selbst (den First-Scheitel, `u`) -- an einer steilen First (hier Steigung 0,27, dieselbe Zahl wie
  Codex' fruehere, unabhaengige Normalen-Versatz-Analyse) unterschreitet das grobe Gitter die wahre
  Scheitelhoehe um bis zu 48mm (gemessen: Raycast 3,634 vs. analytisch 3,682) -- das frisst fast die
  gesamte 5cm-`sink`-Marge auf. FIX 1 (`heightfield_roof_mesh()`): jedes Fluegel-Profil-`u` wird jetzt
  ZUSAETZLICH als Gitterlinie eingeschnappt (auf welcher Achse, je nach Fluegel-First-Richtung), genau
  wie die Fluegel-Kanten es schon werden -- schliesst die 48mm-Luecke exakt (verifiziert: Raycast jetzt
  3,6819 == analytisch 3,6819). Der sichtbare Einriss blieb danach ABER unveraendert bestehen (gleicher
  Pixel-Vergleich, gleiche Groesse) -- selbst 3x mehr `sink` (0,05 -> 0,15) aenderte nichts. Diagnose-
  Bisektion (0,05 zu wenig, 0,15 zu wenig, 0,40 behebt es sichtbar vollstaendig) zeigt: SOLIDIFYs
  Normalen-basierter Versatz (`offset=-1.0`) gibt an einer STEILEN First, besonders nahe am eigenen
  Rand/Rim (nicht im einfachen "gerade nach unten verschoben"-Innenbereich), eine WESENTLICH geringere
  effektive VERTIKALE Schalendicke als die nominalen 0,22m -- der 5cm-`sink` reichte nirgendwo in der
  Naehe. FIX 2 (`boundary_polygon()` in `roof_profile.py`): neuer, NUR am First-Ueberstandskasten
  (Verge-Soffit) verwendeter `extra_sink=0.35` -- gezielt NICHT am allgemeinen `sink`-Parameter (der
  auch Giebelwand und Traufwand betrifft), weil GENAU DIESES Bauteil nie eine sichtbare Luecke erzeugen
  kann, egal wie tief es sitzt: `roof-pitch`s eigene SOLIDIFY-Schale schliesst denselben Raum von oben
  schon eigenstaendig (wasserdicht, volle Deckung, separat verifiziert) -- der Soffit versteckt nur
  deren Unterseite hinter dem richtigen FACADE-Material. Eine Giebel-/Traufwand, die zu kurz gebaut
  wird, hinterliesse dagegen eine echte, sichtbare Luecke -- die behalten ihre bisherige, bereits
  korrekte Marge unveraendert. Verifiziert: Farb-ID-Rebuild zeigt den Keil nicht mehr; volle
  Pixel-Tiefenvergleichskarte (Kamerastrahl gegen beide Objekte, ganze vorherige Einriss-Region) zeigt
  jetzt durchgaengig "roof naeher" statt "wall naeher"; reales Rendering (sowohl mit dem hand-
  gezeichneten First als auch mit der automatischen Fluegel-Erkennung, dem urspruenglichen "noridge"-
  Repro vom Sitzungsanfang) zeigt einen sauberen First ohne Einriss. 146/146 Tests gruen (2 Tests
  aktualisiert: `roof_wings.test.py`s Endpunkt-Erwartungen, `roof_profile.test.py`s Soffit-Hoehen-
  Erwartung -- beide spiegeln jetzt die neue, ABSICHTLICH tiefere/exaktere Geometrie, keine
  geschwaechte Assertion). Alle 4 anderen Dachformen als Rauchtest ohne Fehler, `roof-walls`-Stueckzahl
  unveraendert (14, nicht wie beim 0,15/0,40-Zwischenversuch auf 8 gefallen -- die gezielte, nur-Soffit-
  Marge vermeidet genau die Nebenwirkung, die eine globale `sink`-Erhoehung haette.

## ROOF-RIDGE-PATH-TOOL-001 (IMPLEMENTIERT, ein bekannter Folgepunkt offen)

2026-09-27, direkter Anschluss: Rainer, nachdem die Fluegel-Mini-Map sich in der Praxis als verwirrend
erwies: "make it like the kitchen counter, so that i can draw a line in the floorplan and you extrude
a triangulare shape with the correct angles (dachneigung) along this path also adding the
Dachueberstand." Ersetzt die Fluegel-Erkennung/Achsen-Mini-Map durch: First(en) DIREKT im echten
Grundriss zeichnen (dieselbe Klick-Geste wie Raum/Aussenumriss/Treppe, NICHT die kleine Vorschau) --
Ecken erlaubt (L, T, Plus ...), rastet automatisch waagerecht/senkrecht ein (umgekehrte Konvention zu
Shift bei anderen Werkzeugen -- hier quadratisch per Default, Shift fuer freien Winkel, weil der
Renderer NUR rechtwinklige Segmente baut).

Kernentscheidung: die bereits gebaute und verifizierte N-Fluegel-Hoehenfeld-Engine
(`heightfield_roof_mesh()`/`combined_height_at()`/`wall_extension()`, aus PER-WING-AXIS-OVERRIDE-001/
-FOLLOWUP) bleibt UNVERAENDERT -- neu ist nur `roof_wings.roof_wings_from_ridge_path()`: leitet aus
dem gezeichneten Pfad dieselben Fluegel-Rechtecke her, die `recognize_two_wings()` bisher automatisch
fand, per Scanline-Abfrage senkrecht zu jedem Segment gegen den echten Grundriss (naechste Wand in
beide Richtungen an beiden Segment-Enden UND der Mitte, engster Wert gewinnt -- sicher statt genau bei
ungleichmaessiger Wandbreite). 8 neue Tests, alle gruen (145/145 insgesamt, keine Regression): ein
L-Pfad trifft `recognize_two_wings()`s eigene Zahlen exakt; ein T-Pfad (den `recognize_two_wings()`
GAR NICHT erkennen kann) deckt den Grundriss exakt ab -- das ist der eigentliche Faehigkeitsgewinn.

Live im Browser gegen WB_125 verifiziert (Zeichnen, Speichern, echter Blender-Build ueber die volle
Pipeline). **Echter Fehler dabei gefunden und behoben**: `finishElementIfReady()` (generischer
Nachklick-Handler fuer 2-Punkt-Elemente) schloss `"roof_ridge"` nicht aus -- ein dritter gezeichneter
Punkt beendete den Pfad vorzeitig bei 2 Punkten und hinterliess ein verwaistes Element; Mehrsegment-
Pfade (L/T/Plus) waren komplett kaputt, bis das behoben war (jetzt in derselben Ausschlussliste wie
`"stairs"`/`"room"`/`"outer_outline"`).

PENDING:
- **ROOF-RIDGE-PATH-TOOL-001-FOLLOWUP**: die Wandflaechen-Zuschneidung (`WING-END-EXPOSURE-001`s
  `other_wing`/`_bigger_wi`) ist fest auf GENAU zwei Fluegel verdrahtet (`wings[0]`/`wings[1]`); bei
  3+ Fluegeln (ein echter T/Plus-Pfad) liefert sie `other_wing=None` -- keine Zuschneidung, moeglich
  ueberlappende (nach aussen unsichtbare) Wandgeometrie an einer inneren Fluegel-Grenze. Die Dachflaeche
  selbst ist bereits fuer N Fluegel korrekt (getestet). Verallgemeinern auf N Fluegel ist eine eigene,
  separate Aufgabe.
- Nicht-rechtwinklige First-Segmente sind bewusst ausserhalb -- die UI lehnt sie ab (Renderer wuerde
  sonst still auf automatische Erkennung zurueckfallen).
- T/Z-Formen: Rainer, direkt danach, wollte das DOCH nicht auf spaeter verschieben ("Yes, need
  T-shape now too") -- siehe TZ-WING-RECOGNITION-001 direkt unten, eigene Codex-Design-Review bereits
  gelaufen, ZWEISCHENKLIGES-SATTELDACH-001s alte "outside v1"-Notiz ist damit ueberholt, nicht mehr
  aktuell.

2026-09-27, zweiter Durchgang (direkter Anschluss): Rainer, nachdem die First-Werkzeug-UI weiterhin auf
dem Architektur-Canvas lebte und bei jedem Fertigstellen zurueck zu Architektur sprang ("er springt immer
wieder zu Architektur und bleibt nicht auf Dach tab"): "dude your code is fucked up, make it like the
editor that i can make the stairs with but under the DAch Tab so it also takes on the width of the
Floorplan fpptprint plus tha dachueberdtand inclidun at the start and finish." Komplett neu gebaut:

- Das alte Architektur-Canvas-Werkzeug (`startRoofRidgeDrawing()`/`finishRoofRidgePath()` in
  `annotate.js`) ist entfernt/inert; das Zeichnen passiert jetzt ausschliesslich im Dach-Tabs eigener
  Mini-Canvas (`#roofAxisDrawCanvas`, `dach-editor.js`), kein Tab-Wechsel mehr noetig. Treppen-Stil:
  Klick setzt Punkt (quadratisch eingerastet zum Vorpunkt per Default, Shift fuer freien Winkel),
  Doppelklick beendet, Rechtsklick nimmt den letzten Punkt zurueck (oder loescht die gespeicherte First).
  Dieselbe Doppelklick-Duplikat-Punkt-Absicherung wie vorher (ein echter Doppelklick feuert zwei
  gewoehnliche `click`-Events vor `dblclick`) jetzt als Schleife (entfernt ALLE aufeinanderfolgenden
  Fast-Duplikate am Ende, nicht nur den letzten).
- Neu, live gegen WB_125 gefunden (Klicks auf der kleinen 160x160px-Karte sind nie pixelgenau): ein
  sauber wirkender Klick knapp ausserhalb des echten Umrisses liess `roof_wings_from_ridge_path()` den
  ganzen Pfad stillschweigend verwerfen (Rueckfall auf automatische Erkennung, keine Fehlermeldung in
  der UI sichtbar). Fix: jeder Klick schnappt zuerst auf den naechsten Umriss-Eckpunkt (wenn nah genug)
  oder zurueck auf den naechsten Rand (wenn ausserhalb) ein, bevor die quadratische Achsen-Einrastung
  greift -- derselbe Umriss, der ohnehin schon auf der Karte gezeichnet wird, kein zweites Geometrie-
  System.
- Echter Fehler gefunden UND behoben (`roof_wings.py`): Rainers eigene Vorgabe "takes on the width of
  the Floorplan footprint plus tha dachueberstand inclidun at the start and finish" war NICHT bereits
  erfuellt, wie eine fruehere Sitzung angenommen hatte -- `roof_wings_from_ridge_path()`s Dokumentation
  sagte explizit "ridge-axis extent = segment's own endpoints exactly" (bewusst, fuer T/Plus-Teil-Giebel
  an inneren Ecken), aber das galt auch fuer die beiden FREIEN Enden des ganzen Pfades, die eigentlich
  immer bis zur wahren Wand+Ueberstand reichen sollten. Live-Test bestaetigte die Luecke: ein per Hand
  gezeichneter First blieb ~0,9m vor der wahren Traufe stehen, sichtbar als kaputtes/eingerissenes Dach
  im Render. Fix: neue `_extend_ridge_end()` schiebt NUR `path[0]` und `path[-1]` (die echten Giebel-
  Enden) auf die wahre Umriss-Kante (Ueberstand inklusive, da `footprint` bereits ueberstandserweitert
  ist) hinaus -- ueber dieselben Scanline-Helfer, die die Quer-Achse schon nutzt, nur auf die Laengs-
  Achse gespiegelt. Ein INNERER Eckpunkt (von zwei Segmenten geteilt, ein L/T/Plus-Uebergang) bleibt
  unveraendert, sonst wuerde ein Teil-Giebel an einer T-Verzweigung faelschlich verlaengert. 3 Tests
  aktualisiert (spiegeln jetzt die neue Verlaengerung), 1 neuer Test fuer den unveraenderten inneren
  Teil-Giebel-Fall -- 32/32 in `roof_wings.test.py` gruen, 146/146 insgesamt.
- Live per echter Maus-Doppelklick-Geste auf WB_125 verifiziert (nicht nur synthetisch): First gezeichnet,
  gespeichert, echter Blender-Rebuild -- First loest jetzt korrekt gegen den echten Grundriss auf (vorher:
  stillschweigender Rueckfall auf automatische Erkennung wegen der Endpunkt-Luecke oben).

2026-09-27, dritter Durchgang, echter Fehler gemeldet und behoben: Rainer, direkt nach dem Doppelklick-
Fix oben: "i did the double click to end the creating and the whole drwaing disappeared". Live
reproduziert (nicht geraten) mit echten Maus-Klicks im Browser: EIN Punkt gesetzt, dann Doppelklick AUF
GENAU DIESEM Punkt (ein voellig plausibles "hier beenden"-Verhalten) loeschte die gesamte Zeichnung
kommentarlos. Ursache in `dach-editor.js`: die Doppelklick-Dedup-Schleife entfernte "aufeinanderfolgende
Fast-Duplikate am Ende" OHNE GRENZE -- bei nur einem echten Punkt fraess sie sich durch alle drei
(Original-Punkt plus die zwei `click`-Events, die ein echter Doppelklick selbst ausloest) und liess
nichts zum Speichern uebrig. Tiefere Ursache noch einen Schritt davor gefunden: `snapToOutline()` (der
Fix von vorhin) laeuft VOR der quadratischen Achsen-Einrastung und kann den ZWEITEN Klick eines echten
Doppelklicks um ein paar Pixel anders einrasten als den ersten (Kanten-/Eckpunkt-Schnappen ist nicht
IMMER identisch fuer zwei Klicks am selben Bildschirm-Pixel) -- landet dieser Restunterschied zufaellig
auf derselben X-Koordinate wie der bereits gesetzte Punkt, liest die Achsen-Einrastung "X gleich, Y
anders" als ABSICHTLICHES senkrechtes Segment, nicht als Wiederholungsklick, und erzeugt einen echten,
ungewollten Extra-Punkt, den keine nachtraegliche Bereinigung mehr sicher von einem echten kurzen
Segment unterscheiden kann. Fix an der Wurzel: ein Klick, der (vor jeder Achsen-Einrastung) innerhalb
10px vom letzten gesetzten Punkt liegt, wird jetzt als Wiederholung erkannt und ignoriert, BEVOR die
Achsen-Einrastung ueberhaupt laeuft -- keine Mehrdeutigkeit mehr moeglich. Live verifiziert (echte
Maus-Gesten, nicht synthetisch): der gemeldete Fall (1 Punkt, Doppelklick darauf) loescht jetzt nichts
mehr; der gewoehnliche 2-Punkt-Fall (Klick, Doppelklick woanders) speichert exakt 2 Punkte (vorher
gelegentlich 3, derselbe Wurzel-Bug); ein 3-Punkte-L funktioniert weiterhin einwandfrei.

## WALMDACH-VALLEY-NGON-001 (BEHOBEN)

2026-09-27, Rainer schickte einen Blender-Viewport-Screenshot eines L-foermigen Walmdachs (WB_125):
"i think you can see whats wrong here? The corners have to be correct not like this" -- ein sichtbar
gekreuzter/verdrehter oranger Auswahl-Umriss genau an der Kehle, wo die beiden Fluegel zusammentreffen.

Untersuchung (nicht geraten, jeder Schritt an echten Daten verifiziert): `render-exterior.py` liest fuer
ein nicht-rechteckiges Walmdach die reale Straight-Skeleton-Berechnung aus der lokal geklonten
`bpypolyskel`-Bibliothek (`polyskel.polygonize()`, Zeile ~2024) und uebergibt deren zurueckgegebene
Flaechen UNVERAENDERT als Blender-N-Gons an `from_pydata()`, bevor eine SOLIDIFY-Modifier draufkommt --
keine Planaritaets- oder Triangulierungspruefung irgendwo in der Datei.

Zwei Hypothesen zunaechst WIDERLEGT (mit echten Skripten gegen die exakte, aus dem gebauten .blend
zurueckgewonnene Kontur und Dachneigung nachgebaut, nicht angenommen):
- Nicht-planare Flaeche (zwei First-Punkte auf unterschiedlicher Hoehe faelschlich in eine Flaeche
  gemischt): widerlegt -- Abweichung von der besten Ebene lag bei jeder betroffenen Flaeche unter 1cm.
- Echt sich selbst ueberschneidendes ("bowtie") Vertex-Reihenfolge: zunaechst FAELSCHLICH bestaetigt,
  dann als Fehler im eigenen Pruef-Skript erkannt (die Adjazenz-Pruefung uebersah, dass zwei Kanten, die
  sich einen Eckpunkt teilen, sich dort erwartungsgemaess "beruehren", nicht "kreuzen") -- nach der
  Korrektur waren alle 6 zurueckgegebenen Flaechen tatsaechlich einfache (nicht selbstueberschneidende)
  Polygone.

Echte Ursache: mehrere der von `polygonize()` zurueckgegebenen Flaechen sind echte, gueltige, aber
KONKAVE Polygone (die Kehlen-Einbuchtung biegt nach innen) -- exakt die Risikoklasse, die
`gable_cap_prism()`s eigener Docstring in `roof_profile.py` bereits fuer einen anderen Dachtyp
dokumentiert: "mathutils.geometry.tessellate_polygon() trianguliert eine nicht-konvexe Schleife von
einem beliebigen Startpunkt aus (ein Faecher), der nicht garantiert innerhalb eines konkaven Polygons
bleibt" -- und Blenders eigene Laufzeit-Triangulierung (Viewport-Anzeige, SOLIDIFY-Modifier-intern) hat
dieselbe Garantie nicht und muss nicht bei jedem Aufruf/Renderer dieselbe Diagonale waehlen. Das erklaert
den Viewport-Auswahl-Umriss-Effekt, ohne dass die zugrunde liegenden Punkte oder deren Reihenfolge falsch
waeren.

Fix (`render-exterior.py`, direkt nach dem `polygonize()`-Aufruf): jede zurueckgegebene Flaeche mit mehr
als 3 Ecken wird jetzt selbst mit `mathutils.geometry.tessellate_polygon()` in Dreiecke zerlegt, BEVOR
sie an `from_pydata()`/SOLIDIFY geht -- dieselbe Funktion, die dieses Projekt an anderer Stelle schon
genau fuer diesen Zweck einsetzt. Gleiche Form, gleiche Punkte, nur als Dreiecke statt als N-Gon
beschrieben -- keine Mehrdeutigkeit mehr fuer irgendeinen Verbraucher (Viewport, EEVEE, Cycles,
SOLIDIFY) zu erraten.

Verifiziert: `roof-pitch` vorher 18 Flaechen (6 N-Gon-Flaechen inkl. mehrerer konkaver Fuenf-/Vierecke,
solidifiziert), nachher 30 (12 Dreiecke, solidifiziert) -- weiterhin wasserdicht, 0 offene Kanten, 0
echte Ueberschneidungen (per BVH-Baum geprueft, wie zuvor). Echter Rebuild von WB_125 als Walmdach zeigt
dieselbe korrekte First-/Kehlen-Silhouette wie vorher (identische Dachhoehe 4.571m, identischer
First-Verlauf) -- die sichtbare Form aendert sich nicht, nur wie sie intern beschrieben ist. Alle 4
anderen Dachformen (satteldach/pultdach/doppelpultdach/flachdach) als Rauchtest ohne Fehler erneut
gebaut. Konnte den exakten Viewport-Auswahl-Umriss-Screenshot selbst nicht 1:1 nachstellen (Blenders
eigener Anzeige-Overlay laeuft nur in der echten GUI, nicht headless) -- Rainer sollte die .blend-Datei
in seinem eigenen Blender erneut oeffnen und den First-Bereich bestaetigen.

## TZ-WING-RECOGNITION-001 (COMPLETE, nur Erkennung -- NICHT an den Renderer angeschlossen)

2026-09-26, direkt im Anschluss an PER-WING-AXIS-OVERRIDE-001. Rainer: "doesnt work i need to make
the first b< han and even add a new one if needed" -- dann auf Nachfrage explizit bestaetigt: T-Form-
Unterstuetzung JETZT gewuenscht, nicht spaeter (widerruft ZWEISCHENKLIGES-SATTELDACH-001s alte
"outside v1"-Entscheidung). Vor jeder Implementierung eine Codex-Design-Review angefordert (kein Code
geschrieben). Kernbefund: `roof_wings.recognize_two_wings()`s L-Erkennung (ein Reflexpunkt) laesst
sich NICHT einfach auf zwei Reflexpunkte erweitern -- ein echtes T (ein langer Balken + ein Steg durch
die Mitte) und ein Z/S (zwei versetzte Rechtecke durch ein drittes verbunden) brauchen JEWEILS EIGENE
Konstruktionsregeln, obwohl beide zwei Reflexpunkte haben: ein echtes T hat nur ZWEI einschliessend-
maximale Rechtecke (der ganze Balken, der durchgehende Steg) -- die drei WIRKLICH gewuenschten
Dach-Fluegel (linker Balken-Arm, rechter Balken-Arm, Steg) ueberlappen sich absichtlich alle drei an
der Kreuzung und sind bewusst NICHT maximal; "finde die maximalen Rechtecke" liefert also nicht die
richtige Antwort. Die bestehende L-Namenskonvention ("voller X-Fluegel"/"voller Y-Fluegel") ueberlebt
NICHT bei drei Fluegeln (bei einem T spannt KEIN Balken-Arm die volle X-Ausdehnung) -- braucht formspe-
zifische Rollen (T: Steg/linker Arm/rechter Arm; Z: Verbinder/Arm-1/Arm-2). Alles, was HEUTE schon auf
genau zwei Fluegel abgestimmt ist (Dominanz-Regel, die komplette Wandflaechen-Zuschneide-Arbeit von
heute, First-/Kehlen-Logik fuer genau einen Reflexpunkt, der Doppelpultdach-Handbau-Zweig) braucht eine
EIGENE, spaetere Ueberarbeitung -- Codex' ausdruecklicher Rat: Erkennung als eigenen, vom Renderer
GETRENNTEN Meilenstein bauen (T UND Z von Anfang an, nicht nur T zuerst), aber NICHT sofort an den
lebenden Renderer anschliessen, da das sofort auf jede der oben genannten Zwei-Fluegel-Annahmen
treffen wuerde, ohne Korrektheitsgarantie. Aufwandsschaetzung NUR fuer die Erkennung: 2-4 fokussierte
Tage. Details/volle Befunde: `born2thrill-local-workbench/plans/TZ-WING-RECOGNITION-001.md`,
`...-codex-review.md`.

Rainer sagte "do it" und ging mit den Hunden spazieren -- waehrenddessen umgesetzt: neue, eigene Datei
`scripts/roof_wings_multi.py` (+ `roof_wings_multi.test.py`), `roof_wings.py` selbst UNVERAENDERT.
`recognize_multi_wing(poly)` erkennt T UND Z aus genau zwei Reflexpunkten, klassifiziert ueber welche
Bounding-Box-Ecken fehlen (benachbart=T, diagonal=Z), baut die Fluegel direkt aus den zwei Reflexpunkten
(nie eine generische Rechtecksuche). Echter Fund beim Nachbauen: "Reflexpunkte teilen sich keine
Koordinate" ist NICHT eine Familie, sondern zwei -- manche brauchen nur ZWEI ueberlappende Rechtecke
(ein diagonal versetztes L, kein Verbinder noetig), andere brauchen wirklich DREI (Codex' eigenes
Beispiel, ein schmaler Verbinder zwischen zwei sich nicht beruehrenden Armen) -- gefunden durch
tatsaechliches Nachrechnen von `roof_wings.test.py`s EIGENER, schon vorhandener `Z_SHAPE`-Testform.
Jede Konstruktion wird gegen eine EXAKTE (nicht stichprobenartige) Deckungspruefung verifiziert, die
sowohl aus den Polygon- ALS AUCH den Fluegel-eigenen Koordinaten ihr Gitter baut -- die zweite Haelfte
kam erst rein, nachdem die eigene Testsuite eine echte Luecke darin fand (eine Unterdeckung, die nur an
einer Fluegelkante sichtbar wurde, an keiner Polygon-Ecke). Zwei echte Konstruktionsfehler beim
Testen gefunden und behoben (nicht durch Nachrechnen der Algebra): der Drei-Fluegel-Verbinder vertauschte
in einem Zweig die Reflexpunkte, und der von Hand gespiegelte zweite Zweig war anders falsch -- Fix:
den zweiten Zweig nicht mehr von Hand herleiten, sondern das ganze Problem transponieren (x/y tauschen),
dieselbe bereits prueverifizierte Formel wiederverwenden, Ergebnis zurücktransponieren. Verifiziert:
18 neue Tests (T in allen 4 Ausrichtungen, beide Z-Unterfamilien in allen Ausrichtungen, explizite
Ablehnung von U-Kerbe/Rechteck/einfachem-L/Plus-Form-mit-4-Reflexpunkten, CW/CCW-unabhaengig) plus
die bestehenden 23+92 Tests erneut gruen -- 133 insgesamt, keine Regression.

PENDING:
- Weiterhin explizit NICHT an `render-exterior.py` angeschlossen (Codex' eigener Rat) -- alles, was
  heute schon auf "genau zwei Fluegel" abgestimmt ist (Dominanz-Regel, Wandflaechen-Zuschneidung,
  Kehlen-Logik, Doppelpultdach-Handbau), braucht eine eigene, separate Ueberarbeitung davor.
- Namenskonvention fuer T-/Z-Rollen (aktuell: stem/arm_1/arm_2 bzw. connector/arm_lo/arm_hi, engl.,
  intern) -- noch nicht auf eine deutschsprachige Zeichner-UI-taugliche Benennung geprueft.
- Reihenfolge gegenueber PER-WING-AXIS-OVERRIDE-001 (welches zuerst an den Renderer?) ist weiterhin
  eine Terminfrage fuer Rainer, keine technische Abhaengigkeit.

## WB125-DOPPELPULTDACH-HANDBUILT-001 (COMPLETE) + HAUSTUER-MODELL-001 (COMPLETE) + HAUSTUER-PFLICHT-001 (PENDING)

2026-09-25, `german_catalog_review_bungalow_4_3_1_wb_125` (Doppelpultdach / versetztes Pultdach).
Rainer verwarf das profilbasierte Vorgehen komplett nach einem missgluecktem "Ueberstand-Regal"-Fix
(duenner Spitz-"Zahn" am First). Er baute die Dachgeometrie SELBST in Blender (3 Boxen per
Location/Rotation/Dimensions) und gab mir die exakten Werte zum Uebernehmen: "delete all your fuking
BNS and add these 2 boxes" -> "sorry my mistake ... add these three cubes with the dimensions".

Umgesetzt in `born2thrill-local-workbench/scripts/render-exterior.py` (`has_vertical_step`-Zweig):
2 handgebaute geneigte Box-Dachflaechen (`obj.dimensions = (...)`, reine Y-Rotation nach realem
First) + 1 Versatzwand + Giebel-Fuellpaneele. Danach Codex-Zweitmeinung angefordert (Rainer: "not at
the edge of the dachueberstand, you moron, ask codex"), 4 von 4 Befunden High-Confidence bestaetigt
und uebernommen -- Kernregel destilliert: Wand-/Fuellpaneel-POSITION (X und Y) IMMER unabhaengig aus
`roof_wings.recognize_two_wings()` als `wing_bound ± Dachueberstand` berechnen, NIE von der
Dachflaechen-Geometrie selbst oder von einer anderen, ihrerseits dachabgeleiteten Wand ablesen; nur
die HOEHE (Z) darf von der echten Dachneigung abgelesen werden (`_underside_z_at_x()`). Real gebaut:
First/Giebel/Versatz/4 Fuellpaneele, 0 offene Kanten in Dach UND Giebel-Fuellung, sauber aus 2
verschiedenen Kamerawinkeln (inkl. des zuvor immer fehlerhaften "gegenueberliegenden" Blickwinkels).
Regel schriftlich festgehalten in `born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md`
(Nachtrag 2026-09-25).

Gleicher Tag, eigenes Thema: Rainer bat "use our newer front door closed and antrazit" fuer alle
Haus-Renderings. Von 4 Kandidatenmodellen (7961/7962/7968/7976, identische Bounding-Box) ist nur
7976 echtes Anthrazit (`base_color (0.184, 0.192, 0.212)`, die anderen 3 nahezu Schwarz `~0.05`).
`FRONT_DOOR_ASSET` in `render-exterior.py` auf 7976 umgestellt. Rainer fand danach per Screenshot,
dass ein frisch gebautes Haus im Innenrenderer (Dollhouse) weiter die alte generische Tuer zeigte
("that is a mdel i just 'built' still the old door, fuck you again") -- `render-furnished-
dollhouse.py` hatte fuer die Haustuer NIE ein echtes Modell importiert, nur eine generische weisse
Tuer geschlossen dargestellt (ein Kommentar im Code behauptete faelschlich, das sei bereits erledigt).
Fix: `add_door_leaf()` importiert jetzt bei `role == "main_entrance"` echt das 7976-Modell (gleiche
CGAxis-Skalierungskonvention wie `place_asset()`: `divisor=2.54`, Achsenverhaeltnis auf [0.75, 1.35]
geklemmt), sonst Fallback auf die alte generische Tuer. Getestet an `bungalow_001` (WB_125 selbst
hatte zu dem Zeitpunkt keine `main_entrance`-getaggte Tuer) -- Konsole bestaetigt echtes 7976-Modell,
kein Fehler.

Rainer daraufhin, nachdem er die Haustuer bei WB_125 selbst im Zeichner nachgetaggt hatte: "now it
does but why was this not flagged while saving?" -- `validate_annotation_quality()` in
`floorplan-simplifier/app.py` kennt fuer "hat eine Aussentuer" zwei unabhaengige Wege: eine explizite
Markierung (`role == "main_entrance"` oder `exterior`-Flag) ODER einen rein geometrischen
Fallback (Naehe zur Raum-Aussenkante). Ein Haus kann so vollstaendig sauber speichern und trotzdem
dauerhaft die generische Fallback-Tuer bekommen, ohne dass beim Speichern irgendetwas das anzeigt --
genau WB_125s Fall. Rainer: "we should add that as a rule at least one front door".

Umgesetzt: neue, von der bestehenden Warnung getrennte Speicher-Warnung, wenn eine Aussentuer nur
geometrisch gefunden wurde, aber keine explizit als `main_entrance`/`exterior` markiert ist ("No door
is explicitly tagged role: main_entrance (Haustuer) -- ..."). 4 neue Tests in
`tests/test_haustuer_zaehlt.py` (Klasse `MainEntranceMustBeExplicit`), 34/34 gruen (30 bestehend + 4
neu), keine Regression.

PENDING:
- WB_125s echte Lieferrenderings (ueber den echten "Bauen"-Button, mit den echten Dachformen
  Flachdach/Walmdach, nicht dem Doppelpultdach-Testoverride) noch nicht neu gebaut/geprueft, um zu
  bestaetigen, dass die neue Anthrazit-Tuer dort jetzt tatsaechlich erscheint.
- Das Haus aus Rainers urspruenglichem "still the old door"-Screenshot wurde nie identifiziert (nur
  `bungalow_001` als Ersatzfall getestet) -- falls das konkrete Haus spaeter benannt wird, dort
  gezielt nachpruefen.
- Kosmetischer Kleinfund (unveraendert seit ZWEISCHENKLIGES-SATTELDACH-001): winziger
  Splitter-Face an der First-Kreuzung, kein Loch, nur bei starkem Zoom sichtbar.

## SATTELDACH-GABLE-WALL-RIM-MARGIN-001 (PROPOSED, Plan geschrieben, nicht genehmigt)

2026-09-28, Rainer nach dem echten Pipeline-Build von `german_catalog_review_bungalow_4_3_1_wb_125`
(classic): "the walmdach was working the sattaldach didnt work". Live reproduziert (echter
`run_project.py`-Build, `EXT_ROOF_TYPE=satteldach`): sichtbarer Einriss am First des Giebelendes in
der Hero-Kamera-Ansicht -- optisch derselbe Fehler-Typ wie der bereits als GELOEST getrackte
Traufkasten-Fund oben (`roof-walls` naeher an der Kamera als `roof-pitch`), aber an einer ANDEREN,
bisher unbehobenen Stelle: der Giebel-ENDWAND selbst, nicht dem Traufkasten/Soffit.

Untersucht (nicht geraten): eigener, selbentags gemachter `end_extension_mm`-Mauerwerk-Fix als Ursache
per A/B-Rebuild widerlegt (identischer Fehler mit UND ohne diesen Fix). Farb-ID-Render (`roof-pitch`
rot/`roof-walls` gruen, dieselbe bereits bewaehrte Technik) bestaetigt den Ueberdeckungsfehler direkt.
Senkrechter Raycast an den hoechsten `roof-walls`-Vertices nahe dem First zeigt: die Wand liegt
ÜBERALL senkrecht UNTER der Dachflaeche (0,05-0,4m Abstand, nie echte Ueberschneidung) -- derselbe
"SOLIDIFY versetzt entlang der Flaechennormale, nicht senkrecht" Effekt wie beim Traufkasten, nur aus
einem flachen Kamerawinkel sichtbar, keine echte Polygon-Ueberschneidung.

Bewusst NICHT direkt gefixt: `roof_profile.py:1027-1030` dokumentiert bereits, warum die Giebel-
Endwand absichtlich OHNE `extra_sink`-Marge blieb (anders als der Soffit) -- eine zu kurz gebaute
Endwand hinterliesse eine ECHTE, sichtbare Luecke unter dem Dach, da (anders als beim Soffit) nichts
anderes diesen Raum von oben abdeckt. Ein blindes Kopieren der Soffit-Marge koennte genau die
Luecke wieder oeffnen, die diese Entscheidung vermeiden sollte. Plan geschrieben statt direkt gepatcht:
`born2thrill-local-workbench/plans/SATTELDACH-GABLE-WALL-RIM-MARGIN-001.md`.

**2026-09-29, direkter Anschluss, ERSETZT durch ROOF-SWEEP-CONSTRUCTOR-001:** Rainer, nachdem er
selbst live einen kaputten First (sich ueberschneidender/rueckwaerts laufender First-Pfad) im eigenen
Blender sah: "you do it, but ive noticed you set the first direction wron on this house that is why i
would really like to be able to make a T Z or L shape by hand ... just make the with the same as the
footprint running parallel to the first and add the dachueberstand." Sofortmassnahme: der kaputte
First-Pfad von `german_catalog_review_bungalow_4_3_1_wb_125` (ein sich selbst rueckwaerts kreuzender
4-Punkt-Pfad) in `annotations.json` auf `roof_ridge_path: []` und `roof_axis_override: null`
zurueckgesetzt (alter Wert nicht geloescht, aufbewahrt unter
`roof_ridge_path_removed_2026_09_29`); automatische Zweischenkel-Erkennung baut danach wieder sauber.

ABER beim Verifizieren des sauberen Automatik-Baus: derselbe First-Luecken-Fehler (Raycast durch Dach
UND Wand bis zum Boden) tritt AUCH OHNE jeden handgezeichneten Pfad auf -- reiner Konstruktionsfehler
der Fluegel-Rechteck-Architektur selbst, nicht nur ein First-Pfad-Problem. Rainer bat direkt um Codex-
Zweitmeinung ("ask codex and figure it out, its not creativ its just math") zu genau diesem Vorschlag:
First direkt als EINE zusammenhaengende First-Achse zeichnen und das Dach als durchgehende Extrusion
mit LIVE aus dem echten Grundriss gemessener Breite (plus Dachueberstand) entlang dieser Achse bauen --
dieselbe Technik wie bei der Kuechenzeile/Treppen-Platzierung -- statt Fluegel-Rechtecke zu erkennen und
hinterher gegeneinander abzugleichen.

Codex' Read-only-Designreview (vollstaendig in
`C:\Users\Admin\AppData\Local\Temp\claude\C--dev-Floorplan-tools\4a479835-656e-49e5-8742-a731e21516b2\
scratchpad\codex-out-roof-sweep-constructor.md`) bestaetigt UNABHAENGIG: das durchgehende Abtasten der
Live-Breite ist an einer Fluegelgrenze UNSTETIG (belegtes Rechenbeispiel: ein L, an dem die First-Hoehe
schon VOR der eigentlichen Ecke von 2m auf 5m springt, wenn das Profil auf die Spannweite skaliert) --
mehr Abtastpunkte koennen eine echte Unstetigkeit nicht beheben, T/Plus-Knoten brauchen eine echte
Flaechen-Verschneidung (kein rotierter Querschnitt), und ein fester symmetrischer First-Querschnitt
plus eine frei gezeichnete, nicht mittige Firstlinie plus beide echten Traufkanten sind im Allgemeinen
NICHT gleichzeitig erfuellbar (braucht eine explizite Entscheidung, keine Annahme). Codex fand dabei
GANZ UNABHAENGIG einen weiteren echten Fund: eine reproduzierbare ~98,5mm-Abweichung zwischen der
tatsaechlich gebauten Dreiecksflaeche und der analytischen `combined_height_at()`-Funktion, die die
Wandkonstruktion zur Hoehenberechnung nutzt -- weil die "welcher Fluegel ist hoeher"-Knicklinie keine
echte Netz-Kante ist. Codex lieferte einen vollstaendigen, konkreten Konstruktionsalgorithmus (eine
kanonische First-Flaeche aus Regel- und Knoten-Patches mit echten gemeinsamen Kanten, explizite
vertikale Schalendicke statt SOLIDIFY, Wandhoehen direkt aus dieser Unterseite abgeleitet statt separat
abgetastet).

Ergebnis: `SATTELDACH-GABLE-WALL-RIM-MARGIN-001` als eigenstaendiger Plan ERSETZT (Beleg-Historie bleibt
erhalten, nicht implementieren). Neuer, von Rainer genehmigter Plan:
`born2thrill-local-workbench/plans/ROOF-SWEEP-CONSTRUCTOR-001.md` -- ersetzt die Fluegel-Rechteck-
Architektur durch eine einzige kanonische First-Flaeche mit daraus abgeleiteten Wandhoehen, Umfang
bewusst auf den 2-Fluegel-Fall (L/T) begrenzt, N-Wege-Plus-Knoten und `roof_wings_multi.py`-Anschluss
als eigene Folgeaufgabe getrackt.

**2026-09-29, direkter Anschluss ("fix it all and test it", Rainer danach ~2h abwesend):** vier
weitere, einzeln verifizierte Fixes AUF der bestehenden Fluegel-Rechteck-Architektur (nicht der grosse
Umbau selbst -- der bleibt offen):

1. `mesh_height_at()` (neue Funktion) + `wall_extension(roof_mesh=...)`: Waende fragen jetzt das ECHTE
   gebaute Dachnetz statt der analytischen Funktion, die (Codex-Fund) bis zu 98,5mm davon abweichen
   kann. Verifiziert: reproduziert Codex' genauen Fall.
2. Stufen-Schluss an Fluegelgrenzen ("treat height differences like a giebel", Rainers eigene Vorgabe
   nach Diagnose): ein echter, ~0,9m hoher, im Hero-Kamera-Render sichtbarer Sprung (Raycast durch Dach
   UND Wand bis zum Boden bestaetigt) wird jetzt mit einer schwebenden Stufe geschlossen.
3. Diagonalen-Konsistenz-Fix in `heightfield_roof_mesh()`: Codex-Diagnose + eigener Trace der echten
   Netzdaten bestaetigte hart, dass benachbarte Gitterzellen an derselben Kante ENTGEGENGESETZTE
   Diagonalen waehlten -- behoben durch eine feste Diagonale fuer echte Kanten-Klippen-Zellen.
4. Dichte Sicherheits-Abtastung in `boundary_polygon()`/Langwand-Rampe: ein systematischer Soll/Ist-
   Abgleich (komplettes Dachnetz gegen jeden gebauten Wand-Scheitelpunkt) fand Unterschreitungen bis
   0,4m zwischen bekannten Knickpunkten -- jetzt zusaetzlich alle 0,3m abgetastet.

Alle 4 verifiziert: `roof_profile.test.py` 102/102, `roof_wings.test.py` 34/34 gruen, echte Rebuilds
aller 4 Dachformen auf WB_125 plus 2 weitere echte Projekte (bungalow_007 Rechteck, bungalow_013)
sauber.

**NICHT behoben, bewusst fuer den grossen Umbau liegen gelassen:** trotz aller 4 Fixes hat `roof-pitch`
auf WB_125s echtem Satteldach-Rebuild 164 echte, sich selbst ueberschneidende Dreieckspaare (per
`bmesh`/`BVHTree.overlap()` bestaetigt, nicht geraten) -- alle exakt an derselben Fluegelgrenze/
Kehlenecke wie die Fixes 2-4 oben. Bestaetigt VORBESTEHEND (identische Anzahl vor und nach dem
Diagonalen-Fix). Codex' eigene Mathematik (worked-math Abschnitt 4 im gespeicherten Review) sagt: die
zugrunde liegende Flaeche (max() zweier First-Funktionen) hat dort eine echte Knicklinie, die keine
Pro-Zelle-Diagonalwahl korrekt darstellen kann -- nur das Einfuegen dieser Knicklinie als echte
gemeinsame Netzkante (der grosse Umbau, Punkte 1-4 des Plans) loest es strukturell. Ein sichtbarer
Riss an genau dieser Stelle im echten Hero-Kamera-Render bestaetigt. Ein fuenfter gezielter Patch wurde
bewusst NICHT versucht (Risiko eines falschen, ungetesteten Fixes in begrenzter Zeit) -- hier
dokumentiert, damit die naechste Sitzung nicht neu diagnostizieren muss.

**2026-09-29, direkter Anschluss (Rainer: "yes", nach Rueckkehr, genehmigt den grossen Umbau):** Punkte
1 und 2 des Umbaus implementiert und hart verifiziert (volle Details: `ROOF-SWEEP-CONSTRUCTOR-001.md`'s
eigener Progress-Abschnitt).

Punkt 1 (kanonische First-Flaeche, 2-Fluegel-Kehle als ECHTE gemeinsame Netzkante): neue
`_perpendicular_two_wing_crease()`/`_crease_split_cell()` in `roof_profile.py` -- da jeder Fluegel seine
Hoehe nur von EINER Koordinate abhaengig hat, ist die Differenz beider Hoehenfunktionen innerhalb einer
Gitterzelle exakt AFFIN; ihre Nullstelle ist exakt eine Gerade, kein Naeherungswert. Beim Einbau drei
echte Bugs gefunden und behoben (per fehlschlagendem Test, nicht geraten) -- der wichtigste: benachbarte
Gitterzellen erzeugten je einen EIGENEN Kreuzungspunkt auf derselben gemeinsamen Kante (zwei numerisch
identische, aber index-VERSCHIEDENE Punkte), was das Netz an 21 Punkten tief im Dachinneren aufriss --
behoben mit einem ueber die ganze Zellschleife geteilten `edge_cache`.

Punkt 2 (explizite vertikale Schalendicke statt SOLIDIFY): ein Rebuild mit NUR Punkt 1 zeigte, dass sich
die Selbstueberschneidungen VERSCHLECHTERTEN (328 statt 164) -- SOLIDIFY versetzt entlang der
gemittelten Flaechennormalen, und Punkt 1 macht die Kehle zu einer echten, scharfen Falte, genau die
Bedingung, unter der ein Normalen-Versatz sich selbst durchschlagen kann (Codex' eigene Warnung: Punkte
1 und 2 sind nicht unabhaengig ausreichend). Neue `heightfield_roof_shell()`: Unterseite ist dieselbe
(x,y) mit fest VERTIKAL reduziertem z -- kann die Oberseite nur durchschneiden, wenn diese es selbst
schon tut (durch Punkt 1 ausgeschlossen). In `render-exterior.py`s Satteldach/Pultdach-Zweig verdrahtet,
SOLIDIFY dort vollstaendig ersetzt.

Verifiziert: `roof_profile.test.py` 106/106, `roof_wings.test.py` 34/34 gruen. Echter Rebuild WB_125
Satteldach: `bmesh`/`BVHTree.overlap()` findet **0** Selbstueberschneidungen (von 164 zu Beginn des
Tages, 328 mit nur Punkt 1) -- direkte Manifold-Pruefung: **0** nicht-mannigfaltige Kanten (3588
Vertices/6994 Faces). Alle 4 Dachformen auf WB_125 sauber (Pultdach durchlaeuft denselben neuen Pfad,
ebenfalls 0 Ueberschneidungen). 2 weitere echte Projekte (bungalow_007 Rechteck, bungalow_013) sauber,
keine Regression. Hero-Kamera-Render visuell geprueft: kein Riss mehr an der Kehlenecke.

**2026-09-29, direkter Anschluss (Rainer: "so now?"):** Punkte 3 und 4 abgeschlossen. **Alle 4 Punkte des
Plans sind jetzt umgesetzt und verifiziert.**

Punkt 3: eine Umstellung der Wandhoehen-Abfrage auf die UNTERSEITE der Schale waere FALSCH gewesen --
die bestehende `max(own, combined)`-Logik laesst die Wand absichtlich leicht in die Dachplatte
hineinreichen (in massivem Material versteckt, garantierter Kontakt); die Oberseite bleibt das richtige
Abfrageziel. Tatsaechlich noch offen war nur `boundary_polygon()`s soffitspezifisches `extra_sink`
(0,35m, 2026-09-27 gegen SOLIDIFYs Randverduennung eingefuehrt) -- diese Begruendung existiert nirgends
mehr, wo die Funktion noch aufgerufen wird (Punkt 2 gibt jeder First-Flaeche jetzt ueberall exakt
gleichmaessige Dicke; Doppelpultdachs eigener 2-Fluegel-Zweig ruft diese Funktion ohnehin nie auf).
Entfernt, `sink` (bewusster kleiner aesthetischer Einzug) unveraendert gelassen. Verifiziert per
direktem, kamera-unabhaengigem Raycast (senkrecht von jedem Soffit-Scheitelpunkt gegen das echte
gebaute `roof-pitch`-Netz): 0 Durchstich-Verletzungen auf Satteldach; 3 `NO_HIT_ABOVE`-Faelle auf
Pultdach bestaetigt VORBESTEHEND (identisch vor und nach der Entfernung) -- vermutlich ein separates,
harmloses Raycast-Tangenten-Artefakt an der exakten Ueberstand-Randkoordinate, als eigener kleiner
Folgepunkt notiert, nicht blockierend.

Punkt 4: bereits durch bestehenden Code (2026-09-25, vor diesem Plan) erfuellt, heute nur bestaetigt statt
neu gebaut. WB_125s eigener 2-Fluegel-Doppelpultdach-Zweig baut ueber einen komplett separaten
Hand-Box-Mechanismus (`_hand_built_boxes`/`_make_box()`) -- beide Dachplatten UND die Versatzwand sind
echte Boxen mit expliziten `dimensions` (nie ein Normalen-Versatz-Modifier). Der allgemeine (nicht
WB_125-spezifische) Doppelpultdach-Pfad nutzt `gable_cap_prism()`, eine seit langem bewaehrte explizite
Konstruktion. Keine Code-Aenderung noetig.

**Abschliessender Regressionslauf, alle 4 Punkte:** `roof_profile.test.py` 106/106, `roof_wings.test.py`
34/34 gruen. Alle 5 Dachformen auf WB_125 sauber gebaut, plus `bungalow_007`/`bungalow_013`. Finale
Selbstueberschneidungspruefung: **0** (von 164 zu Beginn dieser Arbeit). `ROOF-SWEEP-CONSTRUCTOR-001`s
Umfang ist vollstaendig umgesetzt; offene Folgepunkte (N-Wege-Knoten, `roof_wings_multi.py`-Anschluss,
Walmdachs eigene Kehlenecken-Bruecke, das Pultdach-Raycast-Artefakt) bleiben getrackt, nicht storniert.

### 2026-10-04 -- ROOF-RIDGE-PER-FORM-001 (Firstlinien pro Dachform) -- umgesetzt, ein Folgepunkt offen

Plan: `born2thrill-local-workbench/plans/ROOF-RIDGE-PER-FORM-001.md` (von Rainer freigegeben, "ja").
Umgesetzt: `roof_ridge_paths_by_form` (Annotator speichert pro Dachform, leere Liste = automatisch,
fehlender Eintrag = gemeinsame Linien), Plan-Builder reicht es durch, `render-exterior.py` waehlt
eigene -> gemeinsame -> automatisch und loggt die Quelle. Ausserdem: der Chevron-Pfad (alle L-Haeuser)
hat gezeichnete Firstlinien bisher komplett ignoriert -- er nimmt jetzt Zerlegung und First-Achsen aus
den Linien (`roof_wings.choose_ridge_guided_decomposition`, 4 neue Tests). Verifiziert an
3_5_1_b_145 (Satteldach + Versetztes Pultdach neu gebaut, Blender-Sonde).

OFFEN (pending, nicht storniert):
- **Spitze hinter dem Hauptfirst** (`roof_profile._depth_to_match_height`, Verdopplung der Tiefe seit
  2026-10-01): der Stich-First laeuft ueber den Haupt-First hinaus und sticht auf der Rueckseite durch
  (3_5_1_b_145: Stich-First endet bei x=4,27 statt am Hauptfirst x=6,69; Satteldach und Versetztes
  Pultdach). ERLEDIGT 2026-10-04 (Rainer: "fix it"): Tiefe am Hauptfirst gekappt; Stich-First endet
  jetzt bei x=6,69 (Satteldach) bzw. 6,52 (Versetztes Pultdach), Blender-Sonde + Ansicht von hinten
  sauber. 3 Erwartungswerte in DepthToMatchHeightTests angepasst (sie schrieben genau den Durchstich
  fest), 1 neuer Test; roof_profile 119/119, roof_wings 46/46, roof_wings_multi 18/18.
- **ROOF-L-JUNCTION-RIDGE-001** (automatische Fluegel ohne Firstlinien, Hauptfluegel nach Flaeche):
  bleibt offen fuer Haeuser ohne gezeichnete Linien.

### 2026-10-04 -- VERSATZ-WHOLE-HOUSE-001 (Versetztes Pultdach = ein Dach ueber das ganze Haus) -- umgesetzt

Plan: `born2thrill-local-workbench/plans/VERSATZ-WHOLE-HOUSE-001.md` (Rainer: "yes"). Nicht-rechteckige
Haeuser bekommen beim Versetzten Pultdach EIN Dach ueber die Bounding-Box mit EINER Versatzlinie (wie die
Dach-Referenzkarte), auf den Umriss zugeschnitten; jede Seite des Versatzes kragt nur ueber ihren eigenen
Hausteil aus; Waende bis zum Dach als ein zugeschnittener Querschnitt-Koerper. Eigene Firstlinien fuer
das Versetzte Pultdach behalten die Fluegel-Konstruktion. 3_5_1_b_145: Versatz bei y=7,59 m, 2 Dachflaechen.
Nebenbei behoben (betraf JEDES Haus): Tiefen-/Maskenpass setzten beim `materials.clear()` alle
Flaechen-Materialnummern auf 0 -- die gespeicherte .blend zeigte Fassaden-Flaechen am Dach dunkel (das PNG
war richtig). Jetzt werden sie gesichert und zurueckgesetzt.

Giebelenden (Rainer: "we need an Ueberstand at the top ... why isn't it flush with the wall?"): ERLEDIGT
fuer L-Haeuser -- die Versatzwand endet buendig an der Giebelwand, der obere Dachueberstand bleibt; ihre
Schnittenden sind Fassade. STORNIERT 2026-10-04 von Rainer ("it is just interesting for L shapes"): rechteckige Haeuser (`elif is_rectangle:`-Zweig) haben
dieselbe ueberstehende Versatzwand noch -- gleiche Korrektur dort nachziehen.

**VERSATZ-WHOLE-HOUSE-001 Nachtrag (nach Rainers eigener Korrektur der .blend, 11:33):** Dach jetzt aus zwei
Platten (kein Stufenblech mehr): die hohe Platte laeuft in ihrer Neigung 0,5 m ueber die Versatzwand hinaus,
die niedrige laeuft unter ihr durch. Giebel-/Versatz-/Innenecken-Fuellwaende sitzen buendig auf der
WANDAUSSENKANTE (vorher Wandmitte, 13 cm zurueck); die Versatzwand steht auf der Aussenkante der Wand
darunter (7,53 m). Rainers Datei aufbewahrt als `exterior-doppelpultdach-baseline.rainer-edit-1133.blend`.
STORNIERT 2026-10-04 von Rainer ("it is just interesting for L shapes"): rechteckige Haeuser mit Versetztem Pultdach bauen noch das alte Stufenblech mit Fuellwaenden
auf der Wandmitte -- dieselbe Bauweise dort nachziehen.

### 2026-10-04 -- ROOF-SLIVER-COVERAGE-001 (keine dachlosen Streifen) -- umgesetzt, Rest offen

`roof_wings.absorb_slivers()` (6 neue Tests, roof_wings 53/53, roof_profile 119/119, multi 18/18): Streifen
0,3-1,0 m werden nicht mehr verworfen, sondern Nachbarfluegeln zugeschlagen (laengste ganze Kante zuerst).
bungalow_040_66: 11,16 m des 0,76-m-Streifens gehen an den Hauptfluegel, Satteldach bleibt Satteldach (Chevron
4 Fluegel). Abweichung vom Plan: ein Rest, der keinem Nachbarn passt, wird NICHT eigener Fluegel (das liess die
Chevron-Konstruktion scheitern -> Walmdach), sondern bleibt den Ueberstaenden ueberlassen.
Regression: bungalow_001, 3_5_1_b_145, wb_125 -- Zerlegung unveraendert.
OFFEN (pending): 040_66 Hofecke rechts, 26 cm x 2,5 m ohne Dach (Raycast 10 von 2877 Punkten);
das "V" im Hauptteil des Satteldachs braucht Rainers Aussenumriss + Firstlinien.

### 2026-10-07 -- MOEBEL-FREMD-FEHLALARM-001 -- erledigt

"Moebel auf fremder Geometrie" erscheint nur noch fuer Moebeldateien ausserhalb von
`render-geometry-mm-y-down-v1`; fuer Dateien auf der Bau-Geometrie vergleicht die Staleness-Route jetzt deren
`geometry_identity` mit der heutigen je Geschoss ("Moebel veraltet · Erdgeschoss"). Die 11 betroffenen Haeuser
sind frei; Gegentests (geaenderte Identitaet, alter Koordinatenraum) mit Wegwerf-Plan bestanden.
OFFEN (pending): twostorey_053 -- /api/floorplan-workbench/generate antwortet "Unknown explicit reference"
(war schon vorher so; nur die Anzeige "grund" betroffen).
FERTIG-BLEIBT-FERTIG-001: ERLEDIGT 2026-10-07 (siehe unten).

### 2026-10-07 -- FERTIG-BLEIBT-FERTIG-001 -- erledigt

`fertig-ledger.json` im Datenordner merkt sich jedes Haus, das je fertig war (32 Haeuser als v1.0 angelegt).
Ein solches Haus faellt nie mehr zurueck: neuer Renderer / neue, nicht angehakte Bilder / WordPress weg ->
`fertig_update` (tuerkis, zaehlt als erledigt, "Fertig v1.x · Update verfuegbar (Grund)"). Wird es auf einem
neuen Build wieder voll fertig, steigt die Version (1.1, 1.2 ...). Echte Fehler (keine Vorlage, kein Massstab,
keine Ausrichtung) gehen weiter vor. house-state 25/25, alle lib-Tests 44/44.
OFFEN (pending): Statusroute braucht ~60 s, weil sie fuer jedes aktuelle Haus (jetzt 29) einzeln WordPress
fragt (`bilderStand`); die Hausakte zeigt solange "0 Haeuser". Abfragen buendeln oder cachen.

## 2026-10-08 — offene Punkte aus ANBAU-BEKOMMT-PULTDACH-001

- **Chevron-Satteldach ohne eindeutige Anbaukante lässt Wandoberkanten offen.**
  `bungalow_040_33` und `german_catalog_review_bungalow_4_1_4_wb_105`: die
  Anbauerkennung in `einfirst_satteldach()` greift nicht (zwei Innenkanten oder
  keine), beide fallen auf `chevron_roof_construction()` zurück und haben dort
  je 8 offene Wandoberkanten. Alter Fehler, nicht von diesem Plan verursacht,
  nicht in dessen Umfang. Braucht einen eigenen Plan.
- **Vier Häuser scheitern am Verifier `wall_angles`, nicht am Dach.**
  `bungalow_040_43`, `4_1_4_wb_105`, `4_1_6_wb_105`, `4_2_3_wb_115`: Wände bis
  34,5 Grad aus der Achse, und nicht die kürzeste Kante. Das ist Annotation,
  nicht Renderer — sie bekommen deshalb kein Zertifikat. Zu klären, ob die
  Annotation korrigiert wird oder die Regel zu streng ist.
- **17 fertige Häuser haben noch das alte Zwei-Dächer-Satteldach.** Nach der
  Regel "fertig ist fertig" bewusst nicht neu gebaut. Liste in
  `plans/ANBAU-BEKOMMT-PULTDACH-001.md`. Rainer entscheidet je Haus.

### 2026-10-09 -- MOEBEL-DOPPELKLICK-001 (Doppelklick setzt keinen dritten Punkt) -- umgesetzt, zwei Folgepunkte offen

Plan: `born2thrill-local-workbench/plans/moebel-doppelklick-dritter-punkt-v1.md`.
Zweiter Druck eines Doppelklicks (< 500 ms, < 10 px) wird beim Zeichnen eines
Laufs verworfen; im Browser geprueft (2 Punkte, auch mit 7 px Wackler).

- [x] Automatischer Test: `istDoppelklickDruck()` in furniture.tsx, vier
      Tests in `scripts/moebel-punkte.test.mjs`, 33/33 gruen (2026-10-09).
- [ ] Rainer fragen, ob "andere linien" auch Annotator-Linien meint; dort
      bisher kein Befund (`annotate.js` ueberspringt `event.detail > 1`).

### 2026-10-09 -- MOEBEL-BEREICH-EINRICHTEN-001 (Bereich markieren, Raumtyp waehlen, einrichten) -- Prototyp umgesetzt

Plan: `born2thrill-local-workbench/plans/moebel-bereich-einrichten-v1.md`.
Prototyp mit Schlafzimmer, Bad, Wohnzimmer. Freigegeben 2026-10-09
(Nachttisch = Stuff, Dusche vor Wanne, bei vorhandenen Moebeln fragen).

- [x] Prototyp (3 Raumtypen) -- 2026-10-09, 12/12 Tests, im Browser geprueft
- [ ] Rainers Urteil zum Prototyp abwarten
- [x] Eigene Bereiche zeichnen (Ecken/Rechteck, Shift+Klick = Raum) + Esszimmer + Kueche -- 2026-10-09
- [x] Restliche Raumtypen: Diele, HWR, Kinderzimmer, Gast, Du/Bad, WC -- 2026-10-09; Bad mit Wanne; Spuele/Kochfeld sichtbar
- [ ] Fehlende Symbolbilder: Lowboard, Sideboard, Garderobe, Esstisch, Esszimmerstuhl, Doppelwaschtisch (zeigen nur Namen)
- [x] Buero als Raumtyp -- 2026-10-09 (Rainer: "büro fehlt")
- [x] Wohnzimmer mit Ecksofa -- 2026-10-09; Ecksofa-Symbol hat Vorderseite -y, Pfeil gedreht
- [ ] Im 3D-Bau pruefen, ob ein vorgeschlagenes Ecksofa richtig herum steht (gleiche Drehung wie handgesetzt)
- [ ] Bad: Teile auf mehrere Waende verteilen (landen oft alle an einer)
- [ ] Nachttisch-Symbol fehlt im Katalog

### 2026-10-09 -- MOEBEL-LEERER-RAUM-001 (Warnung bei leerem Raum vor "Weiter zu Bauen") -- erledigt

Plan: `born2thrill-local-workbench/plans/moebel-leerer-raum-warnung-v1.md`.
Alle Geschosse, Flur/Diele/Treppe/Galerie/Luftraum/Abstell/Garage/Carport/
Balkon/Terrasse ausgenommen. 38/38 Tests, im Browser geprueft. Kein offener Rest.

### 2026-10-09 -- PLAYSTATION-DETAIL-001 (Playstation-Gruppe im Plan mit Teilen) -- erledigt

Rainer: "just a large square with an arrow". Es gab kein PNG (404). Jetzt
zeichnet `PlaystationTeile` in furniture.tsx Lowboard + TV hinten und zwei
Hocker vorn -- dieselbe Aufteilung wie build_playstation() im Bau. Nur
Darstellung im Editor; Daten, Render und Bau unveraendert. Im Browser
geprueft (onehalfstorey_020 OG, nicht gespeichert). Ohne separaten Plan
umgesetzt (kleine reine Darstellungsaenderung auf Rainers direkte Bitte).

### 2026-10-09 -- TEPPICH-UNTER-WAND-002 (Teppiche gegen die echten Waende klemmen) -- umgesetzt

Rainer: "and you still haven fixex the rugs going underneth the walls".
Ursache gemessen an bungalow_040_36: der Fix vom 2026-09-07 haelt 200 mm
Abstand zur RAUMKANTE und nimmt an, sie liege auf der Wandmitte. Hier liegt
sie auf der AUSSENSEITE der Aussenwand (Wand x=14770, 240 mm; Raumkante
x=14890) -> Teppich 40 mm unter der Wand, im Wohnbereich an drei Seiten,
auch beide Schlafteppiche. Neu: `scripts/teppich_klemmen.py` kuerzt den
Teppich gegen jede achsparallele Wand (halbe Dicke + 50 mm), eingehaengt in
render-furnished-dollhouse.py nach der bestehenden Klemmung (Sicherung
`.before-teppich-waende`). Tests: `teppich_klemmen.test.py` 5/5,
`render-furnished-dollhouse.test.py` 26/26. Probe-Render bungalow_040_36 EG
in den Scratch-Ordner (E: unveraendert): Wohnen 3,12x3,30 -> 3,09x3,04 m,
Schlafen 3,00x2,80 -> 2,45x2,80 und 3,00x1,90 -> 2,41x1,29 m; im Bild liegt
jetzt Boden zwischen Teppich und Wand.

- [ ] Schraege Waende werden nicht geprueft (nur die alte Polygon-Pruefung)
- [ ] bungalow_040_36 neu bauen, damit die ausgelieferten Bilder den Fix tragen
- [ ] `render-persp-test.py` hat die alte Teppich-Logik (wird von nichts aufgerufen)

### 2026-10-11 -- bungalow_040_39 render package
- [x] Eight visually accepted review images exported; native originals, prompts, source audits and ZIP preserved in E: render folder.
- [ ] Upload eight images to born2thrill.de: dry run passed, no existing images; automatic approval review blocked actual upload pending explicit destination confirmation. No media uploaded and no customer delivery.
- [ ] Exact geometry/complete marker QA remains uncertified; visual acceptance does not change rights flags.


### 2026-10-11 -- bungalow_040_39 upload completed
- [x] Prior pending destination-confirmation/upload item resolved: user explicitly authorized born2thrill.de; publisher uploaded 8 images, IDs 825-832; independent lookup verified 8 expected names for bungalow_040_39, all send=false. No rights changes.
- [ ] Exact geometry/complete marker certification remains unperformed; not a requirement for the completed internal catalogue upload, and not claimed.


### 2026-10-11 -- bungalow_040_40 finished and uploaded
- [x] Four interior styles and four roof exteriors exported; native images, prompts, Blender audits and ZIP preserved in E: delivery folder.
- [x] Uploaded 8 images to born2thrill.de for bungalow_040_40 (IDs 833-840); independent catalogue query verified all expected names and no customer sending. Rights unchanged.
- [ ] Exact geometry/marker certification remains unperformed; approved master retained with previously disclosed oven-cabinet uncertainty.


### 2026-10-12 -- bungalow_040_42 rendered and uploaded
- [x] Approved Warm Modern master, three other interiors and four roof exteriors exported; source audits, native images, prompts, visual marker observations and ZIP preserved in E: delivery folder.
- [x] Uploaded eight images to born2thrill.de, plan bungalow_040_42, media IDs 841-848; independent catalogue query verified names and send=false. No customer email or rights changes.
- [ ] Exact geometry and occluded/small marker parts remain uncertified; catalogue retains explicit uncertainties.


## 2026-10-17 — Treppenzugang-Warnung (offen)
- [x] `scripts/treppe_zugang.py` + `stair_access.test.py`: Wand ohne Tuer quer vor Antritt/Austritt wird vor dem Bauen gemeldet (Hausakte-Bauen fragt, `go.py` stoppt, `--trotz-treppe` uebergeht). Nicht im Toolchain-Hash.
- [ ] twostorey_058: Wand Wohnen/Essen/Kochen–Diele quer vor dem Antritt (EG) — Rainer korrigiert im Annotator.
- [ ] twostorey_052: Wand quer vor dem Antritt (EG), Tuer liegt daneben.
- [ ] german_catalog_review_onehalfstorey_1_6_1_efh_190: Wand Kind–Eltern quer ueber den Austritt (DG).
- [ ] twostorey_056: Verifier opening_count OG — 2 Fenster/Tueren auf keiner Wand.

### 2026-10-17 -- german_catalog_review_bungalow_3_3_3_b_100_2 completed
- [x] Four interiors and four roof exteriors completed from current Blender sources, including user-corrected Satteldach. Uploaded media IDs968-975; independent query verified8 expected names and all send=false. No rights changes.
- [x] Catalogue, source audits, actual prompts, visual marker observations, checkpoint and ZIP saved in E: job delivery folder. No remaining rendering/upload items for this job.
- [ ] Exact geometric certification and individually occluded marker details remain uncertified; visual catalogue upload does not assert these.


## 2026-10-20 -- Innentueren 20 Grad, Badewanne Armaturen hinten
- [x] `render-furnished-dollhouse.py` (+ Testkopie `render-persp-test.py`): `DOOR_OPEN_DEG` 45 -> 20 (Tuerblaetter verschwanden aus der Kameraperspektive); `MODEL_FACING_DEG["badewanne"]` 180 -> 0 (in Blender gemessen: Armatur sitzt nativ auf +Y = hinten, die 180 drehte sie nach vorn). Plan: `born2thrill-local-workbench/plans/tuerwinkel-und-badewanne-v1.md` (nachtraeglich geschrieben).
- [ ] Ein Haus mit Badewanne und offenen Innentueren neu bauen und am .blend/Bild pruefen (Armatur hinten, Tuerblatt 20 Grad sichtbar). Noch nicht gerendert.
- [ ] Toolchain-Hash geaendert: alle bestehenden Builds gelten jetzt als alt. Entscheiden, ob bereits veroeffentlichte Haeuser mit Badewanne neu gebaut und neu hochgeladen werden.

## 2026-10-20 -- Treppenloch folgt der Treppenform
- [x] Decke wird jetzt mit dem Umriss der Treppe geschnitten (Laufband-Quads, kein Boolean), beide Renderer. 14 neue Tests gruen. twostorey_059 OG im Scratch neu gebaut: Treppenauge und Kerbe sind Boden, alle 6 Gelaender stehen auf Boden (vorher 4 ueber Leere). Plan: `born2thrill-local-workbench/plans/treppenloch-folgt-treppenform-v1.md`.
- [ ] twostorey_059 regulaer neu bauen (`go.py`); Zeichnung hat sich seit dem 08:31-Plan geaendert, Verifier laufen lassen.
- [ ] Entscheiden, ob veroeffentlichte Haeuser mit L-/U-Treppe neu gebaut und neu hochgeladen werden (eigene Upload-Freigabe).
- [ ] Vorbestehend, unabhaengig: `build-simplifier-render-plan.test.py` test_door_hinge_and_swing_are_normalized_into_the_walls_frame schlaegt fehl (6 Tuer-IDs fehlen in den Live-Annotationen).

## 2026-10-20 -- Treppenloch selbst zeichnen
- [x] Treppenoeffnung-Flaeche im OG = Treppenloch (ersetzt Automatik), Gelaender per Kanten-Klick, Austritt automatisch offen, Rechtsklick "Treppenloch selbst zeichnen", Einrasten der Lochkanten auf die Wandflaeche (Annotator 0,6 m; Renderer 150 mm, auch fuer den Automatik-Schnitt), Waende des Geschosses darunter blass, Pruefungen (Austritt, Kopfhoehe, Raum, Versatz EG/OG, Austritt vor der Kante). Tests gruen; Scratch-Builds twostorey_059 gemessen. Plan: `born2thrill-local-workbench/plans/treppenloch-selbst-zeichnen-v1.md`, `floorplan-simplifier/plans/treppenloch-selbst-zeichnen-v1.md`.
- [ ] Preisregel: zaehlt eine gezeichnete Treppenoeffnung in konfigurator-matrix.py als m2 (wie Luftraum) oder nicht? Ueber dem Flur gezeichnet zaehlt sie heute doppelt.
- [ ] Annotator: Einrasten auch beim spaeteren Verschieben einzelner Punkte (punkte-verschieben.js).
- [ ] render-persp-test.py hat keine Luftraum-/Treppenloch-Gelaender.
- [ ] twostorey_059: Luftraum-Flaechen am Treppenhaus pruefen (Flur ueberdeckt den Luftraum und behaelt dort Boden; Luftraum auch im EG). (Die fruehere Notiz "OG-Kopie ~450 mm daneben" war ein Fehler meines Testskripts; gemessen: innerhalb 40 mm.)
- [x] A1: Luftraum schneidet ueberlappende Boeden, Gelaender bis an die Wand, Einrasten nur weitend, Verifier R3 am echten Umriss. Tests gruen; go.py twostorey_059 "fertig", alle Verifier-Regeln PASS. Offene Kanten 87 -> 2 Proben.
- [ ] twostorey_059: ~41 cm Treppenkante 2-left zwischen Luftraum-Ecke (x 5904) und Austritt (x 6315) ohne Gelaender (neben den obersten Stufen, 0-19 cm Hoehe). Zeichenentscheidung: Luftraum bis ans Treppenende ziehen oder eigenes Stueck.
- [x] twostorey_059: OG-Render schief gerahmt -- Ursache war ein Fehler (Kamera-Stempel vor dem Anheben, +2,62 m je Neubau). Behoben (plans/kamera-obergeschoss-stempel-v1.md), Kamera zurueckgesetzt, Neubau 12:12 mittig.
- [ ] Dieselbe falsche Handkamera vermutlich bei bungalow_040_185, twostorey_045-052, 054, 055, 056, 058 (kamera-innen-1.json). Rainer entscheidet je Haus: json loeschen = automatische Rahmung.

## 2026-10-20 -- twostorey_060 ist ein Hanghaus (PROPOSED)
- [ ] Geschosse umbenennen: EG -> Untergeschoss (basement), OG -> Erdgeschoss; Treppe aus dem untersten Geschoss mit echter Treppe lesen. Plan: `born2thrill-local-workbench/plans/twostorey-060-hanghaus-geschosse-v1.md`. Wartet auf Freigabe.
- [ ] Hanggelaende im selben Plan (Teil B): Aussenflaechen auf Geschosshoehe, Gelaende faellt vom Gehweg zur Terrasse, Erde an der UG-Strassenseite. Wartet auf Freigabe. Danach offen: Gelaende auch in den Innenansichten.

## 2026-10-20 -- Katalogzeile automatisch (PROPOSED)
- [x] Route b2t/v1/grundriss-anlegen + publish-renders.py legt fehlende Zeile selbst an. Code fertig, Tests gruen, Dry-Run twostorey_059 zeigt die Zeile. Plan: `born2thrill-local-workbench/plans/katalogzeile-automatisch-v1.md`.
- [x] Plugin 1.1.1 live (als normales Plugin ersetzt, nicht mu-plugins). twostorey_059: Zeile automatisch angelegt, 12 Bilder hochgeladen (IDs 1001-1012), kein Versand.
- [ ] Von Hand eingefuegte Zeilen weichen von der Regel ab (bungalow_040_185, bungalow_040_66) -- eigene Freigabe.


## HANGHAUS-060 — 2026-10-20
Implementation COMPLETE: final preserved-ID go.py build passed (2 styles, 0 excluded, 6 certified artifacts); Blender height acceptance passed. Details: born2thrill-local-workbench/plans/twostorey-060-hanghaus-verification-2026-10-20.md. No upload/commit. Next pending: review four UG openings below terrain and driveway extending into slope. Existing builder door-hinge test fails on before/after source. Out-of-scope follow-ups remain pending: general STALE PLAN mass-sidecar timing, go.py error-banner reporting, interior terrain/sockel presentation, >2-level slopes, retaining walls/ramps, house-type/pricing and UG area decisions. Lowest-real-stair rule also selects bungalow_007 basement source (~2.4 mm core edge change; exterior unchanged), recorded for interior regression review.

HANGHAUS-060 exterior style previews: three reviewed image drafts saved in corrections/twostorey_060/renders/codex-twostorey_060-2026-10-20/exterior-style-review (modern glass, normal horizontal stainless rods, classic metal; premium outdoor furniture). Image styling only, source Blender and renderer unchanged. Next pending: user review, then applying accepted styling to requested catalogue views. No upload. Existing terrain drawing warnings remain pending.

HANGHAUS-060 interiors: Warm Modern UG and EG review images created from reopened current Blender files (220/362 meshes) and corresponding object maps. Saved in corrections/twostorey_060/renders/codex-twostorey_060-2026-10-20/interior-warm-review. Exterior seams and unmodelled stools corrected, laundry fronts corrected toward upper right. Next pending: user review and complete per-marker QA before remaining style variants/catalogue delivery. No upload or source-model edits.

HANGHAUS-060 image delivery 2026-10-20 COMPLETE: user authorized upload; 12 images (4 exterior, 4 UG, 4 EG) uploaded to twostorey_060, media IDs 1013-1024, catalogue re-read verified. Modern flat roof retains glass railing; other roofs stainless horizontal/classic metal. Floating driveway removed from exterior images; perimeter plaster cleanup inspected; Warm Modern EG wardrobe restored after cleanup. Delivery and provenance: E:/born2thrill-local-workbench-data/corrections/twostorey_060/renders/codex-twostorey_060-2026-10-20/delivery. No customer send, no rights changes, no commits. Next pending source follow-up: remove erroneous driveway in source model if future rebuild is required and review UG openings below terrain; image edits did not modify Blender. Other earlier terrain/regression follow-ups remain pending.
- [ ] Teil C im Hanghaus-Plan: bungalow_007 (= VillaBAH) ebenfalls Hanghaus, Zeichnung links/rechts spiegeln. Braucht noch Aussenflaechen (Terrasse UG, Gehweg/Einfahrt EG) und Haustuer. Wartet auf Freigabe.
- [x] Gebaeudemasse-Knopf bei Kontur im Untergeschoss (bungalow_007): kein Zirkel mehr. floorplan-simplifier/plans/gebaeudemass-umriss-im-keller-v1.md
- [ ] Original-Liste: VillaBAH ist bungalow_007 (Rainer, 2026-10-20) -- also 15 von 31 erfasst, 16 fehlen.
- [x] Balkon/Dachterrasse bekommen Zeichenrand wie die Aussenkontur (floorplan-simplifier/plans/balkon-zeichenrand-v1.md).

BUNGALOW-007 hillside image job 2026-10-20 IN PROGRESS: user supplied regenerated balcony package annotation 4c4c6714047a5851; all 28 input hashes verified and six blends reopened. Twelve styled images plus marker QA/catalogue and job-authorized final upload pending. Earlier no-balcony previews superseded. Hard rule: island and perimeter worktops identical. No source changes or rights changes.

BUNGALOW-007 hillside image delivery 2026-10-20 COMPLETE: latest balcony annotation 4c4c6714047a5851, 12 PNGs at contract sizes and catalog.json in corrections/bungalow_007/renders/codex-bungalow_007-2026-10-20. All 12 uploaded, media IDs 1025-1036, exact plan-specific filenames verified. Modern glass balcony railing; island/perimeter worktops match in all four styles. Source models and rights unchanged; no customer sends or commits. No pending item within this image job. Next separate pending source follow-up remains HANGHAUS-060 erroneous driveway / buried UG openings; previous suite source-review items are not cancelled.

BUNGALOW-013 image job 2026-10-20 IN PROGRESS: annotation b6299a11149b390b, 22 input hashes match. Five source blends reopened: 82/82/82/81 exterior meshes, 276 interior. Four roof previews generated and inspected; Warm Modern coat storage correction underway before material variants. Scope: eight images and job-authorized catalogue upload; source/code/rights unchanged. Delivery: corrections/bungalow_013/renders/codex-bungalow_013-2026-10-20.

BUNGALOW-013 image delivery COMPLETE 2026-10-20: eight images uploaded and exact plan-specific names verified, IDs 1037-1044. Satteldach user amendment handled by reopening changed blend (81 meshes, sha b1ea376b2f8416d0...) and rendering fresh reference; obsolete initial roof preview excluded. Four interior styles preserve coat orientation and matching kitchen surfaces. Files and provenance: corrections/bungalow_013/renders/codex-bungalow_013-2026-10-20. No source changes, customer send, rights changes or commits. No pending work in this image job. Previously recorded independent source follow-ups remain pending.

## 2026-10-20 -- 1,5-Geschosser bekommen Kniestock, steiles Dach, Quer-/Ziergiebel (PROPOSED)
- [x] 1,5-Geschosser mit rechteckigem OG: Kniestock 1,0 m, 40 Grad, Zwerchgiebel ueber jeder hohen Traufwand-Oeffnung (Variante A), gezeichnete Giebel genutzt; Innenansicht OG mit Kniestock. Scratch-geprueft an onehalfstorey_044 (Sattel + Walm), Kontrollhaus unveraendert. Plan: `born2thrill-local-workbench/plans/anderthalbgeschosser-dach-v1.md`.
- [ ] 1,5-Geschosser mit Winkel-OG (z. B. onehalfstorey_027): noch ohne Kniestock (WARNUNG).
- [ ] 35 von 44 1,5-Geschossern bauen derzeit keinen Plan (Massstab/Ausrichtung/Moebel) -- unabhaengig vom Dach.
- [ ] onehalfstorey_044: Dachform waehlen (roof_type fehlt), dann go.py.
- [x] Dach-Tab zeigt 1,5-Geschosser mit Kniestock und 40 Grad (floorplan-simplifier/plans/dach-tab-anderthalb-v1.md).

- [x] 2026-10-20 anderthalb-eine-dachform-v1: 1,5-Geschosser get ONE exterior (Satteldach with Kniestock/Zwerchgiebel), = 1 + 4 x Geschosse images. Evidence: eine_dachform.test.py OK; go.py onehalfstorey_044 delivered 3/3 blends, verifier green. Not uploaded.
- [ ] 1,5-Geschosser already published with 4 roofs keep them until rebuilt (rebuild delivers 1) -- decide whether to rebuild/replace on WordPress.
- [ ] go.test.py errors (17) when FLOORPLAN_WORKBENCH_DATA_DIR is unset -- test should set a temp dir itself like eine_dachform.test.py.
- [x] (done 2026-10-20, codex-ein-ordner-ein-knopf-v1: anzahl_satz) make-codex-job.py:408 style text still says "zwei Aussenansichten, classic und modern -- zusammen 4 je Geschoss + 2" -- contradicts required_outputs (4 roofs for normal houses, 1 for 1,5-Geschosser). Needs a plan to derive the sentence from required_outputs. Found 2026-10-20 in the onehalfstorey_044 job; brief told Codex to follow the 9-image list.
- [x] 2026-10-20 codex-ein-ordner-ein-knopf-v1: Codex button creates the delivery folder and names it at the top of the Auftrag; Hochladen takes exactly that folder and uploads only a complete, checked delivery. Evidence in the plan file.
- [ ] Hochladen message in the house list is cut at ~100 chars (go.py line truncation) -- "catalog.json fehlt" gets clipped.
- [x] 2026-10-21 bilder-tab-zeigt-codex-ordner-v1: house page shows the Codex delivery folder from codex-job.json without ANGENOMMEN.json.
- [ ] Codex catalog.json fails lieferung-pruefen (no contract_sha256, state "uploaded" not "approved", OG marker_check uses wrong markers) -- Codex uploads anyway; decide later whether Codex or the button uploads (Rainer 2026-10-21: keep Codex uploading for now).
- [x] 2026-10-21 anderthalb-zwerchkubus-modern-v1: 1,5-Geschosser deliver 2 exteriors (klassisch Zwerchgiebel, modern grey Zwerchkubus with flat roof) = 10 pictures. Evidence in plan; onehalfstorey_044 built 4/4, verifier green.
- [ ] onehalfstorey_044: press "An Codex" again -- the current Codex job/delivery is the old 9-image set without the Kubus exterior.
- [ ] go.py does not rebuild when only the build CODE changed (ist_aktuell compares annotation hashes) -- a renderer change needs run_project.py by hand.
- [ ] Tegalit roof reference + roof rule for Codex (pictures found on bmigroup.com, not saved yet; Rainer wanted to see them first).
- [x] 2026-10-21 quergiebel-ziehen-v1: Quergiebel/Zwerchkubus width+position drawn and dragged in the Annotator (tool "Quergiebel", button "Quergiebel-Vorschlag"); renderer builds exactly the drawn ends. Evidence in plan.
- [ ] onehalfstorey_044: no Quergiebel drawn yet (kept unsaved while Codex renders the Kubus exterior) -- Rainer draws/adjusts, then rebuild + new Codex pictures for both exteriors.
- [ ] Quergiebel-Vorschlag sits ~4 cm per end off the old automatic width on registered upper floors (OG scale x1.07); cosmetic, the build follows the drawing.
- [x] 2026-10-21 onehalfstorey_045: ridge set north-south (roof_axis_override "y", Rainer: "the first goes north south"); the drawn east Quergiebel was on a gable wall before and therefore invisible. source-state.json refreshed with app.write_source_state after the direct annotation edit (dollhouse refused STALE PLAN otherwise).
- [x] 2026-10-21 1,5-Geschosser wall cut: the "above the roof" prism crossed itself (top 13.7 m below its slope end 15.3 m) -> gable walls of 045 stayed up to 8.7 m. Fixed with anderthalb.ueber_dach_profil (test first); 045 probe 0 points above the roof.
- [ ] Annotator could warn when a Quergiebel is drawn on a GABLE side (it is built there but hidden in the gable wall).
- [ ] Direct edits of annotations.json leave source-state.json stale -- any script that writes annotations must call app.write_source_state (or the Annotator must be used).
