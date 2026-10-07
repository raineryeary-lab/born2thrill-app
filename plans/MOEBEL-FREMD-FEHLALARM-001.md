# "Möbel auf fremder Geometrie" ist ein Fehlalarm

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-07: the Hausakte often shows "Möbel auf fremder Geometrie … im Möbel-Schritt prüfen
und einmal speichern". Saving there never makes it go away. The warning should appear only when it
is true, and then say something that actually helps.

## Current evidence and behavior

- `src/app/api/floorplan-workbench/staleness/route.ts:116`: `geometrieFremd = !revision && jetzt`.
  It is true whenever `corrections/<plan>/revisions/` holds no file. Only the correction editor
  writes revisions. The Möbel step (`save_furniture`) never does, so the advice in the text cannot
  clear it.
- The reason behind it (bungalow_039, 2026-08-20) no longer holds. Back then the furniture editor
  showed the correction candidate's geometry, not the build geometry. Today the Möbel step
  (`mode=furniture-embed`, `page.tsx:1026`) loads `render_geometry`, which is exactly what the build
  uses. Every save stamps `coordinate_space: render-geometry-mm-y-down-v1` and that floor's
  `geometry_identity` (`corrections/route.ts` ~600). A save is refused (409) if the rooms changed
  while the editor was open.
- 11 houses show the warning today (bungalow_001, 040_66, 3_2_4, 4_1_2, twostorey_047/049/050/052-055).
  All of their furniture files are already in `render-geometry-mm-y-down-v1`, so it is a false alarm
  on every one.

## Exact scope

In `staleness/route.ts`:
1. `geometrieFremd` is only true when a furniture file of the plan is NOT in
   `render-geometry-mm-y-down-v1` (old furniture placed on the other geometry). Only then is the
   old warning true.
2. The real check for render-geometry files: compare the file's `geometry_identity` with today's
   `render_geometry` identity of that floor. If they differ, the rooms were redrawn after the
   furniture was set. That is reported through the existing "Möbel veraltet" warning
   (`veraltet`), with a reason naming the floor.
3. Text of the remaining "fremd" warning: say what actually clears it (open the Möbel step, check,
   save — which now rewrites the file in render-geometry space).

## Files in scope

- `src/app/api/floorplan-workbench/staleness/route.ts`
- `src/app/haus/page.tsx` (warning text only)

## Explicitly out of scope

Furniture placement, saving, the build. Nothing changes in any furniture file.

## Acceptance criteria

1. Hausakte of the 11 houses: no "fremde Geometrie" warning. Checked via the staleness API for all
   11 and in the browser for one.
2. A test copy of a furniture file with a changed `geometry_identity` (scratch only, never the real
   file) shows "Möbel veraltet" for that floor.
3. A test copy with an old `coordinate_space` still shows "fremde Geometrie".

## Floorplan-suite invariant / external effects

No. This only changes a warning display. No geometry, nothing published.

## Rollback

`.before-moebel-fremd` copies of both files.

## Approval record

Not approved. Stop before implementation.
