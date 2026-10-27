# Double-wall merge: merge only the overlap, keep the rest of each wall as it is

Status: DONE 2026-10-23

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-23, bungalow_tv1 (Blender screenshot): the exterior has a roof and a wall over the terrace. The house is an L, but roof, coping and foundation were built over the full rectangle.

## Current evidence

- Build log: `[plan] Doppelwand zusammengefasst: wall-0 + wall-10 (108 mm auseinander) -> interior`.
- Walls before the merge, from a spy on `_merge_overlapping_parallel_walls` on the real tv1 data:
  - `wall-0`: interior, Wohnen <-> Schlafen, x 8606, y 6172..10151, 115 mm;
  - `wall-10`: exterior, Wohnen -> terrace, x 8498, y 9948..15210, 240 mm.
  - They overlap only at the corner: 203 mm, just over the 200 mm limit.
- `build-simplifier-render-plan.py _merge_overlapping_parallel_walls()` (~1603-1688) then builds ONE wall over the union of both, y 6172..15210 (`t0, t1 = min(0, t[0]), max(laenge, t[1])`). It types the whole wall by probing only its MIDPOINT, which gives "interior".
- Result in plan-modern.json: the terrace facade is missing from the exterior walls (only wall-9, 11, 12, 13, 14 remain). `render-exterior.py trace_wall_loops` (~1205) cannot close the outer ring. The exterior .blend has `roof-deck`, `coping` and `foundation` over x 2.9..16, y 1..15.3, i.e. the full rectangle including the terrace.

## Exact scope (build-simplifier-render-plan.py only)

1. When two parallel walls overlap, merge **only the overlapping section** onto the shared centre line (thickness = the larger, rooms = both). Each wall's parts outside the overlap stay separate walls with their **own** type, position and thickness, so they meet the merged piece end to end.
2. The type of the merged piece is decided as today (rooms on both sides -> interior), but only for that piece.
3. Walls that overlap over (almost) their whole length behave exactly as today: no leftover pieces shorter than the existing 200 mm limit are produced. This is the onehalfstorey_029 case the rule was made for.

## Out of scope

- The 200 mm threshold itself; the exterior renderer; roof shapes.
- Other houses are only rebuilt when Rainer asks. Houses with a "Doppelwand zusammengefasst" line in their bau.log may change on the next build, in the direction of their drawn rooms.

## Tests (first)

- build-simplifier-render-plan.test.py, pure function on synthetic walls:
  - the tv1 pair (interior 6172..10151 at x 8606, exterior 9948..15210 at x 8498) -> one merged piece over the overlap only, plus an **exterior** remainder that reaches up to 15210. No wall typed interior extends beyond the room edge at 10151 +/- the corner.
  - two walls overlapping over their full length -> one wall, same as today (existing behaviour, onehalfstorey_029-like).
- Seam: run the real tv1 plan build; the walls on x ~8500..8600 north of y 10151 are exterior.
- All existing tests unchanged.

Real check: rebuild bungalow_tv1 (no upload). The exterior .blend's `roof-deck` and `foundation` must leave the terrace corner (x > 8.7 m, y > 10.3 m) free, and the flat-roof render must show the L without a roof over the terrace.

## Safety gate

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. Only the derivation of local build walls from the drawn rooms changes; nothing is uploaded or sent.

## Rollback

`build-simplifier-render-plan.py.before-doppelwand-teil`; remove the new tests.

## Approval record

Rainer in chat, 2026-10-23: "Approved: implement doppelwand-nur-ueberlappung-v1, tests first, rebuild bungalow_tv1 (no upload)."

## Implementation record (2026-10-23)

- `_merge_overlapping_parallel_walls()`: merges only the overlap [max(0,t0), min(len,t1)]. The parts of either wall beyond it become their own walls: same type, thickness and line, with id `<id>` for the partner's piece and `<id>-restN` for the own piece. They are appended to the working list, so they are checked too. Overhangs <= 200 mm are absorbed as before. The log line names the pieces.
- Tests first: scripts/doppelwand_teil.test.py, 5 cases. 2 were red before (terrace facade stays exterior; no interior wall past the room edge). 3 guard today's behaviour and were green before and after. All workbench Python suites OK, except the known red bungalow_039 door test in build-simplifier-render-plan.test.py (red before this change too).
- Live, bungalow_tv1 rebuilt (exit 0, 5 .blend certified, no upload). Log: `wall-0 + wall-10 -> interior | Rest wall-0-rest0 interior | Rest wall-10 exterior`. exterior-flachdach and -walmdach renders show the L with the terrace open and the terrace facade with its sliding doors. No roof or wall over the terrace any more.
- Noted, not changed: `render-exterior.py` builds `foundation` from the bounding rectangle (~1491). It lies at -0.15..0 m under the terrace paving and is not visible.
