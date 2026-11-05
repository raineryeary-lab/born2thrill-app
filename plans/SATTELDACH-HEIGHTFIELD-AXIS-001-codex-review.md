# Review request: multi-wing Satteldach gable end is open (hole into the attic), plus torn roof-sheet facets

## Context

`born2thrill-local-workbench/scripts/render-exterior.py` builds an L-shaped
(two-wing) roof for `satteldach`/`pultdach`/`doppelpultdach` via a shared
height-field code path (`roof_profile.heightfield_roof_mesh()`), gated at
`render-exterior.py:1320` on `roof_wings.recognize_two_wings(roof_poly)`
finding exactly two overlapping axis-aligned wing rectangles from the real
footprint.

Earlier this week (2026-09-22 through 2026-09-25) this whole path was
debugged extensively for `doppelpultdach` specifically (a roof form with a
genuine vertical step/discontinuity between its two wings) -- multiple real
bugs found and fixed via direct rendering + a Codex second opinion each time
(wing-overlap height spikes, a wrong-axis height sample, a self-intersecting
fan-triangulated gable cap). `satteldach`/`pultdach` (no step) were assumed
throughout to be UNAFFECTED by the doppelpultdach-specific fixes, based on
this reasoning (see the big comment at `render-exterior.py:1767-1793`):

> Blender's SOLIDIFY modifier's own "Fill Rim" auto-caps the height field's
> open gable boundary for us, but its fill algorithm is not reliable on a
> NON-CONVEX outline -- satteldach/pultdach's gable cross-section is always
> convex, doppelpultdach's step folds it concave, and only THAT one showed a
> jagged tear.

Concretely, at `render-exterior.py:1807-1809`:

```python
for _wi, (wx0, wx1, wy0, wy1) in enumerate(_wall_wings):
    if not roof_profile.has_vertical_step(_wing_profiles[_wi]):
        continue
    ...  # builds an explicit gable_cap_prism() for this wing's gable ends
```

i.e. the explicit cap is built ONLY for wings whose profile has a vertical
step (`roof_profile.has_vertical_step()`, `roof_profile.py:121`) --
satteldach/pultdach wings always skip this loop body entirely and rely
purely on SOLIDIFY's automatic rim-fill.

## The actual bug (confirmed by a real render, not reasoning)

House `german_catalog_review_bungalow_4_3_1_wb_125` (a genuine L-shaped
two-wing footprint, `roof_wings.recognize_two_wings()` returns 2 wings) was
rebuilt today with `EXT_ROOF_TYPE=satteldach` via `go.py` (this repo's own
per-house exterior test harness, which builds every roof form for QA
regardless of the house's actually-configured type). The render
(`renders/go-baseline/exterior-satteldach-baseline.png`) shows:

- One wing's gable end (the smaller/left wing in this house) is correctly
  closed -- a clean triangular gable wall, roof meets it with no gap.
- The OTHER wing's gable end (the bigger/right wing) is a real, visible HOLE
  straight into the underside of the roof -- you can see the dark underside
  of the roof sheet through it, no wall or cap closes it at all.
- Near the ridge, between the two problem areas, there are torn/twisted
  facets -- small diagonal shapes that don't belong to either a clean hip,
  ridge, or gable silhouette.

This reproduces reliably (not a one-off render glitch -- the same `go.py`
run also produced a clean `exterior-doppelpultdach-baseline.png` for the
SAME house/footprint using the code path that DOES build the explicit cap,
and a clean `exterior-walmdach-baseline.png` using a completely separate,
older, real-hip-roof code path not discussed here).

This house is not itself configured as satteldach in production
(`gebaeudemass.json` has `roof_type_modern: flachdach`, `roof_type_classic:
walmdach`) -- but the broken code path (`heightfield_roof_mesh()` +
`has_vertical_step()`-gated caps) is the SAME general code every OTHER
L-shaped house in the catalogue would hit if it IS configured as satteldach
or plain pultdach. This is a general-code bug, not specific to this one
house's data.

## What I need from this review

1. **Why does SOLIDIFY's automatic rim-fill fail here**, when the
   established reasoning (satteldach's cross-section is always convex,
   only doppelpultdach's step is concave) predicts it should work? Read:
   - `roof_profile.heightfield_roof_mesh()` (`roof_profile.py:349-445`) --
     builds the combined grid, drops uncovered faces/vertices. Note the
     diagonal-choice logic at lines 417-431 (splits each quad along
     whichever diagonal better follows a height jump) and the "drop
     loose vertices" step at lines 433-444 (its own comment already
     documents ONE prior Solidify rim-fill failure mode: loose,
     face-less vertices outside every wing's coverage causing Solidify to
     try to rim-fill around every vertex, not just real boundary loops --
     is a residue of that class of problem still possible here, e.g. a
     vertex that touches only ONE triangle, or a boundary edge shared by
     zero or more than one face making the "rim" not a single clean loop?).
   - `roof_profile.combined_height_at()` / `wing_height_at()`
     (`roof_profile.py:226-270`) -- how height is sampled per wing.
   - The wing-clipping logic immediately above the cap loop
     (`render-exterior.py:1700-1723`): this ONLY clips the smaller wing's
     height-sampling domain (`_height_wings`) when
     `has_vertical_step(_wing_profiles[_smaller])` is true -- so for
     satteldach, BOTH wings keep their full, unclipped rectangles for
     height sampling, meaning the smaller wing's rectangle can extend past
     its own true far end into territory the bigger wing already covers
     (by design -- `combined_height_at()`'s `max()` is supposed to make
     the bigger wing dominate there). Does that overlap change what
     `heightfield_roof_mesh()`'s open-boundary loop actually looks like at
     either wing's TRUE gable end, in a way that breaks the "it's just a
     flat planar polygon, convex or not" assumption the doppelpultdach
     comment relies on?
   - Is the bigger wing's own true far gable end (the one that's actually
     broken in the render) even a genuine single flat rim loop, or could
     the per-quad diagonal-choice logic (lines 424-431) produce a
     boundary that isn't flat/simple there (e.g. because the two wings'
     overlap changes which quads survive right at that edge)?
