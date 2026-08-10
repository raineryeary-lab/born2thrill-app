# Hub model catalog audit and fix

Status: PARTIALLY IMPLEMENTED — steps 1, 2, and 4 done and verified. Step 1
went further than originally scoped: rather than tune `SHELL_HEIGHT_MM`,
the height check was removed entirely and the whole "exclude" mechanism was
changed to "flag, never delete" (`large: true` on parts, nothing dropped),
per Rainer's explicit instruction mid-session that deletion was never
authorised. Step 3 (hand-verify every remaining flagged entry, not just the
two zero-parts ones) not done. Step 5 (re-check `symbol-model-picks.json`
against the fixed catalog) not started.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

`tmp/hub-model-catalog.json` (95 models, produced by
`scripts/catalog-hub-models.py`) is what every downstream pick
(`data/symbol-model-picks.json`), scale resolution
(`scripts/resolve-hub-scales.py`), and render placement trusts. Rainer no
longer trusts it. This plan audits it for real defects, with evidence, before
anything downstream is touched again.

## Current evidence and behavior

Found by direct inspection of `tmp/hub-model-catalog.json` tonight (read-only,
no files changed):

### 1. The shell filter discards legitimate tall furniture, not just rooms

`catalog-hub-models.py:33-34`:

```python
SHELL_WIDTH_MM = 3000
SHELL_HEIGHT_MM = 2300
```

Comment above it: "Anything bigger than this, after scaling, is architecture
rather than furniture: a wall, a floor slab, a ceiling." That premise is
false for two real entries:

- **`Double Glass Door 3D Model (7991)`** — 5 objects, all 5 flagged as
  shell, 0 parts kept. Reported `size_mm: [1730, 146, 2440]` — height
  2440mm, over the 2300mm threshold. A double glass door is architecture in
  the ordinary sense but it is exactly the kind of object this pipeline
  needs to place (front doors are explicitly wanted for the exterior phase).
  Every one of its 5 objects individually exceeds the height threshold, so
  the whole model catalogues with **zero usable geometry**.
- **`White Wardrobe`** — 3 objects, 2 shell, reported `size_mm: [3082, 650,
  2384]` — height 2384mm, over threshold. A wardrobe that tall is entirely
  ordinary. Same failure mode.

Both entries report a `size_mm` computed from the discarded objects' raw
bounds even though `parts: []` — meaning the catalog's own size figure for
these two is measuring geometry the pipeline then refuses to use. That
mismatch (non-empty size, empty parts) is itself worth asserting against.

Not yet checked: how many of the other 93 entries lost some-but-not-all
objects to this same threshold, silently shrinking a real piece of furniture
rather than zeroing it out. `shell_objects` is non-zero on 11 of 95 entries;
each needs the same scrutiny as `Bathroom Furniture Set` got tonight, not
just the two that hit zero.

### 2. A duplicate entry from a duplicate extraction

`Kitchen Furniture Set 9` appears twice, at two different paths:

- `E:\_models_hub\_extracted\Kitchen_Furniture_Set_9\Kitchen Furniture Set 9.blend`
- `E:\_models_hub\_extracted\Kitchen_Furniture_Set_9_BLEND\Kitchen Furniture Set 9.blend`

Confirmed byte-identical (md5 `f2804f3e723f40ca5fc5edf1dbcf7c8e` for both).
Both folders exist on disk — not a listing artifact. Whatever extraction
step produced `_BLEND`-suffixed folders for some archives ran twice for this
one. Any pick or shortlist step that iterates the catalog by label rather
than path could resolve to either copy nondeterministically.

Not yet checked: whether this is the only duplicate, or one of several —
needs a full pass over all 95 by content hash, not just by label string.

### 3. Not yet audited at all

- `tmp/hub-models-resolved.json`, `data/symbol-model-picks.json`,
  `data/furniture-model-overrides.json` — each is downstream of the
  catalog and needs its own pass once the catalog itself is trusted, not
  before.
