# Review request: does wall_extension() mis-position a wing's internal (non-eave) wall using overhang math meant only for true eaves?

## Context

`born2thrill-local-workbench/scripts/render-exterior.py` builds two-wing
(L-shaped) `satteldach`/`pultdach`/`doppelpultdach` roofs. The person I work
for just said, after today's axis-mismatch fix: "we are still having the
problem with closing the holes in the walls, they have to be in the same
footprint as the Floorplan walls not where the Ueberstand [roof overhang]
ist" -- i.e. some wall the renderer builds is landing at an overhang-derived
position instead of the TRUE floorplan wall position. This exact bug class
(position computed from roof/overhang geometry instead of independently from
the real wall footprint) was already found and fixed once this week in a
DIFFERENT code path (the hand-built-box doppelpultdach branch, see
`plans/zweischenkliges-satteldach-v1.md`'s "wing_bound ± overhang" rule). I
suspect, from reading the code (not yet confirmed by a render), that the
SAME class of bug exists independently in the shared `wall_extension()`
path used by satteldach/pultdach/doppelpultdach's two-wing branch. Please
confirm or refute this with the actual code, not my framing.

## The suspected mechanism

1. `render-exterior.py` (around line 1265): `roof_poly =
   offset_orthogonal_polygon(footprint, overhang)` -- the TRUE floorplan
   footprint polygon is offset OUTWARD by `overhang` to get the roof's own
   outline, BEFORE wing recognition ever runs.
2. `roof_wings.recognize_two_wings(roof_poly)` (`roof_wings.py:118-164`)
   decomposes THIS ALREADY-OFFSET polygon into two wing rectangles
   `(x0,x1,y0,y1)` each. For an orthogonal polygon, offsetting outward by a
   fixed distance moves CONVEX corners outward but moves the REFLEX
   (concave, interior) corner of an L INWARD relative to the offset amount
   (a textbook property of a uniform polygon buffer/offset: reflex corners
   retract, they don't extend, under a positive/outward offset). So the
   wing rectangles' shared/internal boundary (at the reflex corner) is
   NOT simply "true wall position + overhang" the way a true eave side is
   -- it's wherever the offset polygon's own reflex-corner geometry landed,
   which is a different, offset-direction-dependent amount.
3. Each wing is then passed as `(wx0,wx1,wy0,wy1)` directly into
   `wall_extension(x0, x1, y0, y1, z_eave, overhang, profile, thickness,
   ...)` (`roof_profile.py:601-691`). That function's own docstring states
   plainly: "(x0..y1) is the ROOF outline; the walls stand `overhang`
   INSIDE it" -- and its body subtracts `overhang` from EVERY side
   uniformly to find the true wall position (`c_lo = overhang`, `c_hi =
   span - overhang` at line 642; `a0 + overhang` / `a1 - overhang` at line
   656). This is correct ONLY if all four sides of the rectangle it's
   given are true eaves that each independently received a uniform
   `overhang` outward offset -- true for the single-rectangle path (the
   whole building's own `roof_poly`, every side a real eave), but NOT
   obviously true for a WING's rectangle in the two-wing path, where one
   (or two) sides are the internal division against the OTHER wing, not a
   real eave, and per point 2 did not receive the same "+overhang" the true
   eave sides did.
4. If this is right, whichever wall `wall_extension()` builds using that
   internal-division coordinate (the long "versatz"/high-side wall at
   `c_lo`/`c_hi`, `roof_profile.py:682-690`, and/or the verge soffit at
   `roof_profile.py:675-680`, and/or the end-wall at that side if
   `real_ends` marks it real) would land `overhang` away from where the
   internal-division coordinate ACTUALLY corresponds to the true floorplan
   wall -- possibly in the wrong direction or by the wrong amount, since
   the reflex-corner offset isn't simply "true position + overhang" the
   way a real eave is.

## What I need from this review

1. **Confirm or refute** the mechanism above with the actual code -- is a
   wing's internal (non-eave) side actually mispositioned by
   `wall_extension()`'s blanket "subtract overhang from every side"
   assumption? If you can, work out (symbolically, from the actual offset
   math in `offset_orthogonal_polygon()` -- find and read its real
   implementation, don't assume mine is right) what coordinate the wing's
   internal boundary actually lands at relative to the TRUE floorplan
   reflex corner, and compare that to what `wall_extension()` assumes it
   is (`true_position + overhang` uniformly).
2. Note: `render-exterior.py`'s OWN two-wing branch already independently
   computes the TRUE footprint position elsewhere for a DIFFERENT purpose
   -- search for how `_true_west`/`_true_east`/`wing_bound ± overhang`-style
   values were computed in the (now-replaced) doppelpultdach hand-built-box
   code, described in `plans/zweischenkliges-satteldach-v1.md`'s "Nachtrag
   2026-09-25" section, for the established, already-correct pattern this
   codebase uses elsewhere: compute true wall position directly from the
   REAL (non-offset) wing rectangles that `roof_wings` would derive from
   the UN-offset footprint, never from subtracting overhang off an
   already-offset polygon's internal edge.
3. If the bug is real: what's the minimal, correct fix? Candidates to
   weigh (don't just pick the first one -- say which is actually right):
   - Pass `wall_extension()` a DIFFERENT rectangle for wall-building
     purposes than the one used for roof-sheet coverage -- e.g. wings
     recomputed against the TRUE (non-offset) footprint for wall position,
     while `heightfield_roof_mesh()` etc. keep using the offset-derived
     wings for roof coverage/shape (mirroring the `height_wings` vs `wings`
     split the code already does elsewhere for a related reason).
   - Change `wall_extension()` itself to accept a per-side flag for "this
     side is a true eave, subtract overhang" vs "this side is an internal
     division, use the true coordinate directly" (similar to its existing
     `real_ends` parameter).
   - Something else you find more direct once you've traced the actual
     offset math.
4. Is the SAME issue present in the verge soffit and/or explicit gable-cap
   code (`gable_cap_prism`, `render-exterior.py`'s cap-building loop) for a
   wing's internal end, or are those unaffected for a different reason (e.g.
   they're gated to only run on true/real ends already)?

## Out of scope

- The axis-forwarding bug fixed earlier today (`heightfield_roof_mesh()`
  missing `along_x`) -- already fixed and verified, not related to this
  question.
- The door-asset-scaling plan (`HUB-ASSET-FIT-CONTRACT-001`) -- unrelated.
- Do not propose UI changes -- this is renderer geometry only.

## Output format

`confidence (high/medium/low) | file:line | finding | evidence`. Then a
short "recommended fix" section for point 3, stating which candidate (or
another) is actually correct and why, referencing the real offset math you
found -- not a guess.

---

## Codex output

**The proposed mechanism is refuted for the original wing rectangles. A related error exists in the clipped-wing logic, but that logic is currently bypassed for vertical-step profiles.**

high | [render-exterior.py:449](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:449) | **The reflex corner’s offset is exactly reversible here.** | The implementation computes `p′ = p + overhang × (previous outward normal + next outward normal)`. For an L with its northeast corner missing, the reflex point `(rx, ry)` becomes `(rx+h, ry+h)`. Its two incident boundary lines move outward into the notch. “Reflex corners retract” does not imply a different offset distance for these axis-aligned boundary coordinates.

high | [roof_wings.py:159](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:159) | **Recognition produces overlapping rectangles, not a partition with a newly introduced internal edge.** | For that northeast-notch L, the true wings are:
- `A = (xmin, xmax, ymin, ry)`
- `B = (xmin, rx, ymin, ymax)`

After offsetting, they become:
- `A′ = (xmin−h, xmax+h, ymin−h, ry+h)`
- `B′ = (xmin−h, rx+h, ymin−h, ymax+h)`

Adding `h` to each minimum and subtracting `h` from each maximum recovers **both original rectangles exactly**, including the reflex-side coordinates. Portions of those sides lie inside the other wing, but that does not change their coordinates.

high | [roof_profile.py:642](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:642) | **The ordinary wall inset does not misposition those original wing sides.** | `c_lo/c_hi`, the end-wall positions at line 656, and the longitudinal extents at line 689 apply precisely the inverse above. I executed the actual offset function, extracted through Python AST, followed by the actual recognizer: the identity passed for all four L orientations and overhangs `0`, `0.2`, `0.5`, and `1.0 m`.

high | [render-exterior.py:1485](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1485) | **The cited hand-built branch uses the same offset-wing inset; it does not recompute wings from the un-offset footprint.** | `_true_west`, `_true_east`, `_true_reflex_x`, and the Y bounds all come from `wings ± overhang`. `wings` was recognized from `roof_poly` at line 1320. The [September 25 note](C:/dev/Floorplan-tools/born2thrill-local-workbench/plans/zweischenkliges-satteldach-v1.md:17) explicitly describes this. That branch remains present in the current code.

high | [roof_wings.py:249](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_wings.py:249) | **Clipping creates a genuinely different coordinate contract—and a latent double-offset error.** | In the example above, clipping B against A sets B’s **minimum Y** to the offset reflex coordinate `ry+h`. Passing this to `wall_extension()` adds another `h`, placing the wall at `ry+2h`, rather than `ry`. My numeric probe with `ry=4`, `h=0.5` produced a wall coordinate of `5.0`. Simply marking this side “internal, apply no inset” would still leave it at `4.5`, also wrong.

high | [render-exterior.py:1404](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1404) | **That clipped-wing error does not explain the current ordinary shared-path render.** | A design profile with a vertical step enters the hand-built branch. The shared profile branch starts at `else` on line 1640. Its clipping condition requires a vertical-step wing profile at line 1704; scaling preserves the resolved profile’s `u` positions. Consequently, the current ordinary flow leaves `_height_wings` and `_wall_wings` unclipped. The historical comments describe behavior that the enclosing branch routing now bypasses.

high | [render-exterior.py:1849](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1849) | **Internal end portions are not filtered out by `real_ends` in this caller.** | The argument is omitted, so both ends default to `True`. Thus full end walls and soffits can be generated across portions covered by the other wing. This is an extent/visibility question, separate from the refuted coordinate error.

high | [roof_profile.py:675](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:675) | **Verge soffits deliberately occupy the overhang region.** | Each soffit spans from the roof end to the inset wall and uses the full cross-section down to `z_eave`; it is not merely a thin underside strip. These facade-material closure solids therefore need inspection when the complaint is “the closure is at the overhang.” On original wings their placement follows the intended soffit contract, but they are not confined to the wall footprint.

high | [roof_profile.py:342](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py:342) | **Gable caps do not perform the wall-inset calculation.** | They sit at the supplied rectangle’s end and extend outward by their thickness. The [cap loop](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:1827) selects both ends, without a real-end gate, but requires vertical-step profiles—so it is likewise inactive under the current shared-branch routing. If reactivated with clipped rectangles, its boundary semantics need correction; it is not protected by true-end detection.

**Recommended fix**

Do **not** change the ordinary inset based on this hypothesis: it correctly recovers the original wing rectangles.

For the latent clipping defect, the correct candidate is **separate explicit wall coordinates and roof/profile coordinates**. Derive wall bounds and the division line from the un-offset footprint; retain roof bounds for coverage and height evaluation. Merely passing a smaller rectangle to the existing function would either inset it again or alter its profile span/origin. A boolean “eave versus internal” flag alone is insufficient because the supplied internal coordinate is already offset.

For the reported visible closure, first identify whether the offending mesh is a wall or the full-height verge soffit. If it is an internal/partially exposed closure, compute the exposed boundary segments and build only those segments; a whole-end boolean cannot describe a partially exposed end.

Verification: **92 roof-profile tests and 23 wing tests passed**, plus the 16 coordinate probes. No Blender render was performed. No files changed; rollback is unnecessary. Final worktree status: 16 modified tracked files and 506 untracked files, including the reviewed renderer modules.

Tracking blocker: the canonical roadmap is readable, but this session’s filesystem is read-only, so I could not record these follow-ups. The next review-specific item is identifying the offending closure mesh; the existing roadmap also retains the axis regression test as pending.