# Bilder-Tab zeigt den Codex-Lieferordner

Status: DONE 2026-10-21

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-21: "i have to be able to see it in the annotator". onehalfstorey_044: Codex delivered 9 pictures into `renders/codex-onehalfstorey_044-2026-10-20` (the folder named in codex-job.json) and uploaded them. The house page showed only the raw builds.

## Current evidence

`src/lib/floorplan-workbench/angenommener-ordner.mjs` picks the folder for the Bilder tab (`publish/route.ts localRenders`) and the picture count (`state/route.ts`): `ANGENOMMEN.json`, else the alphabetically last `codex-final-*`. The job's `delivery_folder` (`codex-<plan>-<datum>`) is neither, so it is never shown unless the strict check accepted it.

## Exact scope

`angenommener-ordner.mjs` only. Order:
1. `ANGENOMMEN.json` (unchanged);
2. NEW: the folder named by `go-baseline/codex-job.json` `delivery_folder`, if it exists under `renders/` and holds at least one picture;
3. the old `codex-final-*` rule (unchanged).

Out of scope: the check itself, uploading, who uploads (Rainer, 2026-10-21: keep Codex uploading for now).

## Tests (first)

`scripts/angenommener-ordner.test.mjs`, new cases:
- no pointer + job folder with pictures -> job folder (even if a `codex-final-*` exists);
- pointer still wins over the job folder;
- job folder named but empty or missing -> old rule.
Existing 6 cases stay unchanged.

## Safety gate

Can any changed path publish geometry without an approved reference? No. This only changes which local folder the page displays and counts; nothing is uploaded or released.

## Rollback

Restore `angenommener-ordner.mjs.before-codex-ordner`.

## Approval record

Rainer in chat, 2026-10-21, to "the house page should just show whatever Codex put in its folder ... Should I do it?": "ok".

## Implementation record (2026-10-21)

- `ordnerAusZeiger(zeiger, namen, lieferordner)` + `lieferordnerMitBildern(renders)`; 3 new tests, 9/9 pass; house-state 28/28.
- Real lookup: onehalfstorey_044, twostorey_059, bungalow_007 now resolve to their `codex-<plan>-2026-10-20` folders (before: none).
- Browser: Bilder tab of onehalfstorey_044 shows the 9 pictures (exterior with cover star, 8 interiors) plus the raw builds.
