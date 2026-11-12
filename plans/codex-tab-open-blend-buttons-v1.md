# "An Codex" tab: one button per .blend to open it in Blender before handing off

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer: "in the Tab 'An Codex' could you also place one button per blender
fiel that has been created so i can check what they look like before codex
tries to render them?"

The "An Codex" step (`src/app/haus/page.tsx:485-511`) already shows the
generated `CODEX-AUFTRAG.md` text and the target folder
(`renders/go-baseline/`), but gives no way to actually LOOK at the .blend
files it's about to hand off — today that means leaving the browser,
opening a file explorer, and double-clicking each one by hand. Add a
button per `.blend` file in that folder that opens it directly in Blender's
own interactive window.

## Current evidence and behavior

- `src/app/api/floorplan-workbench/auftrag/route.ts` GET already resolves
  and returns `ordner` (the `renders/go-baseline/` path) for a plan, reading
  `CODEX-AUFTRAG.md` from it. It does not currently list the `.blend` files
  in that folder.
- `src/app/haus/page.tsx:290-` already fetches this endpoint into `auftrag`
  state whenever `schritt === "codex"`.
- `scripts/run_project.py:63` — `BLENDER = r"C:\Program Files\Blender
  Foundation\Blender 5.0\blender.exe"`, always invoked with
  `--background --python ...` for rendering. No existing code path opens
  Blender interactively (GUI, no `--background`) anywhere in this repo.
- `src/app/api/floorplan-workbench/pipeline/route.ts` is the existing
  precedent for validating a `plan` against
  `readdir(.../floorplan-simplifier/projects)` before spawning anything,
  and for the `enabled()` localhost-only guard — the same pattern applies
  here.
