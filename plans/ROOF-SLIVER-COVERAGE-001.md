# No roofless strips: footprint slivers under 1 m join a neighbouring wing

Status: IMPLEMENTED -- 040_66 middle strip roofed; 26 cm corner residue (see roadmap)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-04, on bungalow_040_66 ("that can't be right"): every part of the footprint has a
roof over it. A narrow strip of the footprint must never be left out of the per-wing (chevron) roof.

## Current evidence and behavior

bungalow_040_66 is rebuilt with the current renderer (scratchpad, not over the go-baseline files). Its
footprint (metres, traced from walls, no drawn outer outline) is:
`(18.9,6.07) (15.87,6.07) (15.87,10.26) (18.9,10.26) (18.9,15.52) (11.78,15.52) (11.78,11.02) (8.53,11.02) (8.53,13.64) (4.71,13.64) (4.71,0.47) (18.9,0.47)`

`decompose_rectangles()` returns 5 rectangles. One of them is
`(4.71..18.90) x (10.26..11.02)`, a 0.76 m strip that exists only because the right courtyard ends
at y=10.26 and the back notch starts at y=11.02. `render-exterior.py:1152` drops every rectangle
under 1.0 m as "noise" whenever at least 2 others remain, so the strip gets **no roof**. The top-down
probe render shows white gaps between the main body and the two back wings. The 1.0 m floor exists
for float-jitter slivers (comment at ~1155, bungalow_001), not for real 0.3-1.0 m wall offsets.

## Exact scope

In `render-exterior.py`'s massing step, used by the chevron roof:
1. A decomposed rectangle with a side under 1.0 m (and both sides over 0.3 m, so not jitter) is not
   dropped. It is merged into the neighbouring rectangle it shares a whole side with, where the merge
   gives a rectangle. Of several such neighbours, the one with the longest shared side wins.
2. If no neighbour fits exactly, the sliver is split at the neighbours' own edges and each part
   joins the neighbour it fits. A part that still fits nowhere stays its own small wing.
3. One log line per sliver: where it went.
4. A pure helper in `roof_wings.py` (testable without Blender) does the merging, and
   `render-exterior.py` calls it.

## Files in scope

- `born2thrill-local-workbench/scripts/roof_wings.py` (new pure helper)
- `born2thrill-local-workbench/scripts/roof_wings.test.py` (new tests only)
- `born2thrill-local-workbench/scripts/render-exterior.py` (massing step only)

## Explicitly out of scope

- How wings are roofed (chevron internals), Firstlinien, Versetztes Pultdach whole-house path.
- The crossed "V" in bungalow_040_66's main body. That one needs Rainer's drawn Firstlinien and
  outer outline (his call), not a renderer guess.
- The outdated renderer copies in `C:\dev\wip-born2thrill-local-workbench-*` (not touched; Codex
  must build from `C:\dev\Floorplan-tools\born2thrill-local-workbench`).

## Acceptance criteria

1. bungalow_040_66 Satteldach: the top-down probe render shows no roofless gap over the
   footprint. In the built .blend, every footprint point has roof above it, checked by a raycast
   grid at 0.25 m.
2. bungalow_001, 3_5_1_b_145 and german_catalog_review_bungalow_4_3_1_wb_125: the massing log lines
   are unchanged (no slivers there).
3. New tests: the 040_66 strip joins a neighbour, jitter (<0.3 m) is still dropped, and a sliver
   with no fitting neighbour stays its own piece. Existing roof tests stay green, none changed.

## Floorplan-suite invariant / external effects

No. This only changes the local roof mesh of an already annotated footprint. Nothing is uploaded,
published or emailed.

## Rollback

`render-exterior.py.before-roof-sliver`, `roof_wings.py.before-roof-sliver`.

## Approval record

Approved by Rainer in chat, 2026-10-04 ("ja und ja").
