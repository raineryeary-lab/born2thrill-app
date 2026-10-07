# Dollhouse cutaway: always exempt door/window frames, glazing and leaves

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-08-22, from a real Blender viewport screenshot of a rebuilt
bungalow_039: "fesnter sind fast überall gescnhtitten Kücehntür ist
gfeschnitten Eingagstür ist gescnrhitten" (windows are cut almost
everywhere, kitchen door is cut, entrance door is cut) — distinct from the
door-direction complaints already fixed in
`plans/door-hinge-swing-reference-frame-mismatch-v1.md`.

Root cause, measured directly against bungalow_039's real compiled plan,
not guessed: `wall_object()`'s opening exemption rule
(`build-simplifier-render-plan.py` is unrelated here — this is
`render-furnished-dollhouse.py` lines ~1059-1061) routes an opening's
frame/glazing/door-leaf into `cut_features` (sliced by the SAME diagonal
"dollhouse cutaway" plane as the wall around it) whenever the plane's
local height at that opening is BELOW the opening's own vertical
midpoint. The front-side cut height (`CUT_HEIGHT_FRONT_MM = 500`) is low
enough that on this house, 7 of 8 windows and exactly the two doors
Rainer named (Küche, Eingang — the only two doors reported as "cut", as
opposed to the direction-only complaints) land in that bucket and get
physically sliced through the middle by the same plane that hollows out
the wall for the camera view.

Asked Rainer directly how to handle it (three options: raise the front
cut height, always exempt openings from the cut, or leave as-is) —
answer: always exempt.

## Current evidence and behavior

Measured on bungalow_039's real `plan-modern.json`, replicating
`cut_plane_height()`'s own axis/slope math exactly:

```
window 55b7d2a8  plane=1.78m  mid=1.57m
window 48a0eca2  plane=1.48m  mid=1.57m   DOLLHOUSE-CUT
window a92f741f  plane=1.08m  mid=1.57m   DOLLHOUSE-CUT
window 60ff5e48  plane=0.82m  mid=1.57m   DOLLHOUSE-CUT
window 04f73e38  plane=0.64m  mid=1.57m   DOLLHOUSE-CUT
window e245566a  plane=1.13m  mid=1.57m   DOLLHOUSE-CUT
window b8541ecc  plane=1.32m  mid=1.57m   DOLLHOUSE-CUT
window c4550838  plane=1.53m  mid=1.57m   DOLLHOUSE-CUT
door   369138 (Küche)   plane=0.97m  mid=1.01m   DOLLHOUSE-CUT
door   a64838 (Eingang) plane=0.88m  mid=1.01m   DOLLHOUSE-CUT
(all other doors: plane >= mid, not cut)
```

- `render-furnished-dollhouse.py` `wall_object()`, lines ~1059-1061:
  ```python
  mid = (opening["sill_height_mm"] + cut_height / 2.0) * MM
  local = plane_h((centre[0] / MM, centre[1] / MM)) if plane_h else None
  target = cut_features if (local is not None and local < mid) else features
  ```
  `features` = exempt from the dollhouse cut, always rendered whole.
  `cut_features` = sliced by the SAME plane as the wall body
  (`_feature_slicer` loop, lines ~2127-2130).
- The surrounding comment block (lines ~986-1058) already documents that
  this exact rule was changed three times before (2026-08-17,
  2026-08-21), with two of the three alternatives explicitly rejected as
  worse (full-height cut through every opening; a permanent solid block
  around every opening), and carries "Do not change this rule again
  without being asked to." Rainer has now been asked, directly, and chose
  the third option this session's investigation surfaced but that history
  hadn't tried: always exempt, full stop, no conditional based on the
  local plane height.
