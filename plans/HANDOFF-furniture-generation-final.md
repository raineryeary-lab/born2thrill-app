# Handoff — Furniture Generation Completion

**Last updated:** 2026-08-07  
**Owner:** Rainer  
**Repo:** `C:\dev\Floorplan-tools\born2thrill-local-workbench`  
**Branch:** `agent/zuhausefinder-generator`  
**Governing plan:** `plans/furnished-3d-dollhouse-render-v1.md`

---

## Current Status

### Credits — Updated

```
Original purchase          1000 credits
Test batch (6 pieces)       -180 credits  (2026-08-06 05:13)
First full run (27 pieces)  -810 credits  (2026-08-06 21:28)
Additional purchase        +1000 credits  (2026-08-07)
                          ------
Balance                      10 credits
```

### What's Generated

**Successfully created (27 pieces, 54 items with both styles):**
- nightstand, wardrobe, coffee_table, tv_unit, dining_table, washer_dryer_unit
- storage_shelving, dressing_wardrobe, desk, office_chair, coat_rack
- bathroom_vanity, rug, wall_art (modern only)

All in `data/furniture-assets/full-catalog/`

**Still needed (21 pieces, 41 items):**
- wall_art/classic
- mirror (modern + classic)
- floor_lamp (modern + classic)
- table_lamp (modern + classic)
- potted_plant (modern + classic)
- shower (modern + classic)
- bathtub (modern + classic)
- sink (modern + classic)
- towel (modern + classic)
- clothing_rack (modern + classic)
- shoe_rack (modern + classic)

---

## Next Action — TODAY

**From the repo directory, run:**

```bash
cd C:\dev\Floorplan-tools\born2thrill-local-workbench
node --env-file=.env.local scripts/tripo-generate-furniture-full.mjs
```

This will:
1. Skip the 27 pieces already generated (the script detects them)
2. Generate the 21 remaining pieces with your new 1000 credits
3. Write results to `data/furniture-assets/full-catalog/full-catalog-manifest.json`

**Budget:** 21 pieces × 30 credits = 630 credits. You have 1000 left, so this will complete with 370 to spare.

---

## After Generation Completes

1. **Check the manifest** at `data/furniture-assets/full-catalog/full-catalog-manifest.json`
   - Verify all 54 pieces succeeded (should show no failures)
   - Note the total credits consumed

2. **Next phase:** Extend `export-floorplan-blender.py`
   - Room floors, furniture instancing, scale normalization (§4 in original handoff)
   - Test rendering with 6 pieces first, then full floors
   - This is the actual quality gate before declaring victory

3. **Commit everything** to `agent/zuhausefinder-generator`
   - All `.glb` files, test results, updated manifests
   - Decide whether `.glb` binaries stay here or move to `born2thrill-local-workbench-data`

---

## Key Invariants (§7 of original handoff)

- Furniture data must **never** affect `geometry_hash`
- Rights decisions and approvals are **Rainer's alone**
- All work so far is additive — rollback is deletion of new files

---

## Files Changed Today

- Purchased additional credits (external, logged at https://platform.tripo3d.ai)
- About to regenerate with `tripo-generate-furniture-full.mjs`
- No code changes yet (Blender extension is next)
