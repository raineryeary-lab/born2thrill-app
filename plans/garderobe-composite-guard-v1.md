# Garderobe composite guard for Codex visual-catalog deliveries

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Stop `garderobe*` objects from silently disappearing or being replaced with the
wrong furniture in every Codex-delivered restyle, by pasting the exact pixels
of that object from our own verified Blender baseline render back into the
delivered image, instead of relying on Codex to reproduce it correctly (or on
Rainer's eye to catch it) every single round.

## Current evidence and behavior

- `twostorey_045`'s Codex delivery
  (`E:\born2thrill-local-workbench-data\corrections\twostorey_045\renders\codex-twostorey_045-2026-09-14\catalog.json`)
  shows `garderobe-23`, `garderobe-bench`, `garderobe-clothes`,
  `garderobe-umbrella-stand` marked `"status": "ersetzt"` in all 4 ground-floor
  style variants (03-06). Visual diff confirms the item is simply gone in the
  delivered image (see side-by-side crop produced this session).
- `scripts/make-codex-job.py` already treats this as a known, recurring
  failure: `NENNENSWERT["garderobe"] = "Garderobe (ersetzen)"`, with comments
  dated 2026-08-27/2026-09-01 about the same object class going missing or
  swapping places with an open door leaf repeatedly.
- `scripts/lieferung-pruefen.py` already has a verification/rejection loop for
  this class of bug (`_marker_beanstandungen`, `_beleg_beanstandungen`,
  `kasten_verdacht`/`messe_platzhalter`, `RUNDEN.jsonl` +
  `beanstandungs_abschnitt`), but by explicit design the final visual call is
  a human's ("Nicht geprueft: ob jedes Objekt WIRKLICH im Bild ist. Das bleibt
  der Blick eines Menschen." -- `lieferung-pruefen.py:858`). `kasten_verdacht`
  is a warning only, never a rejection.
- `scripts/objektmaske.py` already exists and produces a pixel-exact,
  per-object silhouette mask from any `.blend` (flat-shaded object-ID render),
  keyed by object name in `objektindex.json`. It is not currently used by the
  Codex delivery path at all.

## Scope refinement vs. the chat proposal

The chat proposal was "mask garderobe/stuff back to the baseline pixels."
`stuff` is explicitly excluded here after reading `make-codex-job.py`:

- `garderobe` is finished, real geometry (coat rack, bench, hooks, umbrella
  stand) that Codex is only supposed to *restyle*, not redesign or move. A
  hard pixel composite is safe and exactly matches the rule already stated in
  `INNEN_REGEL`: "welche Moebel dastehen ... das steht in der .blend."
- `stuff` is a deliberate placeholder (`build: "rect"`, a plain box in our own
  baseline) that Codex is explicitly required to *reinterpret* into real
  furniture per room (`STUFF_NACH_RAUM`). Compositing our own baseline pixels
  back would paste the plain box Rainer has repeatedly rejected
  ("codex muss sich mehr Muehe geben ... nicht nur Quader einstellen"), i.e.
  it would defeat the requirement instead of fixing it. `stuff` keeps its
  existing detection (`kasten_verdacht`) and human-review path unchanged.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `git status --short` shows extensive pre-existing uncommitted work from
  earlier in this session (camera_style, railing_sides, north-wall
  registration, etc. in `scripts/render-furnished-dollhouse.py`,
  `scripts/build-simplifier-render-plan.py`, and others) plus long-standing
  untracked docs/data (`docs/CODEX-*.md`, `data/visual-catalog/`, several
  `plans/*.md`). None of that is touched by this plan; it is listed here only
  because the workflow requires recording pre-existing changes before adding
  more.

## Exact scope

Add one new script, `scripts/schuetze-garderobe.py`, run manually against a
Codex delivery folder before `lieferung-pruefen.py --annehmen`:

```
python scripts/schuetze-garderobe.py <plan> <lieferordner>
```

For every image in that folder's `catalog.json`:

1. Read `geometry_source` (the baseline `.blend` this image was derived from)
   and `floor`/`style`.
2. Run `objektmaske.py` (or its logic, invoked the same way) against that
   `.blend` once per distinct `geometry_source` in the catalog (cache by
   path), to get `objektindex.png` + `objektindex.json`.
3. Build a combined mask of every mesh whose stem (`_stamm`, same helper as
   `make-codex-job.py`) is `garderobe`.
4. If the mask is non-empty: composite the corresponding region from the
   matching *baseline PNG* (`geometry_reference_render`) into the delivered
   image, feathered ~4px at the edge so the paste seam isn't a hard line.
   Overwrite the delivered PNG in place (the original is still recoverable
   from the `vorher-*` mechanism `lieferung-pruefen.py` already uses).
5. Rewrite that image's `marker_check` entries for the affected object(s) to
   `"status": "sichtbar"` with `"bei"` set to the mask's measured centroid, so
   `lieferung-pruefen.py`'s existing checks (which already read
   `marker_check`) pass truthfully instead of needing a separate carve-out.
