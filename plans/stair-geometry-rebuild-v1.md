# Stair geometry rebuild (Treppe neu gebaut) + Sockel unter dem Obergeschoss

Status: COMPLETE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-08-23, on onehalfstorey_029's upper floor: *"your stairs are still
shit"* and *"there is a rail blocking the stairs"*.

Two defects, one file:

1. **FIX A** — the Treppenloch balustrade is built straight across the point
   where the flight arrives, so the top of the stair is walled off.
2. **FIX B** — the flight itself is not a stair. At every turn of the drawn
   Lauflinie the tread degenerates into a self-intersecting quad that measures
   the full 1000 x 1000 mm of the turn and overlaps its neighbours.

Follow-on task added by Rainer the same day (same file, same pass):

3. **FIX C (Sockel)** — an upper storey renders floating in mid-air. Build the
   storeys below it as an uncut socket so the rendered storey has something to
   stand on, and keep the camera on the rendered storey.

The three reference implementations Rainer supplied are the spec for FIX B:

| file | type |
| --- | --- |
| `simple_quarter_turn_stair_blender.py` | viertelgewendelt: flight, square landing, 90 deg turn, flight |
| `simple_half_turn_stair_blender.py` | halbgewendelt mit Podest: two parallel flights + landing |
| `true_half_turn_winder_stair_blender.py` | echte halbgewendelte Treppe: flight, wedge winders through 180 deg, flight |

Their conventions are adopted: `FLOOR_HEIGHT / STEP_COUNT` gives the riser,
tread `top_z = n * riser` with the tread hanging `TREAD_THICKNESS` below it,
`TREAD_DEPTH` 270-280 mm, `STAIR_WIDTH` 1000 mm, landing = full width x width.

## Current evidence and behavior

Measured (not assumed) with a Blender probe against the built baseline
`E:\born2thrill-local-workbench-data\corrections\onehalfstorey_029\renders\go-baseline\interior-modern-upper-baseline.blend`:

Plan `shared_stair_core` (from `annotation_stair_core()`):

```
path_mm      (9357.4, 4344.3) -> (11075.1, 4344.3) -> (11075.1, 5616.0) -> (9274.6, 5616.0)
polygon_mm   bbox x 9274.6..11575.1, y 3844.3..6116.0   (2300.5 x 2271.7 mm)
plan_type    "half_or_multi_turn"    declared_type null    inferred_type "halbgewendelt"
usable_width_mm 1000.0
geometry     {"riseMm": 175, "goingMm": 280, "risers": 16}      <-- hard-coded constant
```

Lauflinie legs: 1717.7 + 1271.7 + 1800.5 = **4789.9 mm** total run.

Built scene, upper storey:

* **16** `stair-step-*` objects, rise **175.0 mm** each (measured top-to-top),
  tread depth **280 mm**, width **1000 mm**, thickness 50 mm.
* The run does follow the drawn path: steps 1-6 centred on y = 4344.3,
  steps 8-10 on x = 11075.1, steps 12-16 on y = 5616.0.
* **BUT** `stair-step-7` and `stair-step-11` measure **1000 x 1000 mm** — they
  are the treads that straddle the two 90 deg vertices. Their back riser line is
  taken on the incoming leg and their front riser line on the outgoing leg, so
  the quad `(back_in, front_in, front_out, back_out)` is a **bow tie**. Step 7
  (x 10.575..11.575, y 3.844..4.844) fully swallows step 6
  (x 10.757..11.037, y 3.844..4.844); step 8 overlaps step 7 again. That is the
  "shit" — two of sixteen treads are not treads.
* Top step: `stair-step-16`, x 9.585..9.865, y 5.116..6.116, top z 2.620 m.
  The flight uses 16 x 280 = 4480 of the 4789.9 mm run and **stops 310 mm short
  of the drawn Austritt** at x = 9274.6.
* `loch-rail-west`: x 9.250..9.300, **y 3.844..6.116** — the FULL west edge of
  the Loch, with 9 balusters, standing directly in front of the top step's exit.
  Confirmed: the balustrade is built straight across the stair exit.
* Storey floor: the arrival room `floor-1784479681063_d10ed38d330d`
  (x 7.066..9.275, y 3.909..6.322) has its top at z 2.620 — level with the top
  tread, so the arrival height itself is right.
* Lower storey (`interior-modern-baseline.blend`): **5** steps, truncated at the
  dollhouse cut plane exactly as intended. This must not regress.

Two further facts that constrain the rebuild:

