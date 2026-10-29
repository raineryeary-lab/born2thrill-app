# BAU-SCHNELLER-001: faster builds, stop early on errors

Status: DONE 2026-10-28 (approved by Rainer: "ok do it"; Codex re-review #3: Ready)

## Measured (german_catalog_review_onehalfstorey_1_2_2_efh_140_1, 2026-10-27)

| Step | Time |
|---|---|
| Plan building + 2 exteriors | ~1 min |
| Interiors (EG, DG) | ~2 min |
| Checks after the last blend (18 Blender calls in a row, each opens the 255 MB file) | ~3 min |

The stair check (R9) failed only at the very end, after 6½ minutes.

## Change (`scripts/run_project.py`, toolchain file)

1. **Run independent Blender jobs in parallel.**
   - Exterior and interior renders are independent once the plan JSON exists.
   - At most N Blender processes run at once (default 3, `BAU_PARALLEL` env, 1 = old serial behaviour).
   - Logs and outputs are per job, as today; nothing shares an output file.
2. **Parallel checks.** `verify_render_blend.py` and `verify_render.py` per blend/style run in the same bounded pool. Each one starts as soon as its own blend is finished, not after all renders.
3. **Stop early.**
   - As soon as one check or render fails, no new jobs start. Running jobs are allowed to finish, so no half-written blend is left behind. The build then fails with that first reason.
   - Certificate rules are unchanged: a failed build writes no delivery-manifest.
4. **Pre-check before Blender** (plan JSON only, no Blender): for 1,5-Geschosser (`anderthalb.ist_anderthalb`), check the top floor with `anderthalb.rechteck_mit_erkern` (the same function the exterior uses).
   - If it fails, stop with "1,5-Geschosser: DG-Umriss ist kein Rechteck (N Aussenwaende) – Aussenumriss im DG zeichnen", instead of silently building a two-storey box.
   - The stair length is NOT approximated. It fails early through point 3, because the upper-floor interior and its R9 check run first.

## Unchanged

Render scripts, checks, thresholds, outputs, manifest format, the toolchain list itself (only run_project.py's hash changes), go.py behaviour and exit codes.

## Effect

Every house shows "renderer changed" once. Ledgered houses stay "fertig" (FERTIG-IST-FERTIG). No geometry change.

## Tests

- **Scheduler:** with fake jobs, at most N run at once; a check starts after its own render, not after all of them; the first failure stops new jobs and is the reported reason; `BAU_PARALLEL=1` gives the old order.
- **Pre-check:** a 1,5-Geschosser with 6 DG outer walls is refused before Blender; a rectangle passes; a Zweigeschosser is not checked.
- Existing suites green: go.test, toolchain_gleich, make-codex-job, hash_cache, run_project tests if any.
- **Real build:** build one house that is currently fine (e.g. twostorey_056 or bungalow_037) and compare to the previous build:
  - same blend set, same verify PASS lines
  - geometry identical (mesh/vertex counts per object)
  - wall-clock time before and after

## Rollback

`run_project.py.before-bau-schneller`, or set `BAU_PARALLEL=1`.
