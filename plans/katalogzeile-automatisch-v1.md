# Katalogzeile automatisch anlegen (kein INSERT von Hand mehr)

Status: DONE 2026-10-20 -- live, first real use twostorey_059

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-20: "you have to get this fixed why all the extra work" -- then: "write the plan: the katalog route creates the row when it is missing, and publish-renders.py calls it before uploading. I'll install the PHP."

When a house is uploaded for the first time, its row in `kon_grundrisse` is created automatically, with the same values the original catalogue import gave every other house. No more SQL in WP Data Access.

## Current evidence and behavior

- `publish-renders.py check_plan()` reads `GET b2t/v1/grundrisse` and exits ("No plan ... in the catalogue") when the plan id is missing. twostorey_059 hit this on 2026-10-20 with 12 images ready; Rainer pasted an INSERT by hand.
- The only write route we own, `wordpress/b2t-katalog-freigabe.php` (`POST b2t/v1/katalog`), UPDATEs `bilder`/`approved` on an existing row and returns 404 for a missing plan. Nothing anywhere INSERTs rows. The repo has no importer: the 312 live rows came from a one-time import (August), and every house drawn since then needed a hand INSERT (bungalow_040_185 on 10-18, twostorey_059 today).
- **The original import rule, reconstructed and measured** against all 311 houses that are both in `data/simplifier-v2/dataset.json` and in the live list (snapshot 2026-10-20):

  | column (API key) | rule | matches |
  |---|---|---|
  | `haustyp` (t) | house_type: bungalow -> "Bungalow", twostorey -> "Zweigeschosser", onehalfstorey -> "1,5-Geschosser", other -> "Sonstige", twostorey_cellar -> "Zweigeschosser mit Keller" | 307/311 |
  | `geschosse` (f) | number of drawn floors | 306/311 |
  | `keller` (b) | 1 if a `basement` floor exists, else 0 | consistent |
  | `raeume` (r) | number of drawn room areas | 308/311 |
  | `schlafzimmer` (sz) | areas with room_id eltern | 311/311 |
  | `kinderzimmer` (kz) | areas with room_ids containing kind | 311/311 |
  | `baeder` (bd) | areas with room_id bad (NOT du_wc) | 310/311 |
  | hash (h) | first 12 chars of annotation_sha256 | 305/311 |
  | `ausstattung` (a) | room_id -> word: eltern Schlafzimmer, bad Bad, kind Kinderzimmer, wc Gäste-WC, buero Arbeitszimmer, hwr_htr HWR, ankleide Ankleide, gast Gästezimmer, speisekammer Speisekammer, kueche/kochen Küche, wohnen Wohnen, essen Essen, wohnen_essen Wohnen+Essen, wohnen_essen_kochen Wohnen+Essen+Küche, essen_kochen/kueche_essen Essen+Küche, abstell storage, garage garage, carport carport, garage_carport garage+carport, hobbyraum hobby_room; diele/flur/du_wc/luftraum/treppe add nothing | consistent |

- The hand INSERTs since August drifted from that rule. The plan does NOT rewrite them; it only stops new drift.
  - bungalow_040_185: "Zweigeschosser" with "Diele, Luftraum" in ausstattung; `bd` 2 counted a DU-WC.
  - bungalow_040_66: lower-case "bungalow".
  - The memory note "DU-WC counts" was wrong; corrected.

## Repository baselines

`born2thrill-local-workbench`, branch `agent/furnished-render-and-annotation-schema`, HEAD `5be1a4e`, user-owned dirty worktree (untouched). `wordpress/b2t-katalog-freigabe.php` unchanged since 2026-08-22.

## Exact scope

1. **New pure module `scripts/katalogzeile.py`.** `zeile(annotations, data)` returns the row: haustyp, geschosse, keller, raeume, qualitaet "geprüft", ausstattung (fixed order), schlafzimmer, kinderzimmer, baeder, hash, blender_pfade.
   - Reads the project's own `annotations.json` + `data.json`.
   - The blender path is the modern exterior .blend in go-baseline, with forward slashes.
