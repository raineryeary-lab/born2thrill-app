# Bilder tab: show local renders alongside published ones

Status: APPROVED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-08-22 night: "why can i not see the floorplans under the
Bilder tab?" then "where are the Bilder?" (pointing at
/haus?plan=bungalow_039). The Bilder tab lists ONLY images published on
born2thrill.de (`published()` in publish/route.ts -> WP
`/wp-json/b2t/v1/bilder`); local renders never appear. bungalow_039 has
only 2 images left online (the vanished-attachments incident took the
rest), while all of tonight's fresh renders sit unpublished in
`corrections/<plan>/renders/go-baseline/`. Fix: the tab shows BOTH — local
renders badged "lokal", published ones badged "online" — so a built house
is always visible there without publishing anything.

## Current evidence and behavior

- `src/app/haus/page.tsx:310-318`: Bilder loaded solely from
  `GET /api/floorplan-workbench/publish?plan=...`.
- `publish/route.ts:130-136`: `published()` is a WordPress catalogue call.
- `overview/asset/route.ts` + `inventory.ts:resolveAssetPath()` already
  serve images safely from the inventory roots (localhost-only, root-key
  allowlist, path-escape refusal, resize via `?w=`); the primary root IS
  `FLOORPLAN_WORKBENCH_DATA_DIR`, which contains go-baseline.
- `inventory.ts` already defines `AUX_SUFFIXES` (-depth/-edge/-mask/
  -normal) — the technical passes the catalogue already excludes
  elsewhere.

## Exact scope

1. `publish/route.ts` GET: alongside `images` (online), also readdir
   `<primary root>/corrections/<plan>/renders/go-baseline/`, filter to
   image extensions minus AUX_SUFFIXES, and return
   `local: [{ name, url }]` where url points at the existing
   overview/asset route (`root=primary`, relative path, `w=768`).
   Plan name validated with the same `^[A-Za-z0-9_.-]+$` rule used by the
   sibling routes. Missing folder -> `local: []`, never an error.
2. `src/app/haus/page.tsx`: Bilder state gains the local list; the tab
   renders local images first (badge "lokal") then online ones (badge
   "online"); the delete-trashcan stays online-only (it deletes WP media);
   empty state text now distinguishes "nothing built yet" from "nothing
   online yet".

## Files in scope

- `src/app/api/floorplan-workbench/publish/route.ts`
- `src/app/haus/page.tsx`

## Out of scope

- Publishing/uploading anything (option 1 from the same conversation —
  separate, needs explicit go-ahead; nothing here touches WordPress
  beyond the existing read).
- The overview tab; the asset route (reused unchanged).

## Rights / suite invariant

Can any changed path generate, publish, or email geometry without an
approved reference? No — read-only listing of local files plus the
existing localhost-gated image server.

## Acceptance criteria

- /haus?plan=bungalow_039 Bilder tab shows tonight's local renders
  (exterior/interior PNGs, no -depth/-edge/-mask passes) badged "lokal",
  plus the 2 surviving online images badged "online".
- A plan with no renders shows the adjusted empty state, no error.
- Crafted plan names / path traversal refused (existing validation +
  resolveAssetPath).

## Verification

Manual in-browser at /haus?plan=bungalow_039 (localhost), plus a crafted
`?plan=../..` request confirming refusal. No existing automated tests
cover these routes (same situation as codex-tab-open-blend-buttons-v1).

## Rollback

Revert the two files.

## Approval record

Rainer, 2026-08-22 night: reported the gap, was offered exactly this
("make the Bilder tab also show local renders, marked lokal vs online"),
answered by pointing at the live page and asking "where are the Bilder?"
— read as approval to implement the local-display option. Publishing
remains NOT approved.