6. Print a one-line summary per image: how many garderobe pixels were
   patched, or "already present, left untouched" if Codex's own delivery
   already matched (skip compositing when the marker was already `sichtbar`
   *and* `_beleg_beanstandungen`-style distance check against the baseline
   centroid is small -- don't paste over a delivery that's already correct).

No change to `lieferung-pruefen.py`'s pass/fail logic itself, and no change to
`make-codex-job.py`'s job contract -- Codex still gets asked to restyle
garderobe like today; this only fixes it up when Codex fails to.

## Files in scope

- `scripts/schuetze-garderobe.py` (new)
- `scripts/schuetze-garderobe.test.py` (new -- unit tests for the mask
  extraction / compositing / marker-rewrite helpers, run without Blender by
  feeding synthetic `objektindex.png`/`.json` fixtures)
- `docs/RENDER-WORKFLOW.md` (add the new manual step to the delivery
  checklist, if that doc already documents the `lieferung-pruefen.py` step --
  read it first, extend rather than restructure)

## Explicitly out of scope

- `stuff` objects (see "Scope refinement" above) -- no compositing, no change
  to `kasten_verdacht`.
- Any change to `make-codex-job.py`'s prompt/contract text.
- Any change to `lieferung-pruefen.py`'s accept/reject logic.
- Wiring this into an automatic pipeline step (`go.py`, `run_project.py`) --
  it stays a manual script Rainer or I run against a delivery folder, matching
  how `lieferung-pruefen.py` itself is invoked today.
- Any other house's Codex delivery besides re-running this against
  `twostorey_045`'s existing `codex-twostorey_045-2026-09-14` folder to prove
  it works, once approved.

## API, schema, and data-contract effects

`catalog.json`'s `marker_check[].status`/`bei` fields get corrected in place
for `garderobe*` entries only, using the existing schema
(`visual-catalog-v1`) -- no new fields, no schema version bump.

## Acceptance criteria

- Running the new script against
  `codex-twostorey_045-2026-09-14` patches all 4 ground-floor images
  (03-06) so the garderobe set is visibly present at its baseline position in
  each, pixel-identical to the baseline render in that region.
- `stuff` regions in the same 4 images are byte-identical before/after (proof
  the tool never touches them).
- Non-affected images (exterior shots, upper-floor images with no garderobe)
  are byte-identical before/after.
- `python scripts/lieferung-pruefen.py twostorey_045
  codex-twostorey_045-2026-09-14` reports no new complaints caused by this
  script (any pre-existing complaints unrelated to garderobe are unaffected).

## Tests and verification commands

New tests in `scripts/schuetze-garderobe.test.py`:
- mask-to-bounding-box and centroid math against a synthetic
  `objektindex.png`/`.json` fixture
- feather/composite produces expected pixel values at a hand-checked sample
  point (fully inside mask, fully outside, on the feather edge)
- marker_check rewrite: `ersetzt` -> `sichtbar` with corrected `bei`; entries
  for `stuff`/other stems untouched
- skip-if-already-correct path: an already-`sichtbar` garderobe marker within
  tolerance of the baseline centroid is left byte-identical

Run: `python -m pytest scripts/schuetze-garderobe.test.py -q` (matches how the
sibling `*.test.py` files in this folder run today -- confirm exact runner
from an existing one, e.g. `lieferung-pruefen.test.py`, before finalizing).

Existing tests: none deleted, skipped, or weakened.

## Protected and risky paths

- Writes directly to files under
  `E:\born2thrill-local-workbench-data\corrections\<plan>\renders\<lieferordner>\`
  (customer-facing render assets). Mitigation: operates on a copy unless
  `--in-place` is passed; default run is dry-run/preview only, printing what
  would change without writing.

## Rights, provenance, privacy, and security impact

None. No new external calls, no new data leaves the machine. The composited
pixels come from our own already-approved Blender baseline render of the same
house, not from any new source.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Required answer: no. This script only copies pixels from the already-approved
baseline render (itself built from the approved corrected geometry via the
existing `go.py` pipeline) back into a Codex-delivered image of the *same*
house/floor/camera. It generates no new geometry and does not touch
publishing or email (`publish-renders.py` is untouched and still gated on
`lieferung-pruefen.py --annehmen` as today).

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

(none yet -- filled in during implementation if needed)

## Rollback

Delete `scripts/schuetze-garderobe.py` and its test file. Delivered images it
modified can be restored from the pre-run copies (default dry-run mode, or the
`vorher-*` backups if `--in-place` was used and `lieferung-pruefen.py`'s own
`VORHER` convention was followed for the backup name).

## Unresolved questions

- Does `docs/RENDER-WORKFLOW.md` already describe the Codex-delivery-review
  step in enough detail to extend cleanly, or does this need its own short
  section? (check before editing it)
- Should the feather radius (~4px) be a CLI flag or fixed? Proposal: fixed
  constant with a comment, same style as `BELEG_RADIUS_PX` /
  `KASTEN_WAR_FLACH` in `lieferung-pruefen.py`, revisit only if a real case
  needs it.

## Approval record

Approved by Rainer, 2026-09-15 ("both").
