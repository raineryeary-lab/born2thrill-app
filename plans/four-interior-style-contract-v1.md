# Four interior style contract

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Make every generated Codex render job require four interior presentation variants per interior Blender source: Warm Modern, Soft Scandinavian, Modern Architectural, and Dark Modern. Preserve architecture, camera, room layout, openings, stairs, and non-Garderobe object placement. Permit controlled style changes to materials, colours, lighting, and restrained accessories. Replace only explicitly named `garderobe-*` placeholders with real, style-matched open coat storage.

## Current evidence and behavior

`scripts/make-codex-job.py::outputs_for()` currently emits one image for every `.blend`. Its `models_locked` text forbids all material and object changes, so the machine contract requests only `interior-modern.png` and conflicts with the established four-style package and Garderobe rule.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Worktree is already dirty with user-owned modified and untracked files. They remain untouched except for the files explicitly listed below.

## Exact scope

- Extend the Codex job contract generator to emit four interior outputs for each interior `.blend`.
- Add explicit style identifiers and stable filenames.
- Split the lock into immutable architecture/non-Garderobe objects and permitted style presentation changes.
- Add the permanent `garderobe-*` replacement rule.
- Render the same rules in generated `CODEX-AUFTRAG.md`.

## Files in scope

- `scripts/make-codex-job.py`
- `scripts/make-codex-job.test.py` (new)
- `plans/four-interior-style-contract-v1.md`
- `C:\dev\Floorplan-tools\born2thrill-app-repo\plans\ROADMAP.md` only to record/complete this tracked rule.

## Explicitly out of scope

- Blender geometry generation or modification
- Existing `.blend`, annotation, correction, or render files
- WordPress upload/publication
- Database migrations, customer email, approvals, exterior style count, UI changes

## API, schema, and data-contract effects

`zf-codex-job-v1.required_outputs` gains four entries per interior source with `style` and stable filename hints: `interior-<floor>-warm-modern.png`, `interior-<floor>-soft-scandinavian.png`, `interior-<floor>-modern-architectural.png`, and `interior-<floor>-dark-modern.png`. Existing exterior entries remain unchanged.

## Acceptance criteria

- A bungalow job with one interior source requires exactly four interior outputs and two existing exterior outputs.
- Multi-floor jobs receive four outputs for every interior floor source without filename collisions.
- Every interior output identifies one of the four required styles.
- Contract text locks architecture, camera, openings, stairs, room layout, and all non-Garderobe objects.
- Contract text permits style-specific materials, colour, lighting, and restrained accessories.
- Contract text requires only explicitly named `garderobe-*` placeholders to become genuine open coat-storage furniture with hooks, hangers, coats, shelf, bench, and shoe storage.
- Generated Markdown accurately mirrors the JSON contract.

## Tests and verification commands

- Add `scripts/make-codex-job.test.py` covering single-floor output expansion, multi-floor stable naming, unchanged exterior outputs, lock wording, Garderobe exception, and Markdown parity.
- Run: `python scripts/make-codex-job.test.py`
- Run: `python -m py_compile scripts/make-codex-job.py scripts/make-codex-job.test.py`
- Run an isolated fixture generation and inspect JSON/Markdown output counts and names.
- Run `git diff --check` and report complete status/diff summary.

## Protected and risky paths

- Never overwrite current `.blend`, annotations, corrections, manifests, render packages, catalog data, or existing tests.
- Preserve all unrelated dirty and untracked worktree files.
- Do not regenerate real jobs during tests; use temporary fixture directories.

## Rights, provenance, privacy, and security impact

No rights status changes. Source hashes and provenance remain required. No credentials or personal data are added.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? No. The change only expands presentation outputs from already certified `.blend` inputs; it does not generate geometry or bypass approval/publication gates. Tests will assert input hashes remain in the contract and exterior/publication behavior is unchanged.

## Customer, email, database, deployment, and external effects

None. No upload, publication, email, deployment, or database write.

## Failed-hypothesis log

- None.

## Rollback

Revert only the scoped generator/test changes and remove this new plan entry. Existing render/model/data files are unaffected.

## Unresolved questions

- None. User established the permanent four-style and Garderobe rules.

## Approval record

Not approved. Stop before implementation.
