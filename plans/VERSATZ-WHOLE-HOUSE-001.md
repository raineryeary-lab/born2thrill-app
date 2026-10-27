# Versetztes Pultdach on non-rectangular houses: ONE roof, one Versatz line

Status: IMPLEMENTED AND VERIFIED on 3_5_1_b_145 (Blender probe + front/back/top/close-up views)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-04, on 3_5_1_b_145 ("it creates 4 roofs", "you are not being logical", pointing at
the Dach-tab reference map: "the small image to the right show where the versatz should be"):
a Versetztes Pultdach on an L-shaped house is ONE roof over the whole house. It has ONE Versatz line,
the one the reference map draws, so it has 2 roof surfaces (A side and B side). It is not one
Versetztes Pultdach per wing (4 surfaces).

## Current evidence and behavior

- The reference map (`dach-referenz.js`, `dach-editor.js`) already draws the intended result: the
  Versatz is one line across the whole outline at u * span of the house's bounding box, using the
  house's axis (`roof_axis_override`; "x" on this house, so the Versatz is horizontal, A below and B above).
- `render-exterior.py` sends every non-rectangular doppelpultdach through the per-wing chevron
  construction. Each wing gets its own scaled profile, so there are 2 Versatz lines and 4 surfaces.
  The render log of 09:50 shows "doppelpultdach chevron ... 2 Fluegel".
- The rectangle branch (`elif is_rectangle:` ~2271) already builds exactly the wanted roof for a
  rectangle: `profile_mesh()` over the roof outline plus a solidify of 0.22.

## Exact scope

In `render-exterior.py`, for roof_type `doppelpultdach` on a non-rectangular footprint, **unless
this form has its own drawn Firstlinien** (then per-wing stays as the explicit choice):
1. Roof sheet: build exactly as the rectangle branch does, over the bounding box of `roof_poly`
   (overhang included), with the same axis rule (`roof_axis_override`) and the same
   `resolve_profile()` span, so the Versatz lands where the reference map shows it. Then cut it to
   the L with a boolean INTERSECT against `roof_poly` extruded vertically.
2. Walls up to the roof (gables, the Versatz step wall, and the walls in the L's inner corner):
   one solid made from the same cross-section (top 0.10 m below the roof surface, so it stays
   inside the 0.22 m sheet). It is extruded over the bounding box and intersected with the true
   footprint (5 mm inset, so its faces never coincide with the walls below). Facade material.
3. Log line: `[exterior] doppelpultdach: ein Dach ueber das ganze Haus, Versatz bei ... m`.
4. The chevron, Walmdach fallback and generic roof blocks are skipped once this was built
   (`_versatz_built`), the same exclusion pattern as `_chevron_built`.

## Files in scope

- `born2thrill-local-workbench/scripts/render-exterior.py`

## Explicitly out of scope

- Satteldach/Pultdach (they stay per-wing / Firstlinien).
- Rectangular houses (unchanged).
- Annotator UI. The reference map already shows the target.

## Acceptance criteria

1. 3_5_1_b_145 Doppelpultdach rebuild: the roof object has exactly 2 sloped surfaces plus the step
   face. The Versatz line is at the y the reference map shows (u=0.4819 of the bbox span). Every roof
   vertex lies inside `roof_poly`. A Blender probe and views from front, back and top are checked in
   full.
2. No wall pokes through the roof, and there is no gap between walls and roof at the gables, the
   Versatz or the inner corner (probe and image check).
3. Satteldach on 3_5_1_b_145 is byte-identical to the 09:50 rebuild in roof vertex terms (not affected).
4. Existing roof tests stay green.

## Tests and verification commands

Blender build + probe (geometry runs only in Blender). `roof_profile.test.py`, `roof_wings.test.py`,
`roof_wings_multi.test.py` stay green.

## Rights, provenance, privacy, and security impact / external effects

None. Local render only, no upload.

## Floorplan-suite invariant

No. This only changes the local roof mesh of an already annotated footprint. Nothing is published
or emailed.

## Rollback

`render-exterior.py.before-versatz-whole-house` copy.

## Approval record

Approved by Rainer in chat, 2026-10-04 ("yes").
