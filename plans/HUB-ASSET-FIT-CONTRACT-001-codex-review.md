# Review request: Hub 3D-asset scaling keeps producing wrong real-world dimensions

## Context

`born2thrill-local-workbench/scripts/render-furnished-dollhouse.py` builds an
interior "dollhouse" render of a house. For a door tagged `role ==
"main_entrance"`, `add_door_leaf()` (around line 1493) imports a real CGAxis
Hub asset ("Metal Front Door 3D Model (7976)", a `.blend` file) instead of the
generic procedural door leaf, and must scale it to exactly fit the real
opening's width and height (millimetres, from the floorplan annotation).

The shared `import_model(filepath, divisor, target_mm)` helper (same file,
around line 1952) appends the `.blend`, discards junk reference-cube objects,
joins remaining meshes into one object, applies `bpy.ops.object.transform_apply`
to bake any existing transform into the mesh data, then applies a `divisor`
unit-scale correction (e.g. `1/2.54`) and bakes that too via a second
`transform_apply`. It returns the object with `location=(0,0,0)`,
`rotation=identity`, `scale=(1,1,1)` -- real-world metres are baked into the
vertex data.

`rest_on_floor(obj)` (around line 2139) re-centres the mesh in X/Y and sits its
base at local Z=0, by reading `obj.bound_box` (object-space) and subtracting
the offset directly from `obj.data.vertices`, then calling `obj.data.update()`.

`_object_extent(obj)` (around line 1941) returns `[hi-lo for each axis]` by
iterating `obj.bound_box`, transforming each corner through
`obj.matrix_world`, and taking min/max per axis.

## Attempt 1 (already reverted/replaced) -- wrong catalogue size

The door was scaled against a hardcoded tuple believed to be the model's real
size: `_door_native_mm = (1813, 572, 2180)` (width, depth, height in mm),
copied from the asset's product-page description, NOT measured from the
actual mesh. The code did:

```python
_door_obj = import_model(_door_asset_path, 2.54, _door_native_mm)
_door_obj.name = name
_sx = max(0.75, min(1.35, (width / MM) / _door_native_mm[0]))
_sz = max(0.75, min(1.35, (leaf_height / MM) / _door_native_mm[2]))
_door_obj.scale = (_sx, 1.0, _sz)
_door_obj.rotation_euler = (0, 0, wall_angle)
_door_obj.location = (centre_x, centre_y, 0.0)
```

