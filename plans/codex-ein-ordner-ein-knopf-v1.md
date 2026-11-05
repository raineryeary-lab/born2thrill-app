# Codex: ein Ordner, ein Knopf zum Hochladen

Status: DONE 2026-10-20

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-20: "why cant we just have an easy way to upload these images the paths and all the BS should be created when we press the button an Codex and this path you could just deliver with the Auftrag an codex".

Press "Codex" → the delivery folder exists and its path is in the Auftrag. Codex drops the images there. Press "Hochladen" → that exact folder is checked and uploaded. Nobody copies, renames or looks for paths.

## Current evidence

- `scripts/make-codex-job.py:1518` already names the folder `renders/codex-<plan>-<datum>` and writes it into the Auftrag ("Ablegen in einem NEUEN Ordner (anlegen, falls er fehlt)") and into `codex-job.json` as `delivery_folder`. It does NOT create the folder.
- `scripts/go.py bilderordner()` (line 245) does NOT read `delivery_folder`. It guesses: the `codex-*` folder with the newest picture. It uploads whatever is there, complete or not.
- `scripts/lieferung-pruefen.py` can check a delivery (count, catalog.json, names), but the Hochladen button (`pipeline/route.ts:139` → `go.py --hochladen`) never calls it.
- `make-codex-job.py:408` still says "zwei Aussenansichten ... 4 je Geschoss + 2", which contradicts the image list (onehalfstorey_044 job, 2026-10-20).

## Exact scope

1. `make-codex-job.py`: create the empty delivery folder when the job is written. Put the absolute path at the TOP of CODEX-AUFTRAG.md ("Bilder hierhin: ..."), not only near the bottom.
2. `make-codex-job.py:408`: derive the count sentence from `required_outputs` (e.g. "1 Aussenansicht + 4 Stile je Geschoss = 9 Bilder"), so it can never contradict the list again.
3. `go.py --hochladen`: take the folder from the newest `codex-job.json` (`delivery_folder`). Before uploading, run the `lieferung-pruefen.py` check. If anything is missing, upload NOTHING and say in one line what is missing ("6 von 9 Bildern fehlen: 03, 04, ... ; catalog.json fehlt"). If it is complete, upload under the `intended_filename` names from catalog.json (publish-renders.py, no `--send`).
4. Old houses without `delivery_folder` in their job: keep today's `bilderordner()` behaviour.

## Out of scope

- Freigeben (approve-plan.py / freigeben.py), `--send`, rights.
- What Codex renders and how.

## Tests (first)

- `make-codex-job.test.py`: the folder exists after the job is written; the path is in the first lines of the Auftrag; the count sentence matches `required_outputs` (1+8 for a 1,5-Geschosser, 4+8 for a two-storey house).
- `go.test.py`: an incomplete folder → no publish call, message names the missing files; a complete folder → publish called with exactly `delivery_folder`; no `delivery_folder` → old behaviour.
- Existing tests stay green, none changed.

## Safety gate

Can any changed path publish geometry without an approved reference? No. The upload only happens on Rainer's button press, never with `--send`, and now additionally only when the delivery is complete.

## Effects / rollback

Local scripts only, no upload while testing. Rollback: restore the `.before-` backups of the two scripts.

## Approval record

Approved by Rainer in chat, 2026-10-20: "Approved: implement codex-ein-ordner-ein-knopf-v1, tests first."

## Implementation record (2026-10-20)

- `make-codex-job.py`: `lieferordner_anlegen(job)` (called in main after the Auftrag is written); `anzahl_satz(required)` replaces the fixed "zwei Aussenansichten ... + 2" sentence in INNEN_REGEL; the folder path is the first thing under the job header in CODEX-AUFTRAG.md.
- `go.py`: `lieferung_fehlt(job, ordner)` (count + catalog.json, then the full `lieferung-pruefen.pruefe`); `--hochladen` uses `delivery_folder` from codex-job.json and uploads nothing unless the list is empty; old jobs without the field fall back to `bilderordner()`.
- Note: the delivered files already carry their final names (`filename_hint`, e.g. `01-exterior-satteldach.png`), so no renaming step is needed before publish-renders.py.
- Tests first: 6 new in make-codex-job.test.py, 4 new in go.test.py, red before, green after. All script suites green except the known unrelated door-hinge failure in build-simplifier-render-plan.test.py.
- Real run onehalfstorey_044: job regenerated, folder `renders/codex-onehalfstorey_044-2026-10-20` exists (empty), Auftrag line 10-12 names it, count sentence "1 Aussenansicht + 4 Stile je Geschoss (2 Geschosse) = 9 Bilder". `go.py onehalfstorey_044 --hochladen` -> "nicht hochgeladen -- Codex-Lieferung unvollstaendig: alle 9 Bilder fehlen noch; catalog.json fehlt". Nothing uploaded.
- Backups: `*.before-ein-ordner` next to the four files.