- Known, already-documented risk of blanket exemption (from the same
  comment block, 2026-08-17): on the Obergeschoss, ordinary windows with a
  900mm sill sat with NO wall left below them once their wall was cut away
  by a lower local plane — "whole window panes floated outside a building
  with no elevation left." Rainer chose this option WITH that risk stated
  in front of him in the option description ("even if that means an
  opening with little/no wall around it in places").

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `scripts/render-furnished-dollhouse.py`: not otherwise touched this
  session before this plan.

## Exact scope

In `wall_object()`, replace the conditional target selection with an
unconditional one: every opening's frame/glazing/door-leaf always goes
into `features` (exempt), never `cut_features`. Remove the now-dead
`mid`/`local` computation. Update the surrounding comment block to record
this decision (date, quote, and the still-open floating-window risk on
upper storeys) rather than deleting the prior history — the same pattern
every other comment block in this file already follows.

No change to how the WALL BODY itself is cut (`cut_solid`/
`flat_cut_solid`, `apply_cut()` on `wall_bodies`/`uncut_walls`) — only to
which bucket an opening's own geometry lands in.

## Files in scope

- `scripts/render-furnished-dollhouse.py` (`wall_object()`'s opening loop
  and its surrounding comment only).

## Explicitly out of scope

- `CUT_HEIGHT_FRONT_MM`/`CUT_HEIGHT_BACK_MM` values themselves — unchanged,
  the wall body cut stays exactly as dramatic as before; only openings
  stop being sliced with it.
- The Obergeschoss "shell stays whole" rule (`DMH_SHELL_WHOLE`,
  `uncut_walls`) — untouched, separate mechanism.
- `flat_cut_solid`/`PARTITION_CUT_MM` partition-wall handling — untouched.
- The already-fixed door hinge/swing direction bug — separate, already
  shipped.
- Not fixing the floating-window-on-upper-storey risk this change
  reopens; Rainer chose this option with that risk already described.
  Revisit only if it's actually observed on a real upper-storey house
  after this ships.

## API, schema, and data-contract effects

None. Purely which Blender objects a wall's opening features end up in
during the render build; no change to plan JSON, annotations, or any
external schema.

## Acceptance criteria

- Rebuilding bungalow_039: all 7 previously-flagged windows and the
  Küche/Eingang doors render with their frame, glazing/leaf whole and
  intact — no longer visibly sliced through the middle.
- Every other opening (already exempt before this change) is unaffected —
  this change only ever WIDENS the exemption, never narrows it, so nothing
  that rendered whole before can start being cut.
- `sliced_features` end up empty (openings never populate it any more);
  no crash or behavior change in the downstream loops that already handle
  a possibly-empty list.

## Tests and verification commands

No existing automated test exercises Blender-side geometry (all
`verify_render_blend.py`/`verify_render.py` checks are structural —
stair/Geländer/symbol-size/wall-angle — not opening-slice detection), and
building a new one would mean scripting a Blender-side geometry probe for
a single visual regression, which the existing test suite for this file
does not do anywhere else. Verification is:

```
cd born2thrill-local-workbench
FLOORPLAN_WORKBENCH_DATA_DIR="E:\born2thrill-local-workbench-data" python scripts/run_project.py bungalow_039 --styles modern,classic
```

Existing `verify_render_blend.py`/`verify_render.py` checks (R0-R6,
wall_angles, opening_count, stairs) must still all PASS — confirms this
change did not break anything those checks already cover. Visual
confirmation of the 7 windows + 2 doors via the "An Codex" tab's
open-in-Blender buttons, same as the door-direction fix's own
verification step.

Existing tests are not deleted, skipped, or weakened.

## Protected and risky paths

- This touches code explicitly marked "Do not change this rule again
  without being asked to" — mitigated by having been asked, directly, in
  this session (see Objective), with the known risk stated up front.
- Re-opens a previously-fixed floating-window risk on upper storeys with
  low sills. Mitigated by: Rainer choosing this with that risk explicitly
  named; and by `DMH_SHELL_WHOLE`'s separate, still-active rule that keeps
  upper-storey EXTERIOR walls whole (not cut at all) by default — the
  floating-window failure mode required BOTH a cut wall AND an exempt
  opening at the same time, and the wall side of that pairing already
  defaults off for upper-storey exteriors.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference? Required answer: no. Purely a
render-time visual-cutaway rule change; no new geometry source.

## Customer, email, database, deployment, and external effects

None directly. bungalow_039 becomes stale under the existing toolchain
hash and needs rebuilding (already done as part of this plan's
verification).

## Failed-hypothesis log

Not applicable — root cause measured directly against real compiled plan
data (axis position, plane height, opening midpoint) before writing this
plan.

## Rollback

Pure code change, one function, one comment block. Revert to undo;
nothing else touched.

## Unresolved questions

None — resolved directly via AskUserQuestion this session.

## Completion record (2026-08-22)

Implemented as scoped: `wall_object()`'s opening loop
(`scripts/render-furnished-dollhouse.py`) now sets `target = features`
unconditionally; the `mid`/`local` computation is removed; the
surrounding comment block records this decision, the quote that drove it,
and the accepted floating-window risk, alongside the prior history
(nothing deleted). `plane_h` remains a `wall_object()` parameter (still
passed by the caller, still used elsewhere for the wall body's own cut)
but is no longer read inside `wall_object()` itself — left in place as a
harmless no-op rather than touching the function signature, which was
outside this plan's stated scope.

Rebuilt bungalow_039 end-to-end (`run_project.py bungalow_039 --styles
modern,classic`): both styles' full verification suite passed unchanged
(`wall_angles`, `opening_count`, `R0`-`R6`, stair/Geländer checks).

Directly inspected the rebuilt `interior-modern-baseline.blend` via a
one-off Blender geometry probe (Z-extent of every opening-related
object), not just the structural pass/fail checks: all 6 doors
(`wall-0/1/4/5/8/11-door`) render at their full 0.000-2.010m height,
including `wall-4-door` (Küche) and `wall-11-door` (Eingang) — the exact
two doors reported as "geschnitten." All 4 windows
(`wall-9/10/11/12-frame-jamb`/`-glass`) render at their full 0.900-2.250m
extent (sill 900mm, height 1350mm), none truncated. No opening in the
file shows a squashed Z-range.

Files changed: `scripts/render-furnished-dollhouse.py`.

## Second approval record (2026-08-22, night)

The exemption's visual consequence (full-height door leaves standing in
knee-high walls, floating window frames on the front kerb) drew Rainer's
"look at your fucking blender file" — the text-option approval above had
not shown him the picture. Re-decided properly with an A/B IMAGE
comparison on the real bungalow_039 (A = always exempt/full height, B =
openings cut flush with their own wall's slicer): Rainer picked **A**.
The exemption therefore stands, now backed by an image-level judgment;
the B implementation (a temporary `DMH_OPENING_CUT` env branch) was
deleted the same night so no half-alive alternative path remains. Any
future change here needs a new image comparison, not a code toggle.

## Approval record

Approved by Rainer, 2026-08-22, via explicit choice among three
alternatives ("Always exempt openings from this cut"), with the known
floating-window risk on upper storeys stated in the option description
before the choice was made.