2. **A concrete, general fix** -- not scoped to this one house. Candidate
   (my own guess, please confirm or correct): remove the
   `has_vertical_step()` gate at `render-exterior.py:1807-1809` so
   `gable_cap_prism()` is built for EVERY wing's gable ends, not just
   stepped ones (the function's own docstring at `roof_profile.py:304-346`
   makes no assumption about step-vs-convex, it just builds the exact
   cross-section prism). If you confirm this is right, also address:
   - Would this now produce a DOUBLE cap (the explicit prism plus
     SOLIDIFY's own rim-fill still also firing on the same now-still-open
     boundary), causing z-fighting/overlap the way the doppelpultdach fix
     had to specifically avoid (see `gable_cap_prism()`'s own docstring,
     the z-fighting paragraph)? If so, what's the right way to suppress
     Solidify's rim-fill only at these ends (there does not appear to be a
     per-edge SOLIDIFY option -- is the fix instead to feed the roof sheet
     itself pre-closed some other way, or is Solidify's rim-fill actually a
     non-issue here because the explicit prism sits OUTSIDE the sheet's own
     boundary, per its docstring's "extending outward instead" fix)?
   - Should the cap be built at EVERY wing's every end, including ends that
     border the internal valley (where the other wing already covers the
     area and there is no real open rim to begin with) -- would that be
     harmless (the prism would just sit flush against a wall that's
     already there / inside solid territory) or does it need the same
     "only if there's a real span left" guard used elsewhere
     (`render-exterior.py:1722`, `min(...) >= 1.5`)?
3. Rank findings by confidence; say plainly where you're inferring from
   reading the code's geometry logic versus where you'd want an actual
   Blender-side measurement to be sure.

## Out of scope

- The separate, older `elif is_rectangle:` single-rectangle path
  (`render-exterior.py:1844+`, `profile_mesh()`/`wall_extension()`) -- not
  implicated, uses different functions entirely.
- `walmdach`'s own roof-building code -- separate, not part of this
  height-field system at all.
- Style/formatting nits.

## Output format

For each finding: `confidence (high/medium/low) | file:line | root cause or
recommendation | evidence`. Then a short "systemic recommendation" section
for point 2 above.

---

## Codex output

**The primary bug is an axis mismatch between the roof sheet and its walls. Removing the cap gate alone would not fix it.** I inspected the reported PNG, measured the saved Blender scene, and ran both roof test suites.

1. **high | [render-exterior.py:1764](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1764) | The height-field call omits the axis used to construct the profiles and walls. | Evidence:** Profile scaling at line 1643 and wall construction at lines 1827–1830 use `_u_along_x`. `heightfield_roof_mesh()` receives no `along_x`, so sampling independently auto-detects each wing’s axis.

   WB_125’s saved plan specifies `"roof_axis_override": "y"`. Its larger wing auto-detects **X**, while the smaller wing auto-detects **Y**. Consequently, the smaller wing’s sheet and walls agree; the larger wing’s do not—matching the asymmetric failure in the render.

   A numerical reconstruction using rounded bounds measured from the saved scene gives **2.25 m above the eave** at the larger wing’s sheet-gable peak, where the Y-oriented wall profile expects **0 m**. This is a missing architectural closure caused by incompatible geometry.