2. **PHP, same mu-plugin file (`b2t-katalog-freigabe.php`, version 1.1.0): new route `POST b2t/v1/grundriss-anlegen`.**
   - Same permission as the existing route (`edit_posts`, the upload's Application Password) and the same table detection.
   - INSERTs ONLY when `plan_id` is missing. An existing row is never changed: it answers 200 `{"angelegt": false}` with the row as it is.
   - Sanitises and validates every field: plan id regex as today; integers >= 0; haustyp from the five known values; ausstattung only from the known words.
   - Never sets `approved` or `bilder` (rights and release stay with the existing gates).
   - Answers with the row as it now is in the table.
3. **`publish-renders.py`.** When `check_plan` finds no row:
   - computes it with `katalogzeile.zeile()` and prints it;
   - in `--dry-run`, stops there ("would create");
   - otherwise POSTs it to `grundriss-anlegen`, then re-reads `GET b2t/v1/grundrisse` and continues only if the plan is now listed.
   - If the route is missing (404 for the route itself), it says exactly that ("PHP not installed yet") and prints the INSERT as today's fallback.
4. **Rainer installs** the updated PHP file into `wp-content/mu-plugins/` (replacing the old one; same filename).

## Files in scope

- new `scripts/katalogzeile.py`, new `scripts/katalogzeile.test.py`
- `scripts/publish-renders.py` (`check_plan` path only)
- `wordpress/b2t-katalog-freigabe.php` (new route added; the existing `katalog` route unchanged)
- new test fixture `scripts/testdaten/grundrisse-live-2026-10-20.json` (snapshot of the public `GET b2t/v1/grundrisse` list: plan ids and catalogue columns, no private data)

## Explicitly out of scope

- Correcting the drifted hand-inserted rows (bungalow_040_185, bungalow_040_66, twostorey_059). Listed for Rainer; changing live rows needs its own OK.
- The `d` description and thumbnail (`th`): produced by the catalogue plugin on the server, not by us.
- Rights (`approved`), release (`bilder`), customer sending.
- The Workbench UI (its "Hochladen" step calls `go.py --hochladen` -> `publish-renders.py`, so it benefits without changes).

## API, schema, and data-contract effects

- New REST route `POST /wp-json/b2t/v1/grundriss-anlegen` (authenticated, `edit_posts`).
- No schema change to `kon_grundrisse`. The same 11 columns as the manual INSERTs; the hash column is filled only if the route finds a column for it (`SHOW COLUMNS`), otherwise left out.

## Acceptance criteria

1. `katalogzeile.zeile()` applied to every `dataset.json` record reproduces the live snapshot for t, f, b, r, sz, kz, bd and the ausstattung SET:
   - for at least the match counts in the table above;
   - every mismatch listed in the test output by plan id (no silent tolerance).
2. For twostorey_059 it gives exactly the row Rainer inserted today (10 rooms, 1/2/1).
3. `publish-renders.py --dry-run` on a plan missing from the catalogue prints the row it would create and uploads nothing.
4. After the PHP is installed, a real first upload of a new house creates the row, then uploads.
   - A second call does not change the row.
   - A call with a bad haustyp or a foreign word in ausstattung is refused (400).
5. Existing tests pass.

## Tests and verification commands

- `python scripts/katalogzeile.test.py` (new): the 311-house reproduction, twostorey_059, a basement house (keller 1), the "nothing" rooms (diele/flur/du_wc/luftraum).
- `python scripts/publish-renders.py --plan <a missing test id> --dir <folder> --dry-run`: prints the row, no network write.
- PHP: `php -l` if PHP is available locally (otherwise noted as not run); the 400/200/404 paths are listed for Rainer's first call.
- No existing test is deleted, skipped or weakened.

## Protected and risky paths

- **A new write path into the live catalogue table.** Mitigated:
  - INSERT-only, never UPDATE;
  - strict validation, same capability as the existing upload;
  - `approved` and `bilder` untouched;
  - the script re-reads the public list before uploading.
- **A wrong row would be visible in the catalogue search** (its values only; no images until the upload, no release until `freigeben`). The dry-run shows it first.

## Rights, provenance, privacy, and security impact

- No rights change: `approved` is never written; the existing rights gate in publish-renders.py runs as today.
- The route accepts room words and counts only; no free text beyond the validated list.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. The new path writes catalogue metadata derived from the existing annotation; it does not approve, release or email anything, and the rights gate still blocks `--send`.

## Customer, email, database, deployment, and external effects

- Database: new rows in `kon_grundrisse`, only through the new route, only for missing plan ids.
- Deployment: Rainer uploads the PHP file himself. Nothing is sent to customers.

## Rollback

Put back the previous `b2t-katalog-freigabe.php` (v1.0.0) in mu-plugins; revert `publish-renders.py`; delete the new files. Rows already created stay (they are correct rows); they can be removed by hand.

## Unresolved questions

1. Should the three drifted hand rows be corrected to the rule (bungalow_040_185: Bungalow vs Zweigeschosser, ausstattung, bd)? Separate OK.

## Approval record

Approved by Rainer in chat, 2026-10-20: "Approved: implement katalogzeile-automatisch-v1, tests first. Give me the PHP file to install when it's ready."

Context at approval: Rainer's hand INSERT for twostorey_059 did not reach the live list (still 312 rows, no twostorey_059, checked 2026-10-20).

## Verification record (2026-10-20)

- `scripts/katalogzeile.test.py`: 11 OK.
  - Reproduction against the live snapshot (`scripts/testdaten/grundrisse-live-2026-10-20.json`, 312 rows) for the 311 dataset houses: t >= 307, f >= 306, b >= 309, r >= 308, sz 311, kz 311, bd >= 310, hash >= 305.
  - ausstattung: 7 named deviations: bungalow_040_66 (hand INSERT) plus 6 houses whose drawing changed after the import.
- Two rules found during implementation, now in katalogzeile.py:
  - a DU-WC on the ground floor is the import's "Gäste-WC" (112 of 114 such houses);
  - balcony/roof_terrace come from the drawn elements.
- Two expectations of the new test were adjusted to the rule while writing it (named in the test): the basement fixture now expects "Gäste-WC"; the ausstattung tolerance is 7 named deviations.
- Plan text corrected: acceptance 2 said "exactly the row Rainer inserted (10 rooms)". The import rule counts every drawn area, the Luftraum included, so twostorey_059 gets raeume 11, and "Diele" is no catalogue word. The test pins 11 / 1 / 2 / 1.
- `publish-renders.py --plan twostorey_059 --dir <codex-twostorey_059-2026-10-20> --dry-run`: printed the new row (Zweigeschosser, 2 floors, Keller 0, 11 rooms, 1/2/1, hash 59ac2b3e3cdc, flachdach .blend), "(dry run: nicht angelegt)", and the 12 images it would upload. No network write.
- `php -l wordpress/b2t-katalog-freigabe.php` (PHP 8.3): no syntax errors. The previous v1.0.0 is backed up in the session scratchpad.
- Not yet verifiable: the live route. It needs Rainer to install the file. The first real upload is the test (it creates the row, re-reads the list, then uploads).
- Rainer's hand INSERT for twostorey_059 did not reach the list (still 312 rows); cause unknown (WP Data Access output not seen). The route makes it unnecessary.
- Install attempt 1 (2026-10-20): Rainer put v1.1.0 into mu-plugins, but the site kept serving 1.0.0 (route index without grundriss-anlegen; POST -> rest_no_route).
  - The wp-admin plugin list shows why: "B2T Katalog-Freigabe 1.0.0" runs as a NORMAL plugin (installed in August via wp-admin), not from mu-plugins.
  - The mu copy evidently is not loaded; had it loaded next to the old plugin, the duplicate function names would have crashed WordPress.
- v1.1.1: the whole file is guarded (`B2T_KATALOG_FREIGABE_GELADEN`, `function_exists`), so a second loaded copy cannot crash the site. Proven with PHP 8.3 against WordPress stubs: included twice, routes registered once (katalog, grundriss-anlegen), all four functions present. `php -l` clean.
- Delivered as the plugin zip `wordpress/b2t-katalog-freigabe.zip` (folder `b2t-katalog-freigabe/`) for wp-admin -> Plugins -> Plugin hochladen -> "Aktuelle mit hochgeladener ersetzen".
- **Live, 2026-10-20 (after Rainer replaced the plugin):**
  - The route index lists `/b2t/v1/grundriss-anlegen`.
  - `publish-renders.py --plan twostorey_059` (no --send) printed the row, "-> angelegt", re-read the list, then uploaded 12 images (media ids 1001-1012).
  - The catalogue now has 313 rows, twostorey_059 included. No customer sending, `approved` untouched.
