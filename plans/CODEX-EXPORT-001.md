# CODEX-EXPORT-001: cleaner Blender export for Codex image jobs

Status: PROPOSED (waiting for Rainer's OK)
Base: request from Codex via Rainer, 2026-10-24 (points 1–6; priority 1, 2, 5).
Test house: twostorey_053. Cross-check: twostorey_058.
Investigation: read-only, measured in the blends. Scripts are in the session scratchpad (`facade_probe.py`, `dump_furniture.py`, `probe.py`, `compare.py`).

## Not changed by this plan
- architecture (rooms, walls, windows, doors)
- furniture positions or rotations in the furniture files
- stored cameras
- uploads, rights, approvals

Finished houses stay "fertig" (FERTIG-IST-FERTIG). Only 053 and 058 are rebuilt, for verification.

---

## 1. Seamless facades (priority)

All five causes are in the geometry, so they already show in every raw render.

| # | Cause (measured on 053, the same on 058) | Location | Change |
|---|---|---|---|
| F1 | EG inner walls in the base under the OG stick out 60 mm past the facade as ribs 120×2400 mm. In the plan they end on the outer face, and the base adds +t/2 at each end. | `render-furnished-dollhouse.py:3892-3896` | Build the base through `wall_object`/`_end_extension_mm`, then cut it with the outline (INTERSECT). In the plan builder, clamp inner-wall end points that lie on or behind the outer-wall centreline to that centreline. |
| F2 | A grey 220 mm storey band (`slab-under-wall-*`, floor screed) sits in the facade plane between the base (to 2400) and the OG (from 2620). Coplanar overlap at the corners. | `:3369-3398`, `:3880/3894` | Build the base walls up to the OG underside (2620). Build the band only under inner walls, or pull it back inward by t/2 − 10 mm. If any outer part remains, it gets the wall material. |
| F3 | Inner walls poke 10 mm through the outer face, in EG and OG: the extension runs to the far face **+10 mm**. | `:1771` | At outer walls end at `far − 10` (buried in the wall). |
| F4 | Exterior: corner posts and wall ends stand 10 mm proud (post `max_t + 0.02`, extension +10). | `render-exterior.py:1487`, `:188` | Post `t − 0.02`, extension `−10`. |
| F5 | Exterior: the EG and OG shells overlap coplanar at storey height (z 2730–2760): z-fighting band. | `render-exterior.py:1378`, `:1511` | Where the outline is the same on both storeys, build one box per wall run over all storeys. Different sections get butt joints plus welding (JOIN + remove_doubles), with no overlap. |

Small fix: the foundation sits 20 mm behind the facade, although the comment says "proud" (`:1515`).

**Tests:** a new `fassade.test.py` with a Blender probe on the 053/058 blends:
- no outward face beyond the facade plane (tolerance 1 mm)
- no coplanar overlap in the facade plane
- window and door counts unchanged before and after

## 2. Unambiguous furniture fronts (priority)

**Cause:** `make-codex-job.py:724` does not derive the front from the rotation. It points the arrow "away from the nearest wall" (`weg_von_der_wand`). Map and text agree with each other, but on 053 they disagree with the real direction:
- kuehlschrank-4: it touches the side wall, so the arrow points sideways. It now disagrees with its neighbouring unit.
- kleiderschrank-7, schreibtisch_kind-2, schreibtischstuhl-20

**Second cause, in the renderer:** `derive_front_axis` (`render-furnished-dollhouse.py:2146-2182`) turns the measured front of generated models onto **+Y**, but the convention is −Y. Result: kleiderschrank-4/5 (053) and -2/-5 (058) stand with the doors facing the wall.

**Change:**
- Fix `derive_front_axis` to −Y.
- At build time, stamp each furniture piece with `fp_front_world` = `matrix_world @ (0,−1,0)`.
- make-codex-job takes the front from that.
- Exceptions:
  - corner sofa: notch rule
  - no arrow: dining group, coffee table, stools, carpet, decor
  - tall units: the front of their run
- `weg_von_der_wand` stays only as a cross-check: more than 45° difference makes the pre-check fail (point 6).
- Move arrows on the object map out from under the label bubbles (16 and 20 were hidden).

**Front control render** `FRONTKONTROLLE-<blend>.png`: a background Blender script, no saving, about 2 s, delivered with the job.
- Green plate on the front, red on the back, arrow on top.
- **Yellow** = job arrow differs from the rotation.
- **Magenta** = mesh differs from the rotation (wardrobe doors facing the wall).

**Tests:**
- `front_aus_drehung` against the 053 list of mismatches
- `derive_front_axis` lands on −Y
- control render: no yellow or magenta left on 053/058 after the rebuild

## 3. Consistent kitchen

- **Island worktop** uses `GRANITE_MAT`, the floor texture; the run uses `arbeitsplatte-granit-schwarz`. Both get the same worktop material (`:6348`/`:5469`).
- **Fronts** are already the same base material. They stay as they are.
- **Tall units** are two separate pillars, 600×600×2400, with the right direction. But they stand 166 mm proud of the run, and the fridge cuts 100 mm into the side wall (they skip the wall snap). Snap them flush to the wall and the run front, and take the run's front.
- **Group:** run, island, tall units, sink and hob get `fp_kitchen` and a collection `Kueche-<n>`.

**Test:** both worktops have the same material; tall units are flush with the run (tolerance 5 mm) and don't overlap the wall.

## 4. Clear placeholder names

**Cause:** markers are picked by name stem. `EG-Sicht-*` (the EG underlay in the OG file), `luftraum-*` and decor without a number (`coffee-table-bowl`, `dining-*`, `desk-books`) become "furniture". Garderobe decor becomes three extra Garderobe markers.

**Change:**
- Custom properties on every furniture piece: `fp_asset`, `fp_symbol_id`, `fp_floor`, `fp_part_of`, `fp_front_world`, `fp_role`, dimensions.
- Markers by the Furniture collection plus `fp_part_of`, not by name.
- Decor is named `<parent>-deko-…`.
- `stuff` objects carry their room label as the role.
- The marker list shows type · ID · floor · W×D×H · front.

## 5. Job only after a completed build (priority)

**Finding:**
- 053 today: consistent; everything comes from one certified build.
- **058:** the job is from 16 Oct, the rebuild from 17 Oct. All 6 blend hashes, all raw renders, the annotation hash and the object maps differ. Codex delivered against that old job.

**Causes:**
- `make-codex-job.py:1583-1597` only checks that the manifest exists and that the furniture fingerprint matches. Not checked: toolchain, annotation, the artifact list, the hashes against the manifest.
- A skip exits 0, and the UI shows success.
- `trim_to_delivery` leaves old `codex-job.json`, `CODEX-AUFTRAG.md` and `OBJEKTKARTE-*` behind.
- The "Auftrag schreiben" button is never disabled.

**Change:**
- (A) Gate in `build_job`: `haus-zustand` must say `zertifikat` and `aktuell`; the blend set must equal `manifest.artifacts`; each sha256 must equal the manifest's; companion PNGs must be from the same build (record the build start in the manifest).
- (B) If it fails: exit 2, and rename old job files to `*.ungueltig`.
- (C) `trim_to_delivery` also moves old job files away.
- (D) Furniture fingerprint at build start; certification refused if it changed during the build.
- (E) `lieferung-pruefen` re-hashes the job inputs against the disk and the manifest.
- (F) Hausakte: the button is only active when the house is certified and current.

## 6. Automatic pre-check before every job

`preflight.json` v2, the job is not issued while `ok: false`. Checks:
- `build_aktuell`: certificate + current; renderer-only as a separate note
- `artifact_set`, `artifact_sha_vs_manifest`, `companion_png_same_build`, `stale_job_files`
- `front_conflict`: rotation front vs wall cross-check vs map arrow
- `frame_clipping`: each storey's bounding box projected into the camera, no corner outside the frame. 058 OG is suspicious: its depth/edge PNGs are only 76 KB.
- `fassade`: the facade probe from point 1

## Order
1. Point 5 + 6 (gate, pre-check). Small, and stops wrong jobs immediately.
2. Point 2 (fronts + control render, `derive_front_axis`).
3. Point 1 (facades F1–F5).
4. Point 3 + 4 (kitchen, names).
5. Rebuild 053 and 058, write jobs, check the pre-check and control render. **No upload.**

Tests first for every step; existing tests stay unchanged.

## Safety question
Can a changed path create, publish or mail geometry without an approved reference? No. Only build and job checks get stricter. Nothing is uploaded, approved or sent.

## Rollback
`*.before-codex-export` per file; old builds are in `superseded-*`.
