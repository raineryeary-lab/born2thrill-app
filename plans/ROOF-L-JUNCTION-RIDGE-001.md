# L-house roof: the branch ridge runs through the main roof

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

On L-shaped houses, the Satteldach / Versetztes Pultdach of the smaller wing must end
in a proper valley (Kehle) at the main roof. It must not run straight through the main
roof and stick out the far side.

## Current evidence and behavior

House: `german_catalog_review_bungalow_3_5_1_b_145`, go-baseline renders of 2026-10-04 08:46
(`E:\born2thrill-local-workbench-data\corrections\german_catalog_review_bungalow_3_5_1_b_145\renders\go-baseline\`).
Rainer's Blender screenshot and my own probe renders (scratchpad `sat_obl*.png`) show it.

I probed `roof-pitch` in `exterior-satteldach-baseline.blend`:
- Wing A (front, x 1.98..11.4, y 0.94..7.6, ~63 m2): ridge along y at x=6.69, **ridge z 4.30**,
  and the ridge vertices run from y=0.44 to **y=14.79**, the far edge of the house.
- Wing B (back, full width 12.76 m, y 7.6..14.79, ~92 m2): ridge along x at y=11.22, **ridge z 3.92**.

Cause, from the code:
1. `render-exterior.py` ~1520 picks the main wing **by area**, so B is main and A becomes the branch.
2. Both wings get the same pitch. A's span (9.4 m) is wider than B's (7.2 m), so the
   *branch* gets the *higher* ridge.
3. `roof_profile.chevron_roof_construction()` (~1843) extends the smaller-area wing's ridge
   until `_depth_to_match_height()` reaches the main roof's height. B never gets to 4.30 m,
   so the extension runs to B's far edge, and A's ridge pokes out the back.
   The Doppelpultdach log shows the same 2-wing chevron path, and the same defect is in the render.

`decompose_rectangles()` always slices in horizontal rows, so the L comes out as
"full-width back + front stub". The other cut, "full-length left wing 9.4x13.85 + small
right stub 3.3x7.2", would give a main wing with the wider span and a branch with the lower ridge.

## Repository baselines

born2thrill-local-workbench, branch `agent/furnished-render-and-annotation-schema`,
HEAD 5be1a4e18956b9fb2e158bee82aa159898356e89, 256 pre-existing dirty/untracked entries
(user-owned, untouched). `scripts/render-exterior.py`, `scripts/roof_profile.py` and
`scripts/roof_profile.test.py` are **untracked**, so before editing I copy them to
`*.before-roof-l-junction` as the rollback copies.

## Exact scope

In the chevron path only (`satteldach`/`pultdach`/`doppelpultdach`, non-rectangular, >=2 wings):
1. Try both orthogonal decompositions of the footprint (row slices as today, plus column slices).
2. Choose the one where every branch's ridge height is <= the wing it attaches to. Tie-break:
   today's choice. If neither qualifies, keep today's choice and log a clear warning
   (no silent guess).
3. Main wing = the wing with the widest cross span among the chosen decomposition's wings
   (area stays the tie-break). `roof_axis_override` keeps its current meaning.

## Files in scope

- `scripts/render-exterior.py` (decomposition choice + main-wing selection only)
- `scripts/roof_profile.test.py` (new tests only)

## Explicitly out of scope

- `chevron_roof_construction()` internals, walls, overhang rules, hip/flat roofs, rectangular houses.
- T/U shapes with 3+ wings beyond what the same rule covers. Logged in the roadmap if they
  still fail.
- Re-rendering or uploading any other house.

## API, schema, and data-contract effects

None. No annotation, gebaeudemass or profile format changes.

## Acceptance criteria

1. Satteldach on 3_5_1_b_145: in the built `.blend`, no roof vertex of the branch lies beyond
   the main wing's ridge line, and the branch's ridge z is <= the main ridge z.
2. Same for the Doppelpultdach.
3. Whole-image check of both baseline exteriors plus one top-down probe render. Rainer confirms visually.
4. Regression: re-build `bungalow_001` and `german_catalog_review_bungalow_4_3_1_wb_125`
   (the two houses the chevron path was tuned on). Their roof vertex sets must stay
   unchanged, or every change must be explained.

## Tests and verification commands

New tests in `roof_profile.test.py`:
- An L where the narrow-but-long wing has the wider span chooses the column decomposition.
- In an L where both cuts are fine, the result is identical to today's.
- No branch ridge is higher than its main wing's ridge for the chosen decomposition.

`python scripts/roof_profile.test.py` (existing tests must stay green, none changed).
Then the go-baseline exterior rebuild for 3_5_1_b_145 + the Blender probe script.

## Protected and risky paths

The chevron path is used by every non-rectangular gable/pult house. Mitigation: regression
houses in acceptance criterion 4.

## Rights, provenance, privacy, and security impact

None. This only touches local render geometry, not rights state.

## Floorplan-suite invariant

No. This only changes how an already-annotated footprint is split for roof building. It does
not publish, upload or email anything, and it does not touch the approval/rights gates.

## Customer, email, database, deployment, and external effects

None. No upload.

## Failed-hypothesis log

(empty)

## Rollback

Copy the `*.before-roof-l-junction` files back over the three scripts.

## Unresolved questions

- Should this also fix the Pultdach (single pitch) the same way? Planned: yes, same code path.

## Approval record

Not approved. Stop before implementation.
