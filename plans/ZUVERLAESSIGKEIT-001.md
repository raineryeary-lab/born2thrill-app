# ZUVERLAESSIGKEIT-001: Hausakte, upload/Freigabe buttons, annotator Massstab

Status: DONE 2026-10-25 (approved by Rainer: "all of it check with codex and recheck"; Codex final re-review: Ready)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make the Hausakte open the requested house at once, make every action button report the true result exactly once, and make the annotator's Massstab and floor alignment agree with the build. The source is two Codex read-only reviews of 2026-10-25 (scratchpad `codex-out.md`, `codex-out-2.md`).

## Current evidence

- `/api/floorplan-workbench/state` takes 37 s. 23.8 s of that is SHA-256 over 24.75 GB of .blend files (105 houses) on every load.
- `page.tsx` holds `plan=""` until the list arrives, so the iframe gets `annotate.html?project=`.
- `batch-build.py:221` prints a checksum warning to stdout. That breaks the JSON from `haus-zustand.py --alle`, and the route then falls back to `{}` (every house uncertified).
- `go.py` returns 0 after a failed upload, so the pipeline route reports `ok:true`.
- Crop or replace image in the annotator keeps `floor_scale` (metres per image width).

## Scope (finding IDs from the review table)

**Part 1: Hausakte page** (`src/app/haus/page.tsx`)
- A1: select the URL plan before the list arrives and render its iframe immediately; with no plan, show a loading state, never `project=`.
- A2: a requested plan that is missing from the list stays selected, with a visible notice; HTTP/schema errors are shown and the previous list is kept; a default house is picked only when no plan was requested.
- A6: ignore late responses (plan/request generation guard) for images, roof, rights, job, Codex return, and overlapping `laden()`; postMessage handlers check `event.source === rahmen.contentWindow` and the project.
- B3: after upload, release, or Codex import, reload the selected house's images immediately.
- B4: image release and Titelbild get a pending/disabled state; one request at a time per control.

**Part 2: State route and freshness** (`state/route.ts`, `scripts/batch-build.py`, `scripts/haus-zustand.py`)
- A3: a persistent SHA-256 cache keyed on resolved path, size, and mtime_ns, in a JSON file under the data root. On a miss or mismatch, rehash. The checksum comparison itself stays. Write-then-rename.
- A4: diagnostics go to stderr. The route checks the exit code, drains stderr, and applies a deadline; a failure becomes an explicit `zustand_unbekannt` error in the response instead of `{}`.
- A5: run the catalogue fetch and the Python process in parallel; per-house image lookups run with bounded concurrency (6); every fetch gets a timeout.
- A7: compute the annotation hash fresh (4.8 MB over all houses) instead of trusting `source-state.json`.
- Toolchain hash once per process (memoized).
- Ledger write uses a unique temp file name.

**Part 3: Upload and Freigabe** (`scripts/go.py`, `scripts/publish-renders.py`, `api/.../pipeline`, `bild-freigabe`, `titelbild` routes)
- B1: `haustyp_nachziehen` failing on the old plugin (HTTP 400) prints a clear warning and continues with the upload. The Haustyp correction is skipped, not fatal.
- B2: a failed upload step returns a non-zero exit code and passes the publisher's last output lines to the UI.
- B5: `urlopen(timeout=60)`; the pipeline route has a process deadline; the browser shows the timeout.
- B6: bild-freigabe and titelbild validate the WordPress JSON and confirm the state they set.
- B7: a per-plan upload lock file in the data root; a second upload while one is running is refused with a message.

**Part 4: Annotator** (`floorplan-simplifier/app.py`, `static/punkte-ausrichten.js`, `static/geometry-tools.js`)
- C1: crop or replace image clears that floor's `floor_scale` and `annotation_space` (and the sidecar value for that floor) and tells the user to measure again.
- C2: the overlay uses the build's pairing rule (each mark to its nearest groundfloor mark, `build-simplifier-render-plan.py:1106`) instead of click order. If both marks pick the same target, the annotator shows a warning ("Ausrichtpunkte mehrdeutig, neu setzen"). **The build script is NOT edited**: it is in the toolchain hash, and a change would mark every delivery stale.
- C3: calibration uses the image dimensions, not the canvas with its margin.
- C4: the annotations endpoint merges `gebaeudemass.json` like `hausdaten.py` does (scale per floor, annotation_space, roof fields).
- C5: warning only, in the annotator. If the two alignment marks imply rotation over 2°, show a warning. The 350 mm snapping stays unchanged.

## Out of scope

- A8 (a stale build shows "fertig"): this is Rainer's explicit rule "fertig ist fertig" (2026-10-18). Unchanged.
- Changing the 350 mm snap, rotation support, plugin deployment (Rainer's click), and any upload or production write.

## Tests (add first; no existing test weakened)

- `batch-build`: a warning never goes to stdout; a cache hit skips the rehash, and a changed size or mtime rehashes; a mismatch is still detected.
- `haus-zustand --alle` output is valid JSON even when a checksum mismatches.
- `go.test.py`: a failed upload gives exit code ≠ 0.
- `publish-renders`: an HTTP 400 on haustyp is not fatal.
- annotator: crop clears `floor_scale` for that floor only; alignment pairing does not depend on click order (JS test and Python test give the same pairs).
- house-state tests unchanged and green.
- Existing suites: toolchain_gleich, go.test, house-state.test.mjs, make-codex-job.test, annotator tests.

## Invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** No change adds a publish path. Upload is still started only by Rainer's click. The checksum check stays (the cache only skips work when path, size, and mtime are unchanged). Freshness can only get stricter (A7).

## External effects

None. No uploads, no WordPress writes during the work, no deploy.

## Verification

- Every test suite is green.
- State route timed before and after.
- Hausakte opens the URL house in under 3 s.
- Codex re-review of the diff (read-only), then a second check.

## Rollback

Every file gets a `*.before-zuverlaessigkeit` copy. The cache file `E:\born2thrill-local-workbench-data\hash-cache.json` can be deleted.