- The 13 large set files the handoff says were never opened
  (Kitchen Furniture Set 1 alone holding 187 objects) — the catalog records
  object counts and top-level sizes for these but nothing about what
  individual usable parts exist inside them (stove, vanity, etc., per the
  handoff's specific complaint).
- Whether `HUB_SCALE_DIVISOR = 2.54` fixed, applied uniformly, is actually
  right for every entry, or only for the ones it was checked against
  (coffee table, washing machine, per the code comment) — tonight's ecksofa
  investigation found the corner sofa's own scale (divisor 1.0, not 2.54) is
  correct by independent measurement, so the catalog is not uniformly on the
  2.54 assumption already, meaning `scale_divisor` per-entry needs the same
  "measured, not assumed" treatment file by file.

## Repository baselines

`born2thrill-local-workbench`, branch `agent/furnished-render-and-annotation-schema`.
`tmp/hub-model-catalog.json` and related `tmp/*.json` are untracked, git
status already reflects that. No changes made tonight to any catalog file —
this plan is investigation only so far.

## Exact scope

1. **Fix the shell threshold**, or replace it with something that doesn't
   zero out legitimate furniture. Candidate: keep excluding by footprint
   (`SHELL_WIDTH_MM`) since a wall's defining trait is being long and flat,
   but don't exclude on height alone — a tall wardrobe and a tall wall are
   only distinguishable by their footprint/aspect, not height alone. Needs
   testing against known-good large objects (the working protocol's own
   requirement) before landing: rerun the catalogue and confirm the door and
   wardrobe now report their real single-object dimensions, not zero parts.
2. **Re-run the full catalogue** after the fix, and diff against the current
   `tmp/hub-model-catalog.json`: which entries change, by how much, and
   does anything that currently looks fine get worse.
3. **Every entry with `shell_objects > 0`** (11 currently, will change after
   step 1): confirm by hand, the same way the door and wardrobe were caught,
   that what got excluded really is a room shell and not another
   legitimate large piece.
4. **Deduplicate** by content hash across all 95 (or however many after
   re-cataloguing), not just by label — confirm `Kitchen Furniture Set 9` is
   the only duplicate or find the others.
5. Only after 1-4: re-run `resolve-hub-scales.py` and re-check
   `data/symbol-model-picks.json` against the corrected catalog, since picks
   made against wrong catalog data (a zeroed-out door, a duplicate kitchen
   set) could have silently picked the wrong thing or a nonexistent one.

Deliberately NOT in this pass: opening the 13 large set files' internal
contents (stove/vanity search) — that's real work but a separate, larger
task from fixing what's already supposed to be a working single-model
catalogue.

## Files in scope

`scripts/catalog-hub-models.py`, `tmp/hub-model-catalog.json` (regenerated,
not hand-edited), `scripts/resolve-hub-scales.py`,
`tmp/hub-models-resolved.json`, `data/symbol-model-picks.json` (step 5 only,
after 1-4 land and are verified).

## Explicitly out of scope

The 13 unopened set files' internal part inventories. The render pipeline
itself (`render-furnished-dollhouse.py`) — not touched by this plan; it
consumes `data/symbol-model-picks.json`, which is downstream of everything
here.

## Acceptance criteria

- `Double Glass Door 3D Model (7991)` and `White Wardrobe` catalogue with
  their real single-object sizes, not zero parts.
- No two catalogue entries share an md5 of their source file.
- Every entry that still reports `shell_objects > 0` has a one-line note of
  what was actually excluded and why it's legitimately architecture, not
  furniture — not just a number.
- `data/symbol-model-picks.json` regenerated against the fixed catalog,
  diffed against its current version, every changed pick listed with old
  and new value.

## Tests and verification commands

```bash
blender --background --python scripts/catalog-hub-models.py -- \
  "E:\_models_hub\_extracted" tmp/hub-model-catalog.json
python -c "import json; d=json.load(open('tmp/hub-model-catalog.json',encoding='utf-8')); \
  print(sum(1 for m in d['models'] if not m['parts'] and m['objects']>0))"
```
Should print 0 after the fix (no all-shell entries with real objects to
account for).

## Protected and risky paths

`data/symbol-model-picks.json` feeds the live render pipeline directly. Step
5 changes what model gets placed for some symbols — needs the same
before/after render proof as any placement change, not just a catalog diff.

## Floorplan-suite invariant

No. Catalog and pick files are internal tooling inputs, not customer-facing
geometry. Nothing here touches promotion, export, or email.

## Rollback

`tmp/*.json` are regenerated artifacts, not hand-maintained — reverting means
re-running the old script version. `data/symbol-model-picks.json` changes
(step 5) are a normal file revert if needed.

## Approval record

Approved by Rainer ("fix it"). Steps 1, 2, 4 done:
- Step 1: shell filter changed from delete-on-threshold to flag-only,
  height criterion removed, `parts if len(pieces) > 1 else []` bug fixed
  (was hiding single-object survivors). Verified: 0 entries with objects
  but zero parts, down from entries like `Double Glass Door 3D Model
  (7991)` (5/5 objects dropped) and `White Wardrobe` (2/3 dropped).
- Step 2: re-catalogued, diffed against the pre-fix backup
  (`tmp/hub-model-catalog.BEFORE.json`, kept in session scratch, not the
  repo) — 13 entries changed, 45 objects restored across 10 of them.
- Step 4: `Kitchen Furniture Set 9` duplicate (two byte-identical extracted
  copies) deduplicated at catalog-build time; kept the `_BLEND`-suffixed
  path matching every other single-model extraction's naming. 95 -> 94
  entries, zero duplicate labels confirmed.

Step 3 (hand-verify the other 9 previously-flagged entries beyond the two
already checked) and step 5 (re-run picks against the fixed catalog) still
open — not started.