* `STOREY_HEIGHT_M` in the renderer is `wall_height (2400) + FLOOR_SLAB_M (220)`
  = **2620 mm**, but the stair climbs 16 x 175 = **2800 mm**. The riser count is
  a hard-coded literal in the plan builder and does not come from the storey.
* The drawn well is 2300 x 2272 mm. A **Podesttreppe** would spend
  2271.7 mm of the 4789.9 mm run on the landing, leaving 2518 mm of flight for
  15 risers = 168 mm going. That is not a stair. The same well as a **wound**
  stair spends the turn run on winder treads, which each earn a riser. Only the
  wound stair fits what Rainer drew.

## Repository baselines

* Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
* Branch: `agent/furnished-render-and-annotation-schema`
* Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
* Pre-existing dirty worktree (NOT mine, preserved): `data/simplifier-v2/corpus-ledger.json`,
  `data/simplifier-v2/dataset.json`, `package.json`, `scripts/build-simplifier-render-plan.py`,
  `scripts/render-furnished-dollhouse.py`, `scripts/start-floorplan-workbench.ps1`,
  `src/app/api/floorplan-workbench/corrections/route.ts`,
  `src/app/api/floorplan-workbench/reviews/route.ts`,
  `src/app/floorplan-workbench/page.tsx`; untracked `data/simplifier-v2/dataset.json.vor-ergaenzung-2026-08-20`,
  `data/visual-catalog/`, `docs/CODEX-HANDOFF.md`, `docs/CODEX-STANDING-TASK.md`.
* Roadmap repo: `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md`

## Exact scope

### FIX A — the blocking rail

The Treppenloch balustrade must leave an **Austritt**: the rail segment in front
of the arriving flight is omitted, leaving a gap of at least the stair width.
The zone is computed from the stair's own top tread (its front riser line and
its direction of travel), not from a hard-coded side. Every other edge of the
Loch keeps its balustrade, so `R2_gelaender` still passes.

### FIX B — the stair

Driven by `plan_type` and the drawn path:

* **straight** — one flight along `path_mm`.
* **quarter_turn / half_or_multi_turn** — one of two constructions, chosen by
  the rule below.
  * **landing (Podesttreppe)** — flights + a flat landing filling the turn
    region; the landing is one riser, level with itself, and the flights carry
    the rest, exactly as in reference files 1 and 2.
  * **winder (gewendelt)** — the sharp vertex of the Lauflinie is replaced by a
    **circular arc centred on the band's INNER corner with radius = half the
    stair width**. Treads are then set out along that filleted Lauflinie with
    riser lines perpendicular to it, which on the arc are exactly radial from
    the inner corner: proper tapered winder treads, as in reference file 3.

#### The turn-type rule (this is the rule asked for)

> A turn is built as a **landing** only if the drawn Lauflinie is long enough to
> carry all the risers on straight flights once the landing has taken its room.
> Otherwise the turn is **wound**.

Formally, in `stair_turn_style()` in the plan builder:

1. Each interior vertex claims a landing zone of `usable_width_mm` along the
   Lauflinie (half the width either side of the vertex) — the square landing of
   the reference scripts.
2. Zones closer than one going apart are **merged** into one landing, so the two
   90 deg vertices of a U become a single landing across both flights, which is
   what reference file 2 builds.
3. `flight_run = total_run - sum(landing zone lengths)`.
4. Each landing IS one of the risers (you step up onto it), so only
   `risers - len(zones)` treads have to fit on the flights. If
   `flight_run >= (risers - len(zones)) * MIN_GOING_MM` (260 mm, DIN 18065
   Auftritt for a notwendige Treppe) the turn is a **landing**; otherwise it is
   a **winder**.
5. An explicit `stair_type` in the annotation still wins: `podest` forces a
   landing, `viertelgewendelt` / `halbgewendelt` force a winder.

This is the geometric reading of Rainer's "a wide turn = landing type, a tight
turn = winder": a turn is wide when the well it is drawn in still has room for
the flights beside it. For onehalfstorey_029: landing zones [1217.7, 2217.7] and
[2489.4, 3489.4] are 271.7 mm apart (< one going) so they merge to
[1217.7, 3489.4] = 2271.7 mm; `flight_run` = 2518.2 mm;
`(15 - 1) * 260 = 3640 > 2518.2` => **winder**. The stair Rainer drew is an
echte halbgewendelte Treppe.

#### Anchoring and riser count

* Riser count comes from the storey, not a literal:
  `risers = round(STOREY_HEIGHT / target rise 175)` => 15 for a 2620 mm storey,
  `rise = STOREY_HEIGHT / risers` = 174.7 mm.
