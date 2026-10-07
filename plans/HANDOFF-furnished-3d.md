# Handoff — Furnished 3D Dollhouse Render

Last updated: 2026-08-07
Owner: Rainer
Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
Branch: `agent/zuhausefinder-generator`
Governing plan: `plans/furnished-3d-dollhouse-render-v1.md`

---

## 1. Goal

Boss wants fewer floorplans, but each one delivered as a furnished 3D
"dollhouse cutaway" isometric render plus a matching exterior view.

Approach: extend the **existing** Blender pipeline in this repo (not
floorplan-simplifier, which has no 3D capability). Furniture is placed
automatically by room kind, with a per-room "rearrange" command and a manual
override. Two styles (modern / classic) with genuinely different meshes, and
unlimited procedural colour/material variety applied in Blender at render
time — no baked textures.

---

## 2. Where things actually stand

### Done and verified

| Thing | Where | State |
|---|---|---|
| Governance plan | `plans/furnished-3d-dollhouse-render-v1.md` | Written, approved verbally |
| Furniture catalogue | `src/lib/generator/furniture-catalog.mjs` | 27 types x 2 styles = 54 entries, all `status: "placeholder"` |
| Material finishes | same file | 14 procedural finishes + per-type compatibility rules |
| Placement engine | `src/lib/generator/furniture-placement.mjs` | Deterministic, room-kind driven, wall-edge assignment |
| `rearrange_room` API | `src/app/api/floorplan-workbench/corrections/route.ts` | Stateless, writes no revision, never touches `geometry_hash` |
| Tests | `scripts/furniture-catalog.test.mjs`, `scripts/furniture-placement.test.mjs` | Passing; exact geometry values derived by running the code, not by hand |
| Test batch of 3D models | `data/furniture-assets/test-batch/` | **6 real `.glb` files + previews.** Quality is good; modern/classic are genuinely different shapes |

### Not done

- **No full furniture catalogue generated.** 48 of the 54 catalogue entries
  still have no mesh. Blocked on Tripo credits (see §3).
- **No interior Blender rendering.** `export-floorplan-blender.py` still only
  does exterior massing. Needs: room floors, furniture instancing, dollhouse
  cutaway camera, and a scale-normalisation step (see §4).
- **No manual furniture override UI** in the Workbench editor.
- **Nothing has been rendered end-to-end.** Not a single furnished image
  exists yet.
- `bungalow_016` still has 14 validation errors, unrelated to this work but
  blocking its use as a demo plan.

---

## 3. Credits — read this before spending anything

The original cost estimate in this project was **wrong**, and it was wrong
twice in a row. Correct numbers, taken from the real API response:

- Tripo bills **30 credits per piece** at our settings
  (`texture:false, pbr:false, geometry_quality:"detailed", face_limit:30000`).
  The earlier "10 credits/piece" figure was an assumption that was never
  checked against a real invoice.
- Source of truth: `data/furniture-assets/test-batch/test-batch-manifest.json`
  records `"total_credits_consumed": 180` for 6 pieces.

Ledger:

```
Purchased          1000 credits  ($10)
Test batch          -180 credits  (6 pieces, done)
                   -------------
Remaining            820 credits
```

Cost of remaining work:

```
Full batch (48 pieces x 30)   1440 credits  (~$14.40)   -> 620 short
Affordable right now           820 credits  = 27 pieces
```

**Do not run `tripo-generate-furniture-full.mjs` as-is** — it will burn all
820 credits and then start failing partway through with insufficient-credit
errors. It does continue past failures and writes a manifest, so nothing is
lost, but you'd end up with an arbitrary 27 of 48 pieces.

Balance / top-up: https://platform.tripo3d.ai (Billing → Credits). 100 credits = $1.

### Recommended order if buying nothing more

Cheapest useful next step is **not** more generation. It's rendering the 6
pieces we already have (§4) to confirm the whole pipeline works before
committing another $14 to it. If those render badly, the catalogue is the
wrong thing to have bought.

If you do want more pieces now, a sensible 780-credit subset (26 pieces) is
the ones that appear in almost every plan:

```
wardrobe, nightstand, coffee_table, tv_unit, dining_table, desk,
bathroom_vanity, shower, bathtub, sink, rug, mirror, storage_shelving
(13 types x 2 styles = 26 pieces = 780 credits)
```

