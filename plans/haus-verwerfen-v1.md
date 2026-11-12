# /haus: schlechte Grundrisse verwerfen

Status: DONE 2026-11-06

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-06: "can we also add a possibility for floorplans that are just shitty so I can delete them?"

## Current evidence

- `src/app/api/floorplan-workbench/discard/route.ts` already does this for renders: it MOVES the render into `_verworfen/` and never deletes it, local-only gate. The same safe pattern applies here.
- `floorplan-simplifier/projects/_verworfen-2026-08-23/` already holds old discarded houses as subfolders.
- Every list skips them:
  - `/haus` state route reads `readdir(projects)`;
  - Annotator `list_projects` (app.py 7244) needs `data.json` directly in the folder;
  - `konfigurator-matrix.py` 267 skips `_` names.

## Exact scope

1. New route `POST /api/floorplan-workbench/haus-verwerfen {plan}`:
   - same local-only gate as discard;
   - plan name must be a plain folder name (no `/`, `..`, leading `_`);
   - moves `projects/<plan>` to `projects/_verworfen/<plan>` (free name if it is already there);
   - never deletes anything.
2. Refusals:
   - the house is published in the WordPress catalogue → answer "erst im Katalog entfernen"; nothing on the website is touched;
   - a build is running for this plan.
3. `/haus`: button "Grundriss verwerfen" in the header of an open house:
   - confirm dialog "<plan> in den Papierkorb (_verworfen) verschieben?";
   - afterwards the list reloads and the next house opens.
4. The state route skips names starting with `_` (defensive; `_backup` and `_verworfen` stay out).

## Out of scope

- Builds and renders on E: stay where they are.
- No WordPress change.
- No real deletion. Emptying `_verworfen` stays Rainer's own job.

## Tests (first)

`scripts/haus-verwerfen.test.mjs`:
- bad plan names are refused;
- a temp project folder is moved, not deleted;
- a second discard of the same name gets a free name;
- published → refused;
- seam: the page calls the route and the state route skips `_` folders.

Real: a test copy of a project folder is made, discarded via the button, gone from /haus, present in `_verworfen`, then moved back.

## Safety gate

Can a changed path generate, publish or email geometry? No. It only moves a local folder; there is no delete, no WordPress call and no build.

## Rollback

- Remove the route and the button (`page.tsx.before-verwerfen`, `state/route.ts.before-verwerfen`).
- A discarded house returns by moving its folder back from `_verworfen`.

## Approval record

Rainer in chat, 2026-11-06: "Yes, build it".

## Implementation record (2026-11-06)

- `src/lib/floorplan-workbench/haus-verwerfen.mjs` (`planNameOk`, `hausVerwerfen`: move only, free name, refuses published / building); route `api/floorplan-workbench/haus-verwerfen` (local-only, reads the catalogue; catalogue unreachable -> refuses); state route skips `_` folders; `/haus` header button "Grundriss verwerfen" with confirm, then opens the next open house.
- Tests first: scripts/haus-verwerfen.test.mjs 6 (red before: module missing; green after); masse-fehlen 6 green; tsc clean for touched files.
- Live: copy `zz_verwerfen_test` of bungalow_012 -> button -> moved to projects/_verworfen, did not reappear, gone from /haus and the Annotator list, next house opened; POST for published onehalfstorey_021 refused, folder untouched. Test copy removed afterwards.
- Note: `_verworfen/` already held `cubicasa_review_high_quality_architectural_904` before this test (not from this change).