2. **high | [render-exterior.py:1771](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1771) | The comment’s explanation of Solidify is incorrect. | Evidence:** Fill Rim connects the original sheet’s boundary to its offset boundary, closing the **sheet thickness**. It does not fill the entire triangular attic opening down to the wall top. Convex versus concave gable cross-sections therefore does not establish whether the attic is closed. See the [Blender Solidify manual](https://docs.blender.org/manual/en/2.93/modeling/modifiers/generate/solidify.html).

   In the actual saved `.blend`, `roof-pitch` has **3,220 vertices, 6,266 polygons, 9,484 edges—all with exactly two incident faces—and zero loose vertices**. Its shell is closed by edge incidence. That does not prove freedom from self-intersections, but it directly contradicts an explanation based on an unfilled shell boundary.

   The existing `wall_extension()` call already creates explicit gable walls and verge infill for **both** wings, irrespective of the cap gate. They are oriented incorrectly relative to the larger wing’s sheet.

3. **high | [render-exterior.py:1404](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1404) | The clean Doppelpultdach render is not a control for this height-field/cap implementation. | Evidence:** A stepped design now enters the separate hand-built slab branch. The actual Doppelpultdach log confirms “3 von Hand platzierte Koerper … 4 Giebel-Fuellungen.” The height-field branch begins at line 1640.

   Furthermore, scaling preserves profile point positions, so profiles entering this non-stepped branch remain non-stepped. The step-gated clipping and cap bodies are effectively inactive for these resolved profiles. The historical comments describe an earlier implementation.

4. **high | [roof_profile.py:417](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:417) | Diagonal selection cannot create the proposed boundary-edge defect by itself. | Evidence:** Each surviving quad contributes two triangles with the same four perimeter edges, whichever diagonal wins. The internal diagonal has two incident faces; neighbouring cells retain matching perimeter edges. A corner vertex touching only one triangle is legitimate.

   The WB_125 reconstruction has **1,610 vertices, 3,048 triangles, 170 boundary edges**, and every boundary vertex has degree two. No edge has more than two incident faces. The larger wing’s outer X-end lies in a constant-X plane; changing triangle diagonals cannot make that end nonplanar.

   Overlap changes sampled heights, but with unchanged coverage rectangles it does not change which quads survive. Internal notch coordinates can still miss grid lines, so exact perimeter coverage deserves a separate test.

5. **medium | [roof_profile.py:403](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:403) | The visible facets have additional plausible causes; caps cannot repair them. | Evidence:** The uniform grid does not explicitly include ridge positions or equal-height intersection lines. Choosing a diagonal by endpoint height difference does not guarantee that it follows the actual ridge or valley.

   More immediately, the axis mismatch also permits high wall/infill geometry to intersect a differently oriented sheet. This is consistent with the protruding white geometry in the PNG. **I have not identified every visible sliver’s originating face through Blender intersection measurements.** Distinguishing wall penetration, sampling artifacts, and Solidify offset intersections requires that measurement; watertight edge counts alone cannot do so.

6. **high | [render-exterior.py:1808](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1808) | Do not remove the cap gate as the standalone fix. | Evidence:** The proposed caps use the forced wall axis, while the current sheet uses automatic axes. They would still close the wrong ends of the larger wing and leave the underlying mismatch intact.

   Also, `max()` guarantees the higher contribution wins—not that the *larger* wing wins. Smooth individual profiles do not guarantee a smooth combined surface when one contribution disappears at its rectangular domain boundary.

7. **high for geometry; medium for visible overlap | [roof_profile.py:326](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:326) | Outward caps are not universally overlap-free, and internal ends need exposure tests. | Evidence:** Extending outward avoids overlap with the same wing’s first sheet row, but:
   
   - The prism’s back face can still coincide with the sheet’s Solidify rim.
   - “Outward” from one rectangle can remain inside the other wing.
   - A full cap can occupy an internal junction or protrude through neighbouring geometry.

   Solidify does not produce a duplicate full triangular attic cap. Nevertheless, the docstring’s broader “nothing left to fight over” claim is unjustified. The `min(...) >= 1.5` condition measures remaining wing size; it does **not** identify exposed boundary intervals.

**Systemic recommendation**

First, pass `along_x=_u_along_x` into the height-field call, consistently with profile scaling and wall construction. Add a regression covering opposite auto-detected wing axes and explicit X/Y overrides before implementing that change.

Then verify the existing walls and verge infill against the corrected sheet. Keep Solidify’s rim fill for sheet thickness; there is no demonstrated reason to disable it. If closure remains necessary, construct it only over exposed perimeter intervals, using the same resolved roof surface and actual wall planes. Do not blanket-cap every rectangle end or substitute the 1.5 m guard for an exposure calculation.

For the facets, measure sheet–wall intersections and evaluated-shell self-intersections after axis correction. If sampling artifacts remain, split geometry at profile ridges, domain boundaries, and equal-height intersections rather than relying on the diagonal heuristic.

Verification: **92 roof-profile tests and 23 roof-wing tests passed**, demonstrating that the current tests miss this renderer-level mismatch. No files or saved scenes were changed; rollback is unnecessary. Baseline: `5be1a4e18956b9fb2e158bee82aa159898356e89`, branch `agent/furnished-render-and-annotation-schema`; existing status remains 16 modified and 503 untracked files.

Next pending work is the axis-consistency fix and Blender regression verification. The canonical roadmap was readable, but this session’s read-only filesystem prevents recording those follow-ups; that tracking requirement remains outstanding.