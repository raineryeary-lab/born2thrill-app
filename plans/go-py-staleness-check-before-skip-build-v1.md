# "Bauen" must not silently skip a stale certificate

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer: "i just saved it and codex says the last save is an hour ago and
you say the last save was 6 hours ago? This is not working we need a good
and secure save and a new build when 'Bauen' is clicked."

Root cause of the trust problem, confirmed by reading the actual code the
"Bauen" button runs: it does NOT reliably produce a fresh build. The
Hausakte's "Bauen" step (`src/app/api/floorplan-workbench/pipeline/
route.ts:134`) runs `scripts/go.py <plan>`. Inside it, `treibe()`'s build
step is gated by:

```python
if not zertifikat(name):
    ... run run_project.py ...
```

where `zertifikat(name)` is just `read_json(.../delivery-manifest.json)` —
**a truthy check for "does a manifest file exist," nothing about whether it
still matches today's annotation, furniture, or renderer code.** Once
bungalow_039 had ANY certificate (from this session's earlier rebuild),
every subsequent click of "Bauen" found `zertifikat(name)` truthy, skipped
`run_project.py` ENTIRELY, and reported "gebaut und zertifiziert" — a false
claim. A save made after that point is real (confirmed: `annotations.json`
`updated_at` does update correctly), but nothing downstream of "Bauen" ever
picks it up.

This is exactly the confusion in the report: three different tools
(Rainer's own "just saved," Codex's "an hour ago," this session's
file-timestamp check) all disagreeing is a symptom of there being no single
enforced link between "the annotation changed" and "the certified build
reflects it."

## Current evidence and behavior

- `scripts/go.py` `zertifikat()` (function definition, ~line 64): `return
  read_json(os.path.join(DATA, "corrections", name, "renders",
  "go-baseline", "delivery-manifest.json"))` — existence only.
- `scripts/go.py` `treibe()`: `if not zertifikat(name): ... run_project.py
  ...` — the ONLY gate on whether a build actually runs.
- This exact class of bug — "a manifest's mere presence treated as current,
  without checking what it certifies against" — was already found and
  FIXED once, in the sibling script `scripts/batch-build.py`, per its own
  docstrings/comments (`:137-` `built_hash()`): "Missing, partial, corrupt,
  classic, or old .blend files can be declared current ... Batch 'current'
  must consult only that manifest" (re: artifact tampering), and separately
  "A renderer change invalidates a delivery as surely as an annotation
  change ... exactly the 'silently delivering a renderer-obsolete artifact
  set' risk" (re: toolchain hash never being compared). `batch-build.py`
  now correctly checks, in order: the manifest's recorded `toolchain` hash
  against `toolchain_now()` (a fresh hash of the four pipeline scripts),
  the furniture folder's fingerprint, every artifact's recorded size (and,
  unless `--ohne-pruefsumme`, its sha256), and only THEN trusts the
  manifest's `input_hash` (a combined hash of the annotation AND
  `gebaeudemass.json`) as "what this delivery was built from" —
  comparing that against a freshly computed hash of the CURRENT annotation
  (`annotation_state()`, ~line 90-) to decide whether a rebuild is needed.
- `go.py` has never had any of this. It was written as the simpler
  original "one command" driver and predates `batch-build.py`'s hardening
  — the two scripts do the same job (decide whether a house needs
  building) with genuinely different rigor, which is exactly the
  "second implementation that quietly drifts" failure mode this
  codebase's own comments warn about elsewhere (this session's earlier
  `build_floor_walls_and_openings()` extraction was motivated by the exact
  same concern).
- Confirmed this session, independently, before this bug was found: every
  fix made today to `build-simplifier-render-plan.py` (walls/openings,
  area_m2, the merge-offset sign bug) was verified via `run_project.py`
  directly, which always rebuilds unconditionally — so today's own
  verification was never affected by this bug. It is specifically the
  "Bauen" BUTTON path (`go.py`) that silently skips.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `scripts/go.py`, `scripts/batch-build.py`: both untracked (new,
  uncommitted) this session — not otherwise touched today.

## Exact scope

1. In `scripts/go.py`, replace `zertifikat(name)`'s existence-only check,
   at its ONE call site in `treibe()`, with a genuine staleness check reusing
   `batch-build.py`'s own `annotation_state()`, `built_hash()`, and
   `toolchain_now()` — loaded via `importlib.util` (this repo's established
   pattern for importing a hyphenated-filename sibling script, already used
   in `build-simplifier-render-plan.test.py` this session), not
   reimplemented a second time.
2. `treibe()`'s build step becomes: compute `current, reason =
   annotation_state(name)`; if `reason` (annotation unreadable/blocked),
   surface that instead of guessing; else run `run_project.py` UNLESS
   `built_hash(name) == current` (genuinely current, matches
   `batch-build.py`'s own skip condition exactly).
3. Keep `zertifikat(name)` itself (still used after the build step, to
   decide whether the build succeeded) — only the SKIP DECISION changes,
   not the "did it work" check afterward.
4. No `--force` flag needed for `go.py` specifically (unlike
   `batch-build.py`, which is a batch tool over many houses where forcing
   is a deliberate power-user action) — `go.py`'s whole point is "one
   house, push it as far as it goes," and the fixed staleness check already
   means "Bauen" only skips when TRULY nothing changed; that is correct
   behavior; making the button always force-rebuild even with zero changes
   would just make "Bauen" slow for no reason on an already-current house.

## Files in scope

- `scripts/go.py` only (`zertifikat`'s call site in `treibe()`; the
  function itself stays for the post-build check).

## Explicitly out of scope

- No change to `batch-build.py` — it already has the correct logic; this
  plan only reuses it.
- No change to `run_project.py`, `build-simplifier-render-plan.py`, or any
  renderer script.
- No change to the Hausakte's own "Möbel veraltet" staleness banner
  (`/haus/page.tsx`, already correct, unrelated code path using
  `/api/floorplan-workbench/staleness`).
- No new `--force` flag or UI control added — out of scope unless a real
  need for one shows up after this fix ships.

## API, schema, and data-contract effects

None. `go.py` is a local CLI script invoked as a subprocess by the
pipeline route; no schema change.

## Acceptance criteria

- On a house with a certificate whose recorded `input_hash` genuinely
  matches the current annotation+Gebäudemass state, AND whose toolchain
  hash matches the current pipeline scripts, AND whose artifacts are intact
  at their recorded size: clicking "Bauen" reports "gebaut und zertifiziert"
  WITHOUT re-running `run_project.py` (unchanged, correct, fast case).
- On bungalow_039 right now (annotation edited multiple times today since
  its one certificate from earlier in the session): clicking "Bauen" (or
  running `python go.py bungalow_039`) DOES re-run `run_project.py` and
  produces a fresh certificate reflecting the current annotation.
- Editing the annotation, saving, then immediately running `go.py` again:
  it rebuilds. Running it a second time right after with no further edits:
  it skips (this is the exact regression test — build once, verify skip;
  edit; verify rebuild).
- A renderer code change (e.g., re-running after this session's earlier
  wall-merge fix) correctly invalidates existing certificates for houses
  built before that fix, same as `batch-build.py` already does.

## Tests and verification commands

No existing test file covers `go.py` (confirmed: no `go.test.py`). New test
`scripts/go.test.py`, following this repo's established `unittest` +
`importlib.util` convention: build a temp/fake `DATA` and `PROJECTS` layout
(or exercise `treibe()`'s decision logic directly against a stubbed
`annotation_state`/`built_hash`, whichever proves less brittle once the
actual import wiring is written) asserting:
- a certificate whose `built_hash()` matches the current annotation hash
  is skipped (no subprocess spawned — verified by monkeypatching `run()`
  and asserting it was not called for the build step).
- a certificate whose `built_hash()` does NOT match (simulating either an
  annotation edit or a toolchain change) triggers a `run_project.py` call.

Verification commands:

```
cd born2thrill-local-workbench
python scripts/go.test.py -v
python scripts\go.py bungalow_039              # first call: should rebuild (stale)
python scripts\go.py bungalow_039              # second call, no edits: should skip
```

Plus manual: click "Bauen" in the Hausakte for bungalow_039, confirm the
build actually runs (visible in the returned `ausgabe` text / timing) this
time, and that the resulting `delivery-manifest.json`'s `input_hash` now
matches a freshly computed hash of the current `annotations.json`.

Existing tests are not deleted, skipped, or weakened.

## Protected and risky paths

- `go.py` is the actual code path behind every "Bauen" click, and also
  behind `--alle` batch runs across the whole corpus (`go.py --alle`) —
  mitigated by reusing already-correct, already-tested logic from
  `batch-build.py` rather than writing new staleness logic, and by the
  explicit skip/rebuild regression test above.
- Risk of the fix making "Bauen" SLOWER than expected if it now rebuilds
  houses that were previously (wrongly) treated as current — this is the
  correct, intended behavior change (a wrong skip becoming a right
  rebuild), not a regression, but worth flagging: `go.py --alle` run
  against the full corpus will very likely rebuild MORE houses than before
  the first time it runs after this fix ships, since every house whose
  toolchain became stale from today's earlier renderer fixes (wall-merge,
  area_m2) was previously invisible to `go.py`'s check.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This plan makes the OPPOSITE of that failure mode
harder, not easier: it stops a stale, no-longer-matching certificate from
being silently treated as valid. No new publish/email/generate path is
added.

## Customer, email, database, deployment, and external effects

None directly. Indirect, and intended: houses previously reported "gebaut
und zertifiziert" on a stale certificate will now correctly rebuild the
next time "Bauen" (or `go.py --alle`) runs.

## Failed-hypothesis log

Not applicable — root cause found by direct code reading (tracing the
"Bauen" button to `pipeline/route.ts` to `go.py` to `zertifikat()`), not by
trial and error.

## Rollback

Pure code change on an already-dirty, uncommitted working tree, one
function's call site in one file. Revert to undo; nothing else touched.

## Unresolved questions

- Exact shape of `go.test.py`'s fixtures (real temp directories vs.
  monkeypatched functions) — will pick the lower-friction approach once
  writing it and report the choice, per this repo's established practice
  this session for new Python tests.

## Completion record (2026-08-22)

Implemented as scoped: `zertifikat(name)`'s existence-only check replaced
at its skip-gate call site with `ist_aktuell(name)`, which imports and
reuses `batch-build.py`'s own `annotation_state()`/`built_hash()` via
`importlib.util` (this repo's established pattern for a hyphenated-filename
sibling import) rather than reimplementing the check. `zertifikat(name)`
itself is untouched and still used for the post-build "did it actually
produce a certificate" check.

Verification:
- New `scripts/go.test.py` — 4/4 pass (skip-when-current,
  rebuild-when-mismatched, rebuild-when-no-certificate,
  fail-safe-when-blocked).
- Real end-to-end regression proof on bungalow_039 (the exact reported
  case): `python go.py bungalow_039` — first call correctly REBUILT (the
  existing certificate predated several annotation saves made this
  session, including Rainer's own), all verifier checks PASS, fresh
  certificate written. Second call, immediately after, with nothing
  further changed — correctly SKIPPED: reported "fertig" instantly with no
  `run_project.py`/Blender invocation at all.

Files changed: `scripts/go.py`, `scripts/go.test.py` (new).

## Approval record

Approved by Rainer, 2026-08-22 (explicit request: "we need a good and
secure save and a new build when 'Bauen' is clicked" — read as approval to
fix the confirmed root cause).
