# Door hinge_side/swing_side: annotator and renderer used different reference frames

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer: "Schlafzimmertür falsche richtung Wohnesstimmer tür auch Bürpo Tür
auch Eingangstüer auch Küchentür auch fesnter sind fast überall gescnhtitten
Kücehntür ist gfeschnitten Eingagstür ist gescnrhitten cocuh ist nicht
gespeigelt" — multiple doors the user manually set a swing direction for
(via the annotator's `swing_side`/`hinge_side` dropdowns) render in the
WRONG direction. Root cause, precisely measured, not guessed: the
annotator's own live preview (`drawDoorSwing`, added this session in
`plans/door-swing-preview-for-unrecorded-doors-v1.md`, and the
hand-set-value path that already existed before it) interprets
`hinge_side`/`swing_side` relative to the door ELEMENT's own two drawn
points (`points[0]` → `points[1]`). The render pipeline
(`add_door_leaf()`, `render-furnished-dollhouse.py`) interprets the exact
same stored strings relative to the WALL's own `start_mm`/`end_mm` order
instead — a direction that has nothing to do with the door's own points,
decided incidentally by which room's edge produced that wall segment first
in `build_walls()`'s pairing loop.

When a door's own two points happen to run the SAME direction as its
wall, both interpretations agree by coincidence. When they run OPPOSITE,
every hand-set choice comes out backwards in the render while still
looking correct in the annotator's own preview — exactly what Rainer is
seeing, and exactly why "redid all of the doors" (in the annotator, where
it previews correctly) didn't fix the render.

## Current evidence and behavior

Measured directly on bungalow_039's real annotation + compiled walls (not
a hypothesis): for each of the 6 doors with an explicitly recorded
`swing_side`/`hinge_side`, compared the door element's own point direction
(`points[0]`→`points[1]`, mm-space via `frame.point()`) against its
resolved wall's `start_mm`→`end_mm` direction:

```
39265e  (Schlafen–Diele)   agrees
40c789  (Bad–Diele)        agrees
f1af94  (HWR–Diele)        agrees
369138  (Diele–Küche)      OPPOSITE   <- "Küchentür"
5d6a18  (Diele–Gast/Büro)  OPPOSITE   <- "Büro Tür"
a64838  (Haupteingang)     OPPOSITE   <- "Eingangstür"
```

Every door Rainer named as wrong (Küche, Büro, Eingang) is exactly the set
where the two reference frames disagree. `8ece0b` (Wohnen/Essen–Diele) has
no explicit setting at all — its direction comes from the automatic
smaller-room heuristic only, a separate, already-working code path not
touched by this bug (its "wrong direction" complaint, if it persists after
this fix, is a heuristic-preference question, not this bug — see
Explicitly out of scope).

- `static/annotate.js` `drawDoorSwing()` (both this session's new preview
  path and the pre-existing recorded-value path): `hinge = element.
  hinge_side === "end" ? second : first` and `direction = element.
  swing_side === "second_room" ? 1 : -1` — both relative to the door's own
  `first`/`second` points, confirmed by direct code reading.
- `render-furnished-dollhouse.py` `add_door_leaf()`: `if annotated_hinge ==
  "start": hinge_sign = -1.0` compared against `wall["start_mm"]`/`wall[
  "end_mm"]`, and `if annotated_swing == "first_room": swing_sign = 1.0,
  target = side_a` where `side_a`/`side_b` are determined by the wall's own
  normal direction — confirmed by direct code reading, this session,
  earlier (door-collision-fix work).
- `build_floor_walls_and_openings()` (`build-simplifier-render-plan.py`,
  shared by both the main render path and `geometry_only()`) is where the
  door element's own two points (`a`, `b`, already frame-converted to the
  SAME mm space as the wall) are available at match time, and where
  `swing_side`/`hinge_side` get copied verbatim from the annotation into
  the opening dict `add_door_leaf()` later reads — the one place both
  reference frames are simultaneously in scope, and therefore the one
  place to reconcile them.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `scripts/build-simplifier-render-plan.py`: already modified, uncommitted
  this session (walls/openings, area_m2, wall-merge-offset fixes, all
  already implemented and verified). This plan's fix lands in the SAME
  function (`build_floor_walls_and_openings`) touched by the walls/openings
  work, not the merge-offset fix (different function).

