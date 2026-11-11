# Workbench overview tab: inventory of everything produced

Status: IMPLEMENTED (read-only feature, 2026-08-16)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Give Rainer one page that lists every render and floorplan the suite has produced so far,
with its data, so he can see what exists, what is ready to hand to Codex, and what is still
incomplete. Read-only: the feature must never write, move or delete anything under
`corrections\`, `revisions\`, `furniture\`, `renders\` or the annotator's `projects\`.

## Current evidence and behavior (before)

- `/floorplan-workbench` shows exactly one project at a time (the correction editor).
- No page lists what has been rendered. `handoff.json` files, `plan-<style>.json`, revisions,
  furniture and exports were only visible on the filesystem.
- Render output is split over two similarly named data roots (see WORKBENCH-DATA-ROOTS-001).

## Exact scope

New read-only route + API. No existing behaviour changed except one added nav link.

## Files in scope

- ADDED `src/lib/floorplan-workbench/inventory.ts` — scanner: resolves the three roots, walks
  `corrections\<project>\{renders,revisions,furniture,exports,blender}` in both data roots and
  `floorplan-simplifier\projects\<project>`, summarises handoff/catalog/plan/revision/furniture
  JSON, derives readiness. Only `stat`/`readFile`.
- ADDED `src/app/api/floorplan-workbench/overview/route.ts` — `GET`, localhost gate copied from
  `corrections/route.ts`, returns `zf-floorplan-workbench-overview-v1`.
- ADDED `src/app/api/floorplan-workbench/overview/asset/route.ts` — `GET` one image out of the
  allow-listed roots; refuses absolute paths, `..` escapes, unknown roots and non-image
  extensions; downscales rasters with sharp (`?w=`).
- ADDED `src/app/floorplan-workbench/overview/page.tsx` — the tab itself.
- CHANGED `src/app/floorplan-workbench/page.tsx` — two nav pills in the existing header
  (Correction editor / Overview). No other change.

## Explicitly out of scope

- `floorplan-simplifier\**` (annotator), `scripts\**` (render pipeline), the correction and
  furniture editing code paths, `**\symbols\**` in either repo (another agent is working there).
- Reconciling the two data roots. The split is reported, never repaired.

## Acceptance criteria

- No write path exists in the added code. Verified by inspection: the new files import only
  `readFile`, `readdir`, `stat` and `sharp`.
- Both API routes 404 for a non-localhost `Host` header and when
  `FLOORPLAN_WORKBENCH_ENABLED !== "true"`.
- The asset route refuses `..\..\Windows\win.ini`, `handoff.json` and unknown roots.
- `npx tsc --noEmit` passes.
- The tab renders with real data at `http://127.0.0.1:3020/floorplan-workbench/overview`.

## Verification performed (2026-08-16)

- `npx tsc --noEmit` — clean.
- `GET /api/floorplan-workbench/overview` — 200, 292 projects, 3 roots present.
- Asset route: baseline PNG 200 image/webp, room-concept SVG 200 image/svg+xml,
  `../../../Windows/win.ini` 404, `handoff.json` 415, `root=bogus` 404,
  `Host: evil.example.com` 404.
- In-browser at 127.0.0.1:3020: all filters, details expansion and 12/12 thumbnails load;
  the correction editor still loads `revision-0001.json` as before.

## Rights, provenance, privacy, and security impact

None changed. The page carries the unchanged "INTERNAL REVIEW – NOT FOR CUSTOMER DELIVERY"
framing, stays behind the same localhost gate as the rest of the workbench, and surfaces
existing internal records only. No export, approval or eligibility flag can be set from it.

## Floorplan-suite invariant

> Can any changed path generate, publish, or email geometry without matching an approved
> corrected corpus reference?

No. The added code has no `writeFile`, `mkdir`, `rename`, `unlink` or `spawn`; it cannot
create geometry, approve anything, or send anything. It only reads and displays what other,
unchanged code paths already produced.

## Follow-ups recorded

- WORKBENCH-DATA-ROOTS-001 (canonical roadmap): the two data roots.
