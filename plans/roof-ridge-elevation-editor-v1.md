# Roof ridge elevation editor (side-view, draggable ridge point) — v1: gable, rectangular footprint only

Status: APPROVED / IMPLEMENTED (v1 + Doppelpult amendment)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer: "can we maybe add a sideview to edit the roof sloping? also with editable points but oyu
also have to fill up the holes, or ask codex" — followed, after being shown the size/risk tradeoff
between a small per-project pitch field and a full point-editable roof, by: "i would rather do B"
(the full side-view point editor).

Today roof pitch is not project-specific at all: `PITCH_DEG`/`PULTDACH_PITCH_DEG`/
`SATTELDACH_PITCH_DEG` are Python module constants in `render-exterior.py` shared by every
project of that roof type (confirmed 2026-09-19 while fixing `twostorey_050`'s roof — that fix
changed the angle for the whole corpus at once, not just one house). There is no per-point roof
data anywhere; roof shape is derived in one shot from the footprint plus one global angle.

This plan scopes a FIRST increment only: a side-view (elevation) editor in the annotator, for
**satteldach (gable) roofs on rectangular footprints**, where the user can drag the ridge point
to change roof height and/or ridge off-center position. Eave height and wall height are
deliberately UNCHANGED in this increment (see "Explicitly out of scope" — raising an eave without
growing the wall beneath it is exactly the kind of hole Rainer flagged, and it needs its own
design pass). Mono-pitch, hip, and irregular (non-rectangular) footprints are also out of scope
for this increment; each has its own distinct failure modes (see Codex review below) and should
be separate follow-up plans once this smallest complete slice is proven end-to-end.

## Current evidence and behavior

Researched 2026-09-19 via three read-only investigations (Annotator canvas architecture, roof
mesh generation, plan-template conventions) plus a Codex read-only design review. Key findings:

1. **No per-project roof-shape data exists today.** `roof_type_modern`/`roof_type_classic` are
   the only per-project roof fields (`gebaeudemass.json`, written by `scripts/dachform.py`).
   Pitch angle is a global constant (`render-exterior.py:887,898,905`). `roof_overhang_mm` is the
   one other per-project roof number (`annotations.json`).

2. **Roof mesh generation is a one-shot closed-form derivation, not built from editable points.**
   For a rectangular footprint (`render-exterior.py:1178-1244`): `inset = min(width,depth)/2`,
   `rise = inset * tan(pitch)`, ridge position/length and gable-vs-hip end-face treatment all
   derive from this. For satteldach specifically, `ridge_inset = 0.0` (line 1228) — ridge runs
   the full building length, two end faces become vertical gable triangles, reassigned from
   `ROOF_MAT` to `FACADE` (lines 1258-1261, added 2026-09-19 same session).

3. **A near-identical "editable per-piece" approach was already tried and abandoned.** Comment at
   `render-exterior.py:30-35`: bpypolyskel (the current straight-skeleton solver for irregular
   footprints) "replaces the earlier rectangle-decomposition roof (independent ridge heights per
   piece -> looked like stacked separate roofs at every wing boundary)". `merge_roof_massing()`
   (lines 447-476) is dead code left over from that abandoned approach. This is the direct
   precedent for why "just let any point move freely" is unsafe without care — confirms Rainer's
   own instinct ("you have to fill up the holes").

4. **The annotator has no existing single-point free-drag interaction anywhere.** Existing point
   patterns (`floorplan-simplifier/static/`): click-to-place while drawing (`annotate.js` canvas
   click/dblclick handlers), marquee-select + arrow-key nudge with undo (`punkte-ausrichten.js`,
   `punkte-verschieben.js`), and whole-element drag-to-translate (`element-edit.js:127-179`). A
   new elevation editor with a draggable ridge handle is a new interaction pattern, not a reuse of
   an identical one — closest precedent is `element-edit.js`'s drag mechanics.