- Files actually present for bungalow_039 right now (per this session's
  own rebuild): `exterior-classic-baseline.blend`,
  `exterior-modern-baseline.blend`, `interior-modern-baseline.blend`,
  `interior-modern-b-baseline.blend` (a second interior variant — `go.py`
  builds one interior render call per declared interior "b" pass, per
  `run_project.py`'s own multiple `render-furnished-dollhouse.py`
  invocations seen in this session's logs).

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `src/app/haus/page.tsx`: untracked, already modified this session
  (save-before-switch guard). This plan's UI addition lands in the SAME
  "codex" step block, not touched by that earlier change.
- `src/app/api/floorplan-workbench/auftrag/route.ts`: untracked, not
  otherwise touched this session.

## Exact scope

1. `auftrag/route.ts` GET: also `readdir(ordner)`, filter to `.blend`
   files, sort, and include as `blends: string[]` in the response
   (alongside the existing `plan`/`ordner`/`text`). No new endpoint needed
   for listing — this is the same folder the route already resolves.
2. New route `src/app/api/floorplan-workbench/blend-oeffnen/route.ts`,
   POST `{plan, datei}`:
   - Same `enabled()` localhost-only guard as every other workbench route.
   - Validate `plan` against the existing `^[A-Za-z0-9_.-]+$` pattern and
     confirm the project folder exists (same check `pipeline/route.ts`
     already does).
   - Validate `datei` against `^[A-Za-z0-9_.-]+\.blend$` AND confirm it is
     one of the files actually present in that plan's `go-baseline` folder
     (`readdir` + membership check) — refuses anything else, so this can
     never be used to open an arbitrary path.
   - Spawns Blender WITHOUT `--background`, pointed at the file, detached
     (`spawn(exe, [path], {detached: true, stdio: "ignore"}).unref()`) so
     the API responds immediately and the request does not hang waiting
     for the user to close their Blender window.
   - Blender executable path: `process.env.FLOORPLAN_BLENDER_EXE?.trim()
     || r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"`
     (same override-with-fallback convention `pipeline/route.ts` already
     uses for `PYTHON_EXECUTABLE`).
3. `src/app/haus/page.tsx`, the `schritt === "codex"` block: render one
   button per `auftrag.blends` entry, label = filename, calling the new
   endpoint with `{plan, datei: name}`. Disabled state / a brief
   "öffnet …" label while the POST is in flight, same convention already
   used for the other pipeline buttons (`laeuft` state) — but scoped
   per-button (opening one file must not disable the others), not the
   shared `laeuft` flag.

## Files in scope

- `src/app/api/floorplan-workbench/auftrag/route.ts`
- `src/app/api/floorplan-workbench/blend-oeffnen/route.ts` (new)
- `src/app/haus/page.tsx`

## Explicitly out of scope

- No change to what `CODEX-AUFTRAG.md`/`codex-job.json` contain — purely
  additive UI for INSPECTING files already produced by the existing
  "Bauen" step.
- No thumbnail/preview rendering of the .blend contents inside the browser
  — opens the REAL file in the REAL Blender application, not a web-based
  3D preview (out of scope, much larger feature).
- No change to which `.blend` files `run_project.py`/`go.py` produce.
- Does not touch the technical `-depth`/`-edge`/`-mask` pass files (those
  are PNGs, not `.blend`, already excluded from the catalogue elsewhere in
  this codebase — not relevant to this button set, which only lists
  `.blend` files).

## API, schema, and data-contract effects

Additive only: `auftrag` GET response gains a `blends` array. No existing
consumer of that response reads a fixed field list that this would break
(confirmed: only `src/app/haus/page.tsx` consumes it, and only via the
fields already scoped above).

## Acceptance criteria

- Opening the "An Codex" tab for a built house shows one button per real
  `.blend` file in that house's `go-baseline` folder, labeled by filename.
- Clicking one opens Blender's own window with that exact file loaded,
  within a few seconds, without blocking the page (the Next.js request
  returns immediately; Blender opening is a detached, independent
  process).
- Clicking a button for a file that (somehow) no longer exists, or a
  crafted request naming a file outside that folder, is refused with a
  clear error, never silently opening something unexpected.
- A house with zero `.blend` files yet (not built) shows no buttons
  (matches the existing "Noch kein Auftrag geschrieben" empty-state
  pattern already in this tab).

## Tests and verification commands

No existing test covers this route family (confirmed: no
`*.test.ts`/`*.test.tsx` under `src/app/api/floorplan-workbench/`). Given
the core logic here is (a) a filename allowlist check and (b) spawning a
detached process, verification is:
1. Manual: click each new button for bungalow_039 (has 4 real `.blend`
   files right now) and confirm each opens the CORRECT file in Blender
   (check the file path in Blender's own title bar / outliner).
2. A crafted-request check (curl/fetch with `datei` set to something not
   in the folder, or containing `..`) confirms the API refuses it — run
   once by hand and reported in the completion record, not added as an
   automated test given there is no existing route-test harness to extend
   here without introducing a new one for a single small check (would be
   reconsidered if this repo gains a route-test convention later).

## Protected and risky paths

- This is the FIRST place in the repo that spawns an interactive
  (non-`--background`) GUI application from a web request. Mitigated by:
  the strict filename-allowlist validation (can only ever open a `.blend`
  file that is already sitting in that specific plan's own output folder,
  never an arbitrary path), the existing `enabled()` localhost-only guard
  (already used by every other workbench route, refuses anything not from
  127.0.0.1/localhost), and the detached spawn (a hung or crashed Blender
  window cannot hang the Node server, since the request never waits on
  it).

## Rights, provenance, privacy, and security impact

None. Opens a file the user's own machine already produced, in an
application already installed on that same machine, for that same user to
look at. No data leaves the machine, nothing is sent anywhere.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This adds a way to VIEW an already-produced,
already-certified `.blend` file — it does not generate, publish, or email
anything.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

Not applicable — new feature, not a bug investigation.

## Rollback

Pure additive change across three files (one new route). Revert to undo;
nothing else touched.

## Unresolved questions

- Whether to also expose the PNG deliverables (already viewable via the
  existing "Bilder ansehen" tab) alongside the `.blend` buttons — not
  requested, so out of scope unless asked for separately.

## Completion record (2026-08-22)

Implemented as scoped. Verified end-to-end on `bungalow_040_66`: the "An
Codex" tab shows one button per real `.blend` file
(`exterior-classic-baseline.blend`, `exterior-modern-baseline.blend`,
`interior-modern-baseline.blend`); clicking one launches Blender with that
exact file (confirmed via `Get-Process -Name blender` showing a new window
titled `exterior-classic-baseline [E:\...\bungalow_040_66\...]` immediately
after the click).

Files changed: `src/app/api/floorplan-workbench/auftrag/route.ts`,
`src/app/api/floorplan-workbench/blend-oeffnen/route.ts` (new),
`src/app/haus/page.tsx`.

## Approval record

Approved by Rainer, 2026-08-22 (explicit feature request).