(`MM = 0.001`, converting mm to metres; `width`/`leaf_height` are the real
opening's width/height in mm.)

A project verifier (`verify_render_blend.py`, check `R8_opening_heights`)
measures the built door leaf's real world Z-span and compares it against the
opening's expected span. It failed on house
`german_catalog_review_bungalow_4_3_1_wb_125`:

```
wall-13-door: door leaf spans -0-1936mm, matches no opening on this wall (expected: 0-2010mm)
```

i.e. the leaf came out 74mm short of the intended 2010mm height. Separately,
all four sibling "Metal Front Door" models (7961/7962/7968/7976, same base
shell, different finish) were earlier confirmed via a headless script to
share an identical RAW (pre-divisor) bounding box of `(2.845, 0.752, 5.334)`
Blender units. Dividing that raw bbox by the divisor (2.54) gives
`(1120, 296, 2100)` mm -- plausible real-world door-with-frame dimensions,
and NOTABLY DIFFERENT from the catalogue tuple `(1813, 572, 2180)` on every
axis, not just height. (2100 * (2010/2180) = 1936.3, which exactly matches
the observed failure -- strong evidence the catalogue tuple's height, and
probably width and depth too, do not match this model's real geometry.)

## Attempt 2 (current code, still wrong) -- measured extent, worse result

Reasoning: don't trust the catalogue number at all, measure the actual
imported object instead. Changed to:

```python
_door_obj = import_model(_door_asset_path, 2.54, _door_native_mm)
_door_obj.name = name
rest_on_floor(_door_obj)
_actual_w, _actual_d, _actual_h = _object_extent(_door_obj)
_sx = max(0.75, min(1.35, (width / MM) / _actual_w)) if _actual_w else 1.0
_sz = max(0.75, min(1.35, (leaf_height / MM) / _actual_h)) if _actual_h else 1.0
_door_obj.scale = (_sx, 1.0, _sz)
_door_obj.rotation_euler = (0, 0, wall_angle)
_door_obj.location = (centre_x, centre_y, 0.0)
```

Rebuilt the same house. Result got WORSE, not better:

```
wall-13-door: door leaf spans 0-2835mm, matches no opening on this wall (expected: 0-2010mm)
```

2835mm is exactly `2100mm * 1.35` -- the scale ratio hit the upper clamp
(1.35), which means the raw computed ratio `(leaf_height_mm/1000) / _actual_h`
was greater than 1.35, i.e. `_actual_h < 2010mm / 1.35 ≈ 1489mm`. But the
model's real height is ~2100mm (established above from the raw-bbox
measurement, and consistent with attempt 1's failure numbers). So
`_object_extent()` measured something far smaller than the object's real,
visible height -- the measurement itself is wrong, not just imprecise.

Candidate causes I have NOT verified (please assess, and add any I've
missed):

1. **Stale `bound_box` cache.** `rest_on_floor()` mutates `obj.data.vertices`
   directly (not via bmesh or an operator) and calls only `obj.data.update()`
   -- does `obj.bound_box` (an object-level cached property) actually get
   invalidated by that, or does reading it immediately after return a stale
   box computed before the mutation? (Note: since the mutation is a pure
   translation, this alone shouldn't change the *size*, only the position --
   so if this were the whole story the extent should still read ~2100mm, not
   ~1489mm. Possibly combined with something else.)
2. **Axis mismatch.** The raw-bbox tuple `(2.845, 0.752, 5.334)` was measured
   by an earlier, separate, unrelated debug script -- never confirmed to be
   in the same (X, Y, Z) axis order as `_object_extent()`'s output, or to
   correspond to (width, depth, height) as assumed. If this asset's local
   "up" is not Z pre-placement, `_actual_h` (`_object_extent()`'s index 2)
   would read the wrong axis entirely.
3. **Leftover disjoint geometry.** `import_model()`'s junk-cube filter only
   discards a `Cube`-named object with `Material`/empty materials; if this
   particular asset's join left some other small disjoint mesh island (e.g.
   a handle, a threshold strip, a stray reference object with different
   material naming) INSIDE the final joined object at a tiny scale/position,
   it could shrink or skew the reported bound_box in a non-obvious way -- but
   this would need to shrink the box, and a leftover *piece* would normally
   only ever enlarge a bound_box, not shrink it, unless the geometry that
   makes up the visible height is somehow excluded from `.bound_box` (e.g.
   lives on a child object, not the joined mesh itself).
4. Something else entirely -- please look at the actual functions rather
   than assume my numbered guesses above are exhaustive or correct.

## What I actually want from this review

1. **Diagnose attempt 2's real root cause** -- why did `_object_extent()`
   return a height inconsistent with the model's real, previously-established
   size? Cite the specific function/line responsible.
2. **A robust, general design** (not just a one-line patch for this one
   asset) for scaling an imported Hub `.blend`/`.fbx`/`.glb` asset to an exact
   target real-world size, that will not silently produce a wrong result
   again the next time a catalogue figure turns out to be wrong or a model's
   geometry has some quirk. Specifically weigh:
   - Should `import_model()` itself be the single place that measures and
     returns authoritative real-world dimensions (so every call site gets
     the same, once-verified number, instead of each call site re-deriving
     it ad hoc)?
   - Should there be a loud, fail-fast check (assertion/log warning) when a
     caller's assumed/catalogue size disagrees with the measured size beyond
     some tolerance, so a wrong catalogue figure is caught at build time
     instead of only by a downstream geometry verifier?
   - `born2thrill-local-workbench/scripts/render-exterior.py`'s
     `place_asset()` / `get_asset_template()` (around lines 897-955) use the
     IDENTICAL pattern as attempt 1 -- scaling against a hardcoded
     `asset["size_mm"]` dict entry, including the very same
     `FRONT_DOOR_ASSET` tuple `(1813, 572, 2180)` for this same model. Does
     that code path share this exact latent bug? It has not been caught
     there only because no verifier currently checks exterior asset
     placement dimensions the way `R8_opening_heights` checks interior
     openings -- that is not evidence it is correct.
3. Rank findings by confidence; say plainly where you are guessing versus
   where you have directly read code that proves the mechanism.

## Out of scope

- Style/formatting nits.
- The rest of `add_door_leaf()` (hinge/swing pose logic for non-main-entrance
  doors) -- unchanged, not implicated.
- Don't just restate my two failing attempts back to me -- I need the actual
  mechanism and a design that prevents a THIRD wrong guess.

## Output format

For each finding: `confidence (high/medium/low) | file:line | root cause or
recommendation | evidence`. Then a short separate "systemic recommendation"
section (a few sentences, not a rewrite) for the general design question in
point 2 above.

---

## Codex output

**Attempt 2 has a proven unit mismatch. The 2835 mm result does not establish that `_object_extent()` measured the wrong height.**

1. **high | [render-furnished-dollhouse.py:1525](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-furnished-dollhouse.py:1525) | Root cause: millimetres divided by metres | Evidence:** `leaf_height` is already in metres: `opening_transform()` converts it at line 1154, and line 1932 passes that value into `add_door_leaf()`. Likewise, `width` is converted to metres at line 1331. `_object_extent()` returns scene-space metres, without converting to millimetres.

   Consequently, even with a **perfectly correct measurement of 2.1 m**, the current calculation is:

   ```text
   (2.010 / 0.001) / 2.100 = 957.142857
   clamp → 1.35
   2100 mm × 1.35 = 2835 mm
   ```

   I executed the actual line-1525 expression extracted from the source AST with those inputs; it produced exactly that result. The dimensionally correct ratios are `width / _actual_w` and `leaf_height / _actual_h`. Your inference that `_actual_h < 1.489 m` assumes a metre numerator; the actual numerator is **2010**, not **2.010**.

2. **high | [render-furnished-dollhouse.py:1524](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-furnished-dollhouse.py:1524) | Recommendation: exact fitting must reject unacceptable ratios, not silently clamp them | Evidence:** Both axes clamp to `[0.75, 1.35]`; zero measurements silently select scale `1.0`. Either behavior can violate an exact-size contract even after correcting the units. Validate finite, positive measurements; calculate the exact ratio; if a deformation limit prohibits it, raise an explicit error containing asset, target, measured dimensions, and requested ratio. Independently verify the resulting dimensions and base elevation.

3. **high | [render-exterior.py:949](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py:949) | Root cause: exterior retains attempt 1’s catalogue-denominator bug | Evidence:** Lines 949–951 use `asset["size_mm"]` directly, and line 773 supplies `(1813, 572, 2180)` for asset 7976. Its importer applies the divisor but never fits to that tuple. Given your measured 2100 mm native height, a 2010 mm target therefore produces approximately **1936 mm** here too. Width has the same defect, compounded by the lower clamp when the catalogue width makes the requested ratio too small. This mechanism is code-proven; I did not rebuild an exterior scene.

4. **high | [render-furnished-dollhouse.py:2035](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-furnished-dollhouse.py:2035) | Recommendation: separate geometry selection from catalogue-size validation | Evidence:** `target_mm` currently determines which meshes survive the shell filter, before joining. Thus an unreliable catalogue entry can affect **what gets measured**, not merely the later scale denominator. The name/material junk filter also deletes geometry heuristically. Use explicit asset component selection or reviewed exclusions, record retained/discarded objects, and reject ambiguous imports. Measuring a mistakenly incomplete assembly precisely would still give the wrong answer. This is a general risk demonstrated by the code, **not an established cause of this door failure**.

5. **medium | [render-furnished-dollhouse.py:1956](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-furnished-dollhouse.py:1956) | Recommendation: define an evaluated-geometry and axis contract | Evidence:** This helper transforms bounding-box corners; it does not explicitly evaluate and enumerate the complete rendered assembly. The importer joins mesh objects and removes other imported objects at lines 2055–2065. A general importer therefore needs explicit handling of modifiers, parenting, instances, and non-mesh geometry before claiming authoritative dimensions. Blender documents `bound_box` as object-space bounds; that alone does not establish assembly completeness. [Blender Object API](https://docs.blender.org/api/5.0/bpy.types.Object.html)

   Your candidate explanations remain **unverified**, and none is needed to explain 2835 mm:
   - A stale box across a pure translation preserves its span.
   - `_object_extent()` explicitly returns X/Y/Z; the separate debug script’s axis convention remains unchecked.
   - Adding internal geometry cannot shrink the bounds of an otherwise unchanged mesh; missing geometry is a different possibility.

**Systemic recommendation**

Yes: centralize import normalization and authoritative measurement in one shared importer used by both renderers. Return the normalized template plus explicitly named dimensions such as `extent_m`, canonical width/depth/up axes, and import provenance; measure the complete evaluated geometry after unit conversion and orientation normalization. Catalogue dimensions should be diagnostic expectations, with discrepancies beyond a documented tolerance blocking unreviewed assets—not scaling denominators or silent geometry-selection rules.

A shared fitting function should convert target millimetres once, apply an explicit per-axis policy, then independently verify final evaluated geometry in the opening’s coordinate frame; world-axis width is unsuitable after rotation. Add regressions for this exact 2100→2010 mm case, wrong catalogue dimensions, transforms/parents/modifiers/instances, all three import formats, invalid extents, clamp-limit violations, and exterior placement. Geometry measurements establish numerical size after the chosen unit conversion; they cannot independently prove that the divisor or semantic fitting envelope is correct.

Read-only review; no Blender rebuild or files changed. Baseline: `5be1a4e18956b9fb2e158bee82aa159898356e89`, branch `agent/furnished-render-and-annotation-schema`; existing worktree contains 16 modified tracked files and 501 untracked files. Review diff: none; rollback: none needed.

Tracking blocker: the canonical roadmap is readable, but this session’s filesystem is read-only, so I could not persist these follow-ups. Next task-specific pending item is an approved shared import/fit contract and regression plan covering both renderers.