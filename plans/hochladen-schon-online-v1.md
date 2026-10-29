# Hochladen: erst nachsehen, was schon online ist

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22, onehalfstorey_vm2: "why cant i upload it?" -- all 10 pictures were already online (Codex uploads itself, Rainer 2026-10-21: keep it that way), but the Hochladen button answered with a refusal: "Codex-Lieferung unvollstaendig: ... state muss approved sein; marker_check fehlt (+17 weitere)".
Wanted: "Hochladen first checks WordPress and says 'schon online (10/10)' when all pictures are already there, instead of the refusal."

## Current evidence

- `go.py treibe(..., hochladen=True)` (codex-ein-ordner-ein-knopf-v1): reads `delivery_folder` from codex-job.json, runs `lieferung_fehlt()` (count + catalog.json + full `lieferung-pruefen.pruefe`), refuses on any complaint, else calls publish-renders.py.
- vm2: 10/10 online (`/wp-json/b2t/v1/bilder?plan=onehalfstorey_vm2`), names = the 10 `filename_hint`s without `.png`. The checker complains about Codex's catalog.json (no `state: approved`, no `marker_check`) and extra folders Codex left (review-copies, upload-*).
- `publish-renders.py existing_slugs(site, plan)` already reads exactly that list (public GET, no credentials).

## Exact scope (go.py only)

1. New `online_namen(plan)` -> set of picture names on WordPress (same public route as `existing_slugs`); on a network error -> None (then today's behaviour).
2. In `treibe(..., hochladen=True)`, BEFORE the delivery check: if every required picture of the job (`filename_hint` without `.png`) is online -> return `(True, "schon online (10/10)")` and upload nothing. If some are online -> the message names how many, e.g. "7/10 schon online"; the check and upload then run as today for the rest.
3. Nothing else changes: the strict check still guards every upload that would actually happen.

## Out of scope

- Whether the pictures online are the right version (that is the Codex/Rainer review), `--send`, freigeben.

## Tests (first, go.test.py)

- all required online -> no run() call, `(True, "schon online (10/10)")`;
- WordPress not reachable (None) -> today's path (check runs);
- 7 of 10 online -> message contains "7/10 schon online", check runs.
- Existing go tests unchanged.

Real check: `go.py onehalfstorey_vm2 --hochladen` -> "schon online (10/10)", nothing uploaded.

## Safety gate

Can any changed path publish geometry without an approved reference? No -- the new path only reads and returns; it never uploads.

## Rollback

`go.py.before-schon-online`, revert the test additions.

## Approval record

Rainer in chat, 2026-10-22: "Approved: implement hochladen-schon-online-v1, tests first, check it on onehalfstorey_vm2."

## Implementation record (2026-10-22)

- `go.py`: `online_namen(plan)` (public GET, 20 s timeout, None on error); `treibe(..., hochladen=True)` returns `(True, "schon online (n/n)")` before any check when all required pictures are online; partial -> "k/n schon online; " in front of today's message. The house-list line prints the "schon online" sentence instead of a bare "fertig".
- Tests first: go.test.py +3 (2 red before, all green after; existing go tests unchanged).
- vm2: `go.py onehalfstorey_vm2 --hochladen` -> "schon online (10/10)", nothing uploaded; without --hochladen still "fertig".