* Going is distributed over the run that is actually drawn:
  `going = clamp(flight_run / flight_treads, 260, 350)`, so the flight starts at
  `path_mm[0]` and ends at `path_mm[-1]` instead of stopping 310 mm short.
* If even 260 mm going will not fit, as many treads as fit are built and the
  shortfall is reported in the log line, as today.

### FIX C — Sockel under a rendered upper storey

* For a storey that is not the lowest, the walls of every storey **below** it are
  also built, at `level * STOREY_HEIGHT_M`, from that storey's own walls in the
  plan (exterior and interior).
* The socket is **not** cut by the dollhouse plane and keeps its full height.
  Only the rendered storey keeps its cutaway.
* Window and door **openings are cut** into the socket. No furniture, no leaves,
  no frames, no glazing — speed over detail.
* Every socket object is named `sockel-...`. The `wall-N` namespace is left
  alone so `R0_symbol_sizes` and `R8_opening_heights`, which index objects by
  `wall-<enumerate index>`, keep judging only the rendered storey.
* The camera frames the **rendered storey's** bounding box only. The socket may
  leave the bottom of the frame.
* Switch: `DMH_SOCKEL=0` disables it; default on for non-lowest storeys.

## Files in scope

* `scripts/build-simplifier-render-plan.py` — `annotation_stair_core()`,
  new `stair_turn_style()`, storey-derived `geometry`, `turn_style` carried
  through the corrected-document path.
* `scripts/render-furnished-dollhouse.py` — the stair block, the Treppenloch
  balustrade, the socket, the camera target.
* `scripts/verify_render_blend.py` — new `R9_stair_access`, wired into `main()`.
* `scripts/build-simplifier-render-plan.test.py` — tests for the new plan-builder
  logic.
* `plans/stair-geometry-rebuild-v1.md` — this document.
* `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md` — follow-ups.

## Explicitly out of scope

* The floor-slab **winding inconsistency**: `polygon_object()` solidifies against
  the face normal, so a room whose polygon is wound clockwise gets its slab
  extruded upwards (top at +220 mm) and a counter-clockwise room downwards (top
  at 0). Both occur on onehalfstorey_029's upper storey. The stair keeps the
  existing anchor (foot at the storey base) rather than chasing this. Recorded on
  the roadmap.
* Which flank of a straight flight carries the balustrade (`+b` is assumed).
* WordPress, publishing, uploading, approval, email, any external system.
* The correction-document stair path beyond passing `turn_style` through.

## API, schema, and data-contract effects

`shared_stair_core` gains one optional field, `turn_style`
(`"straight" | "landing" | "winder"`), and `geometry.risers` / `geometry.riseMm`
become storey-derived instead of the constants 16 / 175. Consumers that ignore
unknown keys are unaffected; the renderer falls back to computing the style
itself when the field is absent, so an old plan still builds.

## Acceptance criteria

1. No `loch-rail-*` object stands in the arrival zone of the top tread; the gap
   is at least `usable_width_mm` wide.
2. `R2_gelaender` still passes: the Loch keeps a balustrade on its other edges.
3. No two `stair-step-*` tread polygons overlap in plan by more than 10 % of the
   smaller tread's area.
4. The top tread's walking surface is level with the storey it arrives on.
5. The lower storey's flight is still truncated by the dollhouse cut plane.
6. `python scripts/build-simplifier-render-plan.test.py` passes, with new tests.
7. `python scripts/go.py onehalfstorey_029` ends `fertig`, all rules PASS.
8. `python scripts/go.py bungalow_039` still builds (single storey, stairless).
9. Upper-storey render: rendered storey still cut open, socket solid beneath it,
   camera centred on the rendered storey, and `R0` / `R8` still evaluate only
   the rendered storey's `wall-N` objects.

## Tests and verification commands

New, added before the implementation:

* `StairTurnStyleTests` in `scripts/build-simplifier-render-plan.test.py`
  — straight path, a wide quarter turn (landing), a tight quarter turn
  (winder), onehalfstorey_029's real U (winder), landing-zone merging, and
  `declared_type` override.
* `StairGeometryFromStoreyTests` — `geometry.risers` follows the storey height
  and `riseMm * risers` equals it.
* `R9_stair_access` in `scripts/verify_render_blend.py` — arrival zone clear of
  railings, top tread reachable, treads not overlapping. Run by Blender inside
  the real build, so it is verified by running the build.

Commands:

```
python scripts/build-simplifier-render-plan.test.py
FLOORPLAN_WORKBENCH_DATA_DIR='E:\born2thrill-local-workbench-data' python scripts/go.py onehalfstorey_029
FLOORPLAN_WORKBENCH_DATA_DIR='E:\born2thrill-local-workbench-data' python scripts/go.py bungalow_039
```