5. **The `layer-tab` mechanism (`geometry-tools.js:447-467`, `setActiveLayer`) is the natural
   integration point for a new view mode** (existing tabs: "architektur", "exterior") — more
   appropriate than a new `floorSelect`-style entity, since an elevation view is a different tool
   mode over the same building, not another floor. `zoom-pan.js` (200 lines, DOM-element-based,
   no floor-plan-specific dependencies) is reusable as-is for the new view's own zoom/pan state.

6. **`architectural_features`** (`app.py`, written via `annotate.js:300-335`, currently only
   `type: "gable"` metadata entries) is an existing generic per-floor extension point that could
   plausibly carry roof-ridge parameters without a new top-level schema key — subject to
   `normalize_architectural_feature()` in `app.py` accepting new fields (not yet verified in
   detail; part of this plan's implementation work, not assumed).

7. **Codex read-only design review (2026-09-19, full transcript in
   `plans/codex-reviews/roof-ridge-editor-design-review-2026-09-19.md`, see below) found one
   critical gap this plan's scope reduction was built to avoid, plus several concrete failure
   cases:**
   - **Walls do not grow with a raised eave.** Wall-top heights are fixed independently of roof
     geometry (`render-exterior.py:983-1023`, `1091-1103`). Raising an eave without growing the
     wall beneath it leaves a real gap — "every roof-point constraint can pass, yet a gap
     remains above the walls." This is why v1 keeps eave height fixed and only exposes the ridge.
   - A rectangular gable roof's ridge CAN move sideways and vertically as a single handle without
     inherently creating cracks, **provided both 3D ridge endpoints move together** (shared
     height and transverse position) rather than independently.
   - Square-footprint hip roofs need an explicit single-apex topology (not two coincident ridge
     vertices) — not applicable to gable, but documents why hip is excluded from v1.
   - Overhang: today's roof corners sit on the outward-offset perimeter (`line 1170`), computed
     BEFORE the ridge; not touched by this plan since overhang stays fixed in v1.
   - Solidify (220mm thickness, `lines 1262-1265`) has known failure modes for short ridges/
     extreme slopes that can only be confirmed by an actual Blender render, not by code review —
     acceptance criteria below require a real render, not just JSON-level validation.
   - Recommends persisting the ridge parameter in canonical mm geometry so editor and Blender
     derive identical results, and explicitly invalidating any existing staleness/verification
     gate when a roof is edited (mirroring the `geometry_identity` pattern already used for
     furniture) rather than letting an edited roof silently reuse an old approved render
     reference.
   - Notes `EXT_ROOF_TYPE` env var override (`render-exterior.py:62-70`) as a separate manual
     debug path that must not be confused with the new per-project stored parameter.

Full Codex output saved verbatim to
`C:\Users\Admin\AppData\Local\Temp\claude\C--dev-Floorplan-tools\093f2b6e-b6aa-4a53-b9cc-8deb1ef9db0b\scratchpad\codex-roof-out.md`
pending a decision on whether to commit it into `plans/codex-reviews/` (see Unresolved questions).

## Repository baselines

**`C:\dev\Floorplan-tools\floorplan-simplifier`** (annotator UI): branch
`agent/annotation-window-type-door-swing`, HEAD `8a08d19a09928f04585ceaf553b9ff1440eca33b`, 133
changed paths (pre-existing dirty worktree from prior sessions, not caused by this plan).

**`C:\dev\Floorplan-tools\born2thrill-local-workbench`** (render pipeline): branch
`agent/furnished-render-and-annotation-schema`, HEAD
`5be1a4e18956b9fb2e158bee82aa159898356e89`, 218 changed paths (pre-existing dirty worktree,
includes this same session's roof-pitch/gable-material and per-floor-outline work, not yet
committed).

Both repos' pre-existing dirty state is unrelated prior work from this and earlier sessions, not
new changes made for this plan. No commits made yet for this feature.

## Exact scope (v1 increment only)

1. **New elevation/side-view layer tab** in the annotator, following the existing
   `setActiveLayer` pattern, showing a simple side elevation for the active floor: left eave
   point, ridge point, right eave point, drawn as a 2D cross-section (fixed geometry, informational
   only, except for the ridge).
2. **Ridge point is draggable** (vertical = ridge height / pitch; horizontal = off-center ridge
   position within the footprint). Eave points are shown but NOT draggable in v1 (fixed at
   today's wall-top height).
3. **Eligibility gate**: the tab/editor is only offered when the active floor's roof-supporting
   footprint (the actual top-storey wall loop the renderer uses, `render-exterior.py:959-968` —
   not a naive re-check) is rectangular AND `roof_type` for the relevant style is `satteldach`.
   Any other combination shows an explanation, not a broken or silently-ignored editor.
4. **Persistence**: ridge parameters (height offset from default, horizontal offset from center)
   stored per floor in canonical mm geometry, keyed so `build-simplifier-render-plan.py` and
   `render-exterior.py` derive the identical ridge position Blender-side as the editor shows.
   Exact storage location (new `architectural_features` entry vs. a new field) to be finalized
   during implementation per point 6 above and documented here before coding begins.
5. **Staleness invalidation**: editing the ridge must invalidate whatever existing
   staleness/verification gate governs that floor's approved render reference (the same class of
   mechanism as the furniture `geometry_identity` stamp) — investigate the actual existing gate
   (referenced in this session's build-log output as "0 style(s) verified and ready") before
   implementing, rather than assuming its shape.
6. **`render-exterior.py` change**: replace the closed-form `rise = inset * tan(pitch)` for
   satteldach-on-rectangle with a value derived from the stored ridge height/offset when present,
   falling back to today's global-constant behavior when absent (so every existing project with
   no ridge override renders byte-identical to today).
7. **Minimum/maximum clamps** on ridge height and horizontal offset to prevent degenerate roofs
   (near-zero slope, ridge outside the footprint, ridge closer to an eave than some minimum run) —
   exact clamp values to be set from real Blender-render testing during implementation, not
   guessed up front.

## Files in scope

- `C:\dev\Floorplan-tools\floorplan-simplifier\static\annotate.js` (new layer tab wiring, side
  elevation draw call, ridge drag handling, save-payload field)
- `C:\dev\Floorplan-tools\floorplan-simplifier\static\geometry-tools.js` (`setActiveLayer`
  extension point)
- `C:\dev\Floorplan-tools\floorplan-simplifier\static\zoom-pan.js` (reused as-is for the new
  view's zoom/pan, only touched if it turns out NOT to generalize cleanly)
- `C:\dev\Floorplan-tools\floorplan-simplifier\app.py` (persistence: new field validation/
  normalization, alongside existing `normalize_architectural_feature`/`normalize_outer_outlines`-
  style functions)
- `C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\build-simplifier-render-plan.py`
  (carry the new ridge parameter into the render-plan JSON)
- `C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\render-exterior.py` (satteldach
  rectangle branch, lines ~1215-1244: read stored ridge override when present)
- New test files alongside existing ones (`floorplan-simplifier/tests/`,
  `born2thrill-local-workbench` test dirs) — exact names finalized during implementation
- `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md` (follow-up tracking only, per
  governance)

## Explicitly out of scope (this increment)

- Draggable eave points / wall-height coupling (Codex-identified critical gap — needs its own
  plan once v1's editor+persistence+staleness plumbing is proven).
- Mono-pitch (pultdach) and hip (walmdach) roof editing.
- Any non-rectangular (L-shape, irregular) footprint — these keep today's global-pitch
  straight-skeleton behavior completely unchanged.
- Overhang editing, gable-material/geometry relocation (both currently sit on the
  overhang-expanded perimeter, not the wall plane — untouched since v1 doesn't move eaves/overhang).
- The single-linked-height handle for irregular footprints that Codex noted as a cheap possible
  future addition (`bpypolyskel`'s `height` parameter) — worth a follow-up roadmap item, not this
  plan.
- The pre-existing "Bauen rebuilds .blend but not final PNGs" gap noted in ROADMAP.md
  (`AUSSENUMRISS-JE-GESCHOSS-001` nachtrag) — unrelated, tracked separately.

## API, schema, and data-contract effects

New field(s) added to the annotation/render-plan schema for ridge height/offset; existing
projects without this field must render byte-identical to today (verified explicitly, see
Acceptance criteria). No existing field renamed, removed, or repurposed. Exact field shape
finalized during implementation and recorded here before the first commit touching schema.

## Acceptance criteria

1. A satteldach, rectangular-footprint project with NO stored ridge override renders
   pixel-identical (or negligibly different — same seed/camera) to its current baseline render.
2. Dragging the ridge point in the new elevation view and saving produces a stored parameter that,
   fed through `build-simplifier-render-plan.py` and `render-exterior.py`, produces a real Blender
   render showing the roof ridge at the edited height/offset, with the roof mesh solid (no visible
   gap, no self-intersection) — verified by an actual render, not JSON inspection alone.
3. The eligibility gate correctly hides/explains the editor for: pultdach/walmdach/flachdach
   projects, and satteldach projects on a non-rectangular footprint.
4. Attempting a degenerate ridge position (at/beyond a clamp boundary) is rejected or clamped,
   not silently producing a broken mesh.
5. Editing the ridge invalidates the floor's existing render-approval/staleness gate exactly as a
   room-geometry edit already does for furniture today (no silent stale-but-marked-fresh state).
6. Existing test suites (`floorplan-simplifier`, `born2thrill-local-workbench`) remain fully green;
   no existing test weakened, skipped, or deleted.

## Tests and verification commands

To be finalized once field storage location (point 4 of Exact scope) is decided, but must
include at minimum:
- Unit test(s) for the new ridge-height/offset -> mesh-parameter math (pure function, testable
  without Blender).
- Unit test(s) for the eligibility gate (rectangular satteldach detection using the actual
  top-storey roof-support loop, not a naive re-derivation).
- Unit test(s) for schema round-trip (save with ridge override -> reload -> same value) and for
  the no-override backward-compatibility path.
- `python -m unittest discover -s tests -p "test_*.py"` (floorplan-simplifier) green.
- Existing `born2thrill-local-workbench` test suite green.
- At least one real Blender render (`render-exterior.py`) for a rectangular satteldach project
  with a non-default ridge override, visually inspected, per this session's established rule
  ([[verify_against_user_visible_surface]]): code-internal consistency is not sufficient proof.

## Protected and risky paths

`render-exterior.py`'s satteldach/rectangle branch (lines ~1215-1244) and the shared
hip/gable vertex construction it reuses with walmdach — must not regress walmdach (unedited,
no ridge-override path) or pultdach in the process. `annotate.js`'s existing outer-outline and
layer-tab logic must not regress (both were fixed earlier this session and are covered by
existing behavior this plan must not disturb).

## Rights, provenance, privacy, and security impact

None. No new external data source, no customer data touched, no change to corpus rights/
provenance status.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected
corpus reference?

Required answer: no. This plan adds an editable roof parameter to the existing internal
annotation/render pipeline only; it does not add or change any customer-delivery, publication, or
email path. The existing WordPress manual-email gate and delivery-manifest verification are
untouched by this plan's scope — and per acceptance criterion 5, an edited roof must correctly
invalidate that verification, not bypass it.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

Not yet applicable — no implementation attempted yet (Status: PROPOSED).

## Rollback

All changes are additive (new optional field, new UI tab, new fallback-preserving code branch).
Rollback is `git checkout --` on the files in scope, or removing the new field from a saved
project's annotation JSON to fall back to today's global-constant behavior. No destructive
operation, no data migration, no irreversible step anywhere in this plan.

## Unresolved questions

1. Exact storage shape for the ridge parameter (new `architectural_features` entry vs. a new
   dedicated top-level field) — needs a short look at `normalize_architectural_feature()` in
   `app.py` before committing to one, not a blocking decision for Rainer.
2. What the existing render-verification/staleness gate actually is (referenced in this session's
   build log as "Stil(e) nicht verifiziert" / "0 style(s) verified and ready") and how a roof edit
   should hook into it — needs investigation during implementation, not assumed.
3. Whether to commit the full Codex design-review transcript into `plans/codex-reviews/` for
   permanent record (matches this suite's practice of citing prior Codex findings by file path in
   ROADMAP.md) — low-stakes, can decide at implementation time.
4. Exact clamp values (minimum ridge-to-eave vertical run, minimum horizontal margin from the
   footprint edge) — Codex flagged these need real Blender-render testing, not analytical
   derivation; will be set empirically during implementation.

## Approval record

Approved by user on 2026-09-19: "yes make a tab with roof editor also add an option for a double
pult dach where you can add a vesetzer pult". Implementation authorized, including the
Doppelpult amendment below.

## Amendment 2026-09-19 (same approval): versetztes Doppelpultdach

Scope change from "gable only" to one shared cross-section polyline, left eave -> P1 -> [P2] ->
right eave, extruded along the long axis (`scripts/roof_profile.py`):

- `satteldach`: one point (P1 == P2), ridge height + off-centre position.
- `doppelpultdach`: two points at different heights; same u = vertical plaster step ("Versatz"),
  different u = sloped/flat strip between them.

Decisions taken during implementation (all reversible, none touches walls or eaves):
1. Storage is a top-level `roof_profile` in `annotations.json` (like `roof_overhang_mm`), not an
   `architectural_features` entry. It is exterior dressing: never part of `geometry_hash`
   (`app.py:248` comment), so the Codex suggestion to invalidate an approval stamp does not apply
   -- Bauen regenerates every exterior from the current annotations anyway.
2. Delivery stays at exactly 4 roof-form exteriors (hard rule): a house whose profile form is
   `doppelpultdach` delivers `exterior-doppelpultdach-baseline` IN THE SATTELDACH SLOT
   (`run_project.py roof_types_for_plan`); the superseded satteldach .blend is moved aside by
   `trim_to_delivery` as usual.
3. Eaves and walls unchanged (Codex's wall-gap finding still applies to any future eave editing).
4. Gable/step caps sit at the overhang-expanded ends, as the existing satteldach gable did.

## Completion record

What changed: `scripts/roof_profile.py` + `roof_profile.test.py` (new, 20 tests);
`render-exterior.py` (profile branch, `doppelpultdach` type, non-rectangle fallback message);
`build-simplifier-render-plan.py` (`roof_profile` into the plan); `run_project.py` (slot swap);
floorplan-simplifier `app.py` (`normalize_roof_profile`, save), `annotate.js` (state/save/load),
`annotate.html` (Dach tab), `geometry-tools.js` (layer hook), `dach-editor.js` (new),
`tests/test_roof_profile.py` (new, 6 tests).

Verification: roof_profile 20/20; simplifier suite 271 + 6 new green; `hausdaten.test.py` 37/37.
Live in the annotator on `twostorey_050`: tab, form switch, drag of P2, field sync, save, reload of
the saved value. End to end: saved profile -> plan JSON -> Blender: doppelpult rise 1.826 m as
edited; off-centre gable (u=0.35, 2.6 m) and tall versetzt (1.2/3.2 m) rendered and inspected; a
satteldach render with a doppelpult profile saved ignores it (rise 0.446 m, old formula).
Mesh proof (unit test, five profile shapes, both orientations): the upward-facing roof area
equals the footprint area exactly, so no gaps; no directed edge is used twice.

Remaining risks: preview in the editor derives width from the outline/rooms and the canvas aspect
(approximate; the renderer clamps with the true span); other consumers of exterior file names
(catalogue/WordPress prefix matching, `verify_render`) were not exercised with a
`doppelpultdach` file; Solidify on extreme profiles only proven within the clamps; irregular
footprints untouched (still walmdach fallback).

Rollback: remove `roof_profile` from a project's annotations.json (or choose "Standard" in the Dach
tab and save); revert the files above. No data migration.

Live test note: `twostorey_050` was used for verification; its `roof_profile` was reset to none
afterwards. Both furniture `geometry_identity` stamps were refreshed after a 37/37 point-in-polygon
check (rooms had changed since the last stamp).

## Amendment 2 (2026-09-19, same approval chain): a profile per form, 4th slot chosen

Rainer: "wouldn't it be better if i could save each edit? we need all 4 so i should be able to
save the satteldach and the versetzte Pultdach and maybe a checkbox at the top satteldach
Pultdach versetztes Pultdach ? and save each one" and, asked which 4 deliver: "Flach Walm
Satteldach (Pultdach oder Versetzes Pultdach)".

- Storage is now `roof_profiles` = one saved profile per form (`satteldach`, `pultdach`,
  `doppelpultdach`) plus `roof_fourth` (`pultdach` default, or `doppelpultdach`). The earlier
  single `roof_profile` key is gone (it only ever held test data, none in the corpus).
- Pultdach is a fourth editable shape: one point on the left or right edge; the high side is a
  plumb plaster wall. Unsaved Pultdach/Satteldach still build exactly as before.
- Delivery: Flach, Walm and Satteldach always; the 4th slot is Pultdach or, when ticked in the Dach
  tab, Versetztes Pultdach (`run_project.py roof_types_for_plan` swaps only the pultdach slot).
  Supersedes decision 2 of the first amendment (satteldach slot).
- UI: form buttons at the top of the Dach tab (each marked when it has its own profile), a
  "Als 4. Dachform liefern" checkbox, per-form Standardwerte and Speichern.

Verification: roof_profile 25/25; simplifier suite 282 green (incl. 11 roof-profile tests);
live in the annotator: all three forms edited and saved in one session, reloaded state matched;
plan JSON carried all three profiles and `roof_fourth`; Blender renders of each form showed the
saved heights (satteldach 1.9 m off-centre, pultdach 1.3 m high side left, versetzt 0.9/2.0 m);
`roof_types_for_plan` returned Flach/Walm/Satteldach/Doppelpult. `twostorey_050` was reset to no
profiles and `pultdach` as 4th afterwards.

## Amendment 3 (2026-09-19): the wall carries the roof

Rainer: "the reall roof on a satteldach is basically like a piece of paper folded in the middle
laid over the house ... the left over triangle would be the extended wall and with the Pultdach
the same, you cant just have the roof in the air."

Correct, and my first build did neither: the gable triangle sat at the far edge of the overhang
(0.5 m outside the wall) and the default Pultdach had no wall at all (roof floating).

- `roof_profile.profile_mesh()` is now ONLY the folded roof sheet (a gable = 2 faces, a Pultdach =
  1 face, a versetztes Pult = 2 slopes + its inner plaster step).
- New `roof_profile.wall_extension()`: closed plaster prisms on the house's own wall planes,
  flush with the walls below, wall-thick: two end walls following the roof line (gable triangle,
  Pultdach side, stepped gable) spanning the full outer width, plus long walls under the eaves where
  the roof is higher than the wall top (the Pultdach's high side). Tops are tucked 5 cm into the
  roof slab and never above the roof surface.
- Satteldach and Pultdach ALWAYS build from this path now (a saved profile or the 5 degree default),
  so every house gets the walls, not only edited ones. Walmdach and Flachdach are untouched.
  The old satteldach/pultdach code and the two global angle constants in `render-exterior.py`
  are removed (dead).
- Editor: the plaster region is drawn on the wall planes; no wall at the roof's outer edge.
- Tests: `roof_profile.test.py` rewritten for sheet + walls (30): walls closed and outward, flush
  with the wall planes, start at the wall top, never poke through the roof (this caught a 3 mm
  poke-through on slopes and a missing corner column), gable apex reaches the ridge, Pultdach high
  side walled to the roof. My earlier tests that encoded "unsaved uses the old code" were
  replaced on purpose (the design changed at Rainer's direction).
- Verified in Blender on twostorey_050: Satteldach (his saved 1.95 m ridge), Pultdach (5 deg
  default), versetztes Pultdach, Walmdach.