---

## 4. Known technical issue: scale normalisation

Tripo returns every model normalised to fit a ~1-unit bounding box, regardless
of what the object is. Measured from the test batch:

| Model | Raw bbox (units) | Catalogue says (mm) |
|---|---|---|
| `bed_double__modern` | 0.741 x 0.384 x 0.980 | 1600 x 2000 x 600 |
| `sofa__modern` | 0.383 x 0.323 x 0.980 | 2000 x 900 x 800 |
| `dining_chair__modern` | 0.621 x 0.980 x 0.543 | 450 x 500 x 900 |

Every one has its longest axis at 0.98. This is normal for text-to-3D output
and is **not** a quality problem.

Fix: on import in Blender, rescale each mesh so its bounding box matches the
catalogue's `bounding_box` for that type, and detect the up-axis / forward-axis
per model (note the chair's long axis is Y, the bed's and sofa's is Z — the
orientation is not consistent between pieces, so this cannot be a single
global transform). Written once, applies to all pieces automatically. No
credits involved.

---

## 5. Next actions, in order

1. **Start the Workbench and look at a real placement.**
   ```
   cd C:\dev\Floorplan-tools\born2thrill-local-workbench
   pnpm dev
   ```
   Then POST to `/api/floorplan-workbench/corrections` with
   `{ action: "rearrange_room", document, floor_id, room_id, style }`.
   This is the "does the layout make sense" check, and it costs nothing.
   Note: `rearrange_room` currently recomputes the *same* deterministic
   layout — there is no seed/variation yet, so pressing it twice gives the
   same answer. Adding variation is a small change but has not been made.

2. **Extend `export-floorplan-blender.py`** with room floors, the scale
   normalisation from §4, furniture instancing from a placement plan, and a
   dollhouse cutaway camera. Verify with the 6 existing pieces.
   Blender 5.0 is installed on this machine. It is not available in the
   sandbox, so this step has to be run locally.

3. **Render one room, then one full floor.** Judge quality here, before
   spending more.

4. **Only then** decide on the remaining 48 pieces.

---

## 6. Environment notes

- API key lives in `.env.local` as `TRIPO_API_KEY`. Already gitignored via the
  existing `.env*` rule. Do not commit it, do not paste it into chat.
- Generation scripts must be run **from this machine** — the agent sandbox is
  behind a domain allowlist that blocks `openapi.tripo3d.ai`, so the agent
  cannot run them itself. Always `cd` into the repo first; running from
  `C:\WINDOWS\system32` gives `.env.local: not found`.
- Run commands:
  ```
  node --env-file=.env.local scripts/tripo-generate-furniture-test.mjs   (done)
  node --env-file=.env.local scripts/tripo-generate-furniture-full.mjs   (see §3 first)
  ```
- Tests: `node --test --test-isolation=none scripts/furniture-*.test.mjs`
- `pnpm install` is extremely slow against `C:\dev` from the Linux sandbox;
  copy the tree to a native path first if working there.

---

## 7. Invariants that must not be broken

- Furniture and any other presentation data must **never** affect
  `geometry_hash`. The existing revision/approval gate stays exactly as it is.
- Rights decisions, `usage_scope`, and "Approve locally" are **Rainer's alone**.
  No agent approves or commercially clears a plan, ever.
- All furniture work so far is purely additive — nothing existing was modified,
  so rollback is deletion of the new files.

---

## 8. Uncommitted work

These files are new and **not yet committed** on `agent/zuhausefinder-generator`:

```
src/lib/generator/furniture-catalog.mjs
src/lib/generator/furniture-placement.mjs
scripts/furniture-catalog.test.mjs
scripts/furniture-placement.test.mjs
scripts/tripo-generate-furniture-test.mjs
scripts/tripo-generate-furniture-full.mjs
data/furniture-assets/            (the 6 .glb models + previews)
```

Plus the `rearrange_room` addition inside `corrections/route.ts`.

Consider whether the `.glb` binaries belong in this repo or in
`born2thrill-local-workbench-data` — 6 models is fine, 54 may not be.

A daily backup task runs at 23:00 and pushes a `wip-backup/*` branch, so this
work is not at risk of being lost, but it is not on a real branch yet either.
