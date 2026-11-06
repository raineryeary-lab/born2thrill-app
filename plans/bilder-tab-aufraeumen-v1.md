# Bilder-Tab: ganze Bilder, keine Doppelten, gross ansehen

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22, onehalfstorey_045: "most of them i cant even select to delete and most of them i cant select to show to customer and i cant even look at any of them because they are being cropped so badly".

## Current evidence (src/app/haus/page.tsx)

- CSS 209-213: `.bilder` is a grid inside a fixed-height flex area; `.bilder figure` has `overflow:hidden`, so the grid rows shrink to fit the visible height -> each card is a thin strip (screenshot 045: 26 cards squeezed into one screen).
- 919-930: `lokaleBilder` (local Codex delivery + go-baseline raw builds) are drawn FIRST, without any buttons; the online pictures (with ☑/★/🗑) come after. For 045 the 10 Codex pictures are online too, so they appear twice -- the top 16 cards have no buttons.
- No way to open a picture large.

## Exact scope (page.tsx only)

1. CSS: grid rows sized to their content (`grid-auto-rows:max-content; align-content:start`), image shown whole (no crop).
2. Order and duplicates: the ONLINE pictures first (with their buttons). A local Codex picture whose name is already online is not shown again. Local Codex pictures that are NOT online yet follow, marked "noch nicht hochgeladen". Raw builds (Rohbau) last, under a small heading "Rohbau (nur intern)".
3. Click on a picture opens it full size in a new browser tab.

## Out of scope

- Uploading/deleting logic, the WordPress routes, the 22 s house-list load (roadmap).

## Tests (first)

A pure helper `bilderOrdnen(online, lokal)` in `src/lib/floorplan-workbench/bilder-ordnen.mjs` + `scripts/bilder-ordnen.test.mjs`: online first; local with an online name dropped; local finals not online kept; Rohbau last. Seam check: page.tsx uses it and the CSS has `grid-auto-rows`. Then look at 045 in the browser: whole pictures, 10 with buttons, 6 Rohbau at the end.

## Safety gate

Can any changed path publish geometry without an approved reference? No -- display only.

## Rollback

`page.tsx.before-bilder-aufraeumen`; delete the helper and its test.

## Approval record

Rainer in chat, 2026-10-22: "Approved: implement bilder-tab-aufraeumen-v1, tests first, check it on onehalfstorey_045."

## Implementation record (2026-10-22)

- New `src/lib/floorplan-workbench/bilder-ordnen.mjs` + `scripts/bilder-ordnen.test.mjs` (5 tests, red before, green after).
- `src/app/haus/page.tsx`: `geordnet = bilderOrdnen(bilder, lokaleBilder)`; online first with their buttons, then "Fertig (Codex), noch nicht hochgeladen", then "Rohbau (nur intern)"; every picture wrapped in a link opening it full size in a new tab; CSS `grid-auto-rows:max-content; align-content:start`. tsc: no errors in page.tsx.
- Browser, onehalfstorey_045: 16 cards instead of 26 (10 online with buttons, 6 Rohbau under their heading), pictures shown whole (screenshot).
