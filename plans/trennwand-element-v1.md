# Trennwand (hand-drawn interior wall) element, and window width 178 cm

Status: APPROVED / IMPLEMENTED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-09-20: "we need a new window width 178 cm" and "can we also add a new element? a
trennwand?". Answers to the design questions: full-height wall; two clicks, 12 cm with a
right-click list of other thicknesses; doors and windows can sit in it like in any wall.

## Exact scope / files

- Window 178 cm: `annotate.html` (Fensterbreite dropdown), `oeffnungsbreiten.js` (FENSTERBREITEN).
  178 cm gets 2 panes through the existing width rule.
- Trennwand: new element type `partition` (two points, optional `thickness_mm`, default 120).
  Annotator: `annotate.html` (tool button), `annotate.js` (draw, delete, default thickness),
  `element-edit.js` (select/drag, right-click thickness 10/12/17.5/24 cm), `geometry-tools.js`
  (wall overlay sends partitions), `app.py` (`thickness_mm` kept on save, `/api/walls` passes
  partitions), `walls.py` (overlay walls). Builder: `build-simplifier-render-plan.py`
  (`partition_walls()`, `build_walls(extra_walls=)`): each partition becomes an ordinary
  interior wall that runs through the shared wall cleanup, so doors/windows match it.
- Out of scope: half-height dividers, glass partitions, partitions across floors.

## Tests and verification

New: `tests/test_trennwand.py` (6), `scripts/trennwand.test.py` (6). Suites: simplifier 288,
workbench scripts green (roof, register, approve-plan, trennwand, go, hausdaten). Live in the
annotator on twostorey_050 (not saved): tool draws a 12 cm element, overlay shows the wall,
right-click sets 24 cm and the stroke follows. With the real twostorey_050 rooms in memory: one
extra interior wall, openings and unmatched unchanged.

## Suite invariant

A Trennwand is drawn geometry in the annotation, like any wall. It does not generate, publish or
send anything and changes no rights or approval state.

## Rollback

Remove the `partition` elements from a project's annotations.json; revert the files above. A
project without partitions builds exactly as before.