No existing test is deleted, skipped, weakened, or rewritten.

## Protected and risky paths

* `scripts/verify_render_blend.py` runs inside Blender: a syntax or API error
  there fails every build. Verified by a real build, not by reading.
* The dollhouse-cut truncation in the stair loop is load-bearing for the lower
  storey and is left byte-identical in behaviour.
* Object naming (`wall-N`, `floor-*`, `stair-step-*`) is read by the verifier.
  The socket must not enter those namespaces.

## Rights, provenance, privacy, and security impact

None. Geometry is read from the existing annotation/correction inputs and
rendered locally. No corpus record, provenance flag, or eligibility state is
touched.

## Floorplan-suite invariant

> Can any changed path generate, publish, or email geometry without matching an
> approved corrected corpus reference?

**No.** The changed code is the local renderer, the local plan builder and the
local blend verifier. Publication still runs only through `publish-renders.py`
behind `go.py --hochladen`, and approval still through `approve-plan.py`; neither
is touched. `not_for_delivery` and `source_provenance` handling is unchanged. The
new `turn_style` field is derived from geometry already in the plan and adds no
new source of geometry.

## Customer, email, database, deployment, and external effects

None. No upload, no `--hochladen`, no approval.

## Failed-hypothesis log

1. *"Build the U as a Podesttreppe, like reference file 2."* Computed the landing
   from the drawn path: the merged landing zone is 2271.7 mm of a 4789.9 mm
   Lauflinie, leaving 2518 mm for 15 risers = 168 mm going. Conclusion: rejected;
   the drawn well is too small for a landing stair, which is what produced the
   turn-type rule above.
2. *"Fillet the Lauflinie with a semicircle of radius half the flight spacing,
   like reference file 3."* r = 1271.7 / 2 = 635.9 mm centred between the two
   vertices puts the outer edge of the turn at x = 12211 mm, 636 mm **outside**
   the drawn polygon at x = 11575.1, i.e. under the floor slab. Conclusion:
   rejected; the fillet is instead centred on the band's inner corner with
   radius = half width, which touches the polygon edges from inside and fits
   exactly.
3. *"Anchor the flight on the measured floor-slab top so the first tread is not
   sunk."* The slabs are inconsistent (some top at +220, some at 0) because of
   the solidify winding, so the anchor would differ per room and could break
   `R2_stair_built`. Conclusion: out of scope, roadmap item; keep the storey-base
   anchor.

## Rollback

