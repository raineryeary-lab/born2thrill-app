# ERSTE-FASSUNG-WARTEN-001: Auftrag text says "show the first version, wait for OK, then upload"

Status: DONE 2026-10-29 (Rainer: "ok"; first version = "one image per floor of one type and one exterior"; corrections also wait, default kept)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-29: "the first version we check together if they are ok then the rest are completed and uploaded by itself."

- This is already in the rulebook (`docs/CODEX-REGELN-4PLUS2.md`, section 12).
- The Auftrag text that `scripts/make-codex-job.py` writes still says only "upload once ALL images are there". It does not say to show the first version and wait for Rainer's OK.
- This plan puts that step into the Auftrag text and into `codex-job.json`, so Codex sees it even without reading the rulebook to the end.

## Current evidence and behavior

- `scripts/make-codex-job.py:1923-1935`, `job["publish"]`:
  - `command` is the publish-renders.py call.
  - `note`: "Du laedst selbst hoch, mit genau diesem Befehl, erst wenn ALLE geforderten Bilder im Ordner liegen. Vorher nicht. Danach schreibst du upload_performed: true in catalog.json."
- `scripts/make-codex-job.py:2306-2311`: section "## Hochladen -- das machst DU, zum Schluss". It prints the command, the note, and "Fehlt auch nur eines, laedst du NICHT hoch ...".
- There is no wait-for-OK step anywhere in the generated text.
- Nothing reads `publish.note` except the text renderer (grep: only `make-codex-job.py:2308`). Tests use dummy `publish` dicts (`make-codex-job.test.py:293, 320, 560, 769, 857, 875, 1764, 1810`).
- `make-codex-job.py` is not in the build toolchain hash (`run_project.py`), so houses are not marked "renderer changed".

## Repository baselines

- `C:\dev\Floorplan-tools` is not a git repository (environment: "Is a git repository: false").
- Backups instead: `scripts/make-codex-job.py.before-erste-fassung`, `scripts/make-codex-job.test.py.before-erste-fassung`.
- Pre-existing changes today: rulebook edits (backups `docs/CODEX-REGELN-4PLUS2.md.before-farbe-garten`, `.before-handoff-1029`, `.before-handoff-1029-2`, `.before-upload-regel`). They are untouched by this plan.

## Exact scope

1. In `job["publish"]`, add a field `erst_freigabe`. Text:
   "ERSTE FASSUNG: Stell zuerst EINE fertige Fassung fertig (ein Innenbild und, falls bestellt, eine Aussenansicht), zeig sie Rainer und WARTE auf sein OK. Erst danach die restlichen Bilder im selben Standard, Pruefliste (Abschnitt 11), dann hochladen."
2. Rewrite `publish.note` so it starts with "Nach Rainers OK zur ersten Fassung ...". Everything else stays: all images present, `upload_performed: true`. Add "ohne --send, keine Kunden-E-Mails, keine Aenderung an Rechte- oder Bildfreigaben".
3. In the text section "## Hochladen": print `erst_freigabe` before the command. Rename the heading to "## Erste Fassung, dann Hochladen -- das machst DU".
4. Old jobs without `erst_freigabe`: the renderer uses `.get()` and prints nothing extra. Old `codex-job.json` files must not fail.

## Files in scope

- `scripts/make-codex-job.py`
- `scripts/make-codex-job.test.py` (new tests only)
- `born2thrill-app-repo/plans/ROADMAP.md` (close the item with evidence)

## Explicitly out of scope

- `publish-renders.py`, its locks and behaviour.
- Workbench routes, the release (Freigabe) flow, the ledger.
- Already generated Auftraege on disk. They change only when an Auftrag is made again.
- The EFH160 EG-Sicht classification (separate roadmap item).

## API, schema, and data-contract effects

- `codex-job.json` gains one optional key, `publish.erst_freigabe` (string). Nothing reads `publish` programmatically.
- `contract_sha256` changes for newly generated jobs because the text changes. That is expected for every generator change.

## Acceptance criteria

- A newly generated CODEX-AUFTRAG.md contains "ERSTE FASSUNG" and "WARTE auf sein OK". The wait-for-OK text comes before the publish command.
- The note still contains "erst wenn ALLE" and `upload_performed: true`, and newly contains "--send".
- A job dict without `erst_freigabe` renders without error.
- All existing make-codex-job tests are green (currently 164 OK).

## Tests and verification commands

New tests in `scripts/make-codex-job.test.py`:
- `test_auftrag_verlangt_erste_fassung_vor_upload`: the generated text has "ERSTE FASSUNG", and it comes before the command line.
- `test_publish_note_behaelt_vollstaendigkeit_und_kein_send`
- `test_alter_job_ohne_erst_freigabe_rendert`

Verification: `python scripts/make-codex-job.test.py`.

No existing test is changed, skipped or deleted.

## Protected and risky paths

None. Generator text only.

## Rights, provenance, privacy, and security impact

None. Rights and image approvals stay human. The new text says so explicitly.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.**

- The change only adds a human gate (Rainer's OK) before Codex runs the existing `publish-renders.py`.
- It adds no new publish path and no `--send`.
- It does not touch email or geometry.

## Customer, email, database, deployment, and external effects

None from this change. Uploads still only happen through `publish-renders.py`, which already exists and was authorised by Rainer on 2026-10-07 and 2026-10-29.

## Failed-hypothesis log

None.

## Rollback

Restore `scripts/make-codex-job.py.before-erste-fassung` and `scripts/make-codex-job.test.py.before-erste-fassung`.

## Unresolved questions

- What counts as "the first version"? This plan says: one finished interior image plus, if ordered, one exterior. Alternative: the whole first draft set, all images once. Rainer decides.
- A correction-only Auftrag (`--nur`, a few images) could skip the wait. This plan does NOT skip it, which is the safe default.

## Approval record

Approved 2026-10-29. Implemented as erste_fassung()/erst_freigabe_text()/PUBLISH_NOTE in make-codex-job.py; 5 new tests, 169 OK; checked on a real in-memory Auftrag (1_2_2: 3 images).