## Exact scope

In `build_floor_walls_and_openings()`, right before appending to
`openings`, compute whether the door's own point direction (`b - a`)
agrees with its matched wall's direction (`wall["end_mm"] -
wall["start_mm"]`) via a dot product (both already in the same mm space —
no unit conversion needed). When it does not agree (dot product negative),
flip BOTH values into the wall's own frame before storing them:
`hinge_side "start"↔"end"`, `swing_side "first_room"↔"second_room"`. Every
downstream reader (`add_door_leaf()` today, anything else that reads
`opening["hinge_side"]`/`["swing_side"]` in the future) then always
receives values already expressed in the wall's own reference frame, and
the annotator's own preview — which is the thing the user actually looks
at when choosing a direction — becomes the authoritative, honored
interpretation.

Windows carry `swing_side`/`hinge_side` too only in the sense that these
fields are copied for every opening type uniformly; windows do not use
either field downstream (`add_door_leaf` is door-only), so this fix has no
behavioral effect on windows — flagged here only so the scope statement is
precise, not because windows need separate handling.

## Files in scope

- `scripts/build-simplifier-render-plan.py` (`build_floor_walls_and_openings`
  only).

## Explicitly out of scope

- `8ece0b`'s (Wohnen/Essen–Diele) automatic direction, and any other
  door with NO explicit `swing_side`/`hinge_side` — those never go through
  either reference frame's hand-set interpretation; if the smaller-room
  heuristic's result there is undesired, that is a separate, already-known,
  already-documented design choice (`SMALL_ROOM_OUTWARD_M2` exception,
  read this session), not this bug. Will re-check after this fix ships
  whether it still looks wrong and needs its own follow-up.
- The two SEPARATE complaints bundled in the same message —
  "fesnter sind fast überall gescnhtitten" (windows cut almost
  everywhere) and "cocuh ist nicht gespeigelt" (couch not mirrored) — are
  different bugs in different code paths (window wall-cutting geometry;
  furniture mirror flag not reaching the render). Investigated and fixed
  separately, not folded into this plan, so each has its own clear
  evidence trail.
- No change to `annotate.js`'s own preview drawing — it is already
  correct FOR ITS OWN REFERENCE FRAME; nothing here changes what it shows.
- No change to the small-room-outward exception or any other part of the
  swing/hinge DECISION logic in `add_door_leaf()` — only which frame its
  inputs are expressed in.

## API, schema, and data-contract effects

None externally. Internal only: the RAW `swing_side`/`hinge_side` values
`build_floor_walls_and_openings()` returns in its `openings` list may now
differ from the raw annotation values for doors where the two frames
disagreed — by design, since that's the fix. `annotations.json` itself is
never written by this path (read-only consumer), so nothing the annotator
UI displays or edits changes.

## Acceptance criteria

- Rebuilding bungalow_039: `369138` (Küche), `5d6a18` (Gast/Büro), and
  `a64838` (Eingang) now swing in the direction their annotator preview
  already showed — i.e., the render matches what Rainer saw and chose when
  setting them, not the opposite.
- `39265e`, `40c789`, `f1af94` (the three that already agreed) are
  UNCHANGED — the fix must be a no-op wherever the two frames already
  matched, not a blanket flip.
- `8ece0b` (no explicit setting) is unaffected — the flip only ever
  applies to a door that HAS an explicit `swing_side`/`hinge_side` to flip.
- Byte-identical regression check on at least one other already-built
  house confirms no unintended change where every door's frames already
  agreed there.

## Tests and verification commands

New test, added to `scripts/build-simplifier-render-plan.test.py`
(already exists this session): assert, for the real bungalow_039 project,
that after this fix every opening's `wall_id` + `position` still resolves
correctly (unchanged from the existing test) AND that a synthetic
before/after comparison of `hinge_side`/`swing_side` for the three known
mismatched doors shows the expected flip while the three agreeing doors
are untouched — comparing against the exact table measured above, so this
is a real regression guard for this exact bug, not a synthetic
approximation.

Verification commands:

```
cd born2thrill-local-workbench
python scripts/build-simplifier-render-plan.test.py -v
python scripts\run_project.py bungalow_039 --styles modern,classic
```

Plus: re-inspect the rebuilt `interior-*.blend` (via this session's new
"An Codex" open-in-Blender buttons) and visually confirm the three
corrected doors now swing the way their annotator preview shows.

Existing tests are not deleted, skipped, or weakened.

## Protected and risky paths

- `build_floor_walls_and_openings()` is shared by the main render path AND
  `geometry_only()` (the furniture editor's 2D plan) — a change here
  affects both. Mitigated by the byte-identical regression check on
  another already-built house, and by the fix being conditional (only
  fires when the two frames disagree, provably a no-op otherwise).

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference? Required answer: no. This only
corrects which direction an ALREADY-DECIDED door swings; no new geometry
source, no publish/email path touched.

## Customer, email, database, deployment, and external effects

None directly. Indirect: bungalow_039's existing certified delivery
becomes stale under the existing toolchain-hash mechanism (same as every
prior fix today) and needs rebuilding — already the expected, correct
behavior after `go.py`'s own staleness fix earlier today.

## Failed-hypothesis log

Not applicable — root cause measured directly against real annotation +
compiled-wall data before writing this plan, not guessed.

## Rollback

Pure code change on an already-dirty, uncommitted working tree, one
function. Revert to undo; nothing else touched.

## Unresolved questions

None.

## Completion record (2026-08-22)

Implemented as scoped in `build_floor_walls_and_openings()`
(`scripts/build-simplifier-render-plan.py`): after matching a door onto
its wall, computed the dot product of the door's own point-order vector
(`b - a`, already in the same mm space as `wall["start_mm"]`/`["end_mm"]`
via `frame.point()`) against the wall's own direction; when negative
(opposite), flipped `hinge_side` (`start`↔`end`) and `swing_side`
(`first_room`↔`second_room`) before storing them, so every downstream
reader (`add_door_leaf()`) always gets values already expressed in the
wall's frame — matching what the annotator's own preview showed. Windows
carry the same two fields through unchanged (gated on `kind == "door"`),
matching the "no behavioral effect on windows" scope statement.

New test `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`
added to `scripts/build-simplifier-render-plan.test.py`, calling
`build_floor_walls_and_openings()` directly (not via `geometry_only()`,
whose short `openings_out` schema drops both fields) with the same
project setup `geometry_only()` itself uses. Confirmed against real
bungalow_039 data: the three previously-mismatched doors (Küche,
Büro/Gast, Eingang) are now flipped exactly as predicted; the three
already-agreeing doors (Schlafen, Bad, HWR) are provably unchanged. All 7
tests in the file pass.

Rebuilt bungalow_039 end-to-end: `python scripts/run_project.py
bungalow_039 --styles modern,classic` — both styles' full verification
suite passed (`wall_angles`, `opening_count`, `R0`–`R6`, stair/Geländer
checks, etc.), 3 `.blend` files certified per style, delivery manifest
written. Visual confirmation in Blender of the three corrected doors is
still pending (next step: open via the "An Codex" tab's blend buttons).

Files changed: `scripts/build-simplifier-render-plan.py`,
`scripts/build-simplifier-render-plan.test.py`.

## Approval record

Approved by Rainer, 2026-08-22 (explicit, detailed bug report — read as
approval to fix the confirmed root cause).