`git checkout -- scripts/build-simplifier-render-plan.py scripts/render-furnished-dollhouse.py scripts/verify_render_blend.py scripts/build-simplifier-render-plan.test.py`
and delete `plans/stair-geometry-rebuild-v1.md`. Both changed scripts were
already dirty before this task, so restore from the base SHA only after checking
the pre-existing diff. Rebuilt artifacts under
`E:\born2thrill-local-workbench-data\corrections\<id>\renders\go-baseline\` are
regenerated by re-running `go.py`.

## Unresolved questions

* None outstanding. (The "second drawn stair" question was measured away: no
  project in the corpus draws two stairs on one storey — see the completion
  record.)

## Approval record

Task delegated with explicit instruction to write this plan and then implement
FIX A, FIX B and FIX C in the same pass; treated as the approval for the scope
written above.

## Completion record

Implemented and verified 2026-08-23.

### What changed

`scripts/build-simplifier-render-plan.py`

* New `STOREY_HEIGHT_MM` / `TARGET_RISE_MM` / `NOMINAL_GOING_MM` / `MIN_GOING_MM` /
  `MAX_GOING_MM` constants, kept in step with the renderer.
* New `stair_risers_for_storey()`, `stair_landing_zones()`, `stair_turn_style()`.
* `annotation_stair_core()` now emits `turn_style` and a storey-derived
  `geometry` (`risers` 15, `riseMm` 174.67 for a 2620 mm storey) instead of the
  literal `{"riseMm": 175, "risers": 16}`.
* The corrected-document path carries `turn_style` through.

`scripts/render-furnished-dollhouse.py`

* `STOREY_HEIGHT_M` hoisted next to `FLOOR_SLAB_M` (it is still used unchanged in
  the storey-elevation section).
* The stair block rebuilt: riser count from the storey, the Lauflinie filleted at
  wound turns with an arc centred on the band's inner corner at radius = half the
  flight width, landing zones merged and built as the convex hull of the turn
  region, going spread over the drawn run, `top_step_front` / `top_step_dir`
  tracked.
* `rail_run()` takes a `gap`; new `arrival_gap()` measures the Austritt off the
  top tread and splits the Treppenloch balustrade around it.
* New Sockel section (FIX C) and a socket-aware ground plane.

`scripts/verify_render_blend.py`

* New `R9_stair_access` with helpers `_xy_quad`, `_tread_polygon`,
  `_polygon_area`, `_convex_overlap_area`, `_separated`; wired into `main()`.

`scripts/build-simplifier-render-plan.test.py`

* New `StairTurnStyleTests` (8) and `StairGeometryFromStoreyTests` (4).
  30 tests before, 42 after. No existing test touched.

### Before / after, measured on onehalfstorey_029's upper storey

| | before | after |
| --- | --- | --- |
| `stair-step-*` | 16 | 15 |
| rise | 175.0 mm (16 x 175 = 2800 into a 2620 storey) | 174.7 mm (15 x 174.67 = 2620 exactly) |
| going | 280 mm | 291 mm (4360.7 mm filleted run / 15) |
| degenerate treads | 2 (`stair-step-7`, `-11`, 1000 x 1000 mm bow ties) | 0 |
| overlapping tread pairs (R9) | 6 | 0 |
| top tread | x 9.585..9.865, 310 mm short of the drawn Austritt | x 9.275..9.565, front edge exactly on `path_mm[-1]` |
| top tread height | 2620 mm | 2620 mm (level with the arrival room's floor) |
| `loch-rail-west` | y 3.844..6.116 (2272 mm, full edge, across the exit) | `loch-rail-west-0` y 3.844..5.066 (1222 mm) |
| Austritt gap | 0 mm | **1050 mm** (stair width 1000 mm) |
| turn type | fanned bow ties, no type decision | `turn_style="winder"`, halbgewendelt |
| Sockel | none (storey floating) | 15 walls / 16 openings, uncut |

Lower storey unchanged where it must be: still 5 `stair-step-*`, truncated at the
dollhouse cut plane, `floor slab top z 0.220`.

### Verification

```
python scripts/build-simplifier-render-plan.test.py        -> Ran 42 tests, OK
go.py onehalfstorey_029                                     -> fertig
go.py bungalow_039                                          -> fertig
```

`verify_render_blend.py` run against every built interior blend:

* `interior-modern-baseline.blend` (groundfloor): R0, R2 x2, R3, R8, R9 all PASS
* `interior-modern-upper-baseline.blend` (upperfloor): R0, R2 x2, R3, R8, R9 all PASS
* `bungalow_039` `interior-modern-baseline.blend`: all PASS (stairless, no Sockel)

R9 was proven in **both** directions before it was allowed to gate: run against
the pre-change `interior-modern-upper-baseline.blend` it FAILS with exactly the
two defects Rainer named — six overlapping tread pairs and
`loch-rail-west` plus four of its balusters in the arrival zone of
`stair-step-16`.

### Git

Branch `agent/furnished-render-and-annotation-schema`, base SHA
`5be1a4e18956b9fb2e158bee82aa159898356e89`. Changed by this task:
`scripts/build-simplifier-render-plan.py`, `scripts/render-furnished-dollhouse.py`
(both already dirty before this task — the diff mixes with pre-existing work),
`scripts/verify_render_blend.py` and `scripts/build-simplifier-render-plan.test.py`
(both UNTRACKED in this checkout, so `git checkout --` will not restore them —
roll those back from the `.before-*` sibling copies or by reverting the two new
blocks by hand), plus this plan file and the roadmap entry. Nothing else in the
dirty worktree was touched.

### Remaining risks

* The floor-slab winding inconsistency (roadmap `STAIR-SLAB-WINDING-001`) means
  the flight is anchored to the storey base, not to the measured floor. On
  onehalfstorey_029 the arrival happens to be exactly level; on a house whose
  arrival room winds the other way the top tread would sit 220 mm below its
  floor. R9's arrival clause tolerates that band deliberately rather than
  failing a scene for a defect that lives elsewhere.
* Only the first drawn stair is built (roadmap `STAIR-SECOND-FLIGHT-001`).
  Counted across the corpus on 2026-08-23: 98 projects have a drawn stair, 65 of
  them with a turn, and **0** have more than one stair on the same
  `floor_level` — the "second stair" is always the same flight redrawn on the
  storey above, so `drawn[0]` is correct today.
* A wound turn whose fillet will not fit on its legs degrades to a Podest at that
  vertex. That path has no house exercising it yet.
