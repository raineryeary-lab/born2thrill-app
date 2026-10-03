# Keep the realistic-camera cut height clear of the inter-storey slab

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Stop the inter-storey floor slab (the 220mm ring between two storeys) from
becoming visible as a grey/beige band along the top of exterior walls in
`camera_style: "realistic"` interior renders.

## Current evidence and behavior

- Rainer, 2026-09-14 (German): asked to watch, on the next Obergeschoss
  build, for rough wall-junction transitions and something that looks like a
  rug showing through the walls.
- Confirmed visually in `interior-modern-upper-baseline.png`
  (`E:\born2thrill-local-workbench-data\corrections\twostorey_045\renders\go-baseline\`)
  and independently in a second, later Codex delivery
  (`twostorey_045-complete-package-2026-09-14.zip`, image
  `07-floorplan-warm-modern-og.png`): a thin flat-toned band runs along the
  top of the upper floor's exterior wall exactly at the cut line, in both
  deliveries, at different wall corners.
- Root cause, from reading `scripts/render-furnished-dollhouse.py`:
  - `wall_height = 2400` (line 2588, fixed for every house).
  - The inter-storey floor slab ring (`slab-under-wall-*`, built at lines
    2738-2766) sits directly on top of that, from 2400mm to 2620mm
    (`FLOOR_SLAB_M = 0.22`).
  - `CUT_HEIGHT_BACK_MM` starts at 2000 (line 2800) and gets `+= 400` for
    `camera_style: "realistic"` (line 2813, added earlier in this session) --
    landing at exactly 2400mm, i.e. exactly the slab's underside, with zero
    clearance. The cut plane sits flush with the wall top, so the slab ring
    immediately above is exposed along the cut edge.
  - `CUT_HEIGHT_FRONT_MM` (900 realistic) stays far below 2400 and is not at
    risk.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `render-furnished-dollhouse.py` already shows as modified in
  `git status --short` from earlier work this session (camera_style,
  railing_sides, wall registration, per-tread handrail fix). This plan adds
  one more small, independent change to the same already-dirty file.

## Exact scope

In `scripts/render-furnished-dollhouse.py`, at the `camera_style == "realistic"`
block (lines 2811-2813), clamp `CUT_HEIGHT_BACK_MM` so it always stays below
the slab ring's underside by a fixed clearance:

```python
if PLAN_CAMERA_STYLE == "realistic":
    CUT_HEIGHT_FRONT_MM += 400
    CUT_HEIGHT_BACK_MM += 400
    # A cut flush with or above the inter-storey slab (wall_height is its
    # underside) exposes the slab ring as a band along the wall top
    # (Rainer, 2026-09-14/15). Keep clear of it regardless of wall_height.
    SLAB_CUT_CLEARANCE_MM = 150
    CUT_HEIGHT_BACK_MM = min(CUT_HEIGHT_BACK_MM, wall_height - SLAB_CUT_CLEARANCE_MM)
```

`wall_height` is already in scope (defined at line 2588, a fixed 2400 for
every house today). This keeps the requested "camera needs the cut ~40cm
higher" raise (2000 -> 2250, i.e. +250mm, still a substantial raise) while
guaranteeing the slab ring stays hidden even if `wall_height` ever changes.

## Files in scope

- `scripts/render-furnished-dollhouse.py` (one clamp line + comment)

## Explicitly out of scope

- `CUT_HEIGHT_FRONT_MM` (not at risk, no change).
- The `DMH_FLAT_CUT` override path (unaffected, applies after this block only
  in the sense both constants already exist by the time it would run --
  actually `DMH_FLAT_CUT` runs *before* the realistic block today; leaving
  the order as-is, out of scope).
- Any change to `FLOOR_SLAB_M`, `wall_height`, or the slab-ring construction
  itself.
- Re-rendering every existing house. Only `twostorey_045` gets rebuilt to
  verify (see Acceptance criteria); other houses' renders are stale in the
  ordinary course of business and rebuild next time they're touched, same as
  every other render-pipeline fix this session.

## API, schema, and data-contract effects

None. No plan-JSON or annotation schema change.

## Acceptance criteria

- `python -m py_compile render-furnished-dollhouse.py` succeeds.
- Rebuilding `twostorey_045` (`go.py twostorey_045 --laut`, both styles) and
  visually inspecting `interior-*-upper-baseline.png` shows no grey/beige
  band along the exterior wall tops (same crop regions as the evidence
  above).
- All existing `verify_render_blend.py` / `verify_render.py` checks still
  pass (R2_gelaender, R3_treppenloch, etc. -- none of them inspect
  `CUT_HEIGHT_BACK_MM` directly, so no regression expected, but the full
  suite is run anyway since `go.py` runs it regardless).

## Tests and verification commands

No existing automated test targets `CUT_HEIGHT_BACK_MM` specifically (checked:
no hits in `render-furnished-dollhouse.test.py` if one exists -- confirm
during implementation and add a small unit test there if that file covers
this kind of constant; otherwise verification is the rebuild + visual check
above, consistent with how this script's other geometry fixes were verified
earlier this session).

Existing tests: none deleted, skipped, or weakened.

## Protected and risky paths

- `scripts/render-furnished-dollhouse.py` is the production interior
  renderer for every house. Change is a one-line clamp with a fixed,
  generous margin (150mm) and only activates for `camera_style: "realistic"`,
  so `classic` (today's default, every existing house) is entirely
  unaffected.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This only clamps a camera/cut-plane parameter derived
from the already-approved corrected geometry; it generates no new geometry
and touches no publishing or email path.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

1. **Hypothesis:** the grey band is the inter-storey `slab-under-wall-*`
   ring becoming visible because `CUT_HEIGHT_BACK_MM` (2400mm, realistic)
   collides exactly with `wall_height` (2400mm), zero clearance.
   **Test:** implemented the clamp in this plan (`CUT_HEIGHT_BACK_MM = min(...,
   wall_height - 150)`), rebuilt `twostorey_045` fully (`go.py --laut`, 0
   excluded, all verify checks passed), visually re-inspected the same crop
   regions of `interior-modern-upper-baseline.png`.
   **Result: FAILED.** Band is pixel-for-pixel identical before and after.
   Confirmed independently by hiding every `slab-under-wall-*` object and
   re-rendering: band unchanged, still present with the slabs invisible.
   **Conclusion:** the slab ring was never the cause. Root cause is
   something else -- see below.
2. **Hypothesis (confirmed):** the band is one of the room's own `teppich-*`
   (rug) objects, correctly sitting on its own storey's floor, becoming
   visible through the gap *over* the deliberately-shortened cut-wall stub,
   because the "realistic" camera is a distant, shallow-angle perspective
   view that can see much further over a low wall stub than the old
   orthographic "classic" camera could.
   **Test:** raycast from the camera through the exact band pixels
   (`scene.ray_cast`) hit `teppich-1` at world Z=2.625m -- which is simply
   this storey's floor height (`STOREY_HEIGHT_M` ~2.62m) plus the rug's own
   ~3.5mm thickness, i.e. the rug sitting correctly on its own floor, not
   floating. Then hid every `teppich*`/`teppich-rand*` object and
   re-rendered: **band completely gone**, both crop regions clean.
   **Conclusion:** confirmed cause. This plan's clamp (which only ever
   moved `CUT_HEIGHT_BACK_MM`) left the problem untouched partly because it
   was never really about slab clearance, and this specific corner may in
   any case be on the `CUT_HEIGHT_FRONT_MM` side of the slope (unclamped,
   still 900mm) -- not yet confirmed which side, moot given the real cause
   is the rug, not the cut height's absolute value as such. A *fix* is not
   yet chosen or implemented; see the plan status note below.

## Status note (2026-09-15)

This plan's originally-proposed fix (the `CUT_HEIGHT_BACK_MM` clamp) is
implemented and harmless, but does **not** resolve the reported defect --
see failed-hypothesis #1 above. The actual cause is failed-hypothesis #2
(rugs visible over a shortened cut-wall stub at the realistic camera's
shallow, distant viewing angle). Fixing that properly needs a follow-up
decision (raise the cut further vs. keep floor decor clear of exterior
walls under `camera_style: realistic` vs. something else) -- not
implemented yet, reported back to Rainer for direction rather than
guessing a third time per the governance 3-hypothesis stop rule.

## Rollback

Revert the one clamp line in `scripts/render-furnished-dollhouse.py`.

## Unresolved questions

None.

## Approval record

Approved by Rainer, 2026-09-15 ("both").
